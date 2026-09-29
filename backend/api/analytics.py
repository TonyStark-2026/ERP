"""
报表与分析模块 + 发票合规记录
===================
自定义报表设计器、管理驾驶舱仪表盘、发票合规校验记录
（现有 report_center.py / compliance.py 已有基础功能，本模块补充持久化记录与可视化配置）
"""
import json
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from typing import Optional
import datetime
from decimal import Decimal

from .. import models
from ..app import make_response
from ..database import get_db

router = APIRouter()
ACCOUNT_SET_ID = 1


def _now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _fmt_date(d):
    if not d:
        return ""
    if isinstance(d, datetime.datetime):
        return d.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(d, datetime.date):
        return str(d)
    return str(d)


DATA_SOURCE_LABELS = {
    "PURCHASE": "采购", "SALES": "销售", "INVENTORY": "库存",
    "PRODUCTION": "生产", "FINANCE": "财务",
}

INVOICE_TYPE_LABELS = {"PURCHASE": "进项发票", "SALES": "销项发票"}


# ============================================================
# 1. 自定义报表
# ============================================================
@router.get("/reports", tags=["报表分析"])
def list_reports(data_source: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.CustomReport).filter(models.CustomReport.account_set_id == ACCOUNT_SET_ID)
    if data_source:
        q = q.filter(models.CustomReport.data_source == data_source)
    items = q.order_by(models.CustomReport.id.desc()).all()
    result = []
    for r in items:
        result.append({
            "id": r.id, "name": r.name, "description": r.description or "",
            "data_source": r.data_source,
            "data_source_label": DATA_SOURCE_LABELS.get(r.data_source, r.data_source),
            "filter_config": r.filter_config or "",
            "dimension_config": r.dimension_config or "",
            "display_config": r.display_config or "",
            "creator": r.creator or "",
            "is_shared": r.is_shared,
            "created_at": _fmt_date(r.created_at),
            "updated_at": _fmt_date(r.updated_at),
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/reports", tags=["报表分析"])
def create_report(data: dict = Body(...), db: Session = Depends(get_db)):
    name = (data.get("name") or "").strip()
    data_source = data.get("data_source")
    if not name or not data_source:
        return make_response(False, None, "报表名称和数据源必填", "40001")
    r = models.CustomReport(
        account_set_id=ACCOUNT_SET_ID, name=name,
        description=data.get("description"),
        data_source=data_source,
        filter_config=json.dumps(data.get("filter_config", {}), ensure_ascii=False),
        dimension_config=json.dumps(data.get("dimension_config", {}), ensure_ascii=False),
        display_config=json.dumps(data.get("display_config", {}), ensure_ascii=False),
        creator=data.get("creator") or "admin",
        is_shared=data.get("is_shared", False),
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return make_response(True, {"id": r.id}, "自定义报表创建成功")


@router.put("/reports/{rid}", tags=["报表分析"])
def update_report(rid: int, data: dict = Body(...), db: Session = Depends(get_db)):
    r = db.query(models.CustomReport).filter(models.CustomReport.id == rid).first()
    if not r:
        return make_response(False, None, "报表不存在", "40401")
    for f in ["name", "description", "data_source", "creator"]:
        if f in data:
            setattr(r, f, data[f])
    for f in ["filter_config", "dimension_config", "display_config"]:
        if f in data:
            setattr(r, f, json.dumps(data[f], ensure_ascii=False) if isinstance(data[f], dict) else data[f])
    if "is_shared" in data:
        r.is_shared = data["is_shared"]
    db.commit()
    return make_response(True, {"id": r.id}, "报表更新成功")


@router.delete("/reports/{rid}", tags=["报表分析"])
def delete_report(rid: int, db: Session = Depends(get_db)):
    r = db.query(models.CustomReport).filter(models.CustomReport.id == rid).first()
    if not r:
        return make_response(False, None, "报表不存在", "40401")
    db.delete(r)
    db.commit()
    return make_response(True, None, "报表已删除")


@router.post("/reports/{rid}/execute", tags=["报表分析"])
def execute_report(rid: int, db: Session = Depends(get_db)):
    """执行自定义报表，返回汇总数据"""
    r = db.query(models.CustomReport).filter(models.CustomReport.id == rid).first()
    if not r:
        return make_response(False, None, "报表不存在", "40401")
    # 根据 data_source 聚合示例数据
    summary = {}
    if r.data_source == "PURCHASE":
        pos = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.account_set_id == ACCOUNT_SET_ID).all()
        summary = {
            "total_orders": len(pos),
            "total_amount": sum(float(po.total_amount or 0) for po in pos),
            "by_status": {},
        }
        for po in pos:
            summary["by_status"][po.status] = summary["by_status"].get(po.status, 0) + 1
    elif r.data_source == "SALES":
        sos = db.query(models.SalesOrder).filter(models.SalesOrder.account_set_id == ACCOUNT_SET_ID).all()
        so_it = db.query(models.SalesOrderItem).all()
        summary = {
            "total_orders": len(sos),
            "total_amount": sum(float(it.quantity or 0) * float(it.unit_price or 0) for it in so_it),
        }
    elif r.data_source == "INVENTORY":
        invs = db.query(models.InventoryRecord).all()
        summary = {
            "total_skus": len(invs),
            "total_quantity": sum(float(i.quantity or 0) for i in invs),
        }
    elif r.data_source == "FINANCE":
        subs = db.query(models.AccountingSubject).filter(models.AccountingSubject.account_set_id == ACCOUNT_SET_ID).all()
        summary = {"total_subjects": len(subs)}
    else:
        summary = {"message": "数据源暂不支持"}
    return make_response(True, {
        "report_name": r.name, "data_source": r.data_source,
        "summary": summary, "executed_at": _now_str(),
    }, "报表执行完成")


# ============================================================
# 2. 管理驾驶舱
# ============================================================
@router.get("/dashboards", tags=["报表分析"])
def list_dashboards(db: Session = Depends(get_db)):
    items = db.query(models.DashboardConfig).filter(models.DashboardConfig.account_set_id == ACCOUNT_SET_ID).all()
    result = []
    for d in items:
        result.append({
            "id": d.id, "name": d.name,
            "widgets": d.widgets or "[]",
            "layout": d.layout or "{}",
            "is_default": d.is_default,
            "created_at": _fmt_date(d.created_at),
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/dashboards", tags=["报表分析"])
def create_dashboard(data: dict = Body(...), db: Session = Depends(get_db)):
    name = (data.get("name") or "").strip()
    if not name:
        return make_response(False, None, "仪表盘名称必填", "40001")
    d = models.DashboardConfig(
        account_set_id=ACCOUNT_SET_ID, name=name,
        widgets=json.dumps(data.get("widgets", []), ensure_ascii=False),
        layout=json.dumps(data.get("layout", {}), ensure_ascii=False),
        is_default=data.get("is_default", False),
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return make_response(True, {"id": d.id}, "仪表盘创建成功")


@router.get("/cockpit", tags=["报表分析"])
def management_cockpit(db: Session = Depends(get_db)):
    """管理驾驶舱：核心经营指标实时汇总"""
    today = datetime.date.today()
    # 采购
    po_count = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.account_set_id == ACCOUNT_SET_ID).count()
    po_amount = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.account_set_id == ACCOUNT_SET_ID).all()
    total_po = sum(float(p.total_amount or 0) for p in po_amount)
    # 销售
    so_count = db.query(models.SalesOrder).filter(models.SalesOrder.account_set_id == ACCOUNT_SET_ID).count()
    so_items = db.query(models.SalesOrderItem).all()
    total_so = sum(float(it.quantity or 0) * float(it.unit_price or 0) for it in so_items)
    # 库存
    inv_items = db.query(models.InventoryRecord).all()
    total_inv_qty = sum(float(i.quantity or 0) for i in inv_items)
    # 呆滞
    slow_count = db.query(models.SlowMovingInventory).filter(
        models.SlowMovingInventory.account_set_id == ACCOUNT_SET_ID,
        models.SlowMovingInventory.status != "RESOLVED",
    ).count()
    slow_value = db.query(models.SlowMovingInventory).filter(
        models.SlowMovingInventory.account_set_id == ACCOUNT_SET_ID,
        models.SlowMovingInventory.status != "RESOLVED",
    ).all()
    total_slow_value = sum(float(s.value or 0) for s in slow_value)
    # 财务
    leaf_subs = db.query(models.AccountingSubject).filter(
        models.AccountingSubject.account_set_id == ACCOUNT_SET_ID,
        models.AccountingSubject.is_leaf == True,
    ).all()
    total_debit = sum(float(s.current_balance or 0) for s in leaf_subs if s.balance_direction == "DEBIT")
    total_credit = sum(float(s.current_balance or 0) for s in leaf_subs if s.balance_direction == "CREDIT")
    revenue = sum(float(s.current_balance or 0) for s in leaf_subs if s.category == "REVENUE")
    expense = sum(float(s.current_balance or 0) for s in leaf_subs if s.category == "EXPENSE")
    # 成本差异
    variances = db.query(models.CostVariance).filter(models.CostVariance.account_set_id == ACCOUNT_SET_ID).all()
    total_variance = sum(float(v.variance_amount or 0) for v in variances)
    # 发票合规
    invoice_alerts = db.query(models.InvoiceCheck).filter(
        models.InvoiceCheck.account_set_id == ACCOUNT_SET_ID,
        models.InvoiceCheck.is_deductible == False,
    ).count()

    return make_response(True, {
        "as_of": today.isoformat(),
        "metrics": {
            "purchase": {"orders": po_count, "amount": round(total_po, 2)},
            "sales": {"orders": so_count, "amount": round(total_so, 2)},
            "inventory": {"skus": len(inv_items), "quantity": round(total_inv_qty, 2)},
            "slow_moving": {"count": slow_count, "value": round(total_slow_value, 2)},
            "finance": {
                "total_debit": round(total_debit, 2),
                "total_credit": round(total_credit, 2),
                "balanced": abs(total_debit - total_credit) < 0.01,
                "revenue": round(revenue, 2),
                "expense": round(expense, 2),
                "net_profit": round(revenue - expense, 2),
            },
            "cost_variance": {"count": len(variances), "total": round(total_variance, 2)},
            "invoice_compliance": {"non_deductible_alerts": invoice_alerts},
        },
    }, "管理驾驶舱数据")


# ============================================================
# 3. 发票合规校验记录
# ============================================================
@router.get("/invoice-checks", tags=["报表分析"])
def list_invoice_checks(
    invoice_type: Optional[str] = None,
    is_deductible: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.InvoiceCheck).filter(models.InvoiceCheck.account_set_id == ACCOUNT_SET_ID)
    if invoice_type:
        q = q.filter(models.InvoiceCheck.invoice_type == invoice_type)
    if is_deductible is not None:
        q = q.filter(models.InvoiceCheck.is_deductible == is_deductible)
    items = q.order_by(models.InvoiceCheck.id.desc()).all()
    result = []
    for c in items:
        result.append({
            "id": c.id, "invoice_no": c.invoice_no,
            "invoice_type": c.invoice_type,
            "invoice_type_label": INVOICE_TYPE_LABELS.get(c.invoice_type, c.invoice_type),
            "supplier_id": c.supplier_id, "customer_id": c.customer_id,
            "invoice_date": _fmt_date(c.invoice_date),
            "amount": float(c.amount or 0), "tax_amount": float(c.tax_amount or 0),
            "tax_rate": float(c.tax_rate or 0),
            "input_tax_rate": float(c.input_tax_rate or 0),
            "output_tax_rate": float(c.output_tax_rate or 0),
            "tax_rate_diff": float(c.tax_rate_diff or 0),
            "is_deductible": c.is_deductible,
            "check_result": c.check_result or "",
            "warning_msg": c.warning_msg or "",
            "status": c.status,
            "created_at": _fmt_date(c.created_at),
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/invoice-checks", tags=["报表分析"])
def create_invoice_check(data: dict = Body(...), db: Session = Depends(get_db)):
    """发票合规校验：自动识别不得抵扣进项税的发票类型"""
    invoice_no = (data.get("invoice_no") or "").strip()
    invoice_type = data.get("invoice_type", "PURCHASE")
    if not invoice_no:
        return make_response(False, None, "发票号必填", "40001")

    amount = Decimal(str(data.get("amount", 0)))
    tax_amount = Decimal(str(data.get("tax_amount", 0)))
    tax_rate = Decimal(str(data.get("tax_rate", 0)))
    input_rate = Decimal(str(data.get("input_tax_rate", 0)))
    output_rate = Decimal(str(data.get("output_tax_rate", 0)))
    rate_diff = abs(input_rate - output_rate) if input_rate and output_rate else Decimal("0")

    # 合规判定逻辑
    is_deductible = True
    warnings = []
    item_name = data.get("item_name", "")

    personal_kw = ["餐饮", "娱乐", "美容", "健身", "旅游", "机票", "酒店", "香烟", "酒", "礼品"]
    welfare_kw = ["空调", "冰箱", "洗衣机", "微波炉", "电饭煲", "热水器", "电视", "家具"]
    for kw in personal_kw:
        if kw in item_name:
            is_deductible = False
            warnings.append(f"识别到个人消费类项目({kw})，不得抵扣进项税")
            break
    for kw in welfare_kw:
        if kw in item_name:
            is_deductible = False
            warnings.append(f"识别到集体福利类项目({kw})，需做进项转出")
            break

    if rate_diff > Decimal("0.05"):
        warnings.append(f"进销项税率差异较大({float(rate_diff)*100:.1f}%)，建议核实业务实质")

    inv_date = data.get("invoice_date")
    if isinstance(inv_date, str) and inv_date:
        inv_date = datetime.date.fromisoformat(inv_date)
    else:
        inv_date = today = datetime.date.today()

    check_result = "PASS" if is_deductible and not warnings else "WARNING"
    if not is_deductible:
        check_result = "REJECT"

    c = models.InvoiceCheck(
        account_set_id=ACCOUNT_SET_ID, invoice_no=invoice_no,
        invoice_type=invoice_type,
        supplier_id=data.get("supplier_id"), customer_id=data.get("customer_id"),
        invoice_date=inv_date, amount=amount, tax_amount=tax_amount,
        tax_rate=tax_rate, input_tax_rate=input_rate, output_tax_rate=output_rate,
        tax_rate_diff=rate_diff, is_deductible=is_deductible,
        check_result=check_result,
        warning_msg="；".join(warnings) if warnings else None,
        status="CHECKED",
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return make_response(True, {
        "id": c.id, "check_result": check_result, "is_deductible": is_deductible,
        "warnings": warnings,
    }, "发票校验完成")


@router.get("/overview", tags=["报表分析"])
def overview(db: Session = Depends(get_db)):
    report_count = db.query(models.CustomReport).filter(models.CustomReport.account_set_id == ACCOUNT_SET_ID).count()
    dashboard_count = db.query(models.DashboardConfig).filter(models.DashboardConfig.account_set_id == ACCOUNT_SET_ID).count()
    invoice_checks = db.query(models.InvoiceCheck).filter(models.InvoiceCheck.account_set_id == ACCOUNT_SET_ID).all()
    return make_response(True, {
        "custom_report_count": report_count,
        "dashboard_count": dashboard_count,
        "invoice_check_count": len(invoice_checks),
        "non_deductible_count": sum(1 for c in invoice_checks if not c.is_deductible),
        "warning_count": sum(1 for c in invoice_checks if c.check_result == "WARNING"),
    }, "报表分析概览")
