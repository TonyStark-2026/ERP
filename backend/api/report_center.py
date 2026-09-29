"""
财务报表中心 API
================
辅助报表：科目余额汇总 / 账龄分析 / 期间费用明细 / 存货明细
纳税申报：增值税申报辅助 / 附加税计算
报表版本管理 + 数据追溯
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import datetime
from decimal import Decimal

from .. import models
from ..app import make_response, get_db
from .print_router import _get_all_vouchers, _calc_account_balances, CHART_OF_ACCOUNTS, _fmt_amount, _get_company_name

router = APIRouter()


# ============================================================
# 科目余额汇总表
# ============================================================
@router.get("/account-balance", tags=["报表中心"])
async def api_account_balance(
    year_month: Optional[str] = None,
    level: int = Query(1, description="科目级次：1=一级科目，2=二级科目"),
    db: Session = Depends(get_db),
):
    """科目余额汇总表：期初/借方/贷方/期末"""
    account_set_id = 1
    company = _get_company_name(db, account_set_id)
    today = datetime.date.today()
    if year_month:
        y, m = int(year_month[:4]), int(year_month[5:7])
    else:
        y, m = today.year, today.month
    # 截止日期
    if m == 12:
        end_date = datetime.date(y, 12, 31)
    else:
        end_date = datetime.date(y, m + 1, 1) - datetime.timedelta(days=1)
    # 月初
    start_date = datetime.date(y, m, 1)

    balances = _calc_account_balances(db, account_set_id, end_date, start_date)

    items = []
    total_debit = 0
    total_credit = 0
    total_opening = 0
    total_closing = 0
    for code in sorted(balances.keys()):
        b = balances[code]
        # 按级次筛选
        if level == 1 and "." in code:
            continue
        if level == 2 and "." not in code:
            continue
        items.append({
            "account_code": code,
            "account_name": b["name"],
            "opening": round(b["opening"], 2),
            "opening_str": _fmt_amount(b["opening"]),
            "debit": round(b["debit"], 2),
            "debit_str": _fmt_amount(b["debit"]),
            "credit": round(b["credit"], 2),
            "credit_str": _fmt_amount(b["credit"]),
            "closing": round(b["closing"], 2),
            "closing_str": _fmt_amount(b["closing"]),
            "direction": "借" if b["closing"] >= 0 else "贷",
        })
        total_debit += b["debit"]
        total_credit += b["credit"]
        total_opening += abs(b["opening"])
        total_closing += abs(b["closing"])

    return make_response(True, {
        "company": company,
        "period": f"{y}年{m}月",
        "items": items,
        "total_opening": round(total_opening, 2),
        "total_debit": round(total_debit, 2),
        "total_credit": round(total_credit, 2),
        "total_closing": round(total_closing, 2),
    })


# ============================================================
# 往来账龄分析表
# ============================================================
@router.get("/aging-analysis", tags=["报表中心"])
async def api_aging_analysis(
    aux_type: str = Query("customer", description="customer=客户应收，supplier=供应商应付"),
    year_month: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """往来账龄分析：30天内/30-60/60-90/90天以上"""
    account_set_id = 1
    company = _get_company_name(db, account_set_id)
    today = datetime.date.today()
    if year_month:
        y, m = int(year_month[:4]), int(year_month[5:7])
    else:
        y, m = today.year, today.month
    if m == 12:
        report_date = datetime.date(y, 12, 31)
    else:
        report_date = datetime.date(y, m + 1, 1) - datetime.timedelta(days=1)

    # 获取已过账凭证
    vouchers = _get_all_vouchers(db, account_set_id, end_date=report_date, status_filter="POSTED")

    # 按辅助核算对象分组累计余额
    aux_data = {}
    target_account = "1122" if aux_type == "customer" else "2202"
    for v in vouchers:
        for e in v["entries"]:
            if not e["account_code"].startswith(target_account):
                continue
            name = e["account_name"]
            # 提取辅助核算名称
            if aux_type == "customer" and "客户：" in name:
                cust_name = name[name.index("客户：") + 3:].rstrip("）")
            elif aux_type == "supplier" and "供应商：" in name:
                cust_name = name[name.index("供应商：") + 4:].rstrip("）")
            else:
                continue
            if cust_name not in aux_data:
                aux_data[cust_name] = {"name": cust_name, "entries": []}
            aux_data[cust_name]["entries"].append({
                "date": v["voucher_date"],
                "voucher_no": v["voucher_no"],
                "summary": e["summary"],
                "debit": e["debit"],
                "credit": e["credit"],
            })

    # 计算余额和账龄
    items = []
    for name, data in aux_data.items():
        balance = 0
        latest_date = None
        for entry in data["entries"]:
            if aux_type == "customer":
                balance += entry["debit"] - entry["credit"]
            else:
                balance += entry["credit"] - entry["debit"]
            if not latest_date or entry["date"] > latest_date:
                latest_date = entry["date"]
        # 计算账龄天数
        if latest_date:
            d = datetime.date.fromisoformat(latest_date)
            age_days = (report_date - d).days
        else:
            age_days = 0
        # 分配到账龄区间
        if age_days <= 30:
            buckets = {"d30": abs(balance), "d60": 0, "d90": 0, "d90p": 0}
        elif age_days <= 60:
            buckets = {"d30": 0, "d60": abs(balance), "d90": 0, "d90p": 0}
        elif age_days <= 90:
            buckets = {"d30": 0, "d60": 0, "d90": abs(balance), "d90p": 0}
        else:
            buckets = {"d30": 0, "d60": 0, "d90": 0, "d90p": abs(balance)}

        items.append({
            "name": name,
            "balance": round(abs(balance), 2),
            "balance_str": _fmt_amount(abs(balance)),
            "age_days": age_days,
            "latest_date": latest_date,
            "d30": round(buckets["d30"], 2),
            "d30_str": _fmt_amount(buckets["d30"]),
            "d60": round(buckets["d60"], 2),
            "d60_str": _fmt_amount(buckets["d60"]),
            "d90": round(buckets["d90"], 2),
            "d90_str": _fmt_amount(buckets["d90"]),
            "d90p": round(buckets["d90p"], 2),
            "d90p_str": _fmt_amount(buckets["d90p"]),
        })

    items.sort(key=lambda x: x["balance"], reverse=True)
    totals = {
        "d30": sum(i["d30"] for i in items),
        "d60": sum(i["d60"] for i in items),
        "d90": sum(i["d90"] for i in items),
        "d90p": sum(i["d90p"] for i in items),
        "balance": sum(i["balance"] for i in items),
    }
    report_title = "应收账款账龄分析表" if aux_type == "customer" else "应付账款账龄分析表"
    return make_response(True, {
        "company": company,
        "report_title": report_title,
        "report_date": str(report_date),
        "aux_type": aux_type,
        "items": items,
        "totals": {
            "balance": round(totals["balance"], 2),
            "balance_str": _fmt_amount(totals["balance"]),
            "d30": round(totals["d30"], 2),
            "d30_str": _fmt_amount(totals["d30"]),
            "d60": round(totals["d60"], 2),
            "d60_str": _fmt_amount(totals["d60"]),
            "d90": round(totals["d90"], 2),
            "d90_str": _fmt_amount(totals["d90"]),
            "d90p": round(totals["d90p"], 2),
            "d90p_str": _fmt_amount(totals["d90p"]),
        },
    })


# ============================================================
# 期间费用明细表
# ============================================================
@router.get("/period-expense", tags=["报表中心"])
async def api_period_expense(
    year_month: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """期间费用明细：管理费用/销售费用/财务费用"""
    account_set_id = 1
    company = _get_company_name(db, account_set_id)
    today = datetime.date.today()
    if year_month:
        y, m = int(year_month[:4]), int(year_month[5:7])
    else:
        y, m = today.year, today.month
    start_date = datetime.date(y, m, 1)
    if m == 12:
        end_date = datetime.date(y, 12, 31)
    else:
        end_date = datetime.date(y, m + 1, 1) - datetime.timedelta(days=1)

    balances = _calc_account_balances(db, account_set_id, end_date, start_date)

    # 费用类别
    expense_categories = [
        ("管理费用", "6602"),
        ("销售费用", "6601"),
        ("财务费用", "6603"),
    ]
    groups = []
    grand_total = 0
    for cat_name, prefix in expense_categories:
        items = []
        cat_total = 0
        for code, b in balances.items():
            if code.startswith(prefix) and b["debit"] != 0:
                items.append({
                    "account_code": code,
                    "account_name": b["name"],
                    "amount": round(b["debit"], 2),
                    "amount_str": _fmt_amount(b["debit"]),
                })
                cat_total += b["debit"]
        if items or cat_total > 0:
            groups.append({
                "category": cat_name,
                "items": items,
                "total": round(cat_total, 2),
                "total_str": _fmt_amount(cat_total),
            })
            grand_total += cat_total

    return make_response(True, {
        "company": company,
        "period": f"{y}年{m}月",
        "groups": groups,
        "grand_total": round(grand_total, 2),
        "grand_total_str": _fmt_amount(grand_total),
    })


# ============================================================
# 存货明细表
# ============================================================
@router.get("/inventory-detail", tags=["报表中心"])
async def api_inventory_detail(
    year_month: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """存货明细表：按物料分类展示数量/单价/金额"""
    account_set_id = 1
    company = _get_company_name(db, account_set_id)
    today = datetime.date.today()
    if year_month:
        y, m = int(year_month[:4]), int(year_month[5:7])
    else:
        y, m = today.year, today.month
    if m == 12:
        end_date = datetime.date(y, 12, 31)
    else:
        end_date = datetime.date(y, m + 1, 1) - datetime.timedelta(days=1)

    # 查全部物料
    materials = db.query(models.Material).all()
    # 按分类分组
    categories = {}
    for mat in materials:
        cat = (mat.type.value if mat.type else "未分类") or "未分类"
        if cat not in categories:
            categories[cat] = []
        # 查库存（汇总所有库存记录）
        records = db.query(models.InventoryRecord).filter(models.InventoryRecord.material_id == mat.id).all()
        qty = sum(float(r.quantity) for r in records) if records else 0
        price = float(mat.unit_price or 0)
        amount = qty * price
        categories[cat].append({
            "material_code": mat.code,
            "material_name": mat.name,
            "unit": mat.unit or "",
            "quantity": qty,
            "unit_price": price,
            "amount": round(amount, 2),
            "amount_str": _fmt_amount(amount),
            "inventory_account": mat.inventory_account_code or "1401",
        })

    groups = []
    grand_total = 0
    for cat, items in categories.items():
        cat_total = sum(i["amount"] for i in items)
        groups.append({
            "category": cat,
            "items": items,
            "total": round(cat_total, 2),
            "total_str": _fmt_amount(cat_total),
        })
        grand_total += cat_total

    return make_response(True, {
        "company": company,
        "report_date": str(end_date),
        "groups": groups,
        "grand_total": round(grand_total, 2),
        "grand_total_str": _fmt_amount(grand_total),
    })


# ============================================================
# 增值税申报辅助表
# ============================================================
@router.get("/vat", tags=["报表中心"])
async def api_vat_report(
    year_month: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """增值税申报辅助表：销项/进项/应纳税额"""
    account_set_id = 1
    company = _get_company_name(db, account_set_id)
    today = datetime.date.today()
    if year_month:
        y, m = int(year_month[:4]), int(year_month[5:7])
    else:
        y, m = today.year, today.month
    start_date = datetime.date(y, m, 1)
    if m == 12:
        end_date = datetime.date(y, 12, 31)
    else:
        end_date = datetime.date(y, m + 1, 1) - datetime.timedelta(days=1)

    balances = _calc_account_balances(db, account_set_id, end_date, start_date)

    # 销项税额 = 2221.01.05 贷方
    output_tax = balances.get("2221.01.05", {}).get("credit", 0)
    # 进项税额 = 2221.01.01 借方
    input_tax = balances.get("2221.01.01", {}).get("debit", 0)
    # 进项转出 = 2221.01 贷方（简化）
    input_transfer = 0
    # 应纳税额 = 销项 - 进项 + 进项转出
    tax_payable = output_tax - input_tax + input_transfer

    return make_response(True, {
        "company": company,
        "period": f"{y}年{m}月",
        "output_tax": round(output_tax, 2),
        "output_tax_str": _fmt_amount(output_tax),
        "input_tax": round(input_tax, 2),
        "input_tax_str": _fmt_amount(input_tax),
        "input_transfer": round(input_transfer, 2),
        "input_transfer_str": _fmt_amount(input_transfer),
        "tax_payable": round(tax_payable, 2),
        "tax_payable_str": _fmt_amount(tax_payable),
        "is_negative": tax_payable < 0,
    })


# ============================================================
# 附加税计算表
# ============================================================
@router.get("/surtax", tags=["报表中心"])
async def api_surtax_report(
    year_month: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """附加税计算表：城建税/教育费附加/地方教育附加"""
    account_set_id = 1
    company = _get_company_name(db, account_set_id)
    today = datetime.date.today()
    if year_month:
        y, m = int(year_month[:4]), int(year_month[5:7])
    else:
        y, m = today.year, today.month

    # 先获取增值税额
    start_date = datetime.date(y, m, 1)
    if m == 12:
        end_date = datetime.date(y, 12, 31)
    else:
        end_date = datetime.date(y, m + 1, 1) - datetime.timedelta(days=1)
    balances = _calc_account_balances(db, account_set_id, end_date, start_date)
    output_tax = balances.get("2221.01.05", {}).get("credit", 0)
    input_tax = balances.get("2221.01.01", {}).get("debit", 0)
    vat_base = max(output_tax - input_tax, 0)  # 不负数

    # 城建税 7%，教育费附加 3%，地方教育附加 2%
    city_tax = vat_base * 0.07
    edu_surcharge = vat_base * 0.03
    local_edu_surcharge = vat_base * 0.02
    total = city_tax + edu_surcharge + local_edu_surcharge

    return make_response(True, {
        "company": company,
        "period": f"{y}年{m}月",
        "vat_base": round(vat_base, 2),
        "vat_base_str": _fmt_amount(vat_base),
        "city_tax": round(city_tax, 2),
        "city_tax_str": _fmt_amount(city_tax),
        "city_tax_rate": "7%",
        "edu_surcharge": round(edu_surcharge, 2),
        "edu_surcharge_str": _fmt_amount(edu_surcharge),
        "edu_surcharge_rate": "3%",
        "local_edu_surcharge": round(local_edu_surcharge, 2),
        "local_edu_surcharge_str": _fmt_amount(local_edu_surcharge),
        "local_edu_surcharge_rate": "2%",
        "total": round(total, 2),
        "total_str": _fmt_amount(total),
    })


# ============================================================
# 报表版本管理
# ============================================================
@router.get("/versions", tags=["报表中心"])
async def api_report_versions(
    report_type: str = Query(..., description="报表类型"),
    db: Session = Depends(get_db),
):
    """获取报表历史版本列表"""
    # 简化：返回虚拟版本列表
    today = datetime.date.today()
    versions = [
        {"version": f"v{today.year}{today.month:02d}", "period": f"{today.year}年{today.month}月", "created_at": f"{today}T10:00:00", "status": "current"},
        {"version": f"v{today.year}{today.month-1:02d}" if today.month > 1 else f"v{today.year-1}12", "period": f"{today.year}年{today.month-1 if today.month > 1 else 12}月", "created_at": f"{today.year}-{today.month-1 if today.month > 1 else 12}-28T10:00:00", "status": "archived"},
    ]
    return make_response(True, {"items": versions, "report_type": report_type})


# ============================================================
# 数据追溯
# ============================================================
@router.get("/trace", tags=["报表中心"])
async def api_report_trace(
    account_code: str = Query(..., description="科目编码"),
    year_month: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """追溯：展示某科目金额的构成明细"""
    account_set_id = 1
    today = datetime.date.today()
    if year_month:
        y, m = int(year_month[:4]), int(year_month[5:7])
    else:
        y, m = today.year, today.month
    start_date = datetime.date(y, m, 1)
    if m == 12:
        end_date = datetime.date(y, 12, 31)
    else:
        end_date = datetime.date(y, m + 1, 1) - datetime.timedelta(days=1)

    vouchers = _get_all_vouchers(db, account_set_id, end_date, start_date, status_filter="POSTED")
    entries = []
    total_debit = 0
    total_credit = 0
    for v in vouchers:
        for e in v["entries"]:
            if e["account_code"] == account_code or e["account_code"].startswith(account_code):
                entries.append({
                    "voucher_no": v["voucher_no"],
                    "voucher_date": v["voucher_date"],
                    "summary": e["summary"],
                    "account_code": e["account_code"],
                    "account_name": e["account_name"],
                    "debit": e["debit"],
                    "credit": e["credit"],
                    "source_doc_type": v.get("source_doc_type", ""),
                    "source_doc_no": v.get("source_doc_no", ""),
                })
                total_debit += e["debit"]
                total_credit += e["credit"]

    account_name = CHART_OF_ACCOUNTS.get(account_code, account_code)
    return make_response(True, {
        "account_code": account_code,
        "account_name": account_name,
        "period": f"{y}年{m}月",
        "entries": entries,
        "total_debit": round(total_debit, 2),
        "total_credit": round(total_credit, 2),
        "net_amount": round(total_debit - total_credit, 2),
        "entry_count": len(entries),
    })
