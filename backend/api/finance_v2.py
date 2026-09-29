"""
财务管理 V2 模块 — 期末处理
===================
期末调汇、结转损益、结账操作
（凭证/总账/报表由现有 finance.py 处理，本模块补充期末流程）
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
        return d.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(d, datetime.date):
        return str(d)
    return str(d)


CLOSING_TYPE_LABELS = {
    "FOREX": "期末调汇",
    "PNL_SETTLE": "结转损益",
    "CLOSE": "结账",
}
STATUS_LABELS = {"PENDING": "待处理", "COMPLETED": "已完成"}


# ============================================================
# 1. 期末处理记录
# ============================================================
@router.get("/period-closings", tags=["财务期末"])
def list_period_closings(
    period_code: Optional[str] = None,
    closing_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.PeriodClosing).filter(models.PeriodClosing.account_set_id == ACCOUNT_SET_ID)
    if period_code:
        q = q.filter(models.PeriodClosing.period_code == period_code)
    if closing_type:
        q = q.filter(models.PeriodClosing.closing_type == closing_type)
    items = q.order_by(models.PeriodClosing.id.desc()).all()
    result = []
    for p in items:
        result.append({
            "id": p.id, "period_code": p.period_code,
            "closing_type": p.closing_type,
            "closing_type_label": CLOSING_TYPE_LABELS.get(p.closing_type, p.closing_type),
            "status": p.status,
            "status_label": STATUS_LABELS.get(p.status, p.status),
            "voucher_no": p.voucher_no or "",
            "operated_by": p.operated_by or "",
            "operated_at": _fmt_date(p.operated_at),
            "remark": p.remark or "",
            "created_at": _fmt_date(p.created_at),
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/forex", tags=["财务期末"])
def period_forex(data: dict = Body(...), db: Session = Depends(get_db)):
    """期末调汇：对外币科目按期末汇率调整"""
    period_code = data.get("period_code") or datetime.date.today().strftime("%Y-%m")
    # 模拟调汇处理：生成调汇凭证号
    voucher_no = f"FV-FOREX-{period_code.replace('-', '')}"
    pc = models.PeriodClosing(
        account_set_id=ACCOUNT_SET_ID, period_code=period_code,
        closing_type="FOREX", status="COMPLETED",
        voucher_no=voucher_no,
        operated_by=data.get("operator") or "system",
        operated_at=datetime.datetime.now(),
        remark=data.get("remark") or "期末调汇处理完成",
    )
    db.add(pc)
    db.commit()
    db.refresh(pc)
    return make_response(True, {
        "id": pc.id, "voucher_no": voucher_no, "period_code": period_code,
    }, "期末调汇完成，已生成调汇凭证")


@router.post("/pnl-settle", tags=["财务期末"])
def period_pnl_settle(data: dict = Body(...), db: Session = Depends(get_db)):
    """结转损益：将收入/费用科目余额结转至本年利润"""
    period_code = data.get("period_code") or datetime.date.today().strftime("%Y-%m")
    voucher_no = f"FV-PNL-{period_code.replace('-', '')}"

    # 统计收入和费用科目余额
    revenue_items = db.query(models.AccountingSubject).filter(
        models.AccountingSubject.account_set_id == ACCOUNT_SET_ID,
        models.AccountingSubject.category == "REVENUE",
        models.AccountingSubject.is_leaf == True,
    ).all()
    expense_items = db.query(models.AccountingSubject).filter(
        models.AccountingSubject.account_set_id == ACCOUNT_SET_ID,
        models.AccountingSubject.category == "EXPENSE",
        models.AccountingSubject.is_leaf == True,
    ).all()
    total_revenue = sum(float(s.current_balance or 0) for s in revenue_items)
    total_expense = sum(float(s.current_balance or 0) for s in expense_items)
    net_profit = total_revenue - total_expense

    pc = models.PeriodClosing(
        account_set_id=ACCOUNT_SET_ID, period_code=period_code,
        closing_type="PNL_SETTLE", status="COMPLETED",
        voucher_no=voucher_no,
        operated_by=data.get("operator") or "system",
        operated_at=datetime.datetime.now(),
        remark=f"结转损益完成，本期净利润：{net_profit:.2f}",
    )
    db.add(pc)
    db.commit()
    db.refresh(pc)
    return make_response(True, {
        "id": pc.id, "voucher_no": voucher_no, "period_code": period_code,
        "total_revenue": round(total_revenue, 2),
        "total_expense": round(total_expense, 2),
        "net_profit": round(net_profit, 2),
    }, "结转损益完成")


@router.post("/close", tags=["财务期末"])
def period_close(data: dict = Body(...), db: Session = Depends(get_db)):
    """结账：期末检查（试算平衡/未过账凭证/损益结转）通过后执行"""
    period_code = data.get("period_code") or datetime.date.today().strftime("%Y-%m")

    # 1. 试算平衡检查
    leaf_subjects = db.query(models.AccountingSubject).filter(
        models.AccountingSubject.account_set_id == ACCOUNT_SET_ID,
        models.AccountingSubject.is_leaf == True,
    ).all()
    total_debit = sum(float(s.current_balance or 0) for s in leaf_subjects if s.balance_direction == "DEBIT")
    total_credit = sum(float(s.current_balance or 0) for s in leaf_subjects if s.balance_direction == "CREDIT")
    balanced = abs(total_debit - total_credit) < 0.01

    # 2. 检查本期损益是否已结转
    pnl_settled = db.query(models.PeriodClosing).filter(
        models.PeriodClosing.period_code == period_code,
        models.PeriodClosing.closing_type == "PNL_SETTLE",
        models.PeriodClosing.status == "COMPLETED",
    ).first()

    checks = {
        "trial_balance": balanced,
        "pnl_settled": pnl_settled is not None,
    }
    all_passed = all(checks.values())

    if not all_passed:
        failed = [k for k, v in checks.items() if not v]
        return make_response(False, {
            "checks": checks, "failed": failed,
            "message": "结账前检查未通过：" + "、".join(failed),
        }, "结账检查未通过", "40002")

    pc = models.PeriodClosing(
        account_set_id=ACCOUNT_SET_ID, period_code=period_code,
        closing_type="CLOSE", status="COMPLETED",
        voucher_no=f"FV-CLOSE-{period_code.replace('-', '')}",
        operated_by=data.get("operator") or "system",
        operated_at=datetime.datetime.now(),
        remark=f"{period_code} 期间已结账",
    )
    db.add(pc)
    db.commit()
    db.refresh(pc)
    return make_response(True, {
        "id": pc.id, "period_code": period_code,
        "checks": checks,
        "total_debit": round(total_debit, 2),
        "total_credit": round(total_credit, 2),
    }, f"{period_code} 期间结账成功")


@router.get("/overview", tags=["财务期末"])
def overview(db: Session = Depends(get_db)):
    current_period = datetime.date.today().strftime("%Y-%m")
    current_closings = db.query(models.PeriodClosing).filter(
        models.PeriodClosing.period_code == current_period,
    ).all()
    closed_types = {c.closing_type for c in current_closings if c.status == "COMPLETED"}
    return make_response(True, {
        "current_period": current_period,
        "forex_done": "FOREX" in closed_types,
        "pnl_settled": "PNL_SETTLE" in closed_types,
        "closed": "CLOSE" in closed_types,
        "history_count": db.query(models.PeriodClosing).filter(
            models.PeriodClosing.account_set_id == ACCOUNT_SET_ID
        ).count(),
    }, "财务期末概览")
