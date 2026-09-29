"""
ERP模拟教学模块 - 5大模块一体化教学演示
模块1：基础数据设置（商品档案+BOM+客户档案+信用额度+初始库存）
模块2：销售订单处理（录入+实时信用检查+实时库存检查+订单状态管理）
模块3：MRP与计划运算（MRP运算+BOM展开+库存对比+自动生成生产工单+采购申请单）
模块4：采购与入库（采购订单管理+模拟入库→库存更新+应付账款增加）
模块5：生产、发货与财务集成（生产领料+完工入库+销售发货+财务总览）
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
import datetime

from .. import crud, schemas, models
from ..database import get_db
from ..app import make_response

router = APIRouter()


# ============================== 工具函数 ==============================

def ensure_account_set(db: Session) -> int:
    """确保默认账套存在，返回 account_set_id"""
    acc = db.query(models.AccountSet).first()
    if not acc:
        acc = models.AccountSet(
            name="ERP模拟教学账套",
            code="SIM-DEMO",
            company_name="模拟教学示例公司",
            currency="CNY",
            timezone="Asia/Shanghai",
            status="ACTIVE"
        )
        db.add(acc)
        db.commit()
        db.refresh(acc)
    return acc.id


def get_material_stock(db: Session, account_set_id: int, material_id: int) -> int:
    """获取物料的可用库存总量"""
    invs = crud.get_batch_inventories(db, account_set_id=account_set_id, material_id=material_id)
    return sum(int(inv.quantity) for inv in invs if inv.quality_status == "AVAILABLE")


def get_customer_receivable(db: Session, customer_id: int) -> Decimal:
    """获取客户当前应收账款余额（从凭证分录中统计 1122 应收账款 借-贷）"""
    entries = db.query(models.VoucherEntry).filter(
        models.VoucherEntry.customer_id == customer_id,
        models.VoucherEntry.account_code == "1122"
    ).all()
    debit = sum(Decimal(str(e.debit or 0)) for e in entries)
    credit = sum(Decimal(str(e.credit or 0)) for e in entries)
    return Decimal(str(debit - credit))


_voucher_counter = {"n": 0}


def _gen_voucher_no(voucher_type: str) -> str:
    """生成唯一凭证号：类型+SIM+时间到微秒+进程内计数，避免同秒冲突"""
    _voucher_counter["n"] = (_voucher_counter["n"] + 1) % 100000
    ts = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    return f"{voucher_type}-SIM-{ts}-{_voucher_counter['n']:05d}"


def create_voucher_with_entries(db: Session, account_set_id: int, voucher_type: str,
                                reference_doc: str, entries_data: list,
                                voucher_date: datetime.date = None) -> models.VoucherDB:
    """创建凭证+分录（模拟教学：直接过账）"""
    if voucher_date is None:
        voucher_date = datetime.date.today()
    voucher_no = _gen_voucher_no(voucher_type)
    vtype = models.VoucherType[voucher_type] if voucher_type in models.VoucherType.__members__ else models.VoucherType.GENERAL
    voucher = models.VoucherDB(
        account_set_id=account_set_id,
        voucher_no=voucher_no,
        voucher_type=vtype,
        voucher_date=voucher_date,
        status=models.VoucherStatus.POSTED,
        reference_doc=reference_doc,
        poster="模拟教学系统"
    )
    db.add(voucher)
    db.commit()
    db.refresh(voucher)
    for e in entries_data:
        db.add(models.VoucherEntry(
            voucher_id=voucher.id,
            account_code=e["account_code"],
            account_name=e["account_name"],
            debit=e.get("debit"),
            credit=e.get("credit"),
            summary=e.get("summary", ""),
            customer_id=e.get("customer_id"),
            supplier_id=e.get("supplier_id"),
            material_id=e.get("material_id")
        ))
    db.commit()
    db.refresh(voucher)
    return voucher


# ============================== 模块1：基础数据设置 ==============================

@router.post("/seed", tags=["模拟教学-基础数据"])
def seed_simulation_data(db: Session = Depends(get_db)):
    """一键初始化模拟教学基础数据：商品A/X/Y、客户A/B、BOM、初始库存"""
    try:
        account_set_id = ensure_account_set(db)
        created = {"materials": [], "customers": [], "bom": None, "inventory": [], "skipped": []}

        existing_mat = db.query(models.Material).filter(
            models.Material.code.in_(["SIM-A", "SIM-X", "SIM-Y"])
        ).all()
        existing_codes = {m.code for m in existing_mat}

        # 1. 机器A（成品，自制）
        if "SIM-A" not in existing_codes:
            mat_a = models.Material(
                account_set_id=account_set_id, name="机器A", code="SIM-A", barcode="SIM000000A",
                spec="A工厂主力机型", description="模拟教学示例成品",
                unit_price=Decimal("5000.00"), unit="台",
                type=models.MaterialType.FINISHED_GOODS, property=models.MaterialProperty.INHOUSE,
                lead_time=7, safety_stock=Decimal("5"), min_stock=0, max_stock=1000
            )
            db.add(mat_a); db.commit(); db.refresh(mat_a)
            mat_a_id = mat_a.id
            created["materials"].append({"id": mat_a.id, "code": mat_a.code, "name": mat_a.name,
                                          "type": "成品", "standard_cost": str(mat_a.unit_price)})
        else:
            mat_a = next(m for m in existing_mat if m.code == "SIM-A")
            mat_a_id = mat_a.id
            created["skipped"].append({"code": "SIM-A", "reason": "已存在"})

        # 2. 零件X（原料，采购）
        if "SIM-X" not in existing_codes:
            mat_x = models.Material(
                account_set_id=account_set_id, name="零件X", code="SIM-X", barcode="SIM000000X",
                spec="机器A核心零件", description="模拟教学示例原料",
                unit_price=Decimal("200.00"), unit="个",
                type=models.MaterialType.RAW_MATERIAL, property=models.MaterialProperty.PURCHASE,
                lead_time=3, safety_stock=Decimal("50"), min_stock=0, max_stock=5000
            )
            db.add(mat_x); db.commit(); db.refresh(mat_x)
            mat_x_id = mat_x.id
            created["materials"].append({"id": mat_x.id, "code": mat_x.code, "name": mat_x.name,
                                          "type": "原料", "standard_cost": str(mat_x.unit_price)})
        else:
            mat_x = next(m for m in existing_mat if m.code == "SIM-X")
            mat_x_id = mat_x.id
            created["skipped"].append({"code": "SIM-X", "reason": "已存在"})

        # 3. 零件Y（原料，采购）
        if "SIM-Y" not in existing_codes:
            mat_y = models.Material(
                account_set_id=account_set_id, name="零件Y", code="SIM-Y", barcode="SIM000000Y",
                spec="机器A辅助零件", description="模拟教学示例原料",
                unit_price=Decimal("100.00"), unit="个",
                type=models.MaterialType.RAW_MATERIAL, property=models.MaterialProperty.PURCHASE,
                lead_time=3, safety_stock=Decimal("30"), min_stock=0, max_stock=5000
            )
            db.add(mat_y); db.commit(); db.refresh(mat_y)
            mat_y_id = mat_y.id
            created["materials"].append({"id": mat_y.id, "code": mat_y.code, "name": mat_y.name,
                                          "type": "原料", "standard_cost": str(mat_y.unit_price)})
        else:
            mat_y = next(m for m in existing_mat if m.code == "SIM-Y")
            mat_y_id = mat_y.id
            created["skipped"].append({"code": "SIM-Y", "reason": "已存在"})

        # 4. BOM：机器A = 2个零件X + 4个零件Y
        existing_bom = db.query(models.BOM).filter(models.BOM.product_id == mat_a_id).first()
        if not existing_bom:
            bom = models.BOM(
                account_set_id=account_set_id, product_id=mat_a_id,
                version="V1", effective_date=datetime.date.today(), status="ACTIVE"
            )
            db.add(bom); db.commit(); db.refresh(bom)
            for mid, qty, seq in [(mat_x_id, Decimal("2"), 1), (mat_y_id, Decimal("4"), 2)]:
                db.add(models.BOMItem(
                    bom_id=bom.id, material_id=mid, quantity=qty, unit="个",
                    scrap_rate=Decimal("0"), sequence=seq, level=1
                ))
            db.commit(); db.refresh(bom)
            created["bom"] = {
                "id": bom.id, "product": "机器A",
                "items": [{"material": "零件X", "quantity": "2"}, {"material": "零件Y", "quantity": "4"}]
            }
        else:
            created["skipped"].append({"bom_for": "SIM-A", "reason": "已存在"})

        # 5. 客户A（金牌，额度100万） + 客户B（普通，额度20万）
        existing_custs = db.query(models.Customer).filter(
            models.Customer.code.in_(["SIM-CUST-A", "SIM-CUST-B"])
        ).all()
        existing_cust_codes = {c.code for c in existing_custs}

        if "SIM-CUST-A" not in existing_cust_codes:
            cust_a = models.Customer(
                account_set_id=account_set_id, name="客户A（金牌）", code="SIM-CUST-A",
                contact="张经理", phone="13800000001",
                credit_limit=Decimal("1000000"), credit_used=Decimal("0"), customer_level="GOLD"
            )
            db.add(cust_a); db.commit(); db.refresh(cust_a)
            created["customers"].append({"id": cust_a.id, "code": cust_a.code, "name": cust_a.name,
                                          "level": "金牌", "credit_limit": "1000000"})
        else:
            created["skipped"].append({"customer_code": "SIM-CUST-A", "reason": "已存在"})

        if "SIM-CUST-B" not in existing_cust_codes:
            cust_b = models.Customer(
                account_set_id=account_set_id, name="客户B（普通）", code="SIM-CUST-B",
                contact="李经理", phone="13800000002",
                credit_limit=Decimal("200000"), credit_used=Decimal("0"), customer_level="NORMAL"
            )
            db.add(cust_b); db.commit(); db.refresh(cust_b)
            created["customers"].append({"id": cust_b.id, "code": cust_b.code, "name": cust_b.name,
                                          "level": "普通", "credit_limit": "200000"})
        else:
            created["skipped"].append({"customer_code": "SIM-CUST-B", "reason": "已存在"})

        # 6. 初始库存：零件X 100个，零件Y 50个
        for mid, code, qty, cost in [(mat_x_id, "SIM-X", 100, Decimal("200")),
                                     (mat_y_id, "SIM-Y", 50, Decimal("100"))]:
            existing_inv = crud.get_batch_inventories(db, account_set_id=account_set_id, material_id=mid)
            if not existing_inv:
                db.add(models.BatchInventory(
                    account_set_id=account_set_id, material_id=mid, batch_no=f"INIT-{code}",
                    location_code="DEFAULT", quantity=qty, unit_cost=cost,
                    total_cost=qty * cost, quality_status="AVAILABLE", inbound_date=datetime.date.today()
                ))
                db.commit()
                created["inventory"].append({"material": code, "quantity": qty, "unit_cost": str(cost)})
            else:
                created["skipped"].append({"inventory_for": code, "reason": "已存在"})

        return make_response(True, {
            "account_set_id": account_set_id,
            "created": created,
            "summary": {
                "materials_count": len(created["materials"]),
                "customers_count": len(created["customers"]),
                "bom_created": created["bom"] is not None,
                "inventory_count": len(created["inventory"])
            }
        }, "模拟教学基础数据初始化完成")
    except Exception as e:
        import traceback
        print(f"[simulation.seed] error: {e}")
        print(traceback.format_exc())
        return make_response(False, None, f"初始化失败: {e}", "50001")


@router.get("/overview", tags=["模拟教学-基础数据"])
def get_simulation_overview(db: Session = Depends(get_db)):
    """获取模拟教学总览：商品（含BOM）、客户、库存"""
    try:
        account_set_id = ensure_account_set(db)

        materials = db.query(models.Material).filter(
            models.Material.account_set_id == account_set_id,
            models.Material.code.like("SIM-%")
        ).all()
        materials_data = []
        for m in materials:
            stock = get_material_stock(db, account_set_id, m.id)
            boms = crud.get_boms(db, account_set_id=account_set_id, product_id=m.id)
            bom_info = None
            if boms:
                bom = boms[0]
                bom_info = [{
                    "material_id": bi.material_id,
                    "material_name": bi.material.name if bi.material else "",
                    "quantity": str(bi.quantity),
                    "unit": bi.unit
                } for bi in bom.items]
            type_text = {"RAW_MATERIAL": "原料", "SEMI_FINISHED": "半成品", "FINISHED_GOODS": "成品"}.get(
                m.type.value if m.type else "RAW_MATERIAL", "原料")
            materials_data.append({
                "id": m.id, "code": m.code, "name": m.name,
                "type": type_text, "unit": m.unit,
                "standard_cost": str(m.unit_price),
                "current_stock": stock,
                "safety_stock": str(m.safety_stock or 0),
                "bom": bom_info
            })

        customers = db.query(models.Customer).filter(
            models.Customer.account_set_id == account_set_id,
            models.Customer.code.like("SIM-CUST-%")
        ).all()
        customers_data = []
        for c in customers:
            level_text = {"GOLD": "金牌", "NORMAL": "普通"}.get(c.customer_level, c.customer_level)
            receivable = get_customer_receivable(db, c.id)
            customers_data.append({
                "id": c.id, "code": c.code, "name": c.name,
                "level": level_text,
                "credit_limit": str(c.credit_limit),
                "credit_used": str(c.credit_used),
                "credit_available": str(Decimal(str(c.credit_limit)) - Decimal(str(c.credit_used))),
                "receivable": str(receivable)
            })

        inventory_data = []
        for m in materials:
            invs = crud.get_batch_inventories(db, account_set_id=account_set_id, material_id=m.id)
            for inv in invs:
                inventory_data.append({
                    "material_code": m.code, "material_name": m.name,
                    "batch_no": inv.batch_no, "location_code": inv.location_code,
                    "quantity": inv.quantity, "unit_cost": str(inv.unit_cost),
                    "quality_status": inv.quality_status
                })

        return make_response(True, {
            "account_set_id": account_set_id,
            "materials": materials_data,
            "customers": customers_data,
            "inventory": inventory_data
        }, "查询成功")
    except Exception as e:
        import traceback
        print(f"[simulation.overview] error: {e}")
        print(traceback.format_exc())
        return make_response(False, None, f"查询失败: {e}", "50001")


# ============================== 模块2：销售订单处理 ==============================

class SimulationSalesOrderItem(BaseModel):
    material_id: int
    quantity: int
    unit_price: Decimal


class SimulationSalesOrderCreate(BaseModel):
    customer_id: int
    items: List[SimulationSalesOrderItem]
    delivery_date: Optional[datetime.date] = None


@router.post("/sales_orders", tags=["模拟教学-销售订单"])
def create_simulation_sales_order(order: SimulationSalesOrderCreate, db: Session = Depends(get_db)):
    """创建销售订单 + 自动执行实时信用检查与实时库存检查，返回弹窗提示内容"""
    try:
        account_set_id = ensure_account_set(db)
        customer = crud.get_customer(db, customer_id=order.customer_id)
        if not customer:
            return make_response(False, None, "客户不存在", "40002")

        total_amount = sum(Decimal(str(item.quantity)) * Decimal(str(item.unit_price)) for item in order.items)

        # ===== 实时信用检查 =====
        current_receivable = get_customer_receivable(db, customer.id)
        credit_check_passed = (Decimal(str(customer.credit_used)) + total_amount) <= Decimal(str(customer.credit_limit))
        credit_check = {
            "passed": credit_check_passed,
            "customer_name": customer.name,
            "customer_level": customer.customer_level,
            "credit_limit": str(customer.credit_limit),
            "credit_used_before": str(customer.credit_used),
            "current_receivable": str(current_receivable),
            "order_amount": str(total_amount),
            "total_after_order": str(Decimal(str(customer.credit_used)) + total_amount),
            "message": (
                f"客户【{customer.name}】当前累计应收账款 {current_receivable}元 + 本单金额 {total_amount}元 "
                f"= {Decimal(str(customer.credit_used)) + total_amount}元，"
                f"{'未超出' if credit_check_passed else '已超出'}信用额度（{customer.credit_limit}元），"
                f"校验{'通过' if credit_check_passed else '未通过'}。"
            )
        }

        # ===== 实时库存检查 =====
        inventory_check_items = []
        all_in_stock = True
        for item in order.items:
            stock = get_material_stock(db, account_set_id, item.material_id)
            shortage = max(0, item.quantity - stock)
            if shortage > 0:
                all_in_stock = False
            material = crud.get_material(db, material_id=item.material_id)
            inventory_check_items.append({
                "material_id": item.material_id,
                "material_name": material.name if material else "",
                "order_qty": item.quantity,
                "current_stock": stock,
                "shortage": shortage,
                "in_stock": shortage == 0
            })

        if all_in_stock:
            inventory_message = "当前订单商品库存充足，可立即发货。"
        else:
            shortage_desc = "、".join([f"{i['material_name']}尚缺{i['shortage']}件"
                                        for i in inventory_check_items if not i['in_stock']])
            inventory_message = f"库存不足：{shortage_desc}，系统将在订单审核后自动触发生产/采购流程。"

        inventory_check = {"passed": all_in_stock, "items": inventory_check_items, "message": inventory_message}

        # ===== 生成订单 =====
        so_no = f"SO-SIM-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        so = models.SalesOrder(
            account_set_id=account_set_id, so_no=so_no, customer_id=customer.id,
            status="PENDING_APPROVAL", credit_check_passed=credit_check_passed,
            delivery_date=order.delivery_date
        )
        db.add(so); db.commit(); db.refresh(so)
        for item in order.items:
            db.add(models.SalesOrderItem(
                sales_order_id=so.id, material_id=item.material_id,
                quantity=item.quantity, unit_price=item.unit_price
            ))
        db.commit(); db.refresh(so)

        return make_response(True, {
            "order": {
                "id": so.id, "so_no": so.so_no,
                "customer_id": customer.id, "customer_name": customer.name,
                "status": so.status, "total_amount": str(total_amount),
                "delivery_date": str(so.delivery_date) if so.delivery_date else None
            },
            "credit_check": credit_check,
            "inventory_check": inventory_check
        }, "订单保存成功，已完成信用检查与库存检查")
    except Exception as e:
        import traceback
        print(f"[simulation.create_sales_order] error: {e}")
        print(traceback.format_exc())
        return make_response(False, None, f"创建订单失败: {e}", "50001")


@router.get("/sales_orders", tags=["模拟教学-销售订单"])
def list_simulation_sales_orders(db: Session = Depends(get_db)):
    """列出所有模拟教学销售订单"""
    try:
        account_set_id = ensure_account_set(db)
        orders = db.query(models.SalesOrder).filter(
            models.SalesOrder.account_set_id == account_set_id,
            models.SalesOrder.so_no.like("SO-SIM-%")
        ).order_by(models.SalesOrder.created_at.desc()).all()

        result = []
        for so in orders:
            total_amount = sum(Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) for i in so.items)
            status_text = {
                "PENDING_APPROVAL": "待审核", "APPROVED": "已审核",
                "IN_PROGRESS": "执行中", "SHIPPED": "已发货", "COMPLETED": "已完成"
            }.get(so.status, so.status)
            result.append({
                "id": so.id, "so_no": so.so_no,
                "customer_id": so.customer_id,
                "customer_name": so.customer.name if so.customer else "",
                "status": so.status, "status_text": status_text,
                "credit_check_passed": so.credit_check_passed,
                "total_amount": str(total_amount),
                "delivery_date": str(so.delivery_date) if so.delivery_date else None,
                "items": [{
                    "material_id": i.material_id,
                    "material_name": i.material.name if i.material else "",
                    "quantity": i.quantity, "unit_price": str(i.unit_price)
                } for i in so.items]
            })
        return make_response(True, result, "查询成功")
    except Exception as e:
        return make_response(False, None, f"查询失败: {e}", "50001")


@router.post("/sales_orders/{sales_order_id}/approve", tags=["模拟教学-销售订单"])
def approve_simulation_sales_order(sales_order_id: int, db: Session = Depends(get_db)):
    """审核销售订单：库存充足→已审核；库存不足→执行中（等待MRP/生产/采购）"""
    try:
        so = crud.get_sales_order(db, sales_order_id=sales_order_id)
        if not so:
            return make_response(False, None, "销售订单不存在", "40002")
        if not so.credit_check_passed:
            return make_response(False, None, "信用检查未通过，无法审核", "40003")

        account_set_id = so.account_set_id
        all_in_stock = True
        for item in so.items:
            stock = get_material_stock(db, account_set_id, item.material_id)
            if stock < item.quantity:
                all_in_stock = False
                break

        if all_in_stock:
            so.status = "APPROVED"
            message = "订单审核通过，库存充足，可执行发货。"
        else:
            so.status = "IN_PROGRESS"
            message = "订单审核通过，但库存不足，已进入执行中状态。请运行MRP生成生产/采购计划。"
        db.commit(); db.refresh(so)
        return make_response(True, {"id": so.id, "so_no": so.so_no, "status": so.status}, message)
    except Exception as e:
        return make_response(False, None, f"审核失败: {e}", "50001")


# ============================== 模块3：MRP运算 ==============================

@router.post("/mrp/run/{sales_order_id}", tags=["模拟教学-MRP运算"])
def run_simulation_mrp(sales_order_id: int, db: Session = Depends(get_db)):
    """对销售订单运行MRP：BOM展开→库存对比→自动生成生产工单+采购申请单"""
    try:
        so = crud.get_sales_order(db, sales_order_id=sales_order_id)
        if not so:
            return make_response(False, None, "销售订单不存在", "40002")
        if so.status not in ["IN_PROGRESS", "APPROVED", "PENDING_APPROVAL"]:
            return make_response(False, None, f"订单状态 {so.status} 无法运行MRP", "40003")

        account_set_id = so.account_set_id
        mrp_run_no = f"MRP-SIM-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        mrp_results = []
        planned_production = []
        planned_purchase = []

        for item in so.items:
            material = crud.get_material(db, material_id=item.material_id)
            if not material:
                continue
            stock = get_material_stock(db, account_set_id, item.material_id)
            net_qty = max(0, item.quantity - stock)

            if net_qty <= 0:
                mrp_results.append({
                    "level": 0, "material_id": item.material_id,
                    "material_name": material.name, "material_type": "成品",
                    "gross_requirement": item.quantity, "on_hand": stock,
                    "net_requirement": 0, "planned_type": "无需生产",
                    "message": f"{material.name} 库存充足（{stock}），无需生产"
                })
                continue

            mrp_results.append({
                "level": 0, "material_id": item.material_id,
                "material_name": material.name, "material_type": "成品",
                "gross_requirement": item.quantity, "on_hand": stock,
                "net_requirement": net_qty, "planned_type": "生产", "planned_qty": net_qty
            })
            planned_production.append({"material_id": item.material_id,
                                        "material_name": material.name, "planned_qty": net_qty})

            # BOM 展开
            boms = crud.get_boms(db, account_set_id=account_set_id, product_id=item.material_id)
            for bom in boms:
                for bi in bom.items:
                    component = crud.get_material(db, material_id=bi.material_id)
                    if not component:
                        continue
                    component_gross = int(Decimal(str(bi.quantity)) * net_qty)
                    component_stock = get_material_stock(db, account_set_id, bi.material_id)
                    component_net = max(0, component_gross - component_stock)

                    if component_net <= 0:
                        mrp_results.append({
                            "level": 1, "material_id": bi.material_id,
                            "material_name": component.name, "material_type": "原料",
                            "parent": material.name,
                            "gross_requirement": component_gross, "on_hand": component_stock,
                            "net_requirement": 0, "planned_type": "库存充足",
                            "message": f"{component.name} 库存充足（{component_stock}），无需采购"
                        })
                    else:
                        mrp_results.append({
                            "level": 1, "material_id": bi.material_id,
                            "material_name": component.name, "material_type": "原料",
                            "parent": material.name,
                            "gross_requirement": component_gross, "on_hand": component_stock,
                            "net_requirement": component_net, "planned_type": "采购",
                            "planned_qty": component_net
                        })
                        planned_purchase.append({
                            "material_id": bi.material_id, "material_name": component.name,
                            "planned_qty": component_net, "unit_cost": Decimal(str(component.unit_price))
                        })

        # ===== 自动生成生产工单 =====
        created_work_orders = []
        for pp in planned_production:
            wo_no = f"WO-SIM-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            wo = models.ProductionWorkOrder(
                account_set_id=account_set_id, work_order_no=wo_no,
                product_id=pp["material_id"], planned_qty=pp["planned_qty"],
                completed_qty=0, in_progress_qty=0,
                status=models.WorkOrderStatus.PLANNED,
                start_date=datetime.date.today(),
                end_date=datetime.date.today() + datetime.timedelta(days=7),
                standard_cost=Decimal("0"), actual_material_cost=Decimal("0"),
                actual_labor_cost=Decimal("0"), actual_overhead_cost=Decimal("0")
            )
            db.add(wo); db.commit(); db.refresh(wo)
            created_work_orders.append({
                "id": wo.id, "work_order_no": wo.work_order_no,
                "product_name": pp["material_name"], "planned_qty": wo.planned_qty,
                "status": wo.status.value if wo.status else "PLANNED"
            })

        # ===== 自动生成采购申请单 =====
        created_purchase_requests = []
        for pp in planned_purchase:
            pr_no = f"PR-SIM-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            pr = models.PurchaseRequest(
                account_set_id=account_set_id, request_no=pr_no,
                material_id=pp["material_id"], requested_qty=pp["planned_qty"],
                required_date=datetime.date.today() + datetime.timedelta(days=3),
                status="PENDING"
            )
            db.add(pr); db.commit(); db.refresh(pr)
            created_purchase_requests.append({
                "id": pr.id, "request_no": pr.request_no,
                "material_name": pp["material_name"], "requested_qty": pr.requested_qty,
                "unit_cost": str(pp["unit_cost"]),
                "total_amount": str(pp["planned_qty"] * pp["unit_cost"]),
                "status": pr.status
            })

        if so.status == "PENDING_APPROVAL":
            so.status = "IN_PROGRESS"
        db.commit()

        return make_response(True, {
            "mrp_run_no": mrp_run_no,
            "sales_order_id": so.id, "sales_order_no": so.so_no,
            "mrp_results": mrp_results,
            "summary": {
                "total_results": len(mrp_results),
                "production_plans": len(planned_production),
                "purchase_plans": len(planned_purchase)
            },
            "created_work_orders": created_work_orders,
            "created_purchase_requests": created_purchase_requests
        }, "MRP运算完成，已自动生成生产工单和采购申请单")
    except Exception as e:
        import traceback
        print(f"[simulation.run_mrp] error: {e}")
        print(traceback.format_exc())
        return make_response(False, None, f"MRP运算失败: {e}", "50001")


# ============================== 模块4：采购与入库 ==============================

@router.get("/purchase_requests", tags=["模拟教学-采购管理"])
def list_simulation_purchase_requests(db: Session = Depends(get_db)):
    """列出所有模拟教学采购申请单"""
    try:
        account_set_id = ensure_account_set(db)
        prs = db.query(models.PurchaseRequest).filter(
            models.PurchaseRequest.account_set_id == account_set_id,
            models.PurchaseRequest.request_no.like("PR-SIM-%")
        ).order_by(models.PurchaseRequest.created_at.desc()).all()
        result = []
        for pr in prs:
            material = crud.get_material(db, material_id=pr.material_id)
            status_text = {"PENDING": "待下单", "ORDERED": "已下单", "COMPLETED": "已完成"}.get(pr.status, pr.status)
            result.append({
                "id": pr.id, "request_no": pr.request_no,
                "material_id": pr.material_id,
                "material_name": material.name if material else "",
                "material_code": material.code if material else "",
                "requested_qty": pr.requested_qty,
                "required_date": str(pr.required_date) if pr.required_date else None,
                "status": pr.status, "status_text": status_text,
                "unit_cost": str(material.unit_price) if material else "0"
            })
        return make_response(True, result, "查询成功")
    except Exception as e:
        return make_response(False, None, f"查询失败: {e}", "50001")


@router.post("/purchase_requests/{request_id}/create_po", tags=["模拟教学-采购管理"])
def create_po_from_request(request_id: int, db: Session = Depends(get_db)):
    """根据采购申请单向供应商下单：生成采购订单"""
    try:
        pr = db.query(models.PurchaseRequest).filter(models.PurchaseRequest.id == request_id).first()
        if not pr:
            return make_response(False, None, "采购申请单不存在", "40002")

        account_set_id = pr.account_set_id
        material = crud.get_material(db, material_id=pr.material_id)
        if not material:
            return make_response(False, None, "物料不存在", "40002")

        # 查找或创建默认供应商
        supplier = db.query(models.Supplier).filter(
            models.Supplier.account_set_id == account_set_id,
            models.Supplier.code == "SIM-SUP-DEFAULT"
        ).first()
        if not supplier:
            supplier = models.Supplier(
                account_set_id=account_set_id, name="模拟教学默认供应商",
                code="SIM-SUP-DEFAULT", contact="供应商客服", phone="13900000000"
            )
            db.add(supplier); db.commit(); db.refresh(supplier)

        po_no = f"PO-SIM-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        po = models.PurchaseOrder(
            account_set_id=account_set_id, po_no=po_no, supplier_id=supplier.id,
            status="PENDING", approval_status=models.ApprovalStatus.APPROVED, tax_rate=Decimal("13")
        )
        db.add(po); db.commit(); db.refresh(po)

        db.add(models.PurchaseOrderItem(
            purchase_order_id=po.id, material_id=pr.material_id,
            quantity=pr.requested_qty, unit_price=material.unit_price
        ))
        db.commit(); db.refresh(po)

        pr.status = "ORDERED"
        db.commit()

        total_amount = Decimal(str(pr.requested_qty)) * Decimal(str(material.unit_price))
        return make_response(True, {
            "po_id": po.id, "po_no": po.po_no,
            "supplier_id": supplier.id, "supplier_name": supplier.name,
            "material_id": pr.material_id, "material_name": material.name,
            "quantity": pr.requested_qty, "unit_price": str(material.unit_price),
            "total_amount": str(total_amount), "status": po.status
        }, "采购订单创建成功")
    except Exception as e:
        import traceback
        print(f"[simulation.create_po] error: {e}")
        print(traceback.format_exc())
        return make_response(False, None, f"创建采购订单失败: {e}", "50001")


@router.get("/purchase_orders", tags=["模拟教学-采购管理"])
def list_simulation_purchase_orders(db: Session = Depends(get_db)):
    """列出所有模拟教学采购订单"""
    try:
        account_set_id = ensure_account_set(db)
        pos = db.query(models.PurchaseOrder).filter(
            models.PurchaseOrder.account_set_id == account_set_id,
            models.PurchaseOrder.po_no.like("PO-SIM-%")
        ).order_by(models.PurchaseOrder.created_at.desc()).all()
        result = []
        for po in pos:
            total = sum(Decimal(str(i.quantity)) * Decimal(str(i.unit_price)) for i in po.items)
            status_text = {"PENDING": "待入库", "INBOUND": "已入库",
                           "COMPLETED": "已完成"}.get(po.status, po.status)
            result.append({
                "id": po.id, "po_no": po.po_no,
                "supplier_id": po.supplier_id,
                "supplier_name": po.supplier.name if po.supplier else "",
                "status": po.status, "status_text": status_text,
                "total_amount": str(total),
                "items": [{
                    "material_id": i.material_id,
                    "material_name": i.material.name if i.material else "",
                    "quantity": i.quantity, "unit_price": str(i.unit_price)
                } for i in po.items]
            })
        return make_response(True, result, "查询成功")
    except Exception as e:
        return make_response(False, None, f"查询失败: {e}", "50001")


@router.post("/purchase_orders/{po_id}/inbound", tags=["模拟教学-采购管理"])
def simulate_inbound(po_id: int, db: Session = Depends(get_db)):
    """模拟入库：更新库存 + 自动生成应付账款凭证"""
    try:
        po = crud.get_purchase_order(db, order_id=po_id)
        if not po:
            return make_response(False, None, "采购订单不存在", "40002")
        if po.status == "COMPLETED":
            return make_response(False, None, "采购订单已入库，请勿重复操作", "40003")

        account_set_id = po.account_set_id
        inbound_no = f"IN-SIM-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        inbound_order = models.InboundOrder(
            account_set_id=account_set_id, inbound_no=inbound_no,
            purchase_order_id=po.id, supplier_id=po.supplier_id,
            inbound_date=datetime.date.today(), status="COMPLETED",
            quality_status="PASS", operator="模拟教学系统"
        )
        db.add(inbound_order); db.commit(); db.refresh(inbound_order)

        total_amount = Decimal("0")
        inbound_items = []
        for po_item in po.items:
            material = crud.get_material(db, material_id=po_item.material_id)
            batch_no = f"INB-{po_item.material_id}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            db.add(models.InboundOrderItem(
                inbound_order_id=inbound_order.id, material_id=po_item.material_id,
                batch_no=batch_no, location_code="DEFAULT",
                quantity=po_item.quantity, unit_price=po_item.unit_price, quality_status="PASS"
            ))
            db.add(models.BatchInventory(
                account_set_id=account_set_id, material_id=po_item.material_id,
                batch_no=batch_no, location_code="DEFAULT",
                quantity=po_item.quantity, unit_cost=po_item.unit_price,
                total_cost=Decimal(str(po_item.quantity)) * Decimal(str(po_item.unit_price)),
                quality_status="AVAILABLE", supplier_id=po.supplier_id,
                purchase_order_id=po.id, inbound_date=datetime.date.today()
            ))
            item_amount = Decimal(str(po_item.quantity)) * Decimal(str(po_item.unit_price))
            total_amount += item_amount
            inbound_items.append({
                "material_id": po_item.material_id,
                "material_name": material.name if material else "",
                "quantity": po_item.quantity, "unit_price": str(po_item.unit_price),
                "batch_no": batch_no
            })

        po.status = "COMPLETED"
        db.commit()

        # ===== 应付账款凭证：借 库存商品/进项税额，贷 应付账款 =====
        tax_rate = Decimal(str(po.tax_rate or 0)) / Decimal("100")
        tax_amount = total_amount * tax_rate
        total_payable = total_amount + tax_amount

        voucher = create_voucher_with_entries(
            db, account_set_id, "PURCHASE", reference_doc=po.po_no,
            entries_data=[
                {"account_code": "1403", "account_name": "库存商品", "debit": total_amount,
                 "summary": f"采购入库 {po.po_no}",
                 "material_id": po.items[0].material_id if po.items else None},
                {"account_code": "22210101", "account_name": "应交税费-应交增值税-进项税额",
                 "debit": tax_amount, "summary": f"进项税额 {po.po_no}"},
                {"account_code": "2202", "account_name": "应付账款", "credit": total_payable,
                 "summary": f"应付货款 {po.po_no}", "supplier_id": po.supplier_id}
            ]
        )

        return make_response(True, {
            "inbound_no": inbound_no, "po_no": po.po_no,
            "total_amount": str(total_amount), "tax_amount": str(tax_amount),
            "total_payable": str(total_payable), "items": inbound_items,
            "voucher_no": voucher.voucher_no,
            "finance_message": f"应付账款增加 {total_payable}元（含税），已自动生成凭证 {voucher.voucher_no}"
        }, "入库成功，库存已更新，应付账款已记账")
    except Exception as e:
        import traceback
        print(f"[simulation.inbound] error: {e}")
        print(traceback.format_exc())
        return make_response(False, None, f"入库失败: {e}", "50001")


# ============================== 模块5：生产、发货与财务集成 ==============================

@router.get("/work_orders", tags=["模拟教学-生产管理"])
def list_simulation_work_orders(db: Session = Depends(get_db)):
    """列出所有模拟教学生产工单"""
    try:
        account_set_id = ensure_account_set(db)
        wos = db.query(models.ProductionWorkOrder).filter(
            models.ProductionWorkOrder.account_set_id == account_set_id,
            models.ProductionWorkOrder.work_order_no.like("WO-SIM-%")
        ).order_by(models.ProductionWorkOrder.created_at.desc()).all()
        result = []
        for wo in wos:
            boms = crud.get_boms(db, account_set_id=account_set_id, product_id=wo.product_id)
            required_materials = []
            if boms:
                bom = boms[0]
                for bi in bom.items:
                    comp = crud.get_material(db, material_id=bi.material_id)
                    required_materials.append({
                        "material_id": bi.material_id,
                        "material_name": comp.name if comp else "",
                        "required_per_unit": str(bi.quantity),
                        "total_required": int(Decimal(str(bi.quantity)) * wo.planned_qty),
                        "current_stock": get_material_stock(db, account_set_id, bi.material_id)
                    })
            status_text = {"PLANNED": "已计划", "IN_PROGRESS": "生产中",
                           "COMPLETED": "已完工", "CANCELLED": "已取消"}.get(
                wo.status.value if wo.status else "PLANNED", "已计划")
            result.append({
                "id": wo.id, "work_order_no": wo.work_order_no,
                "product_id": wo.product_id,
                "product_name": wo.product.name if wo.product else "",
                "planned_qty": wo.planned_qty, "completed_qty": wo.completed_qty,
                "status": wo.status.value if wo.status else "PLANNED",
                "status_text": status_text,
                "required_materials": required_materials
            })
        return make_response(True, result, "查询成功")
    except Exception as e:
        return make_response(False, None, f"查询失败: {e}", "50001")


@router.post("/work_orders/{wo_id}/pick_materials", tags=["模拟教学-生产管理"])
def simulate_pick_materials(wo_id: int, db: Session = Depends(get_db)):
    """模拟生产领料：扣减零件X和Y的库存"""
    try:
        wo = crud.get_workorder(db, workorder_id=wo_id)
        if not wo:
            return make_response(False, None, "生产工单不存在", "40002")
        if wo.status != models.WorkOrderStatus.PLANNED:
            return make_response(False, None, f"工单状态 {wo.status.value} 无法领料", "40003")

        account_set_id = wo.account_set_id
        boms = crud.get_boms(db, account_set_id=account_set_id, product_id=wo.product_id)
        if not boms:
            return make_response(False, None, "产品未配置BOM", "40003")
        bom = boms[0]

        picked_items = []
        total_cost = Decimal("0")
        for bi in bom.items:
            needed = int(Decimal(str(bi.quantity)) * wo.planned_qty)
            invs = crud.get_batch_inventories(db, account_set_id=account_set_id, material_id=bi.material_id)
            invs = [i for i in invs if i.quality_status == "AVAILABLE" and i.quantity > 0]
            invs.sort(key=lambda x: x.inbound_date or datetime.date.min)

            remaining = needed
            for inv in invs:
                if remaining <= 0:
                    break
                use = min(inv.quantity, remaining)
                crud.update_batch_inventory(db, inv.id, inv.quantity - use)
                total_cost += Decimal(str(use)) * Decimal(str(inv.unit_cost))
                remaining -= use

            comp = crud.get_material(db, material_id=bi.material_id)
            picked_items.append({
                "material_id": bi.material_id,
                "material_name": comp.name if comp else "",
                "needed": needed, "picked": needed - remaining, "shortage": remaining
            })

        wo.status = models.WorkOrderStatus.IN_PROGRESS
        wo.in_progress_qty = wo.planned_qty
        wo.actual_material_cost = total_cost
        db.commit(); db.refresh(wo)

        return make_response(True, {
            "work_order_no": wo.work_order_no,
            "picked_items": picked_items,
            "total_material_cost": str(total_cost),
            "status": wo.status.value
        }, "领料完成，工单进入生产中状态")
    except Exception as e:
        import traceback
        print(f"[simulation.pick_materials] error: {e}")
        print(traceback.format_exc())
        return make_response(False, None, f"领料失败: {e}", "50001")


@router.post("/work_orders/{wo_id}/complete", tags=["模拟教学-生产管理"])
def simulate_complete_production(wo_id: int, db: Session = Depends(get_db)):
    """模拟完工入库：增加成品库存 + 自动生成生产成本结转凭证"""
    try:
        wo = crud.get_workorder(db, workorder_id=wo_id)
        if not wo:
            return make_response(False, None, "生产工单不存在", "40002")
        if wo.status != models.WorkOrderStatus.IN_PROGRESS:
            return make_response(False, None, f"工单状态 {wo.status.value} 无法完工", "40003")

        account_set_id = wo.account_set_id
        product = crud.get_material(db, material_id=wo.product_id)

        batch_no = f"FIN-{wo.id}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        db.add(models.BatchInventory(
            account_set_id=account_set_id, material_id=wo.product_id,
            batch_no=batch_no, location_code="DEFAULT", quantity=wo.planned_qty,
            unit_cost=wo.actual_material_cost / wo.planned_qty if wo.planned_qty > 0 else Decimal("0"),
            total_cost=wo.actual_material_cost, quality_status="AVAILABLE",
            inbound_date=datetime.date.today()
        ))

        wo.completed_qty = wo.planned_qty
        wo.in_progress_qty = 0
        wo.completion_ratio = Decimal("100.00")
        wo.status = models.WorkOrderStatus.COMPLETED
        db.commit(); db.refresh(wo)

        # 完工入库凭证：借 库存商品，贷 生产成本-直接材料
        voucher = create_voucher_with_entries(
            db, account_set_id, "GENERAL", reference_doc=wo.work_order_no,
            entries_data=[
                {"account_code": "1403", "account_name": "库存商品", "debit": wo.actual_material_cost,
                 "summary": f"完工入库 {wo.work_order_no}", "material_id": wo.product_id},
                {"account_code": "5001", "account_name": "生产成本-直接材料",
                 "credit": wo.actual_material_cost, "summary": f"结转材料成本 {wo.work_order_no}"}
            ]
        )

        return make_response(True, {
            "work_order_no": wo.work_order_no,
            "product_name": product.name if product else "",
            "completed_qty": wo.completed_qty, "batch_no": batch_no,
            "material_cost": str(wo.actual_material_cost),
            "voucher_no": voucher.voucher_no,
            "finance_message": f"成品入库 {wo.completed_qty} 台，材料成本 {wo.actual_material_cost}元已结转，凭证号 {voucher.voucher_no}"
        }, "完工入库成功，成品库存已增加，成本已结转")
    except Exception as e:
        import traceback
        print(f"[simulation.complete_production] error: {e}")
        print(traceback.format_exc())
        return make_response(False, None, f"完工入库失败: {e}", "50001")


@router.post("/sales_orders/{sales_order_id}/ship", tags=["模拟教学-销售发货"])
def simulate_ship_sales_order(sales_order_id: int, db: Session = Depends(get_db)):
    """模拟销售发货：扣减成品库存 + 生成出库单 + 自动生成收入确认/成本结转凭证"""
    try:
        so = crud.get_sales_order(db, sales_order_id=sales_order_id)
        if not so:
            return make_response(False, None, "销售订单不存在", "40002")
        if so.status in ["SHIPPED", "COMPLETED"]:
            return make_response(False, None, "订单已发货，请勿重复操作", "40003")

        account_set_id = so.account_set_id

        # 检查并扣减成品库存
        shipped_items = []
        total_revenue = Decimal("0")
        total_cost = Decimal("0")
        for item in so.items:
            stock = get_material_stock(db, account_set_id, item.material_id)
            if stock < item.quantity:
                material = crud.get_material(db, material_id=item.material_id)
                return make_response(False, None,
                    f"{material.name if material else ''} 库存不足（{stock}），无法发货", "40003")

            invs = crud.get_batch_inventories(db, account_set_id=account_set_id, material_id=item.material_id)
            invs = [i for i in invs if i.quality_status == "AVAILABLE" and i.quantity > 0]
            invs.sort(key=lambda x: x.inbound_date or datetime.date.min)

            remaining = item.quantity
            for inv in invs:
                if remaining <= 0:
                    break
                use = min(inv.quantity, remaining)
                crud.update_batch_inventory(db, inv.id, inv.quantity - use)
                total_cost += Decimal(str(use)) * Decimal(str(inv.unit_cost))
                remaining -= use

            shipped_items.append({
                "material_id": item.material_id,
                "material_name": item.material.name if item.material else "",
                "quantity": item.quantity, "unit_price": str(item.unit_price)
            })
            total_revenue += Decimal(str(item.quantity)) * Decimal(str(item.unit_price))

        # 生成出库单
        outbound_no = f"OUT-SIM-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        outbound = models.OutboundOrder(
            account_set_id=account_set_id, outbound_no=outbound_no,
            outbound_type="SALES", source_order_id=so.id, source_order_no=so.so_no,
            customer_id=so.customer_id, outbound_date=datetime.date.today(),
            status="COMPLETED", operator="模拟教学系统"
        )
        db.add(outbound); db.commit(); db.refresh(outbound)

        # 生成发货单
        delivery_no = f"DN-SIM-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        delivery_note = models.DeliveryNote(
            account_set_id=account_set_id, delivery_no=delivery_no,
            sales_order_id=so.id, customer_id=so.customer_id,
            delivery_date=datetime.date.today(), status="CONFIRMED", operator="模拟教学系统"
        )
        db.add(delivery_note); db.commit(); db.refresh(delivery_note)

        so.status = "SHIPPED"
        db.commit()

        # ===== 收入确认凭证：借 应收账款，贷 主营业务收入 + 销项税额 =====
        tax_rate = Decimal("13") / Decimal("100")
        tax_amount = total_revenue * tax_rate
        total_receivable = total_revenue + tax_amount

        voucher_revenue = create_voucher_with_entries(
            db, account_set_id, "SALE", reference_doc=so.so_no,
            entries_data=[
                {"account_code": "1122", "account_name": "应收账款", "debit": total_receivable,
                 "summary": f"销售货款 {so.so_no}", "customer_id": so.customer_id},
                {"account_code": "6001", "account_name": "主营业务收入", "credit": total_revenue,
                 "summary": f"销售收入 {so.so_no}"},
                {"account_code": "22210102", "account_name": "应交税费-应交增值税-销项税额",
                 "credit": tax_amount, "summary": f"销项税额 {so.so_no}"}
            ]
        )

        # ===== 成本结转凭证：借 主营业务成本，贷 库存商品 =====
        voucher_cost = create_voucher_with_entries(
            db, account_set_id, "GENERAL", reference_doc=so.so_no,
            entries_data=[
                {"account_code": "6401", "account_name": "主营业务成本", "debit": total_cost,
                 "summary": f"结转销售成本 {so.so_no}"},
                {"account_code": "1403", "account_name": "库存商品", "credit": total_cost,
                 "summary": f"销售出库 {so.so_no}",
                 "material_id": so.items[0].material_id if so.items else None}
            ]
        )

        return make_response(True, {
            "sales_order_no": so.so_no, "delivery_no": delivery_no,
            "outbound_no": outbound_no, "shipped_items": shipped_items,
            "total_revenue": str(total_revenue), "tax_amount": str(tax_amount),
            "total_receivable": str(total_receivable), "total_cost": str(total_cost),
            "gross_profit": str(total_revenue - total_cost),
            "revenue_voucher_no": voucher_revenue.voucher_no,
            "cost_voucher_no": voucher_cost.voucher_no,
            "finance_message": (
                f"销售发货完成。应收账款增加 {total_receivable}元（含税）；"
                f"主营业务收入 {total_revenue}元；主营业务成本 {total_cost}元；"
                f"毛利 {total_revenue - total_cost}元。"
                f"已自动生成凭证 {voucher_revenue.voucher_no} 和 {voucher_cost.voucher_no}。"
            )
        }, "发货成功，库存已扣减，收入与成本已记账")
    except Exception as e:
        import traceback
        print(f"[simulation.ship] error: {e}")
        print(traceback.format_exc())
        return make_response(False, None, f"发货失败: {e}", "50001")


# ============================== 财务总览 ==============================

@router.get("/finance_overview", tags=["模拟教学-财务总览"])
def get_simulation_finance_overview(db: Session = Depends(get_db)):
    """财务总览：应收账款、应付账款、主营业务收入、主营业务成本、毛利、库存价值、凭证列表"""
    try:
        account_set_id = ensure_account_set(db)

        entries = db.query(models.VoucherEntry).join(models.VoucherDB).filter(
            models.VoucherDB.account_set_id == account_set_id
        ).all()

        def sum_account(code_prefix):
            debit = sum(Decimal(str(e.debit or 0)) for e in entries if e.account_code.startswith(code_prefix))
            credit = sum(Decimal(str(e.credit or 0)) for e in entries if e.account_code.startswith(code_prefix))
            return debit, credit, debit - credit

        ar_d, ar_c, _ = sum_account("1122")  # 应收账款
        ap_d, ap_c, _ = sum_account("2202")  # 应付账款
        _, rev_c, _ = sum_account("6001")    # 主营业务收入（贷方）
        cost_d, _, _ = sum_account("6401")    # 主营业务成本（借方）
        _, tax_in_c, _ = sum_account("22210101")  # 进项税额（贷方）
        _, tax_out_c, _ = sum_account("22210102")  # 销项税额（贷方）

        gross_profit = rev_c - cost_d

        # 库存价值（按当前批次库存计算）
        inventory_value = Decimal("0")
        invs = db.query(models.BatchInventory).filter(
            models.BatchInventory.account_set_id == account_set_id,
            models.BatchInventory.quality_status == "AVAILABLE"
        ).all()
        for inv in invs:
            inventory_value += Decimal(str(inv.quantity)) * Decimal(str(inv.unit_cost))

        # 各客户应收账款明细
        customer_ar = []
        customers = db.query(models.Customer).filter(
            models.Customer.account_set_id == account_set_id,
            models.Customer.code.like("SIM-CUST-%")
        ).all()
        for c in customers:
            ar = get_customer_receivable(db, c.id)
            customer_ar.append({"id": c.id, "name": c.name, "receivable": str(ar)})

        # 最近凭证列表
        recent_vouchers = db.query(models.VoucherDB).filter(
            models.VoucherDB.account_set_id == account_set_id
        ).order_by(models.VoucherDB.created_at.desc()).limit(20).all()
        vouchers_data = [{
            "voucher_no": v.voucher_no,
            "voucher_type": v.voucher_type.value if v.voucher_type else "",
            "voucher_date": str(v.voucher_date) if v.voucher_date else None,
            "reference_doc": v.reference_doc,
            "status": v.status.value if v.status else "",
            "entries": [{
                "account_code": e.account_code,
                "account_name": e.account_name,
                "debit": str(e.debit or 0),
                "credit": str(e.credit or 0),
                "summary": e.summary
            } for e in v.entries]
        } for v in recent_vouchers]

        return make_response(True, {
            "summary": {
                "accounts_receivable": str(ar_d - ar_c),  # 应收账款余额（借-贷）
                "accounts_payable": str(ap_c - ap_d),    # 应付账款余额（贷-借）
                "revenue": str(rev_c),
                "cost": str(cost_d),
                "gross_profit": str(gross_profit),
                "inventory_value": str(inventory_value),
                "input_tax": str(tax_in_c),
                "output_tax": str(tax_out_c),
                "net_tax": str(tax_out_c - tax_in_c)
            },
            "customer_ar": customer_ar,
            "recent_vouchers": vouchers_data
        }, "查询成功")
    except Exception as e:
        import traceback
        print(f"[simulation.finance_overview] error: {e}")
        print(traceback.format_exc())
        return make_response(False, None, f"查询失败: {e}", "50001")
