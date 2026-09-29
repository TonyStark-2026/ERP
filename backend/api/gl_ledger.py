# -*- coding: utf-8 -*-
"""总账管理 API：账套、科目、凭证、期间、余额"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
import json
import calendar

from .. import models
from ..database import get_db
from ..app import make_response

router = APIRouter()


# ---------- Pydantic Schemas ----------

class LedgerCreate(BaseModel):
    name: str
    code: str
    fiscal_year: int = 1
    currency: str = "CNY"
    accounting_std: str = "企业会计准则"

class AccountCreate(BaseModel):
    ledger_id: int
    code: str
    name: str
    parent_id: Optional[int] = None
    category: str
    direction: str = "借"
    aux_required: str = "[]"

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    direction: Optional[str] = None
    aux_required: Optional[str] = None
    status: Optional[str] = None

class VoucherEntryIn(BaseModel):
    line_no: int
    account_id: int
    summary: Optional[str] = None
    debit_amount: float = 0
    credit_amount: float = 0
    aux_values: str = "{}"

class VoucherCreate(BaseModel):
    ledger_id: int
    voucher_date: date
    period_id: int
    voucher_type: str = "记账凭证"
    source_type: str = "手工"
    source_id: Optional[int] = None
    summary: Optional[str] = None
    entries: List[VoucherEntryIn] = []

class PeriodCreate(BaseModel):
    ledger_id: int
    year: int
    month: int


# ---------- 账套 ----------

@router.get("/ledgers")
def list_ledgers(db: Session = Depends(get_db)):
    items = db.query(models.GlLedger).filter(models.GlLedger.status == "ACTIVE").all()
    return make_response(True, items, "查询成功")

@router.post("/ledgers")
def create_ledger(data: LedgerCreate, db: Session = Depends(get_db)):
    obj = models.GlLedger(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return make_response(True, obj, "创建成功")

@router.get("/ledgers/{ledger_id}")
def get_ledger(ledger_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.GlLedger).get(ledger_id)
    if not obj:
        raise HTTPException(404, "账套不存在")
    return make_response(True, obj, "查询成功")


# ---------- 会计科目 ----------

@router.get("/accounts")
def list_accounts(ledger_id: int, db: Session = Depends(get_db)):
    items = db.query(models.GlAccount).filter(
        models.GlAccount.ledger_id == ledger_id,
        models.GlAccount.status == "ACTIVE"
    ).order_by(models.GlAccount.code).all()
    return make_response(True, items, "查询成功")

@router.post("/accounts")
def create_account(data: AccountCreate, db: Session = Depends(get_db)):
    obj = models.GlAccount(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return make_response(True, obj, "创建成功")

@router.put("/accounts/{account_id}")
def update_account(account_id: int, data: AccountUpdate, db: Session = Depends(get_db)):
    obj = db.query(models.GlAccount).get(account_id)
    if not obj:
        raise HTTPException(404, "科目不存在")
    for k, v in data.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    return make_response(True, obj, "更新成功")


# ---------- 科目模板（企业会计准则常用科目） ----------

ENTERPRISE_ACCOUNTS = [
    # 资产类
    {"code": "1001", "name": "库存现金", "category": "资产", "direction": "借"},
    {"code": "1002", "name": "银行存款", "category": "资产", "direction": "借"},
    {"code": "1122", "name": "应收账款", "category": "资产", "direction": "借"},
    {"code": "1403", "name": "原材料", "category": "资产", "direction": "借"},
    {"code": "1405", "name": "库存商品", "category": "资产", "direction": "借"},
    {"code": "1601", "name": "固定资产", "category": "资产", "direction": "借"},
    {"code": "1602", "name": "累计折旧", "category": "资产", "direction": "贷"},
    # 负债类
    {"code": "2202", "name": "应付账款", "category": "负债", "direction": "贷"},
    {"code": "2211", "name": "应付职工薪酬", "category": "负债", "direction": "贷"},
    {"code": "2221", "name": "应交税费", "category": "负债", "direction": "贷"},
    {"code": "2241", "name": "其他应付款", "category": "负债", "direction": "贷"},
    # 权益类
    {"code": "4001", "name": "实收资本", "category": "权益", "direction": "贷"},
    {"code": "4103", "name": "本年利润", "category": "权益", "direction": "贷"},
    {"code": "4104", "name": "利润分配", "category": "权益", "direction": "贷"},
    # 收入类
    {"code": "6001", "name": "主营业务收入", "category": "收入", "direction": "贷"},
    {"code": "6051", "name": "其他业务收入", "category": "收入", "direction": "贷"},
    # 费用类
    {"code": "6401", "name": "主营业务成本", "category": "费用", "direction": "借"},
    {"code": "6601", "name": "销售费用", "category": "费用", "direction": "借"},
    {"code": "6602", "name": "管理费用", "category": "费用", "direction": "借"},
    {"code": "6603", "name": "财务费用", "category": "费用", "direction": "借"},
    # 成本类
    {"code": "5001", "name": "生产成本", "category": "成本", "direction": "借"},
    {"code": "5101", "name": "制造费用", "category": "成本", "direction": "借"},
]

@router.post("/accounts/template")
def import_account_template(ledger_id: int, db: Session = Depends(get_db)):
    """按企业会计准则模板批量导入科目"""
    existing = db.query(models.GlAccount).filter(
        models.GlAccount.ledger_id == ledger_id,
        models.GlAccount.code.in_([a["code"] for a in ENTERPRISE_ACCOUNTS])
    ).count()
    if existing > 0:
        return make_response(False, None, "该账套已导入过科目模板，请勿重复导入")

    for a in ENTERPRISE_ACCOUNTS:
        db.add(models.GlAccount(
            ledger_id=ledger_id, code=a["code"], name=a["name"],
            category=a["category"], direction=a["direction"],
            is_leaf=True, aux_required="[]", status="ACTIVE"
        ))
    db.commit()
    return make_response(True, {"count": len(ENTERPRISE_ACCOUNTS)}, "模板导入成功")


# ---------- 会计期间 ----------

@router.get("/periods")
def list_periods(ledger_id: int, db: Session = Depends(get_db)):
    items = db.query(models.GlPeriod).filter(
        models.GlPeriod.ledger_id == ledger_id
    ).order_by(models.GlPeriod.year, models.GlPeriod.month).all()
    return make_response(True, items, "查询成功")

@router.post("/periods")
def create_period(data: PeriodCreate, db: Session = Depends(get_db)):
    # 检查是否已存在
    exist = db.query(models.GlPeriod).filter(
        models.GlPeriod.ledger_id == data.ledger_id,
        models.GlPeriod.year == data.year,
        models.GlPeriod.month == data.month
    ).first()
    if exist:
        return make_response(True, exist, "期间已存在")

    # 计算起止日期
    start = date(data.year, data.month, 1)
    _, last_day = calendar.monthrange(data.year, data.month)
    end = date(data.year, data.month, last_day)

    obj = models.GlPeriod(
        ledger_id=data.ledger_id, year=data.year, month=data.month,
        start_date=start, end_date=end, status="未结账"
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return make_response(True, obj, "创建成功")


# ---------- 凭证 ----------

@router.get("/vouchers")
def list_vouchers(
    ledger_id: int,
    period_id: Optional[int] = None,
    status: Optional[str] = None,
    account_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    q = db.query(models.GlVoucher).filter(models.GlVoucher.ledger_id == ledger_id)
    if period_id:
        q = q.filter(models.GlVoucher.period_id == period_id)
    if status:
        q = q.filter(models.GlVoucher.status == status)
    if account_id:
        q = q.join(models.GlVoucherEntry).filter(models.GlVoucherEntry.account_id == account_id)
    items = q.order_by(models.GlVoucher.voucher_date.desc(), models.GlVoucher.voucher_no.desc()).all()
    # 附带分录
    for v in items:
        v.entries = db.query(models.GlVoucherEntry).filter(
            models.GlVoucherEntry.voucher_id == v.id
        ).order_by(models.GlVoucherEntry.line_no).all()
    return make_response(True, items, "查询成功")

@router.post("/vouchers")
def create_voucher(data: VoucherCreate, db: Session = Depends(get_db)):
    # 生成凭证号：记-YYYYMM-NNN
    period = db.query(models.GlPeriod).get(data.period_id)
    if not period:
        raise HTTPException(404, "期间不存在")

    prefix = f"记-{data.voucher_date.strftime('%Y%m')}"
    max_no = db.query(func.max(models.GlVoucher.voucher_no)).filter(
        models.GlVoucher.ledger_id == data.ledger_id,
        models.GlVoucher.voucher_no.like(f"{prefix}-%")
    ).scalar()
    if max_no:
        seq = int(max_no.split("-")[-1]) + 1
    else:
        seq = 1
    voucher_no = f"{prefix}-{seq:03d}"

    # 校验借贷平衡
    total_debit = sum(e.debit_amount for e in data.entries)
    total_credit = sum(e.credit_amount for e in data.entries)
    if abs(total_debit - total_credit) > 0.001:
        return make_response(False, None, f"借贷不平衡：借方 {total_debit} ≠ 贷方 {total_credit}")

    # 创建凭证
    obj = models.GlVoucher(
        ledger_id=data.ledger_id, voucher_no=voucher_no,
        voucher_date=data.voucher_date, period_id=data.period_id,
        voucher_type=data.voucher_type, source_type=data.source_type,
        source_id=data.source_id, summary=data.summary, status="草稿"
    )
    db.add(obj)
    db.flush()

    # 创建分录
    for e in data.entries:
        db.add(models.GlVoucherEntry(
            voucher_id=obj.id, line_no=e.line_no, account_id=e.account_id,
            summary=e.summary, debit_amount=e.debit_amount, credit_amount=e.credit_amount,
            aux_values=e.aux_values
        ))
    db.commit()
    db.refresh(obj)
    return make_response(True, obj, "创建成功")

@router.post("/vouchers/{voucher_id}/post")
def post_voucher(voucher_id: int, auditor: str = "系统", db: Session = Depends(get_db)):
    """过账凭证：校验已审核+借贷平衡+期间未锁定 → 更新余额表"""
    v = db.query(models.GlVoucher).get(voucher_id)
    if not v:
        raise HTTPException(404, "凭证不存在")
    if v.status != "已审核":
        return make_response(False, None, "只有已审核的凭证才能过账")

    # 校验期间未锁定
    period = db.query(models.GlPeriod).get(v.period_id)
    if period and period.status in ("已结账", "已关闭"):
        return make_response(False, None, f"期间 {period.year}-{period.month} 已{period.status}，禁止过账")

    entries = db.query(models.GlVoucherEntry).filter(
        models.GlVoucherEntry.voucher_id == v.id
    ).all()

    # 校验借贷平衡
    total_debit = sum(float(e.debit_amount or 0) for e in entries)
    total_credit = sum(float(e.credit_amount or 0) for e in entries)
    if abs(total_debit - total_credit) > 0.001:
        return make_response(False, None, f"借贷不平衡：借方 {total_debit} ≠ 贷方 {total_credit}")

    for e in entries:
        bal = db.query(models.GlBalance).filter(
            models.GlBalance.ledger_id == v.ledger_id,
            models.GlBalance.period_id == v.period_id,
            models.GlBalance.account_id == e.account_id,
            models.GlBalance.aux_values == (e.aux_values or "{}")
        ).first()

        if not bal:
            bal = models.GlBalance(
                ledger_id=v.ledger_id, period_id=v.period_id,
                account_id=e.account_id, aux_values=e.aux_values or "{}",
                begin_debit=0, begin_credit=0,
                period_debit=0, period_credit=0,
                end_debit=0, end_credit=0
            )
            db.add(bal)

        bal.period_debit += e.debit_amount
        bal.period_credit += e.credit_amount
        bal.end_debit = bal.begin_debit + bal.period_debit
        bal.end_credit = bal.begin_credit + bal.period_credit

    v.status = "已过账"
    v.posted_at = datetime.now()
    if not v.audited_by:
        v.audited_by = auditor
    db.commit()
    return make_response(True, v, "过账成功")


@router.post("/vouchers/{voucher_id}/audit")
def audit_voucher(voucher_id: int, auditor: str = "审核人", db: Session = Depends(get_db)):
    """审核凭证：草稿 → 已审核，校验制单人≠审核人"""
    v = db.query(models.GlVoucher).get(voucher_id)
    if not v:
        raise HTTPException(404, "凭证不存在")
    if v.status not in ("草稿", "待审核"):
        return make_response(False, None, f"当前状态「{v.status}」不可审核")
    if v.created_by and v.created_by == auditor:
        return make_response(False, None, "制单人与审核人不能为同一人")

    v.status = "已审核"
    v.audited_by = auditor
    db.commit()
    return make_response(True, v, "审核成功")


@router.post("/vouchers/{voucher_id}/reject")
def reject_voucher(voucher_id: int, db: Session = Depends(get_db)):
    """驳回凭证：已审核/待审核 → 草稿"""
    v = db.query(models.GlVoucher).get(voucher_id)
    if not v:
        raise HTTPException(404, "凭证不存在")
    if v.status not in ("已审核", "待审核"):
        return make_response(False, None, f"当前状态「{v.status}」不可驳回")
    v.status = "草稿"
    v.audited_by = None
    db.commit()
    return make_response(True, v, "已驳回至草稿")


@router.post("/vouchers/{voucher_id}/void")
def void_voucher(voucher_id: int, db: Session = Depends(get_db)):
    """作废凭证：已过账的先反过账回退余额，再标记作废"""
    v = db.query(models.GlVoucher).get(voucher_id)
    if not v:
        raise HTTPException(404, "凭证不存在")
    if v.status == "已作废":
        return make_response(False, None, "凭证已作废")

    # 如果已过账，先反过账回退余额
    if v.status == "已过账":
        entries = db.query(models.GlVoucherEntry).filter(
            models.GlVoucherEntry.voucher_id == v.id
        ).all()
        for e in entries:
            bal = db.query(models.GlBalance).filter(
                models.GlBalance.ledger_id == v.ledger_id,
                models.GlBalance.period_id == v.period_id,
                models.GlBalance.account_id == e.account_id,
                models.GlBalance.aux_values == (e.aux_values or "{}")
            ).first()
            if bal:
                bal.period_debit -= e.debit_amount
                bal.period_credit -= e.credit_amount
                bal.end_debit = bal.begin_debit + bal.period_debit
                bal.end_credit = bal.begin_credit + bal.period_credit

    v.status = "已作废"
    db.commit()
    return make_response(True, v, "作废成功")


@router.post("/vouchers/{voucher_id}/unpost")
def unpost_voucher(voucher_id: int, db: Session = Depends(get_db)):
    """反过账：已过账 → 已审核，回退余额"""
    v = db.query(models.GlVoucher).get(voucher_id)
    if not v:
        raise HTTPException(404, "凭证不存在")
    if v.status != "已过账":
        return make_response(False, None, "只有已过账的凭证才能反过账")

    entries = db.query(models.GlVoucherEntry).filter(
        models.GlVoucherEntry.voucher_id == v.id
    ).all()
    for e in entries:
        bal = db.query(models.GlBalance).filter(
            models.GlBalance.ledger_id == v.ledger_id,
            models.GlBalance.period_id == v.period_id,
            models.GlBalance.account_id == e.account_id,
            models.GlBalance.aux_values == (e.aux_values or "{}")
        ).first()
        if bal:
            bal.period_debit -= e.debit_amount
            bal.period_credit -= e.credit_amount
            bal.end_debit = bal.begin_debit + bal.period_debit
            bal.end_credit = bal.begin_credit + bal.period_credit

    v.status = "已审核"
    v.posted_at = None
    db.commit()
    return make_response(True, v, "反过账成功")


@router.post("/vouchers/batch-audit")
def batch_audit_vouchers(voucher_ids: List[int], auditor: str = "审核人", db: Session = Depends(get_db)):
    """批量审核凭证"""
    results = {"success": 0, "failed": []}
    for vid in voucher_ids:
        v = db.query(models.GlVoucher).get(vid)
        if not v:
            results["failed"].append({"id": vid, "reason": "凭证不存在"})
            continue
        if v.status not in ("草稿", "待审核"):
            results["failed"].append({"id": vid, "reason": f"状态「{v.status}」不可审核"})
            continue
        if v.created_by and v.created_by == auditor:
            results["failed"].append({"id": vid, "reason": "制单人=审核人"})
            continue
        v.status = "已审核"
        v.audited_by = auditor
        results["success"] += 1
    db.commit()
    return make_response(True, results, f"批量审核完成：成功{results['success']}条")


# ---------- 标准账簿查询 ----------

@router.get("/books/detail")
def get_detail_ledger(
    ledger_id: int,
    account_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """明细账：按科目查逐笔分录，支持日期范围过滤"""
    q = db.query(models.GlVoucherEntry).join(models.GlVoucher).filter(
        models.GlVoucher.ledger_id == ledger_id,
        models.GlVoucherEntry.account_id == account_id,
        models.GlVoucher.status == "已过账"
    )
    if start_date:
        q = q.filter(models.GlVoucher.voucher_date >= start_date)
    if end_date:
        q = q.filter(models.GlVoucher.voucher_date <= end_date)
    items = q.order_by(models.GlVoucher.voucher_date, models.GlVoucher.voucher_no, models.GlVoucherEntry.line_no).all()
    # 附带凭证信息
    for e in items:
        e.voucher_info = db.query(models.GlVoucher).get(e.voucher_id)
    return make_response(True, items, "查询成功")


@router.get("/books/general")
def get_general_ledger(
    ledger_id: int,
    account_id: int,
    start_period: Optional[str] = None,
    end_period: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """总账：按科目汇总各期间借贷发生额和余额"""
    q = db.query(models.GlBalance).filter(
        models.GlBalance.ledger_id == ledger_id,
        models.GlBalance.account_id == account_id
    )
    if start_period:
        q = q.filter(models.GlBalance.period_id >= int(start_period))
    if end_period:
        q = q.filter(models.GlBalance.period_id <= int(end_period))
    items = q.order_by(models.GlBalance.period_id).all()
    # 附带期间信息
    for b in items:
        b.period_info = db.query(models.GlPeriod).get(b.period_id)
    return make_response(True, items, "查询成功")


@router.get("/books/journal")
def get_journal(
    ledger_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """日记账：按时间顺序列出所有已过账凭证分录"""
    q = db.query(models.GlVoucherEntry).join(models.GlVoucher).filter(
        models.GlVoucher.ledger_id == ledger_id,
        models.GlVoucher.status == "已过账"
    )
    if start_date:
        q = q.filter(models.GlVoucher.voucher_date >= start_date)
    if end_date:
        q = q.filter(models.GlVoucher.voucher_date <= end_date)
    items = q.order_by(models.GlVoucher.voucher_date, models.GlVoucher.voucher_no, models.GlVoucherEntry.line_no).all()
    # 附带凭证和科目信息
    for e in items:
        e.voucher_info = db.query(models.GlVoucher).get(e.voucher_id)
        e.account_info = db.query(models.GlAccount).get(e.account_id)
    return make_response(True, items, "查询成功")


@router.get("/books/trial-balance")
def get_trial_balance(
    ledger_id: int,
    period_id: int,
    db: Session = Depends(get_db)
):
    """试算平衡表：按期间列出所有科目的期初、本期借贷、期末余额"""
    balances = db.query(models.GlBalance).filter(
        models.GlBalance.ledger_id == ledger_id,
        models.GlBalance.period_id == period_id
    ).all()
    # 附带科目信息
    for b in balances:
        b.account_info = db.query(models.GlAccount).get(b.account_id)
    # 计算合计
    total_begin_d = sum(float(b.begin_debit or 0) for b in balances)
    total_begin_c = sum(float(b.begin_credit or 0) for b in balances)
    total_period_d = sum(float(b.period_debit or 0) for b in balances)
    total_period_c = sum(float(b.period_credit or 0) for b in balances)
    total_end_d = sum(float(b.end_debit or 0) for b in balances)
    total_end_c = sum(float(b.end_credit or 0) for b in balances)
    return make_response(True, {
        "balances": balances,
        "totals": {
            "begin_debit": total_begin_d, "begin_credit": total_begin_c,
            "period_debit": total_period_d, "period_credit": total_period_c,
            "end_debit": total_end_d, "end_credit": total_end_c,
            "balanced": abs(total_end_d - total_end_c) < 0.01
        }
    }, "查询成功")


# ---------- 余额表 ----------

@router.get("/balances")
def list_balances(
    ledger_id: int,
    period_id: int,
    account_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    q = db.query(models.GlBalance).filter(
        models.GlBalance.ledger_id == ledger_id,
        models.GlBalance.period_id == period_id
    )
    if account_id:
        q = q.filter(models.GlBalance.account_id == account_id)
    items = q.all()
    # 附带科目信息
    for b in items:
        b.account = db.query(models.GlAccount).get(b.account_id)
    return make_response(True, items, "查询成功")


# ---------- 辅助核算 ----------

@router.get("/aux-types")
def list_aux_types(ledger_id: int, db: Session = Depends(get_db)):
    items = db.query(models.GlAuxType).filter(
        models.GlAuxType.ledger_id == ledger_id,
        models.GlAuxType.status == "ACTIVE"
    ).all()
    return make_response(True, items, "查询成功")

@router.post("/aux-types")
def create_aux_type(ledger_id: int, code: str, name: str, db: Session = Depends(get_db)):
    obj = models.GlAuxType(ledger_id=ledger_id, code=code, name=name)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return make_response(True, obj, "创建成功")

@router.get("/aux-values")
def list_aux_values(aux_type_id: int, db: Session = Depends(get_db)):
    items = db.query(models.GlAuxValue).filter(
        models.GlAuxValue.aux_type_id == aux_type_id,
        models.GlAuxValue.status == "ACTIVE"
    ).all()
    return make_response(True, items, "查询成功")

@router.post("/aux-values")
def create_aux_value(aux_type_id: int, code: str, name: str, db: Session = Depends(get_db)):
    obj = models.GlAuxValue(aux_type_id=aux_type_id, code=code, name=name)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return make_response(True, obj, "创建成功")
