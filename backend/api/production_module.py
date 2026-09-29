"""
生产管理 V2 模块
===================
生产计划、MRP分析、工艺路线、生产工单、派工管理、生产领料、工序报工、质量检验、委外加工、设备工作中心
"""
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import datetime
from decimal import Decimal

from .. import models
from ..app import make_response
from ..database import get_db

router = APIRouter()
ACCOUNT_SET_ID = 1


def _fmt_date(d):
    if not d:
        return ""
    if isinstance(d, datetime.datetime):
        return d.strftime("%Y-%m-%d")
    if isinstance(d, datetime.date):
        return str(d)
    return str(d)


def _parse_date(s):
    if not s:
        return None
    if isinstance(s, (datetime.date, datetime.datetime)):
        return s if isinstance(s, datetime.date) else s.date()
    try:
        return datetime.date.fromisoformat(str(s)[:10])
    except Exception:
        return None


# ============================================================
# 1. 工艺路线
# ============================================================
@router.get("/routings", tags=["生产管理"])
def list_routings(db: Session = Depends(get_db)):
    items = db.query(models.Routing).filter(
        models.Routing.account_set_id == ACCOUNT_SET_ID
    ).order_by(models.Routing.id.desc()).all()
    result = []
    for r in items:
        p = db.query(models.Material).filter(models.Material.id == r.product_id).first()
        ops = db.query(models.RoutingOperation).filter(
            models.RoutingOperation.routing_id == r.id
        ).order_by(models.RoutingOperation.sequence).count()
        result.append({
            "id": r.id, "name": r.name, "version": r.version,
            "product_id": r.product_id, "product_name": p.name if p else "",
            "product_code": p.code if p else "",
            "status": r.status,
            "status_label": "启用" if r.status == "ACTIVE" else "停用",
            "operation_count": ops,
            "created_at": _fmt_date(r.created_at),
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/routings", tags=["生产管理"])
def create_routing(data: dict = Body(...), db: Session = Depends(get_db)):
    r = models.Routing(
        account_set_id=ACCOUNT_SET_ID,
        product_id=data.get("product_id"),
        name=data.get("name", ""),
        version=data.get("version", "V1"),
        status="ACTIVE",
    )
    db.add(r)
    db.flush()
    for op in data.get("operations", []) or []:
        db.add(models.RoutingOperation(
            routing_id=r.id, sequence=int(op.get("sequence", 1)),
            name=op.get("name", ""), description=op.get("description"),
            standard_time=Decimal(str(op.get("standard_time", 0))),
            equipment=op.get("equipment"), work_center=op.get("work_center"),
            labor_type=op.get("labor_type"),
        ))
    db.commit()
    return make_response(True, {"id": r.id}, "工艺路线创建成功")


@router.get("/routings/{rid}/operations", tags=["生产管理"])
def list_routing_operations(rid: int, db: Session = Depends(get_db)):
    ops = db.query(models.RoutingOperation).filter(
        models.RoutingOperation.routing_id == rid
    ).order_by(models.RoutingOperation.sequence).all()
    result = []
    for o in ops:
        result.append({
            "id": o.id, "sequence": o.sequence, "name": o.name,
            "description": o.description or "",
            "standard_time": float(o.standard_time or 0),
            "equipment": o.equipment or "", "work_center": o.work_center or "",
            "labor_type": o.labor_type or "",
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.delete("/routings/{rid}", tags=["生产管理"])
def delete_routing(rid: int, db: Session = Depends(get_db)):
    r = db.query(models.Routing).filter(models.Routing.id == rid).first()
    if not r:
        return make_response(False, None, "工艺路线不存在", "40401")
    db.query(models.RoutingOperation).filter(models.RoutingOperation.routing_id == rid).delete()
    db.delete(r)
    db.commit()
    return make_response(True, None, "工艺路线已删除")


# ============================================================
# 2. 生产领料
# ============================================================
@router.get("/requisitions", tags=["生产管理"])
def list_requisitions(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.MaterialRequisition).filter(
        models.MaterialRequisition.account_set_id == ACCOUNT_SET_ID
    )
    if status:
        q = q.filter(models.MaterialRequisition.status == status)
    items = q.order_by(models.MaterialRequisition.id.desc()).all()
    result = []
    for req in items:
        wo = db.query(models.ProductionWorkOrder).filter(
            models.ProductionWorkOrder.id == req.work_order_id
        ).first()
        result.append({
            "id": req.id, "requisition_no": req.requisition_no,
            "work_order_id": req.work_order_id,
            "work_order_no": wo.work_order_no if wo else "",
            "requisition_date": _fmt_date(req.requisition_date),
            "status": req.status,
            "status_label": {"PENDING": "待审批", "APPROVED": "已审批",
                             "ISSUED": "已发料", "CANCELLED": "已取消"}.get(req.status, req.status),
            "remark": req.remark or "",
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/requisitions", tags=["生产管理"])
def create_requisition(data: dict = Body(...), db: Session = Depends(get_db)):
    ts = datetime.datetime.now().strftime("%H%M%S")
    rno = f"MR-{datetime.date.today().strftime('%Y%m%d')}-{ts}"
    req = models.MaterialRequisition(
        account_set_id=ACCOUNT_SET_ID, requisition_no=rno,
        work_order_id=data.get("work_order_id"),
        requisition_date=_parse_date(data.get("requisition_date")) or datetime.date.today(),
        status="PENDING", remark=data.get("remark"),
    )
    db.add(req)
    db.flush()
    for it in data.get("items", []) or []:
        db.add(models.MaterialRequisitionItem(
            requisition_id=req.id, material_id=it.get("material_id"),
            required_qty=Decimal(str(it.get("required_qty", 0))),
            issued_qty=Decimal(str(it.get("issued_qty", 0))),
            unit_cost=Decimal(str(it.get("unit_cost", 0))) if it.get("unit_cost") else None,
            location_code=it.get("location_code"), batch_no=it.get("batch_no"),
        ))
    db.commit()
    return make_response(True, {"id": req.id, "requisition_no": rno}, "领料单创建成功")


@router.put("/requisitions/{rid}/approve", tags=["生产管理"])
def approve_requisition(rid: int, db: Session = Depends(get_db)):
    req = db.query(models.MaterialRequisition).filter(models.MaterialRequisition.id == rid).first()
    if not req:
        return make_response(False, None, "领料单不存在", "40401")
    req.status = "APPROVED"
    db.commit()
    return make_response(True, {"id": req.id}, "领料单已审批")


@router.put("/requisitions/{rid}/issue", tags=["生产管理"])
def issue_requisition(rid: int, db: Session = Depends(get_db)):
    """发料：扣减库存"""
    req = db.query(models.MaterialRequisition).filter(models.MaterialRequisition.id == rid).first()
    if not req:
        return make_response(False, None, "领料单不存在", "40401")
    if req.status != "APPROVED":
        return make_response(False, None, "需先审批", "40003")
    items = db.query(models.MaterialRequisitionItem).filter(
        models.MaterialRequisitionItem.requisition_id == rid
    ).all()
    for it in items:
        # 扣减库存记录
        inv = models.InventoryRecord(
            material_id=it.material_id,
            quantity=-float(it.required_qty or 0),
            transaction_type="PRODUCTION_ISSUE",
            reference_no=req.requisition_no,
            transaction_date=datetime.date.today(),
        )
        db.add(inv)
        it.issued_qty = it.required_qty
    req.status = "ISSUED"
    db.commit()
    return make_response(True, {"id": req.id}, "领料单已发料，库存已扣减")


# ============================================================
# 3. 工序报工
# ============================================================
@router.get("/work-reports", tags=["生产管理"])
def list_work_reports(
    work_order_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.WorkReport).filter(models.WorkReport.account_set_id == ACCOUNT_SET_ID)
    if work_order_id:
        q = q.filter(models.WorkReport.work_order_id == work_order_id)
    items = q.order_by(models.WorkReport.id.desc()).all()
    result = []
    for w in items:
        wo = db.query(models.ProductionWorkOrder).filter(
            models.ProductionWorkOrder.id == w.work_order_id
        ).first()
        result.append({
            "id": w.id, "report_no": w.report_no,
            "work_order_id": w.work_order_id,
            "work_order_no": wo.work_order_no if wo else "",
            "worker": w.worker, "report_date": _fmt_date(w.report_date),
            "completed_qty": w.completed_qty, "qualified_qty": w.qualified_qty,
            "defective_qty": w.defective_qty,
            "actual_time": float(w.actual_time or 0),
            "status": w.status, "remark": w.remark or "",
            "created_at": _fmt_date(w.created_at),
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/work-reports", tags=["生产管理"])
def create_work_report(data: dict = Body(...), db: Session = Depends(get_db)):
    ts = datetime.datetime.now().strftime("%H%M%S")
    wno = f"WR-{datetime.date.today().strftime('%Y%m%d')}-{ts}"
    w = models.WorkReport(
        account_set_id=ACCOUNT_SET_ID, report_no=wno,
        work_order_id=data.get("work_order_id"),
        routing_operation_id=data.get("routing_operation_id"),
        worker=data.get("worker", ""),
        report_date=_parse_date(data.get("report_date")) or datetime.date.today(),
        completed_qty=int(data.get("completed_qty", 0)),
        qualified_qty=int(data.get("qualified_qty", 0)),
        defective_qty=int(data.get("defective_qty", 0)),
        actual_time=Decimal(str(data.get("actual_time", 0))) if data.get("actual_time") else None,
        status="SUBMITTED", remark=data.get("remark"),
    )
    db.add(w)
    db.commit()
    return make_response(True, {"id": w.id, "report_no": wno}, "报工单创建成功")


@router.get("/overview", tags=["生产管理"])
def production_overview(db: Session = Depends(get_db)):
    routing_count = db.query(models.Routing).filter(
        models.Routing.account_set_id == ACCOUNT_SET_ID
    ).count()
    req_pending = db.query(models.MaterialRequisition).filter(
        models.MaterialRequisition.account_set_id == ACCOUNT_SET_ID,
        models.MaterialRequisition.status == "PENDING",
    ).count()
    req_issued = db.query(models.MaterialRequisition).filter(
        models.MaterialRequisition.account_set_id == ACCOUNT_SET_ID,
        models.MaterialRequisition.status == "ISSUED",
    ).count()
    wr_count = db.query(models.WorkReport).filter(
        models.WorkReport.account_set_id == ACCOUNT_SET_ID
    ).count()
    wo_active = db.query(models.ProductionWorkOrder).filter(
        models.ProductionWorkOrder.status.in_(["PLANNED", "RELEASED", "IN_PROGRESS"])
    ).count()
    # 新增统计
    plan_count = db.execute(text("SELECT COUNT(*) FROM production_plans WHERE account_set_id=:aid"),
                            {"aid": ACCOUNT_SET_ID}).scalar() or 0
    mrp_count = db.execute(text("SELECT COUNT(DISTINCT mrp_run_no) FROM mrp_results WHERE account_set_id=:aid"),
                           {"aid": ACCOUNT_SET_ID}).scalar() or 0
    dispatch_count = db.execute(text("SELECT COUNT(*) FROM production_dispatches WHERE account_set_id=:aid"),
                                 {"aid": ACCOUNT_SET_ID}).scalar() or 0
    outs_count = db.execute(text("SELECT COUNT(*) FROM outsourcing_orders WHERE account_set_id=:aid"),
                            {"aid": ACCOUNT_SET_ID}).scalar() or 0
    equip_count = db.execute(text("SELECT COUNT(*) FROM equipments WHERE account_set_id=:aid"),
                             {"aid": ACCOUNT_SET_ID}).scalar() or 0
    return make_response(True, {
        "routing_count": routing_count, "req_pending": req_pending,
        "req_issued": req_issued, "work_report_count": wr_count,
        "active_work_orders": wo_active,
        "plan_count": plan_count, "mrp_count": mrp_count,
        "dispatch_count": dispatch_count, "outsourcing_count": outs_count,
        "equipment_count": equip_count,
    })


# ============================================================
# 4. 生产工单管理（新增功能）
# ============================================================
@router.get("/work-orders", tags=["生产管理"])
def list_work_orders(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取生产工单列表"""
    query = db.query(models.ProductionWorkOrder).filter(
        models.ProductionWorkOrder.account_set_id == ACCOUNT_SET_ID
    )
    if status and status != "ALL":
        query = query.filter(models.ProductionWorkOrder.status == status)
    items = query.order_by(models.ProductionWorkOrder.id.desc()).all()
    result = []
    for wo in items:
        mat = db.query(models.Material).filter(models.Material.id == wo.product_id).first()
        result.append({
            "id": wo.id,
            "work_order_no": wo.work_order_no,
            "product_id": wo.product_id,
            "product_code": mat.code if mat else "",
            "product_name": mat.name if mat else "",
            "planned_qty": wo.planned_qty,
            "completed_qty": wo.completed_qty,
            "completion_ratio": float(wo.completion_ratio) if wo.completion_ratio else 0,
            "status": wo.status,
            "status_label": {"PLANNED": "已计划", "RELEASED": "已下达", "IN_PROGRESS": "进行中",
                             "COMPLETED": "已完工", "CLOSED": "已关闭"}.get(wo.status, wo.status),
            "start_date": _fmt_date(wo.start_date),
            "end_date": _fmt_date(wo.end_date),
            "priority": wo.priority or "NORMAL",
            "actual_material_cost": float(wo.actual_material_cost) if wo.actual_material_cost else 0,
            "actual_labor_cost": float(wo.actual_labor_cost) if wo.actual_labor_cost else 0,
            "actual_overhead_cost": float(wo.actual_overhead_cost) if wo.actual_overhead_cost else 0,
            "standard_cost": float(wo.standard_cost) if wo.standard_cost else 0,
            "actual_total": float((wo.actual_material_cost or 0) + (wo.actual_labor_cost or 0) + (wo.actual_overhead_cost or 0)),
        })
    return make_response(True, result)


@router.post("/work-orders", tags=["生产管理"])
def create_work_order(
    product_id: int = Body(..., embed=True),
    planned_qty: int = Body(..., embed=True),
    bom_id: Optional[int] = Body(None, embed=True),
    priority: str = Body("NORMAL", embed=True),
    start_date: Optional[str] = Body(None, embed=True),
    end_date: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db),
):
    """创建生产工单"""
    wo_no = f"WO-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    wo = models.ProductionWorkOrder(
        account_set_id=ACCOUNT_SET_ID,
        work_order_no=wo_no,
        product_id=product_id,
        bom_id=bom_id,
        planned_qty=planned_qty,
        completed_qty=0,
        in_progress_qty=0,
        completion_ratio=0,
        status="RELEASED",
        start_date=_parse_date(start_date) or datetime.date.today(),
        end_date=_parse_date(end_date) or datetime.date.today() + datetime.timedelta(days=10),
        priority=priority,
        actual_material_cost=0,
        actual_labor_cost=0,
        actual_overhead_cost=0,
        standard_cost=0,
    )
    db.add(wo)
    db.commit()
    db.refresh(wo)
    return make_response(True, {"id": wo.id, "work_order_no": wo.work_order_no}, "工单创建成功")


@router.put("/work-orders/{wo_id}/complete", tags=["生产管理"])
def complete_work_order(wo_id: int, db: Session = Depends(get_db)):
    """工单完工"""
    wo = db.query(models.ProductionWorkOrder).filter(models.ProductionWorkOrder.id == wo_id).first()
    if not wo:
        return make_response(False, None, "工单不存在", "404")
    wo.status = "COMPLETED"
    wo.completed_qty = wo.planned_qty
    wo.completion_ratio = 100
    wo.end_date = datetime.date.today()
    db.commit()
    return make_response(True, {"id": wo.id, "status": "COMPLETED"}, "工单已完工")


# ============================================================
# 5. 工单工序管理（新增功能）
# ============================================================
@router.get("/work-orders/{wo_id}/processes", tags=["生产管理"])
def list_work_order_processes(wo_id: int, db: Session = Depends(get_db)):
    """获取工单的工序列表"""
    wo = db.query(models.ProductionWorkOrder).filter(models.ProductionWorkOrder.id == wo_id).first()
    if not wo:
        return make_response(False, None, "工单不存在", "404")
    procs = db.query(models.WorkOrderProcess).filter(
        models.WorkOrderProcess.work_order_no == wo.work_order_no
    ).order_by(models.WorkOrderProcess.process_seq).all()
    result = []
    for p in procs:
        result.append({
            "id": p.id,
            "process_seq": p.process_seq,
            "process_name": p.process_name,
            "work_center": p.work_center or "",
            "quantity": p.quantity,
            "status": p.status,
            "status_label": {"PENDING": "待加工", "IN_PROGRESS": "加工中", "COMPLETED": "已完成"}.get(p.status, p.status),
            "plan_start": _fmt_date(p.plan_start),
            "plan_end": _fmt_date(p.plan_end),
        })
    return make_response(True, result)


# ============================================================
# 4.1 工单操作：开始生产、更新进度
# ============================================================
@router.put("/work-orders/{wo_id}/start", tags=["生产管理"])
def start_work_order(wo_id: int, db: Session = Depends(get_db)):
    """工单开始生产：状态 RELEASED → IN_PROGRESS"""
    wo = db.query(models.ProductionWorkOrder).filter(models.ProductionWorkOrder.id == wo_id).first()
    if not wo:
        return make_response(False, None, "工单不存在", "404")
    if wo.status not in ("RELEASED", "PLANNED"):
        return make_response(False, None, f"工单状态为{wo.status}，无法开始", "40001")
    wo.status = "IN_PROGRESS"
    wo.updated_at = datetime.datetime.utcnow()
    db.commit()
    return make_response(True, {"id": wo.id, "status": "IN_PROGRESS"}, "工单已开始生产")


@router.put("/work-orders/{wo_id}/progress", tags=["生产管理"])
def update_work_order_progress(
    wo_id: int,
    completed_qty: int = Body(..., embed=True),
    in_progress_qty: int = Body(0, embed=True),
    db: Session = Depends(get_db),
):
    """更新工单生产进度"""
    wo = db.query(models.ProductionWorkOrder).filter(models.ProductionWorkOrder.id == wo_id).first()
    if not wo:
        return make_response(False, None, "工单不存在", "404")
    wo.completed_qty = completed_qty
    wo.in_progress_qty = in_progress_qty
    ratio = (completed_qty / wo.planned_qty * 100) if wo.planned_qty else 0
    wo.completion_ratio = round(ratio, 1)
    if ratio >= 100:
        wo.status = "COMPLETED"
        wo.end_date = datetime.date.today()
    elif wo.status == "RELEASED":
        wo.status = "IN_PROGRESS"
    wo.updated_at = datetime.datetime.utcnow()
    db.commit()
    return make_response(True, {
        "id": wo.id, "completed_qty": wo.completed_qty,
        "completion_ratio": wo.completion_ratio, "status": wo.status,
    }, "工单进度已更新")


# ============================================================
# 4.2 工序状态流转
# ============================================================
@router.put("/work-order-processes/{proc_id}/start", tags=["生产管理"])
def start_process(proc_id: int, db: Session = Depends(get_db)):
    """工序开始加工：PENDING → IN_PROGRESS"""
    proc = db.query(models.WorkOrderProcess).filter(models.WorkOrderProcess.id == proc_id).first()
    if not proc:
        return make_response(False, None, "工序不存在", "404")
    proc.status = "IN_PROGRESS"
    proc.actual_start = datetime.datetime.now()
    db.commit()
    return make_response(True, {"id": proc.id, "status": "IN_PROGRESS"}, "工序已开始加工")


@router.put("/work-order-processes/{proc_id}/complete", tags=["生产管理"])
def complete_process(proc_id: int, db: Session = Depends(get_db)):
    """工序完工：IN_PROGRESS → COMPLETED"""
    proc = db.query(models.WorkOrderProcess).filter(models.WorkOrderProcess.id == proc_id).first()
    if not proc:
        return make_response(False, None, "工序不存在", "404")
    proc.status = "COMPLETED"
    proc.actual_end = datetime.datetime.now()
    db.commit()
    return make_response(True, {"id": proc.id, "status": "COMPLETED"}, "工序已完工")


# ============================================================
# 6. 质量检验管理
# ============================================================
@router.get("/inspections", tags=["生产管理"])
def list_inspections(
    source_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取质量检验列表"""
    query = db.query(models.QualityInspection).filter(
        models.QualityInspection.account_set_id == ACCOUNT_SET_ID
    )
    if source_type:
        query = query.filter(models.QualityInspection.source_type == source_type)
    items = query.order_by(models.QualityInspection.id.desc()).all()
    result = []
    for qi in items:
        result.append({
            "id": qi.id,
            "inspection_no": qi.inspection_no,
            "source_type": qi.source_type,
            "source_id": qi.source_id,
            "inspection_date": _fmt_date(qi.inspection_date),
            "status": qi.status,
            "status_label": {"PENDING": "待检", "IN_PROGRESS": "检验中", "PASSED": "合格", "FAILED": "不合格"}.get(qi.status, qi.status),
            "inspector": qi.inspector or "",
            "remarks": qi.remarks or "",
        })
    return make_response(True, result)


# ============================================================
# 7. 生产计划管理
# ============================================================
@router.get("/production-plans", tags=["生产管理"])
def list_production_plans(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取生产计划列表"""
    sql = """SELECT p.*, pr.project_name
             FROM production_plans p
             LEFT JOIN wbs_projects pr ON p.project_id = pr.id
             WHERE p.account_set_id = :aid"""
    params = {"aid": ACCOUNT_SET_ID}
    if status and status != "ALL":
        sql += " AND p.status = :st"
        params["st"] = status
    sql += " ORDER BY p.id DESC"
    rows = db.execute(text(sql), params).fetchall()
    result = []
    for r in rows:
        plan_id = r[0]
        items = db.execute(text(
            "SELECT pi.*, m.code as material_code, m.name as material_name "
            "FROM production_plan_items pi "
            "LEFT JOIN materials m ON pi.product_id = m.id "
            "WHERE pi.plan_id = :pid"
        ), {"pid": plan_id}).fetchall()
        item_list = []
        for it in items:
            item_list.append({
                "product_id": it[2], "product_code": it[6] or "",
                "product_name": it[7] or "", "quantity": float(it[3] or 0),
                "start_date": _fmt_date(it[4]), "end_date": _fmt_date(it[5]),
            })
        result.append({
            "id": r[0], "plan_no": r[2], "plan_type": r[3],
            "plan_type_label": {"PRE_PRODUCTION": "预生产计划", "PRODUCTION": "正式生产计划"}.get(r[3], r[3]),
            "plan_date": _fmt_date(r[4]), "status": r[5],
            "status_label": {"DRAFT": "草稿", "CONFIRMED": "已确认", "RELEASED": "已下达",
                             "COMPLETED": "已完成", "CLOSED": "已关闭"}.get(r[5], r[5]),
            "source_type": r[6] or "", "source_id": r[7],
            "project_id": r[8], "project_name": r[13] or "",
            "total_qty": float(r[9] or 0), "planner": r[10] or "",
            "remark": r[11] or "", "items": item_list,
        })
    return make_response(True, result)


# ============================================================
# 8. MRP分析结果
# ============================================================
@router.get("/mrp-results", tags=["生产管理"])
def list_mrp_results(
    mrp_run_no: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取MRP运算结果"""
    sql = """SELECT m.*, mat.code as material_code, mat.name as material_name,
                     mat.spec, mat.unit
              FROM mrp_results m
              LEFT JOIN materials mat ON m.material_id = mat.id
              WHERE m.account_set_id = :aid"""
    params = {"aid": ACCOUNT_SET_ID}
    if mrp_run_no:
        sql += " AND m.mrp_run_no = :rno"
        params["rno"] = mrp_run_no
    sql += " ORDER BY m.bom_level, m.id"
    rows = db.execute(text(sql), params).fetchall()
    result = []
    for r in rows:
        result.append({
            "id": r[0], "mrp_run_no": r[2], "material_id": r[3],
            "material_code": r[20] or "", "material_name": r[21] or "",
            "specification": r[22] or "", "unit": r[23] or "",
            "bom_level": r[5], "gross_requirement": float(r[6] or 0),
            "on_hand_qty": float(r[7] or 0), "on_order_qty": float(r[8] or 0),
            "safety_stock": float(r[9] or 0), "net_requirement": float(r[10] or 0),
            "planned_order_qty": float(r[11] or 0),
            "planned_date": _fmt_date(r[12]), "planned_release_date": _fmt_date(r[13]),
            "planned_type": r[14] or "",
            "planned_type_label": {"PRODUCTION": "生产", "PURCHASE": "采购"}.get(r[14], r[14] or ""),
            "material_property": r[15] or "",
            "loss_rate": float(r[16] or 0),
            "source_order_no": r[18] or "",
        })
    # 如果没有指定run_no，取最新的run_no汇总
    if not mrp_run_no and result:
        run_nos = list(set(r["mrp_run_no"] for r in result))
        latest_run = max(run_nos)
        result = [r for r in result if r["mrp_run_no"] == latest_run]
    return make_response(True, {"items": result, "total": len(result), "mrp_run_no": result[0]["mrp_run_no"] if result else ""})


# ============================================================
# 9. 派工管理
# ============================================================
@router.get("/dispatches", tags=["生产管理"])
def list_dispatches(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取派工单列表"""
    sql = """SELECT d.*, wo.work_order_no, wo.product_id,
                    m.code as product_code, m.name as product_name,
                    p.name as proc_name
             FROM production_dispatches d
             LEFT JOIN production_workorders wo ON d.work_order_id = wo.id
             LEFT JOIN materials m ON wo.product_id = m.id
             LEFT JOIN routing_operations p ON d.process_id = p.id
             WHERE d.account_set_id = :aid"""
    params = {"aid": ACCOUNT_SET_ID}
    if status and status != "ALL":
        sql += " AND d.status = :st"
        params["st"] = status
    sql += " ORDER BY d.id DESC"
    rows = db.execute(text(sql), params).fetchall()
    result = []
    for r in rows:
        result.append({
            "id": r[0], "dispatch_no": r[2], "work_order_id": r[3],
            "work_order_no": r[12] or "", "process_id": r[4],
            "process_name": r[16] or "", "work_center_id": r[5],
            "dispatch_qty": float(r[6] or 0), "status": r[7],
            "status_label": {"PENDING": "待派工", "DISPATCHED": "已派工",
                             "IN_PROGRESS": "加工中", "COMPLETED": "已完成",
                             "CANCELLED": "已取消"}.get(r[7], r[7]),
            "dispatcher": r[8] or "", "operator": r[9] or "",
            "dispatch_date": _fmt_date(r[10]) if r[10] else "",
            "product_code": r[14] or "", "product_name": r[15] or "",
        })
    return make_response(True, result)


@router.post("/dispatches", tags=["生产管理"])
def create_dispatch(data: dict = Body(...), db: Session = Depends(get_db)):
    """创建派工单"""
    ts = datetime.datetime.now().strftime("%H%M%S")
    dno = f"DISP-{datetime.date.today().strftime('%Y%m%d')}-{ts}"
    db.execute(text("""INSERT INTO production_dispatches
        (account_set_id, dispatch_no, work_order_id, process_id, work_center_id,
         dispatch_qty, status, dispatcher, operator, dispatch_date, created_at)
        VALUES (:aid, :dno, :woid, :pid, :wcid, :qty, 'DISPATCHED', :disp, :opr, :ddate, datetime('now'))"""),
        {"aid": ACCOUNT_SET_ID, "dno": dno, "woid": data.get("work_order_id"),
         "pid": data.get("process_id"), "wcid": data.get("work_center_id"),
         "qty": data.get("dispatch_qty", 1), "disp": data.get("dispatcher", ""),
         "opr": data.get("operator", ""),
         "ddate": datetime.datetime.now().isoformat()})
    db.commit()
    return make_response(True, {"dispatch_no": dno}, "派工单创建成功")


@router.put("/dispatches/{did}/complete", tags=["生产管理"])
def complete_dispatch(did: int, db: Session = Depends(get_db)):
    """派工完工"""
    row = db.execute(text("SELECT status FROM production_dispatches WHERE id = :id"),
                     {"id": did}).first()
    if not row:
        return make_response(False, None, "派工单不存在", "404")
    db.execute(text("UPDATE production_dispatches SET status='COMPLETED' WHERE id = :id"),
               {"id": did})
    db.commit()
    return make_response(True, {"id": did, "status": "COMPLETED"}, "派工已完工")


# ============================================================
# 10. 委外加工管理
# ============================================================
@router.get("/outsourcing-orders", tags=["生产管理"])
def list_outsourcing_orders(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取委外加工订单列表"""
    sql = """SELECT o.*, s.name as supplier_name, m.code as material_code,
                    m.name as material_name, m.spec
             FROM outsourcing_orders o
             LEFT JOIN suppliers s ON o.supplier_id = s.id
             LEFT JOIN materials m ON o.material_id = m.id
             WHERE o.account_set_id = :aid"""
    params = {"aid": ACCOUNT_SET_ID}
    if status and status != "ALL":
        sql += " AND o.status = :st"
        params["st"] = status
    sql += " ORDER BY o.id DESC"
    rows = db.execute(text(sql), params).fetchall()
    result = []
    for r in rows:
        # 获取发料信息
        issue = db.execute(text(
            "SELECT issue_no, status FROM outsourcing_issues WHERE outsourcing_order_id = :oid"
        ), {"oid": r[0]}).first()
        # 获取收货信息
        recv = db.execute(text(
            "SELECT receive_no, status FROM outsourcing_receives WHERE outsourcing_order_id = :oid"
        ), {"oid": r[0]}).first()
        result.append({
            "id": r[0], "order_no": r[2], "supplier_id": r[4],
            "supplier_name": r[15] or "", "material_id": r[5],
            "material_code": r[16] or "", "material_name": r[17] or "",
            "specification": r[18] or "",
            "ordered_qty": r[6], "unit_price": float(r[7] or 0),
            "total_fee": float(r[14] or 0), "planned_date": _fmt_date(r[8]),
            "status": r[9],
            "status_label": {"PENDING": "待发料", "ISSUED": "已发料",
                             "IN_PROGRESS": "加工中", "RECEIVED": "已收货",
                             "COMPLETED": "已完成"}.get(r[9], r[9]),
            "process_name": r[13] or "",
            "issue_no": issue[0] if issue else "",
            "issue_status": issue[1] if issue else "",
            "receive_no": recv[0] if recv else "",
            "receive_status": recv[1] if recv else "",
        })
    return make_response(True, result)


@router.post("/outsourcing-orders", tags=["生产管理"])
def create_outsourcing_order(data: dict = Body(...), db: Session = Depends(get_db)):
    """创建委外加工订单"""
    ts = datetime.datetime.now().strftime("%H%M%S")
    ono = f"OS-{datetime.date.today().strftime('%Y%m%d')}-{ts}"
    total_fee = float(data.get("unit_price", 0)) * int(data.get("ordered_qty", 0))
    db.execute(text("""INSERT INTO outsourcing_orders
        (account_set_id, order_no, request_id, supplier_id, material_id,
         ordered_qty, unit_price, planned_date, status, created_at, updated_at,
         project_id, process_name, total_fee)
        VALUES (:aid, :ono, NULL, :sid, :mid, :qty, :price, :pdate,
                'PENDING', datetime('now'), datetime('now'), :pid, :pname, :tfee)"""),
        {"aid": ACCOUNT_SET_ID, "ono": ono, "sid": data.get("supplier_id"),
         "mid": data.get("material_id"), "qty": data.get("ordered_qty", 1),
         "price": data.get("unit_price", 0),
         "pdate": data.get("planned_date"), "pid": data.get("project_id"),
         "pname": data.get("process_name", ""), "tfee": total_fee})
    db.commit()
    return make_response(True, {"order_no": ono}, "委外订单创建成功")


@router.put("/outsourcing-orders/{oid}/issue", tags=["生产管理"])
def issue_outsourcing(oid: int, db: Session = Depends(get_db)):
    """委外发料"""
    ts = datetime.datetime.now().strftime("%H%M%S")
    ino = f"OS-OUT-{datetime.date.today().strftime('%Y%m%d')}-{ts}"
    db.execute(text("""INSERT INTO outsourcing_issues
        (account_set_id, issue_no, outsourcing_order_id, issue_date, status, operator, created_at, updated_at)
        VALUES (:aid, :ino, :oid, date('now'), 'ISSUED', :opr, datetime('now'), datetime('now'))"""),
        {"aid": ACCOUNT_SET_ID, "ino": ino, "oid": oid, "opr": "仓管员"})
    db.execute(text("UPDATE outsourcing_orders SET status='ISSUED', updated_at=datetime('now') WHERE id=:oid"),
               {"oid": oid})
    db.commit()
    return make_response(True, {"issue_no": ino}, "委外已发料")


@router.put("/outsourcing-orders/{oid}/receive", tags=["生产管理"])
def receive_outsourcing(oid: int, db: Session = Depends(get_db)):
    """委外收货入库"""
    ts = datetime.datetime.now().strftime("%H%M%S")
    rno = f"OS-IN-{datetime.date.today().strftime('%Y%m%d')}-{ts}"
    db.execute(text("""INSERT INTO outsourcing_receives
        (account_set_id, receive_no, outsourcing_order_id, expected_arrival_date, actual_arrival_date, status, created_at, updated_at)
        VALUES (:aid, :rno, :oid, date('now'), date('now'), 'RECEIVED', datetime('now'), datetime('now'))"""),
        {"aid": ACCOUNT_SET_ID, "rno": rno, "oid": oid})
    db.execute(text("UPDATE outsourcing_orders SET status='RECEIVED', updated_at=datetime('now') WHERE id=:oid"),
               {"oid": oid})
    db.commit()
    return make_response(True, {"receive_no": rno}, "委外已收货入库")


# ============================================================
# 11. 设备与工作中心管理
# ============================================================
@router.get("/equipments", tags=["生产管理"])
def list_equipments(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取设备列表"""
    sql = "SELECT * FROM equipments WHERE account_set_id = :aid"
    params = {"aid": ACCOUNT_SET_ID}
    if status and status != "ALL":
        sql += " AND status = :st"
        params["st"] = status
    sql += " ORDER BY id DESC"
    rows = db.execute(text(sql), params).fetchall()
    colnames = db.execute(text("PRAGMA table_info(equipments)")).fetchall()
    col_names = [c[1] for c in colnames]
    result = []
    for r in rows:
        row_dict = dict(zip(col_names, r))
        result.append({
            "id": row_dict["id"],
            "equipment_code": row_dict.get("equipment_code", ""),
            "equipment_name": row_dict.get("equipment_name", ""),
            "category": row_dict.get("category") or "",
            "model": row_dict.get("model") or "",
            "manufacturer": row_dict.get("manufacturer") or "",
            "workshop": row_dict.get("workshop") or "",
            "work_center": row_dict.get("work_center") or "",
            "status": row_dict.get("status", "RUNNING"),
            "status_label": {"RUNNING": "运行中", "IDLE": "停机", "MAINTENANCE": "维修中", "SCRAPPED": "已报废"}.get(row_dict.get("status"), row_dict.get("status", "")),
            "oee": float(row_dict.get("oee") or 0),
            "availability": float(row_dict.get("availability") or 0),
            "performance": float(row_dict.get("performance") or 0),
            "quality_rate": float(row_dict.get("quality_rate") or 0),
            "last_maintenance": _fmt_date(row_dict.get("last_maintenance")),
            "next_maintenance": _fmt_date(row_dict.get("next_maintenance")),
            "commission_date": _fmt_date(row_dict.get("commission_date")),
        })
    return make_response(True, result)


@router.get("/work-centers", tags=["生产管理"])
def list_work_centers(db: Session = Depends(get_db)):
    """获取工作中心列表"""
    rows = db.execute(text("""SELECT wc.*, w.name as workshop_name
                               FROM work_centers wc
                               LEFT JOIN workshops w ON wc.workshop_id = w.id
                               WHERE wc.account_set_id = :aid ORDER BY wc.id"""),
                      {"aid": ACCOUNT_SET_ID}).fetchall()
    colnames = db.execute(text("PRAGMA table_info(work_centers)")).fetchall()
    col_names = [c[1] for c in colnames]
    result = []
    for r in rows:
        row_dict = dict(zip(col_names, r))
        result.append({
            "id": row_dict["id"],
            "code": row_dict.get("code", ""),
            "name": row_dict.get("name", ""),
            "type": row_dict.get("type") or "",
            "workshop_id": row_dict.get("workshop_id"),
            "workshop_name": r[-1] or "",
            "capacity_per_hour": float(row_dict.get("capacity_per_hour") or 0),
            "efficiency": float(row_dict.get("efficiency") or 0),
            "labor_cost_rate": float(row_dict.get("labor_cost_rate") or 0),
            "machine_cost_rate": float(row_dict.get("machine_cost_rate") or 0),
            "status": row_dict.get("status", "ACTIVE"),
            "status_label": {"ACTIVE": "启用", "INACTIVE": "停用"}.get(row_dict.get("status"), row_dict.get("status", "")),
        })
    return make_response(True, result)


@router.get("/workshops", tags=["生产管理"])
def list_workshops(db: Session = Depends(get_db)):
    """获取车间列表"""
    rows = db.execute(text("SELECT * FROM workshops WHERE account_set_id = :aid ORDER BY id"),
                      {"aid": ACCOUNT_SET_ID}).fetchall()
    colnames = db.execute(text("PRAGMA table_info(workshops)")).fetchall()
    col_names = [c[1] for c in colnames]
    result = []
    for r in rows:
        row_dict = dict(zip(col_names, r))
        result.append({
            "id": row_dict["id"],
            "code": row_dict.get("code", ""),
            "name": row_dict.get("name", ""),
            "manager": row_dict.get("manager") or "",
            "location": row_dict.get("location") or "",
            "status": row_dict.get("status", "ACTIVE"),
            "status_label": {"ACTIVE": "启用", "INACTIVE": "停用"}.get(row_dict.get("status"), row_dict.get("status", "")),
        })
    return make_response(True, result)
