from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime

from ..database import get_db
from .. import crud, schemas, models
from ..app import make_response

router = APIRouter()

@router.get("/customers/", response_model=List[schemas.Customer])
def read_customers(account_set_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    customers = crud.get_customers(db, account_set_id=account_set_id, skip=skip, limit=limit)
    return customers

@router.get("/customers/{customer_id}", response_model=schemas.Customer)
def read_customer(customer_id: int, db: Session = Depends(get_db)):
    db_customer = crud.get_customer(db, customer_id=customer_id)
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db_customer

@router.post("/customers/", response_model=schemas.Customer)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    return crud.create_customer(db=db, customer=customer)

@router.put("/customers/{customer_id}", response_model=schemas.Customer)
def update_customer(customer_id: int, customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    db_customer = crud.update_customer(db, customer_id=customer_id, customer=customer)
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db_customer

@router.delete("/customers/{customer_id}")
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    success = crud.delete_customer(db, customer_id=customer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Customer deleted successfully"}

@router.get("/price_lists/", response_model=List[schemas.PriceList])
def read_price_lists(account_set_id: Optional[int] = None, material_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    price_lists = crud.get_price_lists(db, account_set_id=account_set_id, material_id=material_id, skip=skip, limit=limit)
    return price_lists

@router.post("/price_lists/", response_model=schemas.PriceList)
def create_price_list(price_list: schemas.PriceListCreate, db: Session = Depends(get_db)):
    return crud.create_price_list(db=db, price_list=price_list)

@router.get("/sales_orders/", response_model=List[schemas.SalesOrder])
def read_sales_orders(account_set_id: Optional[int] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    sales_orders = crud.get_sales_orders(db, account_set_id=account_set_id, status=status, skip=skip, limit=limit)
    return sales_orders

@router.get("/sales_orders/{sales_order_id}", response_model=schemas.SalesOrder)
def read_sales_order(sales_order_id: int, db: Session = Depends(get_db)):
    db_sales_order = crud.get_sales_order(db, sales_order_id=sales_order_id)
    if db_sales_order is None:
        raise HTTPException(status_code=404, detail="Sales order not found")
    return db_sales_order

@router.post("/sales_orders/", response_model=schemas.SalesOrder)
def create_sales_order(sales_order: schemas.SalesOrderCreate, db: Session = Depends(get_db)):
    if sales_order.customer_id:
        customer = crud.get_customer(db, customer_id=sales_order.customer_id)
        if customer:
            total_amount = sum(item.quantity * item.unit_price for item in sales_order.items)
            if customer.credit_used + total_amount > customer.credit_limit and customer.credit_limit > 0:
                sales_order.credit_check_passed = False
    return crud.create_sales_order(db=db, sales_order=sales_order)

@router.put("/sales_orders/{sales_order_id}", response_model=schemas.SalesOrder)
def update_sales_order(sales_order_id: int, sales_order: schemas.SalesOrderCreate, db: Session = Depends(get_db)):
    db_sales_order = crud.update_sales_order(db, sales_order_id=sales_order_id, sales_order=sales_order)
    if db_sales_order is None:
        raise HTTPException(status_code=404, detail="Sales order not found")
    return db_sales_order

@router.delete("/sales_orders/{sales_order_id}")
def delete_sales_order(sales_order_id: int, db: Session = Depends(get_db)):
    success = crud.delete_sales_order(db, sales_order_id=sales_order_id)
    if not success:
        raise HTTPException(status_code=404, detail="Sales order not found")
    return {"message": "Sales order deleted successfully"}

@router.post("/sales_orders/{sales_order_id}/approve")
def approve_sales_order(sales_order_id: int, db: Session = Depends(get_db)):
    db_sales_order = crud.get_sales_order(db, sales_order_id=sales_order_id)
    if db_sales_order is None:
        raise HTTPException(status_code=404, detail="Sales order not found")
    if not db_sales_order.credit_check_passed:
        raise HTTPException(status_code=400, detail="Credit check failed")
    
    for item in db_sales_order.items:
        inventories = crud.get_batch_inventories(db, account_set_id=db_sales_order.account_set_id, material_id=item.material_id)
        total_available = sum(inv.quantity for inv in inventories if inv.quality_status == "AVAILABLE")
        if total_available < item.quantity:
            db_sales_order.status = "PENDING_PRODUCTION"
            db.commit()
            return make_response(False, db_sales_order, "库存不足，已转计划管理", "40003")
    
    db_sales_order.status = "APPROVED"
    db.commit()
    db.refresh(db_sales_order)
    return db_sales_order

@router.post("/sales_orders/{sales_order_id}/create_delivery")
def create_delivery_note_from_sales(sales_order_id: int, db: Session = Depends(get_db)):
    sales_order = crud.get_sales_order(db, sales_order_id=sales_order_id)
    if not sales_order:
        return make_response(False, None, "销售订单不存在", "40002")
    
    if sales_order.status != "APPROVED":
        return make_response(False, None, "销售订单未审批通过", "40003")
    
    delivery_no = f"DN-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    items = []
    for item in sales_order.items:
        inventories = crud.get_batch_inventories(db, account_set_id=sales_order.account_set_id, material_id=item.material_id)
        available_inventories = sorted([inv for inv in inventories if inv.quality_status == "AVAILABLE"], key=lambda x: x.inbound_date or datetime.date.min)
        
        remaining_qty = item.quantity
        for inv in available_inventories:
            if remaining_qty <= 0:
                break
            use_qty = min(inv.quantity, remaining_qty)
            items.append({
                "material_id": item.material_id,
                "batch_no": inv.batch_no,
                "quantity": use_qty,
                "shipped_qty": 0,
                "unit_price": item.unit_price
            })
            remaining_qty -= use_qty
    
    delivery_note = crud.create_delivery_note(db, schemas.DeliveryNoteCreate(
        account_set_id=sales_order.account_set_id,
        delivery_no=delivery_no,
        sales_order_id=sales_order_id,
        customer_id=sales_order.customer_id,
        delivery_date=datetime.date.today(),
        status="PENDING",
        items=items
    ))
    
    sales_order.status = "DELIVERY_CREATED"
    db.commit()
    
    return make_response(True, delivery_note, "发货通知单创建成功")

@router.get("/delivery_notes/", tags=["发货管理"])
def get_delivery_notes(account_set_id: Optional[int] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    notes = crud.get_delivery_notes(db, account_set_id=account_set_id, status=status, skip=skip, limit=limit)
    return make_response(True, notes, "查询成功")

@router.get("/delivery_notes/{delivery_note_id}", tags=["发货管理"])
def get_delivery_note(delivery_note_id: int, db: Session = Depends(get_db)):
    note = crud.get_delivery_note(db, delivery_note_id=delivery_note_id)
    if not note:
        return make_response(False, None, "发货通知单不存在", "40002")
    return make_response(True, note, "查询成功")

@router.post("/delivery_notes/", tags=["发货管理"])
def create_delivery_note(delivery_note: schemas.DeliveryNoteCreate, db: Session = Depends(get_db)):
    delivery_no = f"DN-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    note_data = schemas.DeliveryNoteCreate(
        **delivery_note.dict(),
        delivery_no=delivery_no
    )
    created = crud.create_delivery_note(db, note_data)
    return make_response(True, created, "发货通知单创建成功")

@router.put("/delivery_notes/{delivery_note_id}/confirm", tags=["发货管理"])
def confirm_delivery_note(delivery_note_id: int, db: Session = Depends(get_db)):
    note = crud.get_delivery_note(db, delivery_note_id=delivery_note_id)
    if not note:
        return make_response(False, None, "发货通知单不存在", "40002")
    
    note.status = "CONFIRMED"
    db.commit()
    db.refresh(note)
    
    outbound_no = f"SO-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    items = []
    for item in note.items:
        inventory = crud.get_batch_inventories(db, batch_no=item.batch_no, material_id=item.material_id).first()
        if inventory:
            items.append({
                "material_id": item.material_id,
                "batch_no": item.batch_no,
                "location_code": inventory.location_code,
                "quantity": item.quantity,
                "unit_cost": inventory.unit_cost,
                "unit_price": item.unit_price,
                "total_amount": item.quantity * (item.unit_price or 0)
            })
            crud.update_batch_inventory(db, inventory.id, inventory.quantity - item.quantity)
    
    sales_outbound = crud.create_sales_outbound(db, schemas.SalesOutboundCreate(
        account_set_id=note.account_set_id,
        outbound_no=outbound_no,
        delivery_note_id=delivery_note_id,
        sales_order_id=note.sales_order_id,
        customer_id=note.customer_id,
        outbound_date=datetime.date.today(),
        status="PENDING",
        is_credit=True,
        items=items
    ))
    
    return make_response(True, {"delivery_note": note, "sales_outbound": sales_outbound}, "发货确认完成，已生成销售出库单")

@router.get("/sales_outbound/", tags=["销售出库"])
def get_sales_outbounds(account_set_id: Optional[int] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    outbounds = crud.get_sales_outbounds(db, account_set_id=account_set_id, status=status, skip=skip, limit=limit)
    return make_response(True, outbounds, "查询成功")

@router.get("/sales_outbound/{outbound_id}", tags=["销售出库"])
def get_sales_outbound(outbound_id: int, db: Session = Depends(get_db)):
    outbound = crud.get_sales_outbound(db, outbound_id=outbound_id)
    if not outbound:
        return make_response(False, None, "销售出库单不存在", "40002")
    return make_response(True, outbound, "查询成功")

@router.post("/sales_outbound/", tags=["销售出库"])
def create_sales_outbound(outbound: schemas.SalesOutboundCreate, db: Session = Depends(get_db)):
    outbound_no = f"SO-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    outbound_data = schemas.SalesOutboundCreate(
        **outbound.dict(),
        outbound_no=outbound_no
    )
    created = crud.create_sales_outbound(db, outbound_data)
    return make_response(True, created, "销售出库单创建成功")

@router.put("/sales_outbound/{outbound_id}/complete", tags=["销售出库"])
def complete_sales_outbound(outbound_id: int, db: Session = Depends(get_db)):
    outbound = crud.get_sales_outbound(db, outbound_id=outbound_id)
    if not outbound:
        return make_response(False, None, "销售出库单不存在", "40002")
    
    outbound.status = "COMPLETED"
    db.commit()
    db.refresh(outbound)
    
    if outbound.is_credit and outbound.customer_id:
        customer = crud.get_customer(db, customer_id=outbound.customer_id)
        if customer:
            total_amount = sum(item.total_amount or 0 for item in outbound.items)
            customer.credit_used += total_amount
            db.commit()
    
    return make_response(True, outbound, "销售出库完成")