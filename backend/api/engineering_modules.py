"""
工程导向型ERP 7大核心模块API
============================
1. 项目管理（含WBS树形结构）
2. BOM管理（多版本/EBOM→MBOM/成本卷积/版本对比）
3. ECO变更管理（影响分析/审批流/执行）
4. 生产排程（工序路线/工单/自动排程/冲突检测）
5. WBS成本归集（四路径归集/汇总/预警）
6. 收入确认（完工百分比/里程碑/台账/毛利分析）
7. 设备管理+质量追溯（停机/OEE/维护/IQC/IPQC/FQC）
"""
import json
import io
import re
import uuid
import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from .. import models
from .notifications import push_notification

router = APIRouter()


def _to_date(v):
    if not v: return None
    if isinstance(v, datetime.date): return v
    try: return datetime.date.fromisoformat(str(v)[:10])
    except: return None

def _to_datetime(v):
    if not v: return None
    if isinstance(v, datetime.datetime): return v
    try: return datetime.datetime.fromisoformat(str(v).replace('Z', '+00:00'))
    except: return None

def _parse_level(val):
    """智能解析层级值：支持 'L1'/'L2'/1/2/'Level 1' 等格式，提取数字，失败默认1"""
    if val is None or val == '': return 1
    if isinstance(val, (int, float)): return max(1, int(val))
    m = re.search(r'\d+', str(val))
    return int(m.group()) if m else 1


# ============================================================
# 模块1：项目管理 + WBS树形结构
# ============================================================

@router.get("/projects/board")
def project_board(db: Session = Depends(get_db)):
    """项目看板：按状态分组"""
    try:
        from .engineering import recalc_project_costs
        recalc_project_costs(db)
    except Exception:
        import traceback; traceback.print_exc()
    projects = db.query(models.WBSProject).order_by(models.WBSProject.created_at.desc()).all()
    groups = {"PLANNING": [], "EXECUTING": [], "COMPLETED": [], "CLOSED": []}
    status_names = {"PLANNING": "立项中", "EXECUTING": "进行中", "COMPLETED": "已完工", "CLOSED": "已关闭"}
    for p in projects:
        s = p.status if p.status in groups else "PLANNING"
        groups[s].append({
            "id": p.id, "project_no": p.project_no, "project_name": p.project_name,
            "customer_name": p.customer_name or (p.customer.name if p.customer else "-"),
            "currency": p.currency or "CNY",
            "delivery_mode": p.delivery_mode or "MTO",
            "contract_amount": float(p.contract_amount or 0),
            "budget_cost": float(p.budget_cost or 0),
            "progress_pct": float(p.progress_pct or 0),
            "incurred_cost": float(p.incurred_cost or 0),
            "material_cost": float(p.material_cost or 0),
            "overhead_cost": float(p.overhead_cost or 0),
            "net_profit": float(p.net_profit or 0),
            "gross_margin": float(p.gross_margin or 0),
            "status": p.status, "status_name": status_names.get(p.status, p.status),
            "planned_start": str(p.planned_start) if p.planned_start else None,
            "planned_end": str(p.planned_end) if p.planned_end else None,
            "manager": p.manager,
            "deliverable_count": len(p.deliverables),
        })
    return {"groups": groups, "status_names": status_names, "total": len(projects)}


@router.get("/projects/{project_id}/detail")
def project_detail(project_id: int, db: Session = Depends(get_db)):
    """项目详情：WBS树+成本+收入+里程碑+采购关联"""
    p = db.query(models.WBSProject).filter(models.WBSProject.id == project_id).first()
    if not p: raise HTTPException(404, "项目不存在")
    try:
        from .engineering import recalc_project_costs
        recalc_project_costs(db)
        db.refresh(p)
    except Exception:
        import traceback; traceback.print_exc()
    # WBS树
    nodes = db.query(models.WBSNode).filter(models.WBSNode.project_id == project_id).order_by(models.WBSNode.sort_order).all()
    tree = _build_wbs_tree(nodes)
    # 成本归集
    costs = db.query(models.CostCollection).filter(models.CostCollection.project_id == project_id).all()
    cost_summary = _summarize_costs(costs)
    # 收入确认
    revenues = db.query(models.RevenueRecognition).filter(models.RevenueRecognition.project_id == project_id).order_by(models.RevenueRecognition.confirm_date).all()
    # 里程碑
    milestones = db.query(models.Milestone).filter(models.Milestone.project_id == project_id).order_by(models.Milestone.target_progress).all()
    # 采购关联
    purchases = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.project_id == project_id).all()
    return {
        "project": {"id": p.id, "project_no": p.project_no, "project_name": p.project_name,
                    "customer_name": p.customer_name or (p.customer.name if p.customer else "-"),
                    "currency": p.currency or "CNY",
                    "delivery_mode": p.delivery_mode or "MTO",
                    "contract_amount": float(p.contract_amount or 0), "budget_cost": float(p.budget_cost or 0),
                    "incurred_cost": float(p.incurred_cost or 0), "estimated_total_cost": float(p.estimated_total_cost or 0),
                    "material_cost": float(p.material_cost or 0), "overhead_cost": float(p.overhead_cost or 0),
                    "net_profit": float(p.net_profit or 0), "gross_margin": float(p.gross_margin or 0),
                    "progress_pct": float(p.progress_pct or 0), "recognized_revenue": float(p.recognized_revenue or 0),
                    "status": p.status, "manager": p.manager,
                    "planned_start": str(p.planned_start) if p.planned_start else None,
                    "planned_end": str(p.planned_end) if p.planned_end else None},
        "wbs_tree": tree,
        "cost_summary": cost_summary,
        "revenues": [{"id": r.id, "confirm_date": str(r.confirm_date), "progress": float(r.progress_percent),
                      "total_revenue": float(r.total_revenue), "cumulative_revenue": float(r.cumulative_revenue),
                      "current_revenue": float(r.current_revenue)} for r in revenues],
        "milestones": [{"id": m.id, "name": m.name, "target_progress": float(m.target_progress),
                        "actual_progress": float(m.actual_progress), "status": m.status,
                        "target_date": str(m.target_date) if m.target_date else None,
                        "achieve_date": str(m.achieve_date) if m.achieve_date else None} for m in milestones],
        "purchases": [{"id": o.id, "po_no": o.po_no, "supplier_id": o.supplier_id,
                       "total_amount": float(o.total_amount or 0), "status": o.status} for o in purchases],
    }


def _build_wbs_tree(nodes):
    """构建WBS树形结构"""
    node_map = {}
    roots = []
    for n in nodes:
        node_map[n.id] = {
            "id": n.id, "node_code": n.node_code, "node_name": n.node_name,
            "node_type": n.node_type, "level": n.level, "parent_id": n.parent_id,
            "budget_labor": float(n.budget_labor or 0), "budget_material": float(n.budget_material or 0),
            "budget_outsource": float(n.budget_outsource or 0), "budget_other": float(n.budget_other or 0),
            "budget_cost": float(n.budget_cost or 0), "incurred_cost": float(n.incurred_cost or 0),
            "progress": float(n.progress or 0), "status": n.status,
            "plan_start": str(n.plan_start) if n.plan_start else None,
            "plan_end": str(n.plan_end) if n.plan_end else None,
            "children": [],
        }
    for n in nodes:
        if n.parent_id and n.parent_id in node_map:
            node_map[n.parent_id]["children"].append(node_map[n.id])
        else:
            roots.append(node_map[n.id])
    return roots


@router.post("/projects/{project_id}/wbs-nodes")
def create_wbs_node(project_id: int, body: Dict[str, Any], db: Session = Depends(get_db)):
    """创建WBS节点（支持多级树形）"""
    p = db.query(models.WBSProject).filter(models.WBSProject.id == project_id).first()
    if not p: raise HTTPException(404, "项目不存在")
    parent_id = body.get("parent_id")
    level = 1
    if parent_id:
        parent = db.query(models.WBSNode).filter(models.WBSNode.id == parent_id, models.WBSNode.project_id == project_id).first()
        if parent: level = parent.level + 1
    budget_labor = float(body.get("budget_labor", 0))
    budget_material = float(body.get("budget_material", 0))
    budget_outsource = float(body.get("budget_outsource", 0))
    budget_other = float(body.get("budget_other", 0))
    budget_cost = budget_labor + budget_material + budget_outsource + budget_other
    node = models.WBSNode(
        account_set_id=1, project_id=project_id, node_code=body.get("node_code", ""),
        node_name=body.get("node_name", ""), parent_id=parent_id, level=level,
        node_type=body.get("node_type", "TASK"),
        budget_labor=budget_labor, budget_material=budget_material,
        budget_outsource=budget_outsource, budget_other=budget_other, budget_cost=budget_cost,
        plan_start=_to_date(body.get("plan_start")), plan_end=_to_date(body.get("plan_end")),
        actual_start=_to_date(body.get("actual_start")), actual_end=_to_date(body.get("actual_end")),
        progress=float(body.get("progress", 0)), status=body.get("status", "PLANNING"),
        sort_order=body.get("sort_order", 0),
    )
    db.add(node); db.commit(); db.refresh(node)
    return {"id": node.id, "node_code": node.node_code, "level": node.level, "budget_cost": float(node.budget_cost)}


@router.put("/wbs-nodes/{node_id}")
def update_wbs_node(node_id: int, body: Dict[str, Any], db: Session = Depends(get_db)):
    """更新WBS节点"""
    node = db.query(models.WBSNode).filter(models.WBSNode.id == node_id).first()
    if not node: raise HTTPException(404, "WBS节点不存在")
    for field in ["node_code", "node_name", "node_type", "status", "progress", "sort_order"]:
        if field in body: setattr(node, field, body[field])
    for field in ["budget_labor", "budget_material", "budget_outsource", "budget_other"]:
        if field in body: setattr(node, field, float(body[field]))
    # 重算总预算
    node.budget_cost = float(node.budget_labor or 0) + float(node.budget_material or 0) + float(node.budget_outsource or 0) + float(node.budget_other or 0)
    for field in ["plan_start", "plan_end", "actual_start", "actual_end"]:
        if field in body: setattr(node, field, _to_date(body[field]))
    db.commit(); db.refresh(node)
    return {"id": node.id, "budget_cost": float(node.budget_cost), "progress": float(node.progress)}


# ============================================================
# 模块2：BOM管理
# ============================================================

@router.post("/boms")
def create_bom(body: Dict[str, Any], db: Session = Depends(get_db)):
    """创建BOM（含明细）"""
    product_id = body.get("product_id")
    if not product_id: raise HTTPException(400, "缺少product_id")
    bom = models.BOM(
        account_set_id=1, bom_code=body.get("bom_code"), name=body.get("name"),
        product_id=product_id, version=body.get("version", "V1"),
        bom_type=body.get("bom_type", "EBOM"), status=body.get("status", "DRAFT"),
        effective_date=_to_date(body.get("effective_date")),
    )
    db.add(bom); db.flush()
    # 添加明细
    items = body.get("items", [])
    for idx, item in enumerate(items):
        mat = db.query(models.Material).filter(models.Material.id == item.get("material_id")).first() if item.get("material_id") else None
        bi = models.BOMItem(
            bom_id=bom.id, parent_item_id=item.get("parent_item_id"),
            material_id=item.get("material_id"),
            material_code=mat.code if mat else item.get("material_code"),
            material_name=mat.name if mat else item.get("material_name"),
            spec=mat.specification if mat else item.get("spec"),
            quantity=float(item.get("quantity", 1)), unit=item.get("unit", "个"),
            loss_rate=float(item.get("loss_rate", 0)), scrap_rate=float(item.get("loss_rate", 0)),
            item_type=item.get("item_type", "PURCHASE"),
            process_name=item.get("process_name"), remark=item.get("remark"),
            sequence=item.get("sequence", idx), level=item.get("level", 1),
        )
        db.add(bi)
    db.commit(); db.refresh(bom)
    return {"id": bom.id, "bom_code": bom.bom_code, "version": bom.version, "item_count": len(items)}


@router.get("/boms")
def list_boms(db: Session = Depends(get_db)):
    """BOM列表（供前端下拉选择）"""
    boms = db.query(models.BOM).order_by(models.BOM.id.desc()).all()
    return [{
        "id": b.id, "bom_code": b.bom_code, "name": b.name,
        "version": b.version, "bom_type": b.bom_type, "status": b.status,
        "product_id": b.product_id,
    } for b in boms]


@router.get("/boms/{bom_id}/items")
def get_bom_items(bom_id: int, db: Session = Depends(get_db)):
    """获取BOM明细（树形）"""
    bom = db.query(models.BOM).filter(models.BOM.id == bom_id).first()
    if not bom: raise HTTPException(404, "BOM不存在")
    items = db.query(models.BOMItem).filter(models.BOMItem.bom_id == bom_id).order_by(models.BOMItem.sequence).all()
    return {
        "bom": {"id": bom.id, "bom_code": bom.bom_code, "name": bom.name, "version": bom.version, "bom_type": bom.bom_type, "status": bom.status},
        "items": [{
            "id": i.id, "parent_item_id": i.parent_item_id, "material_id": i.material_id,
            "material_code": i.material_code, "material_name": i.material_name, "spec": i.spec,
            "quantity": float(i.quantity), "unit": i.unit, "loss_rate": float(i.loss_rate or 0),
            "item_type": i.item_type, "process_name": i.process_name, "level": i.level,
        } for i in items]
    }


@router.post("/boms/compare")
def compare_boms(body: Dict[str, Any], db: Session = Depends(get_db)):
    """BOM版本对比：高亮差异行"""
    bom1_id = body.get("bom1_id"); bom2_id = body.get("bom2_id")
    if not bom1_id or not bom2_id: raise HTTPException(400, "需要两个BOM ID")
    items1 = {i.material_id: i for i in db.query(models.BOMItem).filter(models.BOMItem.bom_id == bom1_id).all()}
    items2 = {i.material_id: i for i in db.query(models.BOMItem).filter(models.BOMItem.bom_id == bom2_id).all()}
    all_ids = set(items1.keys()) | set(items2.keys())
    diffs = []
    for mid in all_ids:
        i1 = items1.get(mid); i2 = items2.get(mid)
        if i1 and not i2:
            diffs.append({"type": "removed", "material_id": mid, "material_name": i1.material_name, "quantity": float(i1.quantity)})
        elif not i1 and i2:
            diffs.append({"type": "added", "material_id": mid, "material_name": i2.material_name, "quantity": float(i2.quantity)})
        else:
            changes = {}
            if float(i1.quantity) != float(i2.quantity): changes["quantity"] = {"old": float(i1.quantity), "new": float(i2.quantity)}
            if float(i1.loss_rate or 0) != float(i2.loss_rate or 0): changes["loss_rate"] = {"old": float(i1.loss_rate or 0), "new": float(i2.loss_rate or 0)}
            if i1.item_type != i2.item_type: changes["item_type"] = {"old": i1.item_type, "new": i2.item_type}
            if changes:
                diffs.append({"type": "modified", "material_id": mid, "material_name": i1.material_name, "changes": changes})
    return {"diff_count": len(diffs), "diffs": diffs}


@router.post("/boms/ebom-to-mbom")
def convert_ebom_to_mbom(body: Dict[str, Any], db: Session = Depends(get_db)):
    """EBOM→MBOM转换：自动生成MBOM草稿"""
    ebom_id = body.get("ebom_id")
    ebom = db.query(models.BOM).filter(models.BOM.id == ebom_id).first()
    if not ebom: raise HTTPException(404, "EBOM不存在")
    items = db.query(models.BOMItem).filter(models.BOMItem.bom_id == ebom_id).all()
    # 创建MBOM
    mbom = models.BOM(
        account_set_id=ebom.account_set_id, bom_code=f"MBOM-{ebom.bom_code or ebom.id}",
        name=f"MBOM-{ebom.name or ''}", product_id=ebom.product_id,
        version=ebom.version, bom_type="MBOM", status="DRAFT",
    )
    db.add(mbom); db.flush()
    for item in items:
        mi = models.BOMItem(
            bom_id=mbom.id, parent_item_id=item.parent_item_id, material_id=item.material_id,
            material_code=item.material_code, material_name=item.material_name, spec=item.spec,
            quantity=item.quantity, unit=item.unit, loss_rate=item.loss_rate,
            item_type=item.item_type, level=item.level, sequence=item.sequence,
        )
        db.add(mi)
    db.commit(); db.refresh(mbom)
    return {"id": mbom.id, "bom_code": mbom.bom_code, "message": "MBOM草稿已生成，工艺工程师可补充工序信息后生效"}


@router.get("/boms/{bom_id}/cost-rollup")
def bom_cost_rollup(bom_id: int, db: Session = Depends(get_db)):
    """BOM成本卷积：从底层向上计算成本"""
    bom = db.query(models.BOM).filter(models.BOM.id == bom_id).first()
    if not bom: raise HTTPException(404, "BOM不存在")
    items = db.query(models.BOMItem).filter(models.BOMItem.bom_id == bom_id).all()
    total_material = 0; total_labor = 0; total_outsource = 0
    details = []
    for item in items:
        mat = db.query(models.Material).filter(models.Material.id == item.material_id).first() if item.material_id else None
        unit_price = float(mat.unit_price or 0) if mat else 0
        qty = float(item.quantity or 0) * (1 + float(item.loss_rate or 0) / 100)
        material_cost = unit_price * qty
        total_material += material_cost
        if item.item_type == "OUTSOURCE": total_outsource += material_cost * 0.1
        details.append({"material_name": item.material_name, "quantity": float(item.quantity), "unit_price": unit_price, "cost": round(material_cost, 2), "item_type": item.item_type})
    return {
        "bom_id": bom_id, "bom_code": bom.bom_code,
        "total_material_cost": round(total_material, 2),
        "total_labor_cost": round(total_labor, 2),
        "total_outsource_cost": round(total_outsource, 2),
        "total_cost": round(total_material + total_labor + total_outsource, 2),
        "item_details": details,
    }


# ============================================================
# 模块3：ECO变更管理增强
# ============================================================

@router.post("/eco-orders/{eco_id}/impact-analysis")
def eco_impact_analysis(eco_id: int, db: Session = Depends(get_db)):
    """ECO影响范围分析：自动列出受影响的BOM/工单/采购/库存"""
    eco = db.query(models.ECOChangeOrder).filter(models.ECOChangeOrder.id == eco_id).first()
    if not eco: raise HTTPException(404, "ECO单不存在")
    # 清除旧影响
    db.query(models.EcoImpact).filter(models.EcoImpact.eco_id == eco_id).delete()
    impacts = []
    # 1. 受影响的BOM版本
    if hasattr(eco, 'product_id') and eco.product_id:
        boms = db.query(models.BOM).filter(models.BOM.product_id == eco.product_id, models.BOM.status == "ACTIVE").all()
        for b in boms:
            impacts.append(models.EcoImpact(account_set_id=1, eco_id=eco_id, impact_type="BOM", target_id=b.id, target_desc=f"BOM {b.bom_code or ''} V{b.version}", cost_impact=0))
    # 2. 在产工单
    work_orders = db.query(models.ProductionSchedule).filter(models.ProductionSchedule.status.in_(["PLANNED", "RUNNING"])).all()
    for wo in work_orders:
        impacts.append(models.EcoImpact(account_set_id=1, eco_id=eco_id, impact_type="工单", target_id=wo.id, target_desc=f"工单 {wo.work_order_no or ''} {wo.process_step or ''}", cost_impact=0))
    # 3. 采购订单
    pos = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.status.in_(["PENDING", "APPROVED"])).all()
    for po in pos[:10]:  # 限制数量
        impacts.append(models.EcoImpact(account_set_id=1, eco_id=eco_id, impact_type="采购", target_id=po.id, target_desc=f"采购单 {po.po_no}", cost_impact=0))
    # 4. 库存物料
    inv_total = db.query(func.sum(models.InventoryRecord.quantity)).scalar() if hasattr(models, 'InventoryRecord') else 0
    impacts.append(models.EcoImpact(account_set_id=1, eco_id=eco_id, impact_type="库存", target_desc="现有库存物料可能需报废/返工", cost_impact=0))
    db.add_all(impacts); db.commit()
    return {"impact_count": len(impacts), "impacts": [{"id": i.id, "impact_type": i.impact_type, "target_desc": i.target_desc} for i in impacts]}


@router.get("/eco-orders/{eco_id}/trail")
def eco_trail(eco_id: int, db: Session = Depends(get_db)):
    """变更追溯：全流程记录链"""
    eco = db.query(models.ECOChangeOrder).filter(models.ECOChangeOrder.id == eco_id).first()
    if not eco: raise HTTPException(404, "ECO单不存在")
    impacts = db.query(models.EcoImpact).filter(models.EcoImpact.eco_id == eco_id).all()
    return {
        "eco": {c.name: getattr(eco, c.name, None) for c in eco.__table__.columns},
        "impact_analysis": [{"impact_type": i.impact_type, "target_desc": i.target_desc, "cost_impact": float(i.cost_impact or 0)} for i in impacts],
        "approval_flow": _eco_approval_flow(eco),
    }


def _eco_approval_flow(eco):
    """根据变更类型返回审批流"""
    eco_type = getattr(eco, 'change_type', 'normal') or 'normal'
    if eco_type in ('urgent', '紧急'):
        return ["项目经理审批", "技术总监审批"]
    return ["申请提交", "工艺评审", "项目经理审批", "技术总监审批"]


# ============================================================
# 模块4：生产排程
# ============================================================

@router.get("/work-order-processes")
def list_wo_processes(project_id: Optional[int] = None, work_center: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    """工单工序列表"""
    q = db.query(models.WorkOrderProcess)
    if project_id: q = q.filter(models.WorkOrderProcess.project_id == project_id)
    if work_center: q = q.filter(models.WorkOrderProcess.work_center == work_center)
    if status: q = q.filter(models.WorkOrderProcess.status == status)
    items = q.order_by(models.WorkOrderProcess.plan_start).all()
    return {"total": len(items), "items": [{
        "id": p.id, "work_order_no": p.work_order_no, "project_id": p.project_id,
        "process_seq": p.process_seq, "process_name": p.process_name, "work_center": p.work_center,
        "plan_start": str(p.plan_start) if p.plan_start else None,
        "plan_end": str(p.plan_end) if p.plan_end else None,
        "quantity": p.quantity, "status": p.status,
    } for p in items]}


@router.post("/work-order-processes")
def create_wo_process(body: Dict[str, Any], db: Session = Depends(get_db)):
    """创建工单工序"""
    p = models.WorkOrderProcess(
        account_set_id=1, work_order_no=body.get("work_order_no", ""),
        project_id=body.get("project_id"), product_id=body.get("product_id"),
        process_seq=body.get("process_seq", 1), process_name=body.get("process_name", ""),
        work_center=body.get("work_center"),
        plan_start=_to_datetime(body.get("plan_start")), plan_end=_to_datetime(body.get("plan_end")),
        quantity=body.get("quantity", 0), status=body.get("status", "PENDING"),
    )
    db.add(p); db.commit(); db.refresh(p)
    return {"id": p.id, "work_order_no": p.work_order_no}


@router.post("/schedule/auto")
def auto_schedule(body: Dict[str, Any], db: Session = Depends(get_db)):
    """自动排程引擎：按交期倒排+冲突检测"""
    processes = db.query(models.WorkOrderProcess).filter(models.WorkOrderProcess.status == "PENDING").all()
    if not processes: return {"scheduled": 0, "conflicts": [], "message": "无待排程工单"}
    # 按计划结束日期排序（交期优先）
    processes.sort(key=lambda p: p.plan_end or datetime.datetime.max)
    schedule_result = []
    conflicts = []
    # 工作中心占用记录：{work_center: [(start, end, process_id), ...]}
    wc_occupancy = {}
    for p in processes:
        wc = p.work_center or "默认"
        if wc not in wc_occupancy: wc_occupancy[wc] = []
        start = p.plan_start or datetime.datetime.now()
        end = p.plan_end or (start + datetime.timedelta(hours=8))
        # 冲突检测：同一工作中心同一时段
        for occ_start, occ_end, occ_id in wc_occupancy[wc]:
            if start < occ_end and end > occ_start:
                conflicts.append({
                    "work_center": wc, "process_id": p.id, "work_order_no": p.work_order_no,
                    "conflict_with_id": occ_id,
                    "suggestion": f"建议调整 {p.work_order_no} 的排程时间避开冲突时段",
                })
                break
        wc_occupancy[wc].append((start, end, p.id))
        p.status = "SCHEDULED"
        schedule_result.append({"process_id": p.id, "work_order_no": p.work_order_no, "work_center": wc, "start": str(start), "end": str(end)})
    db.commit()
    return {"scheduled": len(schedule_result), "conflicts": conflicts, "schedule": schedule_result}


@router.get("/schedule/capacity-load")
def capacity_load(db: Session = Depends(get_db)):
    """产能负荷：各工作中心本周负荷率"""
    processes = db.query(models.WorkOrderProcess).filter(models.WorkOrderProcess.status.in_(["SCHEDULED", "RUNNING"])).all()
    wc_load = {}
    for p in processes:
        wc = p.work_center or "默认"
        hours = 0
        if p.plan_start and p.plan_end:
            hours = (p.plan_end - p.plan_start).total_seconds() / 3600
        wc_load[wc] = wc_load.get(wc, 0) + hours
    result = []
    for wc, hours in wc_load.items():
        # 假设每周产能40小时
        capacity = 40
        load_rate = round(hours / capacity * 100, 1) if capacity > 0 else 0
        result.append({"work_center": wc, "planned_hours": round(hours, 1), "capacity_hours": capacity, "load_rate": load_rate, "overload": load_rate > 100})
    result.sort(key=lambda x: x["load_rate"], reverse=True)
    return {"items": result}


@router.get("/schedule/warnings")
def schedule_warnings(db: Session = Depends(get_db)):
    """排程预警面板"""
    processes = db.query(models.WorkOrderProcess).filter(models.WorkOrderProcess.status.in_(["PENDING", "SCHEDULED"])).all()
    today = datetime.date.today()
    overdue = []; today_start = []; bottleneck = []
    for p in processes:
        if p.plan_end and p.plan_end.date() < today and p.status != "COMPLETED":
            overdue.append({"work_order_no": p.work_order_no, "process_name": p.process_name, "plan_end": str(p.plan_end), "type": "即将逾期"})
        if p.plan_start and p.plan_start.date() == today:
            today_start.append({"work_order_no": p.work_order_no, "process_name": p.process_name, "work_center": p.work_center, "type": "今日开工"})
    # 瓶颈工作中心
    load = capacity_load(db)
    bottleneck = [item for item in load["items"] if item["load_rate"] > 90]
    return {"overdue": overdue, "today_start": today_start, "bottleneck": bottleneck}


# ============================================================
# 模块5：WBS成本归集
# ============================================================

@router.post("/cost-collections")
def create_cost_collection(body: Dict[str, Any], db: Session = Depends(get_db)):
    """成本归集入口（四路径）"""
    project_id = body.get("project_id")
    if not project_id: raise HTTPException(400, "缺少project_id")
    cc = models.CostCollection(
        account_set_id=1, project_id=project_id, wbs_id=body.get("wbs_id"),
        cost_type=body.get("cost_type", "其他"), amount=float(body.get("amount", 0)),
        source_type=body.get("source_type", "报销"), source_id=body.get("source_id"),
        source_no=body.get("source_no"), record_date=_to_date(body.get("record_date")) or datetime.date.today(),
        remark=body.get("remark"),
    )
    db.add(cc)
    # 同步到WBS节点和项目
    if cc.wbs_id:
        node = db.query(models.WBSNode).filter(models.WBSNode.id == cc.wbs_id).first()
        if node: node.incurred_cost = float(node.incurred_cost or 0) + cc.amount
    project = db.query(models.WBSProject).filter(models.WBSProject.id == project_id).first()
    if project: project.incurred_cost = float(project.incurred_cost or 0) + cc.amount
    db.commit(); db.refresh(cc)
    return {"id": cc.id, "project_id": cc.project_id, "amount": float(cc.amount)}


@router.get("/cost-collections/summary")
def cost_summary(project_id: Optional[int] = None, db: Session = Depends(get_db)):
    """成本汇总：按WBS节点/成本类型/项目"""
    q = db.query(models.CostCollection)
    if project_id: q = q.filter(models.CostCollection.project_id == project_id)
    costs = q.all()
    # 按成本类型
    by_type = {}
    for c in costs:
        t = c.cost_type or "其他"
        by_type[t] = by_type.get(t, 0) + float(c.amount)
    # 按WBS节点
    by_wbs = {}
    for c in costs:
        key = c.wbs_id or "未归集"
        by_wbs[key] = by_wbs.get(key, 0) + float(c.amount)
    # 预警检测
    warnings = []
    if project_id:
        project = db.query(models.WBSProject).filter(models.WBSProject.id == project_id).first()
        if project:
            total_incurred = float(project.incurred_cost or 0)
            budget = float(project.budget_cost or project.estimated_total_cost or 0)
            if budget > 0:
                ratio = total_incurred / budget * 100
                if ratio > 120: warnings.append({"level": "严重", "msg": f"项目总成本超预算{ratio:.0f}%", "ratio": ratio})
                elif ratio > 110: warnings.append({"level": "警告", "msg": f"项目总成本超预算{ratio:.0f}%", "ratio": ratio})
            # 超合同金额80%预警
            contract = float(project.contract_amount or 0)
            if contract > 0 and total_incurred / contract > 0.8:
                warnings.append({"level": "严重", "msg": "项目总成本已超合同金额80%", "ratio": total_incurred / contract * 100})
    # 返回项目预算和合同额供前端预警展示
    budget_cost = 0
    contract_amount = 0
    if project_id:
        project = db.query(models.WBSProject).filter(models.WBSProject.id == project_id).first()
        if project:
            budget_cost = float(project.budget_cost or project.estimated_total_cost or 0)
            contract_amount = float(project.contract_amount or 0)
    return {
        "total_cost": sum(float(c.amount) for c in costs),
        "by_type": [{"cost_type": k, "amount": round(v, 2)} for k, v in by_type.items()],
        "by_wbs": [{"wbs_id": k, "amount": round(v, 2)} for k, v in by_wbs.items()],
        "warnings": warnings,
        "budget_cost": budget_cost,
        "contract_amount": contract_amount,
    }


def _summarize_costs(costs):
    by_type = {}
    total = 0
    for c in costs:
        t = c.cost_type or "其他"
        by_type[t] = by_type.get(t, 0) + float(c.amount)
        total += float(c.amount)
    return {"total": round(total, 2), "by_type": {k: round(v, 2) for k, v in by_type.items()}}


# ============================================================
# 模块6：收入确认
# ============================================================

@router.post("/revenue-recognitions")
def create_revenue_recognition(body: Dict[str, Any], db: Session = Depends(get_db)):
    """收入确认：完工百分比法"""
    project_id = body.get("project_id")
    project = db.query(models.WBSProject).filter(models.WBSProject.id == project_id).first()
    if not project: raise HTTPException(404, "项目不存在")
    progress = float(body.get("progress_percent", project.progress_pct or 0))
    contract_amount = float(project.contract_amount or 0)
    total_revenue = round(contract_amount * progress / 100, 2)
    # 累计已确认收入
    prev = db.query(models.RevenueRecognition).filter(models.RevenueRecognition.project_id == project_id).order_by(models.RevenueRecognition.confirm_date.desc()).first()
    prev_cumulative = float(prev.cumulative_revenue) if prev else 0
    current_revenue = round(total_revenue - prev_cumulative, 2)
    rr = models.RevenueRecognition(
        account_set_id=1, project_id=project_id,
        confirm_date=_to_date(body.get("confirm_date")) or datetime.date.today(),
        progress_percent=progress, total_revenue=total_revenue,
        cumulative_revenue=total_revenue, current_revenue=current_revenue,
    )
    db.add(rr)
    project.recognized_revenue = total_revenue
    db.commit(); db.refresh(rr)
    # 自动生成凭证
    try:
        from .auto_voucher import trigger_auto_voucher
        trigger_auto_voucher(db, "REVENUE_CONFIRM", project.id, project.project_no, force=True)
    except: pass
    return {"id": rr.id, "progress": progress, "total_revenue": total_revenue, "current_revenue": current_revenue}


@router.get("/revenue-recognitions/ledger")
def revenue_ledger(project_id: Optional[int] = None, db: Session = Depends(get_db)):
    """收入确认台账+毛利分析"""
    q = db.query(models.RevenueRecognition)
    if project_id: q = q.filter(models.RevenueRecognition.project_id == project_id)
    records = q.order_by(models.RevenueRecognition.confirm_date).all()
    items = []
    total_revenue = 0; total_cost = 0
    for r in records:
        project = db.query(models.WBSProject).filter(models.WBSProject.id == r.project_id).first()
        incurred = float(project.incurred_cost) if project else 0
        revenue = float(r.cumulative_revenue)
        gross_profit = revenue - incurred
        total_revenue += float(r.current_revenue)
        total_cost += incurred
        items.append({
            "id": r.id, "project_id": r.project_id, "confirm_date": str(r.confirm_date),
            "progress_percent": float(r.progress_percent), "total_revenue": float(r.total_revenue),
            "cumulative_revenue": float(r.cumulative_revenue), "current_revenue": float(r.current_revenue),
            "incurred_cost": incurred, "gross_profit": gross_profit,
            "gross_margin": round(gross_profit / revenue * 100, 2) if revenue > 0 else 0,
        })
    return {
        "items": items, "total_records": len(items),
        "total_revenue": round(total_revenue, 2),
        "total_gross_profit": round(total_revenue - total_cost, 2),
    }


@router.get("/milestones")
def list_milestones(project_id: Optional[int] = None, db: Session = Depends(get_db)):
    """里程碑列表"""
    q = db.query(models.Milestone)
    if project_id: q = q.filter(models.Milestone.project_id == project_id)
    items = q.order_by(models.Milestone.target_progress).all()
    return {"total": len(items), "items": [{
        "id": m.id, "project_id": m.project_id, "name": m.name,
        "target_progress": float(m.target_progress), "actual_progress": float(m.actual_progress),
        "status": m.status, "target_date": str(m.target_date) if m.target_date else None,
        "achieve_date": str(m.achieve_date) if m.achieve_date else None,
    } for m in items]}


@router.post("/milestones")
def create_milestone(body: Dict[str, Any], db: Session = Depends(get_db)):
    """创建里程碑"""
    m = models.Milestone(
        account_set_id=1, project_id=body.get("project_id"), name=body.get("name", ""),
        target_progress=float(body.get("target_progress", 0)),
        target_date=_to_date(body.get("target_date")),
    )
    db.add(m); db.commit(); db.refresh(m)
    return {"id": m.id, "name": m.name}


@router.put("/milestones/{milestone_id}/achieve")
def achieve_milestone(milestone_id: int, db: Session = Depends(get_db)):
    """里程碑达成：触发收入确认"""
    m = db.query(models.Milestone).filter(models.Milestone.id == milestone_id).first()
    if not m: raise HTTPException(404, "里程碑不存在")
    m.status = "ACHIEVED"; m.achieve_date = datetime.date.today(); m.actual_progress = m.target_progress
    # 触发收入确认
    result = None
    try:
        result = create_revenue_recognition({"project_id": m.project_id, "progress_percent": m.target_progress}, db)
    except: pass
    db.commit()
    return {"id": m.id, "status": m.status, "revenue_triggered": result}


# ============================================================
# 模块7：设备管理 + 质量追溯增强
# ============================================================

@router.post("/downtimes")
def create_downtime(body: Dict[str, Any], db: Session = Depends(get_db)):
    """记录停机"""
    d = models.Downtime(
        account_set_id=1, equipment_id=body.get("equipment_id"),
        start_time=_to_datetime(body.get("start_time")) or datetime.datetime.now(),
        end_time=_to_datetime(body.get("end_time")),
        reason=body.get("reason", "其他"), remark=body.get("remark"),
    )
    if d.start_time and d.end_time:
        d.duration = (d.end_time - d.start_time).total_seconds() / 60
    db.add(d)
    # 更新设备状态
    if body.get("equipment_id"):
        eq = db.query(models.Equipment).filter(models.Equipment.id == body["equipment_id"]).first()
        if eq: eq.status = "IDLE"
    db.commit(); db.refresh(d)
    return {"id": d.id, "duration": float(d.duration or 0)}


@router.get("/downtimes/stats")
def downtime_stats(equipment_id: Optional[int] = None, db: Session = Depends(get_db)):
    """停机统计：按设备/原因"""
    q = db.query(models.Downtime)
    if equipment_id: q = q.filter(models.Downtime.equipment_id == equipment_id)
    downtimes = q.all()
    by_reason = {}; by_equipment = {}
    for d in downtimes:
        r = d.reason or "其他"
        by_reason[r] = by_reason.get(r, {"count": 0, "duration": 0})
        by_reason[r]["count"] += 1
        by_reason[r]["duration"] += float(d.duration or 0)
        eq_key = d.equipment_id or "未知"
        by_equipment[eq_key] = by_equipment.get(eq_key, {"count": 0, "duration": 0})
        by_equipment[eq_key]["count"] += 1
        by_equipment[eq_key]["duration"] += float(d.duration or 0)
    return {
        "total_count": len(downtimes),
        "total_duration": round(sum(float(d.duration or 0) for d in downtimes), 1),
        "by_reason": [{"reason": k, "count": v["count"], "duration": round(v["duration"], 1)} for k, v in by_reason.items()],
        "by_equipment": [{"equipment_id": k, "count": v["count"], "duration": round(v["duration"], 1)} for k, v in by_equipment.items()],
    }


@router.get("/equipments/dashboard")
def equipment_dashboard(db: Session = Depends(get_db)):
    """设备看板：实时状态+OEE+停机TOP5"""
    equipments = db.query(models.Equipment).all()
    status_counts = {"RUNNING": 0, "IDLE": 0, "MAINTENANCE": 0, "SCRAPPED": 0}
    for e in equipments:
        s = e.status if e.status in status_counts else "IDLE"
        status_counts[s] += 1
    # 停机原因TOP5
    stats = downtime_stats(db=db)
    top5 = sorted(stats["by_reason"], key=lambda x: x["duration"], reverse=True)[:5]
    return {
        "total": len(equipments), "status_counts": status_counts,
        "equipments": [{
            "id": e.id, "code": e.equipment_code, "name": e.equipment_name,
            "work_center": e.work_center, "status": e.status,
            "oee": float(e.oee or 0), "availability": float(e.availability or 0),
            "performance": float(e.performance or 0), "quality_rate": float(e.quality_rate or 0),
        } for e in equipments],
        "downtime_top5": top5,
    }


# ============================================================
# 技术管理：合同交付物料拆解 → 采购/加工/装配三类分发
# ============================================================

def _norm_header(h):
    """表头模糊匹配：去括号/空格/转小写"""
    return (h or "").replace("(", "").replace(")", "").replace("（", "").replace("）", "").replace(" ", "").lower()

def _match_field(headers, candidates):
    """在表头中匹配候选字段名，返回列索引"""
    norm = [_norm_header(h) for h in headers]
    for cand in candidates:
        c = _norm_header(cand)
        for i, h in enumerate(norm):
            if h == c: return i
        for i, h in enumerate(norm):
            if c in h: return i
    return -1


@router.get("/technical/projects")
def technical_projects(db: Session = Depends(get_db)):
    """技术管理可选项目：有交付物料的项目"""
    projects = db.query(models.WBSProject).all()
    result = []
    for p in projects:
        deliverable_count = db.query(models.ProjectDeliverable).filter(
            models.ProjectDeliverable.project_id == p.id).count()
        decom_count = db.query(models.TechnicalDecomposition).filter(
            models.TechnicalDecomposition.project_id == p.id).count()
        result.append({
            "id": p.id, "project_no": p.project_no, "project_name": p.project_name,
            "status": p.status, "deliverable_count": deliverable_count,
            "decomposition_count": decom_count,
        })
    return result


@router.get("/technical/{project_id}/decompositions")
def list_decompositions(project_id: int, db: Session = Depends(get_db)):
    """技术分解清单"""
    items = db.query(models.TechnicalDecomposition).filter(
        models.TechnicalDecomposition.project_id == project_id).order_by(
        models.TechnicalDecomposition.id.desc()).all()
    return [{
        "id": i.id, "part_code": i.part_code, "part_name": i.part_name,
        "specification": i.specification, "quantity": float(i.quantity or 1),
        "unit": i.unit, "category": i.category, "dispatch_status": i.dispatch_status,
        "bom_item_id": i.bom_item_id, "source": i.source, "remark": i.remark,
        "created_at": str(i.created_at) if i.created_at else None,
    } for i in items]


@router.post("/technical/{project_id}/import-preview")
async def import_decomposition_preview(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Excel导入预览：解析零件清单，自动匹配字段"""
    project = db.query(models.WBSProject).filter(models.WBSProject.id == project_id).first()
    if not project:
        raise HTTPException(404, "项目不存在")
    try:
        import openpyxl
    except ImportError:
        raise HTTPException(500, "服务器未安装openpyxl库")
    try:
        content = await file.read()
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        ws = wb.active
        rows_raw = list(ws.iter_rows(values_only=True))
        if not rows_raw:
            raise HTTPException(400, "Excel为空")
        headers = [str(c).strip() if c else f"列{j+1}" for j, c in enumerate(rows_raw[0])]
        # 智能匹配字段
        idx_code = _match_field(headers, ["零件编码", "物料编码", "编码", "料号"])
        idx_name = _match_field(headers, ["零件名称", "物料名称", "名称", "品名"])
        idx_spec = _match_field(headers, ["规格", "规格型号", "型号", "spec"])
        idx_qty = _match_field(headers, ["数量", "qty", "quantity"])
        idx_unit = _match_field(headers, ["单位", "unit"])
        idx_cat = _match_field(headers, ["分类", "类型", "category", "可采购", "可加工", "可装配"])
        idx_remark = _match_field(headers, ["备注", "remark"])
        if idx_name < 0:
            raise HTTPException(400, "Excel缺少零件名称列")
        items = []
        for r in rows_raw[1:]:
            if not any(r): continue
            name = str(r[idx_name]).strip() if idx_name < len(r) and r[idx_name] else ""
            if not name: continue
            raw_cat = str(r[idx_cat]).strip() if idx_cat >= 0 and idx_cat < len(r) and r[idx_cat] else ""
            # 分类映射
            cat = "PURCHASABLE"
            if "加工" in raw_cat or "自制" in raw_cat or "manufact" in raw_cat.lower():
                cat = "MANUFACTURABLE"
            elif "装配" in raw_cat or "组装" in raw_cat or "assembl" in raw_cat.lower():
                cat = "ASSEMBLABLE"
            elif "采购" in raw_cat or "外购" in raw_cat or "purchas" in raw_cat.lower():
                cat = "PURCHASABLE"
            items.append({
                "part_code": str(r[idx_code]).strip() if idx_code >= 0 and idx_code < len(r) and r[idx_code] else "",
                "part_name": name,
                "specification": str(r[idx_spec]).strip() if idx_spec >= 0 and idx_spec < len(r) and r[idx_spec] else "",
                "quantity": float(r[idx_qty]) if idx_qty >= 0 and idx_qty < len(r) and r[idx_qty] else 1,
                "unit": str(r[idx_unit]).strip() if idx_unit >= 0 and idx_unit < len(r) and r[idx_unit] else "个",
                "category": cat,
                "remark": str(r[idx_remark]).strip() if idx_remark >= 0 and idx_remark < len(r) and r[idx_remark] else "",
            })
        return {"success": True, "headers": headers, "items": items, "total": len(items)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Excel解析失败: {str(e)}")


@router.post("/technical/{project_id}/import-confirm")
def import_decomposition_confirm(project_id: int, payload: dict, db: Session = Depends(get_db)):
    """确认导入技术分解清单"""
    project = db.query(models.WBSProject).filter(models.WBSProject.id == project_id).first()
    if not project:
        raise HTTPException(404, "项目不存在")
    items = payload.get("items", [])
    count = 0
    for it in items:
        name = (it.get("part_name") or "").strip()
        if not name: continue
        d = models.TechnicalDecomposition(
            project_id=project_id,
            part_code=(it.get("part_code") or "").strip() or None,
            part_name=name,
            specification=(it.get("specification") or "").strip() or None,
            quantity=float(it.get("quantity") or 1),
            unit=(it.get("unit") or "个").strip(),
            category=(it.get("category") or "PURCHASABLE").strip(),
            remark=(it.get("remark") or "").strip() or None,
            source="excel",
        )
        db.add(d)
        count += 1
    db.commit()
    return {"success": True, "imported": count}


@router.post("/technical/{project_id}/load-deliverables")
def load_deliverables_as_decomposition(project_id: int, db: Session = Depends(get_db)):
    """从合同交付物料自动加载为技术拆解项（默认分类为可采购，用户可调整）"""
    project = db.query(models.WBSProject).filter(models.WBSProject.id == project_id).first()
    if not project:
        raise HTTPException(404, "项目不存在")
    deliverables = db.query(models.ProjectDeliverable).filter(
        models.ProjectDeliverable.project_id == project_id).all()
    if not deliverables:
        raise HTTPException(400, "该项目暂无交付物料")
    count = 0
    for d in deliverables:
        td = models.TechnicalDecomposition(
            project_id=project_id,
            deliverable_id=d.id,
            part_code=d.material_code,
            part_name=d.material_name,
            specification=d.specification,
            quantity=d.quantity,
            unit=d.unit,
            category="PURCHASABLE",  # 默认可采购，用户可改
            remark=f"从交付物料#{d.id}加载",
            source="deliverable",
        )
        db.add(td)
        count += 1
    db.commit()
    return {"success": True, "loaded": count}


@router.post("/technical/{project_id}/items")
def add_decomposition_item(project_id: int, payload: dict, db: Session = Depends(get_db)):
    """手动添加分解项"""
    name = (payload.get("part_name") or "").strip()
    if not name:
        raise HTTPException(400, "零件名称不能为空")
    d = models.TechnicalDecomposition(
        project_id=project_id,
        part_code=(payload.get("part_code") or "").strip() or None,
        part_name=name,
        specification=(payload.get("specification") or "").strip() or None,
        quantity=float(payload.get("quantity") or 1),
        unit=(payload.get("unit") or "个").strip(),
        category=(payload.get("category") or "PURCHASABLE").strip(),
        remark=(payload.get("remark") or "").strip() or None,
        source="manual",
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return {"success": True, "id": d.id}


@router.put("/technical/items/{item_id}")
def update_decomposition_item(item_id: int, payload: dict, db: Session = Depends(get_db)):
    """编辑分解项"""
    d = db.query(models.TechnicalDecomposition).filter(models.TechnicalDecomposition.id == item_id).first()
    if not d:
        raise HTTPException(404, "分解项不存在")
    for f in ["part_code", "part_name", "specification", "unit", "category", "remark"]:
        if f in payload:
            setattr(d, f, (str(payload[f]).strip() if payload[f] is not None else None))
    if "quantity" in payload:
        d.quantity = float(payload["quantity"] or 1)
    db.commit()
    return {"success": True}


@router.delete("/technical/items/{item_id}")
def delete_decomposition_item(item_id: int, db: Session = Depends(get_db)):
    """删除分解项"""
    d = db.query(models.TechnicalDecomposition).filter(models.TechnicalDecomposition.id == item_id).first()
    if not d:
        raise HTTPException(404, "分解项不存在")
    db.delete(d)
    db.commit()
    return {"success": True}


def _get_or_create_task(db, project_id):
    """获取或创建项目生产派工任务（用于采购/装配件下发）"""
    task = db.query(models.ProjectProductionTask).filter(
        models.ProjectProductionTask.project_id == project_id).first()
    if not task:
        proj = db.query(models.WBSProject).filter(models.WBSProject.id == project_id).first()
        task_no = f"PT-{project_id}-{datetime.datetime.utcnow().strftime('%H%M%S')}"
        task = models.ProjectProductionTask(
            project_id=project_id, task_no=task_no, status="MATERIALS_UPLOADED")
        db.add(task)
        db.commit()
        db.refresh(task)
    return task


@router.post("/technical/{project_id}/dispatch")
def dispatch_decomposition(project_id: int, payload: dict, db: Session = Depends(get_db)):
    """一键下发：PURCHASABLE→采购需求 / MANUFACTURABLE→委派加工单 / ASSEMBLABLE→生产任务"""
    item_ids = payload.get("item_ids", [])
    if not item_ids:
        raise HTTPException(400, "请选择要下发的零件")
    items = db.query(models.TechnicalDecomposition).filter(
        models.TechnicalDecomposition.id.in_(item_ids),
        models.TechnicalDecomposition.project_id == project_id).all()
    if not items:
        raise HTTPException(404, "未找到选中的分解项")

    task = _get_or_create_task(db, project_id)
    purchase_count = 0
    outsource_count = 0
    assembly_count = 0

    for d in items:
        if d.dispatch_status == "DISPATCHED":
            continue
        if d.category == "PURCHASABLE":
            mr = models.ProjectMaterialRequirement(
                task_id=task.id,
                material_code=d.part_code,
                material_name=d.part_name,
                specification=d.specification,
                quantity=d.quantity, unit=d.unit,
                purchase_status="PENDING",
                source="tech_decomposition",
                remark=f"技术分解下发#{d.id}",
            )
            db.add(mr)
            purchase_count += 1
        elif d.category == "MANUFACTURABLE":
            # 委派加工功能待重新设计：不再自动生成委外加工单，加工件保留在技术分解表
            outsource_count += 0
        elif d.category == "ASSEMBLABLE":
            # 装配件不进采购池，直接标记下发，保留在技术分解表供生产查看
            assembly_count += 1
        d.dispatch_status = "DISPATCHED"

    # 有采购件下发时，推进派工任务状态为「已下发采购」，使其出现在采购需求池
    if purchase_count > 0 and task.status not in ("PROCUREMENT_DISPATCHED", "PURCHASING", "COMPLETED"):
        task.status = "PROCUREMENT_DISPATCHED"
        task.procurement_dispatched_at = datetime.datetime.utcnow()

    db.commit()
    return {"success": True, "purchase": purchase_count, "outsource": outsource_count, "assembly": assembly_count}


@router.get("/technical/outsourcing-orders")
def list_outsourcing_orders(db: Session = Depends(get_db)):
    """委派加工单列表"""
    orders = db.query(models.TechOutsourcingOrder).order_by(models.TechOutsourcingOrder.id.desc()).all()
    return [{
        "id": o.id, "order_no": o.order_no, "project_id": o.project_id,
        "part_name": o.part_name, "specification": o.specification,
        "quantity": float(o.quantity or 1), "unit": o.unit,
        "process_name": o.process_name, "supplier": o.supplier,
        "status": o.status, "remark": o.remark,
        "created_at": str(o.created_at) if o.created_at else None,
    } for o in orders]


@router.put("/technical/outsourcing-orders/{order_id}/status")
def update_outsourcing_status(order_id: int, payload: dict, db: Session = Depends(get_db)):
    """更新委派加工单状态"""
    o = db.query(models.TechOutsourcingOrder).filter(models.TechOutsourcingOrder.id == order_id).first()
    if not o:
        raise HTTPException(404, "委外单不存在")
    status = payload.get("status")
    if status not in ["PENDING", "PROCESSING", "COMPLETED", "CANCELLED"]:
        raise HTTPException(400, "状态无效")
    o.status = status
    for f in ["process_name", "supplier", "remark"]:
        if f in payload:
            setattr(o, f, str(payload[f]).strip() if payload[f] is not None else None)
    db.commit()
    return {"success": True}


@router.get("/technical/decomposition-template")
def download_decomposition_template():
    """下载技术分解Excel模板"""
    try:
        from fastapi.responses import StreamingResponse
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "技术分解清单"
        headers = ["零件编码", "零件名称", "规格型号", "数量", "单位", "分类", "备注"]
        ws.append(headers)
        ws.append(["P-01", "304不锈钢板", "2mmx1220x2440", 5, "张", "可采购", ""])
        ws.append(["M-01", "激光切割件", "按图纸D01", 10, "件", "可加工", "委外加工"])
        ws.append(["A-01", "控制柜装配", "含接线调试", 2, "台", "可装配", ""])
        for i, h in enumerate(headers):
            ws.column_dimensions[openpyxl.utils.get_column_letter(i+1)].width = max(15, len(h)*2)
        buf = io.BytesIO()
        wb.save(buf); buf.seek(0)
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=technical_decomposition_template.xlsx"})
    except Exception as e:
        raise HTTPException(500, f"模板生成失败: {str(e)}")


# ============================================================
# BOM增强：Excel导入 + MRP正推/逆推/共用物料 + 在途物料
# ============================================================

def _get_stock_map(db):
    """获取所有物料库存数量映射 {material_code: total_qty}（单次JOIN查询）"""
    result = {}
    rows = db.query(
        models.Material.code, func.sum(models.InventoryRecord.quantity)
    ).join(models.InventoryRecord, models.InventoryRecord.material_id == models.Material.id
    ).group_by(models.Material.code).all()
    for code, qty in rows:
        if code:
            result[code] = float(qty or 0)
    return result

def _get_intransit_map(db):
    """获取在途物料映射 {material_code: total_qty}"""
    result = {}
    items = db.query(models.InTransitMaterial).filter(
        models.InTransitMaterial.status.in_(["ORDERED", "SHIPPED"])).all()
    for it in items:
        if it.material_code:
            result[it.material_code] = result.get(it.material_code, 0) + float(it.quantity or 0)
    return result

def _flatten_bom_items(db, bom_id):
    """递归展平BOM所有子件，返回扁平列表（含层级、单耗、工件类型等）"""
    items = db.query(models.BOMItem).filter(models.BOMItem.bom_id == bom_id).all()
    # 批量加载物料信息（兜底冗余字段为空的情况）
    mat_ids = list({i.material_id for i in items if i.material_id})
    mat_map = {}
    if mat_ids:
        mats = db.query(models.Material).filter(models.Material.id.in_(mat_ids)).all()
        mat_map = {m.id: m for m in mats}
    flat = []
    def _walk(item, level, parent_qty=1):
        qty = float(item.quantity or 1) * parent_qty
        mat = mat_map.get(item.material_id)
        code = item.material_code or (mat.code if mat else "")
        name = item.material_name or (mat.name if mat else "")
        spec = item.spec or (mat.spec if mat else "")
        grade = item.material_grade or ""
        flat.append({
            "id": item.id, "bom_id": item.bom_id,
            "material_code": code or "",
            "material_name": name or "",
            "spec": spec or "",
            "material_grade": grade or "",
            "surface_treatment": item.surface_treatment or "",
            "item_type": item.item_type or "PURCHASE",
            "process_name": item.process_name or "",
            "unit": item.unit or "个",
            "unit_qty": float(item.quantity or 1),
            "total_qty": qty,
            "bom_level": item.bom_level or level,
            "remark": item.remark or "",
        })
        # 递归子项
        children = [i for i in items if i.parent_item_id == item.id]
        for c in children:
            _walk(c, level + 1, qty)
    # 顶层（parent_item_id为空）
    roots = [i for i in items if not i.parent_item_id]
    for r in roots:
        _walk(r, 1)
    return flat


# =============== BOM工件类型后台自动归类 ===============
# 标准件：即买即用、有标准型号（电气/传动件/辅料），不需图纸
_STD_KEYWORDS = (
    "轴承", "导轨", "丝杆", "丝杠", "气缸", "电磁阀", "PLC", "触摸屏", "伺服", "步进", "电机",
    "接近开关", "光电开关", "传感器", "继电器", "断路器", "接触器", "开关电源", "按钮", "指示灯",
    "电线", "电缆", "线缆", "插头", "接头", "联轴器", "减速机", "减速箱", "同步带", "皮带", "链条",
    "链轮", "齿轮", "螺栓", "螺钉", "螺丝", "螺母", "垫圈", "垫片", "平键", "卡簧", "挡圈",
    "O型圈", "O形圈", "油封", "密封圈", "密封胶", "扎带", "线号管", "波纹管", "气管", "铆钉",
    "弹簧", "风机", "过滤器", "加热管", "温控", "显示屏", "型材", "气源", "真空", "阀门",
)
# 加工件：无现成商品、需图纸定制（机加件/钣金焊接件/线束）
_MAKE_KEYWORDS = (
    "底座", "安装板", "支架", "定位销", "夹具", "轴承座", "法兰", "轴套", "护罩", "防护罩",
    "柜体", "焊接", "集尘罩", "封板", "机架", "框架", "工作台", "转接", "非标", "线束",
    "座", "底板", "压板", "块", "套", "壳", "盖",
)
# 外协表面处理/热处理
_SURFACE_KEYWORDS = ("发黑", "镀铬", "镀锌", "镀镍", "氧化", "阳极", "喷塑", "喷漆", "电泳", "退火", "调质", "淬火", "渗碳", "氮化", "时效", "抛光", "打磨")


def _classify_bom_item(raw_type: str, name: str, grade: str = "", process: str = "", surface: str = "") -> str:
    """工件类型归类：显式类型优先；缺失时按关键词推断（有标准型号→标准件，需图纸加工→自制件）"""
    t = (raw_type or "").upper()
    if "加工" in raw_type or "MACHIN" in t: return "MACHINABLE"
    if "标准" in raw_type or "STANDARD" in t: return "STANDARD"
    if "外协" in raw_type or "OUTSOURCE" in t: return "OUTSOURCE"
    if "装配" in raw_type or "ASSEMBLY" in t: return "ASSEMBLY"
    if "外购" in raw_type or "采购" in raw_type or "PURCHASE" in t: return "PURCHASE"
    # 类型缺失：表面处理/热处理 → 外协（工艺列是制造工序描述，不参与判定，避免"定位销+淬火工艺"误判）
    if any(k in name for k in _SURFACE_KEYWORDS) or any(k in surface for k in _SURFACE_KEYWORDS):
        return "OUTSOURCE"
    # 先判加工件（"轴承座"含"轴承"但仍属加工件，加工件关键词优先）
    if any(k in name for k in _MAKE_KEYWORDS):
        return "MACHINABLE"
    if any(k in name for k in _STD_KEYWORDS):
        return "STANDARD"
    # 常用结构材料（Q235/45钢/铝等）默认需加工
    if any(k in grade for k in ("Q235", "45", "304", "316", "6061", "7075", "铝合金", "不锈钢", "碳钢", "钢", "铝")):
        return "MACHINABLE"
    return "PURCHASE"


@router.post("/bom/import-preview")
async def bom_import_preview(file: UploadFile = File(...), bom_id: Optional[int] = None, db: Session = Depends(get_db)):
    """BOM Excel导入预览：表头[BOM层级,存货编码,工件类型,规格,品名,材质,表面处理,工艺,数量,单位]"""
    try:
        import openpyxl
    except ImportError:
        raise HTTPException(500, "服务器未安装openpyxl库")
    try:
        content = await file.read()
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        ws = wb.active
        rows_raw = list(ws.iter_rows(values_only=True))
        if not rows_raw:
            raise HTTPException(400, "Excel为空")
        headers = [str(c).strip() if c else f"列{j+1}" for j, c in enumerate(rows_raw[0])]
        idx_level = _match_field(headers, ["BOM层级", "层级", "level"])
        idx_code = _match_field(headers, ["存货编码", "零件编码", "物料编码", "代号", "编码", "料号"])
        idx_type = _match_field(headers, ["工件类型", "类型", "item_type"])
        idx_spec = _match_field(headers, ["规格", "规格型号", "spec"])
        idx_name = _match_field(headers, ["品名", "零件名称", "物料名称", "名称"])
        idx_grade = _match_field(headers, ["材质", "material"])
        idx_surface = _match_field(headers, ["表面处理", "surface"])
        idx_process = _match_field(headers, ["工艺", "工序", "process"])
        idx_qty = _match_field(headers, ["数量", "qty", "quantity"])
        idx_unit = _match_field(headers, ["单位", "unit"])
        idx_parent = _match_field(headers, ["物料归属", "归属", "所属部套", "所属组件", "所属总成", "部套", "parent"])
        if idx_name < 0:
            raise HTTPException(400, "Excel缺少品名列")
        items = []
        for r in rows_raw[1:]:
            if not any(r): continue
            name = str(r[idx_name]).strip() if idx_name < len(r) and r[idx_name] else ""
            if not name: continue
            raw_type = str(r[idx_type]).strip() if idx_type >= 0 and idx_type < len(r) and r[idx_type] else ""
            grade = str(r[idx_grade]).strip() if idx_grade >= 0 and idx_grade < len(r) and r[idx_grade] else ""
            surface = str(r[idx_surface]).strip() if idx_surface >= 0 and idx_surface < len(r) and r[idx_surface] else ""
            process = str(r[idx_process]).strip() if idx_process >= 0 and idx_process < len(r) and r[idx_process] else ""
            itype = _classify_bom_item(raw_type, name, grade, process, surface)
            parent_name = str(r[idx_parent]).strip() if idx_parent >= 0 and idx_parent < len(r) and r[idx_parent] else ""
            level = _parse_level(r[idx_level]) if idx_level >= 0 and idx_level < len(r) and r[idx_level] else 1
            if parent_name:
                level = 2  # 有物料归属的零件挂在其归属父件（一级总成）之下
            items.append({
                "bom_level": level,
                "parent_name": parent_name,
                "material_code": str(r[idx_code]).strip() if idx_code >= 0 and idx_code < len(r) and r[idx_code] else "",
                "item_type": itype,
                "spec": str(r[idx_spec]).strip() if idx_spec >= 0 and idx_spec < len(r) and r[idx_spec] else "",
                "material_name": name,
                "material_grade": grade,
                "surface_treatment": surface,
                "process_name": process,
                "quantity": float(r[idx_qty]) if idx_qty >= 0 and idx_qty < len(r) and r[idx_qty] else 1,
                "unit": str(r[idx_unit]).strip() if idx_unit >= 0 and idx_unit < len(r) and r[idx_unit] else "个",
            })
        return {"success": True, "headers": headers, "items": items, "total": len(items)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Excel解析失败: {str(e)}")


@router.post("/bom/{bom_id}/import-confirm")
def bom_import_confirm(bom_id: int, payload: dict, db: Session = Depends(get_db)):
    """确认导入BOM子件：自动匹配/创建Material，按层级构建树形结构；bom_id=0时自动新建BOM（名称取bom_name）"""
    bom = db.query(models.BOM).filter(models.BOM.id == bom_id).first() if bom_id else None
    if not bom:
        bom = models.BOM(
            account_set_id=1, name=(payload.get("bom_name") or "导入BOM").strip() or "导入BOM",
            product_id=0, bom_type="EBOM", status="ACTIVE",
        )
        db.add(bom); db.commit(); db.refresh(bom)
    items = payload.get("items", [])
    account_set_id = bom.account_set_id
    real_bom_id = bom.id  # 自动新建场景下路径参数为0，明细必须挂到新BOM的id上
    # 先按层级排序
    items_sorted = sorted(items, key=lambda x: x.get("bom_level", 1))
    # 清空旧子项
    db.query(models.BOMItem).filter(models.BOMItem.bom_id == real_bom_id).delete()
    code_to_id = {}  # material_code -> material_id
    level_to_item_id = {}  # level -> [bom_item_id]
    parent_name_map = {}  # 物料归属名 -> 一级父件 bom_item_id（同归属复用，不重复创建）
    count = 0
    for it in items_sorted:
        name = (it.get("material_name") or "").strip()
        if not name: continue
        code = (it.get("material_code") or "").strip()
        # 查找或创建Material
        mat = None
        if code:
            mat = db.query(models.Material).filter(models.Material.code == code).first()
        if not mat:
            mat = db.query(models.Material).filter(models.Material.name == name).first()
        if not mat:
            mat = models.Material(
                account_set_id=account_set_id, name=name, code=code or f"AUTO-{bom_id}-{count+1}",
                spec=(it.get("spec") or "").strip(), unit=(it.get("unit") or "个").strip(),
                unit_price=0, type=models.MaterialType.RAW_MATERIAL,
                property=models.MaterialProperty.PURCHASE,
            )
            db.add(mat); db.commit(); db.refresh(mat)
        if code:
            code_to_id[code] = mat.id
        parent_name = (it.get("parent_name") or "").strip()
        parent_id = None
        level = _parse_level(it.get("bom_level") or 1)
        if parent_name:
            # 归属父件（一级总成）：首次出现时创建，同归属复用
            if parent_name not in parent_name_map:
                pmat = db.query(models.Material).filter(models.Material.name == parent_name).first()
                if not pmat:
                    pmat = models.Material(
                        account_set_id=account_set_id, name=parent_name,
                        code=f"AUTO-{bom_id}-G{len(parent_name_map)+1}", unit="套",
                        unit_price=0, type=models.MaterialType.RAW_MATERIAL,
                        property=models.MaterialProperty.INHOUSE,
                    )
                    db.add(pmat); db.commit(); db.refresh(pmat)
                pbi = models.BOMItem(
                    bom_id=real_bom_id, parent_item_id=None, material_id=pmat.id,
                    material_code=pmat.code, material_name=parent_name,
                    quantity=1, unit="套", item_type="ASSEMBLY", bom_level=1,
                )
                db.add(pbi); db.commit(); db.refresh(pbi)
                parent_name_map[parent_name] = pbi.id
                level_to_item_id.setdefault(1, []).append(pbi.id)
            parent_id = parent_name_map[parent_name]
            level = 2
        elif level > 1 and (level - 1) in level_to_item_id:
            parent_id = level_to_item_id[level - 1][-1] if level_to_item_id[level - 1] else None
        bi = models.BOMItem(
            bom_id=real_bom_id, parent_item_id=parent_id, material_id=mat.id,
            material_code=mat.code, material_name=mat.name, spec=it.get("spec"),
            quantity=float(it.get("quantity") or 1), unit=it.get("unit") or "个",
            item_type=it.get("item_type") or "PURCHASE", process_name=it.get("process_name"),
            material_grade=it.get("material_grade"), surface_treatment=it.get("surface_treatment"),
            bom_level=level, remark=it.get("remark"),
        )
        db.add(bi); db.commit(); db.refresh(bi)
        if level not in level_to_item_id:
            level_to_item_id[level] = []
        level_to_item_id[level].append(bi.id)
        count += 1
    # 自动新建的BOM：用第一个一级子件的物料作为所属产品
    if bom.product_id == 0:
        first_l1 = level_to_item_id.get(1, [])
        if first_l1:
            bi = db.query(models.BOMItem).filter(models.BOMItem.id == first_l1[0]).first()
            if bi:
                bom.product_id = bi.material_id
                db.commit()
    # 项目BOM导入：标准件自动下发到采购需求池 + 同步生成采购订单
    purchase_dispatched = 0
    po_no_created = None
    project_id = payload.get("project_id")
    if project_id:
        task = db.query(models.ProjectProductionTask).filter(
            models.ProjectProductionTask.project_id == project_id).first()
        if not task:
            task = models.ProjectProductionTask(
                project_id=project_id,
                task_no=f"PT-{project_id}-{datetime.datetime.utcnow().strftime('%H%M%S')}",
                status="MATERIALS_UPLOADED")
            db.add(task); db.commit(); db.refresh(task)
        # 重新导入时清掉旧的BOM自动下发记录，避免重复
        db.query(models.ProjectMaterialRequirement).filter(
            models.ProjectMaterialRequirement.task_id == task.id,
            models.ProjectMaterialRequirement.source == "bom_import").delete()
        for it in items_sorted:
            if (it.get("item_type") or "").upper() not in ("STANDARD", "PURCHASE"):
                continue
            name = (it.get("material_name") or "").strip()
            if not name:
                continue
            db.add(models.ProjectMaterialRequirement(
                task_id=task.id,
                material_code=(it.get("material_code") or "").strip(),
                material_name=name, specification=(it.get("spec") or ""),
                quantity=float(it.get("quantity") or 1), unit=it.get("unit") or "个",
                purchase_status="PENDING", source="bom_import",
                remark=f"BOM导入自动下发#{bom.id}",
            ))
            purchase_dispatched += 1
        if purchase_dispatched > 0 and task.status not in ("PROCUREMENT_DISPATCHED", "PURCHASING", "COMPLETED"):
            task.status = "PROCUREMENT_DISPATCHED"
            task.procurement_dispatched_at = datetime.datetime.utcnow()
        db.commit()
        # 标准件同步生成采购订单（DRAFT待确认），重新导入时清理旧自动订单防重复
        po_no_created = None
        old_pos = db.query(models.PurchaseOrder).filter(
            models.PurchaseOrder.project_id == project_id,
            models.PurchaseOrder.remark == "BOM导入自动生成",
            models.PurchaseOrder.approval_status == "PENDING").all()
        for opo in old_pos:
            db.query(models.PurchaseOrderItem).filter(
                models.PurchaseOrderItem.purchase_order_id == opo.id).delete()
            db.delete(opo)
        db.commit()
        std_items = db.query(models.BOMItem).filter(
            models.BOMItem.bom_id == bom.id,
            models.BOMItem.item_type.in_(["STANDARD", "PURCHASE"])).order_by(models.BOMItem.id).all()
        po_items_data = []
        for bi in std_items:
            mat = db.query(models.Material).filter(models.Material.id == bi.material_id).first() if bi.material_id else None
            if mat:
                po_items_data.append((bi, mat))
        if po_items_data:
            po = models.PurchaseOrder(
                account_set_id=1,
                po_no=f"PO-{datetime.date.today().strftime('%Y%m%d')}-P{project_id}B{bom.id}-{uuid.uuid4().hex[:4].upper()}",
                supplier_id=None, status="DRAFT", approval_status="PENDING",
                tax_rate=Decimal("13"), discount_amount=0,
                order_date=datetime.date.today(),
                total_amount=0,
                project_id=project_id, bom_line_ref=f"BOM#{bom.id}",
                remark="BOM导入自动生成",
            )
            db.add(po)
            db.flush()
            total = Decimal("0")
            for ln, (bi, mat) in enumerate(po_items_data, start=1):
                qty = Decimal(str(float(bi.quantity or 1)))
                price = Decimal(str(float(mat.unit_price or 0)))
                amt = (qty * price).quantize(Decimal("0.01"))
                db.add(models.PurchaseOrderItem(
                    purchase_order_id=po.id, material_id=mat.id,
                    quantity=int(qty), unit_price=price,
                    line_no=ln, unit=bi.unit or mat.unit or "",
                    amount=amt, source_no=f"BOM#{bom.id}",
                    received_qty=0, remark=bi.material_code or "",
                ))
                total += amt
            po.total_amount = total
            po_no_created = po.po_no
            db.commit()
    # BOM自制件/装配件 → 技术拆解清单：自动纳入生产计划排产（我的工厂·项目产能/生产计划表可见）
    # 注意：只做排产计划，不自动生成委外加工单（委派加工待重新设计，没有安排的事别做）
    production_dispatched = 0
    if project_id:
        # 顺手清掉历史BOM导入残留的待加工单（幂等）
        db.query(models.TechOutsourcingOrder).filter(
            models.TechOutsourcingOrder.project_id == project_id,
            models.TechOutsourcingOrder.status == "PENDING",
            models.TechOutsourcingOrder.remark.like("BOM导入自动下发#%")).delete()
        # 幂等：先删本项目此前BOM导入生成的拆解记录（手工/excel技术拆解的不动）
        db.query(models.TechnicalDecomposition).filter(
            models.TechnicalDecomposition.project_id == project_id,
            models.TechnicalDecomposition.remark == f"BOM导入#{bom.id}").delete()
        db.commit()
        for bi in db.query(models.BOMItem).filter(models.BOMItem.bom_id == bom.id).all():
            itype = (bi.item_type or "").upper()
            if itype not in ("MACHINABLE", "OUTSOURCE", "ASSEMBLY"):
                continue
            name = (bi.material_name or "").strip()
            if not name:
                continue
            db.add(models.TechnicalDecomposition(
                project_id=project_id, deliverable_id=None,
                part_code=bi.material_code or "",
                part_name=name, specification=bi.spec or "",
                quantity=float(bi.quantity or 1), unit=bi.unit or "个",
                category="ASSEMBLABLE" if itype == "ASSEMBLY" else "MANUFACTURABLE",
                dispatch_status="PENDING",
                source="excel", remark=f"BOM导入#{bom.id}",
            ))
            production_dispatched += 1
        if production_dispatched:
            db.commit()
    # 跨部门通知：BOM下发结果上大厅新闻播报
    try:
        _proj = db.query(models.WBSProject).filter(models.WBSProject.id == project_id).first() if project_id else None
        _pname = _proj.project_name if _proj else f"BOM#{bom.id}"
        _parts = []
        if purchase_dispatched:
            _parts.append(f"标准件{purchase_dispatched}项已转采购订单 {po_no_created or ''}")
        if production_dispatched:
            _parts.append(f"自制件{production_dispatched}项已纳入生产计划排产")
        if _parts:
            push_notification(db, f"项目 {_pname} BOM已导入下发", "；".join(_parts) + "，请相关部门跟进",
                              category="技术", source=f"BOM#{bom.id}")
    except Exception:
        pass
    return {"success": True, "imported": count, "bom_id": bom.id,
            "purchase_dispatched": purchase_dispatched, "production_dispatched": production_dispatched,
            "po_no": po_no_created}


@router.get("/bom/import-template")
def bom_import_template():
    """下载BOM导入模板"""
    try:
        from fastapi.responses import StreamingResponse
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "BOM导入"
        headers = ["BOM层级", "存货编码", "工件类型", "规格", "品名", "材质", "表面处理", "工艺", "数量", "单位"]
        ws.append(headers)
        ws.append([1, "P-001", "装配", "总成", "机器人工作站", "Q235", "喷塑", "总装调试", 1, "套"])
        ws.append([2, "M-001", "加工", "2mm钢板", "底座", "304不锈钢", "拉丝", "激光切割+折弯", 2, "件"])
        ws.append([2, "S-001", "标准件", "M8x30", "内六角螺丝", "8.8级", "镀锌", "", 50, "个"])
        ws.append([2, "B-001", "外购", "6轴20kg", "工业机器人", "铸铝", "原色", "", 1, "台"])
        for i, h in enumerate(headers):
            ws.column_dimensions[openpyxl.utils.get_column_letter(i+1)].width = max(14, len(h)*2)
        buf = io.BytesIO(); wb.save(buf); buf.seek(0)
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=bom_import_template.xlsx"})
    except Exception as e:
        raise HTTPException(500, f"模板生成失败: {str(e)}")


@router.get("/bom/{bom_id}/export")
def bom_export(bom_id: int, db: Session = Depends(get_db)):
    """导出BOM全部明细（物料归属/层级/编码/名称/规格/类型/数量/单位/材质/表面处理/工艺/备注），字段与导入模板对齐可回导"""
    try:
        from fastapi.responses import StreamingResponse
        import openpyxl
        bom = db.query(models.BOM).filter(models.BOM.id == bom_id).first()
        if not bom:
            raise HTTPException(404, "BOM不存在")
        items = db.query(models.BOMItem).filter(models.BOMItem.bom_id == bom_id).order_by(
            models.BOMItem.bom_level, models.BOMItem.sequence, models.BOMItem.id).all()
        item_map = {i.id: i for i in items}
        type_map = {"MACHINABLE": "加工件", "STANDARD": "标准件", "PURCHASE": "外购",
                    "OUTSOURCE": "外协", "ASSEMBLY": "装配"}
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "BOM明细"
        bom_name = (bom.name or f"BOM-{bom.id}")
        ws.append([f"BOM：{bom_name}（共{len(items)}项明细）"])
        ws.append([])
        headers = ["物料归属", "BOM层级", "存货编码", "品名", "规格", "工件类型", "数量", "单位", "材质", "表面处理", "工艺", "备注"]
        ws.append(headers)
        for it in items:
            parent_name = ""
            if it.parent_item_id and it.parent_item_id in item_map:
                parent_name = item_map[it.parent_item_id].material_name or ""
            ws.append([
                parent_name,
                int(it.bom_level or 1),
                it.material_code or "",
                it.material_name or "",
                it.spec or "",
                type_map.get(it.item_type or "", it.item_type or ""),
                float(it.quantity or 0),
                it.unit or "",
                it.material_grade or "",
                it.surface_treatment or "",
                it.process_name or "",
                it.remark or "",
            ])
        for i, h in enumerate(headers):
            ws.column_dimensions[openpyxl.utils.get_column_letter(i+1)].width = max(14, len(h)*2)
        ws.column_dimensions['A'].width = 24
        buf = io.BytesIO(); wb.save(buf); buf.seek(0)
        fname = bom_name.replace("/", "-").replace("\\", "-") or f"bom_{bom_id}"
        from urllib.parse import quote
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(fname)}.xlsx"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"BOM导出失败: {str(e)}")


@router.get("/bom/project-import-template")
def bom_project_import_template():
    """下载项目零件分类导入模板（物料归属/零件名称/代号/工件类型/数量/材质）"""
    try:
        from fastapi.responses import StreamingResponse
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "项目零件分类"
        headers = ["物料归属", "零件名称", "代号", "工件类型", "数量", "材质"]
        ws.append(headers)
        ws.append(["机器人搬运系统总成", "六轴机器人本体", "R-30iB", "标准件", 1, "铸铝"])
        ws.append(["机器人搬运系统总成", "机器人底座", "JZ-001", "加工件", 1, "Q235"])
        ws.append(["机器人搬运系统总成", "安装螺栓", "LS-M20", "标准件", 8, "12.9级"])
        ws.append(["", "输送辊道", "SG-002", "加工件", 2, "45钢"])
        for i, h in enumerate(headers):
            ws.column_dimensions[openpyxl.utils.get_column_letter(i+1)].width = max(14, len(h)*2)
        buf = io.BytesIO(); wb.save(buf); buf.seek(0)
        return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=project_parts_template.xlsx"})
    except Exception as e:
        raise HTTPException(500, f"模板生成失败: {str(e)}")


@router.get("/mrp/common-materials")
def mrp_common_materials(bom_ids: str = "", db: Session = Depends(get_db)):
    """共用物料计算：多个BOM展平后group by物料编码求和，按订单顺序依次扣减库存"""
    id_list = [int(x) for x in bom_ids.split(",") if x.strip().isdigit()] if bom_ids else []
    if not id_list:
        boms = db.query(models.BOM).all()
        id_list = [b.id for b in boms]
    stock = _get_stock_map(db)
    # 按BOM顺序汇总需求
    material_demands = {}  # code -> {name, spec, unit, type, total_qty, from_boms:[{bom_id,bom_name,qty}]}
    for bid in id_list:
        bom = db.query(models.BOM).filter(models.BOM.id == bid).first()
        if not bom: continue
        flat = _flatten_bom_items(db, bid)
        for it in flat:
            code = it["material_code"] or f"NAME:{it['material_name']}"
            if code not in material_demands:
                material_demands[code] = {
                    "material_code": it["material_code"], "material_name": it["material_name"],
                    "spec": it["spec"], "unit": it["unit"], "item_type": it["item_type"],
                    "total_qty": 0, "from_boms": [],
                }
            material_demands[code]["total_qty"] += it["total_qty"]
            material_demands[code]["from_boms"].append({"bom_id": bid, "bom_name": bom.name or bom.bom_code or str(bid), "qty": it["total_qty"]})
    # 计算扣减
    result = []
    for code, m in material_demands.items():
        req = m["total_qty"]
        stk = stock.get(m["material_code"], 0) if m["material_code"] else 0
        deficit = req - stk
        result.append({
            **m, "stock_qty": stk, "deficit_qty": deficit,
            "status": "缺料" if deficit > 0 else "充足",
        })
    result.sort(key=lambda x: x["deficit_qty"], reverse=True)
    return result


@router.get("/mrp/forward")
def mrp_forward(bom_id: int, order_qty: int = 1, db: Session = Depends(get_db)):
    """MRP正推：根据订单需求量计算自制/外购/外协欠料表"""
    bom = db.query(models.BOM).filter(models.BOM.id == bom_id).first()
    if not bom:
        raise HTTPException(404, "BOM不存在")
    flat = _flatten_bom_items(db, bom_id)
    stock = _get_stock_map(db)
    intransit = _get_intransit_map(db)
    self_made = []  # 自制欠料（MACHINABLE/ASSEMBLY）
    purchase = []   # 外购欠料（PURCHASE/STANDARD）
    outsource = []  # 外协欠料（OUTSOURCE）
    for it in flat:
        total_req = it["total_qty"] * order_qty
        stk = stock.get(it["material_code"], 0) if it["material_code"] else 0
        transit = intransit.get(it["material_code"], 0) if it["material_code"] else 0
        available = stk + transit
        deficit = total_req - available
        row = {**it, "order_qty": order_qty, "total_req": total_req,
               "stock_qty": stk, "intransit_qty": transit, "deficit_qty": deficit,
               "shortage": deficit > 0}
        t = it["item_type"]
        if t in ["MACHINABLE", "ASSEMBLY"]:
            self_made.append(row)
        elif t == "OUTSOURCE":
            outsource.append(row)
        else:
            purchase.append(row)
    return {
        "bom_id": bom_id, "bom_name": bom.name or bom.bom_code, "order_qty": order_qty,
        "self_made": self_made, "purchase": purchase, "outsource": outsource,
        "summary": {
            "self_made_shortage": sum(1 for r in self_made if r["shortage"]),
            "purchase_shortage": sum(1 for r in purchase if r["shortage"]),
            "outsource_shortage": sum(1 for r in outsource if r["shortage"]),
        }
    }


@router.get("/mrp/backward")
def mrp_backward(bom_id: int, db: Session = Depends(get_db)):
    """逆推：根据库存数量计算可生产成品数量 = min(floor(库存/单耗))"""
    bom = db.query(models.BOM).filter(models.BOM.id == bom_id).first()
    if not bom:
        raise HTTPException(404, "BOM不存在")
    flat = _flatten_bom_items(db, bom_id)
    stock = _get_stock_map(db)
    capacities = []
    min_capacity = None
    for it in flat:
        # 只算叶子节点（单耗）
        unit_qty = it["unit_qty"]
        if unit_qty <= 0: continue
        stk = stock.get(it["material_code"], 0) if it["material_code"] else 0
        cap = int(stk // unit_qty)
        capacities.append({**it, "stock_qty": stk, "unit_qty": unit_qty, "capacity": cap})
        if min_capacity is None or cap < min_capacity:
            min_capacity = cap
    return {
        "bom_id": bom_id, "bom_name": bom.name or bom.bom_code,
        "max_production": min_capacity or 0,
        "capacities": capacities,
    }


# ============================================================
# 在途物料管理
# ============================================================

@router.get("/in-transit-materials")
def list_in_transit(db: Session = Depends(get_db)):
    items = db.query(models.InTransitMaterial).order_by(models.InTransitMaterial.id.desc()).all()
    return [{
        "id": i.id, "material_code": i.material_code, "material_name": i.material_name,
        "specification": i.specification, "quantity": float(i.quantity or 0), "unit": i.unit,
        "transit_type": i.transit_type, "supplier": i.supplier, "order_no": i.order_no,
        "status": i.status, "expected_arrival": str(i.expected_arrival) if i.expected_arrival else None,
        "remark": i.remark, "created_at": str(i.created_at) if i.created_at else None,
    } for i in items]


@router.post("/in-transit-materials")
def add_in_transit(payload: dict, db: Session = Depends(get_db)):
    name = (payload.get("material_name") or "").strip()
    if not name:
        raise HTTPException(400, "物料名称不能为空")
    it = models.InTransitMaterial(
        material_code=(payload.get("material_code") or "").strip() or None,
        material_name=name,
        specification=(payload.get("specification") or "").strip() or None,
        quantity=float(payload.get("quantity") or 0),
        unit=(payload.get("unit") or "个").strip(),
        transit_type=(payload.get("transit_type") or "PURCHASE").strip(),
        supplier=(payload.get("supplier") or "").strip() or None,
        order_no=(payload.get("order_no") or "").strip() or None,
        status=(payload.get("status") or "ORDERED").strip(),
        expected_arrival=_to_date(payload.get("expected_arrival")),
        remark=(payload.get("remark") or "").strip() or None,
    )
    db.add(it); db.commit(); db.refresh(it)
    return {"success": True, "id": it.id}


@router.put("/in-transit-materials/{item_id}/status")
def update_in_transit_status(item_id: int, payload: dict, db: Session = Depends(get_db)):
    it = db.query(models.InTransitMaterial).filter(models.InTransitMaterial.id == item_id).first()
    if not it:
        raise HTTPException(404, "在途物料不存在")
    status = payload.get("status")
    if status not in ["ORDERED", "SHIPPED", "ARRIVED"]:
        raise HTTPException(400, "状态无效")
    it.status = status
    db.commit()
    return {"success": True}


@router.delete("/in-transit-materials/{item_id}")
def delete_in_transit(item_id: int, db: Session = Depends(get_db)):
    it = db.query(models.InTransitMaterial).filter(models.InTransitMaterial.id == item_id).first()
    if not it:
        raise HTTPException(404, "在途物料不存在")
    db.delete(it); db.commit()
    return {"success": True}


@router.get("/orders/{order_id}/material-analysis")
def order_material_analysis(order_id: int, db: Session = Depends(get_db)):
    """订单物料构成分析：订单关联项目的所有BOM物料构成+欠料量+红色缺料标记"""
    # order_id 复用 project_id（简化处理）
    project = db.query(models.WBSProject).filter(models.WBSProject.id == order_id).first()
    if not project:
        raise HTTPException(404, "项目不存在")
    # 查找项目关联的BOM（通过deliverables的material匹配）
    result = []
    stock = _get_stock_map(db)
    intransit = _get_intransit_map(db)
    boms = db.query(models.BOM).all()
    for bom in boms:
        flat = _flatten_bom_items(db, bom.id)
        if not flat: continue
        for it in flat:
            stk = stock.get(it["material_code"], 0) if it["material_code"] else 0
            transit = intransit.get(it["material_code"], 0) if it["material_code"] else 0
            deficit = it["total_qty"] - stk - transit
            result.append({
                **it, "bom_name": bom.name or bom.bom_code or str(bom.id),
                "stock_qty": stk, "intransit_qty": transit, "deficit_qty": deficit,
                "shortage": deficit > 0,
            })
    result.sort(key=lambda x: (x["shortage"], -x["deficit_qty"]), reverse=True)
    return {"project_id": order_id, "project_name": project.project_name, "materials": result}


@router.get("/sales-orders")
def list_sales_orders(db: Session = Depends(get_db)):
    """销售订单列表（供订单物料分析选择）"""
    orders = db.query(models.SalesOrder).order_by(models.SalesOrder.id.desc()).all()
    result = []
    for o in orders:
        customer = db.query(models.Customer).filter(models.Customer.id == o.customer_id).first() if o.customer_id else None
        items_count = db.query(models.SalesOrderItem).filter(models.SalesOrderItem.sales_order_id == o.id).count()
        total_qty = sum(float(i.quantity or 0) for i in o.items)
        result.append({
            "id": o.id, "so_no": o.so_no,
            "customer_name": customer.name if customer else "-",
            "delivery_date": str(o.delivery_date) if o.delivery_date else None,
            "status": o.status, "items_count": items_count, "total_qty": total_qty,
        })
    return result


@router.get("/sales-orders/{so_id}/material-analysis")
def sales_order_material_analysis(so_id: int, db: Session = Depends(get_db)):
    """销售订单物料分析：按订单产品BOM展开，计算需求+库存+缺料"""
    order = db.query(models.SalesOrder).filter(models.SalesOrder.id == so_id).first()
    if not order: raise HTTPException(404, "销售订单不存在")
    stock = _get_stock_map(db)
    intransit = _get_intransit_map(db)
    # 按物料编码汇总（多订单产品BOM可能共用物料）
    agg = {}
    for oi in order.items:
        mat = db.query(models.Material).filter(models.Material.id == oi.material_id).first()
        if not mat: continue
        # 查找该产品关联的BOM
        boms = db.query(models.BOM).filter(models.BOM.product_id == mat.id).all()
        for bom in boms:
            flat = _flatten_bom_items(db, bom.id)
            if not flat: continue
            for it in flat:
                code = it.get("material_code", "")
                if not code: continue
                # 需求 = 订单数量 × BOM单耗
                demand = float(it.get("total_qty", 0)) * float(oi.quantity or 0)
                if code not in agg:
                    agg[code] = {
                        "material_code": code, "material_name": it.get("material_name", ""),
                        "spec": it.get("spec", ""), "unit": it.get("unit", ""),
                        "item_type": it.get("item_type", "PURCHASE"),
                        "demand_qty": 0,
                    }
                agg[code]["demand_qty"] += demand
    # 计算库存和缺料
    materials = []
    for code, m in agg.items():
        stk = stock.get(code, 0)
        transit = intransit.get(code, 0)
        # 可分配库存 = 现有库存 + 在途
        allocatable = stk + transit
        deficit = m["demand_qty"] - allocatable
        m["stock_qty"] = stk
        m["intransit_qty"] = transit
        m["allocatable_qty"] = allocatable
        m["deficit_qty"] = max(deficit, 0)
        m["shortage"] = deficit > 0
        materials.append(m)
    # 排序：缺料在前
    materials.sort(key=lambda x: (not x["shortage"], -x["deficit_qty"]))
    return {
        "so_id": so_id, "so_no": order.so_no,
        "materials": materials, "total": len(materials),
        "shortage_count": sum(1 for m in materials if m["shortage"]),
    }


@router.get("/mrp/shortage-schedule")
def shortage_schedule(start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    """物料欠料表：按日期展开所有销售订单的物料需求，左边物料信息+右边每日需求量"""
    from datetime import datetime, timedelta, date
    if not start_date:
        start_date = date.today().isoformat()
    if not end_date:
        end_date = (date.today() + timedelta(days=30)).isoformat()
    try:
        sd = datetime.strptime(start_date, "%Y-%m-%d").date()
        ed = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(400, "日期格式应为YYYY-MM-DD")
    # 生成日期列表
    dates = []
    d = sd
    while d <= ed:
        dates.append(d.isoformat())
        d += timedelta(days=1)
    # 聚合：code -> {material_info, daily: {date: qty}, total_demand}
    agg = {}

    # 第一步：把所有活跃BOM的物料都纳入欠料表（基础需求：按1个产品计算）
    boms = db.query(models.BOM).filter(models.BOM.status == 'ACTIVE').all()
    for bom in boms:
        flat = _flatten_bom_items(db, bom.id)
        if not flat: continue
        for it in flat:
            code = it.get("material_code", "")
            if not code: continue
            demand = float(it.get("total_qty", 0))
            req_date_str = dates[0]
            if code not in agg:
                agg[code] = {
                    "material_code": code, "material_name": it.get("material_name", ""),
                    "spec": it.get("spec", ""), "unit": it.get("unit", ""),
                    "daily": {}, "total_demand": 0,
                }
            agg[code]["daily"][req_date_str] = agg[code]["daily"].get(req_date_str, 0) + demand
            agg[code]["total_demand"] += demand

    # 第二步：叠加销售订单的物料需求
    orders = db.query(models.SalesOrder).all()
    for order in orders:
        # 需求日期：优先交付日期，否则用创建日期
        req_date = order.delivery_date or (order.created_at.date() if order.created_at else sd)
        req_date_str = req_date.isoformat()
        if req_date_str not in dates:
            # 如果不在范围内，归到最近的日期
            if req_date < sd:
                req_date_str = dates[0]
            else:
                req_date_str = dates[-1]
        for oi in order.items:
            mat = db.query(models.Material).filter(models.Material.id == oi.material_id).first()
            if not mat: continue
            boms = db.query(models.BOM).filter(models.BOM.product_id == mat.id).all()
            for bom in boms:
                flat = _flatten_bom_items(db, bom.id)
                if not flat: continue
                for it in flat:
                    code = it.get("material_code", "")
                    if not code: continue
                    demand = float(it.get("total_qty", 0)) * float(oi.quantity or 0)
                    if code not in agg:
                        agg[code] = {
                            "material_code": code, "material_name": it.get("material_name", ""),
                            "spec": it.get("spec", ""), "unit": it.get("unit", ""),
                            "daily": {}, "total_demand": 0,
                        }
                    agg[code]["daily"][req_date_str] = agg[code]["daily"].get(req_date_str, 0) + demand
                    agg[code]["total_demand"] += demand
    # 合并库存
    stock = _get_stock_map(db)
    intransit = _get_intransit_map(db)
    materials = []
    for code, m in agg.items():
        stk = stock.get(code, 0)
        transit = intransit.get(code, 0)
        allocatable = stk + transit
        deficit = m["total_demand"] - allocatable
        m["stock_qty"] = stk
        m["intransit_qty"] = transit
        m["allocatable_qty"] = allocatable
        m["deficit_qty"] = max(deficit, 0)
        m["shortage"] = deficit > 0
        materials.append(m)
    # 排序：缺料在前
    materials.sort(key=lambda x: (not x["shortage"], -x["deficit_qty"]))
    return {
        "start_date": start_date, "end_date": end_date,
        "dates": dates, "materials": materials,
        "total": len(materials),
        "shortage_count": sum(1 for m in materials if m["shortage"]),
    }


@router.post("/inspections")
def create_inspection(body: Dict[str, Any], db: Session = Depends(get_db)):
    """创建检验单（IQC/IPQC/FQC）"""
    insp = models.Inspection(
        account_set_id=1, inspect_type=body.get("inspect_type", "IQC"),
        source_type=body.get("source_type"), source_id=body.get("source_id"), source_no=body.get("source_no"),
        batch_no=body.get("batch_no"), material_id=body.get("material_id"),
        result=body.get("result", "PENDING"), inspector=body.get("inspector"),
        inspect_date=_to_date(body.get("inspect_date")) or datetime.date.today(),
        qualified_qty=float(body.get("qualified_qty", 0)), unqualified_qty=float(body.get("unqualified_qty", 0)),
        remark=body.get("remark"),
    )
    db.add(insp); db.flush()
    # 添加检验明细
    for item in body.get("items", []):
        ii = models.InspectionItem(
            inspection_id=insp.id, item_name=item.get("item_name", ""),
            standard=item.get("standard"), actual_value=item.get("actual_value"),
            result=item.get("result", "PENDING"),
        )
        db.add(ii)
    db.commit(); db.refresh(insp)
    return {"id": insp.id, "inspect_type": insp.inspect_type, "result": insp.result}


@router.get("/inspections")
def list_inspections(inspect_type: Optional[str] = None, result: Optional[str] = None, db: Session = Depends(get_db)):
    """检验单列表"""
    q = db.query(models.Inspection)
    if inspect_type: q = q.filter(models.Inspection.inspect_type == inspect_type)
    if result: q = q.filter(models.Inspection.result == result)
    items = q.order_by(models.Inspection.inspect_date.desc()).all()
    return {"total": len(items), "items": [{
        "id": i.id, "inspect_type": i.inspect_type, "source_no": i.source_no,
        "batch_no": i.batch_no, "result": i.result, "inspector": i.inspector,
        "inspect_date": str(i.inspect_date) if i.inspect_date else None,
        "qualified_qty": float(i.qualified_qty or 0), "unqualified_qty": float(i.unqualified_qty or 0),
    } for i in items]}


@router.get("/quality/dashboard")
def quality_dashboard(db: Session = Depends(get_db)):
    """质量看板：合格率趋势+不良TOP5"""
    inspections = db.query(models.Inspection).all()
    # 按类型统计
    by_type = {}
    for i in inspections:
        t = i.inspect_type
        if t not in by_type: by_type[t] = {"total": 0, "pass": 0}
        by_type[t]["total"] += 1
        if i.result == "PASS": by_type[t]["pass"] += 1
    # 不良TOP5（按不良数）
    fail_items = [i for i in inspections if i.result == "FAIL"]
    fail_by_reason = {}
    for i in fail_items:
        reason = i.remark or "未知"
        fail_by_reason[reason] = fail_by_reason.get(reason, 0) + 1
    top5 = sorted(fail_by_reason.items(), key=lambda x: x[1], reverse=True)[:5]
    return {
        "total_inspections": len(inspections),
        "by_type": [{
            "type": t, "total": v["total"], "pass": v["pass"],
            "pass_rate": round(v["pass"] / v["total"] * 100, 2) if v["total"] > 0 else 0
        } for t, v in by_type.items()],
        "fail_top5": [{"reason": r, "count": c} for r, c in top5],
    }


# ============================================================
# PMC模块：生产物料控制（主计划→排产→物料需求联动）
# ============================================================

def _pmc_to_date(v):
    if isinstance(v, datetime.date): return v
    if isinstance(v, str):
        try: return datetime.date.fromisoformat(v[:10])
        except: return None
    return None


def _pmc_schedule_no():
    return "PMC" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")


@router.get("/pmc/lines")
def pmc_list_lines(db: Session = Depends(get_db)):
    lines = db.query(models.PMCProductionLine).order_by(models.PMCProductionLine.id.desc()).all()
    return [{
        "id": l.id, "line_code": l.line_code, "line_name": l.line_name, "workshop": l.workshop,
        "daily_capacity": float(l.daily_capacity or 0), "shift_hours": float(l.shift_hours or 8),
        "shift_count": l.shift_count or 1, "max_overtime_hours": float(l.max_overtime_hours or 3),
        "process_codes": l.process_codes, "status": l.status, "remark": l.remark,
    } for l in lines]


@router.post("/pmc/lines")
def pmc_add_line(payload: dict, db: Session = Depends(get_db)):
    name = (payload.get("line_name") or "").strip()
    if not name:
        raise HTTPException(400, "生产线名称不能为空")
    line = models.PMCProductionLine(
        account_set_id=1,
        line_code=(payload.get("line_code") or "").strip() or ("LINE" + str(datetime.datetime.now().timestamp())[-6:]),
        line_name=name,
        workshop=(payload.get("workshop") or "").strip() or None,
        daily_capacity=float(payload.get("daily_capacity") or 0),
        shift_hours=float(payload.get("shift_hours") or 8),
        shift_count=int(payload.get("shift_count") or 1),
        max_overtime_hours=float(payload.get("max_overtime_hours") or 3),
        process_codes=(payload.get("process_codes") or "").strip() or None,
        status=(payload.get("status") or "ACTIVE").strip(),
        remark=(payload.get("remark") or "").strip() or None,
    )
    db.add(line); db.commit(); db.refresh(line)
    return {"success": True, "id": line.id}


@router.put("/pmc/lines/{line_id}")
def pmc_update_line(line_id: int, payload: dict, db: Session = Depends(get_db)):
    line = db.query(models.PMCProductionLine).filter(models.PMCProductionLine.id == line_id).first()
    if not line: raise HTTPException(404, "生产线不存在")
    for k in ["line_code", "line_name", "workshop", "daily_capacity", "shift_hours",
              "shift_count", "max_overtime_hours", "process_codes", "status", "remark"]:
        if k in payload: setattr(line, k, payload[k])
    db.commit()
    return {"success": True}


@router.delete("/pmc/lines/{line_id}")
def pmc_delete_line(line_id: int, db: Session = Depends(get_db)):
    line = db.query(models.PMCProductionLine).filter(models.PMCProductionLine.id == line_id).first()
    if not line: raise HTTPException(404, "生产线不存在")
    db.delete(line); db.commit()
    return {"success": True}


@router.get("/pmc/capacity-analysis")
def pmc_capacity_analysis(start: Optional[str] = None, end: Optional[str] = None, db: Session = Depends(get_db)):
    """产能负荷分析：按生产线/工序统计需求 vs 产能，标记瓶颈"""
    sd = _pmc_to_date(start) or datetime.date.today()
    ed = _pmc_to_date(end) or (sd + datetime.timedelta(days=30))
    days = max((ed - sd).days + 1, 1)
    # 加载有效生产线
    lines = db.query(models.PMCProductionLine).filter(models.PMCProductionLine.status == "ACTIVE").all()
    # 加载时间段内排产单
    schedules = db.query(models.PMCSchedule).filter(
        models.PMCSchedule.plan_start_date <= ed,
        models.PMCSchedule.plan_end_date >= sd,
        models.PMCSchedule.status != "CANCELLED"
    ).all()
    # 按生产线汇总需求
    line_load = {}
    for l in lines:
        daily_cap = float(l.daily_capacity or 0)
        shift_count = int(l.shift_count or 1)
        shift_hours = float(l.shift_hours or 8)
        max_ot = float(l.max_overtime_hours or 3)
        cap = daily_cap * days * shift_count
        # 考虑加班产能
        overtime_cap = daily_cap * days * max_ot / max(shift_hours, 0.1)
        line_load[l.id] = {
            "line_id": l.id, "line_code": l.line_code, "line_name": l.line_name,
            "workshop": l.workshop, "process_codes": l.process_codes,
            "days": days,
            "standard_capacity": round(cap, 2),
            "max_capacity": round(cap + overtime_cap, 2),
            "demand_qty": 0, "utilization": 0, "bottleneck": False,
        }
    # 汇总排产需求
    for s in schedules:
        lid = s.line_id
        demand = float(s.demand_qty or 0)
        if lid and lid in line_load:
            line_load[lid]["demand_qty"] += demand
        else:
            # 未指定生产线的需求，单独汇总
            if 0 not in line_load:
                line_load[0] = {
                    "line_id": 0, "line_code": "UNASSIGNED", "line_name": "未分配",
                    "workshop": "-", "process_codes": "-", "days": days,
                    "standard_capacity": 0, "max_capacity": 0,
                    "demand_qty": 0, "utilization": 0, "bottleneck": False,
                }
            line_load[0]["demand_qty"] += demand
    # 计算利用率和瓶颈
    result = []
    for v in line_load.values():
        if v["standard_capacity"] > 0:
            v["utilization"] = round(v["demand_qty"] / v["standard_capacity"] * 100, 1)
            v["bottleneck"] = v["demand_qty"] > v["standard_capacity"]
        result.append(v)
    result.sort(key=lambda x: -x["utilization"])
    return {"start": str(sd), "end": str(ed), "days": days, "lines": result}


@router.get("/pmc/schedules")
def pmc_list_schedules(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.PMCSchedule)
    if status: q = q.filter(models.PMCSchedule.status == status)
    items = q.order_by(models.PMCSchedule.id.desc()).all()
    result = []
    for s in items:
        line = db.query(models.PMCProductionLine).filter(models.PMCProductionLine.id == s.line_id).first() if s.line_id else None
        item_count = db.query(models.PMCScheduleItem).filter(models.PMCScheduleItem.schedule_id == s.id).count()
        result.append({
            "id": s.id, "schedule_no": s.schedule_no, "product_name": s.product_name,
            "demand_qty": float(s.demand_qty or 0), "completed_qty": float(s.completed_qty or 0),
            "plan_start_date": str(s.plan_start_date) if s.plan_start_date else None,
            "plan_end_date": str(s.plan_end_date) if s.plan_end_date else None,
            "line_id": s.line_id, "line_name": line.line_name if line else None,
            "priority": s.priority, "is_insert": s.is_insert, "status": s.status,
            "material_ready_status": s.material_ready_status, "item_count": item_count,
            "remark": s.remark,
        })
    return result


@router.post("/pmc/schedules")
def pmc_create_schedule(payload: dict, db: Session = Depends(get_db)):
    demand = float(payload.get("demand_qty") or 0)
    if demand <= 0: raise HTTPException(400, "需求数量必须大于0")
    sd = _pmc_to_date(payload.get("plan_start_date"))
    ed = _pmc_to_date(payload.get("plan_end_date"))
    if not sd or not ed: raise HTTPException(400, "计划日期不能为空")
    s = models.PMCSchedule(
        account_set_id=1, schedule_no=_pmc_schedule_no(),
        sales_order_id=payload.get("sales_order_id"),
        work_order_id=payload.get("work_order_id"),
        product_id=payload.get("product_id"),
        product_name=(payload.get("product_name") or "").strip() or None,
        bom_id=payload.get("bom_id"),
        demand_qty=demand, completed_qty=0,
        plan_start_date=sd, plan_end_date=ed,
        line_id=payload.get("line_id"),
        priority=(payload.get("priority") or "NORMAL").strip(),
        is_insert=int(payload.get("is_insert") or 0),
        status="PLANNED",
        remark=(payload.get("remark") or "").strip() or None,
    )
    db.add(s); db.commit(); db.refresh(s)
    # 自动生成排产明细
    _pmc_generate_schedule_items(db, s)
    # 联动物料需求
    _pmc_calc_material_demand(db, s)
    return {"success": True, "id": s.id, "schedule_no": s.schedule_no}


def _pmc_generate_schedule_items(db, schedule):
    """根据生产线产能和日期范围自动生成每日排产明细"""
    line = db.query(models.PMCProductionLine).filter(models.PMCProductionLine.id == schedule.line_id).first() if schedule.line_id else None
    daily_cap = float(line.daily_capacity or 0) if line else float(schedule.demand_qty or 0)
    if daily_cap <= 0: daily_cap = float(schedule.demand_qty or 0)
    # 按工序拆分（如果有process_codes）
    processes = []
    if line and line.process_codes:
        processes = [p.strip() for p in line.process_codes.split(",") if p.strip()]
    if not processes:
        processes = ["组装"]
    # 生成每日排产
    remaining = float(schedule.demand_qty or 0)
    cur_date = schedule.plan_start_date
    end_date = schedule.plan_end_date
    day_idx = 0
    while remaining > 0 and cur_date <= end_date:
        qty = min(daily_cap, remaining)
        # 每个工序生成一行
        for proc in processes:
            item = models.PMCScheduleItem(
                account_set_id=1, schedule_id=schedule.id, line_id=schedule.line_id,
                schedule_date=cur_date, process_code=proc, process_name=proc,
                planned_qty=qty if proc == processes[-1] else 0,  # 末道工序排数量
                completed_qty=0, base_hours=8, overtime_hours=0, status="PLANNED",
            )
            # 非末道工序：按产能比例分摊
            if proc != processes[-1]:
                item.planned_qty = qty
            db.add(item)
        remaining -= qty
        cur_date += datetime.timedelta(days=1)
        day_idx += 1
    db.commit()


def _pmc_calc_material_demand(db, schedule):
    """排产联动MRP：根据BOM和排产日期计算物料需求"""
    if not schedule.bom_id:
        schedule.material_ready_status = "UNKNOWN"
        db.commit()
        return
    flat = _flatten_bom_items(db, schedule.bom_id)
    if not flat:
        schedule.material_ready_status = "UNKNOWN"
        db.commit()
        return
    stock = _get_stock_map(db)
    intransit = _get_intransit_map(db)
    # 清除旧需求
    db.query(models.PMCMaterialDemand).filter(models.PMCMaterialDemand.schedule_id == schedule.id).delete()
    ready_count = 0
    total_count = 0
    for it in flat:
        total_demand = it["total_qty"] * float(schedule.demand_qty or 0)
        code = it["material_code"]
        stk = stock.get(code, 0) if code else 0
        transit = intransit.get(code, 0) if code else 0
        deficit = total_demand - stk - transit
        total_count += 1
        # 采购提前期（默认7天，可从物料主数据取）
        lead_days = 7
        mat = db.query(models.Material).filter(models.Material.code == code).first() if code else None
        if mat and mat.lead_time: lead_days = mat.lead_time
        req_date = schedule.plan_start_date - datetime.timedelta(days=lead_days)
        ready_status = "READY" if deficit <= 0 else ("PARTIAL" if stk > 0 else "SHORTAGE")
        if ready_status == "READY": ready_count += 1
        demand = models.PMCMaterialDemand(
            account_set_id=1, schedule_id=schedule.id,
            material_id=mat.id if mat else None,
            material_code=code, material_name=it["material_name"], spec=it["spec"],
            unit_qty=it["unit_qty"], total_demand=total_demand,
            stock_qty=stk, intransit_qty=transit, deficit_qty=max(deficit, 0),
            lead_time_days=lead_days, schedule_date=schedule.plan_start_date,
            required_date=req_date, ready_status=ready_status,
        )
        db.add(demand)
    # 更新齐套状态
    if total_count == 0:
        schedule.material_ready_status = "UNKNOWN"
    elif ready_count == total_count:
        schedule.material_ready_status = "READY"
    elif ready_count == 0:
        schedule.material_ready_status = "SHORTAGE"
    else:
        schedule.material_ready_status = "PARTIAL"
    db.commit()


@router.get("/pmc/schedules/{schedule_id}")
def pmc_get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    s = db.query(models.PMCSchedule).filter(models.PMCSchedule.id == schedule_id).first()
    if not s: raise HTTPException(404, "排产单不存在")
    items = db.query(models.PMCScheduleItem).filter(models.PMCScheduleItem.schedule_id == schedule_id).order_by(models.PMCScheduleItem.schedule_date).all()
    demands = db.query(models.PMCMaterialDemand).filter(models.PMCMaterialDemand.schedule_id == schedule_id).all()
    return {
        "schedule": {
            "id": s.id, "schedule_no": s.schedule_no, "product_name": s.product_name,
            "demand_qty": float(s.demand_qty or 0), "completed_qty": float(s.completed_qty or 0),
            "plan_start_date": str(s.plan_start_date) if s.plan_start_date else None,
            "plan_end_date": str(s.plan_end_date) if s.plan_end_date else None,
            "line_id": s.line_id, "priority": s.priority, "is_insert": s.is_insert,
            "status": s.status, "material_ready_status": s.material_ready_status,
        },
        "items": [{
            "id": i.id, "schedule_date": str(i.schedule_date) if i.schedule_date else None,
            "process_code": i.process_code, "process_name": i.process_name,
            "planned_qty": float(i.planned_qty or 0), "completed_qty": float(i.completed_qty or 0),
            "base_hours": float(i.base_hours or 8), "overtime_hours": float(i.overtime_hours or 0),
            "status": i.status, "remark": i.remark,
        } for i in items],
        "demands": [{
            "id": d.id, "material_code": d.material_code, "material_name": d.material_name,
            "spec": d.spec, "unit_qty": float(d.unit_qty or 0), "total_demand": float(d.total_demand or 0),
            "stock_qty": float(d.stock_qty or 0), "intransit_qty": float(d.intransit_qty or 0),
            "deficit_qty": float(d.deficit_qty or 0), "lead_time_days": d.lead_time_days,
            "schedule_date": str(d.schedule_date) if d.schedule_date else None,
            "required_date": str(d.required_date) if d.required_date else None,
            "ready_status": d.ready_status, "purchase_status": d.purchase_status,
        } for d in demands],
    }


@router.put("/pmc/schedule-items/{item_id}/overtime")
def pmc_adjust_overtime(item_id: int, payload: dict, db: Session = Depends(get_db)):
    """调节排产明细加班工时"""
    item = db.query(models.PMCScheduleItem).filter(models.PMCScheduleItem.id == item_id).first()
    if not item: raise HTTPException(404, "排产明细不存在")
    if "overtime_hours" in payload:
        item.overtime_hours = float(payload.get("overtime_hours") or 0)
    if "planned_qty" in payload:
        item.planned_qty = float(payload.get("planned_qty") or 0)
    if "status" in payload:
        item.status = payload["status"]
    if "remark" in payload:
        item.remark = payload["remark"]
    db.commit()
    return {"success": True}


@router.put("/pmc/schedules/{schedule_id}/status")
def pmc_update_schedule_status(schedule_id: int, payload: dict, db: Session = Depends(get_db)):
    """排产单状态流转 + 插单标记"""
    s = db.query(models.PMCSchedule).filter(models.PMCSchedule.id == schedule_id).first()
    if not s: raise HTTPException(404, "排产单不存在")
    if "status" in payload: s.status = payload["status"]
    if "is_insert" in payload: s.is_insert = int(payload["is_insert"])
    if "priority" in payload: s.priority = payload["priority"]
    db.commit()
    return {"success": True}


@router.post("/pmc/schedules/{schedule_id}/recalc-material")
def pmc_recalc_material(schedule_id: int, db: Session = Depends(get_db)):
    """重新计算排产单物料需求"""
    s = db.query(models.PMCSchedule).filter(models.PMCSchedule.id == schedule_id).first()
    if not s: raise HTTPException(404, "排产单不存在")
    _pmc_calc_material_demand(db, s)
    return {"success": True, "material_ready_status": s.material_ready_status}


@router.get("/pmc/material-demands")
def pmc_list_material_demands(ready_status: Optional[str] = None, db: Session = Depends(get_db)):
    """PMC物料需求列表：按排产日期展示物料到位计划+缺料预警"""
    q = db.query(models.PMCMaterialDemand)
    if ready_status: q = q.filter(models.PMCMaterialDemand.ready_status == ready_status)
    items = q.order_by(models.PMCMaterialDemand.required_date).all()
    return [{
        "id": d.id, "schedule_id": d.schedule_id,
        "material_code": d.material_code, "material_name": d.material_name, "spec": d.spec,
        "total_demand": float(d.total_demand or 0), "stock_qty": float(d.stock_qty or 0),
        "intransit_qty": float(d.intransit_qty or 0), "deficit_qty": float(d.deficit_qty or 0),
        "lead_time_days": d.lead_time_days,
        "schedule_date": str(d.schedule_date) if d.schedule_date else None,
        "required_date": str(d.required_date) if d.required_date else None,
        "ready_status": d.ready_status, "purchase_status": d.purchase_status,
    } for d in items]


@router.get("/pmc/dashboard")
def pmc_dashboard(db: Session = Depends(get_db)):
    """PMC看板：排产进度+齐套率+缺料预警+产能负荷概览"""
    schedules = db.query(models.PMCSchedule).filter(models.PMCSchedule.status != "CANCELLED").all()
    demands = db.query(models.PMCMaterialDemand).all()
    today = datetime.date.today()
    # 排产统计
    total = len(schedules)
    running = sum(1 for s in schedules if s.status == "RUNNING")
    planned = sum(1 for s in schedules if s.status == "PLANNED")
    completed = sum(1 for s in schedules if s.status == "COMPLETED")
    # 齐套统计
    ready = sum(1 for d in demands if d.ready_status == "READY")
    shortage = sum(1 for d in demands if d.ready_status == "SHORTAGE")
    partial = sum(1 for d in demands if d.ready_status == "PARTIAL")
    # 缺料预警（required_date已过但仍缺料）
    overdue_shortage = sum(1 for d in demands if d.ready_status == "SHORTAGE" and d.required_date and d.required_date < today)
    # 今日排产
    today_schedules = [s for s in schedules if s.plan_start_date <= today <= s.plan_end_date]
    # 产能负荷（未来30天）
    cap = pmc_capacity_analysis(start=str(today), end=str(today + datetime.timedelta(days=30)), db=db)
    return {
        "schedule_stats": {"total": total, "planned": planned, "running": running, "completed": completed},
        "material_stats": {"ready": ready, "partial": partial, "shortage": shortage, "overdue_shortage": overdue_shortage},
        "today_schedule_count": len(today_schedules),
        "capacity_bottlenecks": [l for l in cap["lines"] if l["bottleneck"]],
        "shortage_list": [{
            "material_code": d.material_code, "material_name": d.material_name,
            "deficit_qty": float(d.deficit_qty or 0),
            "required_date": str(d.required_date) if d.required_date else None,
        } for d in sorted(demands, key=lambda x: (x.ready_status != "SHORTAGE", x.required_date or datetime.date.max))[:10]],
    }
