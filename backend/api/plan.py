from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import datetime

from ..database import get_db
from .. import crud, schemas, models
from ..app import make_response

router = APIRouter()

def get_on_order_qty(db: Session, account_set_id: int, material_id: int) -> float:
    on_order = 0.0
    purchase_orders = crud.get_purchase_orders(db, account_set_id=account_set_id, status="PENDING")
    for po in purchase_orders:
        for item in po.items:
            if item.material_id == material_id:
                on_order += float(item.quantity)
    
    production_orders = crud.get_production_workorders(db, account_set_id=account_set_id, status="PLANNED")
    for prod in production_orders:
        if prod.product_id == material_id:
            on_order += float(prod.planned_qty) - float(prod.completed_qty)
    
    planned_orders = crud.get_planned_orders(db, account_set_id=account_set_id, status="PENDING")
    for po in planned_orders:
        if po.material_id == material_id:
            on_order += float(po.planned_qty)
    
    return on_order

def apply_batch_rule(net_requirement: float, batch_rule: str, batch_size: float) -> float:
    if net_requirement <= 0:
        return 0.0
    
    if batch_rule == "FIXED":
        return net_requirement
    elif batch_rule == "MULTIPLE":
        if batch_size <= 0:
            return net_requirement
        remainder = net_requirement % batch_size
        if remainder == 0:
            return net_requirement
        return net_requirement + (batch_size - remainder)
    elif batch_rule == "MINIMUM":
        return max(net_requirement, batch_size)
    else:
        return net_requirement

def calculate_release_date(planned_date: datetime.date, lead_time: int) -> datetime.date:
    if lead_time <= 0:
        return planned_date
    return planned_date - datetime.timedelta(days=lead_time)

def expand_bom(
    db: Session,
    account_set_id: int,
    mrp_run_no: str,
    material_id: int,
    parent_material_id: Optional[int],
    bom_level: int,
    gross_requirement: float,
    planned_date: datetime.date,
    source_order_id: int,
    source_order_no: str,
    processed_materials: set = None
) -> Dict[str, Any]:
    if processed_materials is None:
        processed_materials = set()
    
    if material_id in processed_materials:
        return {"mrp_results": [], "planned_orders": []}
    
    processed_materials.add(material_id)
    
    material = crud.get_material(db, material_id=material_id)
    if not material:
        return {"mrp_results": [], "planned_orders": []}
    
    inventories = crud.get_batch_inventories(db, account_set_id=account_set_id, material_id=material_id)
    on_hand_qty = sum(float(inv.quantity) for inv in inventories if inv.quality_status == "AVAILABLE")
    
    on_order_qty = get_on_order_qty(db, account_set_id, material_id)
    safety_stock = float(material.safety_stock or 0)
    loss_rate = float(material.loss_rate or 0)
    
    adjusted_gross = gross_requirement * (1 + loss_rate / 100)
    net_requirement = max(0, adjusted_gross - on_hand_qty - on_order_qty + safety_stock)
    
    batch_rule = material.batch_rule or "FIXED"
    batch_size = float(material.batch_size or 1)
    planned_order_qty = apply_batch_rule(net_requirement, batch_rule, batch_size)
    
    lead_time = material.lead_time or 0
    planned_release_date = calculate_release_date(planned_date, lead_time)
    
    material_property = str(material.property.value) if material.property else "PURCHASE"
    
    if material_property == "INHOUSE":
        order_type = "PRODUCTION"
    elif material_property == "OUTSOURCING":
        order_type = "OUTSOURCING"
    else:
        order_type = "PURCHASE"
    
    mrp_result = crud.create_mrp_result(db, schemas.MRPResultCreate(
        account_set_id=account_set_id,
        mrp_run_no=mrp_run_no,
        material_id=material_id,
        parent_material_id=parent_material_id,
        bom_level=bom_level,
        gross_requirement=gross_requirement,
        on_hand_qty=on_hand_qty,
        on_order_qty=on_order_qty,
        safety_stock=safety_stock,
        net_requirement=net_requirement,
        planned_order_qty=planned_order_qty,
        planned_date=planned_date,
        planned_release_date=planned_release_date,
        planned_type=order_type,
        material_property=material_property,
        loss_rate=loss_rate,
        source_order_id=source_order_id,
        source_order_no=source_order_no
    ))
    
    results = [mrp_result]
    planned_orders = []
    
    if planned_order_qty > 0:
        planned_no = f"PO-{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
        planned_order = crud.create_planned_order(db, schemas.PlannedOrderCreate(
            account_set_id=account_set_id,
            planned_no=planned_no,
            material_id=material_id,
            planned_qty=planned_order_qty,
            planned_date=planned_release_date,
            order_type=order_type,
            source_type="MRP",
            source_id=source_order_id
        ))
        planned_orders.append(planned_order)
        
        boms = crud.get_boms(db, account_set_id=account_set_id, product_id=material_id)
        for bom in boms:
            today = datetime.date.today()
            if bom.effective_date and bom.effective_date > today:
                continue
            if bom.end_date and bom.end_date < today:
                continue
            
            for bom_item in bom.items:
                component_qty = float(bom_item.quantity) * planned_order_qty
                component_loss_rate = float(bom_item.scrap_rate or 0)
                component_gross = component_qty * (1 + component_loss_rate / 100)
                
                child_result = expand_bom(
                    db=db,
                    account_set_id=account_set_id,
                    mrp_run_no=mrp_run_no,
                    material_id=bom_item.material_id,
                    parent_material_id=material_id,
                    bom_level=bom_level + 1,
                    gross_requirement=component_gross,
                    planned_date=planned_release_date,
                    source_order_id=planned_order.id,
                    source_order_no=planned_order.planned_no,
                    processed_materials=processed_materials
                )
                
                results.extend(child_result["mrp_results"])
                planned_orders.extend(child_result["planned_orders"])
    
    return {"mrp_results": results, "planned_orders": planned_orders}

@router.get("/forecasts/", tags=["预测单"])
def get_forecasts(account_set_id: Optional[int] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    forecasts = crud.get_forecasts(db, account_set_id=account_set_id, status=status, skip=skip, limit=limit)
    return make_response(True, forecasts, "查询成功")

@router.get("/forecasts/{forecast_id}", tags=["预测单"])
def get_forecast(forecast_id: int, db: Session = Depends(get_db)):
    forecast = crud.get_forecast(db, forecast_id=forecast_id)
    if not forecast:
        return make_response(False, None, "预测单不存在", "40002")
    return make_response(True, forecast, "查询成功")

@router.post("/forecasts/", tags=["预测单"])
def create_forecast(forecast: schemas.ForecastCreate, db: Session = Depends(get_db)):
    forecast_no = f"FC-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    forecast_data = schemas.ForecastCreate(
        **forecast.dict(),
        forecast_no=forecast_no
    )
    created = crud.create_forecast(db, forecast_data)
    return make_response(True, created, "预测单创建成功")

@router.put("/forecasts/{forecast_id}/status", tags=["预测单"])
def update_forecast_status(forecast_id: int, status: str, db: Session = Depends(get_db)):
    updated = crud.update_forecast_status(db, forecast_id, status)
    if not updated:
        return make_response(False, None, "预测单不存在", "40002")
    return make_response(True, updated, "状态更新成功")

@router.put("/forecasts/{forecast_id}/approve", tags=["预测单"])
def approve_forecast(forecast_id: int, db: Session = Depends(get_db)):
    updated = crud.update_forecast_status(db, forecast_id, "APPROVED")
    if not updated:
        return make_response(False, None, "预测单不存在", "40002")
    return make_response(True, updated, "审批成功")

@router.delete("/forecasts/{forecast_id}", tags=["预测单"])
def delete_forecast(forecast_id: int, db: Session = Depends(get_db)):
    forecast = crud.get_forecast(db, forecast_id=forecast_id)
    if not forecast:
        return make_response(False, None, "预测单不存在", "40002")
    db.delete(forecast)
    db.commit()
    return make_response(True, None, "删除成功")

@router.get("/forecast-orders", tags=["预测单"])
def get_forecast_orders(account_set_id: Optional[int] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    forecasts = crud.get_forecasts(db, account_set_id=account_set_id, status=status, skip=skip, limit=limit)
    total = crud.get_forecasts_count(db, account_set_id=account_set_id, status=status)
    return make_response(True, {"items": forecasts, "total": total}, "查询成功")

@router.post("/mrp/run", tags=["MRP运算"])
def run_mrp(request: schemas.MRPRunRequest, db: Session = Depends(get_db)):
    try:
        account_set_id = request.account_set_id
        source_type = request.source_type
        source_id = request.source_id
        demand_date = request.demand_date or datetime.date.today()
        
        mrp_run_no = f"MRP-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        demand_items = []
        
        if source_type == "FORECAST" and source_id:
            forecast = crud.get_forecast(db, forecast_id=source_id)
            if forecast:
                demand_items.append({
                    "material_id": forecast.material_id,
                    "quantity": float(forecast.forecast_qty),
                    "source_type": "FORECAST",
                    "source_id": forecast.id,
                    "source_no": forecast.forecast_no,
                    "demand_date": forecast.forecast_date or demand_date
                })
        elif source_type == "SALES_ORDER" and source_id:
            sales_order = crud.get_sales_order(db, sales_order_id=source_id)
            if sales_order:
                for item in sales_order.items:
                    demand_items.append({
                        "material_id": item.material_id,
                        "quantity": float(item.quantity),
                        "source_type": "SALES_ORDER",
                        "source_id": sales_order.id,
                        "source_no": sales_order.so_no,
                        "demand_date": sales_order.delivery_date or demand_date
                    })
        else:
            forecasts = crud.get_forecasts(db, account_set_id=account_set_id, status="PENDING")
            for forecast in forecasts:
                demand_items.append({
                    "material_id": forecast.material_id,
                    "quantity": float(forecast.forecast_qty),
                    "source_type": "FORECAST",
                    "source_id": forecast.id,
                    "source_no": forecast.forecast_no,
                    "demand_date": forecast.forecast_date or demand_date
                })
            
            sales_orders = crud.get_sales_orders(db, account_set_id=account_set_id, status="PENDING_PRODUCTION")
            for order in sales_orders:
                for item in order.items:
                    demand_items.append({
                        "material_id": item.material_id,
                        "quantity": float(item.quantity),
                        "source_type": "SALES_ORDER",
                        "source_id": order.id,
                        "source_no": order.so_no,
                        "demand_date": order.delivery_date or demand_date
                    })
            
            sales_orders_approved = crud.get_sales_orders(db, account_set_id=account_set_id, status="APPROVED")
            for order in sales_orders_approved:
                for item in order.items:
                    demand_items.append({
                        "material_id": item.material_id,
                        "quantity": float(item.quantity),
                        "source_type": "SALES_ORDER",
                        "source_id": order.id,
                        "source_no": order.so_no,
                        "demand_date": order.delivery_date or demand_date
                    })
        
        all_results = []
        all_planned_orders = []
        processed_materials = set()
        
        for demand in demand_items:
            result = expand_bom(
                db=db,
                account_set_id=account_set_id,
                mrp_run_no=mrp_run_no,
                material_id=demand["material_id"],
                parent_material_id=None,
                bom_level=0,
                gross_requirement=demand["quantity"],
                planned_date=demand["demand_date"],
                source_order_id=demand["source_id"],
                source_order_no=demand["source_no"],
                processed_materials=processed_materials.copy()
            )
            
            all_results.extend(result["mrp_results"])
            all_planned_orders.extend(result["planned_orders"])
        
        purchase_orders = [po for po in all_planned_orders if po.order_type == "PURCHASE"]
        production_orders = [po for po in all_planned_orders if po.order_type == "PRODUCTION"]
        outsourcing_orders = [po for po in all_planned_orders if po.order_type == "OUTSOURCING"]
        
        purchase_requests_created = []
        outsourcing_requests_created = []
        
        for po in purchase_orders:
            material = crud.get_material(db, material_id=po.material_id)
            if material:
                request_no = f"PR-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                pr = models.PurchaseRequest(
                    account_set_id=account_set_id,
                    request_no=request_no,
                    material_id=po.material_id,
                    requested_qty=int(po.planned_qty),
                    required_date=po.planned_date,
                    supplier_id=material.default_supplier_id,
                    status="PENDING",
                    planned_order_id=po.id
                )
                db.add(pr)
                db.commit()
                db.refresh(pr)
                purchase_requests_created.append(pr)
        
        for po in outsourcing_orders:
            material = crud.get_material(db, material_id=po.material_id)
            if material:
                request_no = f"OR-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                or_req = models.OutsourcingRequest(
                    account_set_id=account_set_id,
                    request_no=request_no,
                    material_id=po.material_id,
                    requested_qty=int(po.planned_qty),
                    supplier_id=material.default_supplier_id,
                    planned_date=po.planned_date,
                    status="PENDING",
                    planned_order_id=po.id
                )
                db.add(or_req)
                db.commit()
                db.refresh(or_req)
                outsourcing_requests_created.append(or_req)
        
        return make_response(True, {
            "mrp_run_no": mrp_run_no,
            "run_time": datetime.datetime.now(),
            "total_demand_items": len(demand_items),
            "total_mrp_results": len(all_results),
            "total_planned_orders": len(all_planned_orders),
            "total_purchase_orders": len(purchase_orders),
            "total_production_orders": len(production_orders),
            "total_outsourcing_orders": len(outsourcing_orders),
            "total_purchase_requests": len(purchase_requests_created),
            "total_outsourcing_requests": len(outsourcing_requests_created),
            "mrp_results": all_results,
            "planned_orders": all_planned_orders,
            "purchase_orders": purchase_orders,
            "production_orders": production_orders,
            "outsourcing_orders": outsourcing_orders,
            "purchase_requests": purchase_requests_created,
            "outsourcing_requests": outsourcing_requests_created
        }, "MRP运算完成")
    except Exception as e:
        import traceback
        print(f"MRP运算错误: {str(e)}")
        print(traceback.format_exc())
        return make_response(False, None, f"MRP运算失败: {str(e)}", "50001")

@router.get("/mrp/results", tags=["MRP运算"])
def get_mrp_results(mrp_run_no: Optional[str] = None, account_set_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    results = crud.get_mrp_results(db, mrp_run_no=mrp_run_no, account_set_id=account_set_id, skip=skip, limit=limit)
    return make_response(True, results, "查询成功")

@router.get("/mrp/runs", tags=["MRP运算"])
def get_mrp_runs(account_set_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    runs = crud.get_mrp_runs(db, account_set_id=account_set_id, skip=skip, limit=limit)
    return make_response(True, runs, "查询成功")

@router.get("/planned_orders/", tags=["计划订单"])
def get_planned_orders(account_set_id: Optional[int] = None, order_type: Optional[str] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    orders = crud.get_planned_orders(db, account_set_id=account_set_id, order_type=order_type, status=status, skip=skip, limit=limit)
    return make_response(True, orders, "查询成功")

@router.get("/planned_orders/{planned_order_id}", tags=["计划订单"])
def get_planned_order(planned_order_id: int, db: Session = Depends(get_db)):
    order = crud.get_planned_order(db, planned_order_id=planned_order_id)
    if not order:
        return make_response(False, None, "计划订单不存在", "40002")
    return make_response(True, order, "查询成功")

@router.put("/planned_orders/{planned_order_id}/status", tags=["计划订单"])
def update_planned_order_status(planned_order_id: int, status: str, db: Session = Depends(get_db)):
    updated = crud.update_planned_order_status(db, planned_order_id, status)
    if not updated:
        return make_response(False, None, "计划订单不存在", "40002")
    return make_response(True, updated, "状态更新成功")

@router.delete("/planned_orders/{planned_order_id}", tags=["计划订单"])
def delete_planned_order(planned_order_id: int, db: Session = Depends(get_db)):
    success = crud.delete_planned_order(db, planned_order_id=planned_order_id)
    if not success:
        return make_response(False, None, "计划订单不存在", "40002")
    return make_response(True, None, "计划订单删除成功")

@router.post("/planned_orders/{planned_order_id}/release", tags=["计划订单"])
def release_planned_order(planned_order_id: int, db: Session = Depends(get_db)):
    planned_order = crud.get_planned_order(db, planned_order_id=planned_order_id)
    if not planned_order:
        return make_response(False, None, "计划订单不存在", "40002")
    
    created_doc = None
    created_doc_type = None
    
    if planned_order.order_type == "OUTSOURCING":
        osr_no = f"OSR-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        outsourcing_request = crud.create_outsourcing_request(db, schemas.OutsourcingRequestCreate(
            account_set_id=planned_order.account_set_id,
            request_no=osr_no,
            material_id=planned_order.material_id,
            requested_qty=planned_order.planned_qty,
            planned_date=planned_order.planned_date,
            planned_order_id=planned_order.id
        ))
        created_doc = outsourcing_request
        created_doc_type = "outsourcing_request"
    elif planned_order.order_type == "PRODUCTION":
        wo_no = f"WO-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        work_order = crud.create_production_workorder(db, schemas.ProductionWorkOrderCreate(
            account_set_id=planned_order.account_set_id,
            work_order_no=wo_no,
            product_id=planned_order.material_id,
            planned_qty=int(planned_order.planned_qty),
            start_date=planned_order.planned_date
        ))
        created_doc = work_order
        created_doc_type = "production_workorder"
    
    planned_order.status = "RELEASED"
    db.commit()
    
    if created_doc:
        return make_response(True, {
            "planned_order": planned_order,
            created_doc_type: created_doc
        }, f"计划订单已下达，已生成{created_doc_type}")
    
    return make_response(True, planned_order, "计划订单已下达")

@router.get("/outsourcing/requests/", tags=["委外加工"])
def get_outsourcing_requests(account_set_id: Optional[int] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    requests = crud.get_outsourcing_requests(db, account_set_id=account_set_id, status=status, skip=skip, limit=limit)
    return make_response(True, requests, "查询成功")

@router.post("/outsourcing/requests/", tags=["委外加工"])
def create_outsourcing_request(request: schemas.OutsourcingRequestCreate, db: Session = Depends(get_db)):
    request_no = f"OSR-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    request_data = schemas.OutsourcingRequestCreate(
        **request.dict(),
        request_no=request_no
    )
    created = crud.create_outsourcing_request(db, request_data)
    return make_response(True, created, "委外申请单创建成功")

@router.put("/outsourcing/requests/{request_id}/approve", tags=["委外加工"])
def approve_outsourcing_request(request_id: int, db: Session = Depends(get_db)):
    request = crud.get_outsourcing_request(db, request_id=request_id)
    if not request:
        return make_response(False, None, "委外申请单不存在", "40002")
    
    request.status = "APPROVED"
    db.commit()
    
    if request.supplier_id:
        order_no = f"OSO-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        order = crud.create_outsourcing_order(db, schemas.OutsourcingOrderCreate(
            account_set_id=request.account_set_id,
            order_no=order_no,
            request_id=request.id,
            supplier_id=request.supplier_id,
            material_id=request.material_id,
            ordered_qty=request.requested_qty,
            planned_date=request.planned_date
        ))
        return make_response(True, {"request": request, "order": order}, "委外申请已审批，已生成委外订单")
    
    return make_response(True, request, "委外申请已审批")

@router.get("/outsourcing/orders/", tags=["委外加工"])
def get_outsourcing_orders(account_set_id: Optional[int] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    orders = crud.get_outsourcing_orders(db, account_set_id=account_set_id, status=status, skip=skip, limit=limit)
    return make_response(True, orders, "查询成功")

@router.post("/outsourcing/orders/", tags=["委外加工"])
def create_outsourcing_order(order: schemas.OutsourcingOrderCreate, db: Session = Depends(get_db)):
    order_no = f"OSO-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    order_data = schemas.OutsourcingOrderCreate(
        **order.dict(),
        order_no=order_no
    )
    created = crud.create_outsourcing_order(db, order_data)
    
    if order.request_id:
        crud.update_outsourcing_request_status(db, order.request_id, "ORDERED")
    
    return make_response(True, created, "委外订单创建成功")

@router.post("/outsourcing/issues/", tags=["委外加工"])
def create_outsourcing_issue(issue: schemas.OutsourcingIssueCreate, db: Session = Depends(get_db)):
    issue_no = f"OSI-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    items_data = []
    for item in issue.items:
        inventory = crud.get_batch_inventories(db, batch_no=item.batch_no, material_id=item.material_id).first()
        if inventory and inventory.quantity >= item.quantity:
            crud.update_batch_inventory(db, inventory.id, inventory.quantity - item.quantity)
            items_data.append({
                **item.dict(),
                "unit_cost": inventory.unit_cost
            })
    
    issue_data = schemas.OutsourcingIssueCreate(
        **issue.dict(),
        issue_no=issue_no,
        items=items_data
    )
    
    created = crud.create_outsourcing_issue(db, issue_data)
    
    order = crud.get_outsourcing_order(db, order_id=issue.outsourcing_order_id)
    if order:
        order.status = "ISSUED"
        db.commit()
    
    return make_response(True, created, "委外投料单创建成功")

@router.post("/outsourcing/replenishes/", tags=["委外加工"])
def create_outsourcing_replenish(replenish: schemas.OutsourcingReplenishCreate, db: Session = Depends(get_db)):
    replenish_no = f"OSR-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    items_data = []
    for item in replenish.items:
        inventory = crud.get_batch_inventories(db, batch_no=item.batch_no, material_id=item.material_id).first()
        if inventory and inventory.quantity >= item.quantity:
            crud.update_batch_inventory(db, inventory.id, inventory.quantity - item.quantity)
            items_data.append({
                **item.dict(),
                "unit_cost": inventory.unit_cost
            })
    
    replenish_data = schemas.OutsourcingReplenishCreate(
        **replenish.dict(),
        replenish_no=replenish_no,
        items=items_data
    )
    
    created = crud.create_outsourcing_replenish(db, replenish_data)
    return make_response(True, created, "委外补发单创建成功")

@router.post("/outsourcing/returns/", tags=["委外加工"])
def create_outsourcing_return(return_order: schemas.OutsourcingReturnCreate, db: Session = Depends(get_db)):
    return_no = f"OSRT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    items_data = []
    for item in return_order.items:
        items_data.append({
            **item.dict()
        })
    
    return_data = schemas.OutsourcingReturnCreate(
        **return_order.dict(),
        return_no=return_no,
        items=items_data
    )
    
    created = crud.create_outsourcing_return(db, return_data)
    
    for item in created.items:
        crud.create_batch_inventory(db, schemas.BatchInventoryCreate(
            account_set_id=created.account_set_id,
            material_id=item.material_id,
            batch_no=item.batch_no or f"RTN-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
            location_code=item.location_code or "RTN",
            quantity=item.quantity,
            unit_cost=item.unit_cost or 0,
            quality_status="FROZEN"
        ))
    
    return make_response(True, created, "委外退料单创建成功")