from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import date, datetime, timedelta
from decimal import Decimal
import json
import re

from .. import crud, schemas, models
from ..database import get_db
from ..app import make_response

router = APIRouter()

VOUCHER_TEMPLATES = {
    "purchase_inbound": {
        "description": "采购入库",
        "entries": [
            {"account": "库存商品", "debit": True, "summary": "采购入库"},
            {"account": "应交税费-应交增值税-进项税额", "debit": True, "summary": "进项税额"},
            {"account": "应付账款", "credit": True, "summary": "应付货款"}
        ]
    },
    "sales_outbound": {
        "description": "销售出库",
        "entries": [
            {"account": "应收账款", "debit": True, "summary": "销售货款"},
            {"account": "主营业务收入", "credit": True, "summary": "销售收入"},
            {"account": "应交税费-应交增值税-销项税额", "credit": True, "summary": "销项税额"}
        ]
    },
    "sales_gift": {
        "description": "销售赠品",
        "entries": [
            {"account": "销售费用-赠品", "debit": True, "summary": "赠送商品"},
            {"account": "库存商品", "credit": True, "summary": "赠品出库"}
        ]
    },
    "receipt": {
        "description": "收款",
        "entries": [
            {"account": "银行存款", "debit": True, "summary": "收到货款"},
            {"account": "应收账款", "credit": True, "summary": "收回货款"}
        ]
    },
    "payment": {
        "description": "付款",
        "entries": [
            {"account": "应付账款", "debit": True, "summary": "支付货款"},
            {"account": "银行存款", "credit": True, "summary": "付出款项"}
        ]
    },
    "production_completion": {
        "description": "生产完工入库",
        "entries": [
            {"account": "库存商品", "debit": True, "summary": "完工入库"},
            {"account": "生产成本-直接材料", "credit": True, "summary": "结转材料成本"},
            {"account": "生产成本-直接人工", "credit": True, "summary": "结转人工成本"},
            {"account": "生产成本-制造费用", "credit": True, "summary": "结转制造费用"}
        ]
    },
    "inventory_adjustment": {
        "description": "库存调整",
        "entries": [
            {"account": "待处理财产损溢", "debit": True, "summary": "盘盈盘亏"},
            {"account": "库存商品", "credit": True, "summary": "调整库存"}
        ]
    }
}

CASH_FLOW_MAPPING = {
    "1001": {"category": "operating", "item": "销售商品、提供劳务收到的现金", "direction": "in"},
    "1002": {"category": "operating", "item": "购买商品、接受劳务支付的现金", "direction": "out"},
    "1122": {"category": "operating", "item": "销售商品、提供劳务收到的现金", "direction": "in"},
    "2202": {"category": "operating", "item": "购买商品、接受劳务支付的现金", "direction": "out"},
    "5001": {"category": "operating", "item": "支付给职工以及为职工支付的现金", "direction": "out"},
    "6602": {"category": "operating", "item": "支付其他与经营活动有关的现金", "direction": "out"},
    "1501": {"category": "investing", "item": "购建固定资产支付的现金", "direction": "out"},
    "1502": {"category": "investing", "item": "处置固定资产收回的现金", "direction": "in"},
    "2501": {"category": "financing", "item": "取得借款收到的现金", "direction": "in"},
    "2502": {"category": "financing", "item": "偿还债务支付的现金", "direction": "out"},
    "4001": {"category": "financing", "item": "吸收投资收到的现金", "direction": "in"},
}

AUXILIARY_DIMENSIONS = ["customer", "supplier", "department", "employee", "project", "material"]

class VoucherEntry(BaseModel):
    account_code: str
    account_name: str
    debit: Optional[float] = None
    credit: Optional[float] = None
    summary: Optional[str] = None
    auxiliary_info: Optional[Dict] = None

class VoucherCreateRequest(BaseModel):
    voucher_date: str
    voucher_type: str = "记"
    entries: List[VoucherEntry]
    source_document_id: Optional[int] = None
    source_document_type: Optional[str] = None
    attachments: int = 0
    preparer: str = ""
    auxiliary_info: Optional[Dict] = None

class AutoVoucherRequest(BaseModel):
    document_type: str
    document_id: int
    account_set_id: Optional[int] = None

@router.post("/auto-voucher", tags=["财务管理"])
def generate_auto_voucher(request: AutoVoucherRequest, db: Session = Depends(get_db)):
    template = VOUCHER_TEMPLATES.get(request.document_type)
    if not template:
        return make_response(False, None, f"不支持的单据类型: {request.document_type}", "40003")
    
    entries = []
    total_amount = 0
    auxiliary_info = {}
    
    if request.document_type == "purchase_inbound":
        po = crud.get_purchase_order(db, order_id=request.document_id)
        if not po:
            return make_response(False, None, "采购订单不存在", "40002")
        
        total_amount = sum(item.quantity * (item.special_price or item.unit_price) for item in po.items)
        tax_amount = total_amount * (po.tax_rate or 0)
        
        entries = [
            {"account_code": "1403", "account_name": "库存商品", "debit": total_amount, "summary": "采购入库"},
            {"account_code": "22210101", "account_name": "应交税费-应交增值税-进项税额", "debit": tax_amount, "summary": "进项税额"},
            {"account_code": "2202", "account_name": "应付账款", "credit": total_amount + tax_amount, "summary": "应付货款"}
        ]
        
        if po.supplier:
            auxiliary_info["supplier"] = {"id": po.supplier_id, "name": po.supplier.name}
    
    elif request.document_type == "sales_outbound":
        so = crud.get_sales_order(db, sales_order_id=request.document_id)
        if not so:
            return make_response(False, None, "销售订单不存在", "40002")
        
        total_amount = sum(item.quantity * item.unit_price for item in so.items if not item.is_gift)
        tax_amount = total_amount * (so.tax_rate or 0)
        
        entries = [
            {"account_code": "1122", "account_name": "应收账款", "debit": total_amount + tax_amount, "summary": "销售货款"},
            {"account_code": "6001", "account_name": "主营业务收入", "credit": total_amount, "summary": "销售收入"},
            {"account_code": "22210102", "account_name": "应交税费-应交增值税-销项税额", "credit": tax_amount, "summary": "销项税额"}
        ]
        
        if so.customer:
            auxiliary_info["customer"] = {"id": so.customer_id, "name": so.customer.name}
        if so.department:
            auxiliary_info["department"] = so.department
        if so.salesperson:
            auxiliary_info["employee"] = {"id": so.salesperson_id, "name": so.salesperson}
        if so.project:
            auxiliary_info["project"] = so.project
    
    elif request.document_type == "sales_gift":
        so = crud.get_sales_order(db, sales_order_id=request.document_id)
        if not so:
            return make_response(False, None, "销售订单不存在", "40002")
        
        gift_items = [item for item in so.items if item.is_gift]
        gift_cost = sum(item.quantity * (item.material.standard_cost or 0) for item in gift_items)
        
        entries = [
            {"account_code": "660102", "account_name": "销售费用-赠品", "debit": gift_cost, "summary": "赠送商品"},
            {"account_code": "1403", "account_name": "库存商品", "credit": gift_cost, "summary": "赠品出库"}
        ]
    
    elif request.document_type == "receipt":
        receipt = crud.get_receipt_record(db, receipt_id=request.document_id)
        if not receipt:
            return make_response(False, None, "收款记录不存在", "40002")
        
        entries = [
            {"account_code": "1002", "account_name": "银行存款", "debit": receipt.amount, "summary": "收到货款"},
            {"account_code": "1122", "account_name": "应收账款", "credit": receipt.amount, "summary": "收回货款"}
        ]
        
        if receipt.customer:
            auxiliary_info["customer"] = {"id": receipt.customer_id, "name": receipt.customer.name}
    
    draft_voucher = {
        "document_type": request.document_type,
        "document_id": request.document_id,
        "template": template["description"],
        "entries": entries,
        "total_amount": total_amount,
        "auxiliary_info": auxiliary_info,
        "can_edit": True
    }
    
    return make_response(True, draft_voucher, "凭证草稿生成成功")

@router.post("/vouchers", tags=["财务管理"])
def create_voucher(request: VoucherCreateRequest, db: Session = Depends(get_db)):
    voucher_no = f"{request.voucher_type}-{datetime.now().strftime('%Y%m%d')}-{len(crud.get_vouchers(db)) + 1:04d}"
    
    db_voucher = models.VoucherDB(
        voucher_no=voucher_no,
        voucher_date=datetime.strptime(request.voucher_date, "%Y-%m-%d").date(),
        voucher_type=request.voucher_type,
        attachments=request.attachments,
        preparer=request.preparer,
        status="DRAFT",
        source_document_id=request.source_document_id,
        source_document_type=request.source_document_type,
        auxiliary_info=json.dumps(request.auxiliary_info) if request.auxiliary_info else None,
        account_set_id=request.account_set_id
    )
    db.add(db_voucher)
    db.commit()
    db.refresh(db_voucher)
    
    for entry in request.entries:
        db_entry = models.VoucherEntry(
            voucher_id=db_voucher.id,
            account_code=entry.account_code,
            account_name=entry.account_name,
            debit=entry.debit,
            credit=entry.credit,
            summary=entry.summary,
            auxiliary_info=json.dumps(entry.auxiliary_info) if entry.auxiliary_info else None
        )
        db.add(db_entry)
    
    db.commit()
    
    update_cash_flow_from_voucher(db, db_voucher)
    
    return make_response(True, {
        "id": db_voucher.id,
        "voucher_no": db_voucher.voucher_no,
        "status": db_voucher.status
    }, "凭证创建成功")

@router.get("/vouchers", tags=["财务管理"])
def get_vouchers(account_set_id: Optional[int] = None, status: Optional[str] = None, 
                 start_date: Optional[str] = None, end_date: Optional[str] = None,
                 skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    vouchers = crud.get_vouchers(db, account_set_id=account_set_id, status=status, 
                                 start_date=start_date, end_date=end_date,
                                 skip=skip, limit=limit)
    total = crud.get_vouchers_count(db, account_set_id=account_set_id, status=status,
                                    start_date=start_date, end_date=end_date)
    return make_response(True, {"items": vouchers, "total": total}, "查询成功")

@router.get("/vouchers/{voucher_id}", tags=["财务管理"])
def get_voucher(voucher_id: int, db: Session = Depends(get_db)):
    voucher = crud.get_voucher(db, voucher_id=voucher_id)
    if not voucher:
        return make_response(False, None, "凭证不存在", "40002")
    
    entries = crud.get_voucher_entries(db, voucher_id=voucher_id)
    
    result = {
        "id": voucher.id,
        "voucher_no": voucher.voucher_no,
        "voucher_date": voucher.voucher_date.isoformat() if voucher.voucher_date else None,
        "voucher_type": voucher.voucher_type,
        "status": voucher.status,
        "attachments": voucher.attachments,
        "preparer": voucher.preparer,
        "entries": entries,
        "auxiliary_info": json.loads(voucher.auxiliary_info) if voucher.auxiliary_info else {}
    }
    
    return make_response(True, result, "查询成功")

@router.put("/vouchers/{voucher_id}/approve", tags=["财务管理"])
def approve_voucher(voucher_id: int, db: Session = Depends(get_db)):
    voucher = crud.get_voucher(db, voucher_id=voucher_id)
    if not voucher:
        return make_response(False, None, "凭证不存在", "40002")
    
    if voucher.status not in ["DRAFT", "PENDING"]:
        return make_response(False, None, "只能审核草稿或待审核状态的凭证", "40003")
    
    voucher.status = "APPROVED"
    voucher.approver = "system"
    voucher.approved_at = datetime.now()
    db.commit()
    db.refresh(voucher)
    
    return make_response(True, voucher, "凭证审核成功")

@router.put("/vouchers/{voucher_id}/post", tags=["财务管理"])
def post_voucher(voucher_id: int, db: Session = Depends(get_db)):
    voucher = crud.get_voucher(db, voucher_id=voucher_id)
    if not voucher:
        return make_response(False, None, "凭证不存在", "40002")
    
    if voucher.status != "APPROVED":
        return make_response(False, None, "只能记账已审核的凭证", "40003")
    
    voucher.status = "POSTED"
    voucher.posted_at = datetime.now()
    db.commit()
    db.refresh(voucher)
    
    return make_response(True, voucher, "凭证记账成功")

def update_cash_flow_from_voucher(db: Session, voucher: models.VoucherDB):
    entries = crud.get_voucher_entries(db, voucher_id=voucher.id)
    
    for entry in entries:
        mapping = CASH_FLOW_MAPPING.get(entry.account_code[:4])
        if mapping:
            amount = entry.debit if entry.debit else entry.credit
            direction = mapping["direction"]
            
            if direction == "in":
                cf_item = crud.get_cash_flow_item(db, category=mapping["category"], item_name=mapping["item"])
                if cf_item:
                    cf_item.amount += amount
                else:
                    crud.create_cash_flow_item(db, schemas.CashFlowItemCreate(
                        category=mapping["category"],
                        item_name=mapping["item"],
                        amount=amount
                    ))
            else:
                cf_item = crud.get_cash_flow_item(db, category=mapping["category"], item_name=mapping["item"])
                if cf_item:
                    cf_item.amount -= amount
                else:
                    crud.create_cash_flow_item(db, schemas.CashFlowItemCreate(
                        category=mapping["category"],
                        item_name=mapping["item"],
                        amount=-amount
                    ))
    
    db.commit()

@router.get("/reports/cash-flow-direct", tags=["财务管理"])
def get_cash_flow_direct(start_date: Optional[str] = None, end_date: Optional[str] = None, db: Session = Depends(get_db)):
    cf_items = crud.get_cash_flow_items(db, start_date=start_date, end_date=end_date)
    
    operating_items = [item for item in cf_items if item.category == "operating"]
    investing_items = [item for item in cf_items if item.category == "investing"]
    financing_items = [item for item in cf_items if item.category == "financing"]
    
    operating_total = sum(item.amount for item in operating_items)
    investing_total = sum(item.amount for item in investing_items)
    financing_total = sum(item.amount for item in financing_items)
    
    result = {
        "report_name": "现金流量表（直接法）",
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "operating_activities": {
            "items": [{"name": item.item_name, "amount": float(item.amount)} for item in operating_items],
            "subtotal": float(operating_total)
        },
        "investing_activities": {
            "items": [{"name": item.item_name, "amount": float(item.amount)} for item in investing_items],
            "subtotal": float(investing_total)
        },
        "financing_activities": {
            "items": [{"name": item.item_name, "amount": float(item.amount)} for item in financing_items],
            "subtotal": float(financing_total)
        },
        "net_cash_flow": float(operating_total + investing_total + financing_total)
    }
    
    return make_response(True, result, "查询成功")

@router.get("/reports/cash-flow-indirect", tags=["财务管理"])
def get_cash_flow_indirect(start_date: Optional[str] = None, end_date: Optional[str] = None, db: Session = Depends(get_db)):
    vouchers = crud.get_vouchers(db, status="POSTED", start_date=start_date, end_date=end_date)
    
    net_profit = 0
    depreciation = 0
    amortization = 0
    accounts_receivable_change = 0
    inventory_change = 0
    accounts_payable_change = 0
    
    for voucher in vouchers:
        entries = crud.get_voucher_entries(db, voucher_id=voucher.id)
        for entry in entries:
            if entry.account_code.startswith('6301'):
                net_profit -= (entry.credit or 0)
                net_profit += (entry.debit or 0)
            elif entry.account_code.startswith('1602'):
                depreciation += (entry.credit or 0)
            elif entry.account_code.startswith('1702'):
                amortization += (entry.credit or 0)
            elif entry.account_code.startswith('1122'):
                accounts_receivable_change -= (entry.debit or 0)
                accounts_receivable_change += (entry.credit or 0)
            elif entry.account_code.startswith('1403') or entry.account_code.startswith('1405'):
                inventory_change -= (entry.debit or 0)
                inventory_change += (entry.credit or 0)
            elif entry.account_code.startswith('2202'):
                accounts_payable_change += (entry.credit or 0)
                accounts_payable_change -= (entry.debit or 0)
    
    operating_cash_flow = net_profit + depreciation + amortization + \
                          accounts_receivable_change + inventory_change + accounts_payable_change
    
    result = {
        "report_name": "现金流量表（间接法）",
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "net_profit": float(net_profit),
        "adjustments": {
            "depreciation": float(depreciation),
            "amortization": float(amortization),
            "accounts_receivable_change": float(accounts_receivable_change),
            "inventory_change": float(inventory_change),
            "accounts_payable_change": float(accounts_payable_change)
        },
        "operating_cash_flow": float(operating_cash_flow)
    }
    
    return make_response(True, result, "查询成功")

@router.get("/reports/aging-analysis", tags=["财务管理"])
def get_aging_analysis(account_set_id: Optional[int] = None, db: Session = Depends(get_db)):
    receivables = crud.get_receivables(db, account_set_id=account_set_id)
    payables = crud.get_payables(db, account_set_id=account_set_id)
    today = datetime.now().date()
    
    ar_aging = {"0-30": 0, "31-60": 0, "61-90": 0, "91-180": 0, "180+": 0}
    ap_aging = {"0-30": 0, "31-60": 0, "61-90": 0, "91-180": 0, "180+": 0}
    
    for rec in receivables:
        days_overdue = (today - rec.due_date).days if rec.due_date else 0
        if days_overdue <= 30:
            ar_aging["0-30"] += rec.amount
        elif days_overdue <= 60:
            ar_aging["31-60"] += rec.amount
        elif days_overdue <= 90:
            ar_aging["61-90"] += rec.amount
        elif days_overdue <= 180:
            ar_aging["91-180"] += rec.amount
        else:
            ar_aging["180+"] += rec.amount
    
    for pay in payables:
        days_overdue = (today - pay.due_date).days if pay.due_date else 0
        if days_overdue <= 30:
            ap_aging["0-30"] += pay.amount
        elif days_overdue <= 60:
            ap_aging["31-60"] += pay.amount
        elif days_overdue <= 90:
            ap_aging["61-90"] += pay.amount
        elif days_overdue <= 180:
            ap_aging["91-180"] += pay.amount
        else:
            ap_aging["180+"] += pay.amount
    
    result = {
        "report_name": "账龄分析表",
        "report_date": today.isoformat(),
        "receivables": ar_aging,
        "payables": ap_aging
    }
    
    return make_response(True, result, "查询成功")

@router.get("/reports/auxiliary-analysis", tags=["财务管理"])
def get_auxiliary_analysis(account_code: str, dimension: str, account_set_id: Optional[int] = None, db: Session = Depends(get_db)):
    if dimension not in AUXILIARY_DIMENSIONS:
        return make_response(False, None, f"无效的辅助核算维度: {dimension}", "40003")
    
    vouchers = crud.get_vouchers(db, account_set_id=account_set_id, status="POSTED")
    result = {}
    
    for voucher in vouchers:
        entries = crud.get_voucher_entries(db, voucher_id=voucher.id)
        for entry in entries:
            if entry.account_code.startswith(account_code[:4]):
                aux_info = json.loads(entry.auxiliary_info) if entry.auxiliary_info else {}
                if dimension in aux_info:
                    key = aux_info[dimension]
                    if isinstance(key, dict):
                        key = key.get("name", str(key.get("id", "unknown")))
                    amount = entry.debit if entry.debit else entry.credit
                    result[key] = result.get(key, 0) + amount
    
    return make_response(True, {
        "account_code": account_code,
        "dimension": dimension,
        "data": {k: float(v) for k, v in result.items()}
    }, "查询成功")


@router.get("/reports/trial-balance", tags=["财务管理"])
def get_trial_balance(account_set_id: Optional[int] = None, period: str = "THIS_MONTH", db: Session = Depends(get_db)):
    today = datetime.now().date()
    
    if period == "THIS_MONTH":
        start_date = date(today.year, today.month, 1)
        end_date = today
    elif period == "LAST_MONTH":
        last_month = today.month - 1 if today.month > 1 else 12
        last_year = today.year if today.month > 1 else today.year - 1
        start_date = date(last_year, last_month, 1)
        end_date = date(last_year, last_month, 1) + timedelta(days=32)
        end_date = end_date - timedelta(days=end_date.day)
    elif period == "THIS_YEAR":
        start_date = date(today.year, 1, 1)
        end_date = today
    else:
        return make_response(False, None, "无效的时间周期", "40003")
    
    vouchers = crud.get_vouchers(db, account_set_id=account_set_id, status="POSTED",
                                 start_date=start_date.isoformat(), end_date=end_date.isoformat())
    
    account_balances = {}
    
    for voucher in vouchers:
        entries = crud.get_voucher_entries(db, voucher_id=voucher.id)
        for entry in entries:
            if entry.account_code not in account_balances:
                account_balances[entry.account_code] = {
                    "account_code": entry.account_code,
                    "account_name": entry.account_name,
                    "debit": 0,
                    "credit": 0
                }
            if entry.debit:
                account_balances[entry.account_code]["debit"] += entry.debit
            if entry.credit:
                account_balances[entry.account_code]["credit"] += entry.credit
    
    total_debit = sum(b["debit"] for b in account_balances.values())
    total_credit = sum(b["credit"] for b in account_balances.values())
    
    return make_response(True, {
        "report_name": "科目余额表",
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_debit": float(total_debit),
        "total_credit": float(total_credit),
        "balanced": abs(total_debit - total_credit) < 0.01,
        "accounts": [
            {
                "account_code": b["account_code"],
                "account_name": b["account_name"],
                "debit": float(b["debit"]),
                "credit": float(b["credit"]),
                "balance": float(b["debit"] - b["credit"])
            } for b in account_balances.values()
        ]
    }, "查询成功")


@router.get("/reports/profit-loss", tags=["财务管理"])
def get_profit_loss(account_set_id: Optional[int] = None, period: str = "THIS_MONTH", db: Session = Depends(get_db)):
    today = datetime.now().date()
    
    if period == "THIS_MONTH":
        start_date = date(today.year, today.month, 1)
        end_date = today
    elif period == "LAST_MONTH":
        last_month = today.month - 1 if today.month > 1 else 12
        last_year = today.year if today.month > 1 else today.year - 1
        start_date = date(last_year, last_month, 1)
        end_date = date(last_year, last_month, 1) + timedelta(days=32)
        end_date = end_date - timedelta(days=end_date.day)
    elif period == "THIS_YEAR":
        start_date = date(today.year, 1, 1)
        end_date = today
    else:
        return make_response(False, None, "无效的时间周期", "40003")
    
    vouchers = crud.get_vouchers(db, account_set_id=account_set_id, status="POSTED",
                                 start_date=start_date.isoformat(), end_date=end_date.isoformat())
    
    revenue = 0
    cost_of_sales = 0
    operating_expenses = 0
    other_income = 0
    other_expenses = 0
    income_tax = 0
    
    for voucher in vouchers:
        entries = crud.get_voucher_entries(db, voucher_id=voucher.id)
        for entry in entries:
            if entry.account_code.startswith('60'):
                revenue += (entry.credit or 0)
            elif entry.account_code.startswith('64'):
                cost_of_sales += (entry.debit or 0)
            elif entry.account_code.startswith('66'):
                operating_expenses += (entry.debit or 0)
            elif entry.account_code.startswith('67'):
                other_income += (entry.credit or 0)
                other_expenses += (entry.debit or 0)
            elif entry.account_code.startswith('6801'):
                income_tax += (entry.debit or 0)
    
    gross_profit = revenue - cost_of_sales
    operating_profit = gross_profit - operating_expenses
    total_profit = operating_profit + other_income - other_expenses
    net_profit = total_profit - income_tax
    
    return make_response(True, {
        "report_name": "利润表",
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "revenue": float(revenue),
        "cost_of_sales": float(cost_of_sales),
        "gross_profit": float(gross_profit),
        "operating_expenses": float(operating_expenses),
        "operating_profit": float(operating_profit),
        "other_income": float(other_income),
        "other_expenses": float(other_expenses),
        "total_profit": float(total_profit),
        "income_tax": float(income_tax),
        "net_profit": float(net_profit)
    }, "查询成功")


@router.get("/reports/balance-sheet", tags=["财务管理"])
def get_balance_sheet(account_set_id: Optional[int] = None, report_date: Optional[str] = None, db: Session = Depends(get_db)):
    today = datetime.now().date()
    report_date = datetime.strptime(report_date, "%Y-%m-%d").date() if report_date else today
    
    start_date = date(report_date.year, 1, 1)
    
    vouchers = crud.get_vouchers(db, account_set_id=account_set_id, status="POSTED",
                                 start_date=start_date.isoformat(), end_date=report_date.isoformat())
    
    assets = {"current": 0, "non_current": 0}
    liabilities = {"current": 0, "non_current": 0}
    equity = 0
    
    for voucher in vouchers:
        entries = crud.get_voucher_entries(db, voucher_id=voucher.id)
        for entry in entries:
            ac = entry.account_code
            amount = (entry.debit or 0) - (entry.credit or 0)
            
            if ac.startswith('1'):
                if ac.startswith('10') or ac.startswith('11') or ac.startswith('12') or ac.startswith('13') or ac.startswith('14'):
                    assets["current"] += amount
                else:
                    assets["non_current"] += amount
            elif ac.startswith('2'):
                if ac.startswith('21') or ac.startswith('22'):
                    liabilities["current"] += amount
                else:
                    liabilities["non_current"] += amount
            elif ac.startswith('4'):
                equity += amount
    
    total_assets = assets["current"] + assets["non_current"]
    total_liabilities = liabilities["current"] + liabilities["non_current"]
    total_equity = equity
    
    return make_response(True, {
        "report_name": "资产负债表",
        "report_date": report_date.isoformat(),
        "assets": {
            "current": float(assets["current"]),
            "non_current": float(assets["non_current"]),
            "total": float(total_assets)
        },
        "liabilities": {
            "current": float(liabilities["current"]),
            "non_current": float(liabilities["non_current"]),
            "total": float(total_liabilities)
        },
        "equity": float(total_equity),
        "balanced": abs(total_assets - total_liabilities - total_equity) < 0.01
    }, "查询成功")


@router.post("/vouchers/batch-approve", tags=["财务管理"])
def batch_approve_vouchers(voucher_ids: List[int], db: Session = Depends(get_db)):
    approved_count = 0
    failed_count = 0
    failed_ids = []
    
    for vid in voucher_ids:
        voucher = crud.get_voucher(db, voucher_id=vid)
        if voucher and voucher.status in ["DRAFT", "PENDING"]:
            voucher.status = "APPROVED"
            voucher.approver = "system"
            voucher.approved_at = datetime.now()
            approved_count += 1
        else:
            failed_count += 1
            failed_ids.append(vid)
    
    db.commit()
    
    return make_response(True, {
        "total_count": len(voucher_ids),
        "approved_count": approved_count,
        "failed_count": failed_count,
        "failed_ids": failed_ids
    }, "批量审核完成")


@router.post("/vouchers/batch-post", tags=["财务管理"])
def batch_post_vouchers(voucher_ids: List[int], db: Session = Depends(get_db)):
    posted_count = 0
    failed_count = 0
    failed_ids = []
    
    for vid in voucher_ids:
        voucher = crud.get_voucher(db, voucher_id=vid)
        if voucher and voucher.status == "APPROVED":
            voucher.status = "POSTED"
            voucher.posted_at = datetime.now()
            posted_count += 1
        else:
            failed_count += 1
            failed_ids.append(vid)
    
    db.commit()
    
    return make_response(True, {
        "total_count": len(voucher_ids),
        "posted_count": posted_count,
        "failed_count": failed_count,
        "failed_ids": failed_ids
    }, "批量记账完成")


@router.get("/voucher-templates", tags=["财务管理"])
def get_voucher_templates(db: Session = Depends(get_db)):
    templates = []
    for key, template in VOUCHER_TEMPLATES.items():
        templates.append({
            "code": key,
            "description": template["description"],
            "entries": template["entries"]
        })
    return make_response(True, templates, "查询成功")


@router.post("/voucher-templates/{template_code}/preview", tags=["财务管理"])
def preview_voucher_template(template_code: str, amounts: Dict[str, float], db: Session = Depends(get_db)):
    template = VOUCHER_TEMPLATES.get(template_code)
    if not template:
        return make_response(False, None, f"模板不存在: {template_code}", "40002")
    
    entries = []
    total_debit = 0
    total_credit = 0
    
    for entry in template["entries"]:
        amount = amounts.get(entry["account"], 0)
        if entry["debit"]:
            entries.append({
                "account": entry["account"],
                "debit": amount,
                "credit": 0,
                "summary": entry["summary"]
            })
            total_debit += amount
        else:
            entries.append({
                "account": entry["account"],
                "debit": 0,
                "credit": amount,
                "summary": entry["summary"]
            })
            total_credit += amount
    
    return make_response(True, {
        "template_code": template_code,
        "description": template["description"],
        "entries": entries,
        "total_debit": float(total_debit),
        "total_credit": float(total_credit),
        "balanced": abs(total_debit - total_credit) < 0.01
    }, "预览完成")


# ==================== 财务仪表盘 ====================

@router.get("/dashboard", tags=["财务管理"])
def get_finance_dashboard(db: Session = Depends(get_db)):
    """财务仪表盘汇总数据：关键指标 + 月度趋势 + 科目分布 + 凭证类型分布 + 损益结构。
    数据来源：全部已过账凭证（POSTED）及其分录。"""
    from sqlalchemy import func as _f

    # 1) 关键指标
    v_all = db.query(models.VoucherDB).filter(
        models.VoucherDB.status == models.VoucherStatus.POSTED).all()
    total_vouchers = len(v_all)
    total_debit = db.query(_f.sum(models.VoucherEntry.debit)).join(
        models.VoucherDB, models.VoucherEntry.voucher_id == models.VoucherDB.id
    ).filter(models.VoucherDB.status == models.VoucherStatus.POSTED).scalar() or 0
    total_credit = db.query(_f.sum(models.VoucherEntry.credit)).join(
        models.VoucherDB, models.VoucherEntry.voucher_id == models.VoucherDB.id
    ).filter(models.VoucherDB.status == models.VoucherStatus.POSTED).scalar() or 0

    # 2) 月度借贷趋势（近12个月）
    today = datetime.now().date()
    start = date(today.year - 1, today.month, 1)
    month_rows = db.query(
        _f.strftime('%Y-%m', models.VoucherDB.voucher_date).label('ym'),
        _f.sum(models.VoucherEntry.debit).label('d'),
        _f.sum(models.VoucherEntry.credit).label('c'),
    ).join(
        models.VoucherDB, models.VoucherEntry.voucher_id == models.VoucherDB.id
    ).filter(
        models.VoucherDB.status == models.VoucherStatus.POSTED,
        models.VoucherDB.voucher_date >= start,
    ).group_by('ym').order_by('ym').all()
    monthly_trend = [{"month": r.ym, "debit": float(r.d or 0), "credit": float(r.c or 0)} for r in month_rows]

    # 3) 科目分布（按借方金额 Top 10）
    acct_rows = db.query(
        models.VoucherEntry.account_code,
        models.VoucherEntry.account_name,
        _f.sum(models.VoucherEntry.debit).label('d'),
    ).join(
        models.VoucherDB, models.VoucherEntry.voucher_id == models.VoucherDB.id
    ).filter(
        models.VoucherDB.status == models.VoucherStatus.POSTED,
        models.VoucherEntry.debit > 0,
    ).group_by(models.VoucherEntry.account_code, models.VoucherEntry.account_name
    ).order_by(_f.sum(models.VoucherEntry.debit).desc()).limit(10).all()
    account_dist = [{"code": r[0], "name": r[1], "amount": float(r[2] or 0)} for r in acct_rows]

    # 4) 凭证类型分布
    type_rows = db.query(
        models.VoucherDB.voucher_type,
        _f.count(models.VoucherDB.id),
    ).filter(
        models.VoucherDB.status == models.VoucherStatus.POSTED,
    ).group_by(models.VoucherDB.voucher_type).all()
    voucher_types = [{"type": (r[0] or "GENERAL"), "count": r[1]} for r in type_rows]

    # 5) 损益结构（收入 vs 支出大类）
    income_codes = ['6001', '6051', '6301']  # 主营收入、其他收入、营业外收入
    expense_codes = ['6401', '6402', '6601', '6602', '6603', '6701']  # 主营成本等
    income_total = db.query(_f.sum(models.VoucherEntry.credit)).join(
        models.VoucherDB, models.VoucherEntry.voucher_id == models.VoucherDB.id
    ).filter(
        models.VoucherDB.status == models.VoucherStatus.POSTED,
        models.VoucherEntry.account_code.in_(income_codes),
    ).scalar() or 0
    expense_total = db.query(_f.sum(models.VoucherEntry.debit)).join(
        models.VoucherDB, models.VoucherEntry.voucher_id == models.VoucherDB.id
    ).filter(
        models.VoucherDB.status == models.VoucherStatus.POSTED,
        models.VoucherEntry.account_code.in_(expense_codes),
    ).scalar() or 0

    # 6) 资产负债摘要
    asset_codes = ['1001', '1002', '1122', '1401', '1402', '1403', '1405', '1411', '1501']
    liability_codes = ['2202', '2203', '2211', '2221']
    asset_total = db.query(_f.sum(models.VoucherEntry.debit - models.VoucherEntry.credit)).join(
        models.VoucherDB, models.VoucherEntry.voucher_id == models.VoucherDB.id
    ).filter(
        models.VoucherDB.status == models.VoucherStatus.POSTED,
        models.VoucherEntry.account_code.in_(asset_codes),
    ).scalar() or 0
    liability_total = db.query(_f.sum(models.VoucherEntry.credit - models.VoucherEntry.debit)).join(
        models.VoucherDB, models.VoucherEntry.voucher_id == models.VoucherDB.id
    ).filter(
        models.VoucherDB.status == models.VoucherStatus.POSTED,
        models.VoucherEntry.account_code.in_(liability_codes),
    ).scalar() or 0

    return make_response(True, {
        "summary": {
            "total_vouchers": total_vouchers,
            "total_debit": float(total_debit or 0),
            "total_credit": float(total_credit or 0),
            "balanced": abs(float(total_debit or 0) - float(total_credit or 0)) < 0.01,
            "income_total": float(income_total or 0),
            "expense_total": float(expense_total or 0),
            "net_profit": round(float(income_total or 0) - float(expense_total or 0), 2),
            "asset_total": float(asset_total or 0),
            "liability_total": float(liability_total or 0),
            "equity_total": round(float(asset_total or 0) - float(liability_total or 0), 2),
        },
        "monthly_trend": monthly_trend,
        "account_distribution": account_dist,
        "voucher_types": voucher_types,
        "profit_loss_structure": {
            "income": float(income_total or 0),
            "expense": float(expense_total or 0),
        },
    }, "查询成功")


# ==================== 财务报表导入（Excel/HTML 解析） ====================

_STMT_TYPE_KEYWORDS = {
    "PL": ["营业总收入", "营业成本", "净利润", "利润总额", "营业利润"],
    "BS": ["流动资产", "货币资金", "负债合计", "所有者权益", "未分配利润", "总资产"],
    "CF": ["经营活动产生的现金流量净额", "投资活动产生的现金流量净额", "筹资活动产生的现金流量净额", "现金流量"],
}


def _detect_statement_type(item_names):
    """根据科目名称集合推断报表类型：PL 利润表 / BS 资产负债表 / CF 现金流量表"""
    names = set(n.replace(" ", "") for n in item_names if n)
    best_type, best_score = "PL", 0
    for t, kws in _STMT_TYPE_KEYWORDS.items():
        score = sum(1 for kw in kws if any(kw in n for n in names))
        if score > best_score:
            best_type, best_score = t, score
    return best_type


def _parse_num(v):
    """把字符串/数字转为 float，非数字返回 None"""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace(",", "").replace("，", "").strip()
    if s in ("", "--", "-", "—", "None", "null", "N/A"):
        return None
    # 去掉货币符号/千分位空格
    s = s.replace("¥", "").replace("￥", "").replace("元", "").replace(" ", "").replace("\u3000", "")
    try:
        return float(s)
    except Exception:
        return None


def _is_valid_period(p):
    """过滤非法报表期间：如东方财富 HTML 末尾混入的 19700101 等垃圾日期"""
    s = str(p).strip()
    if len(s) != 8 or not s.isdigit():
        return False
    y, m, d = int(s[:4]), int(s[4:6]), int(s[6:8])
    return 1990 <= y <= 2099 and 1 <= m <= 12 and 1 <= d <= 31


def _norm_period(p):
    """把各种期间格式规范为 8 位 YYYYMMDD：2024-12-31 / 2024/12/31 / 2024年12月31日 / 20241231 / 2024.12.31"""
    if p is None:
        return None
    if isinstance(p, (datetime, date)):
        return p.strftime("%Y%m%d")
    s = str(p).strip()
    if _is_valid_period(s):
        return s
    m = re.match(r"^(\d{4})[年\-/.\.](\d{1,2})[月\-/.](\d{1,2})日?$", s)
    if m:
        try:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if 1990 <= y <= 2099 and 1 <= mo <= 12 and 1 <= d <= 31:
                return f"{y:04d}{mo:02d}{d:02d}"
        except Exception:
            return None
    return None


def _norm_item_name(name):
    """规范科目名称：去掉序号前缀（一、二、1. ① 等）、『其中』『减』等装饰、行号与多余空白"""
    import re as _re
    s = str(name or "").strip()
    if not s:
        return ""
    # 去掉开头序号：一、 二、 1. 1、 ① （1） 等
    s = _re.sub(r"^[（(【\[]?\s*[一二三四五六七八九十百\d]+[、.．:：)）】\]]*\s*", "", s)
    # 去掉『其中：』『其中』『加：』『减：』
    s = _re.sub(r"^(其中[:：]?|[加减][:：]?|其中)", "", s)
    # 去掉多余空白
    s = s.replace(" ", "").replace("\u3000", "")
    return s


def _rows_to_statement(rows, unit_mult=1.0):
    """把二维表格行转换为统一结构（供 xlrd/openpyxl 读取的真实 .xls/.xlsx 使用）。
    自动跳过标题行（公司名/报表名/报表日期/单位），定位表头行提取期间列。
    unit_mult：金额单位换算为元的乘数（万元→×10000，千元→×1000）。"""
    # 清理空行
    clean = []
    for r in rows:
        if not r:
            continue
        row = [("" if c is None else str(c).strip()) for c in r]
        if any(row):
            clean.append(row)
    if not clean:
        return {"company": "", "statement_type": "PL", "periods": [], "items": []}

    # 定位表头行：第一行中包含 ≥1 个合法期间的 非空行
    header_idx = 0
    periods = []
    for i, r in enumerate(clean[:10]):
        pds = [_norm_period(p) for p in r[1:]]
        pds = [p for p in pds if p and _is_valid_period(p)]
        if pds:
            header_idx = i
            periods = pds
            break
    if not periods:
        return {"company": "", "statement_type": "PL", "periods": [], "items": []}

    # 期间去重保序
    seen = set()
    periods = [p for p in periods if not (p in seen or seen.add(p))]

    items = []
    item_names = []
    for r in clean[header_idx + 1:]:
        if len(r) < 2:
            continue
        name = _norm_item_name(r[0])
        if not name or name in ("单位", "报表日期"):
            continue
        values = {}
        for i, pd in enumerate(periods):
            if i + 1 < len(r):
                v = _parse_num(r[i + 1])
                if v is not None:
                    values[pd] = v * unit_mult
        item_names.append(name)
        items.append({"name": name, "values": values})
    stype = _detect_statement_type(item_names)
    return {"company": "", "statement_type": stype, "periods": periods, "items": items}


def _detect_unit(rows):
    """从表头附近识别金额单位，返回换算为元的乘数（万元→10000 / 千元→1000 / 元→1）。"""
    for r in rows[:8]:
        for c in r:
            s = str(c or "")
            if "单位" in s or "元" in s:
                if "万" in s:
                    return 10000.0
                if "千" in s:
                    return 1000.0
    return 1.0


def _parse_statements_from_content(content):
    """解析外部财务报表文件，返回解析出的全部报表列表（多工作表 Excel 每个表一张）。
    支持：东方财富导出的 HTML 假 .xls / 真实 .xls / .xlsx / CSV / 新浪等含多个工作表的 Excel。
    每个元素：{company, statement_type, periods, items:[{name, values:{period:amount}}]}
    """
    text = None
    for enc in ("utf-8", "gbk", "gb18030"):
        try:
            text = content.decode(enc)
            if "报表日期" in text or "单位" in text or "营业收入" in text or "营业总收入" in text:
                break
        except Exception:
            continue

    if text is not None:
        # HTML / 文本（制表符或逗号分隔）
        lines = text.replace("\r", "").split("\n")
        rows = []
        for ln in lines:
            ln = ln.strip()
            if not ln:
                continue
            ln = re.sub(r"<[^>]+>", "", ln)
            if "<table" in text.lower():
                # HTML 表格行内单元格以 >...</td> 分隔
                parts = [p.strip() for p in re.split(r"</td>|</th>", ln)]
                parts = [re.sub(r"<td[^>]*>|<th[^>]*>", "", p).strip() for p in parts]
            else:
                parts = [p.strip() for p in ln.split("\t")]
                if len(parts) < 2 and "," in ln:
                    parts = [p.strip() for p in ln.split(",")]
            # 保留空单元格以对齐列（东方财富等导出的行可能含空列，删除会错位）；
            # 仅去掉末尾的空单元格
            while parts and parts[-1].replace(" ", "") == "":
                parts = parts[:-1]
            if parts:
                rows.append(parts)
        return [_rows_to_statement(rows, _detect_unit(rows))]

    # 真实 .xlsx（openpyxl）：读取全部工作表，每个工作表解析为一张报表
    if content[:2] == b"PK":
        import io
        import openpyxl
        try:
            wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        except Exception:
            raise HTTPException(400, "无法解析 .xlsx 文件，请确认是标准财务报表")
        out = []
        for ws in wb.worksheets:
            rows = [[c.value for c in row] for row in ws.iter_rows()]
            p = _rows_to_statement(rows, _detect_unit(rows))
            if p["items"]:
                out.append(p)
        if not out:
            raise HTTPException(400, "无法从 .xlsx 中解析出报表科目数据，请确认是标准财务报表（利润表/资产负债表/现金流量表）")
        return out

    # 真实 .xls（xlrd）：读取全部工作表
    try:
        import xlrd
        wb = xlrd.open_workbook(file_contents=content)
        out = []
        for sh in wb.sheets():
            rows = [[sh.cell_value(r, c) for c in range(sh.ncols)] for r in range(sh.nrows)]
            p = _rows_to_statement(rows, _detect_unit(rows))
            if p["items"]:
                out.append(p)
        if not out:
            raise HTTPException(400, "无法解析该报表文件，请确认是标准财务报表（利润表/资产负债表/现金流量表）")
        return out
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(400, "无法解析该报表文件，请确认是标准财务报表（利润表/资产负债表/现金流量表）")


def _save_parsed_statement(db: Session, parsed: dict, filename: str):
    """把解析后的报表数据写入 imported_financials 表（同一账套的同类报表先清空旧数据）。
    返回响应数据 {company, statement_type, periods, saved_items, items}。"""
    # 取账套
    account_set_id = 1
    try:
        acct = db.query(models.AccountSet).order_by(models.AccountSet.id.asc()).first()
        if acct:
            account_set_id = acct.id
    except Exception:
        pass

    # 清空旧导入（同一账套的同类报表）
    db.query(models.ImportedFinancialStatement).filter(
        models.ImportedFinancialStatement.account_set_id == account_set_id,
        models.ImportedFinancialStatement.statement_type == parsed["statement_type"],
    ).delete(synchronize_session=False)

    company = ""
    m = re.search(r"([\u4e00-\u9fa5A-Za-z0-9]+?)\(?(\d{6})\)?(?:_.*|\.xlsx?|\.xls)?$", filename)
    if m:
        company = m.group(1)
    if not company:
        company = filename.rsplit(".", 1)[0]

    saved_items = 0
    for item in parsed["items"]:
        for pd, amt in item["values"].items():
            db.add(models.ImportedFinancialStatement(
                account_set_id=account_set_id,
                company_name=company,
                statement_type=parsed["statement_type"],
                period=pd,
                item_name=item["name"][:100],
                amount=Decimal(str(round(amt, 2))),
                unit="元",
            ))
            saved_items += 1
    db.commit()

    return {
        "company": company,
        "statement_type": parsed["statement_type"],
        "periods": parsed["periods"],
        "saved_items": saved_items,
        "items": parsed["items"][:30],
    }


@router.post("/import-statement", tags=["财务管理"])
async def import_financial_statement(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """导入外部财务报表（利润表/资产负债表/现金流量表）。
    支持：东方财富导出的 HTML 假 .xls、真实 .xls、.xlsx。
    解析关键科目后写入 imported_financials 表，供可视化与 AI 决策使用。"""
    content = await file.read()
    if not content:
        raise HTTPException(400, "上传文件为空")
    filename = (file.filename or "").strip()
    try:
        parsed_list = _parse_statements_from_content(content)
    except Exception as e:
        raise HTTPException(400, f"无法解析该报表文件：{str(e)}")
    valid = [p for p in parsed_list if p["items"]]
    if not valid:
        raise HTTPException(400, "未能从文件中解析出报表科目数据，请确认是标准财务报表（利润表/资产负债表/现金流量表）")

    results = [_save_parsed_statement(db, p, filename) for p in valid]
    data = {"imported": results}
    return make_response(True, data, f"成功导入 {len(results)} 张报表")


@router.post("/import-by-path", tags=["财务管理"])
def import_statement_by_path(body: dict, db: Session = Depends(get_db)):
    """从服务器本地文件地址导入财务报表（Excel/HTML/CSV）。
    请求体：{"path": "C:\\xxx\\资产负债表.xls"}。
    与文件上传共用同一套解析与入库逻辑，支持东方财富导出的 .xls / 真实 .xls / .xlsx / CSV。"""
    import os as _os
    path = (body.get("path") or "").strip()
    path = path.strip('"').strip("'") if path else ""
    if not path:
        return make_response(False, None, "请输入报表文件地址", "40001")
    if not _os.path.isfile(path):
        return make_response(False, None, f"文件不存在：{path}", "40002")
    filename = _os.path.basename(path)
    try:
        with open(path, "rb") as f:
            content = f.read()
    except Exception as e:
        return make_response(False, None, f"读取文件失败：{str(e)}", "40003")
    if not content:
        return make_response(False, None, "文件内容为空", "40003")
    try:
        parsed_list = _parse_statements_from_content(content)
    except Exception as e:
        return make_response(False, None, f"无法解析该报表文件：{str(e)}", "40002")
    valid = [p for p in parsed_list if p["items"]]
    if not valid:
        return make_response(False, None, "未能从文件中解析出报表科目数据，请确认是标准财务报表（利润表/资产负债表/现金流量表）", "40002")

    results = [_save_parsed_statement(db, p, filename) for p in valid]
    data = {"imported": results}
    return make_response(True, data, f"成功导入 {len(results)} 张报表")


@router.get("/imported-statements", tags=["财务管理"])
def get_imported_statements(db: Session = Depends(get_db)):
    """返回已导入的财务报表汇总：按报表类型/期间聚合关键科目，供前端可视化。"""
    account_set_id = 1
    try:
        acct = db.query(models.AccountSet).order_by(models.AccountSet.id.asc()).first()
        if acct:
            account_set_id = acct.id
    except Exception:
        pass
    rows = db.query(models.ImportedFinancialStatement).filter(
        models.ImportedFinancialStatement.account_set_id == account_set_id
    ).order_by(models.ImportedFinancialStatement.period.desc()).all()

    groups = {}
    for r in rows:
        key = r.statement_type
        if key not in groups:
            groups[key] = {"company": r.company_name, "periods": [], "items": {}}
        g = groups[key]
        if r.company_name:
            g["company"] = r.company_name
        if r.period not in g["periods"]:
            g["periods"].append(r.period)
        g["items"].setdefault(r.item_name, {})[r.period] = float(r.amount)

    return make_response(True, {"statements": groups}, "查询成功")


@router.post("/clear-imported", tags=["财务管理"])
def clear_imported_statements(db: Session = Depends(get_db)):
    """清除所有已导入的财务报表数据"""
    account_set_id = 1
    try:
        acct = db.query(models.AccountSet).order_by(models.AccountSet.id.asc()).first()
        if acct:
            account_set_id = acct.id
    except Exception:
        pass
    n = db.query(models.ImportedFinancialStatement).filter(
        models.ImportedFinancialStatement.account_set_id == account_set_id
    ).delete(synchronize_session=False)
    db.commit()
    return make_response(True, {"deleted": n}, "已清除")


# ==================== AI 财务分析 ====================

_DEFAULT_AI_BASE = "https://api.deepseek.com"
_DEFAULT_AI_MODEL = "deepseek-chat"


def _build_chat_url(base_url: str) -> str:
    """把用户填写的接口地址规范化为 OpenAI 兼容的 chat/completions 完整地址。
    兼容：https://xxx.com 、 https://xxx.com/v1 、 https://xxx.com/v1/chat/completions 等写法。"""
    b = (base_url or _DEFAULT_AI_BASE).strip().rstrip("/")
    if b.endswith("/chat/completions"):
        return b
    if b.endswith("/v1"):
        return b + "/chat/completions"
    return b + "/v1/chat/completions"


def _clean_ai_text(text):
    """清洗 AI 返回正文：推理模型可能把英文思考过程混入 content，
    若英文占比过高，截取第一个「中文主导段落」开始；确实没有中文则原样返回。"""
    import re as _re
    if not text:
        return text
    if len(_re.findall(r"[\u4e00-\u9fff]", text)) * 2 >= len(_re.findall(r"[A-Za-z]", text)):
        return text  # 中文占主导，无需清洗
    for _p in text.split("\n"):
        _pc = len(_re.findall(r"[\u4e00-\u9fff]", _p))
        _pe = len(_re.findall(r"[A-Za-z]", _p))
        if _pc >= 20 and _pc >= _pe:
            _i = text.find(_p)
            return text[_i:]  # 从第一个中文主导段落开始保留
    return text


def _get_ai_record(db: Session):
    """读取 AI 集成配置记录（api_type=deepseek，兼容名字模糊匹配）。"""
    try:
        return db.query(models.ApiIntegration).filter(
            (models.ApiIntegration.api_type == "deepseek") |
            (models.ApiIntegration.name.ilike("%deepseek%"))
        ).filter(models.ApiIntegration.status == "active").order_by(
            models.ApiIntegration.updated_at.desc()
        ).first()
    except Exception:
        return None


def _get_ai_config(db: Session) -> dict:
    """获取 AI 配置：优先数据库（页面配置，支持第三方中转），其次环境变量。
    返回 {api_key, base_url, model, source}。模型名存在 extra_config 的 JSON 里。"""
    import os, json as _json
    cfg = {"api_key": "", "base_url": _DEFAULT_AI_BASE, "model": _DEFAULT_AI_MODEL, "source": ""}
    rec = _get_ai_record(db)
    if rec and rec.api_key:
        cfg["api_key"] = rec.api_key.strip()
        cfg["base_url"] = (rec.base_url or _DEFAULT_AI_BASE).strip()
        model = _DEFAULT_AI_MODEL
        try:
            if rec.extra_config:
                model = _json.loads(rec.extra_config).get("model") or model
        except Exception:
            pass
        cfg["model"] = model
        cfg["source"] = "页面配置"
        return cfg
    env_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if env_key:
        cfg["api_key"] = env_key
        cfg["base_url"] = os.environ.get("AI_API_BASE", _DEFAULT_AI_BASE).strip()
        cfg["model"] = os.environ.get("AI_MODEL", _DEFAULT_AI_MODEL).strip()
        cfg["source"] = "环境变量"
    return cfg


@router.get("/ai-key-status", tags=["财务管理"])
def ai_key_status(db: Session = Depends(get_db)):
    """检查 AI 接口配置状态（只返回是否已配置、尾号、接口地址和模型名，不泄露完整Key）。"""
    cfg = _get_ai_config(db)
    key = cfg["api_key"]
    return make_response(True, {
        "configured": bool(key),
        "key_tail": ("****" + key[-6:]) if key else "",
        "base_url": cfg["base_url"],
        "model": cfg["model"],
        "chat_url": _build_chat_url(cfg["base_url"]),
        "source": cfg["source"],
    }, "查询成功")


@router.post("/ai-key", tags=["财务管理"])
def save_ai_key(body: dict, db: Session = Depends(get_db)):
    """保存 AI 接口配置（支持 DeepSeek 官网或 OpenAI 兼容的第三方中转，如 hua api）。
    请求体：{ "api_key": "sk-xxx", "base_url": "可选，默认官网", "model": "可选，默认deepseek-chat" }
    永久保存在集成配置表，重启不丢。"""
    key = (body.get("api_key") or "").strip()
    if not key:
        return make_response(False, None, "Key 不能为空", "40001")
    base_url = (body.get("base_url") or _DEFAULT_AI_BASE).strip() or _DEFAULT_AI_BASE
    model = (body.get("model") or _DEFAULT_AI_MODEL).strip() or _DEFAULT_AI_MODEL
    # upsert：更新已有的 AI 配置，没有则新建
    rec = db.query(models.ApiIntegration).filter(
        models.ApiIntegration.api_type == "deepseek"
    ).first()
    now = datetime.now()
    if rec:
        rec.api_key = key
        rec.base_url = base_url
        rec.extra_config = json.dumps({"model": model}, ensure_ascii=False)
        rec.status = "active"
        rec.updated_at = now
    else:
        rec = models.ApiIntegration(
            name="DeepSeek AI 财务分析",
            api_type="deepseek",
            base_url=base_url,
            auth_type="bearer",
            api_key=key,
            extra_config=json.dumps({"model": model}, ensure_ascii=False),
            status="active",
            created_at=now,
            updated_at=now,
        )
        db.add(rec)
    db.commit()
    return make_response(True, {
        "key_tail": "****" + key[-6:], "base_url": base_url, "model": model,
    }, "配置已保存")


@router.post("/ai-key/test", tags=["财务管理"])
def test_ai_key(body: dict = None, db: Session = Depends(get_db)):
    """用当前已保存的配置发一条最小请求，测试接口/Key/模型是否可用。
    请求体可空（测已保存配置），也可带 {api_key, base_url, model} 临时测试（不保存）。"""
    import json as _json, urllib.request, urllib.error
    if body:
        key = (body.get("api_key") or "").strip()
        base_url = (body.get("base_url") or _DEFAULT_AI_BASE).strip()
        model = (body.get("model") or _DEFAULT_AI_MODEL).strip()
    else:
        cfg = _get_ai_config(db)
        key, base_url, model = cfg["api_key"], cfg["base_url"], cfg["model"]
    if not key:
        return make_response(False, None, "尚未配置 Key", "40001")
    payload = _json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 16,
    }, ensure_ascii=False).encode("utf-8")
    url = _build_chat_url(base_url)
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = _json.loads(resp.read().decode("utf-8"))
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return make_response(True, {"ok": True, "reply": content[:50], "model": model, "url": url}, "连接成功")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")[:300]
        hint = ""
        if e.code == 401: hint = "（Key 无效）"
        elif e.code == 402: hint = "（账户余额不足）"
        elif e.code == 404: hint = "（接口地址或模型名不对）"
        return make_response(False, None, f"测试失败 HTTP {e.code}{hint}：{err_body}", "40002")
    except Exception as e:
        return make_response(False, None, f"连接异常：{str(e)}", "40003")


def _compute_financial_ratios(db: Session) -> dict:
    """计算关键财务比率与结构指标（基于全部已过账凭证的分录）。"""
    from sqlalchemy import func as _f

    # 各科目借贷发生额与余额
    rows = db.query(
        models.VoucherEntry.account_code,
        models.VoucherEntry.account_name,
        _f.sum(models.VoucherEntry.debit).label('d'),
        _f.sum(models.VoucherEntry.credit).label('c'),
    ).join(
        models.VoucherDB, models.VoucherEntry.voucher_id == models.VoucherDB.id
    ).filter(
        models.VoucherDB.status == models.VoucherStatus.POSTED,
    ).group_by(
        models.VoucherEntry.account_code, models.VoucherEntry.account_name
    ).all()

    # 按科目大类聚合（资产：借-贷；负债/权益/收入：贷-借；成本费用：借-贷）
    asset_codes = ['1001', '1002', '1122', '1401', '1402', '1403', '1405', '1411', '1501', '1601']
    liability_codes = ['2202', '2203', '2211', '2221', '2241']
    income_codes = ['6001', '6051', '6301']
    cost_codes = ['6401', '6402', '6601', '6602', '6603', '6701']
    inventory_codes = ['1403', '1405', '1401']  # 原材料/库存商品
    receivable_codes = ['1122']
    payable_codes = ['2202', '2211', '2221']
    cash_codes = ['1001', '1002']

    agg = {c: {'d': 0.0, 'c': 0.0, 'name': ''} for c in
           set(asset_codes + liability_codes + income_codes + cost_codes)}
    for r in rows:
        code = r[0] or ''
        if code in agg:
            agg[code]['d'] += float(r[2] or 0)
            agg[code]['c'] += float(r[3] or 0)
            agg[code]['name'] = r[1] or agg[code]['name']

    def _sum(codes, sign='asset'):
        t = 0.0
        for c in codes:
            if c in agg:
                a = agg[c]
                t += (a['d'] - a['c']) if sign == 'asset' else (a['c'] - a['d'])
        return round(t, 2)

    total_asset = _sum(asset_codes, 'asset')
    current_asset = _sum(['1001', '1002', '1122', '1401', '1402', '1403', '1405', '1411'], 'asset')
    total_liability = _sum(liability_codes, 'liab')
    current_liability = _sum(['2202', '2203', '2211', '2221', '2241'], 'liab')
    equity = round(total_asset - total_liability, 2)
    income = _sum(income_codes, 'liab')
    cost = _sum(cost_codes, 'asset')
    cogs = _sum(['6401', '6402'], 'asset')  # 主营业务成本等直接成本
    profit = round(income - cost, 2)
    inventory = _sum(inventory_codes, 'asset')
    receivable = _sum(receivable_codes, 'asset')
    payable = _sum(payable_codes, 'liab')
    cash = _sum(cash_codes, 'asset')

    # 补充 29 项核心指标所需的衍生值
    period_exp = _sum(['6601', '6602', '6603'], 'asset')    # 销售/管理/财务费用
    fin_exp = _sum(['6603'], 'asset')                        # 财务费用（近似利息支出）
    operating_profit = round(income - cogs - period_exp, 2)  # 近似营业利润（未单列税金及附加）
    non_current_asset = round(total_asset - current_asset, 2)

    def _safe(n, d):
        return round(n / d, 4) if d else None

    return {
        'total_asset': total_asset, 'current_asset': current_asset,
        'total_liability': total_liability, 'current_liability': current_liability,
        'equity': equity, 'income': income, 'cost': cost, 'profit': profit,
        'inventory': inventory, 'receivable': receivable, 'payable': payable, 'cash': cash,
        'cogs': cogs, 'period_exp': period_exp, 'fin_exp': fin_exp,
        'operating_profit': operating_profit, 'non_current_asset': non_current_asset,
        'debt_ratio': _safe(total_liability, total_asset),          # 资产负债率
        'current_ratio': _safe(current_asset, current_liability),   # 流动比率
        'gross_margin': _safe(income - cogs, income),              # 毛利率（收入-主营成本）
        'net_margin': _safe(profit, income),                        # 净利率
        'roe': _safe(profit, equity),                               # 净资产收益率
        'receivable_ratio': _safe(receivable, income),              # 应收占收入比
        'inventory_ratio': _safe(inventory, income),                # 存货占收入比
    }


@router.get("/decision-insights", tags=["财务管理"])
def get_decision_insights(db: Session = Depends(get_db)):
    """财务决策引擎：返回结构化指标、健康度评分与规则化预警（不依赖 AI，本地可算）。
    供前端展示「本企业财务概览 + 决策建议」基础卡片。"""
    from sqlalchemy import func as _f

    ratios = _compute_financial_ratios(db)
    r = ratios
    alerts = []
    score = 100

    # 规则 1：资产负债率
    if r['total_asset'] > 0:
        dr = r['debt_ratio'] or 0
        if dr > 0.7:
            alerts.append({'level': 'high', 'item': '资产负债率', 'value': f"{dr*100:.1f}%",
                           'msg': '负债率偏高（>70%），偿债压力大，建议控制新增负债、加快回款'})
            score -= 20
        elif dr > 0.5:
            alerts.append({'level': 'mid', 'item': '资产负债率', 'value': f"{dr*100:.1f}%",
                           'msg': '负债率中等（50%~70%），建议关注有息负债规模'})
            score -= 8
        else:
            alerts.append({'level': 'ok', 'item': '资产负债率', 'value': f"{dr*100:.1f}%",
                           'msg': '负债率健康（<50%），资产对负债的保障程度较好'})

    # 规则 2：流动比率
    cr = r['current_ratio']
    if cr is not None:
        if cr < 1:
            alerts.append({'level': 'high', 'item': '流动比率', 'value': f"{cr:.2f}",
                           'msg': '流动比率<1，短期偿债能力不足，建议补充流动资金或延缓大额支出'})
            score -= 15
        elif cr < 1.5:
            alerts.append({'level': 'mid', 'item': '流动比率', 'value': f"{cr:.2f}",
                           'msg': '流动比率偏低（1~1.5），建议保持现金储备'})
            score -= 5
        else:
            alerts.append({'level': 'ok', 'item': '流动比率', 'value': f"{cr:.2f}",
                           'msg': '流动比率良好（>1.5），短期偿债能力充足'})

    # 规则 3：毛利率
    gm = r['gross_margin']
    if gm is not None:
        if gm < 0.15:
            alerts.append({'level': 'high', 'item': '毛利率', 'value': f"{gm*100:.1f}%",
                           'msg': '毛利率偏低（<15%），建议优化采购成本/BOM 或调整报价策略'})
            score -= 15
        elif gm < 0.3:
            alerts.append({'level': 'mid', 'item': '毛利率', 'value': f"{gm*100:.1f}%",
                           'msg': '毛利率中等（15%~30%），可通过降本增效率提升'})
            score -= 5
        else:
            alerts.append({'level': 'ok', 'item': '毛利率', 'value': f"{gm*100:.1f}%",
                           'msg': '毛利率良好（>30%），产品盈利能力较强'})

    # 规则 4：应收占收入比
    rr = r['receivable_ratio']
    if rr is not None and rr > 0.5:
        alerts.append({'level': 'mid', 'item': '应收账款占收入比', 'value': f"{rr*100:.1f}%",
                       'msg': '应收占收入比偏高（>50%），资金被占用，建议收紧账期、加强催收'})
        score -= 10

    # 规则 5：存货占收入比
    ir = r['inventory_ratio']
    if ir is not None and ir > 0.5:
        alerts.append({'level': 'mid', 'item': '存货占收入比', 'value': f"{ir*100:.1f}%",
                       'msg': '存货占收入比偏高（>50%），建议排查呆滞库存、按需采购'})
        score -= 8

    # 规则 6：现金余额
    if r['cash'] < 0:
        alerts.append({'level': 'high', 'item': '货币资金', 'value': f"{r['cash']:.2f}",
                       'msg': '账面货币资金为负，存在资金链风险，请核对银行流水与凭证'})
        score -= 20

    # 规则 7：存货/成本科目负余额（多为领料/结转未同步导致）
    if r['inventory'] < 0:
        alerts.append({'level': 'mid', 'item': '存货净额', 'value': f"{r['inventory']:.2f}",
                       'msg': '原材料/库存商品出现负余额，说明出库结转大于入库，建议补录采购入库或核对领料单'})
        score -= 8

    # 规则 8：应收账款占比虽低但收入全部已回款
    if r['income'] > 0 and r['receivable'] == 0 and r['cash'] > 0:
        alerts.append({'level': 'ok', 'item': '回款情况', 'value': '应收已结清',
                       'msg': '应收账款余额为 0，销售收入已全额回款，现金流质量好'})

    score = max(0, min(100, score))
    grade = 'A（优秀）' if score >= 90 else 'B（良好）' if score >= 75 else 'C（一般）' if score >= 60 else 'D（需关注）'

    return make_response(True, {
        'ratios': {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()},
        'health_score': score,
        'health_grade': grade,
        'alerts': alerts,
    }, "查询成功")


# ============================================================
# 29 项核心财务指标 + 8 维分析框架（财务报表分析指南）
# ============================================================
def _compute_indicator_suite(db: Session) -> dict:
    """计算财务报表分析指南中的 29 项核心财务指标与 8 维分析框架。
    数据来源：当前账套已过账凭证（主）；已导入的利润表/资产负债表/现金流量表（补充现金流、期初与上期数据）。"""
    r = _compute_financial_ratios(db)

    # ---- 加载已导入财务报表（PL/BS/CF），期间倒序 ----
    account_set_id = 1
    try:
        _acct = db.query(models.AccountSet).order_by(models.AccountSet.id.asc()).first()
        if _acct:
            account_set_id = _acct.id
    except Exception:
        pass
    _rows = db.query(models.ImportedFinancialStatement).filter(
        models.ImportedFinancialStatement.account_set_id == account_set_id
    ).order_by(models.ImportedFinancialStatement.period.desc()).all()

    _groups = {}   # type -> {'periods':[], 'items':{name:{period:amount}}}
    _company = ''
    for _row in _rows:
        _g = _groups.setdefault(_row.statement_type, {'periods': [], 'items': {}})
        if _row.period not in _g['periods']:
            _g['periods'].append(_row.period)
        _g['items'].setdefault(_row.item_name, {})[_row.period] = float(_row.amount)
        if not _company and _row.company_name:
            _company = _row.company_name

    def _find(typ, *kws):
        _g = _groups.get(typ)
        if not _g:
            return {}
        # 优先精确名称，其次「合计/总计」类汇总科目，避免误取明细子项（如「其他流动资产」）
        _best, _best_s = None, -1
        for _n, _per in _g['items'].items():
            for _kw in kws:
                if _kw in _n:
                    _s = 10 if _n == _kw else 0
                    if _n.endswith('合计') or _n.endswith('总计'):
                        _s += 5
                    if len(_n) - len(_kw) <= 4:
                        _s += 3
                    if _s > _best_s:
                        _best_s, _best = _s, _per
        return _best or {}

    def _latest(_per):
        if not _per:
            return None
        for _p in _per:
            return _per[_p]
        return None

    def _prev(_per):
        _ks = list(_per or {})
        if len(_ks) >= 2:
            return _per[_ks[1]]
        return None

    def _avg2(_cur, _pv):
        if _cur is None and _pv is None:
            return None
        if _cur is None:
            return _pv
        if _pv is None:
            return _cur
        return (_cur + _pv) / 2

    def _cf_net(_kw):
        _per = _find('CF', _kw + '活动产生的现金流量净额', _kw + '活动现金流量净额', _kw + '现金净流量')
        if _per:
            return _latest(_per)
        for _n, _per2 in (_groups.get('CF', {}).get('items', {}) or {}).items():
            if _kw in _n and '现金' in _n and ('净额' in _n or '净流量' in _n) and '流入' not in _n and '流出' not in _n:
                return _latest(_per2)
        return None

    # ---- 原始值：单一数据源（优先已导入报表，无导入则用当前账套），绝不混用 ----
    _use_imp = bool(_rows)
    if _use_imp:
        total_asset = _latest(_find('BS', '资产总计', '总资产'))
        total_liability = _latest(_find('BS', '负债合计'))
        equity = _latest(_find('BS', '所有者权益', '股东权益'))
        if equity is None and total_asset is not None and total_liability is not None:
            equity = total_asset - total_liability
        current_asset = _latest(_find('BS', '流动资产'))
        current_liability = _latest(_find('BS', '流动负债'))
        inventory = _latest(_find('BS', '存货'))
        receivable = _latest(_find('BS', '应收账款'))
        cash = _latest(_find('BS', '货币资金'))
        income = _latest(_find('PL', '营业收入', '主营业务收入'))
        cogs = _latest(_find('PL', '营业成本', '主营业务成本'))
        profit = _latest(_find('PL', '净利润'))
        operating_profit = _latest(_find('PL', '营业利润'))
        total_profit = _latest(_find('PL', '利润总额'))
        fin_exp = _latest(_find('PL', '财务费用')) or 0.0
        non_current_asset = _latest(_find('BS', '非流动资产'))
        if non_current_asset is None and total_asset is not None and current_asset is not None:
            non_current_asset = total_asset - current_asset
    else:
        total_asset = r['total_asset']
        total_liability = r['total_liability']
        equity = r['equity']
        current_asset = r['current_asset']
        current_liability = r['current_liability']
        inventory = r['inventory']
        receivable = r['receivable']
        cash = r['cash']
        income = r['income']
        cogs = r.get('cogs') or 0.0
        profit = r['profit']
        operating_profit = r.get('operating_profit') or 0.0
        total_profit = r.get('total_profit') or r['profit']
        fin_exp = r.get('fin_exp') or 0.0
        non_current_asset = r.get('non_current_asset') or (total_asset - (current_asset or 0.0))

    op_cashflow = _cf_net('经营')
    inv_cashflow = _cf_net('投资')
    fin_cashflow = _cf_net('筹资')
    cash_sales = _latest(_find('CF', '销售商品、提供劳务收到的现金', '销售收到现金'))

    _safe = lambda n, d: (n / d) if (n is not None and d not in (None, 0)) else None
    _sub = lambda a, b: (a - b) if (a is not None and b is not None) else None

    # ---- 平均与期初值 ----
    _pr = lambda t, *kws: _prev(_find(t, *kws))
    avg_receivable = _avg2(receivable, _pr('BS', '应收账款'))
    avg_inventory = _avg2(inventory, _pr('BS', '存货'))
    avg_current_asset = _avg2(current_asset, _pr('BS', '流动资产'))
    avg_total_asset = _avg2(total_asset, _pr('BS', '资产总计', '总资产'))
    avg_equity = _avg2(equity, _pr('BS', '所有者权益', '股东权益'))
    avg_non_current = _avg2(non_current_asset, _pr('BS', '非流动资产'))
    wc = (current_asset - current_liability) if (current_asset is not None and current_liability is not None) else None
    _pca, _pcl = _pr('BS', '流动资产'), _pr('BS', '流动负债')
    prev_wc = (_pca - _pcl) if (_pca is not None and _pcl is not None) else None
    avg_wc = _avg2(wc, prev_wc)
    prev_income = _pr('PL', '营业收入', '主营业务收入')
    prev_profit = _pr('PL', '净利润')
    prev_op = _pr('PL', '营业利润')
    prev_equity = _pr('BS', '所有者权益', '股东权益')
    prev_asset = _pr('BS', '资产总计', '总资产')

    # ---- 数值格式化与指标构造 ----
    def _fmt_money(v):
        if v is None:
            return '—'
        a = abs(v)
        if a >= 1e8:
            return f"¥{v/1e8:,.2f} 亿"
        if a >= 1e4:
            return f"¥{v/1e4:,.2f} 万"
        return f"¥{v:,.2f}"

    def _fmt_pct(v):
        return f"{v*100:.1f}%" if v is not None else '—'

    def _fmt_ratio(v):
        return f"{v:.2f}" if v is not None else '—'

    def _fmt_times(v):
        return f"{v:.2f} 次" if v is not None else '—'

    def _ind(key, name, formula, value, kind, reference, interpretation, status, note=None):
        _disp = {'pct': _fmt_pct, 'times': _fmt_times, 'money': _fmt_money}.get(kind, _fmt_ratio)
        return {
            'key': key, 'name': name, 'formula': formula,
            'value': (round(value, 6) if isinstance(value, float) else value),
            'display': _disp(value), 'unit': kind,
            'reference': reference, 'interpretation': interpretation,
            'status': status, 'note': note,
        }

    def _st_thr(v, ok_ge, warn_ge, inv=False):
        """越大越好（inv=False）或越小越好（inv=True）时的三段式状态。None→na"""
        if v is None:
            return 'na'
        if not inv:
            if v >= ok_ge:
                return 'ok'
            if v >= warn_ge:
                return 'warn'
            return 'bad'
        if v <= ok_ge:
            return 'ok'
        if v <= warn_ge:
            return 'warn'
        return 'bad'

    def _st_pos(v):
        if v is None:
            return 'na'
        return 'ok' if v > 0 else 'bad'

    def _st_grow(v):
        if v is None:
            return 'na'
        if v > 0:
            return 'ok'
        if v == 0:
            return 'warn'
        return 'bad'

    # ============ 一、偿债能力 ============
    cr = _safe(current_asset, current_liability)
    qr = _safe((current_asset - inventory) if (current_asset is not None and inventory is not None) else None, current_liability)
    car = _safe(cash, current_liability)
    dr = _safe(total_liability, total_asset)
    er_ = _safe(total_liability, equity)
    em = _safe(total_asset, equity)
    if fin_exp in (None, 0):
        ic, ic_note, ic_st = None, '本期无利息/财务费用支出', 'ok'
    else:
        ic = _safe((total_profit + fin_exp) if total_profit is not None else None, fin_exp)
        ic_note = None
        ic_st = 'ok' if (ic is not None and ic >= 3) else ('warn' if (ic is not None and ic >= 1) else 'bad')
    cf_ic = _safe(op_cashflow, fin_exp) if fin_exp not in (None, 0) else None
    cf_debt = _safe(op_cashflow, total_liability)

    _solvency = [
        _ind('net_wc', '净营运资本', '流动资产 - 流动负债', wc, 'money', '越大越安全',
             '短期偿债的安全边际，数值越大越不容易资金链断裂',
             'ok' if (wc is not None and wc > 0) else ('bad' if wc is not None else 'na')),
        _ind('current_ratio', '流动比率', '流动资产 ÷ 流动负债', cr, 'ratio', '标准≈2，底线 1',
             '衡量变现还债的能力', _st_thr(cr, 2, 1)),
        _ind('quick_ratio', '速动比率', '(流动资产 - 存货) ÷ 流动负债', qr, 'ratio', '标准≈1',
             '去掉难卖的存货，比流动比率更严苛', _st_thr(qr, 1, 0.5)),
        _ind('cash_ratio', '现金比率', '(货币资金 + 交易性金融资产) ÷ 流动负债', car, 'ratio', '>0.2 才安心',
             '手里的现金够不够马上还债', _st_thr(car, 0.2, 0.1)),
        _ind('debt_ratio', '资产负债率', '总负债 ÷ 总资产 ×100%', dr, 'pct', '红线 50%~70%',
             '借钱经营的程度，越低财务风险越小', _st_thr(dr, 0.5, 0.7, True)),
        _ind('equity_ratio', '产权比率', '总负债 ÷ 股东权益', er_, 'ratio', '一般 <1',
             '债主出的钱是股东出钱的多少倍', _st_thr(er_, 1, 1.5, True),
             None if equity else '所有者权益非正，无法计算'),
        _ind('equity_multiplier', '权益乘数', '总资产 ÷ 股东权益', em, 'ratio', '越大杠杆越高',
             '杠杆倍数，越大说明借钱越多风险越高', _st_thr(em, 2, 3, True),
             None if equity else '所有者权益非正，无法计算'),
        _ind('interest_coverage', '利息保障倍数', 'EBIT ÷ 利息支出（财务费用近似）', ic, 'times', '必须 >1',
             '赚的钱够不够还利息，否则就是在给银行打工', ic_st, ic_note),
        _ind('cf_interest_coverage', '现金流量利息保障倍数', '经营活动现金流量 ÷ 利息费用', cf_ic, 'times', '>1 越硬核',
             '用真金白银还利息的能力', _st_thr(cf_ic, 1, 0),
             '需导入现金流量表' if cf_ic is None else None),
        _ind('cf_debt_ratio', '经营现金流量债务比', '经营活动现金流量 ÷ 债务总额 ×100%', cf_debt, 'pct', '靠主业几年还清债务',
             '靠主业赚的现金覆盖全部债务的能力', 'ok' if (cf_debt is not None and cf_debt > 0) else ('bad' if cf_debt is not None else 'na'),
             '需导入现金流量表' if cf_debt is None else None),
    ]

    # ============ 二、营运能力 ============
    v_rtr = _safe(income, avg_receivable)
    v_itr = _safe(cogs, avg_inventory)
    v_cat = _safe(income, avg_current_asset)
    v_wct = _safe(income, avg_wc)
    v_nct = _safe(income, avg_non_current)
    v_tat = _safe(income, avg_total_asset)

    _turnover = [
        _ind('receivable_turnover', '应收账款周转率', '销售收入 ÷ 平均应收账款', v_rtr, 'times', '工业>4 次，商贸>6 次',
             '催账快不快，次数越高越好', _st_thr(v_rtr, 4, 2),
             ('应收账款为 0，周转极快' if avg_receivable in (None, 0) else None)),
        _ind('inventory_turnover', '存货周转率', '营业成本 ÷ 平均存货', v_itr, 'times', '越高越抢手',
             '货卖得快不快，次数越高说明产品越抢手', _st_thr(v_itr, 4, 2),
             ('存货为 0，无可比库存' if avg_inventory in (None, 0) else None)),
        _ind('current_asset_turnover', '流动资产周转率', '销售收入 ÷ 平均流动资产', v_cat, 'times', '流动资金使用效率',
             '流动资金的使用效率', _st_thr(v_cat, 1, 0.5)),
        _ind('wc_turnover', '净营运资本周转率', '销售收入 ÷ 平均净营运资本', v_wct, 'times', '营运资金每圈收入',
             '营运资金每转一圈能带来多少收入', _st_thr(v_wct, 1, 0),
             ('净营运资本为 0 或负数，无法计算' if (avg_wc is None or avg_wc <= 0) else None)),
        _ind('non_current_turnover', '非流动资产周转率', '销售收入 ÷ 平均非流动资产', v_nct, 'times', '重资产有无闲置',
             '厂房设备这些重资产有没有闲置浪费', _st_thr(v_nct, 1, 0.5),
             ('无非流动资产' if (avg_non_current is None or avg_non_current <= 0) else None)),
        _ind('total_asset_turnover', '总资产周转率', '销售收入 ÷ 平均总资产', v_tat, 'times', '1 块钱资产做多大生意',
             '投入 1 块钱资产能做多大的生意，体现整体管理水平', _st_thr(v_tat, 0.5, 0.2)),
    ]

    # ============ 三、盈利能力 ============
    v_gm = _safe(_sub(income, cogs), income)
    v_nm = _safe(profit, income)
    v_roa = _safe(profit, avg_total_asset)
    v_roe = _safe(profit, avg_equity)
    v_roic = _safe((total_profit + fin_exp) if (total_profit is not None and fin_exp is not None) else None, avg_total_asset)
    v_om = _safe(operating_profit, income)
    v_acr = _safe(op_cashflow, avg_total_asset)

    _profit = [
        _ind('net_margin', '销售净利率', '净利润 ÷ 销售收入 ×100%', v_nm, 'pct', '每 100 元收入剩多少利润',
             '薄利多销还是厚利少销', _st_pos(v_nm)),
        _ind('roa', '资产净利率（ROA）', '净利润 ÷ 总资产 ×100%', v_roa, 'pct', '资产综合利用回报率',
             '资产的综合利用回报率', _st_pos(v_roa)),
        _ind('roe', '净资产收益率（ROE）', '净利润 ÷ 股东权益 ×100%', v_roe, 'pct', '巴菲特最爱，越高越好',
             '衡量股东投的钱回本快不快', _st_pos(v_roe),
             None if avg_equity else '所有者权益非正，无法计算'),
        _ind('roic', '总资产报酬率', '(利润总额 + 利息支出) ÷ 平均资产 ×100%', v_roic, 'pct', '债权人+股东总回报',
             '把债权人和股东看作一个整体，看企业的总回报', _st_pos(v_roic)),
        _ind('operating_margin', '营业利润率', '营业利润 ÷ 营业收入 ×100%', v_om, 'pct', '剔除意外收入，只看主业',
             '剔除「彩票中奖」等意外收入，只看主业强不强', _st_pos(v_om)),
        _ind('asset_cash_return', '全部资产现金回收率', '经营现金净流量 ÷ 平均资产 ×100%', v_acr, 'pct', '资产变现金能力',
             '资产变成现金的能力', _st_pos(v_acr),
             '需导入现金流量表' if v_acr is None else None),
    ]

    # ============ 四、盈利质量 ============
    v_pcr = _safe(op_cashflow, profit)
    v_scr = _safe(cash_sales, income)

    _quality = [
        _ind('profit_cash_ratio', '盈利现金比率', '经营现金净流量 ÷ 净利润 ×100%', v_pcr, 'pct', '持续<1 警惕造假/回款难',
             '利润的含金量，有现金流的利润才是硬道理', _st_thr(v_pcr, 1, 0),
             ('需导入现金流量表' if op_cashflow is None else ('净利润为 0，无法计算' if not profit else None))),
        _ind('sales_cash_ratio', '销售收现比率', '销售收到现金 ÷ 主营业务收入 ×100%', v_scr, 'pct', '收到钱还是收到白条',
             '卖货是收到了钱，还是收了一堆白条（应收账款）', _st_thr(v_scr, 0.9, 0.7),
             '需导入现金流量表' if v_scr is None else None),
    ]

    # ============ 五、发展能力 ============
    v_eg = _safe(_sub(equity, prev_equity), prev_equity)
    v_ag = _safe(_sub(total_asset, prev_asset), prev_asset)
    v_sg = _safe(_sub(income, prev_income), prev_income)
    v_pg = _safe(_sub(profit, prev_profit), prev_profit)
    v_og = _safe(_sub(operating_profit, prev_op), prev_op)

    _growth = [
        _ind('equity_growth', '股东权益增长率', '本期权益增加 ÷ 期初权益 ×100%', v_eg, 'pct', '净家底增厚速度',
             '企业净家底的增厚速度', _st_grow(v_eg), '需导入两期报表（上期数据）' if v_eg is None else None),
        _ind('asset_growth', '资产增长率', '本期资产增加 ÷ 期初资产 ×100%', v_ag, 'pct', '规模扩张快慢',
             '企业规模扩张得有多快', _st_grow(v_ag), '需导入两期报表（上期数据）' if v_ag is None else None),
        _ind('sales_growth', '销售增长率', '本期收入增加 ÷ 上期收入 ×100%', v_sg, 'pct', '成长性第一指标',
             '市场份额有没有变大', _st_grow(v_sg), '需导入两期报表（上期数据）' if v_sg is None else None),
        _ind('profit_growth', '净利润增长率', '本期净利增加 ÷ 上期净利 ×100%', v_pg, 'pct', '比去年赚更多',
             '不仅要赚，还要比去年赚得更多', _st_grow(v_pg), '需导入两期报表（上期数据）' if v_pg is None else None),
        _ind('op_growth', '营业利润增长率', '本期营业利润增加 ÷ 上期营业利润 ×100%', v_og, 'pct', '主业盈利加速度',
             '主业盈利能力的加速度', _st_grow(v_og), '需导入两期报表（上期数据）' if v_og is None else None),
    ]

    # ============ 8 维分析框架 ============
    _npm = _safe(profit, income)
    _tat = _safe(income, total_asset)
    _em = _safe(total_asset, equity)
    _roe2 = _safe(profit, equity)
    _eq_chg = (equity - prev_equity) if (equity is not None and prev_equity is not None) else None

    _framework = [
        {'key': 'company', 'name': '公司概况', 'focus': '历史沿革、业务范围、市场地位（成立/上市时间、产品结构）',
         'value': f"{_company or '本企业'} · 数据源：{'已导入报表' if _rows else '当前账套凭证'}"},
        {'key': 'industry', 'name': '行业与政策', 'focus': '行业增长率、市场格局、政策支持',
         'value': '需结合所在行业信息人工补充判断'},
        {'key': 'core', 'name': '财报核心数据', 'focus': '三大报表整体规模与结构（资产负债率、净利润、经营现金流）',
         'value': f"资产负债率 {_fmt_pct(dr)} · 净利润 {_fmt_money(profit)} · 经营现金流 {_fmt_money(op_cashflow)}"},
        {'key': 'finance', 'name': '财务专项分析', 'focus': '资本结构、资产配置、偿债压力（资产负债率、流动比率、速动比率）',
         'value': f"资产负债率 {_fmt_pct(dr)} · 流动比率 {_fmt_ratio(cr)} · 速动比率 {_fmt_ratio(qr)}"},
        {'key': 'pl', 'name': '利润表分析', 'focus': '收入质量、利润构成及趋势（营收增长率、毛利率、净利率）',
         'value': f"营收增长率 {_fmt_pct(v_sg)} · 毛利率 {_fmt_pct(v_gm)} · 净利率 {_fmt_pct(v_nm)}"},
        {'key': 'cf', 'name': '现金流分析', 'focus': '经营、投资、筹资三大活动流向',
         'value': f"经营 {_fmt_money(op_cashflow)} · 投资 {_fmt_money(inv_cashflow)} · 筹资 {_fmt_money(fin_cashflow)}"},
        {'key': 'tie', 'name': '勾稽关系', 'focus': '净利润与权益变动、现金流匹配度',
         'value': f"净利润 {_fmt_money(profit)} · 权益变动 {_fmt_money(_eq_chg)} · 盈利现金比率 {_fmt_pct(v_pcr)}"},
        {'key': 'dupont', 'name': '杜邦分析', 'focus': 'ROE = 销售净利率 × 总资产周转率 × 权益乘数',
         'value': f"ROE {_fmt_pct(_roe2)} = {_fmt_pct(_npm)} × {_fmt_times(_tat)} × {_fmt_ratio(_em)}"},
    ]

    return {
        'company': _company,
        'period_label': _rows[0].period if _rows else '当前账套',
        'source': ('已导入财务报表' if _use_imp else '当前账套凭证'),
        'has_ledger': bool(r['total_asset'] or r['income']),
        'has_imported': bool(_rows),
        'framework': _framework,
        'categories': [
            {'key': 'solvency', 'name': '偿债能力', 'desc': '看企业安不安全', 'items': _solvency},
            {'key': 'turnover', 'name': '营运能力', 'desc': '看管理效率高不高', 'items': _turnover},
            {'key': 'profit', 'name': '盈利能力', 'desc': '看赚钱行不行', 'items': _profit},
            {'key': 'quality', 'name': '盈利质量', 'desc': '看利润真不真', 'items': _quality},
            {'key': 'growth', 'name': '发展能力', 'desc': '看未来强不强', 'items': _growth},
        ],
    }


@router.get("/indicators", tags=["财务管理"])
def get_finance_indicators(db: Session = Depends(get_db)):
    """29 项核心财务指标 + 8 维分析框架（账套自动计算，导入报表补充现金流与期初数据）。"""
    try:
        return make_response(True, _compute_indicator_suite(db), "查询成功")
    except Exception as e:
        return make_response(False, None, f"指标计算失败：{str(e)}", "40003")


@router.get("/cost-behavior", tags=["财务管理"])
def cost_behavior_analysis(fixed_kw: Optional[str] = None, variable_kw: Optional[str] = None,
                           mixed_kw: Optional[str] = None, db: Session = Depends(get_db)):
    """成本性态分析：按性态将成本/费用科目划分为固定/变动/混合成本，并计算本量利(CVP)指标。
    数据源：优先当前账套凭证（科目代码 5* 成本类、6* 损益类）；凭证无成本数据时回退到已导入利润表。
    关键词规则可用 fixed_kw/variable_kw/mixed_kw 覆盖（逗号分隔），用于匹配科目名称。"""
    DEFAULT_MIXED = "制造费用,电费,水费,维护,维修,保养,燃气,动力,车间"
    DEFAULT_FIXED = "折旧,摊销,房租,租金,利息,保险,物业,办公,培训,差旅,通讯,审计,咨询,工资,薪酬,社保,公积金,福利,税费,税金"
    DEFAULT_VAR = "材料,原料,直接人工,计件,燃料,运输,运费,包装,佣金,提成,加工,委外,成本,水电"
    fkw = [x.strip() for x in (fixed_kw or DEFAULT_FIXED).split(",") if x.strip()]
    vkw = [x.strip() for x in (variable_kw or DEFAULT_VAR).split(",") if x.strip()]
    mkw = [x.strip() for x in (mixed_kw or DEFAULT_MIXED).split(",") if x.strip()]

    def classify(nm):
        if any(k in nm for k in mkw):
            return "混合"
        if any(k in nm for k in fkw):
            return "固定"
        if any(k in nm for k in vkw):
            return "变动"
        return "其他"

    from sqlalchemy import text as _text
    monthly = {}    # ym -> 各性态金额 + 收入
    acct_meta = {}  # 科目名 -> {code, cat}
    acct_series = {}  # 科目名 -> {ym: 金额}

    def _month(ym):
        return monthly.setdefault(ym, {"ym": ym, "total": 0.0, "fixed": 0.0, "variable": 0.0,
                                       "mixed": 0.0, "other": 0.0, "revenue": 0.0})

    def _add_account(nm, code, cat, ym, amt):
        meta = acct_meta.setdefault(nm, {"code": code, "cat": cat})
        s = acct_series.setdefault(nm, {})
        s[ym] = round(s.get(ym, 0.0) + amt, 2)

    try:
        rows = db.execute(_text(
            "SELECT substr(v.voucher_date,1,7) AS ym, e.account_code, e.account_name, "
            "COALESCE(e.debit,0) AS debit, COALESCE(e.credit,0) AS credit "
            "FROM voucher_entries e JOIN vouchers v ON v.id=e.voucher_id "
            "WHERE e.debit IS NOT NULL OR e.credit IS NOT NULL "
            "ORDER BY v.voucher_date")).fetchall()
    except Exception:
        rows = []

    for ym, code, name, debit, credit in rows:
        nm = (name or "").strip()
        if not nm:
            continue
        code = (code or "").strip()
        d_amt = float(debit or 0)
        c_amt = float(credit or 0)
        if code.startswith("6") and "收入" in nm:
            _month(ym)["revenue"] += c_amt - d_amt   # 收入取贷方净额
            continue
        if not (code.startswith("5") or code.startswith("6")):
            continue
        # 成本/费用取本期借方发生额（贷方为期末结转/完工转出，不属于本期成本发生）
        amt = d_amt
        if abs(amt) < 0.005:
            continue
        cat = classify(nm)
        mm = _month(ym)
        mm["total"] += amt
        if cat == "混合":
            mm["mixed"] += amt
        elif cat == "固定":
            mm["fixed"] += amt
        elif cat == "变动":
            mm["variable"] += amt
        else:
            mm["other"] += amt
        _add_account(nm, code, cat, ym, amt)

    source = "voucher" if acct_meta else None

    # ---- 回退：凭证无成本数据时，使用已导入利润表 ----
    if not acct_meta:
        try:
            rows = db.execute(_text(
                "SELECT period, item_name, amount FROM imported_financials "
                "WHERE statement_type='PL' ORDER BY period")).fetchall()
        except Exception:
            rows = []
        PL_COST_ITEMS = ("营业成本", "销售费用", "管理费用", "财务费用", "研发费用",
                         "税金及附加", "营业税金及附加", "所得税费用", "营业外支出")
        for period, iname, amount in rows:
            nm = (iname or "").strip()
            if not nm or amount is None:
                continue
            amt = float(amount)
            ym = str(period)[:7]
            if "收入" in nm:
                _month(ym)["revenue"] += amt
                continue
            if nm not in PL_COST_ITEMS:
                continue
            cat = classify(nm)
            mm = _month(ym)
            mm["total"] += amt
            if cat == "混合":
                mm["mixed"] += amt
            elif cat == "固定":
                mm["fixed"] += amt
            elif cat == "变动":
                mm["variable"] += amt
            else:
                mm["other"] += amt
            _add_account(nm, "", cat, ym, amt)
        source = "pl" if acct_meta else "none"

    months = sorted(monthly.keys())
    if not months:
        return make_response(True, {
            "source": source or "none", "months": [], "monthly": [], "accounts": [], "latest": None,
            "cvp": {"note": "暂无成本费用数据。请先录入凭证（成本/费用科目），或导入利润表。"},
            "fixed_kw": fkw, "variable_kw": vkw, "mixed_kw": mkw,
        }, "查询成功")

    latest_ym = months[-1]
    latest = monthly[latest_ym]

    # ---- 本量利（CVP）分析：混合成本用高低点法（收入为驱动）分解 ----
    fixed_c = latest["fixed"]
    var_c = latest["variable"]
    mixed_c = latest["mixed"]
    decomp_note = ""
    mixed_decomposed = False
    if mixed_c > 0 and len(months) >= 2:
        add_fixed = add_var = 0.0
        for nm, meta in acct_meta.items():
            if meta["cat"] != "混合":
                continue
            pairs = [(ym, acct_series[nm].get(ym, 0.0), monthly[ym]["revenue"])
                     for ym in months if monthly[ym]["revenue"] > 0 and abs(acct_series[nm].get(ym, 0.0)) > 0.005]
            if len(pairs) >= 2:
                hi = max(pairs, key=lambda x: x[2])
                lo = min(pairs, key=lambda x: x[2])
                if hi[2] > lo[2]:
                    rate = (hi[1] - lo[1]) / (hi[2] - lo[2])
                    if rate >= 0:
                        fp = hi[1] - rate * hi[2]
                        add_var += rate * latest["revenue"]
                        add_fixed += fp
        if add_fixed or add_var:
            fixed_c += add_fixed
            var_c += add_var
            mixed_decomposed = True
            decomp_note = "混合成本已用高低点法（以收入为驱动）分解计入固定与变动部分。"
        else:
            decomp_note = "混合成本数据不足，未分解，暂按『混合』单列（未计入固定/变动）。"
    elif mixed_c > 0:
        decomp_note = "混合成本仅 1 期数据，未分解（需至少 2 期），暂按『混合』单列。"
    else:
        decomp_note = "本次分析无混合成本，固定/变动成本已完整归集。"

    revenue = latest["revenue"]
    total_c = fixed_c + var_c
    contribution = revenue - var_c
    cmr = (contribution / revenue) if revenue else 0.0
    breakeven = (fixed_c / cmr) if (cmr > 0 and revenue) else 0.0
    safety = revenue - breakeven
    safety_rate = (safety / revenue) if revenue else 0.0
    profit = contribution - fixed_c
    dol = (contribution / profit) if (profit and abs(profit) > 1e-9) else None
    if not revenue:
        cvp_note = "暂无收入数据，无法计算边际贡献与盈亏平衡点。请录入销售/收入凭证，或导入含营业收入的利润表。"
    else:
        cvp_note = decomp_note

    # ---- 科目明细（最新期） ----
    acct_list = []
    for nm, meta in acct_meta.items():
        amt = acct_series[nm].get(latest_ym, 0.0)
        if abs(amt) < 0.005:
            continue
        acct_list.append({
            "name": nm, "code": meta["code"], "cat": meta["cat"],
            "amount": round(amt, 2),
            "ratio": round(amt / latest["total"] * 100, 2) if latest["total"] else 0.0,
        })
    acct_list.sort(key=lambda x: -x["amount"])

    monthly_list = [{k: (round(v, 2) if isinstance(v, float) else v)
                     for k, v in monthly[ym].items()} for ym in months]

    return make_response(True, {
        "source": source,
        "months": months,
        "monthly": monthly_list,
        "accounts": acct_list,
        "latest": {k: round(v, 2) if isinstance(v, float) else v for k, v in latest.items()},
        "cvp": {
            "revenue": round(revenue, 2), "fixed": round(fixed_c, 2), "variable": round(var_c, 2),
            "total": round(total_c, 2), "contribution": round(contribution, 2),
            "cmr": round(cmr, 4), "breakeven": round(breakeven, 2),
            "safety": round(safety, 2), "safety_rate": round(safety_rate, 4),
            "dol": round(dol, 2) if dol is not None else None,
            "mixed_decomposed": mixed_decomposed, "note": cvp_note,
        },
        "fixed_kw": fkw, "variable_kw": vkw, "mixed_kw": mkw,
    }, "查询成功")


@router.post("/ai-analysis", tags=["财务管理"])
def ai_finance_analysis(data: dict, db: Session = Depends(get_db)):
    """调用 AI（DeepSeek 官网或 OpenAI 兼容中转）对当期财务数据进行智能分析。
    请求体：
      { "question": "可选自定义问题",
        "mode": "视角模式：comprehensive(全面体检)|decision(经营决策)|cost(成本优化)|risk(风险预警)|cash(资金规划)|tax(税务建议)|report(报表解读)|benchmark(预测计划)",
        "benchmark": true/false,
        "plan": {"revenue_target": "年度营收目标(元)", "profit_target": "年度净利目标(元)", "targets": {"gross_margin": 40, "net_margin": 15, "debt_ratio": 50, "roe": 12}} }
    返回：{ "analysis": "分析文本", "model": "实际使用的模型名", "mode": "实际使用的模式" }"""
    import json as _json, urllib.request, urllib.error

    cfg = _get_ai_config(db)
    api_key = cfg["api_key"]
    base_url = cfg["base_url"]
    model = cfg["model"]
    if not api_key:
        return make_response(False, None, "未配置 AI API Key，请在仪表盘页面点击「配置 API Key」填入", "40001")

    # 获取仪表盘数据作为分析上下文
    dash = get_finance_dashboard(db)
    dash_data = dash.get("data", {}) if isinstance(dash, dict) else {}
    summary = dash_data.get("summary", {})

    # 结构化财务比率（本地计算，不依赖 AI）
    try:
        ratios = _compute_financial_ratios(db)
    except Exception:
        ratios = {}

    def _pct(v):
        return f"{v*100:.1f}%" if isinstance(v, (int, float)) else "—"

    # 构建财务摘要
    finance_summary = (
        f"【财务仪表盘摘要】\n"
        f"凭证总数：{summary.get('total_vouchers', 0)} 张\n"
        f"借方合计：¥{summary.get('total_debit', 0):.2f}\n"
        f"贷方合计：¥{summary.get('total_credit', 0):.2f}\n"
        f"是否平衡：{'是' if summary.get('balanced') else '否'}\n"
        f"收入合计：¥{summary.get('income_total', 0):.2f}\n"
        f"支出合计：¥{summary.get('expense_total', 0):.2f}\n"
        f"净利润：¥{summary.get('net_profit', 0):.2f}\n"
        f"资产合计：¥{summary.get('asset_total', 0):.2f}\n"
        f"负债合计：¥{summary.get('liability_total', 0):.2f}\n"
        f"所有者权益：¥{summary.get('equity_total', 0):.2f}\n"
    )
    if ratios:
        finance_summary += (
            f"\n【关键财务比率（系统自动计算）】\n"
            f"资产负债率：{_pct(ratios.get('debt_ratio'))}｜流动比率：{ratios.get('current_ratio') or '—'}\n"
            f"毛利率：{_pct(ratios.get('gross_margin'))}｜净利率：{_pct(ratios.get('net_margin'))}｜ROE：{_pct(ratios.get('roe'))}\n"
            f"货币资金：¥{ratios.get('cash', 0):.2f}｜应收账款：¥{ratios.get('receivable', 0):.2f}｜存货：¥{ratios.get('inventory', 0):.2f}\n"
            f"应付账款类：¥{ratios.get('payable', 0):.2f}｜流动资产：¥{ratios.get('current_asset', 0):.2f}｜流动负债：¥{ratios.get('current_liability', 0):.2f}\n"
            f"应收占收入比：{_pct(ratios.get('receivable_ratio'))}｜存货占收入比：{_pct(ratios.get('inventory_ratio'))}\n"
        )
    finance_summary += (
        f"\n月度趋势：{dash_data.get('monthly_trend', [])}\n"
        f"科目分布Top10：{dash_data.get('account_distribution', [])}\n"
        f"凭证类型分布：{dash_data.get('voucher_types', [])}\n"
    )

    # 已导入的外部财务报表（用户上传 Excel/HTML 解析入库）作为补充上下文
    try:
        _imp_rows = db.query(models.ImportedFinancialStatement).order_by(
            models.ImportedFinancialStatement.period.desc()
        ).all()
        if _imp_rows:
            _imp_company = _imp_rows[0].company_name or "导入报表"
            _imp_latest = {}  # 各报表类型 → 最新期间快照（按期间倒序，首见即最新）
            _imp_trend = {}   # 各报表类型 → 科目 → 近5期 [(period, amount)]
            _TYPE_LABEL = {"PL": "利润表", "BS": "资产负债表", "CF": "现金流量表"}
            for _r in _imp_rows:
                _g = _imp_latest.setdefault(_r.statement_type, {})
                if _r.item_name not in _g:
                    _g[_r.item_name] = float(_r.amount)
                _tl = _imp_trend.setdefault(_r.statement_type, {}).setdefault(_r.item_name, [])
                if len(_tl) < 5:
                    _tl.append((_r.period, float(_r.amount)))
            finance_summary += f"\n\n【已导入的外部财务报表：{_imp_company}（数据来自用户上传，与上方凭证账套无关）】\n"
            for _t, _items in _imp_latest.items():
                finance_summary += f"\n—— {_TYPE_LABEL.get(_t, _t)}（最新期间快照）——\n"
                for _k, _v in _items.items():
                    finance_summary += f"· {_k}：¥{_v:,.2f}\n"
                _tk = _imp_trend.get(_t, {})
                _keys = [k for k in _tk if k in _items][:6]
                if _keys:
                    finance_summary += "近5期趋势：\n"
                    for _k in _keys:
                        _seq = "，".join(f"{_p}→¥{_v:,.0f}" for _p, _v in _tk[_k])
                        finance_summary += f"· {_k}：{_seq}\n"
    except Exception:
        pass

    user_question = data.get("question", "").strip()
    mode = (data.get("mode") or ("benchmark" if data.get("benchmark") else "")).strip()

    # 预测与计划分析模式：把用户在面板填写的计划目标注入上下文（去掉外部对标案例）
    if data.get("benchmark") or mode == "benchmark":
        _plan = data.get("plan") or {}
        _plan_txt = ""
        try:
            if _plan.get("revenue_target"):
                _plan_txt += f"· 年度营业收入计划目标：¥{float(_plan['revenue_target']):,.2f}\n"
            if _plan.get("profit_target"):
                _plan_txt += f"· 年度净利润计划目标：¥{float(_plan['profit_target']):,.2f}\n"
        except Exception:
            pass
        _tgt = _plan.get("targets") if isinstance(_plan.get("targets"), dict) else {}
        _tgt_labels = {"gross_margin": "毛利率", "net_margin": "净利率", "debt_ratio": "资产负债率", "roe": "净资产收益率"}
        for _k, _label in _tgt_labels.items():
            try:
                if _tgt.get(_k) not in (None, ""):
                    _plan_txt += f"· {_label}目标：{float(_tgt[_k])}%\n"
            except Exception:
                pass
        finance_summary += (
            "\n\n【本企业预测与计划目标（用户在『预测与计划』面板填写）】\n"
            + (_plan_txt if _plan_txt else "· 尚未填写计划目标，请提醒用户设定营收/净利等年度目标后再做对比。\n")
            + "说明：本企业实际数据单位一律为元（¥），预测与计划同样基于本企业口径，不存在任何外部对标案例数据。\n"
        )

    # 决策视角模式库：不同按钮对应不同的分析框架
    MODE_PROMPTS = {
        "comprehensive": (
            "请对当前企业做一次全面财务体检，按以下结构输出：\n"
            "1. 财务健康度总评（结合资产负债率、流动比率、ROE 等已给比率）\n"
            "2. 盈利能力分析（毛利率、净利率、利润构成）\n"
            "3. 资产与负债结构（货币资金/应收/存货/应付的配比是否合理）\n"
            "4. 三大风险点及预警等级（高/中/低）\n"
            "5. 未来 3 个月可执行的财务行动清单（每条含责任角色与量化目标）"
        ),
        "decision": (
            "请站在企业经营者（总经理/财务负责人）的视角，基于以上真实数据给出【经营决策建议】：\n"
            "1. 当前经营态势一句话结论（增长/持平/收缩，用数据支撑）\n"
            "2. 要不要加大投入？给出扩张、维持、收缩三种情景的触发条件与对应动作\n"
            "3. 定价与接单策略建议（结合毛利率与成本结构，给出最低接单毛利率红线）\n"
            "4. 现金流安全垫测算（按当前现金与月均支出，还能支撑几个月）\n"
            "5. 未来 30/60/90 天决策日历（每个节点做什么、看哪个指标）"
        ),
        "cost": (
            "请做一次【成本优化专项分析】：\n"
            "1. 成本结构拆解（直接材料/人工/制造费用的占比与合理性判断）\n"
            "2. 找出 3 个最值得优化的成本项，按降本空间从大到小排序，并估算可节约金额\n"
            "3. 每个优化项给出具体落地动作（采购议价、BOM 改进、工艺优化、费用管控等）\n"
            "4. 降本对毛利率与净利润的敏感性测算（降本 5%/10%/15% 分别带来多少利润提升）\n"
            "5. ERP 中如何跟踪这些降本措施（建议设置哪些报表与预警）"
        ),
        "risk": (
            "请做一次【财务风险预警扫描】：\n"
            "1. 逐项扫描以下风险：偿债风险、流动性风险、应收坏账风险、存货积压风险、成本超支风险\n"
            "2. 每项给出风险等级（高/中/低）+ 判断依据（引用具体数据）+ 触发阈值\n"
            "3. 列出最紧急的 3 个风险，给出 7 天内可执行的应对动作\n"
            "4. 设计一套风险监控指标看板（指标名、警戒线、检查频率）"
        ),
        "cash": (
            "请做一次【资金规划专项分析】：\n"
            "1. 当前资金状况盘点（货币资金、应收、应付、存货变现能力）\n"
            "2. 未来 3 个月现金流预测（按现有应收账期与应付到期情况估算）\n"
            "3. 资金缺口预警（若有）与三种补足方案（催收/账期谈判/融资），比较成本与可行性\n"
            "4. 闲余资金若充足，给出增强收益的建议（理财/再投资/备货，结合行业特点）\n"
            "5. 建议设置的现金流预警线与监控频率"
        ),
        "tax": (
            "请做一次【税务与合规建议】：\n"
            "1. 基于当前收入/成本/利润结构，分析增值税与企业所得税的大致负担水平\n"
            "2. 指出账务中可能存在的税务风险点（如暂估入库、进项缺失、费用凭证不全等）\n"
            "3. 给出 3~5 条合规前提下的税务优化建议（如进项发票管理、小微企业优惠适用性）\n"
            "4. 提醒需要重点留存的备查资料清单\n"
            "5. 声明：以上为管理建议，具体以主管税务机关口径与专业税务顾问意见为准"
        ),
        "report": (
            "请用通俗易懂的语言解读当前财务报表，面向不懂财务的老板：\n"
            "1. 用 5 句话讲清公司现在赚不赚钱、钱在哪、欠多少\n"
            "2. 把资产负债表和利润表的关键数字翻译成业务语言（比如应收=客户欠我们的钱）\n"
            "3. 与上期/行业常态相比，哪些科目异常？为什么？\n"
            "4. 给出 3 个老板本月就应该关注的数字，以及每个数字背后的业务动因\n"
            "5. 如果只看一张报表，应该看哪张？为什么？"
        ),
        "benchmark": (
            "请以财务分析师+经营计划顾问的视角，做一次【本企业预测与计划对比分析】：\n"
            "1. 当前实际经营表现一句话结论（营业收入、净利润、关键比率，引用具体数字）\n"
            "2. 根据提供的月度趋势/近5期导入报表趋势，判断未来 1-3 期的收入、利润走势，说明预测依据与假设\n"
            "3. 把实际值、预测值与用户填写的年度计划目标逐项对比，说明差距金额与百分比，判断目标能否达成\n"
            "4. 若存在差距，给出追赶目标或修正计划的具体建议（可执行动作、责任角色、量化目标）\n"
            "5. 给出未来 90 天的经营计划行动清单（按时间顺序排列，每条含动作、负责人与完成标准）"
        ),
    }

    has_user_question = bool(user_question)
    if not user_question:
        user_question = MODE_PROMPTS.get(mode, MODE_PROMPTS["comprehensive"])

    # 模式对应的系统提示词（角色设定）
    MODE_ROLES = {
        "comprehensive": "你是一位资深财务总监（CFO），擅长财务体检与风险识别。",
        "decision": "你是一位既懂财务又懂业务的经营顾问，擅长把财务数据翻译成经营决策。",
        "cost": "你是一位精通制造业成本会计的专家，擅长成本拆解与降本方案设计。",
        "risk": "你是一位审慎的风险管理专家，擅长财务风险识别与预警体系设计。",
        "cash": "你是一位资金管理专家，擅长现金流预测与资金调度。",
        "tax": "你是一位熟悉中小企业税务实务的税务顾问，注重合规。",
        "report": "你是一位善于向非财务人员讲解财报的财务BP，表达通俗清晰。",
        "benchmark": "你是一位精通财务分析与经营计划编制的财务分析师，擅长本企业实际、预测与计划目标的三维对比分析。",
    }
    sys_role = MODE_ROLES.get(mode, "你是一位资深财务分析师，精通成本会计和ERP财务分析。")

    # 输出格式约束：禁止表格，改为详细书面化分点叙述
    OUTPUT_RULES = (
        "【输出格式要求，必须严格遵守】\n"
        "1. 严禁使用任何表格（包括 markdown 表格、HTML 表格、以 | 分隔的行），表格在系统中容易乱码，影响阅读。\n"
        "2. 严禁使用任何 emoji、特殊符号装饰。\n"
        "3. 必须使用详细的书面化语言进行叙述，像撰写正式财务分析报告那样，段落完整、逻辑连贯、论述充分。\n"
        "4. 可以使用分点结构组织内容，但每个分点下必须写出 2 至 5 句完整、详实的说明，"
        "讲清楚现象、原因、影响与建议，不允许只写一句话或几个关键词了事。\n"
        "5. 每一条结论都必须引用给出的具体财务数字作为支撑，说明数字是多少、意味着什么；"
        "禁止空泛表述，例如“建议加强管理”“优化成本结构”这类没有具体做法的句子。\n"
        "6. 建议部分必须具体到可执行的动作、责任人角色与量化目标（如金额、比例、时间节点）。\n"
        "7. 使用中文回答，可用 markdown 标题（##、###）和有序/无序列表组织层级，但正文主体应是详细文字描述。\n"
    )

    # 最高优先级约束：禁止输出思考过程，防止推理模型把英文思维链混入正文（表现为乱码）
    NO_THINK_RULE = (
        "【最高优先级约束，必须严格遵守】\n"
        "1. 严禁输出任何思考过程、推理草稿、内心独白、英文草稿，严禁以『让我分析』『Hmm』『首先』『好的』等过渡语开头，"
        "直接从最终中文答案正文开始写。\n"
        "2. 全文必须使用中文（报表科目名、单位、专有名词保留原样），正文不允许出现成段的英文。\n"
        "3. 只输出最终答案本身，不得附带任何对思考过程的说明或自我解释。\n"
    )

    if has_user_question:
        # 用户提出了具体问题：以回答问题为第一优先级，财务数据是必须引用的真实依据
        ANSWER_RULES = (
            "【回答要求（最高优先级，必须严格遵守）】\n"
            "1. 你唯一的核心任务就是回答用户提出的问题本身，全文必须紧扣这个问题展开，"
            "严禁输出与问题无关的通用财务体检报告或全面分析报告。\n"
            "2. 直接给出答案和结论，然后再展开依据、理由与具体做法，先把问题说清楚再补充。\n"
            "3. 下面提供的【本企业财务数据】和【本企业预测与计划目标】均来自本系统的真实数据，是回答的依据："
            "当用户的问题涉及公司营收、利润、资产、负债、比率等财务/经营数据时，"
            "必须直接从参考资料中引用对应数字作答。资料里明明有的数字，严禁回答"
            "『不知道』『未提供』『暂无数据』『我没有贵公司数据』之类的话——数字就在参考资料里，先看资料再回答。\n"
            "4. 本企业数据与计划目标均为本企业口径，单位是元（¥），回答时注意区分实际值与目标值，不要混为一谈。\n"
            "5. 如果问题与财务数据完全无关（例如咨询政策、流程、工具、写法、行业常识等），"
            "可直接用专业知识回答，但也不要编造本企业数字。\n"
            "6. 严禁使用任何表格（包括 markdown 表格、HTML 表格、以 | 分隔的行）。\n"
            "7. 严禁使用任何 emoji。\n"
            "8. 使用详细的书面化中文回答，逻辑连贯，可以用分点结构，但每个分点下要有 2 至 5 句详实说明。\n"
            "9. 若回答该问题需要的数据确实未提供，明确说明缺少什么，再基于已有信息给出最接近的判断或建议。\n"
        )
        messages = [
            {"role": "system", "content":
                "你是一位既懂财务又懂企业经营的综合顾问，能够回答用户提出的各类问题。\n\n" + NO_THINK_RULE + ANSWER_RULES},
            {"role": "user", "content":
                f"【用户的问题】\n{user_question}\n\n"
                f"【参考资料：本系统真实财务数据（回答财务问题必须引用，禁止答『不知道』）】\n{finance_summary}"},
        ]
    else:
        messages = [
            {"role": "system", "content": sys_role + "\n\n" + NO_THINK_RULE + OUTPUT_RULES +
                "请基于提供的财务数据进行专业、深入的分析。重点关注：成本控制、盈利能力、资产负债结构、异常预警。"},
            {"role": "user", "content": f"{finance_summary}\n\n请回答以下问题：\n{user_question}"},
        ]

    try:
        # 注意：本模型为推理模型，思维链会先消耗 token，max_tokens 过小会导致正文 content 为空
        payload = _json.dumps({"model": model, "messages": messages, "max_tokens": 8000, "temperature": 0.7}, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(
            _build_chat_url(base_url),
            data=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = _json.loads(resp.read().decode('utf-8'))
            _msg = (result.get("choices") or [{}])[0].get("message") or {}
            analysis = (_msg.get("content") or "").strip()
            if not analysis:
                analysis = "AI 本次未生成正文（思考超时），请稍后重试，或把问题说得更聚焦一些。"
            analysis = _clean_ai_text(analysis)
            return make_response(True, {"analysis": analysis, "model": result.get("model", model), "mode": mode or "comprehensive"}, "分析完成")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='replace')[:300]
        hint = ""
        if e.code == 401: hint = "（Key 无效，请检查）"
        elif e.code == 402: hint = "（账户余额不足）"
        elif e.code == 404: hint = "（接口地址或模型名不对）"
        return make_response(False, None, f"AI API 调用失败（HTTP {e.code}）{hint}：{err_body}", "40002")
    except Exception as e:
        return make_response(False, None, f"AI 分析异常：{str(e)}", "40003")


@router.post("/market-price-query", tags=["财务管理"])
def market_price_query(data: dict, db: Session = Depends(get_db)):
    """调用 DeepSeek 查询某个产品的当期市场价格。
    请求体：{ "product_name": "产品名称", "spec": "规格型号（可选）", "industry": "行业（可选）", "region": "地区（可选）" }
    返回：{ "result": "AI 返回的市场价格分析", "model": "使用的模型", "product_info": {...} }"""
    import json as _json, urllib.request, urllib.error

    cfg = _get_ai_config(db)
    api_key = cfg["api_key"]
    base_url = cfg["base_url"]
    model = cfg["model"]
    if not api_key:
        return make_response(False, None, "未配置 AI API Key，请在仪表盘页面点击「配置 API Key」填入", "40001")

    product_name = (data.get("product_name") or "").strip()
    spec = (data.get("spec") or "").strip()
    industry = (data.get("industry") or "").strip()
    region = (data.get("region") or "").strip()

    if not product_name:
        return make_response(False, None, "请输入产品名称", "40004")

    # 构建提示词
    prompt = f"请查询并分析【{product_name}】的当前市场价格情况。\n"
    if spec:
        prompt += f"规格型号：{spec}\n"
    if industry:
        prompt += f"所属行业：{industry}\n"
    if region:
        prompt += f"地区：{region}\n"
    prompt += """
请按照以下结构输出：

## 一、市场价格区间
- 主流价格区间：（给出最低-最高价格，注明单位）
- 市场均价：（给出平均价格）
- 价格说明：（说明价格差异的主要原因，如品牌、规格、采购量等）

## 二、主要品牌/厂商价格对比
（列出3-5个主要品牌或厂商的价格范围，用表格形式呈现）

## 三、价格影响因素分析
1. 原材料成本影响
2. 市场供需关系
3. 行业竞争程度
4. 季节性/周期性因素

## 四、定价建议
- 对于采购方的建议
- 对于销售方的建议

注意：
1. 请基于你掌握的市场知识和行业数据进行分析，数据尽量准确。
2. 如果是比较细分的产品，说明数据的参考价值和局限性。
3. 价格单位请明确标注（如：元/件、元/吨、元/米等）。
4. 使用中文回答，条理清晰，专业严谨。
"""

    messages = [
        {"role": "system", "content": "你是一位市场价格分析专家，精通各行业产品价格行情，能够根据产品名称、规格等信息提供专业的市场价格分析和定价建议。回答要专业、准确、有参考价值。"},
        {"role": "user", "content": prompt},
    ]

    try:
        payload = _json.dumps({
            "model": model,
            "messages": messages,
            "max_tokens": 8000,
            "temperature": 0.6,
        }, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(
            _build_chat_url(base_url),
            data=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = _json.loads(resp.read().decode('utf-8'))
            _msg = (result.get("choices") or [{}])[0].get("message") or {}
            analysis = (_msg.get("content") or "").strip()
            # 兼容推理模型：content 为空时，尝试从 reasoning_content 提取
            if not analysis:
                reasoning = (_msg.get("reasoning_content") or "").strip()
                if reasoning:
                    analysis = reasoning
            if not analysis:
                analysis = "AI 本次未生成结果（可能是模型思考超时或输出为空），请稍后重试，或换个更具体的产品名称试试。"
            analysis = _clean_ai_text(analysis)
            return make_response(True, {
                "result": analysis,
                "model": result.get("model", model),
                "product_info": {
                    "product_name": product_name,
                    "spec": spec,
                    "industry": industry,
                    "region": region,
                }
            }, "查询完成")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='replace')[:300]
        hint = ""
        if e.code == 401: hint = "（Key 无效，请检查）"
        elif e.code == 402: hint = "（账户余额不足）"
        elif e.code == 404: hint = "（接口地址或模型名不对）"
        return make_response(False, None, f"AI API 调用失败（HTTP {e.code}）{hint}：{err_body}", "40002")
    except Exception as e:
        return make_response(False, None, f"市场价查询异常：{str(e)}", "40003")


@router.post("/cost-decision-analyze", tags=["财务管理"])
def cost_decision_analyze(data: dict, db: Session = Depends(get_db)):
    """AI 成本决策分析：用户用自然语言描述决策问题，系统结合企业数据给出最佳方案。
    请求体：{ "question": "用户的决策问题", "context": { 企业当前数据 } }"""
    import json as _json, urllib.request, urllib.error

    cfg = _get_ai_config(db)
    api_key = cfg["api_key"]
    base_url = cfg["base_url"]
    model = cfg["model"]
    if not api_key:
        return make_response(False, None, "未配置 AI API Key，请在仪表盘页面点击「配置 API Key」填入", "40001")

    question = (data.get("question") or "").strip()
    context = data.get("context") or {}

    if not question:
        return make_response(False, None, "请输入您的决策问题", "40004")

    # 构建企业数据上下文字符串
    ctx_lines = []
    cb = context.get("costBehavior") or {}
    cvp = context.get("cvp") or {}
    if cb.get("year"):
        ctx_lines.append(f"【企业产量与成本数据（{cb['year']}年）】")
        ctx_lines.append(f"  - 年产量：约 {cb.get('annualOutput', '未知')} 件")
        ctx_lines.append(f"  - 年总成本：约 {cb.get('annualTotalCost', '未知')} 元")
        fixed = cb.get('fixedCost') or {}
        variable = cb.get('variableCost') or {}
        if fixed.get('total'):
            ctx_lines.append(f"  - 年固定成本：约 {fixed['total']} 元（含折旧、租金、固定人工等）")
        if variable.get('unitVarCost'):
            ctx_lines.append(f"  - 单位变动成本：约 {variable['unitVarCost']} 元/件")
    if cvp:
        ctx_lines.append(f"【本量利数据】")
        if cvp.get('unitPrice'):
            ctx_lines.append(f"  - 产品单价：{cvp['unitPrice']} 元")
        if cvp.get('unitVarCost'):
            ctx_lines.append(f"  - 单位变动成本：{cvp['unitVarCost']} 元")
        if cvp.get('fixedCost'):
            ctx_lines.append(f"  - 固定成本总额：{cvp['fixedCost']} 元")
        if cvp.get('breakevenQty'):
            ctx_lines.append(f"  - 盈亏平衡点：{cvp['breakevenQty']} 件")
        if cvp.get('targetProfitQty'):
            ctx_lines.append(f"  - 目标利润销量：{cvp['targetProfitQty']} 件")
        if cvp.get('currentProfit') is not None:
            ctx_lines.append(f"  - 当前利润：{cvp['currentProfit']} 元")
    ctx_str = '\n'.join(ctx_lines) if ctx_lines else "（暂无企业数据，基于一般制造业经验分析）"

    prompt = f"""你是一位资深的制造业成本管理顾问，精通成本会计、管理会计和经营决策分析。

## 企业背景数据
{ctx_str}

## 用户的决策问题
{question}

## 分析要求

请按照以下结构进行专业分析（使用 Markdown 格式）：

### 一、问题诊断
- 识别这是什么类型的决策问题（如：定价决策、生产决策、停产/转产决策、自制/外购决策、接受特殊订单等）
- 指出决策中需要考虑的关键成本因素
- 明确哪些是相关成本，哪些是不相关成本（沉没成本等）

### 二、数据梳理与关键指标
根据用户描述和企业背景数据，梳理出：
- 相关收入
- 相关成本（变动成本、机会成本、付现成本等）
- 边际贡献
- 关键决策指标

### 三、方案对比分析
列出 2-3 个可行方案，分别计算：
| 方案 | 相关收入 | 相关成本 | 增量利润 | 优缺点 |
|------|---------|---------|---------|--------|
| 方案A | ... | ... | ... | ... |
| 方案B | ... | ... | ... | ... |

### 四、最佳方案推荐
- 明确推荐哪个方案
- 给出推荐理由（量化数据支撑）
- 说明风险和注意事项

### 五、行动建议
给出 3-5 条具体可执行的建议。

## 重要原则
1. **区分相关成本与不相关成本**：沉没成本、已投入的固定成本等不影响决策的成本要明确指出
2. **重视机会成本**：被放弃的最优方案的收益就是机会成本
3. **关注边际贡献**：定价决策时，只要价格高于单位变动成本，就有边际贡献
4. **考虑付现成本**：资金紧张时，付现成本比总利润更重要
5. **数据不足时**：明确说明假设条件，给出估算方法，提醒用户核实
6. **使用中文回答**，专业严谨，条理清晰

请直接输出分析结果，不要说"好的"、"让我分析一下"之类的开场白。"""

    messages = [
        {"role": "system", "content": "你是一位资深制造业成本管理顾问，擅长成本会计、管理会计和经营决策分析，能够用专业的成本分析方法帮助企业做出最优决策。"},
        {"role": "user", "content": prompt},
    ]

    try:
        payload = _json.dumps({
            "model": model,
            "messages": messages,
            "max_tokens": 8000,
            "temperature": 0.5,
        }, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(
            _build_chat_url(base_url),
            data=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = _json.loads(resp.read().decode('utf-8'))
            _msg = (result.get("choices") or [{}])[0].get("message") or {}
            analysis = (_msg.get("content") or "").strip()
            if not analysis:
                reasoning = (_msg.get("reasoning_content") or "").strip()
                if reasoning:
                    analysis = reasoning
            if not analysis:
                analysis = "AI 本次未生成结果，请稍后重试。"
            analysis = _clean_ai_text(analysis)
            return make_response(True, {
                "result": analysis,
                "model": result.get("model", model),
                "question": question,
            }, "分析完成")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='replace')[:300]
        hint = ""
        if e.code == 401: hint = "（Key 无效，请检查）"
        elif e.code == 402: hint = "（账户余额不足）"
        elif e.code == 404: hint = "（接口地址或模型名不对）"
        return make_response(False, None, f"AI API 调用失败（HTTP {e.code}）{hint}：{err_body}", "40002")
    except Exception as e:
        return make_response(False, None, f"成本决策分析异常：{str(e)}", "40003")