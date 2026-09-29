"""
凭证设置 API —— 编号规则/摘要模板/科目映射/显示/打印/审核
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
import json

from .. import models
from ..app import make_response, get_db

router = APIRouter()

# 默认设置
DEFAULT_SETTINGS = {
    "numbering": {
        "prefix": "记",
        "separator": "-",
        "date_format": "YYYY-MM",
        "reset_rule": "monthly",  # monthly/yearly/continuous
        "serial_digits": 3,
        "recycle_deleted": False,
    },
    "summary_templates": [
        {"id": 1, "template": "采购入库 {供应商名称}", "variables": ["{供应商名称}"]},
        {"id": 2, "template": "销售出库 {客户名称}", "variables": ["{客户名称}"]},
        {"id": 3, "template": "生产领料 {工单号}", "variables": ["{工单号}"]},
        {"id": 4, "template": "完工入库 {工单号}", "variables": ["{工单号}"]},
        {"id": 5, "template": "收到货款 {客户名称}", "variables": ["{客户名称}"]},
        {"id": 6, "template": "支付货款 {供应商名称}", "variables": ["{供应商名称}"]},
        {"id": 7, "template": "提取现金", "variables": []},
        {"id": 8, "template": "存入现金", "variables": []},
    ],
    "account_mapping": [
        {"material_category": "原材料", "inventory_account": "1401", "income_account": "6001", "cost_account": "6401"},
        {"material_category": "半成品", "inventory_account": "1403", "income_account": "6001", "cost_account": "6401"},
        {"material_category": "产成品", "inventory_account": "1403", "income_account": "6001", "cost_account": "6401"},
        {"material_category": "低值易耗品", "inventory_account": "1411", "income_account": "6051", "cost_account": "6402"},
    ],
    "display": {
        "show_columns": ["voucher_date", "voucher_no", "summary", "account", "debit", "credit", "attachments", "preparer", "approver", "status"],
        "row_height": "standard",  # compact/standard/loose
        "default_entry_rows": 3,
        "auto_balance": True,
        "red_negative": True,
        "allow_multi_debit_credit": True,
        "check_aux_on_save": False,
    },
    "print": {
        "paper_size": "A4",
        "orientation_voucher": "portrait",
        "orientation_report": "landscape",
        "margin_top": 15,
        "margin_bottom": 15,
        "margin_left": 18,
        "margin_right": 18,
        "vouchers_per_page": 5,
        "header_font": "SimHei",
        "header_font_size": 14,
        "body_font": "SimSun",
        "body_font_size": 10,
        "info_font_size": 12,
        "bold_total": True,
        "show_signatures": ["preparer", "approver", "poster", "manager"],
        "signature_style": "underline",  # underline/box
        "company_position": "left",  # left/center/right
    },
    "audit": {
        "enable_audit": True,
        "audit_mode": "single",  # single/double
        "allow_self_audit": False,
        "allow_modify_posted": False,
        "modify_posted_creates_reversal": True,
    },
}

# 全局设置缓存（简化：存内存，实际应存数据库）
_settings_cache = None

def _get_settings(db):
    global _settings_cache
    if _settings_cache is None:
        # 尝试从数据库读取
        config = db.query(models.SystemConfig).filter(models.SystemConfig.account_set_id == 1).first()
        _settings_cache = json.loads(config.voucher_settings) if config and hasattr(config, 'voucher_settings') and config.voucher_settings else DEFAULT_SETTINGS.copy()
    return _settings_cache

def _save_settings(db, settings):
    global _settings_cache
    _settings_cache = settings
    # 尝试保存到数据库
    config = db.query(models.SystemConfig).filter(models.SystemConfig.account_set_id == 1).first()
    if config:
        config.voucher_settings = json.dumps(settings, ensure_ascii=False)
        db.commit()


# ---------- 获取全部设置 ----------
@router.get("", tags=["凭证设置"])
async def api_get_all_settings(db: Session = Depends(get_db)):
    s = _get_settings(db)
    return make_response(True, s)

# ---------- 编号规则 ----------
@router.get("/numbering", tags=["凭证设置"])
async def api_get_numbering(db: Session = Depends(get_db)):
    s = _get_settings(db)
    return make_response(True, s.get("numbering", {}))

@router.put("/numbering", tags=["凭证设置"])
async def api_update_numbering(body: Dict[str, Any], db: Session = Depends(get_db)):
    s = _get_settings(db)
    s["numbering"] = body
    _save_settings(db, s)
    # 生成预览
    prefix = body.get("prefix", "记")
    sep = body.get("separator", "-")
    df = body.get("date_format", "YYYY-MM")
    digits = body.get("serial_digits", 3)
    import datetime
    now = datetime.date.today()
    if df == "YYYYMMDD":
        date_part = now.strftime("%Y%m%d")
    elif df == "YYYY-MM-DD":
        date_part = now.strftime("%Y-%m-%d")
    else:  # YYMM
        date_part = now.strftime("%Y-%m")
    preview = f"{prefix}{sep}{date_part}{sep}{'0' * (digits - 1)}1"
    return make_response(True, {"preview": preview}, "编号规则已保存")

# ---------- 摘要模板 ----------
@router.get("/summary-templates", tags=["凭证设置"])
async def api_get_summary_templates(db: Session = Depends(get_db)):
    s = _get_settings(db)
    return make_response(True, {"items": s.get("summary_templates", [])})

@router.post("/summary-templates", tags=["凭证设置"])
async def api_add_summary_template(body: Dict[str, Any], db: Session = Depends(get_db)):
    s = _get_settings(db)
    templates = s.get("summary_templates", [])
    new_id = max([t["id"] for t in templates], default=0) + 1
    tpl = {"id": new_id, "template": body.get("template", ""), "variables": body.get("variables", [])}
    templates.append(tpl)
    s["summary_templates"] = templates
    _save_settings(db, s)
    return make_response(True, tpl, "摘要模板已添加")

@router.put("/summary-templates/{tpl_id}", tags=["凭证设置"])
async def api_update_summary_template(tpl_id: int, body: Dict[str, Any], db: Session = Depends(get_db)):
    s = _get_settings(db)
    templates = s.get("summary_templates", [])
    for t in templates:
        if t["id"] == tpl_id:
            t["template"] = body.get("template", t["template"])
            t["variables"] = body.get("variables", t.get("variables", []))
            _save_settings(db, s)
            return make_response(True, t, "摘要模板已更新")
    return make_response(False, None, f"模板 {tpl_id} 不存在")

@router.delete("/summary-templates/{tpl_id}", tags=["凭证设置"])
async def api_delete_summary_template(tpl_id: int, db: Session = Depends(get_db)):
    s = _get_settings(db)
    templates = s.get("summary_templates", [])
    s["summary_templates"] = [t for t in templates if t["id"] != tpl_id]
    _save_settings(db, s)
    return make_response(True, None, "摘要模板已删除")

# ---------- 科目映射 ----------
@router.get("/account-mapping", tags=["凭证设置"])
async def api_get_account_mapping(db: Session = Depends(get_db)):
    s = _get_settings(db)
    return make_response(True, {"items": s.get("account_mapping", [])})

@router.put("/account-mapping", tags=["凭证设置"])
async def api_update_account_mapping(body: Dict[str, Any], db: Session = Depends(get_db)):
    s = _get_settings(db)
    s["account_mapping"] = body.get("items", [])
    _save_settings(db, s)
    return make_response(True, None, "科目映射已更新")

# ---------- 显示设置 ----------
@router.get("/display", tags=["凭证设置"])
async def api_get_display(db: Session = Depends(get_db)):
    s = _get_settings(db)
    return make_response(True, s.get("display", {}))

@router.put("/display", tags=["凭证设置"])
async def api_update_display(body: Dict[str, Any], db: Session = Depends(get_db)):
    s = _get_settings(db)
    s["display"] = body
    _save_settings(db, s)
    return make_response(True, None, "显示设置已保存")

# ---------- 打印设置 ----------
@router.get("/print", tags=["凭证设置"])
async def api_get_print_settings(db: Session = Depends(get_db)):
    s = _get_settings(db)
    return make_response(True, s.get("print", {}))

@router.put("/print", tags=["凭证设置"])
async def api_update_print_settings(body: Dict[str, Any], db: Session = Depends(get_db)):
    s = _get_settings(db)
    s["print"] = body
    _save_settings(db, s)
    return make_response(True, None, "打印设置已保存")

# ---------- 审核设置 ----------
@router.get("/audit", tags=["凭证设置"])
async def api_get_audit(db: Session = Depends(get_db)):
    s = _get_settings(db)
    return make_response(True, s.get("audit", {}))

@router.put("/audit", tags=["凭证设置"])
async def api_update_audit(body: Dict[str, Any], db: Session = Depends(get_db)):
    s = _get_settings(db)
    s["audit"] = body
    _save_settings(db, s)
    return make_response(True, None, "审核设置已保存")
