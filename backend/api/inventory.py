from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime

from .. import crud, schemas, models
from ..database import get_db
from ..app import make_response

router = APIRouter()

CVA_CLASSIFICATION = {"S": "关键", "A": "重要", "B": "一般", "C": "不重要"}
ABC_CLASSIFICATION = {"A": "高价值", "B": "中等价值", "C": "低价值"}

CLASSIFICATION_COEFFICIENTS = {
    "A-S": {"safety_stock_factor": 1.5, "alert_level": "HIGH", "replenish_frequency": "DAILY"},
    "A-A": {"safety_stock_factor": 1.2, "alert_level": "HIGH", "replenish_frequency": "DAILY"},
    "A-B": {"safety_stock_factor": 1.0, "alert_level": "MEDIUM", "replenish_frequency": "WEEKLY"},
    "A-C": {"safety_stock_factor": 0.8, "alert_level": "MEDIUM", "replenish_frequency": "WEEKLY"},
    "B-S": {"safety_stock_factor": 1.2, "alert_level": "HIGH", "replenish_frequency": "WEEKLY"},
    "B-A": {"safety_stock_factor": 1.0, "alert_level": "MEDIUM", "replenish_frequency": "WEEKLY"},
    "B-B": {"safety_stock_factor": 0.8, "alert_level": "MEDIUM", "replenish_frequency": "BIWEEKLY"},
    "B-C": {"safety_stock_factor": 0.6, "alert_level": "LOW", "replenish_frequency": "BIWEEKLY"},
    "C-S": {"safety_stock_factor": 1.0, "alert_level": "MEDIUM", "replenish_frequency": "BIWEEKLY"},
    "C-A": {"safety_stock_factor": 0.8, "alert_level": "MEDIUM", "replenish_frequency": "MONTHLY"},
    "C-B": {"safety_stock_factor": 0.5, "alert_level": "LOW", "replenish_frequency": "MONTHLY"},
    "C-C": {"safety_stock_factor": 0.3, "alert_level": "LOW", "replenish_frequency": "QUARTERLY"}
}

def generate_batch_no(db: Session, account_set_id: int, material_id: int, supplier_id: int = None, po_no: str = None):
    rules = crud.get_batch_rules(db, account_set_id=account_set_id)
    active_rule = next((r for r in rules if r.is_active), None)
    
    if not active_rule:
        pattern = "{material_code}{date}{seq}"
    else:
        pattern = active_rule.rule_pattern
    
    material = crud.get_material(db, material_id=material_id)
    material_code = material.code if material else "MAT"
    
    today = datetime.date.today().strftime("%Y%m%d")
    
    seq = db.query(models.BatchInventory).filter(
        models.BatchInventory.account_set_id == account_set_id,
        models.BatchInventory.batch_no.like(f"{material_code}{today}%")
    ).count() + 1
    
    supplier = crud.get_supplier(db, supplier_id=supplier_id) if supplier_id else None
    supplier_code = supplier.code if supplier else ""
    
    batch_no = pattern.format(
        material_code=material_code,
        date=today,
        seq=f"{seq:04d}",
        supplier_code=supplier_code,
        po_no=po_no or ""
    )
    
    return batch_no[:50]

@router.get("/batch-rules", tags=["基础数据管理"])
def get_batch_rules(account_set_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    rules = crud.get_batch_rules(db, account_set_id=account_set_id, skip=skip, limit=limit)
    return make_response(True, rules, "查询成功")

@router.post("/batch-rules", tags=["基础数据管理"])
def create_batch_rule(rule: schemas.BatchRuleCreate, db: Session = Depends(get_db)):
    created = crud.create_batch_rule(db, rule)
    return make_response(True, created, "创建成功")

@router.put("/batch-rules/{rule_id}", tags=["基础数据管理"])
def update_batch_rule(rule_id: int, rule: schemas.BatchRuleCreate, db: Session = Depends(get_db)):
    updated = crud.update_batch_rule(db, rule_id, rule)
    if not updated:
        return make_response(False, None, "批次规则不存在", "40002")
    return make_response(True, updated, "更新成功")

@router.delete("/batch-rules/{rule_id}", tags=["基础数据管理"])
def delete_batch_rule(rule_id: int, db: Session = Depends(get_db)):
    success = crud.delete_batch_rule(db, rule_id)
    if not success:
        return make_response(False, None, "批次规则不存在", "40002")
    return make_response(True, None, "删除成功")

@router.get("/storage-locations", tags=["基础数据管理"])
def get_storage_locations(account_set_id: Optional[int] = None, parent_code: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    locations = crud.get_storage_locations(db, account_set_id=account_set_id, parent_code=parent_code, skip=skip, limit=limit)
    return make_response(True, locations, "查询成功")

@router.post("/storage-locations", tags=["基础数据管理"])
def create_storage_location(location: schemas.StorageLocationCreate, db: Session = Depends(get_db)):
    existing = crud.get_storage_location_by_code(db, location.location_code)
    if existing:
        return make_response(False, None, "库位编码已存在", "40003")
    created = crud.create_storage_location(db, location)
    return make_response(True, created, "创建成功")

@router.put("/storage-locations/{location_id}", tags=["基础数据管理"])
def update_storage_location(location_id: int, location: schemas.StorageLocationCreate, db: Session = Depends(get_db)):
    updated = crud.update_storage_location(db, location_id, location)
    if not updated:
        return make_response(False, None, "库位不存在", "40002")
    return make_response(True, updated, "更新成功")

@router.delete("/storage-locations/{location_id}", tags=["基础数据管理"])
def delete_storage_location(location_id: int, db: Session = Depends(get_db)):
    success = crud.delete_storage_location(db, location_id)
    if not success:
        return make_response(False, None, "库位不存在", "40002")
    return make_response(True, None, "删除成功")

@router.get("/unit-conversions", tags=["基础数据管理"])
def get_unit_conversions(account_set_id: Optional[int] = None, material_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    conversions = crud.get_unit_conversions(db, account_set_id=account_set_id, material_id=material_id, skip=skip, limit=limit)
    return make_response(True, conversions, "查询成功")

@router.post("/unit-conversions", tags=["基础数据管理"])
def create_unit_conversion(conversion: schemas.UnitConversionCreate, db: Session = Depends(get_db)):
    created = crud.create_unit_conversion(db, conversion)
    return make_response(True, created, "创建成功")

@router.delete("/unit-conversions/{conversion_id}", tags=["基础数据管理"])
def delete_unit_conversion(conversion_id: int, db: Session = Depends(get_db)):
    success = crud.delete_unit_conversion(db, conversion_id)
    if not success:
        return make_response(False, None, "单位换算不存在", "40002")
    return make_response(True, None, "删除成功")

@router.get("/purchase-agreements", tags=["基础数据管理"])
def get_purchase_agreements(account_set_id: Optional[int] = None, supplier_id: Optional[int] = None, material_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    agreements = crud.get_purchase_agreements(db, account_set_id=account_set_id, supplier_id=supplier_id, material_id=material_id, skip=skip, limit=limit)
    return make_response(True, agreements, "查询成功")

@router.post("/purchase-agreements", tags=["基础数据管理"])
def create_purchase_agreement(agreement: schemas.PurchaseAgreementCreate, db: Session = Depends(get_db)):
    existing = crud.get_purchase_agreement_by_no(db, agreement.agreement_no)
    if existing:
        return make_response(False, None, "协议编号已存在", "40003")
    created = crud.create_purchase_agreement(db, agreement)
    return make_response(True, created, "创建成功")

@router.put("/purchase-agreements/{agreement_id}", tags=["基础数据管理"])
def update_purchase_agreement(agreement_id: int, agreement: schemas.PurchaseAgreementCreate, db: Session = Depends(get_db)):
    updated = crud.update_purchase_agreement(db, agreement_id, agreement)
    if not updated:
        return make_response(False, None, "采购协议不存在", "40002")
    return make_response(True, updated, "更新成功")

@router.delete("/purchase-agreements/{agreement_id}", tags=["基础数据管理"])
def delete_purchase_agreement(agreement_id: int, db: Session = Depends(get_db)):
    success = crud.delete_purchase_agreement(db, agreement_id)
    if not success:
        return make_response(False, None, "采购协议不存在", "40002")
    return make_response(True, None, "删除成功")

@router.get("/pre-receipts", tags=["入库管理"])
def get_pre_receipts(account_set_id: Optional[int] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    receipts = crud.get_pre_receipts(db, account_set_id=account_set_id, status=status, skip=skip, limit=limit)
    return make_response(True, receipts, "查询成功")

@router.post("/pre-receipts", tags=["入库管理"])
def create_pre_receipt(receipt: schemas.PreReceiptCreate, db: Session = Depends(get_db)):
    pre_receipt_no = f"PR-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    receipt_data = schemas.PreReceiptCreate(
        **receipt.dict(),
        pre_receipt_no=pre_receipt_no,
        status="PENDING"
    )
    created = crud.create_pre_receipt(db, receipt_data)
    return make_response(True, created, "预入库单创建成功")

@router.put("/pre-receipts/{pre_receipt_id}/arrive", tags=["入库管理"])
def confirm_arrival(pre_receipt_id: int, actual_arrival_date: datetime.date, items: List[dict], db: Session = Depends(get_db)):
    pre_receipt = crud.get_pre_receipt(db, pre_receipt_id=pre_receipt_id)
    if not pre_receipt:
        return make_response(False, None, "预入库单不存在", "40002")
    
    pre_receipt.actual_arrival_date = actual_arrival_date
    pre_receipt.status = "ARRIVED"
    db.commit()
    
    return make_response(True, pre_receipt, "到货登记完成")

@router.post("/quick-inbound", tags=["入库管理"])
def quick_inbound(quick_inbound_data: dict, db: Session = Depends(get_db)):
    account_set_id = quick_inbound_data.get('account_set_id', 1)
    items = quick_inbound_data.get('items', [])

    if not items:
        return make_response(False, None, "请提供入库物料", "40001")

    inbound_no = f"IN-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

    inbound_order = models.InboundOrder(
        account_set_id=account_set_id,
        inbound_no=inbound_no,
        inbound_date=datetime.date.today(),
        status="COMPLETED",
        quality_status="PASS"
    )
    db.add(inbound_order)
    db.commit()
    db.refresh(inbound_order)

    total_qty = 0
    total_amount = 0
    result_items = []

    for item_data in items:
        material_id = item_data.get('material_id')
        quantity = item_data.get('quantity', 1)
        unit_price = item_data.get('unit_price', 0)

        if not material_id:
            continue

        material = crud.get_material(db, material_id=material_id)
        if not material:
            continue

        batch_no = generate_batch_no(db, account_set_id, material_id)
        expiry_date = None
        if material.shelf_life_days:
            expiry_date = datetime.date.today() + datetime.timedelta(days=material.shelf_life_days)

        # 创建入库子项
        inbound_item = models.InboundOrderItem(
            inbound_order_id=inbound_order.id,
            material_id=material_id,
            batch_no=batch_no,
            location_code="DEFAULT",
            quantity=quantity,
            unit_price=unit_price,
            quality_status="PASS"
        )
        db.add(inbound_item)

        # 创建批次库存
        batch_inv = models.BatchInventory(
            account_set_id=account_set_id,
            material_id=material_id,
            batch_no=batch_no,
            location_code="DEFAULT",
            expiry_date=expiry_date,
            quantity=quantity,
            unit_cost=unit_price,
            total_cost=quantity * unit_price,
            quality_status="AVAILABLE",
            inbound_date=datetime.date.today()
        )
        db.add(batch_inv)

        # 创建库存变动记录
        movement = models.BatchMovement(
            account_set_id=account_set_id,
            material_id=material_id,
            batch_no=batch_no,
            movement_type="INBOUND",
            quantity=quantity,
            location_code="DEFAULT",
            reference_no=inbound_no,
            reference_type="INBOUND",
            operator="SCAN"
        )
        db.add(movement)

        total_qty += quantity
        total_amount += quantity * unit_price
        result_items.append({
            "material_id": material_id,
            "material_code": material.code,
            "material_name": material.name,
            "batch_no": batch_no,
            "quantity": quantity,
            "unit_price": unit_price
        })

    db.commit()

    return make_response(True, {
        "inbound_no": inbound_no,
        "total_qty": total_qty,
        "total_amount": total_amount,
        "items": result_items
    }, "扫码入库成功")

@router.post("/inbound", tags=["入库管理"])
def create_inbound_order(inbound: schemas.InboundOrderCreate, db: Session = Depends(get_db)):
    inbound_no = f"IN-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    items_with_batch = []
    for item in inbound.items:
        batch_no = generate_batch_no(db, inbound.account_set_id, item.material_id, inbound.supplier_id)
        expiry_date = None
        
        material = crud.get_material(db, material_id=item.material_id)
        if material and hasattr(material, 'shelf_life_days') and material.shelf_life_days:
            expiry_date = datetime.date.today() + datetime.timedelta(days=material.shelf_life_days)
        
        items_with_batch.append({
            **item.dict(),
            "batch_no": batch_no,
            "expiry_date": expiry_date,
            "quality_status": "PENDING"
        })
    
    inbound_data = schemas.InboundOrderCreate(
        **inbound.dict(),
        inbound_no=inbound_no,
        status="PENDING",
        quality_status="PENDING",
        items=items_with_batch
    )
    
    created = crud.create_inbound_order(db, inbound_data)
    
    for item in created.items:
        crud.create_batch_inventory(db, schemas.BatchInventoryCreate(
            account_set_id=created.account_set_id,
            material_id=item.material_id,
            batch_no=item.batch_no,
            location_code=item.location_code,
            expiry_date=item.expiry_date,
            quantity=item.quantity,
            unit_cost=item.unit_price,
            quality_status="PENDING",
            supplier_id=created.supplier_id,
            purchase_order_id=created.purchase_order_id,
            inbound_date=created.inbound_date
        ))
        
        crud.create_batch_movement(db, schemas.BatchMovementCreate(
            account_set_id=created.account_set_id,
            material_id=item.material_id,
            batch_no=item.batch_no,
            movement_type="INBOUND",
            quantity=item.quantity,
            location_code=item.location_code,
            reference_no=created.inbound_no,
            reference_type="INBOUND",
            operator=created.operator or "system"
        ))
    
    return make_response(True, created, "入库单创建成功")

@router.put("/inbound/{inbound_id}/quality", tags=["入库管理"])
def update_quality_status(inbound_id: int, quality_results: List[dict], db: Session = Depends(get_db)):
    inbound = crud.get_inbound_order(db, inbound_id=inbound_id)
    if not inbound:
        return make_response(False, None, "入库单不存在", "40002")
    
    all_passed = True
    for result in quality_results:
        item = next((i for i in inbound.items if i.id == result["item_id"]), None)
        if item:
            item.quality_status = result["quality_status"]
            if result["quality_status"] != "PASS":
                all_passed = False
    
    inbound.quality_status = "PASS" if all_passed else "FAIL"
    inbound.status = "COMPLETED"
    
    for item in inbound.items:
        if item.quality_status == "PASS":
            inventory = crud.get_batch_inventories(db, batch_no=item.batch_no, material_id=item.material_id).first()
            if inventory:
                inventory.quality_status = "AVAILABLE"
        elif item.quality_status == "FAIL":
            inventory = crud.get_batch_inventories(db, batch_no=item.batch_no, material_id=item.material_id).first()
            if inventory:
                inventory.quality_status = "FROZEN"
    
    db.commit()
    
    return make_response(True, inbound, "质检完成")

@router.get("/outbound", tags=["出库管理"])
def get_outbound_orders(account_set_id: Optional[int] = None, outbound_type: Optional[str] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    orders = crud.get_outbound_orders(db, account_set_id=account_set_id, outbound_type=outbound_type, status=status, skip=skip, limit=limit)
    return make_response(True, orders, "查询成功")

@router.post("/outbound", tags=["出库管理"])
def create_outbound_order(outbound: schemas.OutboundOrderCreate, db: Session = Depends(get_db)):
    outbound_no = f"OUT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    outbound_data = schemas.OutboundOrderCreate(
        **outbound.dict(),
        outbound_no=outbound_no,
        status="PENDING"
    )
    
    created = crud.create_outbound_order(db, outbound_data)
    return make_response(True, created, "出库单创建成功")

@router.get("/outbound/batch-suggestion/{material_id}", tags=["出库管理"])
def get_batch_suggestion(material_id: int, quantity: int, db: Session = Depends(get_db)):
    inventories = crud.get_batch_inventories(db, material_id=material_id)
    available_inventories = [inv for inv in inventories if inv.quality_status == "AVAILABLE" and inv.quantity > 0]
    
    available_inventories.sort(key=lambda x: x.inbound_date or datetime.date.min)
    
    suggestions = []
    remaining_qty = quantity
    
    for inv in available_inventories:
        if remaining_qty <= 0:
            break
        
        suggest_qty = min(inv.quantity, remaining_qty)
        suggestions.append({
            "batch_id": inv.id,
            "batch_no": inv.batch_no,
            "location_code": inv.location_code,
            "available_qty": inv.quantity,
            "suggested_qty": suggest_qty,
            "inbound_date": inv.inbound_date,
            "expiry_date": inv.expiry_date
        })
        remaining_qty -= suggest_qty
    
    return make_response(True, {
        "material_id": material_id,
        "requested_qty": quantity,
        "suggested_batches": suggestions,
        "remaining_qty": remaining_qty
    }, "查询成功")

@router.put("/outbound/{outbound_id}/confirm", tags=["出库管理"])
def confirm_outbound(outbound_id: int, confirmed_items: List[dict], operator: str = "system", db: Session = Depends(get_db)):
    outbound = crud.get_outbound_order(db, outbound_id=outbound_id)
    if not outbound:
        return make_response(False, None, "出库单不存在", "40002")
    
    for confirmed in confirmed_items:
        item = next((i for i in outbound.items if i.id == confirmed["item_id"]), None)
        if not item:
            continue
        
        actual_qty = confirmed["actual_qty"]
        item.actual_qty = actual_qty
        
        inventory = crud.get_batch_inventories(db, batch_no=item.batch_no, material_id=item.material_id).first()
        if inventory and inventory.quantity >= actual_qty:
            crud.update_batch_inventory(db, inventory.id, inventory.quantity - actual_qty)
            
            crud.create_batch_movement(db, schemas.BatchMovementCreate(
                account_set_id=outbound.account_set_id,
                material_id=item.material_id,
                batch_no=item.batch_no,
                movement_type="OUTBOUND",
                quantity=actual_qty,
                location_code=item.location_code,
                reference_no=outbound.outbound_no,
                reference_type=outbound.outbound_type,
                operator=operator
            ))
        else:
            return make_response(False, None, f"批次 {item.batch_no} 库存不足", "40003")
    
    outbound.status = "COMPLETED"
    outbound.operator = operator
    db.commit()
    
    return make_response(True, outbound, "出库确认完成")

@router.get("/batch-inventory", tags=["库存管理与追溯"])
def get_batch_inventories_api(account_set_id: Optional[int] = None, material_id: Optional[int] = None, location_code: Optional[str] = None, batch_no: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    inventories = crud.get_batch_inventories(db, account_set_id=account_set_id, material_id=material_id, location_code=location_code, batch_no=batch_no, skip=skip, limit=limit)
    return make_response(True, inventories, "查询成功")

@router.get("/batch-trace/{material_id}", tags=["库存管理与追溯"])
def get_batch_trace(material_id: int, batch_no: Optional[str] = None, db: Session = Depends(get_db)):
    movements = crud.get_batch_movements(db, material_id=material_id, batch_no=batch_no)
    
    timeline = []
    for move in movements:
        timeline.append({
            "movement_id": move.id,
            "batch_no": move.batch_no,
            "movement_type": move.movement_type,
            "quantity": move.quantity,
            "location_code": move.location_code,
            "to_location_code": move.to_location_code,
            "reference_no": move.reference_no,
            "reference_type": move.reference_type,
            "operator": move.operator,
            "created_at": move.created_at
        })
    
    timeline.sort(key=lambda x: x["created_at"])
    
    return make_response(True, {
        "material_id": material_id,
        "timeline": timeline
    }, "查询成功")

@router.get("/location-dashboard", tags=["库存管理与追溯"])
def get_location_dashboard(account_set_id: Optional[int] = None, db: Session = Depends(get_db)):
    locations = crud.get_storage_locations(db, account_set_id=account_set_id)
    inventories = crud.get_batch_inventories(db, account_set_id=account_set_id)
    
    location_stats = {}
    for loc in locations:
        loc_inventories = [inv for inv in inventories if inv.location_code == loc.location_code]
        total_qty = sum(inv.quantity for inv in loc_inventories)
        
        utilization = 0
        status_color = "green"
        
        if loc.max_capacity:
            utilization = total_qty / loc.max_capacity * 100
            if utilization > 100:
                status_color = "red"
            elif utilization > 80:
                status_color = "yellow"
        
        location_stats[loc.location_code] = {
            "location_code": loc.location_code,
            "location_name": loc.location_name,
            "level": loc.level,
            "parent_code": loc.parent_code,
            "current_qty": total_qty,
            "max_capacity": loc.max_capacity,
            "utilization": round(utilization, 1),
            "status_color": status_color,
            "items": [{
                "material_id": inv.material_id,
                "batch_no": inv.batch_no,
                "quantity": inv.quantity
            } for inv in loc_inventories]
        }
    
    return make_response(True, location_stats, "查询成功")

@router.get("/alerts/slow-moving", tags=["库存管理与追溯"])
def get_slow_moving_alerts(account_set_id: Optional[int] = None, days_threshold: int = 180, db: Session = Depends(get_db)):
    today = datetime.date.today()
    threshold_date = today - datetime.timedelta(days=days_threshold)
    
    inventories = crud.get_batch_inventories(db, account_set_id=account_set_id)
    
    slow_moving = []
    for inv in inventories:
        if inv.last_movement_date and inv.last_movement_date < threshold_date:
            material = crud.get_material(db, material_id=inv.material_id)
            slow_moving.append({
                "material_id": inv.material_id,
                "material_code": material.code if material else "",
                "material_name": material.name if material else "",
                "batch_no": inv.batch_no,
                "location_code": inv.location_code,
                "quantity": inv.quantity,
                "last_movement_date": inv.last_movement_date,
                "days_since_movement": (today - inv.last_movement_date).days,
                "unit_cost": float(inv.unit_cost),
                "total_value": float(inv.total_cost)
            })
    
    return make_response(True, slow_moving, "查询成功")

@router.get("/alerts/expiry", tags=["库存管理与追溯"])
def get_expiry_alerts(account_set_id: Optional[int] = None, db: Session = Depends(get_db)):
    today = datetime.date.today()
    
    inventories = crud.get_batch_inventories(db, account_set_id=account_set_id)
    
    alerts = []
    for inv in inventories:
        if inv.expiry_date:
            days_left = (inv.expiry_date - today).days
            
            alert_level = None
            if days_left <= 7:
                alert_level = "HIGH"
            elif days_left <= 15:
                alert_level = "MEDIUM"
            elif days_left <= 30:
                alert_level = "LOW"
            
            if alert_level:
                material = crud.get_material(db, material_id=inv.material_id)
                alerts.append({
                    "material_id": inv.material_id,
                    "material_code": material.code if material else "",
                    "material_name": material.name if material else "",
                    "batch_no": inv.batch_no,
                    "location_code": inv.location_code,
                    "quantity": inv.quantity,
                    "expiry_date": inv.expiry_date,
                    "days_left": days_left,
                    "alert_level": alert_level,
                    "unit_cost": float(inv.unit_cost),
                    "total_value": float(inv.total_cost)
                })
    
    alerts.sort(key=lambda x: x["days_left"])
    
    return make_response(True, alerts, "查询成功")

@router.post("/stocktake/task", tags=["盘点管理"])
def create_stocktake_task(task: schemas.StocktakingTaskCreate, mode: str = "full", db: Session = Depends(get_db)):
    task_no = f"STK-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    task_data = schemas.StocktakingTaskCreate(
        **task.dict(),
        task_no=task_no
    )
    
    created = crud.create_stocktaking_task(db, task_data)
    
    inventories = crud.get_batch_inventories(db, account_set_id=task.account_set_id)
    if task.location_code:
        inventories = [inv for inv in inventories if inv.location_code == task.location_code]
    
    if mode == "cycle":
        material_ids = list(set(inv.material_id for inv in inventories))[:10]
        inventories = [inv for inv in inventories if inv.material_id in material_ids]
    
    for inv in inventories:
        crud.create_stocktaking_item(db, schemas.StocktakingItemCreate(
            task_id=created.id,
            material_id=inv.material_id,
            location_code=inv.location_code,
            book_qty=inv.quantity
        ))
    
    return make_response(True, created, "盘点任务创建成功")

@router.post("/stocktake/scan", tags=["盘点管理"])
def stocktake_scan(task_id: int, location_code: str, batch_no: str, actual_qty: int, db: Session = Depends(get_db)):
    task = crud.get_stocktaking_task(db, task_id=task_id)
    if not task:
        return make_response(False, None, "盘点任务不存在", "40002")
    
    inventory = crud.get_batch_inventories(db, batch_no=batch_no, location_code=location_code).first()
    if not inventory:
        return make_response(False, None, "批次库存不存在", "40002")
    
    book_qty = inventory.quantity
    variance = actual_qty - book_qty
    
    item = db.query(models.StocktakingItem).filter(
        models.StocktakingItem.task_id == task_id,
        models.StocktakingItem.material_id == inventory.material_id,
        models.StocktakingItem.location_code == location_code
    ).first()
    
    if not item:
        item = crud.create_stocktaking_item(db, schemas.StocktakingItemCreate(
            task_id=task_id,
            material_id=inventory.material_id,
            location_code=location_code,
            book_qty=book_qty,
            actual_qty=actual_qty,
            variance=variance
        ))
    else:
        item.actual_qty = actual_qty
        item.variance = variance
        db.commit()
    
    material = crud.get_material(db, material_id=inventory.material_id)
    
    return make_response(True, {
        "material_id": inventory.material_id,
        "material_name": material.name if material else "",
        "batch_no": batch_no,
        "location_code": location_code,
        "book_qty": book_qty,
        "actual_qty": actual_qty,
        "variance": variance
    }, "扫码成功")

@router.post("/stocktake/{task_id}/confirm", tags=["盘点管理"])
def confirm_stocktake(task_id: int, db: Session = Depends(get_db)):
    task = crud.get_stocktaking_task(db, task_id=task_id)
    if not task:
        return make_response(False, None, "盘点任务不存在", "40002")
    
    items = db.query(models.StocktakingItem).filter(models.StocktakingItem.task_id == task_id).all()
    adjustments = []
    total_diff = 0
    total_value_diff = 0
    
    for item in items:
        if item.variance != 0:
            inventory = crud.get_batch_inventories(db, material_id=item.material_id, location_code=item.location_code).first()
            
            if inventory:
                new_qty = item.book_qty + item.variance
                crud.update_batch_inventory(db, inventory.id, new_qty)
                
                crud.create_batch_movement(db, schemas.BatchMovementCreate(
                    account_set_id=task.account_set_id,
                    material_id=item.material_id,
                    batch_no=inventory.batch_no,
                    movement_type="STOCKTAKE",
                    quantity=item.variance,
                    location_code=item.location_code,
                    reference_no=task.task_no,
                    reference_type="STOCKTAKE",
                    operator="system"
                ))
                
                value_diff = item.variance * inventory.unit_cost
                total_value_diff += value_diff
                
                material = crud.get_material(db, material_id=item.material_id)
                adjustments.append({
                    "material_id": item.material_id,
                    "material_name": material.name if material else "",
                    "location_code": item.location_code,
                    "batch_no": inventory.batch_no,
                    "book_qty": item.book_qty,
                    "actual_qty": item.actual_qty,
                    "variance": item.variance,
                    "unit_cost": float(inventory.unit_cost),
                    "value_diff": float(value_diff)
                })
                total_diff += item.variance
    
    task.status = "COMPLETED"
    db.commit()
    
    return make_response(True, {
        "task": task,
        "adjustments": adjustments,
        "total_difference": total_diff,
        "total_value_diff": float(total_value_diff),
        "has_adjustments": len(adjustments) > 0
    }, "盘点确认完成")

@router.get("/reports/inventory-overview", tags=["报表与决策支持"])
def get_inventory_overview(account_set_id: Optional[int] = None, material_category: Optional[str] = None, location_code: Optional[str] = None, db: Session = Depends(get_db)):
    inventories = crud.get_batch_inventories(db, account_set_id=account_set_id)
    
    if location_code:
        inventories = [inv for inv in inventories if inv.location_code == location_code]
    
    material_summary = {}
    total_qty = 0
    total_value = 0
    
    for inv in inventories:
        if inv.material_id not in material_summary:
            material = crud.get_material(db, material_id=inv.material_id)
            material_summary[inv.material_id] = {
                "material_id": inv.material_id,
                "material_code": material.code if material else "",
                "material_name": material.name if material else "",
                "unit": material.unit if material else "",
                "total_qty": 0,
                "total_value": 0,
                "safety_stock": material.safety_stock if material else 0,
                "stock_status": "NORMAL"
            }
        
        material_summary[inv.material_id]["total_qty"] += inv.quantity
        material_summary[inv.material_id]["total_value"] += float(inv.total_cost)
        
        total_qty += inv.quantity
        total_value += float(inv.total_cost)
    
    for mat_id, summary in material_summary.items():
        if summary["total_qty"] < summary["safety_stock"]:
            summary["stock_status"] = "LOW"
        elif summary["total_qty"] > summary["safety_stock"] * 3:
            summary["stock_status"] = "HIGH"
    
    return make_response(True, {
        "total_qty": total_qty,
        "total_value": round(total_value, 2),
        "material_count": len(material_summary),
        "materials": list(material_summary.values())
    }, "查询成功")

@router.get("/reports/batch-trace", tags=["报表与决策支持"])
def get_batch_trace_report(material_id: Optional[int] = None, batch_no: Optional[str] = None, start_date: Optional[datetime.date] = None, end_date: Optional[datetime.date] = None, db: Session = Depends(get_db)):
    movements = crud.get_batch_movements(db, material_id=material_id, batch_no=batch_no)
    
    if start_date:
        movements = [m for m in movements if m.created_at.date() >= start_date]
    if end_date:
        movements = [m for m in movements if m.created_at.date() <= end_date]
    
    report = []
    for move in movements:
        material = crud.get_material(db, material_id=move.material_id)
        report.append({
            "movement_id": move.id,
            "material_code": material.code if material else "",
            "material_name": material.name if material else "",
            "batch_no": move.batch_no,
            "movement_type": move.movement_type,
            "quantity": move.quantity,
            "location_code": move.location_code,
            "to_location_code": move.to_location_code,
            "reference_no": move.reference_no,
            "reference_type": move.reference_type,
            "operator": move.operator,
            "created_at": move.created_at
        })
    
    report.sort(key=lambda x: x["created_at"])
    
    return make_response(True, {
        "total_movements": len(report),
        "report": report
    }, "查询成功")

@router.get("/reports/turnover", tags=["报表与决策支持"])
def get_inventory_turnover(account_set_id: Optional[int] = None, period: str = "THIS_MONTH", db: Session = Depends(get_db)):
    today = datetime.date.today()
    
    if period == "THIS_MONTH":
        start_date = datetime.date(today.year, today.month, 1)
        end_date = today
    elif period == "LAST_MONTH":
        if today.month == 1:
            start_date = datetime.date(today.year - 1, 12, 1)
        else:
            start_date = datetime.date(today.year, today.month - 1, 1)
        end_date = start_date + datetime.timedelta(days=32)
        end_date = end_date - datetime.timedelta(days=end_date.day)
    elif period == "THIS_YEAR":
        start_date = datetime.date(today.year, 1, 1)
        end_date = today
    else:
        return make_response(False, None, "无效的时间周期", "40003")
    
    movements = crud.get_batch_movements(db, account_set_id=account_set_id)
    outbound_movements = [m for m in movements if m.movement_type == "OUTBOUND" and start_date <= m.created_at.date() <= end_date]
    
    material_turnover = {}
    for move in outbound_movements:
        if move.material_id not in material_turnover:
            material_turnover[move.material_id] = {"total_outbound": 0, "total_cost": 0}
        
        inventory = crud.get_batch_inventories(db, batch_no=move.batch_no, material_id=move.material_id).first()
        if inventory:
            material_turnover[move.material_id]["total_outbound"] += move.quantity
            material_turnover[move.material_id]["total_cost"] += move.quantity * float(inventory.unit_cost)
    
    inventories = crud.get_batch_inventories(db, account_set_id=account_set_id)
    avg_inventory = {}
    for inv in inventories:
        if inv.material_id not in avg_inventory:
            avg_inventory[inv.material_id] = 0
        avg_inventory[inv.material_id] += float(inv.total_cost)
    
    results = []
    for mat_id, turnover in material_turnover.items():
        material = crud.get_material(db, material_id=mat_id)
        avg_cost = avg_inventory.get(mat_id, 0) / 2
        
        if avg_cost > 0:
            turnover_rate = turnover["total_cost"] / avg_cost
            turnover_days = (end_date - start_date).days / turnover_rate if turnover_rate > 0 else 0
        else:
            turnover_rate = 0
            turnover_days = 0
        
        results.append({
            "material_id": mat_id,
            "material_code": material.code if material else "",
            "material_name": material.name if material else "",
            "total_outbound": turnover["total_outbound"],
            "total_cost": round(turnover["total_cost"], 2),
            "avg_inventory": round(avg_cost, 2),
            "turnover_rate": round(turnover_rate, 2),
            "turnover_days": round(turnover_days, 1)
        })
    
    return make_response(True, {
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "total_outbound_value": sum(t["total_cost"] for t in results),
        "avg_inventory_value": sum(t["avg_inventory"] for t in results),
        "overall_turnover_rate": sum(t["total_cost"] for t in results) / sum(t["avg_inventory"] for t in results) if sum(t["avg_inventory"] for t in results) > 0 else 0,
        "materials": results
    }, "查询成功")

@router.get("/reports/slow-moving", tags=["报表与决策支持"])
def get_slow_moving_report(account_set_id: Optional[int] = None, days_threshold: int = 180, db: Session = Depends(get_db)):
    today = datetime.date.today()
    threshold_date = today - datetime.timedelta(days=days_threshold)
    
    inventories = crud.get_batch_inventories(db, account_set_id=account_set_id)
    
    slow_moving = []
    overstock = []
    
    for inv in inventories:
        material = crud.get_material(db, material_id=inv.material_id)
        
        if inv.last_movement_date and inv.last_movement_date < threshold_date:
            slow_moving.append({
                "material_id": inv.material_id,
                "material_code": material.code if material else "",
                "material_name": material.name if material else "",
                "batch_no": inv.batch_no,
                "location_code": inv.location_code,
                "quantity": inv.quantity,
                "unit_cost": float(inv.unit_cost),
                "total_value": float(inv.total_cost),
                "last_movement_date": inv.last_movement_date,
                "days_since_movement": (today - inv.last_movement_date).days
            })
        
        if material and material.max_stock and inv.quantity > material.max_stock:
            overstock.append({
                "material_id": inv.material_id,
                "material_code": material.code if material else "",
                "material_name": material.name if material else "",
                "batch_no": inv.batch_no,
                "location_code": inv.location_code,
                "quantity": inv.quantity,
                "max_stock": material.max_stock,
                "overstock_qty": inv.quantity - material.max_stock,
                "unit_cost": float(inv.unit_cost),
                "overstock_value": float((inv.quantity - material.max_stock) * inv.unit_cost)
            })
    
    return make_response(True, {
        "slow_moving_count": len(slow_moving),
        "slow_moving_value": sum(item["total_value"] for item in slow_moving),
        "slow_moving": slow_moving,
        "overstock_count": len(overstock),
        "overstock_value": sum(item["overstock_value"] for item in overstock),
        "overstock": overstock
    }, "查询成功")

@router.get("/quality-inspections/", tags=["质检管理"])
def get_quality_inspections(account_set_id: Optional[int] = None, source_type: Optional[str] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    inspections = crud.get_quality_inspections(db, account_set_id=account_set_id, source_type=source_type, status=status, skip=skip, limit=limit)
    return make_response(True, inspections, "查询成功")

@router.get("/quality-inspections/{inspection_id}", tags=["质检管理"])
def get_quality_inspection(inspection_id: int, db: Session = Depends(get_db)):
    inspection = crud.get_quality_inspection(db, inspection_id=inspection_id)
    if not inspection:
        return make_response(False, None, "质检单不存在", "40002")
    return make_response(True, inspection, "查询成功")

@router.post("/quality-inspections/", tags=["质检管理"])
def create_quality_inspection(inspection: schemas.QualityInspectionCreate, db: Session = Depends(get_db)):
    inspection_no = f"QI-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    items_data = []
    if inspection.source_type == "INBOUND":
        inbound_order = crud.get_inbound_order(db, inbound_id=inspection.source_id)
        if inbound_order:
            for item in inbound_order.items:
                items_data.append({
                    "material_id": item.material_id,
                    "batch_no": item.batch_no,
                    "sample_qty": item.quantity,
                    "inspected_qty": 0,
                    "qualified_qty": 0,
                    "unqualified_qty": 0,
                    "quality_status": "PENDING"
                })
    
    inspection_data = schemas.QualityInspectionCreate(
        **inspection.dict(),
        inspection_no=inspection_no,
        items=items_data if items_data else inspection.items
    )
    
    created = crud.create_quality_inspection(db, inspection_data)
    return make_response(True, created, "质检单创建成功")

@router.put("/quality-inspections/{inspection_id}/results", tags=["质检管理"])
def submit_quality_results(inspection_id: int, results: List[dict], db: Session = Depends(get_db)):
    inspection = crud.update_quality_inspection(db, inspection_id, results)
    if not inspection:
        return make_response(False, None, "质检单不存在", "40002")
    
    for result in results:
        item = next((i for i in inspection.items if i.id == result["item_id"]), None)
        if item:
            inventory = crud.get_batch_inventories(db, batch_no=item.batch_no, material_id=item.material_id).first()
            if inventory:
                if result["quality_status"] == "PASS":
                    inventory.quality_status = "AVAILABLE"
                elif result["quality_status"] == "FAIL":
                    inventory.quality_status = "FROZEN"
    
    db.commit()
    
    all_passed = all(result.get("quality_status") == "PASS" for result in results)
    
    if inspection.source_type == "INBOUND":
        inbound_order = crud.get_inbound_order(db, inbound_id=inspection.source_id)
        if inbound_order:
            inbound_order.quality_status = "PASS" if all_passed else "FAIL"
            inbound_order.status = "COMPLETED"
            db.commit()
    
    return make_response(True, inspection, "质检结果提交成功")

@router.post("/quality-inspections/{inspection_id}/return", tags=["质检管理"])
def create_return_for_unqualified(inspection_id: int, db: Session = Depends(get_db)):
    inspection = crud.get_quality_inspection(db, inspection_id=inspection_id)
    if not inspection:
        return make_response(False, None, "质检单不存在", "40002")
    
    unqualified_items = [item for item in inspection.items if item.quality_status == "FAIL"]
    if not unqualified_items:
        return make_response(False, None, "没有不合格品需要退货", "40003")
    
    for item in unqualified_items:
        inventory = crud.get_batch_inventories(db, batch_no=item.batch_no, material_id=item.material_id).first()
        if inventory:
            crud.update_batch_inventory(db, inventory.id, inventory.quantity - item.unqualified_qty)
            
            crud.create_batch_movement(db, schemas.BatchMovementCreate(
                account_set_id=inspection.account_set_id,
                material_id=item.material_id,
                batch_no=item.batch_no,
                movement_type="RETURN",
                quantity=-item.unqualified_qty,
                location_code=inventory.location_code,
                reference_no=inspection.inspection_no,
                reference_type="QUALITY_RETURN",
                operator=inspection.inspector or "system"
            ))
    
    return make_response(True, {"inspection_id": inspection_id, "returned_items": len(unqualified_items)}, "不合格品退货处理完成")