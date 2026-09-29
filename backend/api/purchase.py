from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, schemas, models
from ..database import get_db
from ..app import make_response

router = APIRouter()

@router.post("/orders", tags=["采购管理"])
def create_purchase_order(order: schemas.PurchaseOrderCreate, db: Session = Depends(get_db)):
    db_order = crud.get_purchase_order_by_no(db, po_no=order.po_no)
    if db_order:
        return make_response(False, None, "采购订单号已存在", "40003")
    
    if order.template_id:
        template = crud.get_purchase_order_template(db, template_id=order.template_id)
        if template:
            order.supplier_id = template.supplier_id or order.supplier_id
            order.tax_rate = template.tax_rate
    
    items_data = order.dict().pop('items', [])
    db_order = models.PurchaseOrder(**order.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    total_amount = 0
    for item_data in items_data:
        if item_data.get('is_gift', False):
            item_data['unit_price'] = 0
        item_data['purchase_order_id'] = db_order.id
        db_item = models.PurchaseOrderItem(**item_data)
        db.add(db_item)
        total_amount += item_data.get('quantity', 0) * (item_data.get('special_price') or item_data.get('unit_price', 0))
    
    if order.discount_amount > 0 and len(items_data) > 0:
        discount_per_item = order.discount_amount / len(items_data)
        for item in db_order.items:
            item.allocated_discount = discount_per_item
    
    db.commit()
    db.refresh(db_order)
    
    if order.is_emergency:
        db_order.approval_status = schemas.ApprovalStatus.WAITING_SUPPLEMENT
    
    return make_response(True, db_order, "创建成功")

@router.get("/orders", tags=["采购管理"])
def list_purchase_orders(account_set_id: Optional[int] = None, skip: int = 0, limit: int = 100, status: str = None, db: Session = Depends(get_db)):
    orders = crud.get_purchase_orders(db, account_set_id=account_set_id, skip=skip, limit=limit, status=status)
    total = crud.get_purchase_orders_count(db)
    return make_response(True, {"items": orders, "total": total}, "查询成功")

@router.get("/orders/{order_id}", tags=["采购管理"])
def get_purchase_order(order_id: int, db: Session = Depends(get_db)):
    db_order = crud.get_purchase_order(db, order_id=order_id)
    if db_order is None:
        return make_response(False, None, "采购订单不存在", "40002")
    return make_response(True, db_order, "查询成功")

@router.post("/orders/{order_id}/approve", tags=["采购管理"])
def approve_purchase_order(order_id: int, db: Session = Depends(get_db)):
    db_order = crud.get_purchase_order(db, order_id=order_id)
    if db_order is None:
        return make_response(False, None, "采购订单不存在", "40002")
    
    db_order.approval_status = schemas.ApprovalStatus.APPROVED
    db_order.status = "APPROVED"
    db.commit()
    db.refresh(db_order)
    return make_response(True, db_order, "审批通过")

@router.post("/orders/{order_id}/supplement", tags=["采购管理"])
def supplement_purchase_order(order_id: int, db: Session = Depends(get_db)):
    db_order = crud.get_purchase_order(db, order_id=order_id)
    if db_order is None:
        return make_response(False, None, "采购订单不存在", "40002")
    
    if db_order.approval_status != schemas.ApprovalStatus.WAITING_SUPPLEMENT:
        return make_response(False, None, "订单不需要补批", "40003")
    
    db_order.approval_status = schemas.ApprovalStatus.APPROVED
    db_order.need_supplement = False
    db.commit()
    db.refresh(db_order)
    return make_response(True, db_order, "补批完成")

@router.post("/suppliers", tags=["采购管理"])
def create_supplier(supplier: schemas.SupplierCreate, db: Session = Depends(get_db)):
    created = crud.create_supplier(db, supplier)
    return make_response(True, created, "创建成功")

@router.get("/suppliers", tags=["采购管理"])
def list_suppliers(account_set_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    suppliers = crud.get_suppliers(db, skip=skip, limit=limit)
    total = crud.get_suppliers_count(db)
    return make_response(True, {"items": suppliers, "total": total}, "查询成功")

@router.get("/suppliers/{supplier_id}", tags=["采购管理"])
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    db_supplier = crud.get_supplier(db, supplier_id=supplier_id)
    if db_supplier is None:
        return make_response(False, None, "供应商不存在", "40002")
    return make_response(True, db_supplier, "查询成功")

@router.get("/templates", tags=["采购管理"])
def list_templates(account_set_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    templates = crud.get_purchase_order_templates(db, account_set_id=account_set_id, skip=skip, limit=limit)
    return make_response(True, {"items": templates}, "查询成功")

@router.post("/templates", tags=["采购管理"])
def create_template(template: schemas.PurchaseOrderTemplateCreate, db: Session = Depends(get_db)):
    created = crud.create_purchase_order_template(db, template)
    return make_response(True, created, "创建成功")

@router.post("/templates/{template_id}/generate", tags=["采购管理"])
def generate_order_from_template(template_id: int, po_no: str, db: Session = Depends(get_db)):
    template = crud.get_purchase_order_template(db, template_id=template_id)
    if not template:
        return make_response(False, None, "模板不存在", "40002")
    
    items_data = []
    for item in template.items:
        items_data.append({
            "material_id": item.material_id,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "is_gift": item.is_gift
        })
    
    order_create = schemas.PurchaseOrderCreate(
        po_no=po_no,
        supplier_id=template.supplier_id,
        template_id=template_id,
        tax_rate=template.tax_rate,
        account_set_id=template.account_set_id,
        items=items_data
    )
    
    return create_purchase_order(order_create, db)