"""
打印中心 API —— 会计凭证与报表一体化打印模板
==============================================
6种模板：记账凭证 / 总分类账 / 明细分类账 / 资产负债表 / 利润表 / 现金流量表
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import datetime
from decimal import Decimal

from .. import models
from ..app import make_response, get_db

router = APIRouter()

# ============================================================
# 标准科目编码表（中国会计准则）
# ============================================================
CHART_OF_ACCOUNTS = {
    # 资产类
    "1001": "库存现金", "1002": "银行存款", "1121": "应收票据", "1122": "应收账款",
    "1123": "预付账款", "1131": "应收股利", "1221": "其他应收款", "1231": "坏账准备",
    "1401": "原材料", "1402": "在途物资", "1403": "库存商品", "1404": "材料成本差异", "1405": "在途物资",
    "1411": "周转材料", "1471": "存货跌价准备", "1501": "固定资产", "1502": "累计折旧",
    "1503": "固定资产减值准备", "1601": "无形资产", "1602": "累计摊销",
    "1701": "长期待摊费用", "1801": "长期股权投资",
    # 负债类
    "2201": "应付票据", "2202": "应付账款", "2203": "预收账款", "2211": "应付职工薪酬",
    "2221": "应交税费", "2221.01": "应交增值税", "2221.01.01": "进项税额",
    "2221.01.05": "销项税额", "2221.02": "应交所得税", "2241": "其他应付款",
    "2501": "长期借款", "2502": "应付债券",
    # 所有者权益
    "4001": "实收资本", "4002": "资本公积", "4101": "盈余公积", "4103": "本年利润",
    "4104": "利润分配",
    # 成本类
    "5001": "生产成本", "5001.01": "直接材料", "5001.02": "直接人工",
    "5001.03": "制造费用", "5101": "制造费用", "5201": "劳务成本",
    # 损益类
    "6001": "主营业务收入", "6051": "其他业务收入", "6101": "公允价值变动损益",
    "6111": "投资收益", "6301": "营业外收入", "6401": "主营业务成本",
    "6402": "其他业务成本", "6403": "营业税金及附加", "6601": "销售费用",
    "6602": "管理费用", "6603": "财务费用", "6701": "资产减值损失",
    "6711": "营业外支出", "6801": "所得税费用",
}

# 资产负债表项目映射
BS_ASSETS = [
    # (项目名称, [科目编码列表], 排序)
    ("货币资金", ["1001", "1002"]),
    ("应收票据", ["1121"]),
    ("应收账款", ["1122"]),
    ("预付款项", ["1123"]),
    ("应收利息", ["1131"]),
    ("其他应收款", ["1221"]),
    ("存货", ["1401", "1402", "1403", "1404", "1405", "1411"]),
    ("固定资产", ["1501"]),
    ("累计折旧", ["1502"]),
    ("无形资产", ["1601"]),
    ("长期待摊费用", ["1701"]),
    ("长期股权投资", ["1801"]),
]

BS_LIABILITIES = [
    ("短期借款", ["2201"]),
    ("应付票据", ["2201"]),
    ("应付账款", ["2202"]),
    ("预收款项", ["2203"]),
    ("应付职工薪酬", ["2211"]),
    ("应交税费", ["2221"]),
    ("其他应付款", ["2241"]),
    ("长期借款", ["2501"]),
    ("应付债券", ["2502"]),
]

BS_EQUITY = [
    ("实收资本", ["4001"]),
    ("资本公积", ["4002"]),
    ("盈余公积", ["4101"]),
    ("未分配利润", ["4103", "4104"]),
]

# 利润表项目映射
IS_ITEMS = [
    ("营业收入", ["6001", "6051"]),
    ("营业成本", ["6401", "6402"]),
    ("营业税金及附加", ["6403"]),
    ("销售费用", ["6601"]),
    ("管理费用", ["6602"]),
    ("财务费用", ["6603"]),
    ("资产减值损失", ["6701"]),
    ("公允价值变动收益", ["6101"]),
    ("投资收益", ["6111"]),
    ("营业利润", []),  # 计算项
    ("营业外收入", ["6301"]),
    ("营业外支出", ["6711"]),
    ("利润总额", []),  # 计算项
    ("所得税费用", ["6801"]),
    ("净利润", []),  # 计算项
]

# 现金流量表项目
CF_ITEMS_OPERATING = [
    ("销售商品、提供劳务收到的现金", ["6001"]),
    ("收到的税费返还", []),
    ("收到其他与经营活动有关的现金", []),
    ("购买商品、接受劳务支付的现金", ["6401"]),
    ("支付给职工以及为职工支付的现金", ["5001.02", "2211"]),
    ("支付的各项税费", ["2221.02"]),
    ("支付其他与经营活动有关的现金", ["6601", "6602"]),
]

CF_ITEMS_INVESTING = [
    ("收回投资收到的现金", []),
    ("取得投资收益收到的现金", []),
    ("处置固定资产收回的现金净额", []),
    ("购建固定资产支付的现金", ["1501"]),
    ("投资支付的现金", ["1801"]),
]

CF_ITEMS_FINANCING = [
    ("取得借款收到的现金", ["2501"]),
    ("偿还债务支付的现金", []),
    ("分配股利、利润或偿付利息支付的现金", []),
]


# ============================================================
# 工具函数
# ============================================================
def _fmt_amount(val) -> str:
    """格式化金额：千分位 + 两位小数"""
    if val is None:
        return "—"
    v = float(val)
    if v == 0:
        return "—"
    if v < 0:
        return f"-{abs(v):,.2f}"
    return f"{v:,.2f}"


def _amount_cn(val) -> str:
    """金额转中文大写"""
    if val is None:
        return "零元整"
    v = float(val)
    if v == 0:
        return "零元整"
    digits = "零壹贰叁肆伍陆柒捌玖"
    units = ["", "拾", "佰", "仟"]
    big_units = ["", "万", "亿"]
    negative = v < 0
    v = abs(v)
    integer_part = int(v)
    decimal_part = round((v - integer_part) * 100)
    jiao = decimal_part // 10
    fen = decimal_part % 10
    if integer_part == 0:
        int_str = "零"
    else:
        int_str = ""
        s = str(integer_part)
        n = len(s)
        for i, ch in enumerate(s):
            d = int(ch)
            pos = n - 1 - i
            unit_idx = pos % 4
            big_idx = pos // 4
            if d != 0:
                int_str += digits[d] + units[unit_idx]
                if unit_idx == 0 and big_idx > 0:
                    int_str += big_units[big_idx]
            else:
                if not int_str.endswith("零"):
                    int_str += "零"
        int_str = int_str.rstrip("零")
    result = ("负" if negative else "") + int_str + "元"
    if jiao == 0 and fen == 0:
        result += "整"
    else:
        result += (digits[jiao] + "角" if jiao > 0 else "零角")
        result += (digits[fen] + "分" if fen > 0 else "")
    return result


def _get_company_name(db, account_set_id=1):
    acc = db.query(models.AccountSet).filter(models.AccountSet.id == account_set_id).first()
    return acc.company_name if acc else "示例公司"


def _get_all_vouchers(db, account_set_id=1, start_date=None, end_date=None, status_filter=None):
    """获取凭证列表（合并 VoucherDB 和 AutoVoucher）"""
    result = []
    # 1. 手动凭证
    q = db.query(models.VoucherDB).filter(models.VoucherDB.account_set_id == account_set_id)
    if start_date:
        q = q.filter(models.VoucherDB.voucher_date >= start_date)
    if end_date:
        q = q.filter(models.VoucherDB.voucher_date <= end_date)
    if status_filter:
        status_map = {"DRAFT": "DRAFT", "PENDING": "PENDING", "APPROVED": "APPROVED", "POSTED": "POSTED"}
        if status_filter in status_map:
            q = q.filter(models.VoucherDB.status == status_map[status_filter])
    for v in q.order_by(models.VoucherDB.voucher_date, models.VoucherDB.voucher_no).all():
        entries = []
        for e in v.entries:
            aux = ""
            if e.customer_id:
                c = db.query(models.Customer).filter(models.Customer.id == e.customer_id).first()
                if c:
                    aux = f"（客户：{c.name}）"
            elif e.supplier_id:
                s = db.query(models.Supplier).filter(models.Supplier.id == e.supplier_id).first()
                if s:
                    aux = f"（供应商：{s.name}）"
            elif e.material_id:
                m = db.query(models.Material).filter(models.Material.id == e.material_id).first()
                if m:
                    aux = f"（物料：{m.name}）"
            entries.append({
                "account_code": e.account_code,
                "account_name": e.account_name + aux,
                "debit": float(e.debit or 0),
                "credit": float(e.credit or 0),
                "summary": e.summary or "",
            })
        result.append({
            "voucher_no": v.voucher_no,
            "voucher_date": str(v.voucher_date),
            "status": v.status.value if hasattr(v.status, 'value') else str(v.status),
            "attachments": v.attachments or 0,
            "preparer": v.preparer or "",
            "approver": v.approver or "",
            "poster": v.poster or "",
            "entries": entries,
            "total_debit": sum(e["debit"] for e in entries),
            "total_credit": sum(e["credit"] for e in entries),
        })
    # 2. 自动凭证
    q2 = db.query(models.AutoVoucher).filter(models.AutoVoucher.account_set_id == account_set_id)
    if start_date:
        q2 = q2.filter(models.AutoVoucher.voucher_date >= start_date)
    if end_date:
        q2 = q2.filter(models.AutoVoucher.voucher_date <= end_date)
    if status_filter:
        q2 = q2.filter(models.AutoVoucher.status == status_filter)
    for v in q2.order_by(models.AutoVoucher.voucher_date, models.AutoVoucher.voucher_no).all():
        entries = []
        for e in v.entries:
            aux = ""
            if e.customer_id:
                c = db.query(models.Customer).filter(models.Customer.id == e.customer_id).first()
                if c:
                    aux = f"（客户：{c.name}）"
            elif e.supplier_id:
                s = db.query(models.Supplier).filter(models.Supplier.id == e.supplier_id).first()
                if s:
                    aux = f"（供应商：{s.name}）"
            elif e.material_id:
                m = db.query(models.Material).filter(models.Material.id == e.material_id).first()
                if m:
                    aux = f"（物料：{m.name}）"
            entries.append({
                "account_code": e.account_code,
                "account_name": e.account_name + aux,
                "debit": float(e.amount) if e.side == "debit" else 0,
                "credit": float(e.amount) if e.side == "credit" else 0,
                "summary": e.summary or "",
            })
        result.append({
            "voucher_no": v.voucher_no,
            "voucher_date": str(v.voucher_date),
            "status": v.status,
            "attachments": 1,
            "preparer": v.approved_by or "系统自动",
            "approver": v.approved_by or "",
            "poster": v.approved_by or "",
            "entries": entries,
            "total_debit": float(v.total_debit or 0),
            "total_credit": float(v.total_credit or 0),
            "source_doc_type": v.source_doc_type,
            "source_doc_no": v.source_doc_no,
        })
    result.sort(key=lambda x: (x["voucher_date"], x["voucher_no"]))
    return result


def _calc_account_balances(db, account_set_id, end_date, start_date=None):
    """计算各科目余额（期初+本期借方+本期贷方+期末）"""
    balances = {}  # code -> {opening, debit, credit, closing}
    # 初始化所有科目
    for code, name in CHART_OF_ACCOUNTS.items():
        balances[code] = {"name": name, "opening": 0, "debit": 0, "credit": 0, "closing": 0}
    # 汇总凭证数据
    vouchers = _get_all_vouchers(db, account_set_id, end_date=end_date, status_filter="POSTED")
    for v in vouchers:
        for e in v["entries"]:
            code = e["account_code"]
            if code not in balances:
                balances[code] = {"name": e["account_name"], "opening": 0, "debit": 0, "credit": 0, "closing": 0}
            if start_date and v["voucher_date"] >= str(start_date):
                balances[code]["debit"] += e["debit"]
                balances[code]["credit"] += e["credit"]
            elif not start_date:
                balances[code]["debit"] += e["debit"]
                balances[code]["credit"] += e["credit"]
    # 计算期末余额
    for code, b in balances.items():
        if code.startswith("1") or code.startswith("5"):
            # 资产/成本类：借方余额
            b["closing"] = b["opening"] + b["debit"] - b["credit"]
        elif code.startswith("2") or code.startswith("4") or code.startswith("6"):
            # 负债/权益/损益类：贷方余额
            b["closing"] = b["opening"] + b["credit"] - b["debit"]
    return balances


# ============================================================
# API 端点
# ============================================================

@router.get("/templates", tags=["打印中心"])
async def api_print_templates():
    """获取可用打印模板列表"""
    templates = [
        {"code": "voucher", "name": "记账凭证", "orientation": "portrait", "description": "通用记账凭证打印，每页A4可容纳5张"},
        {"code": "general_ledger", "name": "总分类账", "orientation": "portrait", "description": "按科目分页打印总账"},
        {"code": "subsidiary_ledger", "name": "明细分类账", "orientation": "portrait", "description": "按辅助核算明细打印"},
        {"code": "balance_sheet", "name": "资产负债表", "orientation": "landscape", "description": "账户式资产负债表"},
        {"code": "income_statement", "name": "利润表", "orientation": "landscape", "description": "多步式利润表"},
        {"code": "cash_flow", "name": "现金流量表", "orientation": "landscape", "description": "直接法现金流量表"},
    ]
    return make_response(True, {"items": templates})


@router.get("/voucher", tags=["打印中心"])
async def api_print_voucher(
    start_no: Optional[str] = None,
    end_no: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """记账凭证打印数据"""
    account_set_id = 1
    sd = datetime.date.fromisoformat(start_date) if start_date else None
    ed = datetime.date.fromisoformat(end_date) if end_date else None
    vouchers = _get_all_vouchers(db, account_set_id, sd, ed, status)
    # 按凭证号范围筛选
    if start_no:
        vouchers = [v for v in vouchers if v["voucher_no"] >= start_no]
    if end_no:
        vouchers = [v for v in vouchers if v["voucher_no"] <= end_no]
    company = _get_company_name(db, account_set_id)
    items = []
    for v in vouchers:
        total = v["total_debit"]
        items.append({
            "voucher_no": v["voucher_no"],
            "voucher_date": v["voucher_date"],
            "company": company,
            "attachments": v["attachments"],
            "preparer": v["preparer"],
            "approver": v["approver"],
            "poster": v["poster"],
            "entries": v["entries"],
            "total_debit": v["total_debit"],
            "total_credit": v["total_credit"],
            "total_cn": _amount_cn(total),
            "source_doc_type": v.get("source_doc_type", ""),
            "source_doc_no": v.get("source_doc_no", ""),
        })
    # 分页：每页5张
    per_page = 5
    pages = [items[i:i+per_page] for i in range(0, len(items), per_page)] if items else [[]]
    return make_response(True, {
        "company": company,
        "template": "记账凭证",
        "orientation": "portrait",
        "pages": pages,
        "total_pages": len(pages),
        "total_vouchers": len(items),
    })


@router.get("/general-ledger", tags=["打印中心"])
async def api_print_general_ledger(
    start_month: Optional[str] = None,
    end_month: Optional[str] = None,
    account_code: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """总分类账打印数据"""
    account_set_id = 1
    company = _get_company_name(db, account_set_id)
    year = datetime.date.today().year
    # 确定月份范围
    sm = int(start_month) if start_month else 1
    em = int(end_month) if end_month else datetime.date.today().month
    # 获取已过账凭证
    vouchers = _get_all_vouchers(db, account_set_id, status_filter="POSTED")
    # 按科目汇总
    accounts = {}
    for v in vouchers:
        for e in v["entries"]:
            code = e["account_code"]
            vmonth = int(v["voucher_date"][5:7])
            if vmonth < sm or vmonth > em:
                continue
            if account_code and not code.startswith(account_code):
                continue
            if code not in accounts:
                accounts[code] = {
                    "account_code": code,
                    "account_name": CHART_OF_ACCOUNTS.get(code, e["account_name"]),
                    "opening": 0,
                    "entries": [],
                }
            accounts[code]["entries"].append({
                "date": v["voucher_date"],
                "voucher_no": v["voucher_no"],
                "summary": e["summary"],
                "debit": e["debit"],
                "credit": e["credit"],
            })
    # 计算余额
    pages = []
    for code in sorted(accounts.keys()):
        acc = accounts[code]
        balance = acc["opening"]
        monthly_totals = {}
        for entry in acc["entries"]:
            balance += entry["debit"] - entry["credit"]
            entry["balance"] = balance
            entry["direction"] = "借" if balance >= 0 else "贷"
            m = int(entry["date"][5:7])
            if m not in monthly_totals:
                monthly_totals[m] = {"debit": 0, "credit": 0}
            monthly_totals[m]["debit"] += entry["debit"]
            monthly_totals[m]["credit"] += entry["credit"]
        # 添加月度合计
        for m in sorted(monthly_totals.keys()):
            acc["entries"].append({
                "date": f"{year}-{m:02d}-28",
                "voucher_no": "",
                "summary": "本月合计",
                "debit": monthly_totals[m]["debit"],
                "credit": monthly_totals[m]["credit"],
                "balance": balance,
                "direction": "借" if balance >= 0 else "贷",
                "is_monthly_total": True,
            })
        # 本年累计
        total_d = sum(e["debit"] for e in acc["entries"] if not e.get("is_monthly_total"))
        total_c = sum(e["credit"] for e in acc["entries"] if not e.get("is_monthly_total"))
        acc["entries"].append({
            "date": f"{year}-12-31",
            "voucher_no": "",
            "summary": "本年累计",
            "debit": total_d,
            "credit": total_c,
            "balance": balance,
            "direction": "借" if balance >= 0 else "贷",
            "is_yearly_total": True,
        })
        acc["closing"] = balance
        pages.append(acc)
    return make_response(True, {
        "company": company,
        "year": year,
        "template": "总分类账",
        "orientation": "portrait",
        "accounts": pages,
        "total_accounts": len(pages),
    })


@router.get("/subsidiary-ledger", tags=["打印中心"])
async def api_print_subsidiary_ledger(
    account_code: Optional[str] = None,
    aux_type: Optional[str] = None,
    start_month: Optional[str] = None,
    end_month: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """明细分类账打印数据"""
    account_set_id = 1
    company = _get_company_name(db, account_set_id)
    year = datetime.date.today().year
    sm = int(start_month) if start_month else 1
    em = int(end_month) if end_month else datetime.date.today().month
    vouchers = _get_all_vouchers(db, account_set_id, status_filter="POSTED")
    # 按辅助核算分组
    aux_groups = {}
    for v in vouchers:
        vmonth = int(v["voucher_date"][5:7])
        if vmonth < sm or vmonth > em:
            continue
        for e in v["entries"]:
            code = e["account_code"]
            if account_code and not code.startswith(account_code):
                continue
            # 提取辅助核算名称
            aux_name = ""
            aux_key = "_default"
            name = e["account_name"]
            if "（客户：" in name:
                aux_name = name[name.index("（客户：")+4:name.rindex("）")] if "）" in name else ""
                aux_key = f"customer_{aux_name}"
            elif "（供应商：" in name:
                aux_name = name[name.index("（供应商：")+5:name.rindex("）")] if "）" in name else ""
                aux_key = f"supplier_{aux_name}"
            elif "（物料：" in name:
                aux_name = name[name.index("（物料：")+4:name.rindex("）")] if "）" in name else ""
                aux_key = f"material_{aux_name}"
            if aux_type and not aux_key.startswith(aux_type):
                continue
            if aux_key not in aux_groups:
                aux_groups[aux_key] = {
                    "aux_type": aux_key.split("_")[0],
                    "aux_name": aux_name,
                    "account_code": code,
                    "account_name": CHART_OF_ACCOUNTS.get(code, code),
                    "entries": [],
                    "opening": 0,
                }
            aux_groups[aux_key]["entries"].append({
                "date": v["voucher_date"],
                "voucher_no": v["voucher_no"],
                "summary": e["summary"],
                "debit": e["debit"],
                "credit": e["credit"],
            })
    # 计算余额
    pages = []
    for key in sorted(aux_groups.keys()):
        g = aux_groups[key]
        balance = g["opening"]
        for entry in g["entries"]:
            balance += entry["debit"] - entry["credit"]
            entry["balance"] = balance
            entry["direction"] = "借" if balance >= 0 else "贷"
        g["closing"] = balance
        pages.append(g)
    return make_response(True, {
        "company": company,
        "year": year,
        "template": "明细分类账",
        "orientation": "portrait",
        "groups": pages,
        "total_groups": len(pages),
    })


@router.get("/balance-sheet", tags=["打印中心"])
async def api_print_balance_sheet(
    year_month: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """资产负债表打印数据"""
    data = _build_balance_sheet_data(db, year_month)
    return make_response(True, data)


def _build_balance_sheet_data(db: Session, year_month: Optional[str] = None):
    """资产负债表数据构建（供 JSON 打印与 Excel 导出共用）"""
    account_set_id = 1
    company = _get_company_name(db, account_set_id)
    today = datetime.date.today()
    if year_month:
        y, m = int(year_month[:4]), int(year_month[5:7])
    else:
        y, m = today.year, today.month
    # 报表日期：当月最后一天
    if m == 12:
        report_date = datetime.date(y, 12, 31)
    else:
        report_date = datetime.date(y, m + 1, 1) - datetime.timedelta(days=1)
    # 年初日期
    year_start = datetime.date(y, 1, 1)
    # 计算期末余额
    end_balances = _calc_account_balances(db, account_set_id, report_date)
    # 年初余额（简化：期初=0，实际应取上年结转）
    start_balances = _calc_account_balances(db, account_set_id, year_start)
    
    def sum_accounts(item_list, balances, field="closing"):
        total = 0
        for name, codes in item_list:
            for code in codes:
                if code in balances:
                    total += balances[code][field]
        return total
    
    # 构建资产项目
    asset_items = []
    asset_total_current = 0
    asset_total_non_current = 0
    asset_begin_current = 0
    asset_begin_non_current = 0
    for name, codes in BS_ASSETS:
        end_val = sum((end_balances[c]["closing"] if c in end_balances else 0) for c in codes)
        start_val = sum((start_balances[c]["closing"] if c in start_balances else 0) for c in codes)
        if name == "累计折旧":
            end_val = -abs(end_val)
            start_val = -abs(start_val)
        if name in ["货币资金", "应收票据", "应收账款", "预付款项", "应收利息", "其他应收款", "存货"]:
            asset_total_current += end_val
            asset_begin_current += start_val
        else:
            asset_total_non_current += end_val
            asset_begin_non_current += start_val
        asset_items.append({
            "name": name,
            "ending": end_val,
            "beginning": start_val,
            "ending_str": _fmt_amount(end_val),
            "beginning_str": _fmt_amount(start_val),
        })
    asset_total = asset_total_current + asset_total_non_current
    asset_begin_total = asset_begin_current + asset_begin_non_current
    
    # 构建负债项目
    liability_items = []
    liability_total_current = 0
    liability_total_non_current = 0
    liability_begin_current = 0
    liability_begin_non_current = 0
    for name, codes in BS_LIABILITIES:
        end_val = sum((end_balances[c]["closing"] if c in end_balances else 0) for c in codes)
        start_val = sum((start_balances[c]["closing"] if c in start_balances else 0) for c in codes)
        if name in ["短期借款", "应付票据", "应付账款", "预收款项", "应付职工薪酬", "应交税费", "其他应付款"]:
            liability_total_current += end_val
            liability_begin_current += start_val
        else:
            liability_total_non_current += end_val
            liability_begin_non_current += start_val
        liability_items.append({
            "name": name,
            "ending": end_val,
            "beginning": start_val,
            "ending_str": _fmt_amount(end_val),
            "beginning_str": _fmt_amount(start_val),
        })
    liability_total = liability_total_current + liability_total_non_current
    liability_begin_total = liability_begin_current + liability_begin_non_current
    
    # 构建所有者权益项目
    equity_items = []
    equity_total = 0
    equity_begin_total = 0
    for name, codes in BS_EQUITY:
        end_val = sum((end_balances[c]["closing"] if c in end_balances else 0) for c in codes)
        start_val = sum((start_balances[c]["closing"] if c in start_balances else 0) for c in codes)
        equity_total += end_val
        equity_begin_total += start_val
        equity_items.append({
            "name": name,
            "ending": end_val,
            "beginning": start_val,
            "ending_str": _fmt_amount(end_val),
            "beginning_str": _fmt_amount(start_val),
        })
    
    liab_equity_total = liability_total + equity_total
    liab_equity_begin_total = liability_begin_total + equity_begin_total
    is_balanced = abs(asset_total - liab_equity_total) < 0.01
    
    return {
        "company": company,
        "report_date": str(report_date),
        "report_date_cn": f"{y}年{m}月{report_date.day}日",
        "template": "资产负债表",
        "orientation": "landscape",
        "unit": "元",
        "assets": {
            "items": asset_items,
            "current_total": asset_total_current,
            "non_current_total": asset_total_non_current,
            "total": asset_total,
            "current_total_str": _fmt_amount(asset_total_current),
            "non_current_total_str": _fmt_amount(asset_total_non_current),
            "total_str": _fmt_amount(asset_total),
            "current_begin": asset_begin_current,
            "non_current_begin": asset_begin_non_current,
            "total_begin": asset_begin_total,
        },
        "liabilities": {
            "items": liability_items,
            "current_total": liability_total_current,
            "non_current_total": liability_total_non_current,
            "total": liability_total,
            "current_total_str": _fmt_amount(liability_total_current),
            "non_current_total_str": _fmt_amount(liability_total_non_current),
            "total_str": _fmt_amount(liability_total),
            "current_begin": liability_begin_current,
            "non_current_begin": liability_begin_non_current,
            "total_begin": liability_begin_total,
        },
        "equity": {
            "items": equity_items,
            "total": equity_total,
            "total_str": _fmt_amount(equity_total),
            "total_begin": equity_begin_total,
        },
        "liab_equity_total": liab_equity_total,
        "liab_equity_total_str": _fmt_amount(liab_equity_total),
        "liab_equity_begin_total": liab_equity_begin_total,
        "is_balanced": is_balanced,
    }


@router.get("/income-statement", tags=["打印中心"])
async def api_print_income_statement(
    year_month: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """利润表打印数据"""
    data = _build_income_statement_data(db, year_month)
    return make_response(True, data)


def _build_income_statement_data(db: Session, year_month: Optional[str] = None):
    """利润表数据构建（供 JSON 打印与 Excel 导出共用）"""
    account_set_id = 1
    company = _get_company_name(db, account_set_id)
    today = datetime.date.today()
    if year_month:
        y, m = int(year_month[:4]), int(year_month[5:7])
    else:
        y, m = today.year, today.month
    # 本期：月初到月末
    month_start = datetime.date(y, m, 1)
    if m == 12:
        month_end = datetime.date(y, 12, 31)
    else:
        month_end = datetime.date(y, m + 1, 1) - datetime.timedelta(days=1)
    # 本年累计：1月1日到月末
    year_start = datetime.date(y, 1, 1)
    
    # 计算各科目本期和累计发生额
    current_balances = _calc_account_balances(db, account_set_id, month_end, month_start)
    year_balances = _calc_account_balances(db, account_set_id, month_end, year_start)
    
    items = []
    operating_revenue = 0
    operating_cost = 0
    operating_profit = 0
    total_profit = 0
    net_profit = 0
    
    for name, codes in IS_ITEMS:
        if name == "营业利润":
            current_val = operating_revenue - operating_cost
            year_val = current_val  # 简化
        elif name == "利润总额":
            current_val = operating_profit
            year_val = current_val
        elif name == "净利润":
            current_val = total_profit
            year_val = current_val
        else:
            current_val = sum((current_balances[c]["credit"] - current_balances[c]["debit"]) if c in current_balances else 0 for c in codes)
            year_val = sum((year_balances[c]["credit"] - year_balances[c]["debit"]) if c in year_balances else 0 for c in codes)
            if name == "营业收入":
                operating_revenue = current_val
            elif name == "营业成本":
                operating_cost = current_val
            elif name in ["营业税金及附加", "销售费用", "管理费用", "财务费用", "资产减值损失"]:
                operating_profit -= current_val
            elif name in ["公允价值变动收益", "投资收益"]:
                operating_profit += current_val
        if name == "营业利润":
            operating_profit = current_val
        elif name == "利润总额":
            total_profit = operating_profit + (items[-1]["current"] if items[-1]["name"] == "营业外收入" else 0) - (items[-1]["current"] if items and items[-1]["name"] == "营业外支出" else 0)
            current_val = total_profit
        elif name == "净利润":
            # 所得税费用
            tax_val = items[-1]["current"] if items and items[-1]["name"] == "所得税费用" else 0
            current_val = total_profit - tax_val
            net_profit = current_val
        
        items.append({
            "name": name,
            "current": current_val,
            "year_accumulated": year_val,
            "current_str": _fmt_amount(current_val),
            "year_str": _fmt_amount(year_val),
            "is_bold": name in ["营业利润", "利润总额", "净利润"],
            "is_negative": current_val < 0,
        })
    
    return {
        "company": company,
        "period": f"{y}年{m}月",
        "year": y,
        "month": m,
        "template": "利润表",
        "orientation": "landscape",
        "unit": "元",
        "items": items,
        "net_profit": net_profit,
    }


@router.get("/cash-flow", tags=["打印中心"])
async def api_print_cash_flow(
    year_month: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """现金流量表打印数据"""
    data = _build_cash_flow_data(db, year_month)
    return make_response(True, data)


def _build_cash_flow_data(db: Session, year_month: Optional[str] = None):
    """现金流量表数据构建（供 JSON 打印与 Excel 导出共用）"""
    account_set_id = 1
    company = _get_company_name(db, account_set_id)
    today = datetime.date.today()
    if year_month:
        y, m = int(year_month[:4]), int(year_month[5:7])
    else:
        y, m = today.year, today.month
    month_start = datetime.date(y, m, 1)
    if m == 12:
        month_end = datetime.date(y, 12, 31)
    else:
        month_end = datetime.date(y, m + 1, 1) - datetime.timedelta(days=1)
    
    balances = _calc_account_balances(db, account_set_id, month_end, month_start)
    
    def calc_flow(items_def):
        result = []
        subtotal = 0
        for name, codes in items_def:
            val = 0
            for code in codes:
                if code in balances:
                    # 现金流入=贷方，流出=借方
                    val += balances[code]["credit"] - balances[code]["debit"]
            result.append({"name": name, "amount": val, "amount_str": _fmt_amount(val)})
            subtotal += val
        return result, subtotal
    
    operating_items, operating_subtotal = calc_flow(CF_ITEMS_OPERATING)
    investing_items, investing_subtotal = calc_flow(CF_ITEMS_INVESTING)
    financing_items, financing_subtotal = calc_flow(CF_ITEMS_FINANCING)
    
    net_increase = operating_subtotal + investing_subtotal + financing_subtotal
    
    return {
        "company": company,
        "period": f"{y}年{m}月",
        "year": y,
        "month": m,
        "template": "现金流量表",
        "orientation": "landscape",
        "unit": "元",
        "operating": {"items": operating_items, "subtotal": operating_subtotal, "subtotal_str": _fmt_amount(operating_subtotal)},
        "investing": {"items": investing_items, "subtotal": investing_subtotal, "subtotal_str": _fmt_amount(investing_subtotal)},
        "financing": {"items": financing_items, "subtotal": financing_subtotal, "subtotal_str": _fmt_amount(financing_subtotal)},
        "net_increase": net_increase,
        "net_increase_str": _fmt_amount(net_increase),
    }


# ============================================================
# Excel 导出（标准财务报表格式，供报税/打印/归档）
# ============================================================

def _make_xlsx_response(wb, filename: str):
    """openpyxl Workbook → 标准 xlsx 下载响应（UTF-8 文件名）"""
    import io
    from fastapi.responses import StreamingResponse
    from urllib.parse import quote
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}.xlsx"},
    )


def _xl_base_styles():
    """报表通用样式"""
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    thin = Side(style="thin", color="000000")
    return {
        "border": Border(left=thin, right=thin, top=thin, bottom=thin),
        "title_font": Font(name="宋体", bold=True, size=16),
        "sub_font": Font(name="宋体", size=10),
        "head_font": Font(name="宋体", bold=True, size=10),
        "body_font": Font(name="宋体", size=10),
        "bold_font": Font(name="宋体", bold=True, size=10),
        "head_fill": PatternFill("solid", fgColor="DCE6F1"),
        "center": Alignment(horizontal="center", vertical="center", wrap_text=True),
        "left": Alignment(horizontal="left", vertical="center", wrap_text=True),
        "right": Alignment(horizontal="right", vertical="center"),
        "num_fmt": "#,##0.00",
    }


def _xl_write_title(ws, ncols, text, sub_text):
    """写报表标题 + 编制单位/日期行，返回下一行号"""
    from openpyxl.styles import Alignment
    st = _xl_base_styles()
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
    c = ws.cell(row=1, column=1, value=text)
    c.font = st["title_font"]
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 32
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ncols)
    c2 = ws.cell(row=2, column=1, value=sub_text)
    c2.font = st["sub_font"]
    c2.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 20
    return 3


def _xl_write_header(ws, row, headers):
    """写表头行，返回下一行号"""
    st = _xl_base_styles()
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=row, column=i, value=h)
        c.font = st["head_font"]
        c.fill = st["head_fill"]
        c.alignment = st["center"]
        c.border = st["border"]
    ws.row_dimensions[row].height = 22
    return row + 1


def _xl_write_row(ws, row, values, num_cols=(), bold=False, start_col=1):
    """写数据行：values 从 start_col 列开始写入；num_cols 指定金额列（实际列号，数字格式）"""
    st = _xl_base_styles()
    col = start_col
    for i, v in enumerate(values):
        c = ws.cell(row=row, column=col, value=v)
        c.font = st["bold_font"] if bold else st["body_font"]
        c.border = st["border"]
        c.alignment = st["center"] if i == 0 else st["right"]
        if col in num_cols and v is not None:
            c.number_format = st["num_fmt"]
        col += 1
    return row + 1


@router.get("/balance-sheet/excel", tags=["打印中心"])
def api_balance_sheet_excel(year_month: Optional[str] = None, db: Session = Depends(get_db)):
    """资产负债表 Excel 导出（标准账户式：左资产 / 右负债和所有者权益）"""
    from openpyxl import Workbook
    data = _build_balance_sheet_data(db, year_month)
    wb = Workbook()
    ws = wb.active
    ws.title = "资产负债表"
    ncols = 9
    # 列宽
    for col, w in zip("ABCDEFGHI", [26, 6, 14, 14, 2, 26, 6, 14, 14]):
        ws.column_dimensions[col].width = w

    sub = f"编制单位：{data['company']}    {data['report_date_cn']}    单位：{data['unit']}"
    r = _xl_write_title(ws, ncols, "资产负债表", sub)
    r = _xl_write_header(ws, r, ["资产", "行次", "期末余额", "年初余额", "", "负债和所有者权益", "行次", "期末余额", "年初余额"])

    assets = data["assets"]
    liab = data["liabilities"]
    equity = data["equity"]

    line = 1
    # 左列：资产项目（写第 1-4 列）
    for it in assets["items"]:
        _xl_write_row(ws, r, [it["name"], line, it["ending"], it["beginning"]], num_cols=(3, 4))
        r += 1
        line += 1
    _xl_write_row(ws, r, ["流动资产合计", line, assets["current_total"], assets["current_begin"]], num_cols=(3, 4), bold=True)
    r += 1
    line += 1
    _xl_write_row(ws, r, ["非流动资产合计", line, assets["non_current_total"], assets["non_current_begin"]], num_cols=(3, 4), bold=True)
    r += 1
    line += 1
    _xl_write_row(ws, r, ["资产总计", line, assets["total"], assets["total_begin"]], num_cols=(3, 4), bold=True)
    r += 1
    line += 1
    return_line = r

    # 右列：负债 + 所有者权益项目（写第 6-9 列，不触碰左列）
    r2 = 4
    line2 = 1
    for it in liab["items"]:
        _xl_write_row(ws, r2, [it["name"], line2, it["ending"], it["beginning"]], num_cols=(8, 9), start_col=6)
        r2 += 1
        line2 += 1
    _xl_write_row(ws, r2, ["流动负债合计", line2, liab["current_total"], liab["current_begin"]], num_cols=(8, 9), start_col=6, bold=True)
    r2 += 1
    line2 += 1
    _xl_write_row(ws, r2, ["非流动负债合计", line2, liab["non_current_total"], liab["non_current_begin"]], num_cols=(8, 9), start_col=6, bold=True)
    r2 += 1
    line2 += 1
    _xl_write_row(ws, r2, ["负债合计", line2, liab["total"], liab["total_begin"]], num_cols=(8, 9), start_col=6, bold=True)
    r2 += 1
    line2 += 1
    for it in equity["items"]:
        _xl_write_row(ws, r2, [it["name"], line2, it["ending"], it["beginning"]], num_cols=(8, 9), start_col=6)
        r2 += 1
        line2 += 1
    _xl_write_row(ws, r2, ["所有者权益合计", line2, equity["total"], equity["total_begin"]], num_cols=(8, 9), start_col=6, bold=True)
    r2 += 1
    line2 += 1
    _xl_write_row(ws, r2, ["负债和所有者权益总计", line2, data["liab_equity_total"], data["liab_equity_begin_total"]], num_cols=(8, 9), start_col=6, bold=True)
    r2 += 1

    # 平衡校验备注
    note = "注：资产总计 = 负债和所有者权益总计，报表平衡。" if data["is_balanced"] else "注：资产总计与负债和所有者权益总计不一致，请核对凭证。"
    last = max(return_line, r2)
    ws.merge_cells(start_row=last + 1, start_column=1, end_row=last + 1, end_column=ncols)
    nc = ws.cell(row=last + 1, column=1, value=note)
    nc.font = _xl_base_styles()["sub_font"]

    # 打印设置：横向 A4，适合宽表
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.print_area = f"A1:I{last + 1}"
    return _make_xlsx_response(wb, f"资产负债表_{data['report_date']}")


@router.get("/income-statement/excel", tags=["打印中心"])
def api_income_statement_excel(year_month: Optional[str] = None, db: Session = Depends(get_db)):
    """利润表 Excel 导出（标准多步式：本月数 + 本年累计数）"""
    from openpyxl import Workbook
    data = _build_income_statement_data(db, year_month)
    wb = Workbook()
    ws = wb.active
    ws.title = "利润表"
    ncols = 4
    for col, w in zip("ABCD", [34, 6, 16, 16]):
        ws.column_dimensions[col].width = w

    sub = f"编制单位：{data['company']}    {data['period']}    单位：{data['unit']}"
    r = _xl_write_title(ws, ncols, "利润表", sub)
    r = _xl_write_header(ws, r, ["项目", "行次", "本月数", "本年累计数"])

    line = 1
    for it in data["items"]:
        _xl_write_row(ws, r, [it["name"], line, it["current"], it["year_accumulated"]], num_cols=(3, 4), bold=it["is_bold"])
        r += 1
        line += 1

    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.print_area = f"A1:D{r - 1}"
    return _make_xlsx_response(wb, f"利润表_{data['year']}年{data['month']}月")


@router.get("/cash-flow/excel", tags=["打印中心"])
def api_cash_flow_excel(year_month: Optional[str] = None, db: Session = Depends(get_db)):
    """现金流量表 Excel 导出（标准直接法：经营/投资/筹资 + 净增加额）"""
    from openpyxl import Workbook
    data = _build_cash_flow_data(db, year_month)
    wb = Workbook()
    ws = wb.active
    ws.title = "现金流量表"
    ncols = 3
    for col, w in zip("ABC", [42, 6, 16]):
        ws.column_dimensions[col].width = w

    sub = f"编制单位：{data['company']}    {data['period']}    单位：{data['unit']}"
    r = _xl_write_title(ws, ncols, "现金流量表", sub)
    r = _xl_write_header(ws, r, ["项目", "行次", "本期金额"])

    line = 1
    sections = [
        ("一、经营活动产生的现金流量", data["operating"]),
        ("二、投资活动产生的现金流量", data["investing"]),
        ("三、筹资活动产生的现金流量", data["financing"]),
    ]
    for sec_name, sec_data in sections:
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=1)
        c = ws.cell(row=r, column=1, value=sec_name)
        c.font = _xl_base_styles()["bold_font"]
        c.border = _xl_base_styles()["border"]
        c.alignment = _xl_base_styles()["left"]
        ws.cell(row=r, column=2, value="").border = _xl_base_styles()["border"]
        cc = ws.cell(row=r, column=3, value="")
        cc.border = _xl_base_styles()["border"]
        r += 1
        for it in sec_data["items"]:
            _xl_write_row(ws, r, [it["name"], line, it["amount"]], num_cols=(3,))
            r += 1
            line += 1
        _xl_write_row(ws, r, [f"{sec_name.split('、')[1]}净额", line, sec_data["subtotal"]], num_cols=(3,), bold=True)
        r += 1
        line += 1
    _xl_write_row(ws, r, ["四、汇率变动对现金的影响", line, 0], num_cols=(3,))
    r += 1
    line += 1
    _xl_write_row(ws, r, ["五、现金及现金等价物净增加额", line, data["net_increase"]], num_cols=(3,), bold=True)
    r += 1

    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.print_area = f"A1:C{r - 1}"
    return _make_xlsx_response(wb, f"现金流量表_{data['year']}年{data['month']}月")
