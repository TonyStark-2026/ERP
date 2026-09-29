"""
工程导向型适配API
=================
采购/销售/库存模块的工程导向型扩展功能：
  1. 供应商评级（质量×0.6 + 交期×0.4）
  2. 采购成本按项目统计
  3. 合同台账（应收/已收/未收）
  4. 库存批次管理与追溯
  5. 库存预警（安全库存/最低库存）
  6. BOM成本+毛利报价测算
"""
import json
import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from .. import models

router = APIRouter()


# ==================== 1. 供应商评级 ====================

@router.post("/suppliers/{supplier_id}/calculate-rating")
def calculate_supplier_rating(supplier_id: int, db: Session = Depends(get_db)):
    """计算供应商综合评级：质量评分×0.6 + 交期评分×0.4"""
    supplier = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(404, "供应商不存在")
    quality = float(supplier.quality_rate or 0)
    on_time = float(supplier.on_time_rate or 0)
    rating = round(quality * 0.6 + on_time * 0.4, 2)
    supplier.rating_score = rating
    db.commit()
    return {
        "id": supplier.id,
        "name": supplier.name,
        "quality_rate": quality,
        "on_time_rate": on_time,
        "rating_score": rating,
        "rating_level": _rating_level(rating),
    }


def _rating_level(score: float) -> str:
    if score >= 90: return "A"
    if score >= 75: return "B"
    if score >= 60: return "C"
    return "D"


@router.get("/suppliers/ranking")
def supplier_ranking(db: Session = Depends(get_db)):
    """供应商评级排行榜"""
    suppliers = db.query(models.Supplier).order_by(
        models.Supplier.rating_score.is_(None),  # NULL排最后（SQLite兼容）
        models.Supplier.rating_score.desc()
    ).all()
    return {
        "total": len(suppliers),
        "items": [{
            "id": s.id,
            "name": s.name,
            "quality_rate": float(s.quality_rate or 0),
            "on_time_rate": float(s.on_time_rate or 0),
            "rating_score": float(s.rating_score or 0),
            "rating_level": _rating_level(float(s.rating_score or 0)),
        } for s in suppliers]
    }


# ==================== 2. 采购成本按项目统计 ====================

@router.get("/purchase/project-cost-stats")
def purchase_project_cost_stats(project_id: Optional[int] = None, db: Session = Depends(get_db)):
    """按项目统计采购成本"""
    q = db.query(
        models.PurchaseOrder.project_id,
        func.count(models.PurchaseOrder.id).label("order_count"),
        func.sum(models.PurchaseOrder.total_amount).label("total_cost"),
    ).filter(models.PurchaseOrder.project_id.isnot(None))
    if project_id:
        q = q.filter(models.PurchaseOrder.project_id == project_id)
    results = q.group_by(models.PurchaseOrder.project_id).all()
    items = []
    for r in results:
        proj = db.query(models.WBSProject).filter(models.WBSProject.id == r[0]).first()
        items.append({
            "project_id": r[0],
            "project_no": proj.project_no if proj else "",
            "project_name": proj.project_name if proj else "",
            "order_count": r[1],
            "total_purchase_cost": float(r[2] or 0),
            "budget_cost": float(proj.budget_cost or 0) if proj else 0,
            "cost_ratio": round(float(r[2] or 0) / float(proj.budget_cost) * 100, 2) if proj and proj.budget_cost else 0,
        })
    return {"total": len(items), "items": items}


@router.get("/purchase/by-project/{project_id}")
def purchase_orders_by_project(project_id: int, db: Session = Depends(get_db)):
    """查询某项目的所有采购订单"""
    orders = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.project_id == project_id
    ).order_by(models.PurchaseOrder.created_at.desc()).all()
    return {
        "total": len(orders),
        "total_amount": float(sum(o.total_amount or 0 for o in orders)),
        "items": [{
            "id": o.id, "po_no": o.po_no, "supplier_id": o.supplier_id,
            "status": o.status, "total_amount": float(o.total_amount or 0),
            "order_date": str(o.order_date) if o.order_date else None,
            "bom_line_ref": o.bom_line_ref,
            "created_at": str(o.created_at) if o.created_at else None,
        } for o in orders]
    }


# ==================== 3. 合同台账 ====================

@router.get("/contracts/ledger")
def contract_ledger(project_id: Optional[int] = None, customer_id: Optional[int] = None, db: Session = Depends(get_db)):
    """合同台账：按合同统计应收、已收、未收金额"""
    q = db.query(models.Contract)
    if project_id:
        q = q.filter(models.Contract.project_id == project_id)
    if customer_id:
        q = q.filter(models.Contract.customer_id == customer_id)
    contracts = q.order_by(models.Contract.created_at.desc()).all()
    items = []
    total_receivable = 0
    total_received = 0
    for c in contracts:
        amount = float(c.contract_amount or c.amount or 0)
        # 从收款单统计已收金额
        received = 0
        try:
            receipts = db.query(models.Receipt).filter(models.Receipt.customer_id == c.customer_id).all()
            received = float(sum(r.amount or 0 for r in receipts))
        except Exception:
            pass
        unreceived = amount - received
        total_receivable += amount
        total_received += received
        # 解析里程碑
        milestones = []
        if c.milestone_payments:
            try:
                milestones = json.loads(c.milestone_payments)
            except Exception:
                pass
        items.append({
            "id": c.id,
            "contract_no": c.contract_no,
            "contract_type": str(c.contract_type),
            "project_id": c.project_id,
            "customer_id": c.customer_id,
            "contract_amount": amount,
            "received_amount": received,
            "unreceived_amount": unreceived,
            "receivable_status": "已结清" if unreceived <= 0 else ("部分收款" if received > 0 else "未收款"),
            "milestone_count": len(milestones),
            "status": str(c.status),
            "start_date": str(c.start_date) if c.start_date else None,
            "end_date": str(c.end_date) if c.end_date else None,
        })
    return {
        "total": len(items),
        "total_receivable": total_receivable,
        "total_received": total_received,
        "total_unreceived": total_receivable - total_received,
        "items": items,
    }


@router.put("/contracts/{contract_id}/milestones")
def update_contract_milestones(contract_id: int, body: Dict[str, Any], db: Session = Depends(get_db)):
    """更新合同里程碑付款计划"""
    contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(404, "合同不存在")
    milestones = body.get("milestone_payments", [])
    contract.milestone_payments = json.dumps(milestones, ensure_ascii=False)
    if body.get("project_id"):
        contract.project_id = body["project_id"]
    if body.get("contract_amount"):
        contract.contract_amount = body["contract_amount"]
    db.commit()
    return {"id": contract.id, "milestone_count": len(milestones)}


# ==================== 4. 库存批次管理 ====================

@router.get("/inventory/batches")
def list_batches(material_id: Optional[int] = None, project_id: Optional[int] = None,
                 warehouse_id: Optional[int] = None, status: Optional[str] = None,
                 db: Session = Depends(get_db)):
    """批次列表（支持按物料/项目/仓库/状态筛选）"""
    q = db.query(models.InventoryBatch)
    if material_id:
        q = q.filter(models.InventoryBatch.material_id == material_id)
    if project_id:
        q = q.filter(models.InventoryBatch.project_id == project_id)
    if warehouse_id:
        q = q.filter(models.InventoryBatch.warehouse_id == warehouse_id)
    if status:
        q = q.filter(models.InventoryBatch.status == status)
    batches = q.order_by(models.InventoryBatch.created_at.desc()).all()
    return {
        "total": len(batches),
        "items": [{
            "id": b.id, "batch_no": b.batch_no, "material_id": b.material_id,
            "warehouse_id": b.warehouse_id, "quantity": float(b.quantity or 0),
            "unit_cost": float(b.unit_cost or 0), "total_cost": float(b.total_cost or 0),
            "production_date": str(b.production_date) if b.production_date else None,
            "expiry_date": str(b.expiry_date) if b.expiry_date else None,
            "inbound_date": str(b.inbound_date) if b.inbound_date else None,
            "supplier_id": b.supplier_id, "project_id": b.project_id,
            "source_doc_no": b.source_doc_no, "status": b.status,
        } for b in batches]
    }


@router.post("/inventory/batches")
def create_batch(body: Dict[str, Any], db: Session = Depends(get_db)):
    """创建入库批次"""
    batch_no = body.get("batch_no")
    if not batch_no:
        # 自动生成批次号
        batch_no = f"BATCH-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    batch = models.InventoryBatch(
        account_set_id=body.get("account_set_id", 1),
        material_id=body["material_id"],
        warehouse_id=body.get("warehouse_id"),
        batch_no=batch_no,
        quantity=body.get("quantity", 0),
        unit_cost=body.get("unit_cost", 0),
        total_cost=float(body.get("quantity", 0)) * float(body.get("unit_cost", 0)),
        production_date=datetime.date.fromisoformat(body["production_date"]) if body.get("production_date") else None,
        expiry_date=datetime.date.fromisoformat(body["expiry_date"]) if body.get("expiry_date") else None,
        inbound_date=datetime.date.fromisoformat(body["inbound_date"]) if body.get("inbound_date") else datetime.date.today(),
        supplier_id=body.get("supplier_id"),
        project_id=body.get("project_id"),
        source_doc_no=body.get("source_doc_no"),
        status=body.get("status", "NORMAL"),
        remark=body.get("remark"),
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return {"id": batch.id, "batch_no": batch.batch_no}


@router.get("/inventory/batches/trace/{batch_no}")
def trace_batch(batch_no: str, db: Session = Depends(get_db)):
    """批次追溯：根据批次号查询完整信息"""
    batch = db.query(models.InventoryBatch).filter(models.InventoryBatch.batch_no == batch_no).first()
    if not batch:
        raise HTTPException(404, f"批次 {batch_no} 不存在")
    material = db.query(models.Material).filter(models.Material.id == batch.material_id).first()
    warehouse = db.query(models.Warehouse).filter(models.Warehouse.id == batch.warehouse_id).first() if batch.warehouse_id else None
    supplier = db.query(models.Supplier).filter(models.Supplier.id == batch.supplier_id).first() if batch.supplier_id else None
    project = db.query(models.WBSProject).filter(models.WBSProject.id == batch.project_id).first() if batch.project_id else None
    return {
        "batch": {
            "id": batch.id, "batch_no": batch.batch_no,
            "material": {"id": material.id, "code": material.code, "name": material.name} if material else None,
            "warehouse": {"id": warehouse.id, "name": warehouse.name} if warehouse else None,
            "supplier": {"id": supplier.id, "name": supplier.name} if supplier else None,
            "project": {"id": project.id, "project_no": project.project_no, "project_name": project.project_name} if project else None,
            "quantity": float(batch.quantity or 0), "unit_cost": float(batch.unit_cost or 0),
            "production_date": str(batch.production_date) if batch.production_date else None,
            "expiry_date": str(batch.expiry_date) if batch.expiry_date else None,
            "inbound_date": str(batch.inbound_date) if batch.inbound_date else None,
            "source_doc_no": batch.source_doc_no, "status": batch.status,
        }
    }


# ==================== 5. 库存预警 ====================

@router.get("/inventory/warnings")
def inventory_warnings(db: Session = Depends(get_db)):
    """库存预警：低于安全库存或最低库存的物料"""
    materials = db.query(models.Material).all()
    warnings = []
    for m in materials:
        # 查询当前库存（汇总InventoryRecord）
        try:
            inv_total = db.query(func.sum(models.InventoryRecord.quantity)).filter(
                models.InventoryRecord.material_id == m.id
            ).scalar()
            current_qty = float(inv_total or 0)
        except Exception:
            current_qty = 0
        safety = float(m.safety_stock or 0)
        min_stock = float(m.min_stock or 0)
        if safety > 0 and current_qty <= safety:
            warnings.append({
                "material_id": m.id, "material_code": m.code, "material_name": m.name,
                "current_qty": current_qty, "safety_stock": safety, "min_stock": min_stock,
                "warning_type": "安全库存预警",
                "severity": "严重" if current_qty <= min_stock else "警告",
                "shortage": safety - current_qty,
            })
        elif min_stock > 0 and current_qty <= min_stock:
            warnings.append({
                "material_id": m.id, "material_code": m.code, "material_name": m.name,
                "current_qty": current_qty, "safety_stock": safety, "min_stock": min_stock,
                "warning_type": "最低库存预警",
                "severity": "严重",
                "shortage": min_stock - current_qty,
            })
    return {"total": len(warnings), "items": warnings}


# ==================== 6. BOM成本+毛利报价测算 ====================

@router.post("/sales/quote-from-bom")
def quote_from_bom(body: Dict[str, Any], db: Session = Depends(get_db)):
    """根据BOM成本+毛利测算报价
    body: { bom_id, profit_margin(默认0.2即20%), additional_costs(其他附加成本) }
    """
    bom_id = body.get("bom_id")
    if not bom_id:
        raise HTTPException(400, "缺少 bom_id")
    bom = db.query(models.BOM).filter(models.BOM.id == bom_id).first()
    if not bom:
        raise HTTPException(404, "BOM不存在")
    # 获取BOM明细
    items = db.query(models.BOMItem).filter(models.BOMItem.bom_id == bom_id).all() if hasattr(models, 'BOMItem') else []
    material_cost = 0
    item_details = []
    for item in items:
        mat = db.query(models.Material).filter(models.Material.id == item.material_id).first() if item.material_id else None
        unit_price = float(mat.unit_price or 0) if mat else 0
        qty = float(item.quantity or 0)
        cost = unit_price * qty
        material_cost += cost
        item_details.append({
            "material_id": item.material_id,
            "material_name": mat.name if mat else "",
            "quantity": qty, "unit_price": unit_price, "cost": cost,
        })
    additional_costs = float(body.get("additional_costs", 0))
    total_cost = material_cost + additional_costs
    profit_margin = float(body.get("profit_margin", 0.2))
    # 报价 = 成本 / (1 - 毛利率)
    quote_price = round(total_cost / (1 - profit_margin), 2) if profit_margin < 1 else total_cost
    profit = quote_price - total_cost
    return {
        "bom_id": bom_id,
        "material_cost": round(material_cost, 2),
        "additional_costs": additional_costs,
        "total_cost": round(total_cost, 2),
        "profit_margin": profit_margin,
        "quote_price": quote_price,
        "profit": round(profit, 2),
        "profit_amount_at_margin": round(total_cost * profit_margin / (1 - profit_margin), 2),
        "item_details": item_details,
    }
