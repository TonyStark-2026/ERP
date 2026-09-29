"""
成本会计模块
===================
标准成本管理、成本差异分析、约当产量法成本分摊
"""
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
        return d.strftime("%Y-%m-%d")
    if isinstance(d, datetime.date):
        return str(d)
    return str(d)


def _material_to_dict(m):
    if not m:
        return {}
    return {"id": m.id, "code": m.code, "name": m.name, "unit": m.unit or "", "spec": m.spec or ""}


def _workorder_to_dict(w):
    if not w:
        return {}
    return {"id": w.id, "wo_no": getattr(w, "wo_no", "") or "", "product_name": getattr(w, "product_name", "") or ""}


VARIANCE_TYPE_LABELS = {
    "MATERIAL": "材料成本差异",
    "LABOR": "人工成本差异",
    "OVERHEAD": "制造费用差异",
}


# ============================================================
# 1. 标准成本管理
# ============================================================
@router.get("/standards", tags=["成本会计"])
def list_standards(keyword: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.CostStandard).filter(models.CostStandard.account_set_id == ACCOUNT_SET_ID)
    items = q.order_by(models.CostStandard.id.desc()).all()
    result = []
    for s in items:
        m = db.query(models.Material).filter(models.Material.id == s.material_id).first()
        result.append({
            "id": s.id, "material_id": s.material_id,
            "material": _material_to_dict(m),
            "standard_material_cost": float(s.standard_material_cost or 0),
            "standard_labor_cost": float(s.standard_labor_cost or 0),
            "standard_overhead_cost": float(s.standard_overhead_cost or 0),
            "standard_total_cost": float(s.standard_total_cost or 0),
            "effective_date": _fmt_date(s.effective_date),
            "status": s.status,
            "created_at": _fmt_date(s.created_at),
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/standards", tags=["成本会计"])
def create_standard(data: dict = Body(...), db: Session = Depends(get_db)):
    material_id = data.get("material_id")
    if not material_id:
        return make_response(False, None, "物料必填", "40001")
    mat = Decimal(str(data.get("standard_material_cost", 0)))
    lab = Decimal(str(data.get("standard_labor_cost", 0)))
    oh = Decimal(str(data.get("standard_overhead_cost", 0)))
    total = mat + lab + oh
    eff_date = data.get("effective_date")
    if isinstance(eff_date, str) and eff_date:
        eff_date = datetime.date.fromisoformat(eff_date)
    else:
        eff_date = datetime.date.today()
    s = models.CostStandard(
        account_set_id=ACCOUNT_SET_ID, material_id=material_id,
        standard_material_cost=mat, standard_labor_cost=lab,
        standard_overhead_cost=oh, standard_total_cost=total,
        effective_date=eff_date, status=data.get("status", "ACTIVE"),
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return make_response(True, {"id": s.id}, "标准成本创建成功")


@router.put("/standards/{sid}", tags=["成本会计"])
def update_standard(sid: int, data: dict = Body(...), db: Session = Depends(get_db)):
    s = db.query(models.CostStandard).filter(models.CostStandard.id == sid).first()
    if not s:
        return make_response(False, None, "标准成本不存在", "40401")
    for f in ["standard_material_cost", "standard_labor_cost", "standard_overhead_cost"]:
        if f in data:
            setattr(s, f, Decimal(str(data[f])))
    s.standard_total_cost = (s.standard_material_cost or 0) + (s.standard_labor_cost or 0) + (s.standard_overhead_cost or 0)
    if "effective_date" in data and data["effective_date"]:
        s.effective_date = datetime.date.fromisoformat(data["effective_date"])
    if "status" in data:
        s.status = data["status"]
    db.commit()
    return make_response(True, {"id": s.id}, "标准成本更新成功")


@router.delete("/standards/{sid}", tags=["成本会计"])
def delete_standard(sid: int, db: Session = Depends(get_db)):
    s = db.query(models.CostStandard).filter(models.CostStandard.id == sid).first()
    if not s:
        return make_response(False, None, "标准成本不存在", "40401")
    db.delete(s)
    db.commit()
    return make_response(True, None, "标准成本已删除")


# ============================================================
# 2. 成本差异分析
# ============================================================
@router.get("/variances", tags=["成本会计"])
def list_variances(
    work_order_id: Optional[int] = None,
    variance_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.CostVariance).filter(models.CostVariance.account_set_id == ACCOUNT_SET_ID)
    if work_order_id:
        q = q.filter(models.CostVariance.work_order_id == work_order_id)
    if variance_type:
        q = q.filter(models.CostVariance.variance_type == variance_type)
    items = q.order_by(models.CostVariance.id.desc()).all()
    result = []
    for v in items:
        wo = db.query(models.ProductionWorkOrder).filter(models.ProductionWorkOrder.id == v.work_order_id).first()
        m = db.query(models.Material).filter(models.Material.id == v.material_id).first() if v.material_id else None
        result.append({
            "id": v.id, "work_order_id": v.work_order_id,
            "work_order": _workorder_to_dict(wo),
            "material_id": v.material_id, "material": _material_to_dict(m),
            "variance_type": v.variance_type,
            "variance_type_label": VARIANCE_TYPE_LABELS.get(v.variance_type, v.variance_type),
            "standard_cost": float(v.standard_cost or 0),
            "actual_cost": float(v.actual_cost or 0),
            "variance_amount": float(v.variance_amount or 0),
            "variance_rate": float(v.variance_rate or 0),
            "analysis": v.analysis or "",
            "created_at": _fmt_date(v.created_at),
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/variances", tags=["成本会计"])
def create_variance(data: dict = Body(...), db: Session = Depends(get_db)):
    work_order_id = data.get("work_order_id")
    variance_type = data.get("variance_type")
    if not work_order_id or not variance_type:
        return make_response(False, None, "工单ID和差异类型必填", "40001")
    std = Decimal(str(data.get("standard_cost", 0)))
    actual = Decimal(str(data.get("actual_cost", 0)))
    diff = actual - std
    rate = (diff / std * 100) if std > 0 else Decimal("0")
    v = models.CostVariance(
        account_set_id=ACCOUNT_SET_ID, work_order_id=work_order_id,
        material_id=data.get("material_id"), variance_type=variance_type,
        standard_cost=std, actual_cost=actual,
        variance_amount=diff, variance_rate=rate,
        analysis=data.get("analysis"),
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return make_response(True, {"id": v.id}, "差异分析记录创建成功")


# ============================================================
# 3. 约当产量法成本分摊
# ============================================================
@router.post("/equivalent-units", tags=["成本会计"])
def calc_equivalent_units(data: dict = Body(...), db: Session = Depends(get_db)):
    """约当产量法成本分摊计算
    输入：期初在产品成本、本期投入成本、完工数量、期末在产品数量、完工程度%
    输出：完工产品成本、期末在产品成本
    """
    begin_wip = Decimal(str(data.get("begin_wip_cost", 0)))
    current_cost = Decimal(str(data.get("current_cost", 0)))
    completed_qty = Decimal(str(data.get("completed_qty", 0)))
    end_wip_qty = Decimal(str(data.get("end_wip_qty", 0)))
    completion_pct = Decimal(str(data.get("completion_pct", 50))) / Decimal("100")

    total_cost = begin_wip + current_cost
    equivalent_completed = completed_qty + (end_wip_qty * completion_pct)
    if equivalent_completed <= 0:
        return make_response(False, None, "约当产量为0，无法计算", "40001")
    unit_cost = total_cost / equivalent_completed
    completed_cost = unit_cost * completed_qty
    end_wip_cost = unit_cost * end_wip_qty * completion_pct

    return make_response(True, {
        "total_cost": round(float(total_cost), 2),
        "equivalent_units": round(float(equivalent_completed), 4),
        "unit_cost": round(float(unit_cost), 4),
        "completed_qty": float(completed_qty),
        "completed_cost": round(float(completed_cost), 2),
        "end_wip_qty": float(end_wip_qty),
        "end_wip_cost": round(float(end_wip_cost), 2),
        "completion_pct": float(completion_pct * 100),
    }, "约当产量法计算完成")


@router.get("/overview", tags=["成本会计"])
def overview(db: Session = Depends(get_db)):
    std_count = db.query(models.CostStandard).filter(models.CostStandard.account_set_id == ACCOUNT_SET_ID).count()
    var_count = db.query(models.CostVariance).filter(models.CostVariance.account_set_id == ACCOUNT_SET_ID).count()
    variances = db.query(models.CostVariance).filter(models.CostVariance.account_set_id == ACCOUNT_SET_ID).all()
    total_variance = sum(float(v.variance_amount or 0) for v in variances)
    favorable = sum(1 for v in variances if float(v.variance_amount or 0) < 0)
    unfavorable = sum(1 for v in variances if float(v.variance_amount or 0) > 0)
    return make_response(True, {
        "standard_count": std_count,
        "variance_count": var_count,
        "total_variance": round(total_variance, 2),
        "favorable_count": favorable,
        "unfavorable_count": unfavorable,
    }, "成本会计概览")
