"""
基础设置模块
===================
会计科目表、编码规则、会计期间、角色权限、操作日志审计
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, List
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


CATEGORY_LABELS = {
    "ASSET": "资产", "LIABILITY": "负债", "EQUITY": "所有者权益",
    "REVENUE": "收入", "EXPENSE": "费用", "COST": "成本",
}

ENTITY_LABELS = {
    "MATERIAL": "物料", "SUPPLIER": "供应商", "CUSTOMER": "客户",
    "PO": "采购订单", "SO": "销售订单", "WO": "生产工单", "VOUCHER": "凭证",
}


# ============================================================
# 1. 会计科目表
# ============================================================
@router.get("/subjects", tags=["基础设置"])
def list_subjects(
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.AccountingSubject).filter(
        models.AccountingSubject.account_set_id == ACCOUNT_SET_ID
    )
    if category:
        q = q.filter(models.AccountingSubject.category == category)
    if keyword:
        q = q.filter(models.AccountingSubject.code.contains(keyword) |
                     models.AccountingSubject.name.contains(keyword))
    items = q.order_by(models.AccountingSubject.code).all()
    result = []
    for s in items:
        result.append({
            "id": s.id, "code": s.code, "name": s.name,
            "parent_code": s.parent_code or "", "level": s.level,
            "category": s.category, "category_label": CATEGORY_LABELS.get(s.category, s.category),
            "balance_direction": s.balance_direction,
            "direction_label": "借" if s.balance_direction == "DEBIT" else "贷",
            "is_leaf": s.is_leaf,
            "opening_balance": float(s.opening_balance or 0),
            "current_balance": float(s.current_balance or 0),
            "is_active": s.is_active,
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/subjects", tags=["基础设置"])
def create_subject(data: dict = Body(...), db: Session = Depends(get_db)):
    code = (data.get("code") or "").strip()
    name = (data.get("name") or "").strip()
    if not code or not name:
        return make_response(False, None, "科目编码和名称必填", "40001")
    exists = db.query(models.AccountingSubject).filter(
        models.AccountingSubject.account_set_id == ACCOUNT_SET_ID,
        models.AccountingSubject.code == code,
    ).first()
    if exists:
        return make_response(False, None, "科目编码已存在", "40002")
    subj = models.AccountingSubject(
        account_set_id=ACCOUNT_SET_ID, code=code, name=name,
        parent_code=data.get("parent_code") or None,
        level=int(data.get("level", 1)),
        category=data.get("category", "ASSET"),
        balance_direction=data.get("balance_direction", "DEBIT"),
        is_leaf=data.get("is_leaf", True),
        opening_balance=Decimal(str(data.get("opening_balance", 0))),
        current_balance=Decimal(str(data.get("opening_balance", 0))),
        is_active=data.get("is_active", True),
    )
    db.add(subj)
    db.commit()
    db.refresh(subj)
    return make_response(True, {"id": subj.id, "code": subj.code}, "科目创建成功")


@router.put("/subjects/{sid}", tags=["基础设置"])
def update_subject(sid: int, data: dict = Body(...), db: Session = Depends(get_db)):
    subj = db.query(models.AccountingSubject).filter(models.AccountingSubject.id == sid).first()
    if not subj:
        return make_response(False, None, "科目不存在", "40401")
    for f in ["name", "parent_code", "category", "balance_direction"]:
        if f in data:
            setattr(subj, f, data[f] if data[f] else None)
    for f in ["level", "is_leaf", "is_active"]:
        if f in data:
            setattr(subj, f, data[f])
    if "opening_balance" in data:
        subj.opening_balance = Decimal(str(data["opening_balance"]))
    db.commit()
    return make_response(True, {"id": subj.id}, "科目更新成功")


@router.delete("/subjects/{sid}", tags=["基础设置"])
def delete_subject(sid: int, db: Session = Depends(get_db)):
    subj = db.query(models.AccountingSubject).filter(models.AccountingSubject.id == sid).first()
    if not subj:
        return make_response(False, None, "科目不存在", "40401")
    children = db.query(models.AccountingSubject).filter(
        models.AccountingSubject.parent_code == subj.code
    ).count()
    if children > 0:
        return make_response(False, None, "存在下级科目，不能删除", "40003")
    db.delete(subj)
    db.commit()
    return make_response(True, None, "科目已删除")


@router.post("/subjects/init-template", tags=["基础设置"])
def init_subject_template(db: Session = Depends(get_db)):
    """初始化行业标准会计科目模板（企业会计准则）"""
    existing = db.query(models.AccountingSubject).filter(
        models.AccountingSubject.account_set_id == ACCOUNT_SET_ID
    ).count()
    if existing > 0:
        return make_response(False, None, f"已有{existing}条科目，请先清空再初始化", "40004")
    template = [
        ("1001", "库存现金", "ASSET", "DEBIT", None, 1),
        ("1002", "银行存款", "ASSET", "DEBIT", None, 1),
        ("1122", "应收账款", "ASSET", "DEBIT", None, 1),
        ("1123", "预付账款", "ASSET", "DEBIT", None, 1),
        ("1401", "原材料", "ASSET", "DEBIT", None, 1),
        ("1402", "在途物资", "ASSET", "DEBIT", None, 1),
        ("1405", "库存商品", "ASSET", "DEBIT", None, 1),
        ("1601", "固定资产", "ASSET", "DEBIT", None, 1),
        ("1602", "累计折旧", "ASSET", "CREDIT", None, 1),
        ("2202", "应付账款", "LIABILITY", "CREDIT", None, 1),
        ("2203", "预收账款", "LIABILITY", "CREDIT", None, 1),
        ("2211", "应付职工薪酬", "LIABILITY", "CREDIT", None, 1),
        ("2221", "应交税费", "LIABILITY", "CREDIT", None, 1),
        ("2501", "长期借款", "LIABILITY", "CREDIT", None, 1),
        ("4001", "实收资本", "EQUITY", "CREDIT", None, 1),
        ("4101", "盈余公积", "EQUITY", "CREDIT", None, 1),
        ("4103", "本年利润", "EQUITY", "CREDIT", None, 1),
        ("5001", "生产成本", "COST", "DEBIT", None, 1),
        ("5101", "制造费用", "COST", "DEBIT", None, 1),
        ("6001", "主营业务收入", "REVENUE", "CREDIT", None, 1),
        ("6051", "其他业务收入", "REVENUE", "CREDIT", None, 1),
        ("6401", "主营业务成本", "EXPENSE", "DEBIT", None, 1),
        ("6601", "销售费用", "EXPENSE", "DEBIT", None, 1),
        ("6602", "管理费用", "EXPENSE", "DEBIT", None, 1),
        ("6603", "财务费用", "EXPENSE", "DEBIT", None, 1),
    ]
    created = 0
    for code, name, cat, direction, parent, level in template:
        subj = models.AccountingSubject(
            account_set_id=ACCOUNT_SET_ID, code=code, name=name,
            parent_code=parent, level=level, category=cat,
            balance_direction=direction, is_leaf=True,
            opening_balance=Decimal("0"), current_balance=Decimal("0"),
            is_active=True,
        )
        db.add(subj)
        created += 1
    db.commit()
    return make_response(True, {"created": created}, f"已初始化{created}条标准科目")


@router.get("/subjects/trial-balance", tags=["基础设置"])
def trial_balance(db: Session = Depends(get_db)):
    """试算平衡校验"""
    items = db.query(models.AccountingSubject).filter(
        models.AccountingSubject.account_set_id == ACCOUNT_SET_ID,
        models.AccountingSubject.is_leaf == True,
    ).all()
    total_debit = 0.0
    total_credit = 0.0
    rows = []
    for s in items:
        bal = float(s.current_balance or 0)
        if s.balance_direction == "DEBIT":
            total_debit += bal
        else:
            total_credit += bal
        rows.append({
            "code": s.code, "name": s.name,
            "direction": "借" if s.balance_direction == "DEBIT" else "贷",
            "balance": bal,
        })
    balanced = abs(total_debit - total_credit) < 0.01
    return make_response(True, {
        "rows": rows, "total_debit": total_debit, "total_credit": total_credit,
        "difference": total_debit - total_credit, "balanced": balanced,
        "balanced_label": "平衡" if balanced else "不平衡",
    })


# ============================================================
# 2. 编码规则
# ============================================================
@router.get("/coding-rules", tags=["基础设置"])
def list_coding_rules(db: Session = Depends(get_db)):
    items = db.query(models.CodingRule).filter(
        models.CodingRule.account_set_id == ACCOUNT_SET_ID
    ).order_by(models.CodingRule.entity_type).all()
    result = []
    for r in items:
        result.append({
            "id": r.id, "entity_type": r.entity_type,
            "entity_label": ENTITY_LABELS.get(r.entity_type, r.entity_type),
            "prefix": r.prefix or "", "date_format": r.date_format or "",
            "seq_length": r.seq_length, "reset_cycle": r.reset_cycle,
            "separator": r.separator or "", "is_active": r.is_active,
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/coding-rules", tags=["基础设置"])
def create_coding_rule(data: dict = Body(...), db: Session = Depends(get_db)):
    et = (data.get("entity_type") or "").strip()
    if not et:
        return make_response(False, None, "实体类型必填", "40001")
    exists = db.query(models.CodingRule).filter(
        models.CodingRule.account_set_id == ACCOUNT_SET_ID,
        models.CodingRule.entity_type == et,
    ).first()
    if exists:
        return make_response(False, None, "该实体已有编码规则", "40002")
    rule = models.CodingRule(
        account_set_id=ACCOUNT_SET_ID, entity_type=et,
        prefix=data.get("prefix") or None,
        date_format=data.get("date_format") or None,
        seq_length=int(data.get("seq_length", 4)),
        reset_cycle=data.get("reset_cycle", "YEARLY"),
        separator=data.get("separator", "-"),
        is_active=data.get("is_active", True),
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return make_response(True, {"id": rule.id}, "编码规则创建成功")


@router.put("/coding-rules/{rid}", tags=["基础设置"])
def update_coding_rule(rid: int, data: dict = Body(...), db: Session = Depends(get_db)):
    rule = db.query(models.CodingRule).filter(models.CodingRule.id == rid).first()
    if not rule:
        return make_response(False, None, "编码规则不存在", "40401")
    for f in ["prefix", "date_format", "reset_cycle", "separator"]:
        if f in data:
            setattr(rule, f, data[f] if data[f] else None)
    for f in ["seq_length", "is_active"]:
        if f in data:
            setattr(rule, f, data[f])
    db.commit()
    return make_response(True, {"id": rule.id}, "编码规则更新成功")


@router.delete("/coding-rules/{rid}", tags=["基础设置"])
def delete_coding_rule(rid: int, db: Session = Depends(get_db)):
    rule = db.query(models.CodingRule).filter(models.CodingRule.id == rid).first()
    if not rule:
        return make_response(False, None, "编码规则不存在", "40401")
    db.delete(rule)
    db.commit()
    return make_response(True, None, "编码规则已删除")


@router.get("/coding-rules/preview", tags=["基础设置"])
def preview_coding_rule(
    entity_type: str = Query(...),
    prefix: Optional[str] = None,
    date_format: Optional[str] = None,
    seq_length: int = Query(4),
    separator: str = Query("-"),
):
    """预览编码生成结果"""
    parts = []
    if prefix:
        parts.append(prefix)
    if date_format and date_format != "none":
        now = datetime.datetime.now()
        fmt_map = {"YYYYMMDD": "%Y%m%d", "YYYYMM": "%Y%m"}
        parts.append(now.strftime(fmt_map.get(date_format, "%Y%m%d")))
    parts.append("0" * max(seq_length - 1, 0) + "1")
    sample = separator.join(parts) if separator else "".join(parts)
    return make_response(True, {"sample": sample})


# ============================================================
# 3. 会计期间
# ============================================================
@router.get("/periods", tags=["基础设置"])
def list_periods(year: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(models.AccountingPeriod).filter(
        models.AccountingPeriod.account_set_id == ACCOUNT_SET_ID
    )
    if year:
        q = q.filter(models.AccountingPeriod.year == year)
    items = q.order_by(models.AccountingPeriod.year.desc(),
                      models.AccountingPeriod.month.desc()).all()
    result = []
    for p in items:
        result.append({
            "id": p.id, "year": p.year, "month": p.month,
            "period_code": p.period_code,
            "start_date": _fmt_date(p.start_date), "end_date": _fmt_date(p.end_date),
            "status": p.status,
            "status_label": "已开" if p.status == "OPEN" else "已关",
            "closed_at": _fmt_date(p.closed_at), "closed_by": p.closed_by or "",
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/periods/init-year", tags=["基础设置"])
def init_year_periods(data: dict = Body(...), db: Session = Depends(get_db)):
    """初始化指定年度的12个会计期间"""
    year = int(data.get("year", datetime.date.today().year))
    existing = db.query(models.AccountingPeriod).filter(
        models.AccountingPeriod.account_set_id == ACCOUNT_SET_ID,
        models.AccountingPeriod.year == year,
    ).count()
    if existing > 0:
        return make_response(False, None, f"{year}年已有{existing}个期间", "40002")
    created = 0
    for m in range(1, 13):
        start = datetime.date(year, m, 1)
        if m == 12:
            end = datetime.date(year, 12, 31)
        else:
            end = datetime.date(year, m + 1, 1) - datetime.timedelta(days=1)
        period = models.AccountingPeriod(
            account_set_id=ACCOUNT_SET_ID, year=year, month=m,
            period_code=f"{year}-{m:02d}", start_date=start, end_date=end,
            status="OPEN",
        )
        db.add(period)
        created += 1
    db.commit()
    return make_response(True, {"created": created}, f"已初始化{year}年{created}个期间")


@router.post("/periods/{pid}/close", tags=["基础设置"])
def close_period(pid: int, data: dict = Body(default={}), db: Session = Depends(get_db)):
    period = db.query(models.AccountingPeriod).filter(models.AccountingPeriod.id == pid).first()
    if not period:
        return make_response(False, None, "期间不存在", "40401")
    if period.status == "CLOSED":
        return make_response(False, None, "期间已关闭", "40003")
    period.status = "CLOSED"
    period.closed_at = datetime.datetime.utcnow()
    period.closed_by = data.get("username", "system")
    db.commit()
    return make_response(True, None, f"{period.period_code}已结账")


@router.post("/periods/{pid}/reopen", tags=["基础设置"])
def reopen_period(pid: int, db: Session = Depends(get_db)):
    period = db.query(models.AccountingPeriod).filter(models.AccountingPeriod.id == pid).first()
    if not period:
        return make_response(False, None, "期间不存在", "40401")
    period.status = "OPEN"
    period.closed_at = None
    period.closed_by = None
    db.commit()
    return make_response(True, None, f"{period.period_code}已重新开启")


# ============================================================
# 4. 角色权限
# ============================================================
@router.get("/roles", tags=["基础设置"])
def list_roles(db: Session = Depends(get_db)):
    items = db.query(models.Role).order_by(models.Role.id).all()
    result = []
    for r in items:
        result.append({
            "id": r.id, "name": r.name, "description": r.description or "",
            "permissions": r.permissions or "", "is_active": r.is_active,
            "created_at": _fmt_date(r.created_at),
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/roles", tags=["基础设置"])
def create_role(data: dict = Body(...), db: Session = Depends(get_db)):
    name = (data.get("name") or "").strip()
    if not name:
        return make_response(False, None, "角色名称必填", "40001")
    exists = db.query(models.Role).filter(models.Role.name == name).first()
    if exists:
        return make_response(False, None, "角色名称已存在", "40002")
    import json
    perms = data.get("permissions")
    if isinstance(perms, (list, dict)):
        perms = json.dumps(perms, ensure_ascii=False)
    role = models.Role(
        account_set_id=ACCOUNT_SET_ID, name=name,
        description=data.get("description"),
        permissions=perms, is_active=data.get("is_active", True),
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return make_response(True, {"id": role.id}, "角色创建成功")


@router.put("/roles/{rid}", tags=["基础设置"])
def update_role(rid: int, data: dict = Body(...), db: Session = Depends(get_db)):
    role = db.query(models.Role).filter(models.Role.id == rid).first()
    if not role:
        return make_response(False, None, "角色不存在", "40401")
    for f in ["name", "description"]:
        if f in data:
            setattr(role, f, data[f] if data[f] else None)
    if "permissions" in data:
        import json
        perms = data["permissions"]
        if isinstance(perms, (list, dict)):
            perms = json.dumps(perms, ensure_ascii=False)
        role.permissions = perms
    if "is_active" in data:
        role.is_active = data["is_active"]
    db.commit()
    return make_response(True, {"id": role.id}, "角色更新成功")


@router.delete("/roles/{rid}", tags=["基础设置"])
def delete_role(rid: int, db: Session = Depends(get_db)):
    role = db.query(models.Role).filter(models.Role.id == rid).first()
    if not role:
        return make_response(False, None, "角色不存在", "40401")
    db.delete(role)
    db.commit()
    return make_response(True, None, "角色已删除")


# ============================================================
# 5. 操作日志
# ============================================================
@router.get("/logs", tags=["基础设置"])
def list_logs(
    module: Optional[str] = None,
    username: Optional[str] = None,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(models.OperationLog)
    if module:
        q = q.filter(models.OperationLog.module == module)
    if username:
        q = q.filter(models.OperationLog.username.contains(username))
    items = q.order_by(models.OperationLog.id.desc()).limit(limit).all()
    result = []
    for l in items:
        result.append({
            "id": l.id, "user_id": l.user_id, "username": l.username or "",
            "module": l.module, "action": l.action,
            "target_type": l.target_type or "", "target_id": l.target_id or "",
            "detail": l.detail or "", "ip_address": l.ip_address or "",
            "created_at": _fmt_date(l.created_at),
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/logs", tags=["基础设置"])
def add_log(data: dict = Body(...), db: Session = Depends(get_db)):
    log = models.OperationLog(
        user_id=data.get("user_id"), username=data.get("username"),
        module=data.get("module", "SYSTEM"), action=data.get("action", "VIEW"),
        target_type=data.get("target_type"), target_id=data.get("target_id"),
        detail=data.get("detail"), ip_address=data.get("ip_address"),
    )
    db.add(log)
    db.commit()
    return make_response(True, {"id": log.id}, "日志已记录")


@router.get("/overview", tags=["基础设置"])
def overview(db: Session = Depends(get_db)):
    """基础设置总览统计"""
    subj_count = db.query(models.AccountingSubject).filter(
        models.AccountingSubject.account_set_id == ACCOUNT_SET_ID
    ).count()
    rule_count = db.query(models.CodingRule).filter(
        models.CodingRule.account_set_id == ACCOUNT_SET_ID
    ).count()
    period_open = db.query(models.AccountingPeriod).filter(
        models.AccountingPeriod.account_set_id == ACCOUNT_SET_ID,
        models.AccountingPeriod.status == "OPEN",
    ).count()
    role_count = db.query(models.Role).filter(models.Role.is_active == True).count()
    log_count = db.query(models.OperationLog).count()
    # 试算平衡
    items = db.query(models.AccountingSubject).filter(
        models.AccountingSubject.account_set_id == ACCOUNT_SET_ID,
        models.AccountingSubject.is_leaf == True,
    ).all()
    td = sum(float(s.current_balance or 0) for s in items if s.balance_direction == "DEBIT")
    tc = sum(float(s.current_balance or 0) for s in items if s.balance_direction == "CREDIT")
    return make_response(True, {
        "subject_count": subj_count, "rule_count": rule_count,
        "period_open": period_open, "role_count": role_count,
        "log_count": log_count,
        "total_debit": td, "total_credit": tc,
        "balanced": abs(td - tc) < 0.01,
    })
