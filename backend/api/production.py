from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
import datetime
from decimal import Decimal

from .. import crud, schemas, models
from ..database import get_db
from ..app import make_response
from ..utils import allocate_cost, allocate_cost_by_type
from ..models import CostType, WorkOrderStatus

router = APIRouter()


@router.post("/boms/{bom_id}/explode", tags=["生产管理"])
def explode_bom(bom_id: int, quantity: int = 1, db: Session = Depends(get_db)):
    db_bom = crud.get_bom(db, bom_id=bom_id)
    if db_bom is None:
        return make_response(False, None, "BOM不存在", "40002")

    exploded_items = []
    for item in db_bom.items:
        required_qty = item.quantity * quantity * (1 + item.scrap_rate)
        inventory = crud.get_inventory_record(db, material_id=item.material_id, location_code="WH")
        exploded_items.append({
            "material_id": item.material_id,
            "material_name": item.material.name if item.material else "",
            "material_code": item.material.code if item.material else "",
            "quantity": float(required_qty),
            "unit": item.unit,
            "level": item.level,
            "scrap_rate": float(item.scrap_rate),
            "current_stock": float(inventory.quantity) if inventory else 0,
            "shortage": float(max(0, required_qty - (inventory.quantity if inventory else 0)))
        })

    return make_response(True, {
        "bom_id": db_bom.id,
        "product_id": db_bom.product_id,
        "product_name": db_bom.product.name if db_bom.product else "",
        "quantity": quantity,
        "exploded_items": exploded_items,
        "has_shortage": any(item["shortage"] > 0 for item in exploded_items)
    }, "BOM展开完成")


@router.post("/monthly-cost-allocation", tags=["生产管理"])
def monthly_cost_allocation(account_set_id: int, month: int, year: int, db: Session = Depends(get_db)):
    first_day = datetime.date(year, month, 1)
    last_day = datetime.date(year, month, 1) + datetime.timedelta(days=32)
    last_day = last_day - datetime.timedelta(days=last_day.day)

    workorders = crud.get_workorders_by_period(db, account_set_id=account_set_id, start_date=first_day, end_date=last_day)

    results = []
    for wo in workorders:
        if wo.status == WorkOrderStatus.COMPLETED:
            costs = crud.get_production_costs(db, work_order_id=wo.id)
            total_material = sum(c.amount for c in costs if c.cost_type == CostType.RAW_MATERIAL)
            total_labor = sum(c.amount for c in costs if c.cost_type == CostType.DIRECT_LABOR)
            total_overhead = sum(c.amount for c in costs if c.cost_type == CostType.MANUFACTURING_OVERHEAD)

            unit_material = total_material / wo.completed_qty if wo.completed_qty > 0 else 0
            unit_labor = total_labor / wo.completed_qty if wo.completed_qty > 0 else 0
            unit_overhead = total_overhead / wo.completed_qty if wo.completed_qty > 0 else 0
            unit_total = unit_material + unit_labor + unit_overhead

            results.append({
                "work_order_no": wo.work_order_no,
                "product_name": wo.product.name if wo.product else "",
                "completed_qty": wo.completed_qty,
                "total_cost": float(total_material + total_labor + total_overhead),
                "unit_cost": {
                    "material": float(unit_material),
                    "labor": float(unit_labor),
                    "overhead": float(unit_overhead),
                    "total": float(unit_total)
                },
                "status": "completed"
            })
        elif wo.status == WorkOrderStatus.IN_PROGRESS and wo.in_progress_qty > 0:
            costs = crud.get_production_costs(db, work_order_id=wo.id)
            total_material = sum(c.amount for c in costs if c.cost_type == CostType.RAW_MATERIAL)
            total_labor = sum(c.amount for c in costs if c.cost_type == CostType.DIRECT_LABOR)
            total_overhead = sum(c.amount for c in costs if c.cost_type == CostType.MANUFACTURING_OVERHEAD)

            completion_ratio = wo.completion_ratio or 0.5

            equiv_material_qty = wo.completed_qty + wo.in_progress_qty * (wo.material_ratio or 1.0)
            equiv_labor_qty = wo.completed_qty + wo.in_progress_qty * (wo.labor_ratio or completion_ratio)
            equiv_overhead_qty = wo.completed_qty + wo.in_progress_qty * (wo.overhead_ratio or completion_ratio)

            cost_per_equiv_material = total_material / equiv_material_qty if equiv_material_qty > 0 else 0
            cost_per_equiv_labor = total_labor / equiv_labor_qty if equiv_labor_qty > 0 else 0
            cost_per_equiv_overhead = total_overhead / equiv_overhead_qty if equiv_overhead_qty > 0 else 0

            completed_cost_material = wo.completed_qty * cost_per_equiv_material
            completed_cost_labor = wo.completed_qty * cost_per_equiv_labor
            completed_cost_overhead = wo.completed_qty * cost_per_equiv_overhead

            wip_cost_material = wo.in_progress_qty * (wo.material_ratio or 1.0) * cost_per_equiv_material
            wip_cost_labor = wo.in_progress_qty * (wo.labor_ratio or completion_ratio) * cost_per_equiv_labor
            wip_cost_overhead = wo.in_progress_qty * (wo.overhead_ratio or completion_ratio) * cost_per_equiv_overhead

            results.append({
                "work_order_no": wo.work_order_no,
                "product_name": wo.product.name if wo.product else "",
                "completed_qty": wo.completed_qty,
                "wip_qty": wo.in_progress_qty,
                "completion_ratio": float(completion_ratio),
                "total_cost_input": float(total_material + total_labor + total_overhead),
                "completed_allocation": {
                    "material": float(completed_cost_material),
                    "labor": float(completed_cost_labor),
                    "overhead": float(completed_cost_overhead),
                    "total": float(completed_cost_material + completed_cost_labor + completed_cost_overhead)
                },
                "wip_allocation": {
                    "material": float(wip_cost_material),
                    "labor": float(wip_cost_labor),
                    "overhead": float(wip_cost_overhead),
                    "total": float(wip_cost_material + wip_cost_labor + wip_cost_overhead)
                },
                "cost_per_equivalent": {
                    "material": float(cost_per_equiv_material),
                    "labor": float(cost_per_equiv_labor),
                    "overhead": float(cost_per_equiv_overhead)
                },
                "status": "in_progress"
            })

    return make_response(True, {
        "period": f"{year}-{month:02d}",
        "total_workorders": len(workorders),
        "completed_count": sum(1 for r in results if r["status"] == "completed"),
        "wip_count": sum(1 for r in results if r["status"] == "in_progress"),
        "allocations": results
    }, "月末成本分摊完成")

@router.post("/workorders", tags=["生产管理"])
def create_workorder(workorder: schemas.ProductionWorkOrderCreate, db: Session = Depends(get_db)):
    db_workorder = crud.get_workorder_by_no(db, work_order_no=workorder.work_order_no)
    if db_workorder:
        return make_response(False, None, "工单号已存在", "40003")
    
    if workorder.bom_id:
        bom = crud.get_bom(db, bom_id=workorder.bom_id)
        if bom:
            reserved_items = []
            for item in bom.items:
                required_qty = item.quantity * workorder.planned_qty * (1 + item.scrap_rate)
                inventory = crud.get_inventory_record(db, material_id=item.material_id, location_code="WH")
                if inventory and inventory.quantity < required_qty:
                    return make_response(False, None, f"物料{item.material.name if item.material else ''}库存不足", "40003")
                reserved_items.append({
                    "material_id": item.material_id,
                    "required_qty": required_qty,
                    "reserved": True
                })
    
    created = crud.create_workorder(db, workorder)
    return make_response(True, {"workorder": created, "reserved_items": reserved_items if workorder.bom_id else []}, "创建成功")

@router.get("/workorders", tags=["生产管理"])
def list_workorders(account_set_id: Optional[int] = None, skip: int = 0, limit: int = 100, status: str = None, db: Session = Depends(get_db)):
    workorders = crud.get_workorders(db, skip=skip, limit=limit, status=status)
    total = crud.get_workorders_count(db, status=status)
    return make_response(True, {"items": workorders, "total": total}, "查询成功")

@router.get("/workorders/{workorder_id}", tags=["生产管理"])
def get_workorder(workorder_id: int, db: Session = Depends(get_db)):
    db_workorder = crud.get_workorder(db, workorder_id=workorder_id)
    if db_workorder is None:
        return make_response(False, None, "工单不存在", "40002")
    
    costs = crud.get_production_costs(db, work_order_id=workorder_id)
    allocations = crud.get_cost_allocations(db, work_order_id=workorder_id)
    
    total_actual_cost = db_workorder.actual_material_cost + db_workorder.actual_labor_cost + db_workorder.actual_overhead_cost
    unit_cost = 0
    if db_workorder.completed_qty > 0:
        unit_cost = total_actual_cost / db_workorder.completed_qty
    
    variance = 0
    if db_workorder.standard_cost:
        variance = total_actual_cost - db_workorder.standard_cost
    
    result = {
        **schemas.ProductionWorkOrder.from_orm(db_workorder).dict(),
        "cost_summary": {
            "total_actual_cost": float(total_actual_cost),
            "actual_material_cost": float(db_workorder.actual_material_cost),
            "actual_labor_cost": float(db_workorder.actual_labor_cost),
            "actual_overhead_cost": float(db_workorder.actual_overhead_cost),
            "unit_cost": float(unit_cost),
            "standard_cost": float(db_workorder.standard_cost) if db_workorder.standard_cost else 0,
            "variance": float(variance)
        },
        "costs": costs,
        "allocations": allocations
    }
    
    return make_response(True, result, "查询成功")

@router.post("/workorders/{workorder_id}/start", tags=["生产管理"])
def start_workorder(workorder_id: int, db: Session = Depends(get_db)):
    db_workorder = crud.get_workorder(db, workorder_id=workorder_id)
    if db_workorder is None:
        return make_response(False, None, "工单不存在", "40002")
    
    db_workorder.status = WorkOrderStatus.IN_PROGRESS
    db.commit()
    db.refresh(db_workorder)
    return make_response(True, db_workorder, "工单已开始")

@router.post("/workorders/{workorder_id}/complete", tags=["生产管理"])
def complete_workorder(workorder_id: int, completed_qty: int, db: Session = Depends(get_db)):
    db_workorder = crud.get_workorder(db, workorder_id=workorder_id)
    if db_workorder is None:
        return make_response(False, None, "工单不存在", "40002")
    
    db_workorder.completed_qty = completed_qty
    db_workorder.in_progress_qty = 0
    db_workorder.status = WorkOrderStatus.COMPLETED
    db.commit()
    db.refresh(db_workorder)
    
    total_cost = db_workorder.actual_material_cost + db_workorder.actual_labor_cost + db_workorder.actual_overhead_cost
    unit_cost = total_cost / completed_qty if completed_qty > 0 else 0
    
    return make_response(True, {
        "workorder": db_workorder,
        "unit_cost": float(unit_cost),
        "total_cost": float(total_cost)
    }, "工单已完成")

@router.post("/costs", tags=["生产管理"])
def create_production_cost(cost: schemas.ProductionCostCreate, db: Session = Depends(get_db)):
    db_workorder = crud.get_workorder(db, workorder_id=cost.work_order_id)
    if db_workorder is None:
        return make_response(False, None, "工单不存在", "40002")
    
    created = crud.create_production_cost(db, cost)
    
    if cost.cost_type == CostType.RAW_MATERIAL:
        db_workorder.actual_material_cost += cost.amount
    elif cost.cost_type == CostType.DIRECT_LABOR:
        db_workorder.actual_labor_cost += cost.amount
    elif cost.cost_type == CostType.MANUFACTURING_OVERHEAD:
        db_workorder.actual_overhead_cost += cost.amount
    
    db.commit()
    db.refresh(db_workorder)
    
    return make_response(True, {"cost": created, "workorder": db_workorder}, "成本录入成功")

@router.get("/costs", tags=["生产管理"])
def list_production_costs(work_order_id: int = None, db: Session = Depends(get_db)):
    costs = crud.get_production_costs(db, work_order_id=work_order_id)
    return make_response(True, costs, "查询成功")

@router.post("/allocation", tags=["生产管理"])
def calculate_cost_allocation(request: schemas.CostAllocationRequest, db: Session = Depends(get_db)):
    db_workorder = crud.get_workorder(db, workorder_id=request.work_order_id)
    if db_workorder is None:
        return make_response(False, None, "工单不存在", "40002")
    
    costs = crud.get_production_costs(db, work_order_id=request.work_order_id)
    if not costs:
        return make_response(False, None, "该工单暂无成本记录", "40003")
    
    total_cost = sum(c.amount for c in costs)
    
    cost_list = [{"cost_type": c.cost_type.value, "amount": float(c.amount)} for c in costs]
    
    allocation_result = allocate_cost_by_type(
        cost_list,
        request.completed_qty,
        request.in_progress_qty,
        request.completion_ratio
    )
    
    total_allocation = allocation_result["total"]
    
    crud.create_cost_allocation(db, schemas.CostAllocationCreate(
        work_order_id=request.work_order_id,
        total_input_cost=total_allocation["total_input_cost"],
        equivalent_output=total_allocation["equivalent_output"],
        cost_per_equivalent=total_allocation["cost_per_equivalent"],
        completed_allocation=total_allocation["completed_allocation"],
        in_progress_allocation=total_allocation["in_progress_allocation"],
        material_ratio=request.material_ratio,
        labor_ratio=request.labor_ratio,
        overhead_ratio=request.overhead_ratio
    ))
    
    crud.update_workorder_progress(db, request.work_order_id, request.completed_qty, request.in_progress_qty, request.completion_ratio)
    
    result = {
        "work_order_id": request.work_order_id,
        "work_order_no": db_workorder.work_order_no,
        **total_allocation,
        "breakdown": {k: v for k, v in allocation_result.items() if k != "total"}
    }
    
    return make_response(True, result, "成本分摊完成")

@router.get("/allocation/{workorder_id}", tags=["生产管理"])
def get_cost_allocation(workorder_id: int, db: Session = Depends(get_db)):
    allocations = crud.get_cost_allocations(db, work_order_id=workorder_id)
    return make_response(True, allocations, "查询成功")

@router.post("/workorders/{workorder_id}/split", tags=["生产管理"])
def split_workorder(workorder_id: int, new_work_order_no: str, split_qty: int, db: Session = Depends(get_db)):
    db_workorder = crud.get_workorder(db, workorder_id=workorder_id)
    if db_workorder is None:
        return make_response(False, None, "工单不存在", "40002")
    
    if split_qty >= db_workorder.planned_qty:
        return make_response(False, None, "拆分数量不能大于原工单数量", "40003")
    
    db_workorder.planned_qty -= split_qty
    
    new_workorder = schemas.ProductionWorkOrderCreate(
        work_order_no=new_work_order_no,
        product_id=db_workorder.product_id,
        bom_id=db_workorder.bom_id,
        planned_qty=split_qty,
        start_date=db_workorder.start_date,
        end_date=db_workorder.end_date,
        account_set_id=db_workorder.account_set_id,
        standard_cost=db_workorder.standard_cost
    )
    
    new_created = crud.create_workorder(db, new_workorder)
    
    db.commit()
    db.refresh(db_workorder)
    
    return make_response(True, {"original": db_workorder, "new": new_created}, "工单拆分完成")