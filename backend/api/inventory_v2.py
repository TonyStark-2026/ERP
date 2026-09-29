"""
库存管理 V2 模块
===================
仓库主数据管理、呆滞库存预警
（入库/出库/批次/库位由现有 inventory.py 处理，本模块补充仓库档案与呆滞分析）
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


# ============================================================
# 1. 仓库主数据管理
# ============================================================
@router.get("/warehouses", tags=["库存管理V2"])
def list_warehouses(keyword: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.Warehouse).filter(models.Warehouse.account_set_id == ACCOUNT_SET_ID)
    if keyword:
        q = q.filter(models.Warehouse.code.contains(keyword) | models.Warehouse.name.contains(keyword))
    items = q.order_by(models.Warehouse.code).all()
    result = []
    for w in items:
        result.append({
            "id": w.id, "code": w.code, "name": w.name,
            "address": w.address or "", "manager": w.manager or "",
            "phone": w.phone or "", "is_active": w.is_active,
            "created_at": _fmt_date(w.created_at),
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/warehouses", tags=["库存管理V2"])
def create_warehouse(data: dict = Body(...), db: Session = Depends(get_db)):
    code = (data.get("code") or "").strip()
    name = (data.get("name") or "").strip()
    if not code or not name:
        return make_response(False, None, "仓库编码和名称必填", "40001")
    exists = db.query(models.Warehouse).filter(
        models.Warehouse.account_set_id == ACCOUNT_SET_ID,
        models.Warehouse.code == code,
    ).first()
    if exists:
        return make_response(False, None, "仓库编码已存在", "40002")
    w = models.Warehouse(
        account_set_id=ACCOUNT_SET_ID, code=code, name=name,
        address=data.get("address"), manager=data.get("manager"),
        phone=data.get("phone"), is_active=data.get("is_active", True),
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return make_response(True, {"id": w.id, "code": w.code}, "仓库创建成功")


@router.put("/warehouses/{wid}", tags=["库存管理V2"])
def update_warehouse(wid: int, data: dict = Body(...), db: Session = Depends(get_db)):
    w = db.query(models.Warehouse).filter(models.Warehouse.id == wid).first()
    if not w:
        return make_response(False, None, "仓库不存在", "40401")
    for f in ["name", "address", "manager", "phone"]:
        if f in data:
            setattr(w, f, data[f])
    if "is_active" in data:
        w.is_active = data["is_active"]
    db.commit()
    return make_response(True, {"id": w.id}, "仓库更新成功")


@router.delete("/warehouses/{wid}", tags=["库存管理V2"])
def delete_warehouse(wid: int, db: Session = Depends(get_db)):
    w = db.query(models.Warehouse).filter(models.Warehouse.id == wid).first()
    if not w:
        return make_response(False, None, "仓库不存在", "40401")
    db.delete(w)
    db.commit()
    return make_response(True, None, "仓库已删除")


# ============================================================
# 2. 呆滞库存预警
# ============================================================
@router.get("/slow-moving", tags=["库存管理V2"])
def list_slow_moving(days_threshold: int = 90, status: Optional[str] = None, db: Session = Depends(get_db)):
    """呆滞库存清单（默认90天无动销）"""
    q = db.query(models.SlowMovingInventory).filter(
        models.SlowMovingInventory.account_set_id == ACCOUNT_SET_ID
    )
    if status:
        q = q.filter(models.SlowMovingInventory.status == status)
    else:
        q = q.filter(models.SlowMovingInventory.days_idle >= days_threshold)
    items = q.order_by(models.SlowMovingInventory.days_idle.desc()).all()
    result = []
    total_value = 0.0
    for s in items:
        m = s.material
        val = float(s.value or 0)
        total_value += val
        result.append({
            "id": s.id, "material_id": s.material_id,
            "material": _material_to_dict(m),
            "last_move_date": _fmt_date(s.last_move_date),
            "days_idle": s.days_idle,
            "quantity": float(s.quantity or 0),
            "value": val,
            "status": s.status,
            "status_label": {"PENDING": "待处理", "PROCESSING": "处理中",
                             "RESOLVED": "已处理"}.get(s.status, s.status),
            "created_at": _fmt_date(s.created_at),
        })
    return make_response(True, {
        "items": result, "total": len(result),
        "total_value": round(total_value, 2),
        "days_threshold": days_threshold,
    })


@router.post("/slow-moving/scan", tags=["库存管理V2"])
def scan_slow_moving(days_threshold: int = 90, db: Session = Depends(get_db)):
    """扫描生成呆滞库存清单：检查所有物料的最后出入库记录"""
    today = datetime.date.today()
    threshold_date = today - datetime.timedelta(days=days_threshold)

    # 查询库存流水（InventoryTransaction）获取各物料最后动销日期
    materials = db.query(models.Material).all()
    created = 0
    updated = 0
    for m in materials:
        # 查找最近一笔库存流水
        last_txn = db.query(models.InventoryTransaction).filter(
            models.InventoryTransaction.material_id == m.id
        ).order_by(models.InventoryTransaction.created_at.desc()).first()

        if last_txn and last_txn.created_at:
            last_move = last_txn.created_at.date() if isinstance(last_txn.created_at, datetime.datetime) else last_txn.created_at
        else:
            last_move = None

        days_idle = (today - last_move).days if last_move else 9999

        if days_idle >= days_threshold:
            # 查当前库存
            stock = db.query(models.InventoryRecord).filter(models.InventoryRecord.material_id == m.id).first()
            qty = float(stock.quantity or 0) if stock else 0
            if qty <= 0:
                continue
            unit_cost = float(m.standard_cost or m.purchase_price or 0) if hasattr(m, "standard_cost") else 0
            value = qty * unit_cost

            existing = db.query(models.SlowMovingInventory).filter(
                models.SlowMovingInventory.material_id == m.id,
                models.SlowMovingInventory.status != "RESOLVED",
            ).first()
            if existing:
                existing.last_move_date = last_move
                existing.days_idle = days_idle
                existing.quantity = qty
                existing.value = value
                updated += 1
            else:
                db.add(models.SlowMovingInventory(
                    account_set_id=ACCOUNT_SET_ID, material_id=m.id,
                    last_move_date=last_move, days_idle=days_idle,
                    quantity=qty, value=value, status="PENDING",
                ))
                created += 1
    db.commit()
    return make_response(True, {"created": created, "updated": updated},
                         f"扫描完成：新增{created}条，更新{updated}条呆滞记录")


@router.put("/slow-moving/{sid}/status", tags=["库存管理V2"])
def update_slow_moving_status(sid: int, data: dict = Body(...), db: Session = Depends(get_db)):
    s = db.query(models.SlowMovingInventory).filter(models.SlowMovingInventory.id == sid).first()
    if not s:
        return make_response(False, None, "呆滞记录不存在", "40401")
    s.status = data.get("status", s.status)
    db.commit()
    return make_response(True, {"id": s.id}, "状态已更新")


@router.get("/overview", tags=["库存管理V2"])
def overview(db: Session = Depends(get_db)):
    wh_count = db.query(models.Warehouse).filter(models.Warehouse.account_set_id == ACCOUNT_SET_ID).count()
    sm_count = db.query(models.SlowMovingInventory).filter(
        models.SlowMovingInventory.account_set_id == ACCOUNT_SET_ID,
        models.SlowMovingInventory.status != "RESOLVED",
    ).count()
    sm_value = db.query(models.SlowMovingInventory).filter(
        models.SlowMovingInventory.account_set_id == ACCOUNT_SET_ID,
        models.SlowMovingInventory.status != "RESOLVED",
    ).all()
    total_value = sum(float(s.value or 0) for s in sm_value)
    return make_response(True, {
        "warehouse_count": wh_count,
        "slow_moving_count": sm_count,
        "slow_moving_value": round(total_value, 2),
    }, "库存管理V2概览")
