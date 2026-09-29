"""
Auto Voucher API —— 自动凭证管理端点
====================================
提供：凭证列表/详情/审核/驳回/修改/生成/过账/异常
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
import datetime

from .. import models
from ..database import SessionLocal
from ..app import make_response, get_db
from .auto_voucher import (
    generate_voucher, VoucherException, list_auto_vouchers,
    approve_voucher, reject_voucher, post_voucher, BUILTIN_TEMPLATES,
    trigger_auto_voucher, seed_engineering_accounts, ENGINEERING_ACCOUNTS,
)

router = APIRouter()


# ---------- 凭证列表（含筛选） ----------
@router.get("", tags=["自动凭证"])
async def api_list_vouchers(
    status: Optional[str] = None,
    source_doc_type: Optional[str] = None,
    keyword: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    account_set_id = 1  # 默认账套
    sd = datetime.date.fromisoformat(start_date) if start_date else None
    ed = datetime.date.fromisoformat(end_date) if end_date else None
    vouchers = list_auto_vouchers(db, account_set_id, status, source_doc_type, keyword, sd, ed)
    result = []
    for v in vouchers:
        result.append({
            "id": v.id,
            "voucher_no": v.voucher_no,
            "voucher_date": str(v.voucher_date),
            "status": v.status,
            "source_doc_type": v.source_doc_type,
            "source_doc_id": v.source_doc_id,
            "source_doc_no": v.source_doc_no,
            "summary": v.summary,
            "total_debit": float(v.total_debit or 0),
            "total_credit": float(v.total_credit or 0),
            "error_message": v.error_message,
            "reject_reason": v.reject_reason,
            "created_at": str(v.created_at) if v.created_at else None,
            "entries_count": len(v.entries),
        })
    return make_response(True, {"total": len(result), "items": result}, f"共 {len(result)} 条凭证")


# ---------- 工程行业科目列表（静态路由，必须在 /{voucher_id} 之前）----------
@router.get("/engineering-accounts", tags=["自动凭证"])
async def api_list_engineering_accounts():
    return make_response(True, {"total": len(ENGINEERING_ACCOUNTS), "items": ENGINEERING_ACCOUNTS})


# ---------- 预置工程行业会计科目 ----------
@router.post("/seed-engineering-accounts", tags=["自动凭证"])
async def api_seed_engineering_accounts(account_set_id: int = 1, db: Session = Depends(get_db)):
    result = seed_engineering_accounts(db, account_set_id)
    return make_response(True, result, f"工程行业会计科目预置完成：新增{result['created']}，已存在{result['updated']}")


# ---------- 手动触发自动凭证（6大触发点统一入口）----------
@router.post("/trigger", tags=["自动凭证"])
async def api_trigger_auto_voucher(body: Dict[str, Any], db: Session = Depends(get_db)):
    """
    手动触发自动凭证生成
    body: { doc_type, doc_id, doc_no?, account_set_id?, force?, auto_approve? }
    支持的 doc_type:
      采购入库: INBOUND / ENG_INBOUND
      销售出库: SALES_OUTBOUND
      生产领料: PROD_PICK / PROJ_PICK
      生产入库: PROD_COMPLETE
      项目成本归集: PROJECT_COST
      收入确认: REVENUE_CONFIRM
      工程结算: ENG_SETTLE
      竣工结转: PROJ_COMPLETE
    """
    doc_type = body.get("doc_type", "")
    doc_id = body.get("doc_id")
    if not doc_type or doc_id is None:
        return make_response(False, None, "缺少 doc_type 或 doc_id")
    result = trigger_auto_voucher(
        db=db,
        doc_type=doc_type,
        doc_id=int(doc_id),
        doc_no=body.get("doc_no", ""),
        account_set_id=int(body.get("account_set_id", 1)),
        force=bool(body.get("force", False)),
        auto_approve=bool(body.get("auto_approve", True)),
    )
    if result.get("success"):
        return make_response(True, result, f"凭证 {result.get('voucher_no', '')} 生成成功")
    return make_response(False, result, result.get("error", "凭证生成失败"))


# ---------- 凭证详情 ----------
@router.get("/{voucher_id}", tags=["自动凭证"])
async def api_get_voucher(voucher_id: int, db: Session = Depends(get_db)):
    v = db.query(models.AutoVoucher).filter(models.AutoVoucher.id == voucher_id).first()
    if not v:
        return make_response(False, None, f"凭证 {voucher_id} 不存在")
    result = {
        "id": v.id,
        "voucher_no": v.voucher_no,
        "voucher_date": str(v.voucher_date),
        "status": v.status,
        "source_doc_type": v.source_doc_type,
        "source_doc_id": v.source_doc_id,
        "source_doc_no": v.source_doc_no,
        "summary": v.summary,
        "total_debit": float(v.total_debit or 0),
        "total_credit": float(v.total_credit or 0),
        "error_message": v.error_message,
        "reject_reason": v.reject_reason,
        "created_at": str(v.created_at) if v.created_at else None,
        "approved_at": str(v.approved_at) if v.approved_at else None,
        "entries": [{
            "id": e.id,
            "side": e.side,
            "account_code": e.account_code,
            "account_name": e.account_name,
            "amount": float(e.amount or 0),
            "summary": e.summary,
            "customer_id": e.customer_id,
            "supplier_id": e.supplier_id,
            "material_id": e.material_id,
        } for e in v.entries],
    }
    return make_response(True, result)


# ---------- 生成凭证 ----------
@router.post("/generate", tags=["自动凭证"])
async def api_generate_voucher(body: Dict[str, Any], db: Session = Depends(get_db)):
    account_set_id = body.get("account_set_id", 1)
    doc_type = body.get("doc_type", "")
    doc_id = body.get("doc_id")
    doc_no = body.get("doc_no", "")
    voucher_date = body.get("voucher_date")
    force = body.get("force", False)
    if not doc_type or not doc_id:
        return make_response(False, None, "缺少 doc_type 或 doc_id")
    try:
        v = generate_voucher(
            db, account_set_id, doc_type, int(doc_id), doc_no,
            datetime.date.fromisoformat(voucher_date) if voucher_date else None, force,
        )
        return make_response(True, {
            "id": v.id, "voucher_no": v.voucher_no, "status": v.status,
            "total_debit": float(v.total_debit or 0), "total_credit": float(v.total_credit or 0),
        }, f"凭证 {v.voucher_no} 生成成功")
    except VoucherException as e:
        # 标记异常
        return make_response(False, {
            "error_code": e.error_code,
            "doc_type": doc_type,
            "doc_id": doc_id,
        }, str(e))
    except Exception as e:
        return make_response(False, None, f"生成失败：{str(e)}")


# ---------- 审核通过 ----------
@router.post("/{voucher_id}/approve", tags=["自动凭证"])
async def api_approve_voucher(voucher_id: int, body: Dict[str, Any] = None, db: Session = Depends(get_db)):
    approver = (body or {}).get("approver", "system")
    try:
        v = approve_voucher(db, voucher_id, approver)
        return make_response(True, {"id": v.id, "status": v.status}, "审核通过")
    except VoucherException as e:
        return make_response(False, None, str(e))


# ---------- 驳回 ----------
@router.post("/{voucher_id}/reject", tags=["自动凭证"])
async def api_reject_voucher(voucher_id: int, body: Dict[str, Any], db: Session = Depends(get_db)):
    reason = body.get("reason", "")
    if not reason:
        return make_response(False, None, "驳回原因不能为空")
    try:
        v = reject_voucher(db, voucher_id, reason)
        return make_response(True, {"id": v.id, "status": v.status}, "已驳回")
    except VoucherException as e:
        return make_response(False, None, str(e))


# ---------- 过账 ----------
@router.post("/{voucher_id}/post", tags=["自动凭证"])
async def api_post_voucher(voucher_id: int, db: Session = Depends(get_db)):
    try:
        v = post_voucher(db, voucher_id)
        return make_response(True, {"id": v.id, "status": v.status}, "已过账")
    except VoucherException as e:
        return make_response(False, None, str(e))


# ---------- 修改凭证（草稿状态可改） ----------
@router.put("/{voucher_id}", tags=["自动凭证"])
async def api_update_voucher(voucher_id: int, body: Dict[str, Any], db: Session = Depends(get_db)):
    v = db.query(models.AutoVoucher).filter(models.AutoVoucher.id == voucher_id).first()
    if not v:
        return make_response(False, None, "凭证不存在")
    if v.status != "DRAFT":
        return make_response(False, None, f"只有草稿状态可修改（当前：{v.status}）")
    summary = body.get("summary")
    if summary:
        v.summary = summary
    # 修改分录
    entries_data = body.get("entries", [])
    if entries_data:
        # 删除旧分录
        for e in v.entries:
            db.delete(e)
        db.flush()
        total_d, total_c = 0, 0
        for ed in entries_data:
            side = ed.get("side", "debit")
            amount = float(ed.get("amount", 0))
            ne = models.AutoVoucherEntry(
                auto_voucher_id=v.id,
                account_code=ed.get("account_code", ""),
                account_name=ed.get("account_name", ""),
                side=side,
                amount=amount,
                summary=ed.get("summary", ""),
                customer_id=ed.get("customer_id"),
                supplier_id=ed.get("supplier_id"),
                material_id=ed.get("material_id"),
            )
            db.add(ne)
            if side == "debit":
                total_d += amount
            else:
                total_c += amount
        v.total_debit = total_d
        v.total_credit = total_c
        if abs(total_d - total_c) > 0.02:
            return make_response(False, None, f"借贷不平衡：借 {total_d:.2f}，贷 {total_c:.2f}")
    db.commit()
    return make_response(True, {"id": v.id, "status": v.status}, "修改成功")


# ---------- 批量生成 ----------
@router.post("/batch-generate", tags=["自动凭证"])
async def api_batch_generate(body: Dict[str, Any], db: Session = Depends(get_db)):
    items = body.get("items", [])
    results = []
    for item in items:
        try:
            v = generate_voucher(
                db,
                item.get("account_set_id", 1),
                item.get("doc_type", ""),
                int(item.get("doc_id", 0)),
                item.get("doc_no", ""),
                force=False,
            )
            results.append({"success": True, "id": v.id, "voucher_no": v.voucher_no})
        except VoucherException as e:
            results.append({"success": False, "error": str(e), "error_code": e.error_code})
        except Exception as e:
            results.append({"success": False, "error": str(e)})
    success_count = sum(1 for r in results if r.get("success"))
    return make_response(True, {"total": len(results), "success": success_count, "failed": len(results) - success_count, "results": results})


# ---------- 异常列表 ----------
@router.get("/exceptions/list", tags=["自动凭证"])
async def api_list_exceptions(db: Session = Depends(get_db)):
    account_set_id = 1
    vouchers = db.query(models.AutoVoucher).filter(
        models.AutoVoucher.account_set_id == account_set_id
    ).filter(
        models.AutoVoucher.error_message.isnot(None)
    ).order_by(models.AutoVoucher.created_at.desc()).all()
    result = [{
        "id": v.id,
        "voucher_no": v.voucher_no,
        "source_doc_type": v.source_doc_type,
        "source_doc_id": v.source_doc_id,
        "source_doc_no": v.source_doc_no,
        "error_message": v.error_message,
        "status": v.status,
        "created_at": str(v.created_at) if v.created_at else None,
    } for v in vouchers]
    return make_response(True, {"total": len(result), "items": result})


# ---------- 凭证模板列表 ----------
@router.get("/templates/list", tags=["自动凭证"])
async def api_list_templates():
    result = []
    for code, tpl in BUILTIN_TEMPLATES.items():
        result.append({
            "template_code": code,
            "template_name": tpl["name"],
            "doc_type": code,
            "description": tpl.get("summary_template", ""),
            "debit_count": len(tpl["debit_entries"]),
            "credit_count": len(tpl["credit_entries"]),
            "summary_template": tpl.get("summary_template", ""),
        })
    return make_response(True, {"total": len(result), "items": result})


# ---------- 统计概览 ----------
@router.get("/stats/overview", tags=["自动凭证"])
async def api_voucher_stats(db: Session = Depends(get_db)):
    account_set_id = 1
    today = datetime.date.today()
    month_start = today.replace(day=1)
    stats = {}
    # 按状态统计
    for status in ["DRAFT", "PENDING", "APPROVED", "POSTED", "REJECTED"]:
        cnt = db.query(models.AutoVoucher).filter(
            models.AutoVoucher.account_set_id == account_set_id,
            models.AutoVoucher.status == status
        ).count()
        stats[status.lower()] = cnt
    # 本月凭证数
    month_cnt = db.query(models.AutoVoucher).filter(
        models.AutoVoucher.account_set_id == account_set_id,
        models.AutoVoucher.created_at >= datetime.datetime.combine(month_start, datetime.time())
    ).count()
    # 按单据类型统计
    by_type = {}
    for v in db.query(models.AutoVoucher).filter(
        models.AutoVoucher.account_set_id == account_set_id
    ).all():
        t = v.source_doc_type
        if t not in by_type:
            by_type[t] = 0
        by_type[t] += 1
    return make_response(True, {
        "by_status": stats,
        "month_count": month_cnt,
        "by_doc_type": by_type,
    })
