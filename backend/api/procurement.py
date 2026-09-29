from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime

from ..database import get_db
from .. import crud, schemas, models
from ..app import make_response

router = APIRouter()

@router.post("/purchase-requests", tags=["采购管理"])
def create_purchase_request(request: schemas.PurchaseRequestCreate, db: Session = Depends(get_db)):
    db_request = crud.get_purchase_request_by_no(db, request_no=request.request_no) if hasattr(request, 'request_no') else None
    if db_request:
        return make_response(False, None, "采购申请单号已存在", "40003")
    
    request_no = f"PR-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    db_request = models.PurchaseRequest(
        account_set_id=request.account_set_id,
        request_no=request_no,
        material_id=request.material_id,
        requested_qty=request.requested_qty,
        required_date=request.required_date,
        supplier_id=request.supplier_id,
        status=request.status,
        planned_order_id=request.planned_order_id
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    
    return make_response(True, db_request, "创建成功")

@router.get("/purchase-requests", tags=["采购管理"])
def get_purchase_requests(account_set_id: Optional[int] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    requests = crud.get_purchase_requests(db, account_set_id=account_set_id, status=status, skip=skip, limit=limit)
    total = crud.get_purchase_requests_count(db, account_set_id=account_set_id, status=status)
    return make_response(True, {"items": requests, "total": total}, "查询成功")

@router.get("/purchase-requests/{request_id}", tags=["采购管理"])
def get_purchase_request(request_id: int, db: Session = Depends(get_db)):
    db_request = crud.get_purchase_request(db, request_id=request_id)
    if db_request is None:
        return make_response(False, None, "采购申请单不存在", "40002")
    return make_response(True, db_request, "查询成功")

@router.put("/purchase-requests/{request_id}/approve", tags=["采购管理"])
def approve_purchase_request(request_id: int, db: Session = Depends(get_db)):
    db_request = crud.get_purchase_request(db, request_id=request_id)
    if db_request is None:
        return make_response(False, None, "采购申请单不存在", "40002")
    
    db_request.status = "APPROVED"
    db.commit()
    db.refresh(db_request)
    
    return make_response(True, db_request, "审批通过")

@router.get("/purchase-orders", tags=["采购管理"])
def get_purchase_orders(account_set_id: Optional[int] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    orders = crud.get_purchase_orders(db, account_set_id=account_set_id, status=status, skip=skip, limit=limit)
    total = crud.get_purchase_orders_count(db, account_set_id=account_set_id, status=status)
    return make_response(True, {"items": orders, "total": total}, "查询成功")

@router.get("/purchase-orders/{order_id}", tags=["采购管理"])
def get_purchase_order(order_id: int, db: Session = Depends(get_db)):
    db_order = crud.get_purchase_order(db, order_id=order_id)
    if db_order is None:
        return make_response(False, None, "采购订单不存在", "40002")
    return make_response(True, db_order, "查询成功")

@router.post("/purchase-orders", tags=["采购管理"])
def create_purchase_order(order: schemas.PurchaseOrderCreate, db: Session = Depends(get_db)):
    db_order = crud.get_purchase_order_by_no(db, po_no=order.po_no)
    if db_order:
        return make_response(False, None, "采购订单号已存在", "40003")
    
    created = crud.create_purchase_order_with_items(db, order)
    return make_response(True, created, "创建成功")

@router.put("/purchase-orders/{order_id}/status", tags=["采购管理"])
def update_purchase_order_status(order_id: int, status: str, db: Session = Depends(get_db)):
    db_order = crud.get_purchase_order(db, order_id=order_id)
    if db_order is None:
        return make_response(False, None, "采购订单不存在", "40002")
    
    db_order.status = status
    db.commit()
    db.refresh(db_order)
    
    return make_response(True, db_order, "状态更新成功")

@router.get("/pre-receipts", tags=["采购管理"])
def get_pre_receipts(account_set_id: Optional[int] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    receipts = crud.get_pre_receipts(db, account_set_id=account_set_id, status=status, skip=skip, limit=limit)
    total = crud.get_pre_receipts_count(db, account_set_id=account_set_id, status=status)
    return make_response(True, {"items": receipts, "total": total}, "查询成功")

@router.get("/pre-receipts/{receipt_id}", tags=["采购管理"])
def get_pre_receipt(receipt_id: int, db: Session = Depends(get_db)):
    db_receipt = crud.get_pre_receipt(db, pre_receipt_id=receipt_id)
    if db_receipt is None:
        return make_response(False, None, "来料通知单不存在", "40002")
    return make_response(True, db_receipt, "查询成功")

@router.post("/pre-receipts", tags=["采购管理"])
def create_pre_receipt(receipt: schemas.PreReceiptCreate, db: Session = Depends(get_db)):
    receipt_no = f"PRC-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    receipt_data = schemas.PreReceiptCreate(
        **receipt.dict(),
        pre_receipt_no=receipt_no
    )
    created = crud.create_pre_receipt(db, receipt_data)
    return make_response(True, created, "创建成功")

@router.put("/pre-receipts/{receipt_id}/confirm", tags=["采购管理"])
def confirm_pre_receipt(receipt_id: int, db: Session = Depends(get_db)):
    db_receipt = crud.get_pre_receipt(db, pre_receipt_id=receipt_id)
    if db_receipt is None:
        return make_response(False, None, "来料通知单不存在", "40002")
    
    db_receipt.status = "CONFIRMED"
    db_receipt.actual_arrival_date = datetime.date.today()
    db.commit()
    db.refresh(db_receipt)
    
    return make_response(True, db_receipt, "确认到货")

@router.get("/inbound-orders", tags=["采购管理"])
def get_inbound_orders(account_set_id: Optional[int] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    orders = crud.get_inbound_orders(db, account_set_id=account_set_id, status=status, skip=skip, limit=limit)
    total = crud.get_inbound_orders_count(db, account_set_id=account_set_id, status=status)
    return make_response(True, {"items": orders, "total": total}, "查询成功")

@router.get("/inbound-orders/{order_id}", tags=["采购管理"])
def get_inbound_order(order_id: int, db: Session = Depends(get_db)):
    db_order = crud.get_inbound_order(db, inbound_id=order_id)
    if db_order is None:
        return make_response(False, None, "采购入库单不存在", "40002")
    return make_response(True, db_order, "查询成功")

@router.post("/inbound-orders", tags=["采购管理"])
def create_inbound_order(order: schemas.InboundOrderCreate, db: Session = Depends(get_db)):
    inbound_no = f"POI-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    order_data = schemas.InboundOrderCreate(
        **order.dict(),
        inbound_no=inbound_no
    )
    created = crud.create_inbound_order(db, order_data)
    
    for item in created.items:
        crud.create_batch_inventory(db, schemas.BatchInventoryCreate(
            account_set_id=created.account_set_id,
            material_id=item.material_id,
            batch_no=item.batch_no,
            location_code=item.location_code,
            quantity=item.quantity,
            unit_cost=item.unit_price,
            expiry_date=item.expiry_date,
            quality_status="PENDING"
        ))
    
    return make_response(True, created, "创建成功")

@router.put("/inbound-orders/{order_id}/complete", tags=["采购管理"])
def complete_inbound_order(order_id: int, quality_status: str = "PASS", db: Session = Depends(get_db)):
    db_order = crud.get_inbound_order(db, inbound_id=order_id)
    if db_order is None:
        return make_response(False, None, "采购入库单不存在", "40002")
    
    db_order.status = "COMPLETED"
    db_order.quality_status = quality_status
    db.commit()
    db.refresh(db_order)
    
    if quality_status == "PASS":
        for item in db_order.items:
            inventories = crud.get_batch_inventories(db, material_id=item.material_id, batch_no=item.batch_no)
            for inv in inventories:
                if inv.location_code == item.location_code:
                    crud.update_batch_inventory(db, inv.id, inv.quantity + item.quantity)
    
    return make_response(True, db_order, "入库完成")

@router.post("/outsourcing-requests", tags=["委外加工"])
def create_outsourcing_request(request: schemas.OutsourcingRequestCreate, db: Session = Depends(get_db)):
    request_no = f"OR-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    db_request = models.OutsourcingRequest(
        account_set_id=request.account_set_id,
        request_no=request_no,
        material_id=request.material_id,
        requested_qty=request.requested_qty,
        supplier_id=request.supplier_id,
        planned_date=request.planned_date,
        status=request.status,
        planned_order_id=request.planned_order_id
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    
    return make_response(True, db_request, "创建成功")

@router.get("/outsourcing-requests", tags=["委外加工"])
def get_outsourcing_requests(account_set_id: Optional[int] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    requests = crud.get_outsourcing_requests(db, account_set_id=account_set_id, status=status, skip=skip, limit=limit)
    total = crud.get_outsourcing_requests_count(db, account_set_id=account_set_id, status=status)
    return make_response(True, {"items": requests, "total": total}, "查询成功")

@router.get("/outsourcing-requests/{request_id}", tags=["委外加工"])
def get_outsourcing_request(request_id: int, db: Session = Depends(get_db)):
    db_request = crud.get_outsourcing_request(db, request_id=request_id)
    if db_request is None:
        return make_response(False, None, "委外申请单不存在", "40002")
    return make_response(True, db_request, "查询成功")

@router.put("/outsourcing-requests/{request_id}/approve", tags=["委外加工"])
def approve_outsourcing_request(request_id: int, db: Session = Depends(get_db)):
    db_request = crud.get_outsourcing_request(db, request_id=request_id)
    if db_request is None:
        return make_response(False, None, "委外申请单不存在", "40002")
    
    db_request.status = "APPROVED"
    db.commit()
    db.refresh(db_request)
    
    return make_response(True, db_request, "审批通过")

@router.post("/outsourcing-orders", tags=["委外加工"])
def create_outsourcing_order(order: schemas.OutsourcingOrderCreate, db: Session = Depends(get_db)):
    order_no = f"OO-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    db_order = models.OutsourcingOrder(
        account_set_id=order.account_set_id,
        order_no=order_no,
        request_id=order.request_id,
        supplier_id=order.supplier_id,
        material_id=order.material_id,
        ordered_qty=order.ordered_qty,
        unit_price=order.unit_price,
        planned_date=order.planned_date,
        status=order.status
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    return make_response(True, db_order, "创建成功")

@router.get("/outsourcing-orders", tags=["委外加工"])
def get_outsourcing_orders(account_set_id: Optional[int] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    orders = crud.get_outsourcing_orders(db, account_set_id=account_set_id, status=status, skip=skip, limit=limit)
    total = crud.get_outsourcing_orders_count(db, account_set_id=account_set_id, status=status)
    return make_response(True, {"items": orders, "total": total}, "查询成功")

@router.post("/outsourcing-issues", tags=["委外加工"])
def create_outsourcing_issue(issue: schemas.OutsourcingIssueCreate, db: Session = Depends(get_db)):
    issue_no = f"OI-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    db_issue = models.OutsourcingIssue(
        account_set_id=issue.account_set_id,
        issue_no=issue_no,
        outsourcing_order_id=issue.outsourcing_order_id,
        issue_date=issue.issue_date,
        status=issue.status,
        operator=issue.operator
    )
    db.add(db_issue)
    db.commit()
    db.refresh(db_issue)
    
    for item_data in issue.items:
        item_data['issue_id'] = db_issue.id
        db_item = models.OutsourcingIssueItem(**item_data)
        db.add(db_item)
    
    db.commit()
    db.refresh(db_issue)
    
    return make_response(True, db_issue, "创建成功")

@router.get("/outsourcing-issues", tags=["委外加工"])
def get_outsourcing_issues(account_set_id: Optional[int] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    issues = crud.get_outsourcing_issues(db, account_set_id=account_set_id, status=status, skip=skip, limit=limit)
    total = crud.get_outsourcing_issues_count(db, account_set_id=account_set_id, status=status)
    return make_response(True, {"items": issues, "total": total}, "查询成功")

@router.post("/outsourcing-replenishes", tags=["委外加工"])
def create_outsourcing_replenish(replenish: schemas.OutsourcingReplenishCreate, db: Session = Depends(get_db)):
    replenish_no = f"ORP-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    db_replenish = models.OutsourcingReplenish(
        account_set_id=replenish.account_set_id,
        replenish_no=replenish_no,
        outsourcing_order_id=replenish.outsourcing_order_id,
        issue_id=replenish.issue_id,
        replenish_date=replenish.replenish_date,
        status=replenish.status,
        operator=replenish.operator
    )
    db.add(db_replenish)
    db.commit()
    db.refresh(db_replenish)
    
    for item_data in replenish.items:
        item_data['replenish_id'] = db_replenish.id
        db_item = models.OutsourcingReplenishItem(**item_data)
        db.add(db_item)
    
    db.commit()
    db.refresh(db_replenish)
    
    return make_response(True, db_replenish, "创建成功")

@router.post("/outsourcing-returns", tags=["委外加工"])
def create_outsourcing_return(return_order: schemas.OutsourcingReturnCreate, db: Session = Depends(get_db)):
    return_no = f"ORT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    db_return = models.OutsourcingReturn(
        account_set_id=return_order.account_set_id,
        return_no=return_no,
        outsourcing_order_id=return_order.outsourcing_order_id,
        issue_id=return_order.issue_id,
        return_date=return_order.return_date,
        status=return_order.status,
        return_reason=return_order.return_reason,
        operator=return_order.operator
    )
    db.add(db_return)
    db.commit()
    db.refresh(db_return)
    
    for item_data in return_order.items:
        item_data['return_id'] = db_return.id
        db_item = models.OutsourcingReturnItem(**item_data)
        db.add(db_item)
    
    db.commit()
    db.refresh(db_return)
    
    return make_response(True, db_return, "创建成功")

@router.post("/outsourcing-receives", tags=["委外加工"])
def create_outsourcing_receive(receive: schemas.OutsourcingReceiveCreate, db: Session = Depends(get_db)):
    receive_no = f"ORC-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    db_receive = models.OutsourcingReceive(
        account_set_id=receive.account_set_id,
        receive_no=receive_no,
        outsourcing_order_id=receive.outsourcing_order_id,
        expected_arrival_date=receive.expected_arrival_date,
        actual_arrival_date=receive.actual_arrival_date,
        status=receive.status
    )
    db.add(db_receive)
    db.commit()
    db.refresh(db_receive)
    
    for item_data in receive.items:
        item_data['receive_id'] = db_receive.id
        db_item = models.OutsourcingReceiveItem(**item_data)
        db.add(db_item)
    
    db.commit()
    db.refresh(db_receive)
    
    return make_response(True, db_receive, "创建成功")

@router.get("/outsourcing-receives", tags=["委外加工"])
def get_outsourcing_receives(account_set_id: Optional[int] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    receives = crud.get_outsourcing_receives(db, account_set_id=account_set_id, status=status, skip=skip, limit=limit)
    total = crud.get_outsourcing_receives_count(db, account_set_id=account_set_id, status=status)
    return make_response(True, {"items": receives, "total": total}, "查询成功")

@router.post("/outsourcing-invoices", tags=["委外加工"])
def create_outsourcing_invoice(invoice: schemas.OutsourcingInvoiceCreate, db: Session = Depends(get_db)):
    invoice_no = f"OIV-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    db_invoice = models.OutsourcingInvoice(
        account_set_id=invoice.account_set_id,
        invoice_no=invoice_no,
        outsourcing_order_id=invoice.outsourcing_order_id,
        receive_id=invoice.receive_id,
        supplier_id=invoice.supplier_id,
        amount=invoice.amount,
        tax_amount=invoice.tax_amount,
        total_amount=invoice.total_amount,
        invoice_date=invoice.invoice_date,
        status=invoice.status
    )
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    
    return make_response(True, db_invoice, "创建成功")

@router.post("/outsourcing-estimates", tags=["委外加工"])
def create_outsourcing_estimate(estimate: schemas.OutsourcingEstimateCreate, db: Session = Depends(get_db)):
    estimate_no = f"OES-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    db_estimate = models.OutsourcingEstimate(
        account_set_id=estimate.account_set_id,
        estimate_no=estimate_no,
        receive_id=estimate.receive_id,
        outsourcing_order_id=estimate.outsourcing_order_id,
        estimated_amount=estimate.estimated_amount,
        status=estimate.status
    )
    db.add(db_estimate)
    db.commit()
    db.refresh(db_estimate)
    
    for item_data in estimate.items:
        item_data['estimate_id'] = db_estimate.id
        db_item = models.OutsourcingEstimateItem(**item_data)
        db.add(db_item)
    
    db.commit()
    db.refresh(db_estimate)
    
    return make_response(True, db_estimate, "创建成功")

@router.post("/outsourcing-accounts", tags=["委外加工"])
def create_outsourcing_account(account: schemas.OutsourcingAccountCreate, db: Session = Depends(get_db)):
    account_no = f"OAC-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    variance_amount = float(account.actual_amount) - float(account.estimated_amount)
    db_account = models.OutsourcingAccount(
        account_set_id=account.account_set_id,
        account_no=account_no,
        estimate_id=account.estimate_id,
        invoice_id=account.invoice_id,
        receive_id=account.receive_id,
        actual_amount=account.actual_amount,
        estimated_amount=account.estimated_amount,
        variance_amount=variance_amount,
        status=account.status
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    
    return make_response(True, db_account, "创建成功")