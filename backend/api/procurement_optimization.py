"""
采购-库存平衡优化模型 API
=========================
1. EOQ平衡优化引擎 (7公式联动)
2. 供应商管理增强 (交期/MOQ/阶梯报价/评级)
3. 到料跟踪看板
4. 建档发料4种领料模式
5. ROI看板
6. 物料底层治理 (双编码规则/去重)
7. 流程卡点校验
"""
import math
import json
import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ..database import get_db
from .. import models

router = APIRouter()

def _to_date(v):
    if not v: return None
    if isinstance(v, datetime.date): return v
    try: return datetime.date.fromisoformat(str(v)[:10])
    except: return None


# ============================================================
# 1. EOQ 平衡优化引擎 —— 7公式联动
# ============================================================

@router.post("/eoq/calculate")
def eoq_calculate(data: dict, db: Session = Depends(get_db)):
    """
    EOQ平衡优化计算
    输入: annual_demand(D), order_cost(S), unit_cost(C), holding_rate(i),
          lead_time_days(L), warehouse_fee(H), sell_price, service_level
    输出: EOQ, 修正持有成本H', 总成本TC, 资金占用, 周转率, 利润率, ROI
    """
    D = float(data.get('annual_demand', 0))       # 年需求量
    S = float(data.get('order_cost', 200))         # 单次订货成本
    C = float(data.get('unit_cost', 0))            # 采购单价
    i = float(data.get('holding_rate', 0.08))      # 资金成本率(年化)
    L = float(data.get('lead_time_days', 7))       # 供应商交货周期(天)
    H = float(data.get('warehouse_fee', 5))        # 仓储费(元/件·年)
    sell_price = float(data.get('sell_price', 0))  # 销售单价
    service_level = float(data.get('service_level', 0.95))  # 服务水平
    sigma_d = float(data.get('demand_stddev', 0))  # 日需求标准差
    wmax = float(data.get('warehouse_capacity', 999999))  # 仓库最大容量

    # 公式②: 修正持有成本 H' = H + C×i + C×i×(L/365)
    H_prime = H + C * i + C * i * (L / 365)

    # 公式①: EOQ = √(2DS/H')
    if D > 0 and H_prime > 0:
        eoq = math.sqrt(2 * D * S / H_prime)
    else:
        eoq = 0

    # MOQ约束
    moq = float(data.get('moq', 0))
    if moq > 0 and eoq < moq:
        eoq = moq
        moq_adjusted = True
    else:
        moq_adjusted = False

    # 公式⑥: 仓库容量约束 Q* + SS ≤ Wmax
    # 公式⑤: 安全库存 SS = Z × σd × √L
    z_map = {0.90: 1.28, 0.95: 1.65, 0.99: 2.33}
    Z = z_map.get(service_level, 1.65)
    if sigma_d > 0 and L > 0:
        ss = Z * sigma_d * math.sqrt(L)
    else:
        ss = 0

    if eoq + ss > wmax:
        eoq = max(moq, wmax - ss)
        capacity_adjusted = True
    else:
        capacity_adjusted = False

    # 公式⑦: 总成本 TC = D×C + (D/Q)×S + (Q/2)×H'
    if eoq > 0:
        tc = D * C + (D / eoq) * S + (eoq / 2) * H_prime
        num_orders = D / eoq
    else:
        tc = 0
        num_orders = 0

    # 公式③: 资金占用 = (Q/2) × C × i × (L/365)
    capital_occupation = (eoq / 2) * C * i * (L / 365) if eoq > 0 else 0

    # 周转率 = D×C / (Q/2 × C) = 2D/Q
    turnover = (2 * D / eoq) if eoq > 0 else 0

    # 利润率 = (收入 - TC) / 收入
    revenue = D * sell_price
    profit_rate = ((revenue - tc) / revenue) if revenue > 0 else 0

    # ROI = 周转率 × 利润率
    roi = turnover * profit_rate

    # 公式④: 再订货点 ROP = d×L + SS
    d_daily = D / 365
    rop = d_daily * L + ss

    return {
        "success": True,
        "data": {
            "inputs": {
                "annual_demand": D, "order_cost": S, "unit_cost": C,
                "holding_rate": i, "lead_time_days": L, "warehouse_fee": H,
                "sell_price": sell_price, "moq": moq, "service_level": service_level,
                "warehouse_capacity": wmax,
            },
            "results": {
                "H_prime": round(H_prime, 4),           # 修正持有成本
                "eoq": round(eoq, 0),                    # 最优采购批量
                "safety_stock": round(ss, 0),            # 安全库存
                "rop": round(rop, 0),                    # 再订货点
                "total_cost": round(tc, 2),              # 总成本
                "num_orders": round(num_orders, 1),      # 年订货次数
                "capital_occupation": round(capital_occupation, 2),  # 资金占用
                "turnover": round(turnover, 2),          # 库存周转率
                "profit_rate": round(profit_rate * 100, 2),  # 利润率%
                "roi": round(roi, 4),                    # 投资回报率
                "moq_adjusted": moq_adjusted,            # 是否被MOQ调整
                "capacity_adjusted": capacity_adjusted,   # 是否被仓库容量调整
            },
            "formulas": {
                "H_prime": f"H' = {H} + {C}×{i} + {C}×{i}×({L}/365) = {round(H_prime,4)}",
                "eoq": f"Q* = √(2×{D}×{S}/{round(H_prime,4)}) = {round(eoq,0)}",
                "tc": f"TC = {D}×{C} + ({D}/{round(eoq,0)})×{S} + ({round(eoq,0)}/2)×{round(H_prime,4)} = {round(tc,2)}",
                "roi": f"ROI = {round(turnover,2)} × {round(profit_rate*100,2)}% = {round(roi,4)}",
            }
        }
    }


@router.post("/eoq/compare-suppliers")
def eoq_compare_suppliers(data: dict, db: Session = Depends(get_db)):
    """
    多供应商EOQ对比：输入物料信息+多个供应商报价，系统计算每个供应商的ROI，推荐最优
    """
    D = float(data.get('annual_demand', 0))
    S = float(data.get('order_cost', 200))
    H = float(data.get('warehouse_fee', 5))
    i = float(data.get('holding_rate', 0.08))
    sell_price = float(data.get('sell_price', 0))
    service_level = float(data.get('service_level', 0.95))
    sigma_d = float(data.get('demand_stddev', 0))
    wmax = float(data.get('warehouse_capacity', 999999))

    suppliers = data.get('suppliers', [])
    results = []

    for sup in suppliers:
        calc_data = {
            'annual_demand': D, 'order_cost': S, 'unit_cost': sup.get('unit_cost', 0),
            'holding_rate': i, 'lead_time_days': sup.get('lead_time', 7),
            'warehouse_fee': H, 'sell_price': sell_price, 'service_level': service_level,
            'demand_stddev': sigma_d, 'moq': sup.get('moq', 0),
            'warehouse_capacity': wmax,
        }
        calc = eoq_calculate(calc_data, db)
        r = calc['data']['results']
        results.append({
            'supplier_id': sup.get('id'),
            'supplier_name': sup.get('name', '-'),
            'unit_cost': sup.get('unit_cost', 0),
            'lead_time': sup.get('lead_time', 7),
            'moq': sup.get('moq', 0),
            'eoq': r['eoq'],
            'total_cost': r['total_cost'],
            'capital_occupation': r['capital_occupation'],
            'turnover': r['turnover'],
            'profit_rate': r['profit_rate'],
            'roi': r['roi'],
        })

    # 按ROI排序，推荐最优
    results.sort(key=lambda x: x['roi'], reverse=True)
    recommended = results[0] if results else None

    return {
        "success": True,
        "data": {
            "results": results,
            "recommended": recommended,
            "comparison_note": "ROI = 周转率 × 利润率，推荐ROI最高的供应商"
        }
    }


# ============================================================
# 2. 供应商管理增强
# ============================================================

@router.get("/suppliers/enhanced")
def suppliers_enhanced(db: Session = Depends(get_db)):
    """供应商列表（含交期、MOQ、阶梯报价、评级）"""
    suppliers = db.query(models.Supplier).all()
    result = []
    for s in suppliers:
        result.append({
            "id": s.id,
            "code": s.code if hasattr(s, 'code') else f"SUP-{s.id:03d}",
            "name": s.name,
            "contact_person": s.contact_person if hasattr(s, 'contact_person') else "",
            "phone": s.phone if hasattr(s, 'phone') else "",
            "address": s.address if hasattr(s, 'address') else "",
            "lead_time_days": getattr(s, 'lead_time_days', 7),
            "moq": getattr(s, 'moq', 0),
            "payment_terms": getattr(s, 'payment_terms', '30天'),
            "rating": getattr(s, 'rating', 'B'),
            "supply_capacity": getattr(s, 'supply_capacity', 0),
            "pass_rate": getattr(s, 'pass_rate', 95.0),
        })
    return {"success": True, "data": result, "total": len(result)}


@router.put("/suppliers/{supplier_id}/enhanced")
def update_supplier_enhanced(supplier_id: int, data: dict, db: Session = Depends(get_db)):
    """更新供应商增强字段"""
    s = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if not s:
        raise HTTPException(404, "供应商不存在")

    for field in ['lead_time_days', 'moq', 'payment_terms', 'rating', 'supply_capacity', 'pass_rate']:
        if field in data:
            setattr(s, field, data[field])

    db.commit()
    return {"success": True, "message": "供应商信息已更新"}


# ============================================================
# 3. 到料跟踪看板
# ============================================================

@router.get("/arrival-tracking")
def arrival_tracking(
    project_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """项目物料到料跟踪看板"""
    query = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.status != 'CANCELLED')
    if project_id:
        query = query.filter(models.PurchaseOrder.project_id == project_id)

    orders = query.all()
    tracking = []

    for po in orders:
        items = db.query(models.PurchaseOrderItem).filter(models.PurchaseOrderItem.purchase_order_id == po.id).all()
        for item in items:
            # 查到料记录
            received = float(item.received_qty or 0)
            ordered = float(item.quantity or 0)
            arrival_rate = (received / ordered * 100) if ordered > 0 else 0

            material = db.query(models.Material).filter(models.Material.id == item.material_id).first() if item.material_id else None

            tracking.append({
                "po_id": po.id,
                "po_no": po.order_no if hasattr(po, 'order_no') else f"PO-{po.id}",
                "project_id": po.project_id,
                "material_id": item.material_id,
                "material_code": material.code if material else "-",
                "material_name": material.name if material else "-",
                "ordered_qty": ordered,
                "received_qty": received,
                "arrival_rate": round(arrival_rate, 1),
                "planned_date": str(po.expected_date) if hasattr(po, 'expected_date') and po.expected_date else None,
                "actual_date": str(po.received_date) if hasattr(po, 'received_date') and po.received_date else None,
                "is_critical": getattr(item, 'is_critical', False),
                "status": "已到齐" if arrival_rate >= 100 else ("部分到料" if arrival_rate > 0 else "未到料"),
                "delayed_days": _calc_delay(po),
            })

    # 汇总
    total_items = len(tracking)
    arrived = sum(1 for t in tracking if t['arrival_rate'] >= 100)
    partial = sum(1 for t in tracking if 0 < t['arrival_rate'] < 100)
    not_arrived = sum(1 for t in tracking if t['arrival_rate'] == 0)
    critical_short = sum(1 for t in tracking if t['is_critical'] and t['arrival_rate'] < 100)

    return {
        "success": True,
        "data": tracking,
        "summary": {
            "total": total_items,
            "arrived": arrived,
            "partial": partial,
            "not_arrived": not_arrived,
            "critical_short": critical_short,
            "overall_arrival_rate": round(sum(t['arrival_rate'] for t in tracking) / total_items, 1) if total_items else 0,
        }
    }

def _calc_delay(po):
    if not hasattr(po, 'expected_date') or not po.expected_date:
        return 0
    if hasattr(po, 'received_date') and po.received_date:
        delta = (po.received_date - po.expected_date).days
        return max(0, delta)
    delta = (datetime.date.today() - po.expected_date).days
    return max(0, delta) if delta > 0 else 0


# ============================================================
# 4. 建档发料 —— 4种领料模式
# ============================================================

PICKING_MODES = {
    1: {"id": 1, "name": "按单领料", "icon": "📋", "desc": "操作工拿工单去仓库领料", "default": True},
    2: {"id": 2, "name": "配料制", "icon": "🔧", "desc": "仓库按BOM配齐，整项目发到车间"},
    3: {"id": 3, "name": "集中领料", "icon": "🏭", "desc": "仓库定时定量配送到线边"},
    4: {"id": 4, "name": "倒冲领料", "icon": "⬇️", "desc": "完工入库时按BOM定额自动反扣"},
}

@router.get("/picking-modes")
def get_picking_modes():
    """获取4种领料模式定义"""
    return {"success": True, "data": list(PICKING_MODES.values())}


@router.put("/materials/{material_id}/picking-mode")
def set_material_picking_mode(material_id: int, data: dict, db: Session = Depends(get_db)):
    """设置物料的领料模式"""
    m = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not m:
        raise HTTPException(404, "物料不存在")

    mode = int(data.get('picking_mode', 1))
    if mode not in PICKING_MODES:
        raise HTTPException(400, "无效的领料模式")

    m.picking_mode = mode
    db.commit()

    return {"success": True, "message": f"物料{m.code}领料模式已设置为「{PICKING_MODES[mode]['name']}」"}


@router.get("/materials/picking-modes")
def get_all_picking_modes(db: Session = Depends(get_db)):
    """获取所有物料的领料模式配置"""
    materials = db.query(models.Material).all()

    result = []
    for m in materials:
        mode = getattr(m, 'picking_mode', None) or 1
        result.append({
            "material_id": m.id,
            "material_code": m.code,
            "material_name": m.name,
            "material_type": m.type.value if m.type else "RAW_MATERIAL",
            "picking_mode": mode,
            "picking_mode_name": PICKING_MODES[mode]["name"],
            "picking_mode_icon": PICKING_MODES[mode]["icon"],
        })
    return {"success": True, "data": result}


# ============================================================
# 5. ROI 看板
# ============================================================

@router.get("/roi/dashboard")
def roi_dashboard(db: Session = Depends(get_db)):
    """ROI看板：周转率×利润率=投资回报率"""
    # 按物料计算
    materials = db.query(models.Material).filter(models.Material.type.in_([models.MaterialType.RAW_MATERIAL, models.MaterialType.SEMI_FINISHED])).all()
    items = []

    for m in materials:
        # 年销售成本（从库存事务中统计出库金额）
        outbound_value = db.query(func.sum(models.InventoryTransaction.quantity * models.InventoryTransaction.unit_cost)).filter(
            and_(
                models.InventoryTransaction.material_id == m.id,
                models.InventoryTransaction.transaction_type == models.TransactionType.OUTBOUND
            )
        ).scalar() or 0

        # 平均库存
        avg_inventory_value = db.query(func.avg(models.InventoryTransaction.quantity * models.InventoryTransaction.unit_cost)).filter(
            models.InventoryTransaction.material_id == m.id
        ).scalar() or 0

        if avg_inventory_value > 0 and outbound_value > 0:
            turnover = float(outbound_value) / float(avg_inventory_value)
            cost = float(m.unit_price or 0)
            price = cost * 1.3 if cost > 0 else 0
            profit_rate = ((price - cost) / price) if price > 0 else 0
            roi = turnover * profit_rate
        else:
            turnover = 0
            profit_rate = 0
            roi = 0

        items.append({
            "material_id": m.id,
            "material_code": m.code,
            "material_name": m.name,
            "outbound_value": round(float(outbound_value), 2),
            "avg_inventory_value": round(float(avg_inventory_value), 2),
            "turnover": round(turnover, 2),
            "profit_rate": round(profit_rate * 100, 2),
            "roi": round(roi, 4),
            "roi_level": "高" if roi >= 3 else ("中" if roi >= 1 else "低"),
        })

    items.sort(key=lambda x: x['roi'], reverse=True)

    # 汇总
    total_outbound = sum(i['outbound_value'] for i in items)
    total_inventory = sum(i['avg_inventory_value'] for i in items)
    overall_turnover = total_outbound / total_inventory if total_inventory > 0 else 0
    overall_profit = sum(i['profit_rate'] for i in items) / len(items) if items else 0
    overall_roi = overall_turnover * (overall_profit / 100)

    return {
        "success": True,
        "data": {
            "items": items[:50],  # Top 50
            "summary": {
                "total_materials": len(items),
                "total_outbound_value": round(total_outbound, 2),
                "total_inventory_value": round(total_inventory, 2),
                "overall_turnover": round(overall_turnover, 2),
                "overall_profit_rate": round(overall_profit, 2),
                "overall_roi": round(overall_roi, 4),
            }
        }
    }


# ============================================================
# 6. 物料底层治理 —— 双编码规则 + 去重
# ============================================================

@router.get("/material-governance/check-duplicates")
def check_duplicate_materials(db: Session = Depends(get_db)):
    """检查重复物料（同名/同规格不同编码）"""
    materials = db.query(models.Material).all()
    name_groups = {}
    for m in materials:
        key = m.name.strip().lower() if m.name else ""
        if key:
            if key not in name_groups:
                name_groups[key] = []
            name_groups[key].append({
                "id": m.id, "code": m.code, "name": m.name,
                "spec": getattr(m, 'specification', '') or getattr(m, 'spec', ''),
                "unit": m.unit if hasattr(m, 'unit') else "",
            })

    duplicates = {k: v for k, v in name_groups.items() if len(v) > 1}

    return {
        "success": True,
        "data": {
            "duplicates": list(duplicates.values()),
            "duplicate_count": sum(len(v) for v in duplicates.values()),
            "total_materials": len(materials),
        }
    }


@router.post("/material-governance/merge")
def merge_materials(data: dict, db: Session = Depends(get_db)):
    """合并重复物料：保留主物料，将事务迁移到主物料"""
    keep_id = int(data.get('keep_id'))
    merge_ids = data.get('merge_ids', [])

    if not keep_id or not merge_ids:
        raise HTTPException(400, "请指定保留物料和合并物料")

    merged = 0
    for mid in merge_ids:
        mid = int(mid)
        if mid == keep_id:
            continue
        # 迁移库存事务
        db.query(models.InventoryTransaction).filter(
            models.InventoryTransaction.material_id == mid
        ).update({"material_id": keep_id})
        # 迁移BOM项
        db.query(models.BOMItem).filter(
            models.BOMItem.material_id == mid
        ).update({"material_id": keep_id})
        # 删除重复物料
        m = db.query(models.Material).filter(models.Material.id == mid).first()
        if m:
            db.delete(m)
            merged += 1

    db.commit()
    return {"success": True, "message": f"已合并{merged}个重复物料"}


@router.get("/material-governance/coding-rules")
def get_coding_rules():
    """获取双编码规则"""
    return {
        "success": True,
        "data": {
            "standard": {
                "name": "标准件编码规则",
                "rule": "规格型号+品牌",
                "examples": ["FLANGE-DN50-316L-Hengtong", "BEARING-6204-SKF"],
                "applies_to": "电气元件、气动元件、紧固件、密封圈、导轨",
                "principle": "一物一码，专人维护，严禁重复创建",
            },
            "non_standard": {
                "name": "非标件编码规则",
                "rule": "项目图号+零件号",
                "examples": ["P2024-001-DWG-A03", "P2024-001-DWG-B12"],
                "applies_to": "机加件、钣金件、焊接件、定制轴套",
                "principle": "每次新图必须新码，即使长得一样只要图号不同就不同码",
            },
            "creation_flow": "新物料创建须经「技术+PMC」双确认",
        }
    }


# ============================================================
# 7. 流程卡点校验
# ============================================================

@router.post("/checkpoints/validate")
def validate_checkpoint(data: dict, db: Session = Depends(get_db)):
    """流程卡点校验"""
    checkpoint = int(data.get('checkpoint', 0))
    result = {"checkpoint": checkpoint, "passed": True, "message": "", "details": {}}

    if checkpoint == 1:
        # 卡点①：项目预算校验
        project_id = data.get('project_id')
        amount = float(data.get('amount', 0))
        if project_id:
            project = db.query(models.WBSProject).filter(models.WBSProject.id == project_id).first()
            if project:
                budget = float(project.budget_amount or 0)
                incurred = float(project.incurred_cost or 0)
                remaining = budget - incurred
                result['details'] = {
                    "budget": budget, "incurred": incurred,
                    "remaining": remaining, "this_amount": amount,
                }
                if amount > remaining:
                    result['passed'] = False
                    result['message'] = f"预算超支！剩余{remaining}元，本次需{amount}元"
                else:
                    result['message'] = f"预算校验通过，剩余{remaining}元"

    elif checkpoint == 2:
        # 卡点②：库存是否够用
        material_id = data.get('material_id')
        need_qty = float(data.get('need_qty', 0))
        if material_id:
            avail = db.query(func.sum(models.InventoryTransaction.quantity)).filter(
                and_(
                    models.InventoryTransaction.material_id == material_id,
                    models.InventoryTransaction.transaction_type == 'INBOUND'
                )
            ).scalar() or 0
            consumed = db.query(func.sum(models.InventoryTransaction.quantity)).filter(
                and_(
                    models.InventoryTransaction.material_id == material_id,
                    models.InventoryTransaction.transaction_type == 'OUTBOUND'
                )
            ).scalar() or 0
            available = float(avail) - float(consumed)
            result['details'] = {"available": available, "need": need_qty}
            if available >= need_qty:
                result['message'] = f"库存充足，可用{available}，需求{need_qty}"
            else:
                result['passed'] = False
                result['message'] = f"库存不足！可用{available}，需求{need_qty}，建议采购{need_qty - available}"

    elif checkpoint == 3:
        # 卡点③：≥3家比价
        material_id = data.get('material_id')
        if material_id:
            quotes = db.query(models.PurchaseQuotation).filter(
                models.PurchaseQuotation.material_id == material_id
            ).all()
            count = len(quotes)
            result['details'] = {"quote_count": count}
            if count >= 3:
                result['message'] = f"已有{count}家报价，满足比价要求"
            else:
                result['passed'] = False
                result['message'] = f"仅有{count}家报价，需至少3家才能进入审批"

    elif checkpoint == 4:
        # 卡点④：额度权限
        employee_id = data.get('employee_id')
        amount = float(data.get('amount', 0))
        if employee_id:
            emp = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
            if emp:
                limit = float(getattr(emp, 'approval_limit', 50000) or 50000)
                result['details'] = {"approval_limit": limit, "amount": amount}
                if amount <= limit:
                    result['message'] = f"额度内审批，限额{limit}元"
                else:
                    result['passed'] = False
                    result['message'] = f"超出额度！限额{limit}元，需{amount}元，需上级审批"

    elif checkpoint == 5:
        # 卡点⑤：检验合格率
        inspection_id = data.get('inspection_id')
        threshold = float(data.get('threshold', 95))
        if inspection_id:
            insp = db.query(models.QualityInspection).filter(models.QualityInspection.id == inspection_id).first()
            if insp:
                total = float(insp.total_qty or 0)
                passed = float(insp.passed_qty or 0)
                rate = (passed / total * 100) if total > 0 else 0
                result['details'] = {"pass_rate": rate, "threshold": threshold}
                if rate >= threshold:
                    result['message'] = f"检验合格率{rate}%，达标"
                else:
                    result['passed'] = False
                    result['message'] = f"检验合格率{rate}%，低于阈值{threshold}%，需退货"

    elif checkpoint == 6:
        # 卡点⑥：项目号绑定
        project_id = data.get('project_id')
        result['details'] = {"project_id": project_id}
        if project_id:
            result['message'] = "已绑定项目号"
        else:
            result['passed'] = False
            result['message'] = "未绑定项目号！所有领料单必须绑定项目号"

    return result


@router.get("/checkpoints/list")
def get_checkpoints():
    """获取6个流程卡点定义"""
    return {
        "success": True,
        "data": [
            {"id": 1, "name": "项目预算校验", "rule": "本次采购金额 ≤ 项目剩余预算", "fail_action": "退回申请人，提示预算超支"},
            {"id": 2, "name": "库存是否够用", "rule": "可用库存 ≥ 需求量", "fail_action": "系统自动生成采购建议量"},
            {"id": 3, "name": "≥3家比价", "rule": "同一物料至少录入3家供应商报价", "fail_action": "无法进入审批环节"},
            {"id": 4, "name": "额度权限匹配", "rule": "采购金额 ≤ 员工审批额度权限", "fail_action": "自动流转到上级审批"},
            {"id": 5, "name": "检验合格率", "rule": "IQC检验合格率 ≥ 设定阈值", "fail_action": "不合格批次退回供应商"},
            {"id": 6, "name": "项目号绑定", "rule": "所有领料单必须绑定项目号", "fail_action": "无法发料，强制补填项目号"},
        ]
    }


# ============================================================
# 8. 登录选型门 —— 行业类型→业务模式→收入确认→领料方式
# ============================================================

INDUSTRY_TYPES = {
    "engineering": {"name": "工程导向型", "icon": "🔧", "desc": "专用设备制造、建筑业、非标自动化"},
    "agility": {"name": "敏捷导向型", "icon": "⚡", "desc": "纺织服装、批发零售、餐饮"},
    "compliance": {"name": "合规导向型", "icon": "🛡️", "desc": "金融、IT服务、医疗、航空航天"},
    "subscription": {"name": "订阅导向型", "icon": "🔄", "desc": "SaaS、在线教育、物业管理"},
}

# A模式自动匹配行业
AUTO_DETECT_A = ["汽车制造", "白色家电", "标准件", "消费电子", "标准电机", "减速机", "压缩机", "阀门", "泵", "建材预制"]
AUTO_DETECT_B = ["非标自动化", "模具", "船舶", "重型装备", "航空", "定制家具", "建筑装饰", "环保设备", "定制机械", "电力工程"]

REVENUE_MODES = {
    "percentage": {"name": "完工百分比法", "desc": "按项目完工进度确认收入，里程碑达成时触发", "default": True},
    "shipment": {"name": "按出库确认", "desc": "成品出库时确认收入", "default": False},
}

@router.get("/selection-gate/options")
def get_selection_gate_options():
    """获取选型门所有选项"""
    return {
        "success": True,
        "data": {
            "industry_types": INDUSTRY_TYPES,
            "business_modes": {
                "A": {"name": "大批量单品种", "desc": "规模效应，产品少批量大，工艺稳定", "default": False},
                "B": {"name": "小批量多品种", "desc": "柔性制造，产品多批量小，工艺频繁切换", "default": True},
            },
            "revenue_modes": REVENUE_MODES,
            "picking_modes": PICKING_MODES,
            "auto_detect": {
                "A_industries": AUTO_DETECT_A,
                "B_industries": AUTO_DETECT_B,
                "rule": "看备料方式：吨/卷采购大宗原材料→A模式；个/套采购大量SKU→B模式。若无法判断，默认B模式",
            },
        }
    }


@router.post("/selection-gate/save")
def save_selection_gate(data: dict, db: Session = Depends(get_db)):
    """保存选型门配置（使用EnterpriseConfig单例）"""
    industry_type = data.get('industry_type', 'engineering')
    business_mode = data.get('business_mode', 'B')
    revenue_mode = data.get('revenue_mode', 'percentage')
    picking_mode = data.get('picking_mode', 1)
    sub_industry = data.get('sub_industry', '')

    # 自动判断业务模式
    if sub_industry and not data.get('manual_override'):
        for kw in AUTO_DETECT_A:
            if kw in sub_industry:
                business_mode = 'A'
                break
        else:
            for kw in AUTO_DETECT_B:
                if kw in sub_industry:
                    business_mode = 'B'
                    break
            else:
                business_mode = 'B'  # 默认B模式

    # 映射到EnterpriseConfig字段
    revenue_map = {
        'percentage': 'percentage_of_completion',
        'shipment': 'on_delivery',
    }
    picking_map = {1: 'by_order', 2: 'batch_prep', 3: 'central', 4: 'backflush'}
    picking_modes_json = json.dumps([picking_map.get(int(picking_mode), 'by_order')])

    # upsert单例配置
    config = db.query(models.EnterpriseConfig).filter(models.EnterpriseConfig.id == 1).first()
    if not config:
        config = models.EnterpriseConfig(id=1)
        db.add(config)

    config.industry_type = industry_type
    config.business_mode = business_mode
    config.revenue_method = revenue_map.get(revenue_mode, 'percentage_of_completion')
    config.picking_modes = picking_modes_json
    config.sub_industry = sub_industry

    db.commit()

    return {
        "success": True,
        "message": "选型配置已保存",
        "data": {
            "industry_type": industry_type,
            "industry_name": INDUSTRY_TYPES.get(industry_type, {}).get('name', ''),
            "business_mode": business_mode,
            "revenue_mode": revenue_mode,
            "picking_mode": picking_mode,
            "auto_detected": not data.get('manual_override', False),
        }
    }


@router.get("/selection-gate/current")
def get_current_selection(db: Session = Depends(get_db)):
    """获取当前选型配置"""
    config = db.query(models.EnterpriseConfig).filter(models.EnterpriseConfig.id == 1).first()

    if not config:
        return {
            "success": True,
            "data": {
                "industry_type": "engineering",
                "business_mode": "B",
                "revenue_mode": "percentage",
                "picking_mode": 1,
                "sub_industry": "",
            }
        }

    # 反向映射
    revenue_reverse = {
        'percentage_of_completion': 'percentage',
        'on_delivery': 'shipment',
    }
    picking_reverse = {'by_order': 1, 'batch_prep': 2, 'central': 3, 'backflush': 4}

    try:
        pm_list = json.loads(config.picking_modes or '["by_order"]')
        pm_int = picking_reverse.get(pm_list[0] if pm_list else 'by_order', 1)
    except Exception:
        pm_int = 1

    return {
        "success": True,
        "data": {
            "industry_type": config.industry_type or "engineering",
            "business_mode": config.business_mode or "B",
            "revenue_mode": revenue_reverse.get(config.revenue_method, 'percentage'),
            "picking_mode": pm_int,
            "sub_industry": config.sub_industry or "",
        }
    }
