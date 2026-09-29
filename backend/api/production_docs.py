"""
生产单据体系 API
================
核心思想：单据流转，而非模块堆砌
8种单据通过 document_links 通用关系表实现下推、自动生成、双向追溯

单据类型：
  work_order      生产工单
  component_list  组件清单
  process_plan    工序计划
  pick            生产领料单
  material_return 生产退料单
  replenish       生产补料单
  inbound         完工入库单
  return_inbound  完工退库单

核心接口：
  GET    /pd/work-orders              工单列表
  POST   /pd/work-orders              新建工单
  GET    /pd/work-orders/{id}         工单详情
  PUT    /pd/work-orders/{id}         更新工单
  POST   /pd/work-orders/{id}/release 下达工单（自动生成组件清单+工序计划）
  POST   /pd/work-orders/{id}/push-pick   下推生成领料单
  POST   /pd/work-orders/{id}/push-inbound 下推生成入库单
  POST   /pd/picks/{id}/push-return    领料单下推生成退料单
  POST   /pd/inbounds/{id}/push-return-inbound 入库单下推生成退库单
  GET    /pd/trace/{doc_type}/{id}     BFS双向追溯
  GET    /pd/graph/{doc_type}/{id}     关系图数据
"""
import json
import datetime
from typing import List, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..database import get_db
from ..app import make_response
from .. import models

router = APIRouter()


# ============================================================
# 工具函数
# ============================================================

def _get_account_set_id(db: Session) -> int:
    """获取默认账套ID"""
    from ..models import AccountSet
    acc = db.query(AccountSet).first()
    return acc.id if acc else 1


def _gen_doc_no(prefix: str, model, db: Session) -> str:
    """生成单据号：prefix + YYYYMM + 4位流水"""
    today = datetime.datetime.now()
    ym = today.strftime("%Y%m")
    count = db.query(model).filter(
        model.doc_no.like(f"{prefix}{ym}%")
    ).count()
    return f"{prefix}{ym}{count + 1:04d}"


def _doc_to_dict(obj, items_fields=None) -> dict:
    """通用单据转字典，自动解析JSON字段"""
    d = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, Decimal):
            val = float(val)
        elif isinstance(val, datetime.datetime):
            val = val.isoformat()
        elif isinstance(val, datetime.date):
            val = val.isoformat()
        elif hasattr(val, 'value'):  # Enum
            val = val.value
        d[col.name] = val
    # 解析JSON字段
    if items_fields:
        for f in items_fields:
            if d.get(f):
                try:
                    d[f] = json.loads(d[f])
                except:
                    d[f] = []
    return d


def _add_link(db: Session, source_type: str, source_id: int, source_no: str,
              target_type: str, target_id: int, target_no: str, link_type: str = "push"):
    """添加双向链接：正向+反向"""
    # 正向：source → target
    fwd = models.DocumentLink(
        source_doc_type=source_type, source_doc_id=source_id, source_doc_no=source_no,
        target_doc_type=target_type, target_doc_id=target_id, target_doc_no=target_no,
        link_type=link_type, is_reverse=False
    )
    db.add(fwd)
    # 反向：target → source，标记 is_reverse=True
    rev = models.DocumentLink(
        source_doc_type=target_type, source_doc_id=target_id, source_doc_no=target_no,
        target_doc_type=source_type, target_doc_id=source_id, target_doc_no=source_no,
        link_type=link_type, is_reverse=True
    )
    db.add(rev)
    db.commit()


# ============================================================
# 1. 生产工单
# ============================================================

@router.get("/work-orders")
def list_work_orders(status: Optional[str] = None, keyword: Optional[str] = None,
                     db: Session = Depends(get_db)):
    q = db.query(models.ProductionWorkOrderDoc)
    if status:
        q = q.filter(models.ProductionWorkOrderDoc.status == status)
    if keyword:
        q = q.filter(or_(
            models.ProductionWorkOrderDoc.doc_no.contains(keyword),
            models.ProductionWorkOrderDoc.product_name.contains(keyword)
        ))
    items = q.order_by(models.ProductionWorkOrderDoc.created_at.desc()).all()
    return make_response(True, [_doc_to_dict(i) for i in items], "ok")


@router.post("/work-orders")
def create_work_order(data: dict, db: Session = Depends(get_db)):
    acc_id = _get_account_set_id(db)
    doc_no = _gen_doc_no("WO", models.ProductionWorkOrderDoc, db)
    obj = models.ProductionWorkOrderDoc(
        account_set_id=acc_id,
        doc_no=doc_no,
        product_code=data.get("product_code"),
        product_name=data.get("product_name"),
        product_id=data.get("product_id"),
        planned_qty=Decimal(str(data.get("planned_qty", 0))),
        planned_start=datetime.date.fromisoformat(data["planned_start"]) if data.get("planned_start") else None,
        planned_end=datetime.date.fromisoformat(data["planned_end"]) if data.get("planned_end") else None,
        workshop=data.get("workshop"),
        priority=data.get("priority", "normal"),
        remark=data.get("remark"),
        created_by=data.get("created_by"),
        status=models.ProdDocStatus.DRAFT
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return make_response(True, _doc_to_dict(obj), f"工单创建成功：{doc_no}")


@router.get("/work-orders/{wo_id}")
def get_work_order(wo_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.ProductionWorkOrderDoc).get(wo_id)
    if not obj:
        return make_response(False, None, "工单不存在", "40401")
    d = _doc_to_dict(obj)
    # 关联查询：组件清单、工序计划、领料单、入库单
    d["component_list"] = _get_related(db, "component_list", wo_id)
    d["process_plan"] = _get_related(db, "process_plan", wo_id)
    d["picks"] = _get_related(db, "pick", wo_id)
    d["inbounds"] = _get_related(db, "inbound", wo_id)
    return make_response(True, d, "ok")


def _get_related(db: Session, doc_type: str, work_order_id: int):
    """获取工单关联的下游单据"""
    if doc_type == "component_list":
        obj = db.query(models.ProductionComponentList).filter_by(work_order_id=work_order_id).first()
        return _doc_to_dict(obj, ["items_json"]) if obj else None
    elif doc_type == "process_plan":
        obj = db.query(models.ProductionProcessPlan).filter_by(work_order_id=work_order_id).first()
        return _doc_to_dict(obj, ["steps_json"]) if obj else None
    elif doc_type == "pick":
        objs = db.query(models.ProductionPick).filter_by(work_order_id=work_order_id).all()
        return [_doc_to_dict(o, ["items_json"]) for o in objs]
    elif doc_type == "inbound":
        objs = db.query(models.ProductionInbound).filter_by(work_order_id=work_order_id).all()
        return [_doc_to_dict(o) for o in objs]
    return []


@router.put("/work-orders/{wo_id}")
def update_work_order(wo_id: int, data: dict, db: Session = Depends(get_db)):
    obj = db.query(models.ProductionWorkOrderDoc).get(wo_id)
    if not obj:
        return make_response(False, None, "工单不存在", "40401")
    for k, v in data.items():
        if k in ("planned_start", "planned_end", "actual_start", "actual_end"):
            setattr(obj, k, datetime.date.fromisoformat(v) if v else None)
        elif k in ("planned_qty", "completed_qty", "issued_qty"):
            setattr(obj, k, Decimal(str(v)))
        elif hasattr(obj, k):
            setattr(obj, k, v)
    db.commit()
    return make_response(True, _doc_to_dict(obj), "工单已更新")


@router.post("/work-orders/{wo_id}/release")
def release_work_order(wo_id: int, db: Session = Depends(get_db)):
    """下达工单：自动生成组件清单 + 工序计划"""
    obj = db.query(models.ProductionWorkOrderDoc).get(wo_id)
    if not obj:
        return make_response(False, None, "工单不存在", "40401")
    if obj.status != models.ProdDocStatus.DRAFT and obj.status != models.ProdDocStatus.CONFIRMED:
        return make_response(False, None, "只有草稿/已确认状态的工单可以下达", "40001")

    acc_id = obj.account_set_id

    # 1. 生成组件清单（BOM展开快照）
    cl_no = _gen_doc_no("CL", models.ProductionComponentList, db)
    items = []
    # 从产品找到BOM并展开
    if obj.product_id:
        bom = db.query(models.BOM).filter_by(
            product_id=obj.product_id, status="ACTIVE"
        ).order_by(models.BOM.version.desc()).first()
        if bom and bom.items:
            planned = Decimal(str(obj.planned_qty))
            for bi in bom.items:
                mat = db.query(models.Material).get(bi.material_id) if bi.material_id else None
                qty_per = Decimal(str(bi.quantity or 0))
                required = qty_per * planned
                items.append({
                    "material_id": bi.material_id,
                    "material_code": mat.code if mat else "",
                    "material_name": mat.name if mat else (bi.material_name if hasattr(bi, 'material_name') else ''),
                    "qty_per": float(qty_per),
                    "required_qty": float(required),
                    "issued_qty": 0,
                    "unit": bi.unit if hasattr(bi, 'unit') and bi.unit else (mat.unit if mat else '')
                })
    # 如果没有BOM，给一组示例组件
    if not items:
        items = [
            {"material_code": "MAT-001", "material_name": "主要原材料", "qty_per": 1, "required_qty": float(obj.planned_qty), "issued_qty": 0, "unit": "个"},
            {"material_code": "MAT-002", "material_name": "辅料A", "qty_per": 2, "required_qty": float(obj.planned_qty * 2), "issued_qty": 0, "unit": "个"},
            {"material_code": "MAT-003", "material_name": "包装材料", "qty_per": 1, "required_qty": float(obj.planned_qty), "issued_qty": 0, "unit": "套"},
        ]
    cl = models.ProductionComponentList(
        account_set_id=acc_id, doc_no=cl_no,
        work_order_id=obj.id, work_order_no=obj.doc_no,
        product_name=obj.product_name,
        items_json=json.dumps(items, ensure_ascii=False),
        status=models.ProdDocStatus.CONFIRMED
    )
    db.add(cl)
    db.flush()

    # 2. 生成工序计划（默认3道工序）
    pp_no = _gen_doc_no("PP", models.ProductionProcessPlan, db)
    steps = [
        {"seq": 1, "name": "下料", "work_center": "下料车间", "standard_hours": 2, "operator": "", "status": "待开始"},
        {"seq": 2, "name": "加工", "work_center": "加工车间", "standard_hours": 4, "operator": "", "status": "待开始"},
        {"seq": 3, "name": "组装检验", "work_center": "组装车间", "standard_hours": 2, "operator": "", "status": "待开始"},
    ]
    pp = models.ProductionProcessPlan(
        account_set_id=acc_id, doc_no=pp_no,
        work_order_id=obj.id, work_order_no=obj.doc_no,
        product_name=obj.product_name,
        steps_json=json.dumps(steps, ensure_ascii=False),
        status=models.ProdDocStatus.CONFIRMED
    )
    db.add(pp)
    db.flush()

    # 3. 建立链接（auto）
    _add_link(db, "work_order", obj.id, obj.doc_no, "component_list", cl.id, cl_no, "auto")
    _add_link(db, "work_order", obj.id, obj.doc_no, "process_plan", pp.id, pp_no, "auto")

    # 4. 更新工单状态
    obj.status = models.ProdDocStatus.RELEASED
    obj.actual_start = datetime.date.today()
    db.commit()

    return make_response(True, {
        "work_order": _doc_to_dict(obj),
        "component_list": _doc_to_dict(cl, ["items_json"]),
        "process_plan": _doc_to_dict(pp, ["steps_json"])
    }, f"工单已下达，自动生成组件清单{cl_no}和工序计划{pp_no}")


# ============================================================
# 2. 生产领料单
# ============================================================

@router.get("/picks")
def list_picks(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.ProductionPick)
    if status:
        q = q.filter(models.ProductionPick.status == status)
    items = q.order_by(models.ProductionPick.created_at.desc()).all()
    return make_response(True, [_doc_to_dict(i, ["items_json"]) for i in items], "ok")


@router.get("/picks/{pick_id}")
def get_pick(pick_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.ProductionPick).get(pick_id)
    if not obj:
        return make_response(False, None, "领料单不存在", "40402")
    return make_response(True, _doc_to_dict(obj, ["items_json"]), "ok")


@router.post("/picks")
def create_pick(data: dict, db: Session = Depends(get_db)):
    acc_id = _get_account_set_id(db)
    doc_no = _gen_doc_no("PK", models.ProductionPick, db)
    items = data.get("items", [])
    obj = models.ProductionPick(
        account_set_id=acc_id, doc_no=doc_no,
        work_order_id=data.get("work_order_id"),
        work_order_no=data.get("work_order_no"),
        pick_date=datetime.date.fromisoformat(data["pick_date"]) if data.get("pick_date") else None,
        items_json=json.dumps(items, ensure_ascii=False),
        status=models.ProdDocStatus.DRAFT,
        warehouse=data.get("warehouse"),
        remark=data.get("remark"),
        created_by=data.get("created_by")
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    # 如果关联工单，建立链接
    if obj.work_order_id:
        _add_link(db, "work_order", obj.work_order_id, obj.work_order_no or "", "pick", obj.id, doc_no, "push")
    return make_response(True, _doc_to_dict(obj, ["items_json"]), f"领料单创建成功：{doc_no}")


@router.post("/picks/{pick_id}/confirm")
def confirm_pick(pick_id: int, db: Session = Depends(get_db)):
    """确认领料：回写数量到工单的 issued_qty"""
    obj = db.query(models.ProductionPick).get(pick_id)
    if not obj:
        return make_response(False, None, "领料单不存在", "40402")
    if obj.status not in (models.ProdDocStatus.DRAFT, models.ProdDocStatus.CONFIRMED):
        return make_response(False, None, "当前状态不允许确认", "40001")

    obj.status = models.ProdDocStatus.CONFIRMED
    # 回写到工单
    if obj.work_order_id:
        wo = db.query(models.ProductionWorkOrderDoc).get(obj.work_order_id)
        if wo:
            items = json.loads(obj.items_json or "[]")
            total_picked = sum(Decimal(str(it.get("picked_qty", 0))) for it in items)
            wo.issued_qty = (wo.issued_qty or 0) + total_picked
            if wo.status == models.ProdDocStatus.RELEASED:
                wo.status = models.ProdDocStatus.IN_PROGRESS
            # 同步回写到组件清单
            cl = db.query(models.ProductionComponentList).filter_by(work_order_id=wo.id).first()
            if cl:
                cl_items = json.loads(cl.items_json or "[]")
                # 简单累加：同物料编码累加已领数量
                for ci in cl_items:
                    for pi in items:
                        if ci.get("material_code") == pi.get("material_code"):
                            ci["issued_qty"] = float(Decimal(str(ci.get("issued_qty", 0))) + Decimal(str(pi.get("picked_qty", 0))))
                cl.items_json = json.dumps(cl_items, ensure_ascii=False)
    db.commit()
    return make_response(True, _doc_to_dict(obj, ["items_json"]), "领料单已确认，数量已回写")


@router.post("/picks/{pick_id}/push-return")
def push_pick_to_return(pick_id: int, db: Session = Depends(get_db)):
    """领料单下推生成退料单"""
    src = db.query(models.ProductionPick).get(pick_id)
    if not src:
        return make_response(False, None, "领料单不存在", "40402")
    acc_id = src.account_set_id
    doc_no = _gen_doc_no("RT", models.ProductionMaterialReturn, db)
    # 复制明细，退料数量默认等于已领数量
    items = json.loads(src.items_json or "[]")
    return_items = [{
        "material_code": it.get("material_code"),
        "material_name": it.get("material_name"),
        "picked_qty": it.get("picked_qty", 0),
        "return_qty": it.get("picked_qty", 0),
        "unit": it.get("unit", "")
    } for it in items]
    obj = models.ProductionMaterialReturn(
        account_set_id=acc_id, doc_no=doc_no,
        pick_id=src.id, pick_no=src.doc_no,
        work_order_id=src.work_order_id, work_order_no=src.work_order_no,
        return_date=datetime.date.today(),
        items_json=json.dumps(return_items, ensure_ascii=False),
        status=models.ProdDocStatus.DRAFT,
        warehouse=src.warehouse
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    _add_link(db, "pick", src.id, src.doc_no, "material_return", obj.id, doc_no, "push")
    return make_response(True, _doc_to_dict(obj, ["items_json"]), f"已下推生成退料单：{doc_no}")


# ============================================================
# 3. 完工入库单
# ============================================================

@router.get("/inbounds")
def list_inbounds(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.ProductionInbound)
    if status:
        q = q.filter(models.ProductionInbound.status == status)
    items = q.order_by(models.ProductionInbound.created_at.desc()).all()
    return make_response(True, [_doc_to_dict(i) for i in items], "ok")


@router.get("/inbounds/{inbound_id}")
def get_inbound(inbound_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.ProductionInbound).get(inbound_id)
    if not obj:
        return make_response(False, None, "入库单不存在", "40403")
    return make_response(True, _doc_to_dict(obj), "ok")


@router.post("/inbounds")
def create_inbound(data: dict, db: Session = Depends(get_db)):
    acc_id = _get_account_set_id(db)
    doc_no = _gen_doc_no("IN", models.ProductionInbound, db)
    obj = models.ProductionInbound(
        account_set_id=acc_id, doc_no=doc_no,
        work_order_id=data.get("work_order_id"),
        work_order_no=data.get("work_order_no"),
        product_id=data.get("product_id"),
        product_name=data.get("product_name"),
        inbound_date=datetime.date.fromisoformat(data["inbound_date"]) if data.get("inbound_date") else None,
        qty=Decimal(str(data.get("qty", 0))),
        qualified_qty=Decimal(str(data.get("qualified_qty", data.get("qty", 0)))),
        defective_qty=Decimal(str(data.get("defective_qty", 0))),
        warehouse=data.get("warehouse"),
        location=data.get("location"),
        status=models.ProdDocStatus.DRAFT,
        remark=data.get("remark"),
        created_by=data.get("created_by")
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    if obj.work_order_id:
        _add_link(db, "work_order", obj.work_order_id, obj.work_order_no or "", "inbound", obj.id, doc_no, "push")
    return make_response(True, _doc_to_dict(obj), f"入库单创建成功：{doc_no}")


@router.post("/inbounds/{inbound_id}/confirm")
def confirm_inbound(inbound_id: int, db: Session = Depends(get_db)):
    """确认入库：回写 completed_qty 到工单"""
    obj = db.query(models.ProductionInbound).get(inbound_id)
    if not obj:
        return make_response(False, None, "入库单不存在", "40403")
    if obj.status not in (models.ProdDocStatus.DRAFT, models.ProdDocStatus.CONFIRMED):
        return make_response(False, None, "当前状态不允许确认", "40001")
    obj.status = models.ProdDocStatus.CONFIRMED
    if obj.work_order_id:
        wo = db.query(models.ProductionWorkOrderDoc).get(obj.work_order_id)
        if wo:
            wo.completed_qty = (wo.completed_qty or 0) + obj.qualified_qty
            if wo.completed_qty >= wo.planned_qty and wo.planned_qty > 0:
                wo.status = models.ProdDocStatus.COMPLETED
                wo.actual_end = datetime.date.today()
            elif wo.status == models.ProdDocStatus.IN_PROGRESS:
                wo.status = models.ProdDocStatus.IN_PROGRESS
    db.commit()
    return make_response(True, _doc_to_dict(obj), "入库单已确认，完工数量已回写")


@router.post("/inbounds/{inbound_id}/push-return-inbound")
def push_inbound_to_return(inbound_id: int, db: Session = Depends(get_db)):
    """入库单下推生成完工退库单"""
    src = db.query(models.ProductionInbound).get(inbound_id)
    if not src:
        return make_response(False, None, "入库单不存在", "40403")
    acc_id = src.account_set_id
    doc_no = _gen_doc_no("RI", models.ProductionReturnInbound, db)
    obj = models.ProductionReturnInbound(
        account_set_id=acc_id, doc_no=doc_no,
        inbound_id=src.id, inbound_no=src.doc_no,
        work_order_id=src.work_order_id, work_order_no=src.work_order_no,
        return_date=datetime.date.today(),
        qty=src.qty,
        reason="质量异常退回",
        status=models.ProdDocStatus.DRAFT
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    _add_link(db, "inbound", src.id, src.doc_no, "return_inbound", obj.id, doc_no, "push")
    return make_response(True, _doc_to_dict(obj), f"已下推生成完工退库单：{doc_no}")


# ============================================================
# 4. 工单下推
# ============================================================

@router.post("/work-orders/{wo_id}/push-pick")
def push_wo_to_pick(wo_id: int, data: dict = None, db: Session = Depends(get_db)):
    """工单下推生成领料单"""
    wo = db.query(models.ProductionWorkOrderDoc).get(wo_id)
    if not wo:
        return make_response(False, None, "工单不存在", "40401")
    if wo.status not in (models.ProdDocStatus.RELEASED, models.ProdDocStatus.IN_PROGRESS):
        return make_response(False, None, "工单未下达，不能下推领料", "40001")

    acc_id = wo.account_set_id
    doc_no = _gen_doc_no("PK", models.ProductionPick, db)
    # 从组件清单复制明细
    cl = db.query(models.ProductionComponentList).filter_by(work_order_id=wo.id).first()
    items = []
    if cl:
        cl_items = json.loads(cl.items_json or "[]")
        for ci in cl_items:
            required = Decimal(str(ci.get("required_qty", 0)))
            issued = Decimal(str(ci.get("issued_qty", 0)))
            # 待领数量 = 需领 - 已领
            to_pick = float(required - issued) if required > issued else 0
            items.append({
                "material_code": ci.get("material_code"),
                "material_name": ci.get("material_name"),
                "planned_qty": float(required),
                "picked_qty": to_pick,
                "unit": ci.get("unit", "")
            })
    pick = models.ProductionPick(
        account_set_id=acc_id, doc_no=doc_no,
        work_order_id=wo.id, work_order_no=wo.doc_no,
        pick_date=datetime.date.today(),
        items_json=json.dumps(items, ensure_ascii=False),
        status=models.ProdDocStatus.DRAFT,
        warehouse=data.get("warehouse") if data else None,
        remark=f"由工单{wo.doc_no}下推生成"
    )
    db.add(pick)
    db.commit()
    db.refresh(pick)
    _add_link(db, "work_order", wo.id, wo.doc_no, "pick", pick.id, doc_no, "push")
    return make_response(True, _doc_to_dict(pick, ["items_json"]), f"已下推生成领料单：{doc_no}")


@router.post("/work-orders/{wo_id}/push-inbound")
def push_wo_to_inbound(wo_id: int, data: dict = None, db: Session = Depends(get_db)):
    """工单下推生成入库单"""
    wo = db.query(models.ProductionWorkOrderDoc).get(wo_id)
    if not wo:
        return make_response(False, None, "工单不存在", "40401")
    if wo.status not in (models.ProdDocStatus.RELEASED, models.ProdDocStatus.IN_PROGRESS, models.ProdDocStatus.COMPLETED):
        return make_response(False, None, "工单未下达，不能下推入库", "40001")

    acc_id = wo.account_set_id
    doc_no = _gen_doc_no("IN", models.ProductionInbound, db)
    # 待入库 = 计划 - 已完工
    pending = float(wo.planned_qty - wo.completed_qty) if wo.planned_qty > wo.completed_qty else 0
    inbound = models.ProductionInbound(
        account_set_id=acc_id, doc_no=doc_no,
        work_order_id=wo.id, work_order_no=wo.doc_no,
        product_id=wo.product_id, product_name=wo.product_name,
        inbound_date=datetime.date.today(),
        qty=Decimal(str(pending)),
        qualified_qty=Decimal(str(pending)),
        defective_qty=Decimal("0"),
        warehouse=data.get("warehouse") if data else None,
        status=models.ProdDocStatus.DRAFT,
        remark=f"由工单{wo.doc_no}下推生成"
    )
    db.add(inbound)
    db.commit()
    db.refresh(inbound)
    _add_link(db, "work_order", wo.id, wo.doc_no, "inbound", inbound.id, doc_no, "push")
    return make_response(True, _doc_to_dict(inbound), f"已下推生成入库单：{doc_no}")


# ============================================================
# 5. BFS双向追溯 + 关系图
# ============================================================

@router.get("/trace/{doc_type}/{doc_id}")
def trace_document(doc_type: str, doc_id: int, db: Session = Depends(get_db)):
    """
    BFS双向追溯：
    - 向上追溯源头（source方向，is_reverse=False的目标端）
    - 向下追踪衍生（target方向，is_reverse=True的来源端）
    返回 { upstream: [...], downstream: [...] }
    """
    visited_up = set()
    visited_down = set()
    upstream = []
    downstream = []

    def bfs_up(doc_type, doc_id, path):
        """向上追溯：找以当前单据为target的正向链接"""
        key = (doc_type, doc_id)
        if key in visited_up:
            return
        visited_up.add(key)
        # 找 target = 当前单据 的正向链接
        links = db.query(models.DocumentLink).filter(
            models.DocumentLink.target_doc_type == doc_type,
            models.DocumentLink.target_doc_id == doc_id,
            models.DocumentLink.is_reverse == False
        ).all()
        for link in links:
            node = {
                "doc_type": link.source_doc_type,
                "doc_id": link.source_doc_id,
                "doc_no": link.source_doc_no,
                "link_type": link.link_type,
                "direction": "up",
                "path": path + [{"type": doc_type, "id": doc_id}]
            }
            upstream.append(node)
            bfs_up(link.source_doc_type, link.source_doc_id, node["path"])

    def bfs_down(doc_type, doc_id, path):
        """向下追踪：找以当前单据为source的正向链接"""
        key = (doc_type, doc_id)
        if key in visited_down:
            return
        visited_down.add(key)
        links = db.query(models.DocumentLink).filter(
            models.DocumentLink.source_doc_type == doc_type,
            models.DocumentLink.source_doc_id == doc_id,
            models.DocumentLink.is_reverse == False
        ).all()
        for link in links:
            node = {
                "doc_type": link.target_doc_type,
                "doc_id": link.target_doc_id,
                "doc_no": link.target_doc_no,
                "link_type": link.link_type,
                "direction": "down",
                "path": path + [{"type": doc_type, "id": doc_id}]
            }
            downstream.append(node)
            bfs_down(link.target_doc_type, link.target_doc_id, node["path"])

    bfs_up(doc_type, doc_id, [])
    bfs_down(doc_type, doc_id, [])

    return make_response(True, {
        "current": {"doc_type": doc_type, "doc_id": doc_id},
        "upstream": upstream,
        "downstream": downstream
    }, "追溯完成")


@router.get("/graph/{doc_type}/{doc_id}")
def graph_data(doc_type: str, doc_id: int, db: Session = Depends(get_db)):
    """
    关系图数据：
    返回 nodes 和 edges，供前端SVG渲染
    nodes: [{id, type, doc_no, status, direction}]
    edges: [{source, target, type, link_type}]
    """
    trace_result = trace_document(doc_type, doc_id, db)
    data = trace_result["data"]

    nodes = []
    edges = []
    node_ids = set()

    def add_node(n_type, n_id, n_no, direction, link_type="push"):
        nid = f"{n_type}_{n_id}"
        if nid in node_ids:
            return nid
        node_ids.add(nid)
        nodes.append({
            "id": nid, "type": n_type, "doc_id": n_id,
            "doc_no": n_no or f"{n_type}#{n_id}",
            "direction": direction, "link_type": link_type
        })
        return nid

    # 中心节点
    center_id = add_node(doc_type, doc_id, doc_type, "center")

    # 上游
    for u in data["upstream"]:
        uid = add_node(u["doc_type"], u["doc_id"], u["doc_no"], "up", u["link_type"])
        # 找到连接关系
        edges.append({"source": uid, "target": center_id, "link_type": u["link_type"], "direction": "up"})

    # 下游
    for d in data["downstream"]:
        did = add_node(d["doc_type"], d["doc_id"], d["doc_no"], "down", d["link_type"])
        edges.append({"source": center_id, "target": did, "link_type": d["link_type"], "direction": "down"})

    return make_response(True, {"nodes": nodes, "edges": edges}, "ok")


# ============================================================
# 6. 其他单据（退料/补料/退库）列表占位
# ============================================================

@router.get("/material-returns")
def list_material_returns(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.ProductionMaterialReturn)
    if status:
        q = q.filter(models.ProductionMaterialReturn.status == status)
    items = q.order_by(models.ProductionMaterialReturn.created_at.desc()).all()
    return make_response(True, [_doc_to_dict(i, ["items_json"]) for i in items], "ok")


@router.get("/replenishes")
def list_replenishes(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.ProductionReplenish)
    if status:
        q = q.filter(models.ProductionReplenish.status == status)
    items = q.order_by(models.ProductionReplenish.created_at.desc()).all()
    return make_response(True, [_doc_to_dict(i, ["items_json"]) for i in items], "ok")


@router.get("/return-inbounds")
def list_return_inbounds(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.ProductionReturnInbound)
    if status:
        q = q.filter(models.ProductionReturnInbound.status == status)
    items = q.order_by(models.ProductionReturnInbound.created_at.desc()).all()
    return make_response(True, [_doc_to_dict(i) for i in items], "ok")
