"""
跨部门通知中心（大厅新闻播报）
====================================================
规则：任何跨部门业务通知（审核/下发/入库/质检等关键节点）统一调用
push_notification() 入库，大厅界面以新闻条形式动态滚动播报。

业务模块接入方式：
    from .notifications import push_notification
    push_notification(db, "采购订单 PO-xxx 已审核", "请仓库留意到货", category="采购", source="PO-xxx")
"""
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from datetime import datetime

from .. import models
from ..app import make_response
from ..database import get_db

router = APIRouter()


def push_notification(db: Session, title: str, content: str = "", category: str = "综合", source: str = ""):
    """跨部门通知统一入口。通知失败不影响主业务（异常吞掉只回滚通知）"""
    try:
        db.add(models.CrossDeptNotification(
            title=(title or "")[:200],
            content=content or "",
            category=category or "综合",
            source=(source or "")[:100],
            created_at=datetime.utcnow(),
        ))
        db.commit()
    except Exception:
        db.rollback()


@router.get("")
@router.get("/")
def list_notifications(limit: int = 30, db: Session = Depends(get_db)):
    items = db.query(models.CrossDeptNotification).order_by(
        models.CrossDeptNotification.id.desc()).limit(max(1, min(limit, 100))).all()
    return make_response(True, {"items": [{
        "id": n.id,
        "title": n.title,
        "content": n.content or "",
        "category": n.category or "综合",
        "source": n.source or "",
        "created_at": n.created_at.isoformat() if n.created_at else None,
    } for n in items]})


@router.post("")
@router.post("/")
def create_notification(data: dict = Body(default=None), db: Session = Depends(get_db)):
    data = data or {}
    title = (data.get("title") or "").strip()
    if not title:
        return make_response(False, None, "通知标题不能为空")
    push_notification(db, title, data.get("content", ""), data.get("category", "综合"), data.get("source", ""))
    return make_response(True, {"ok": True})
