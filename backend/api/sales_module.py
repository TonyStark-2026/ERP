"""
销售管理 V2 模块
===================
销售报价、销售退货、应收管理、收款核销
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
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


def _customer_to_dict(c):
    if not c:
        return {}
    return {"id": c.id, "name": c.name, "code": getattr(c, "code", "") or ""}


def _material_to_dict(m):
    if not m:
        return {}
    return {"id": m.id, "code": m.code, "name": m.name, "unit": m.unit or "", "spec": m.spec or ""}


# ============================================================
# 1. 销售报价
# ============================================================
@router.get("/quotations", tags=["销售管理"])
def list_quotations(
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.SalesQuotation).filter(models.SalesQuotation.account_set_id == ACCOUNT_SET_ID)
    if status:
        q = q.filter(models.SalesQuotation.status == status)
    if keyword:
        q = q.filter(models.SalesQuotation.quotation_no.contains(keyword))
    items = q.order_by(models.SalesQuotation.id.desc()).all()
    result = []
    for qt in items:
        c = db.query(models.Customer).filter(models.Customer.id == qt.customer_id).first() if qt.customer_id else None
        result.append({
            "id": qt.id, "quotation_no": qt.quotation_no,
            "customer_id": qt.customer_id, "customer_name": c.name if c else "",
            "quotation_date": _fmt_date(qt.quotation_date), "valid_until": _fmt_date(qt.valid_until),
            "currency": qt.currency, "exchange_rate": float(qt.exchange_rate or 1),
            "status": qt.status,
            "status_label": {"DRAFT": "草稿", "SENT": "已发送", "ACCEPTED": "已接受",
                             "REJECTED": "已拒绝", "EXPIRED": "已过期"}.get(qt.status, qt.status),
            "total_amount": float(qt.total_amount or 0), "remark": qt.remark or "",
            "created_at": _fmt_date(qt.created_at),
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/quotations", tags=["销售管理"])
def create_quotation(data: dict = Body(...), db: Session = Depends(get_db)):
    today = datetime.date.today()
    ts = datetime.datetime.now().strftime("%H%M%S")
    qno = f"QT-{today.strftime('%Y%m%d')}-{ts}"
    qt = models.SalesQuotation(
        account_set_id=ACCOUNT_SET_ID, quotation_no=qno,
        customer_id=data.get("customer_id"),
        quotation_date=today,
        valid_until=_parse_date(data.get("valid_until")),
        currency=data.get("currency", "CNY"),
        exchange_rate=Decimal(str(data.get("exchange_rate", 1.0))),
        status="DRAFT", total_amount=0,
        remark=data.get("remark"),
    )
    db.add(qt)
    db.flush()
    # 明细
    total = Decimal("0")
    for idx, it in enumerate(data.get("items", []) or []):
        qty = Decimal(str(it.get("quantity", 0)))
        price = Decimal(str(it.get("unit_price", 0)))
        amt = qty * price
        total += amt
        db.add(models.SalesQuotationItem(
            quotation_id=qt.id, material_id=it.get("material_id"),
            quantity=qty, unit_price=price, amount=amt,
            price_type=it.get("price_type"), remark=it.get("remark"),
        ))
    qt.total_amount = total
    db.commit()
    return make_response(True, {"id": qt.id, "quotation_no": qno}, "报价单创建成功")


@router.put("/quotations/{qid}/status", tags=["销售管理"])
def update_quotation_status(qid: int, data: dict = Body(...), db: Session = Depends(get_db)):
    qt = db.query(models.SalesQuotation).filter(models.SalesQuotation.id == qid).first()
    if not qt:
        return make_response(False, None, "报价单不存在", "40401")
    qt.status = data.get("status", qt.status)
    db.commit()
    return make_response(True, {"id": qt.id}, "状态已更新")


@router.delete("/quotations/{qid}", tags=["销售管理"])
def delete_quotation(qid: int, db: Session = Depends(get_db)):
    qt = db.query(models.SalesQuotation).filter(models.SalesQuotation.id == qid).first()
    if not qt:
        return make_response(False, None, "报价单不存在", "40401")
    db.query(models.SalesQuotationItem).filter(models.SalesQuotationItem.quotation_id == qid).delete()
    db.delete(qt)
    db.commit()
    return make_response(True, None, "报价单已删除")


# ============================================================
# 2. 销售退货
# ============================================================
@router.get("/returns", tags=["销售管理"])
def list_returns(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.SalesReturn).filter(models.SalesReturn.account_set_id == ACCOUNT_SET_ID)
    if status:
        q = q.filter(models.SalesReturn.status == status)
    items = q.order_by(models.SalesReturn.id.desc()).all()
    result = []
    for r in items:
        c = db.query(models.Customer).filter(models.Customer.id == r.customer_id).first() if r.customer_id else None
        result.append({
            "id": r.id, "return_no": r.return_no,
            "customer_id": r.customer_id, "customer_name": c.name if c else "",
            "return_date": _fmt_date(r.return_date), "reason": r.reason or "",
            "status": r.status,
            "status_label": {"PENDING": "待处理", "INSPECTING": "质检中",
                             "ACCEPTED": "已接受", "REJECTED": "已拒绝"}.get(r.status, r.status),
            "total_amount": float(r.total_amount or 0),
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/returns", tags=["销售管理"])
def create_return(data: dict = Body(...), db: Session = Depends(get_db)):
    today = datetime.date.today()
    ts = datetime.datetime.now().strftime("%H%M%S")
    rno = f"SR-{today.strftime('%Y%m%d')}-{ts}"
    ret = models.SalesReturn(
        account_set_id=ACCOUNT_SET_ID, return_no=rno,
        customer_id=data.get("customer_id"),
        sales_order_id=data.get("sales_order_id"),
        outbound_id=data.get("outbound_id"),
        return_date=today, reason=data.get("reason"),
        status="PENDING", total_amount=0,
    )
    db.add(ret)
    db.flush()
    total = Decimal("0")
    for it in data.get("items", []) or []:
        qty = Decimal(str(it.get("quantity", 0)))
        price = Decimal(str(it.get("unit_price", 0)))
        amt = qty * price
        total += amt
        db.add(models.SalesReturnItem(
            return_id=ret.id, material_id=it.get("material_id"),
            quantity=qty, unit_price=price, amount=amt,
            reason=it.get("reason"),
        ))
    ret.total_amount = total
    db.commit()
    return make_response(True, {"id": ret.id, "return_no": rno}, "退货单创建成功")


@router.put("/returns/{rid}/status", tags=["销售管理"])
def update_return_status(rid: int, data: dict = Body(...), db: Session = Depends(get_db)):
    ret = db.query(models.SalesReturn).filter(models.SalesReturn.id == rid).first()
    if not ret:
        return make_response(False, None, "退货单不存在", "40401")
    ret.status = data.get("status", ret.status)
    db.commit()
    return make_response(True, {"id": ret.id}, "状态已更新")


# ============================================================
# 3. 应收管理
# ============================================================
@router.get("/receivables", tags=["销售管理"])
def list_receivables(
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Receivable).filter(models.Receivable.account_set_id == ACCOUNT_SET_ID)
    if status:
        q = q.filter(models.Receivable.status == status)
    if customer_id:
        q = q.filter(models.Receivable.customer_id == customer_id)
    items = q.order_by(models.Receivable.id.desc()).all()
    result = []
    for r in items:
        c = db.query(models.Customer).filter(models.Customer.id == r.customer_id).first()
        result.append({
            "id": r.id, "receivable_no": r.receivable_no,
            "customer_id": r.customer_id, "customer_name": c.name if c else "",
            "source_type": r.source_type,
            "source_label": {"SALES_OUTBOUND": "销售出库", "SALES_ORDER": "销售订单"}.get(r.source_type, r.source_type),
            "source_no": r.source_no or "",
            "amount": float(r.amount or 0), "received_amount": float(r.received_amount or 0),
            "balance": float(r.balance or 0), "due_date": _fmt_date(r.due_date),
            "status": r.status,
            "status_label": {"PENDING": "待收", "PARTIAL": "部分收款",
                             "SETTLED": "已结清", "OVERDUE": "逾期"}.get(r.status, r.status),
            "created_at": _fmt_date(r.created_at),
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/receivables", tags=["销售管理"])
def create_receivable(data: dict = Body(...), db: Session = Depends(get_db)):
    ts = datetime.datetime.now().strftime("%H%M%S")
    rno = f"AR-{datetime.date.today().strftime('%Y%m%d')}-{ts}"
    amt = Decimal(str(data.get("amount", 0)))
    rv = models.Receivable(
        account_set_id=ACCOUNT_SET_ID, receivable_no=rno,
        customer_id=data.get("customer_id"),
        source_type=data.get("source_type", "SALES_ORDER"),
        source_no=data.get("source_no"),
        amount=amt, received_amount=Decimal("0"), balance=amt,
        due_date=_parse_date(data.get("due_date")), status="PENDING",
    )
    db.add(rv)
    db.commit()
    return make_response(True, {"id": rv.id, "receivable_no": rno}, "应收单创建成功")


# ============================================================
# 4. 收款核销
# ============================================================
@router.get("/receipts", tags=["销售管理"])
def list_receipts(db: Session = Depends(get_db)):
    items = db.query(models.Receipt).filter(
        models.Receipt.account_set_id == ACCOUNT_SET_ID
    ).order_by(models.Receipt.id.desc()).all()
    result = []
    for r in items:
        c = db.query(models.Customer).filter(models.Customer.id == r.customer_id).first()
        result.append({
            "id": r.id, "receipt_no": r.receipt_no,
            "customer_id": r.customer_id, "customer_name": c.name if c else "",
            "receipt_date": _fmt_date(r.receipt_date), "amount": float(r.amount or 0),
            "payment_method": r.payment_method or "",
            "method_label": {"CASH": "现金", "BANK": "银行转账",
                             "ALIPAY": "支付宝", "WECHAT": "微信"}.get(r.payment_method, r.payment_method or ""),
            "receivable_id": r.receivable_id, "remark": r.remark or "",
            "status": r.status, "created_at": _fmt_date(r.created_at),
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/receipts", tags=["销售管理"])
def create_receipt(data: dict = Body(...), db: Session = Depends(get_db)):
    """创建收款单并自动核销应收单"""
    ts = datetime.datetime.now().strftime("%H%M%S")
    rno = f"RC-{datetime.date.today().strftime('%Y%m%d')}-{ts}"
    amt = Decimal(str(data.get("amount", 0)))
    rc = models.Receipt(
        account_set_id=ACCOUNT_SET_ID, receipt_no=rno,
        customer_id=data.get("customer_id"),
        receipt_date=_parse_date(data.get("receipt_date")) or datetime.date.today(),
        amount=amt, payment_method=data.get("payment_method"),
        receivable_id=data.get("receivable_id"),
        remark=data.get("remark"), status="CONFIRMED",
    )
    db.add(rc)
    db.flush()
    # 核销应收单
    rv_id = data.get("receivable_id")
    if rv_id:
        rv = db.query(models.Receivable).filter(models.Receivable.id == rv_id).first()
        if rv:
            rv.received_amount = (rv.received_amount or Decimal("0")) + amt
            rv.balance = rv.amount - rv.received_amount
            if rv.balance <= Decimal("0.01"):
                rv.status = "SETTLED"
            else:
                rv.status = "PARTIAL"
    db.commit()
    return make_response(True, {"id": rc.id, "receipt_no": rno}, "收款单创建成功，已核销应收")


@router.get("/overview", tags=["销售管理"])
def sales_overview(db: Session = Depends(get_db)):
    """销售财务总览"""
    qt_count = db.query(models.SalesQuotation).filter(
        models.SalesQuotation.account_set_id == ACCOUNT_SET_ID
    ).count()
    ret_count = db.query(models.SalesReturn).filter(
        models.SalesReturn.account_set_id == ACCOUNT_SET_ID
    ).count()
    rvs = db.query(models.Receivable).filter(
        models.Receivable.account_set_id == ACCOUNT_SET_ID
    ).all()
    total_ar = sum(float(r.amount or 0) for r in rvs)
    total_received = sum(float(r.received_amount or 0) for r in rvs)
    total_balance = sum(float(r.balance or 0) for r in rvs)
    overdue = sum(1 for r in rvs if r.status == "OVERDUE")
    pending = sum(1 for r in rvs if r.status == "PENDING")
    receipt_count = db.query(models.Receipt).filter(
        models.Receipt.account_set_id == ACCOUNT_SET_ID
    ).count()
    return make_response(True, {
        "quotation_count": qt_count, "return_count": ret_count,
        "receivable_count": len(rvs), "receipt_count": receipt_count,
        "total_receivable": total_ar, "total_received": total_received,
        "total_balance": total_balance, "overdue_count": overdue, "pending_count": pending,
    })


def _parse_date(s):
    if not s:
        return None
    if isinstance(s, (datetime.date, datetime.datetime)):
        return s if isinstance(s, datetime.date) else s.date()
    try:
        return datetime.date.fromisoformat(str(s)[:10])
    except Exception:
        return None
