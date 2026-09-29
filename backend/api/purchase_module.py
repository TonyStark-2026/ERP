"""
采购管理 V2 模块
===================
采购建议、供应商评估、询价比价、采购订单增强、跟踪预警、入库质检、报表分析
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
import io
import re
import datetime
from decimal import Decimal

from .. import models
from ..app import make_response
from ..database import get_db
from .notifications import push_notification

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


def _material_to_dict(m):
    if not m: return {}
    return {"id": m.id, "code": m.code, "name": m.name, "unit": m.unit or "", "spec": m.spec or ""}


def _supplier_to_dict(s):
    if not s: return {}
    return {
        "id": s.id, "code": s.code, "name": s.name, "contact": s.contact,
        "phone": s.phone, "email": s.email, "address": s.address,
        "tax_id": s.tax_id, "on_time_rate": float(s.on_time_rate or 0),
        "quality_rate": float(s.quality_rate or 0),
    }


# ============================================================
# 1. 采购建议
# ============================================================
@router.get("/suggestions", tags=["采购管理"])
def list_suggestions(
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.PurchaseSuggestion)
    if status:
        q = q.filter(models.PurchaseSuggestion.status == status)
    if keyword:
        q = q.filter(models.PurchaseSuggestion.suggestion_no.contains(keyword) |
                     models.PurchaseSuggestion.source_no.contains(keyword))
    items = q.order_by(models.PurchaseSuggestion.id.desc()).all()
    result = []
    for s in items:
        m = db.query(models.Material).filter(models.Material.id == s.material_id).first()
        result.append({
            "id": s.id, "suggestion_no": s.suggestion_no,
            "source_type": s.source_type, "source_type_label": {"MRP":"MRP运算","STOCK":"备库申请","MANUAL":"手工申请"}.get(s.source_type, s.source_type),
            "source_no": s.source_no,
            "material_id": s.material_id, "material_code": m.code if m else "",
            "material_name": m.name if m else "", "material_spec": s.material_spec,
            "requested_qty": float(s.requested_qty), "suggested_qty": float(s.suggested_qty),
            "unit": s.unit, "expected_date": _fmt_date(s.expected_date),
            "status": s.status,
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/suggestions/{sid}/convert", tags=["采购管理"])
def convert_suggestion(sid: int, supplier_id: int = Query(...), db: Session = Depends(get_db)):
    s = db.query(models.PurchaseSuggestion).filter(models.PurchaseSuggestion.id == sid).first()
    if not s:
        return make_response(False, None, "采购建议不存在", "40002")
    if s.status == "CONVERTED":
        return make_response(False, None, "已转单", "40003")
    po_no = f"PO-{datetime.date.today().strftime('%Y%m%d')}-{s.id:05d}"
    
    # Handle date conversion
    exp_date = s.expected_date
    if isinstance(exp_date, str):
        try:
            exp_date = datetime.date.fromisoformat(exp_date)
        except:
            exp_date = None
    
    po = models.PurchaseOrder(
        account_set_id=ACCOUNT_SET_ID,
        po_no=po_no,
        supplier_id=supplier_id,
        status="DRAFT",
        approval_status="PENDING",
        tax_rate=Decimal("13"),
        discount_amount=0,
        # V2 扩展字段
        order_date=datetime.date.today(),
        expected_date=exp_date,
        payment_terms="",
        transport_type="",
        total_amount=0,
    )
    db.add(po)
    db.flush()
    unit_price = 0
    m = db.query(models.Material).filter(models.Material.id == s.material_id).first()
    if m and m.unit_price:
        unit_price = float(m.unit_price)
    qty_dec = Decimal(str(s.suggested_qty))
    price_dec = Decimal(str(unit_price))
    amount = qty_dec * price_dec
    item = models.PurchaseOrderItem(
        purchase_order_id=po.id,
        material_id=s.material_id,
        quantity=int(s.suggested_qty),
        unit_price=Decimal(str(unit_price)),
        # V2 扩展字段
        line_no=1,
        unit=s.unit or "",
        amount=amount,
        source_no=s.source_no or s.suggestion_no,
        delivery_date=exp_date,
        received_qty=0,
    )
    db.add(item)
    po.total_amount = amount
    s.status = "CONVERTED"
    s.converted_order_id = po.id
    db.commit()
    return make_response(True, {"po_no": po_no, "po_id": po.id, "suggestion_no": s.suggestion_no}, "转单成功")


@router.post("/suggestions/batch-convert", tags=["采购管理"])
def batch_convert_suggestions(data: dict, db: Session = Depends(get_db)):
    ids = data.get("ids", [])
    supplier_id = data.get("supplier_id")
    if not ids or not supplier_id:
        return make_response(False, None, "参数不完整", "40003")
    results = []
    for sid in ids:
        try:
            s = db.query(models.PurchaseSuggestion).filter(models.PurchaseSuggestion.id == sid).first()
            if s and s.status == "PENDING":
                po_no = f"PO-{datetime.date.today().strftime('%Y%m%d')}-{s.id:05d}"
                
                # Handle date
                exp_date = s.expected_date
                if isinstance(exp_date, str):
                    try: exp_date = datetime.date.fromisoformat(exp_date)
                    except: exp_date = None
                
                po = models.PurchaseOrder(
                    account_set_id=ACCOUNT_SET_ID, po_no=po_no, supplier_id=supplier_id,
                    status="DRAFT", approval_status="PENDING", tax_rate=Decimal("13"), discount_amount=0,
                    order_date=datetime.date.today(), expected_date=exp_date,
                    payment_terms="", transport_type="", total_amount=0,
                )
                db.add(po)
                db.flush()
                m = db.query(models.Material).filter(models.Material.id == s.material_id).first()
                up = float(m.unit_price) if m and m.unit_price else 0
                qty_dec = Decimal(str(s.suggested_qty))
                price_dec = Decimal(str(up))
                amount = qty_dec * price_dec
                item = models.PurchaseOrderItem(
                    purchase_order_id=po.id, material_id=s.material_id,
                    quantity=int(s.suggested_qty), unit_price=Decimal(str(up)),
                    line_no=1, unit=s.unit or "", amount=amount,
                    source_no=s.source_no or s.suggestion_no,
                    delivery_date=exp_date, received_qty=0,
                )
                db.add(item)
                po.total_amount = amount
                s.status = "CONVERTED"
                s.converted_order_id = po.id
                results.append({"suggestion_no": s.suggestion_no, "po_no": po_no})
        except Exception as e:
            print(f"Error converting suggestion {sid}: {e}")
    db.commit()
    return make_response(True, {"converted": len(results), "items": results})


@router.post("/suggestions/generate-mrp", tags=["采购管理"])
def generate_mrp_suggestions(db: Session = Depends(get_db)):
    """MRP：根据现有生产工单和BOM生成采购建议"""
    today = datetime.date.today()
    date_str = today.strftime('%Y%m%d')
    created = []
    # 使用时间戳后缀保证唯一性
    ts = datetime.datetime.now().strftime('%H%M%S')
    sug_index = 1

    # 1. 尝试从生产工单 + BOM 生成
    work_orders = db.query(models.ProductionWorkOrder).filter(
        models.ProductionWorkOrder.status.in_(["PLANNED", "RELEASED", "IN_PROGRESS"])
    ).all()

    for wo in work_orders:
        bom = db.query(models.BOM).filter(models.BOM.id == wo.bom_id).first() if wo.bom_id else None
        if not bom:
            # 若无 BOM，尝试查该产品的活动 BOM
            bom = db.query(models.BOM).filter(
                models.BOM.product_id == wo.product_id,
                models.BOM.status == "ACTIVE"
            ).first()
        if not bom:
            continue
        bom_items = db.query(models.BOMItem).filter(models.BOMItem.bom_id == bom.id).all()
        for bi in bom_items:
            mat = db.query(models.Material).filter(models.Material.id == bi.material_id).first()
            if not mat:
                continue
            qty = float(wo.planned_qty or 0) * float(bi.quantity or 0)
            # 扣减库存
            inv_recs = db.query(models.InventoryRecord).filter(
                models.InventoryRecord.material_id == mat.id
            ).all()
            stock = sum(float(r.quantity or 0) for r in inv_recs)
            needed = max(qty - stock, 0)
            if needed <= 0:
                continue
            sn = f"SUG-{date_str}-{ts}-{sug_index:04d}"
            sug = models.PurchaseSuggestion(
                account_set_id=ACCOUNT_SET_ID, suggestion_no=sn,
                source_type="MRP", source_no=wo.work_order_no,
                material_id=mat.id, material_spec=mat.spec or "",
                requested_qty=qty, suggested_qty=needed,
                unit=mat.unit or "",
                expected_date=today + datetime.timedelta(days=7),
                status="PENDING",
            )
            db.add(sug)
            created.append({"suggestion_no": sn, "material": mat.name, "qty": needed})
            sug_index += 1

    # 2. 若无工单/BOM数据，从物料库生成示例建议
    if not created:
        mats = db.query(models.Material).limit(3).all()
        for i, m in enumerate(mats):
            sn = f"SUG-{date_str}-{ts}-{sug_index:04d}"
            sug = models.PurchaseSuggestion(
                account_set_id=ACCOUNT_SET_ID, suggestion_no=sn,
                source_type="STOCK", source_no="STOCK-DEMO",
                material_id=m.id, material_spec=m.spec or "",
                requested_qty=100, suggested_qty=100,
                unit=m.unit or "",
                expected_date=today + datetime.timedelta(days=7),
                status="PENDING",
            )
            db.add(sug)
            created.append({"suggestion_no": sn, "material": m.name, "qty": 100})
            sug_index += 1

    db.commit()
    return make_response(True, {"created": len(created), "items": created}, "MRP运算完成")


# ============================================================
# 2. 供应商评估
# ============================================================
@router.get("/suppliers/{sid}/evaluation", tags=["采购管理"])
def get_supplier_evaluation(sid: int, db: Session = Depends(get_db)):
    s = db.query(models.Supplier).filter(models.Supplier.id == sid).first()
    if not s:
        return make_response(False, None, "供应商不存在")
    evaluations = db.query(models.SupplierEvaluation)\
        .filter(models.SupplierEvaluation.supplier_id == sid)\
        .order_by(models.SupplierEvaluation.created_at.desc()).limit(12).all()
    # 订单统计
    pos = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.supplier_id == sid,
                                               models.PurchaseOrder.status == "POSTED").all()
    total_amount = sum(sum(float(i.unit_price or 0) * int(i.quantity or 0) for i in po.items) for po in pos)
    return make_response(True, {
        "supplier": _supplier_to_dict(s),
        "order_count": len(pos),
        "total_amount": round(total_amount, 2),
        "evaluations": [{
            "period": e.period_month, "price_score": float(e.price_score),
            "on_time_score": float(e.on_time_score), "quality_score": float(e.quality_score),
            "cooperation_score": float(e.cooperation_score),
            "composite_score": float(e.composite_score), "rank_level": e.rank_level
        } for e in evaluations],
    })


@router.post("/suppliers/{sid}/evaluation", tags=["采购管理"])
def save_supplier_evaluation(sid: int, data: dict, db: Session = Depends(get_db)):
    period = data.get("period_month", datetime.date.today().strftime("%Y-%m"))
    price_s = float(data.get("price_score", 3))
    on_time_s = float(data.get("on_time_score", 3))
    quality_s = float(data.get("quality_score", 3))
    coop_s = float(data.get("cooperation_score", 3))
    composite = round((price_s + on_time_s + quality_s + coop_s) / 4, 2)
    if composite >= 4.5: level = "A"
    elif composite >= 3.5: level = "B"
    elif composite >= 2.5: level = "C"
    else: level = "D"
    ev = models.SupplierEvaluation(
        account_set_id=ACCOUNT_SET_ID, supplier_id=sid, period_month=period,
        price_score=price_s, on_time_score=on_time_s, quality_score=quality_s,
        cooperation_score=coop_s, composite_score=composite, rank_level=level,
    )
    db.add(ev)
    db.commit()
    return make_response(True, {"composite_score": composite, "rank_level": level})


# ============================================================
# 3. 询价比价
# ============================================================
@router.get("/quotations", tags=["采购管理"])
def list_quotations(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.PurchaseQuotation)
    if status: q = q.filter(models.PurchaseQuotation.status == status)
    items = q.order_by(models.PurchaseQuotation.id.desc()).all()
    result = []
    for qt in items:
        m = db.query(models.Material).filter(models.Material.id == qt.material_id).first()
        replies = db.query(models.PurchaseQuotationReply).filter(models.PurchaseQuotationReply.quotation_id == qt.id).all()
        result.append({
            "id": qt.id, "quotation_no": qt.quotation_no, "status": qt.status,
            "material_code": m.code if m else "", "material_name": m.name if m else "",
            "material_spec": qt.material_spec, "quantity": float(qt.quantity),
            "reply_count": len(replies),
            "expected_date": _fmt_date(qt.expected_date),
            "created_at": _fmt_date(qt.created_at),
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/quotations", tags=["采购管理"])
def create_quotation(data: dict, db: Session = Depends(get_db)):
    material_id = data.get("material_id")
    m = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not m:
        return make_response(False, None, "物料不存在", "40003")
    qn = f"QT-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    qt = models.PurchaseQuotation(
        account_set_id=ACCOUNT_SET_ID, quotation_no=qn, material_id=material_id,
        material_spec=data.get("material_spec") or m.spec,
        quantity=Decimal(str(data.get("quantity", 1))),
        expected_date=data.get("expected_date"),
        status="DRAFT",
    )
    db.add(qt)
    db.commit()
    return make_response(True, {"id": qt.id, "quotation_no": qn})


@router.post("/quotations/{qid}/reply", tags=["采购管理"])
def add_quotation_reply(qid: int, data: dict, db: Session = Depends(get_db)):
    qt = db.query(models.PurchaseQuotation).filter(models.PurchaseQuotation.id == qid).first()
    if not qt:
        return make_response(False, None, "询价单不存在")
    reply = models.PurchaseQuotationReply(
        quotation_id=qid, supplier_id=data["supplier_id"],
        unit_price=Decimal(str(data["unit_price"])),
        lead_time_days=data.get("lead_time_days"),
    )
    db.add(reply)
    qt.status = "REPLIED"
    db.commit()
    return make_response(True, {"reply_id": reply.id})


@router.post("/quotations/{qid}/award", tags=["采购管理"])
def award_quotation(qid: int, reply_id: int, db: Session = Depends(get_db)):
    qt = db.query(models.PurchaseQuotation).filter(models.PurchaseQuotation.id == qid).first()
    if not qt:
        return make_response(False, None, "询价单不存在")
    reply = db.query(models.PurchaseQuotationReply).filter(models.PurchaseQuotationReply.id == reply_id).first()
    if not reply:
        return make_response(False, None, "回复不存在")
    # 标记中标
    for r in db.query(models.PurchaseQuotationReply).filter(models.PurchaseQuotationReply.quotation_id == qid).all():
        r.is_selected = (r.id == reply_id)
    qt.status = "AWARDED"
    qt.winner_supplier_id = reply.supplier_id
    # 更新物料最近采购价
    m = db.query(models.Material).filter(models.Material.id == qt.material_id).first()
    if m:
        m.last_purchase_price = float(reply.unit_price)
    db.commit()
    return make_response(True, {"winner_supplier_id": reply.supplier_id, "unit_price": float(reply.unit_price)})


# ============================================================
# 4. 采购订单跟踪与预警
# ============================================================
@router.get("/order-tracking", tags=["采购管理"])
def list_order_tracking(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.PurchaseOrder)
    if status: q = q.filter(models.PurchaseOrder.status == status)
    orders = q.order_by(models.PurchaseOrder.id.desc()).limit(200).all()
    today = datetime.date.today()
    result = []
    for o in orders:
        s = db.query(models.Supplier).filter(models.Supplier.id == o.supplier_id).first()
        items = db.query(models.PurchaseOrderItem).filter(models.PurchaseOrderItem.purchase_order_id == o.id).all()
        total_qty = sum(int(i.quantity or 0) for i in items)
        # 合格入库（质检通过POSTED）才计入到料/损耗
        posted_inbounds = db.query(models.PurchaseInbound).filter(
            models.PurchaseInbound.purchase_order_id == o.id,
            models.PurchaseInbound.status == "POSTED").all()
        received_qty = sum(float(i.received_qty or 0) for i in posted_inbounds)
        ordered_in = sum(float(i.ordered_qty or 0) for i in posted_inbounds)
        loss_qty = round(sum(max(float(i.ordered_qty or 0) - float(i.received_qty or 0), 0) for i in posted_inbounds), 4)
        loss_amount = round(sum(
            max(float(i.ordered_qty or 0) - float(i.received_qty or 0), 0) * float(i.unit_price or 0)
            for i in posted_inbounds), 2)
        # 到料率=累计合格到货/订单总订购；损耗率=损耗数量/已到货批次订购
        arrival_rate = round(received_qty / total_qty * 100, 1) if total_qty > 0 else 0.0
        loss_rate = round(loss_qty / ordered_in * 100, 1) if ordered_in > 0 else 0.0
        # 预警状态
        warn_level = "normal"
        expected = None
        for item in items:
            # 找对应的入库通知
            continue
        result.append({
            "id": o.id, "po_no": o.po_no, "status": o.status,
            "supplier_id": o.supplier_id, "supplier_name": s.name if s else "",
            "material_names": ", ".join(
                (db.query(models.Material).filter(models.Material.id == i.material_id).first().name if db.query(models.Material).filter(models.Material.id == i.material_id).first() else "")
                for i in items
            ),
            "total_qty": total_qty, "received_qty": received_qty,
            "pending_qty": max(total_qty - received_qty, 0),
            "arrival_rate": arrival_rate, "loss_rate": loss_rate,
            "loss_qty": loss_qty, "loss_amount": loss_amount,
            "expected_date": _fmt_date(expected),
            "warn_level": warn_level,
            "created_at": _fmt_date(o.created_at),
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/orders/{oid}/communication", tags=["采购管理"])
def add_communication(oid: int, data: dict, db: Session = Depends(get_db)):
    c = models.PurchaseCommunication(
        account_set_id=ACCOUNT_SET_ID, purchase_order_id=oid,
        contact_type=data.get("contact_type", "PHONE"),
        content=data.get("content", ""),
        communicator=data.get("communicator"),
    )
    db.add(c)
    db.commit()
    return make_response(True, {"id": c.id})


@router.get("/orders/{oid}/communications", tags=["采购管理"])
def list_communications(oid: int, db: Session = Depends(get_db)):
    items = db.query(models.PurchaseCommunication)\
        .filter(models.PurchaseCommunication.purchase_order_id == oid)\
        .order_by(models.PurchaseCommunication.communication_date.desc()).all()
    return make_response(True, {"items": [{
        "id": c.id, "contact_type": c.contact_type,
        "content": c.content, "communicator": c.communicator,
        "communication_date": _fmt_date(c.communication_date),
    } for c in items]})


# ============================================================
# 5. 入库单与质检
# ============================================================
@router.get("/inbounds", tags=["采购管理"])
def list_inbounds(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.PurchaseInbound)
    if status: q = q.filter(models.PurchaseInbound.status == status)
    items = q.order_by(models.PurchaseInbound.id.desc()).limit(200).all()
    result = []
    for i in items:
        po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == i.purchase_order_id).first()
        m = db.query(models.Material).filter(models.Material.id == i.material_id).first()
        s = db.query(models.Supplier).filter(models.Supplier.id == i.supplier_id).first()
        result.append({
            "id": i.id, "inbound_no": i.inbound_no, "po_no": po.po_no if po else "",
            "material_name": m.name if m else "", "material_code": m.code if m else "",
            "supplier_name": s.name if s else "",
            "ordered_qty": float(i.ordered_qty), "received_qty": float(i.received_qty),
            "unit_price": float(i.unit_price), "amount": float(i.amount),
            "quality_status": i.quality_status, "difference_type": i.difference_type,
            "status": i.status, "inbound_date": _fmt_date(i.inbound_date),
        })
    return make_response(True, {"items": result, "total": len(result)})


@router.post("/inbounds", tags=["采购管理"])
def create_inbound(data: dict, db: Session = Depends(get_db)):
    po_id = data.get("purchase_order_id")
    po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == po_id).first()
    if not po:
        return make_response(False, None, "采购订单不存在")
    material_id = data.get("material_id")
    m = db.query(models.Material).filter(models.Material.id == material_id).first()
    if not m:
        return make_response(False, None, "物料不存在")
    import uuid
    ino = f"IN-{datetime.date.today().strftime('%Y%m%d')}-{po_id:05d}-{uuid.uuid4().hex[:4].upper()}"
    received = float(data.get("received_qty", 0))
    unit_price = float(data.get("unit_price", 0))
    inbound = models.PurchaseInbound(
        account_set_id=ACCOUNT_SET_ID, inbound_no=ino,
        purchase_order_id=po_id, supplier_id=po.supplier_id,
        material_id=material_id,
        ordered_qty=Decimal(str(data.get("ordered_qty", received))),
        received_qty=Decimal(str(received)),
        unit_price=Decimal(str(unit_price)),
        amount=Decimal(str(received * unit_price)),
        tax_rate=Decimal(str(data.get("tax_rate", 13))),
        difference_type=data.get("difference_type"),
        quality_status=data.get("quality_status", "PENDING"),
        inbound_date=data.get("inbound_date", datetime.date.today()),
        operator=data.get("operator", "system"),
        status=data.get("status", "DRAFT"),
        has_invoice=data.get("has_invoice", False),
    )
    db.add(inbound)
    db.commit()
    return make_response(True, {"id": inbound.id, "inbound_no": ino})


@router.post("/inbounds/{iid}/inspect", tags=["采购管理"])
def inspect_inbound(iid: int, data: dict, db: Session = Depends(get_db)):
    ib = db.query(models.PurchaseInbound).filter(models.PurchaseInbound.id == iid).first()
    if not ib:
        return make_response(False, None, "入库单不存在")
    if ib.status == "REJECTED":
        return make_response(False, None, "已驳回的入库单不可质检，请重新导入")
    if ib.status == "DRAFT":
        return make_response(False, None, "该入库单尚未审核，请先审核通过")
    ib.quality_status = data.get("quality_status", "PASSED")
    ib.status = data.get("status", "POSTED")
    db.commit()
    # 质检合格正式入库：每笔入库自动生成记账凭证（借原材料/管理费用-损耗，贷在途物资）
    if ib.quality_status == "PASSED" and ib.status == "POSTED":
        try:
            _auto_inbound_voucher(db, ib)
        except Exception:
            import traceback
            traceback.print_exc()
    # 跨部门通知：质检结果上大厅新闻播报
    _passed = (ib.quality_status == "PASSED")
    push_notification(db,
        f"入库单 {ib.inbound_no} 质检{'合格' if _passed else '不合格'}，{'已入库' if ib.status == 'POSTED' else '待处理'}",
        "已入库物料进入库存，请财务关注应付/成本核算" if _passed else "请采购联系供应商处理不合格品",
        category="质检", source=ib.inbound_no or "")
    return make_response(True, {"id": ib.id, "quality_status": ib.quality_status})


@router.post("/inbounds/{iid}/audit", tags=["采购管理"])
def audit_inbound(iid: int, data: dict, db: Session = Depends(get_db)):
    """入库单审核：approve→APPROVED进入质检环节；reject→REJECTED驳回"""
    ib = db.query(models.PurchaseInbound).filter(models.PurchaseInbound.id == iid).first()
    if not ib:
        return make_response(False, None, "入库单不存在")
    if ib.status not in ("DRAFT", "REJECTED"):
        return make_response(False, None, "仅待审核/已驳回状态可审核")
    action = (data.get("action") or "approve").lower()
    remark = (data.get("remark") or "").strip()
    if action == "approve":
        ib.status = "APPROVED"
        note = f"审核通过 {datetime.date.today().strftime('%Y-%m-%d')} {remark}".strip()
    else:
        ib.status = "REJECTED"
        note = f"驳回：{remark or '信息有误，请修改后重新导入'}"
    ib.notes = note
    db.commit()
    return make_response(True, {"id": ib.id, "status": ib.status}, "审核通过，已进入质检环节" if action == "approve" else "已驳回")


@router.delete("/inbounds/{iid}", tags=["采购管理"])
def delete_inbound(iid: int, db: Session = Depends(get_db)):
    """删除入库单（已入库POSTED的不可删，保证账实一致）"""
    ib = db.query(models.PurchaseInbound).filter(models.PurchaseInbound.id == iid).first()
    if not ib:
        return make_response(False, None, "入库单不存在")
    if ib.status == "POSTED":
        return make_response(False, None, "已入库的单据不可删除")
    db.delete(ib)
    db.commit()
    return make_response(True, {"id": iid}, "入库单已删除")


@router.get("/inbounds/template", tags=["采购管理"])
def inbound_template(db: Session = Depends(get_db)):
    """入库单Excel模板（示例行用真实物料，可直接试导入）"""
    from fastapi.responses import StreamingResponse
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "入库单"
    sample_mats = db.query(models.Material).limit(2).all()
    today = datetime.date.today().strftime("%Y-%m-%d")
    headers = ["采购订单号(选填)", "物料编码*", "物料名称", "订单数量", "实收数量*", "单价", "税率%", "入库日期", "经办人", "备注"]
    ws.append(headers)
    for i, m in enumerate(sample_mats):
        ws.append(["", m.code, m.name, 10, 10, 50.0, 13, today, "仓管员", f"示例行{i + 1}，可删除"])
    if not sample_mats:
        ws.append(["", "示例编码", "示例物料", 10, 10, 50.0, 13, today, "仓管员", "请替换为系统已有物料"])
    ws.append([])
    ws.append(["填写说明："])
    ws.append(["1. 必填列：物料编码、实收数量；其他列可留空，单号自动生成"])
    ws.append(["2. 物料编码必须已存在于系统物料档案，否则该行导入失败"])
    ws.append(["3. 采购订单号填系统内PO单号可自动关联订单和供应商"])
    ws.append(["4. 日期格式支持 2026-09-06 / 2026/9/6 / 2026年9月6日"])
    ws.append(["5. 导入后入库单为「待审核」状态，审核通过后进入质检环节"])
    for col_idx, w in enumerate([18, 16, 20, 10, 10, 10, 8, 12, 10, 24], 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = w
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    from urllib.parse import quote
    fname = quote("入库单导入模板")
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{fname}.xlsx"})


def _ib_norm_header(s) -> str:
    import re as _re
    s = str(s or "")
    s = _re.sub(r"[（(【\[].*?[)）\]】]", "", s)
    return s.replace(" ", "").replace("\u3000", "").lower()


def _ib_date(v):
    if v is None or v == "":
        return datetime.date.today()
    if isinstance(v, datetime.datetime):
        return v.date()
    if isinstance(v, datetime.date):
        return v
    if isinstance(v, (int, float)) and 20000 < v < 80000:
        try:
            return datetime.date(1899, 12, 30) + datetime.timedelta(days=int(v))
        except Exception:
            pass
    s = str(v).strip()
    m = re.match(r"^(\d{4})[-/.年](\d{1,2})[-/.月](\d{1,2})日?$", s)
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except Exception:
            pass
    try:
        return datetime.date.fromisoformat(s[:10])
    except Exception:
        return datetime.date.today()


def _ib_gen_no(db: Session) -> str:
    import uuid
    while True:
        no = f"IB-{datetime.date.today().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        if not db.query(models.PurchaseInbound).filter(models.PurchaseInbound.inbound_no == no).first():
            return no


@router.post("/inbounds/import", tags=["采购管理"])
async def import_inbounds(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """导入入库单Excel：逐行校验→生成待审核(DRAFT)入库单，审核通过后进入质检环节"""
    import openpyxl
    content = await file.read()
    try:
        wb = openpyxl.load_workbook(io.BytesIO(content))
    except Exception:
        return make_response(False, None, "无法解析Excel文件，请使用系统提供的模板")
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return make_response(False, None, "Excel内容为空")
    # 表头行定位与模糊匹配
    header_idx, colmap = None, {}
    alias = {
        "po_no": ["采购订单号", "订单号", "po号", "采购单号"],
        "code": ["物料编码", "物料代码", "存货编码", "编码", "料号"],
        "name": ["物料名称", "名称", "品名"],
        "ordered": ["订单数量", "应收数量", "订购数量"],
        "received": ["实收数量", "入库数量", "实际数量", "数量"],
        "price": ["单价", "含税单价"],
        "tax": ["税率", "税率%"],
        "date": ["入库日期", "日期"],
        "operator": ["经办人", "操作员", "仓管员"],
        "remark": ["备注", "说明"],
    }
    for idx, row in enumerate(rows[:10]):
        vals = [_ib_norm_header(v) for v in row]
        if not any(vals):
            continue
        used_cols = set()
        hits = {}
        # 两轮匹配：先精确、后子串，且一列只归一个字段，防止「数量」兜底抢占「订单数量」列
        for exact_pass in (True, False):
            for field, keys in alias.items():
                if field in hits:
                    continue
                for ci, v in enumerate(vals):
                    if not v or ci in used_cols:
                        continue
                    if (v in keys) if exact_pass else any(k in v for k in keys):
                        hits[field] = ci
                        used_cols.add(ci)
                        break
        if "code" in hits and "received" in hits:
            header_idx, colmap = idx, hits
            break
    if header_idx is None:
        return make_response(False, None, "未找到表头（需含「物料编码」和「实收数量」列），请使用系统模板")
    # 预加载物料索引
    mats = db.query(models.Material).all()
    mat_by_code = {}
    for m in mats:
        if m.code:
            mat_by_code[m.code.strip().upper()] = m
            mat_by_code[re.sub(r"[\s\-()（）]", "", m.code).upper()] = m
    po_by_no = {o.po_no.strip().upper(): o for o in db.query(models.PurchaseOrder).all() if o.po_no}
    ok_rows, fail_rows, po_ids = 0, [], set()
    for ri, row in enumerate(rows[header_idx + 1:], header_idx + 2):
        def gv(field):
            ci = colmap.get(field)
            return row[ci] if ci is not None and ci < len(row) else None
        code = str(gv("code") or "").strip()
        name = str(gv("name") or "").strip()
        if not code and not name:
            continue  # 空行/说明行跳过
        mkey = re.sub(r"[\s\-()（）]", "", code).upper()
        mat = mat_by_code.get(mkey) or (mat_by_code.get(code.strip().upper())) \
            or next((m for m in mats if name and m.name == name), None) \
            or (next((m for m in mats if name and name in m.name), None) if len(name) >= 4 else None)
        if not mat:
            fail_rows.append(f"第{ri}行：物料「{code or name}」不存在，请先在物料档案建档")
            continue
        try:
            received = float(gv("received") or 0)
            if received <= 0:
                raise ValueError
        except Exception:
            fail_rows.append(f"第{ri}行：实收数量无效")
            continue
        po = po_by_no.get(str(gv("po_no") or "").strip().upper())
        if gv("po_no") and not po:
            fail_rows.append(f"第{ri}行：采购订单号「{gv('po_no')}」不存在")
            continue
        try:
            price = float(gv("price") or 0)
        except Exception:
            price = 0.0
        try:
            tax = float(gv("tax") or 13)
        except Exception:
            tax = 13.0
        ordered = gv("ordered")
        try:
            ordered_q = float(ordered) if ordered not in (None, "") else received
        except Exception:
            ordered_q = received
        operator = str(gv("operator") or "仓管员").strip()
        remark = str(gv("remark") or "").strip()
        if remark.startswith("示例行") or remark.startswith("请替换"):
            continue  # 模板示例行跳过
        db.add(models.PurchaseInbound(
            account_set_id=ACCOUNT_SET_ID,
            inbound_no=_ib_gen_no(db),
            purchase_order_id=po.id if po else 0,
            supplier_id=po.supplier_id if po else None,
            material_id=mat.id,
            ordered_qty=Decimal(str(ordered_q)),
            received_qty=Decimal(str(received)),
            unit_price=Decimal(str(price)),
            amount=Decimal(str(round(received * price, 2))),
            tax_rate=Decimal(str(tax)),
            quality_status="PENDING",
            inbound_date=_ib_date(gv("date")),
            operator=operator,
            status="DRAFT",
            has_invoice=False,
            notes=remark or None,
        ))
        if po:
            po_ids.add(po.id)
        ok_rows += 1
    if not ok_rows and fail_rows:
        db.rollback()
        return make_response(False, {"fail_rows": fail_rows}, "全部行导入失败，未生成入库单")
    db.commit()
    msg = f"导入成功 {ok_rows} 行入库单（待审核）"
    if fail_rows:
        msg += f"；失败 {len(fail_rows)} 行"
    return make_response(True, {"imported": ok_rows, "fail_rows": fail_rows, "po_ids": list(po_ids)}, msg)


# ============================================================
# 6. 报表与分析
# ============================================================
@router.get("/reports/order-execution", tags=["采购管理"])
def report_order_execution(month: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.PurchaseOrder)
    if month:
        y, m = int(month[:4]), int(month[5:7])
        q = q.filter(models.PurchaseOrder.created_at >= f"{y}-{m}-01",
                     models.PurchaseOrder.created_at < f"{y}-{m+1 if m<12 else 1}-01")
    orders = q.all()
    items = []
    total_amount = 0
    for o in orders:
        s = db.query(models.Supplier).filter(models.Supplier.id == o.supplier_id).first()
        pos = db.query(models.PurchaseOrderItem).filter(models.PurchaseOrderItem.purchase_order_id == o.id).all()
        amount = sum(float(i.unit_price or 0) * int(i.quantity or 0) for i in pos)
        total_amount += amount
        items.append({
            "po_no": o.po_no, "supplier_name": s.name if s else "",
            "status": o.status, "amount": round(amount, 2),
            "item_count": len(pos),
            "created_at": _fmt_date(o.created_at),
        })
    return make_response(True, {"items": items, "total_count": len(items), "total_amount": round(total_amount, 2)})


@router.get("/reports/supplier-performance", tags=["采购管理"])
def report_supplier_performance(month: Optional[str] = None, db: Session = Depends(get_db)):
    suppliers = db.query(models.Supplier).all()
    items = []
    for s in suppliers:
        pos = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.supplier_id == s.id).all()
        total_amt = 0
        total_items = 0
        for po in pos:
            po_items = db.query(models.PurchaseOrderItem).filter(models.PurchaseOrderItem.purchase_order_id == po.id).all()
            total_amt += sum(float(i.unit_price or 0) * int(i.quantity or 0) for i in po_items)
            total_items += len(po_items)
        evals = db.query(models.SupplierEvaluation).filter(models.SupplierEvaluation.supplier_id == s.id).all()
        avg_score = sum(float(e.composite_score) for e in evals) / len(evals) if evals else 0
        items.append({
            "supplier_id": s.id, "supplier_name": s.name, "order_count": len(pos),
            "total_amount": round(total_amt, 2), "item_lines": total_items,
            "avg_score": round(avg_score, 2),
            "on_time_rate": float(s.on_time_rate or 0),
            "quality_rate": float(s.quality_rate or 0),
        })
    return make_response(True, {"items": items})


@router.get("/reports/price-fluctuation", tags=["采购管理"])
def report_price_fluctuation(db: Session = Depends(get_db)):
    """采购价格波动"""
    items = []
    for mat in db.query(models.Material).limit(20).all():
        # 查所有入库单中的历史价格
        inbounds = db.query(models.PurchaseInbound)\
            .filter(models.PurchaseInbound.material_id == mat.id)\
            .order_by(models.PurchaseInbound.created_at.desc()).limit(10).all()
        if not inbounds: continue
        prices = [float(i.unit_price) for i in inbounds]
        avg = sum(prices) / len(prices)
        min_p = min(prices); max_p = max(prices)
        items.append({
            "material_id": mat.id, "material_code": mat.code, "material_name": mat.name,
            "current_price": prices[0], "avg_price": round(avg, 2),
            "min_price": round(min_p, 2), "max_price": round(max_p, 2),
            "change_pct": round((prices[0] - avg) / avg * 100, 2) if avg > 0 else 0,
            "history": [{"date": _fmt_date(i.created_at), "price": float(i.unit_price)} for i in inbounds],
        })
    return make_response(True, {"items": items})


# ============================================================
# 7. 供应商列表增强
# ============================================================
@router.post("/suppliers", tags=["采购管理"])
def create_supplier_v2(data: dict, db: Session = Depends(get_db)):
    existing = db.query(models.Supplier).filter(models.Supplier.code == data.get("code")).first()
    if existing:
        return make_response(False, None, "供应商编码已存在", "40003")
    s = models.Supplier(
        account_set_id=ACCOUNT_SET_ID,
        name=data.get("name"), code=data.get("code"),
        tax_id=data.get("tax_id"), contact=data.get("contact"),
        phone=data.get("phone"), email=data.get("email"),
        address=data.get("address"),
        history_price=Decimal(str(data.get("last_price", 0))),
        on_time_rate=Decimal(str(data.get("on_time_rate", 100))),
        quality_rate=Decimal(str(data.get("quality_rate", 100))),
    )
    db.add(s)
    db.commit()
    return make_response(True, {"id": s.id, "code": s.code, "name": s.name})


@router.put("/suppliers/{sid}", tags=["采购管理"])
def update_supplier(sid: int, data: dict, db: Session = Depends(get_db)):
    s = db.query(models.Supplier).filter(models.Supplier.id == sid).first()
    if not s:
        return make_response(False, None, "供应商不存在")
    for k, v in data.items():
        if hasattr(s, k) and v is not None:
            setattr(s, k, v)
    db.commit()
    return make_response(True, {"id": s.id})


# ============================================================
# 供应商列表查询
# ============================================================
@router.get("/suppliers", tags=["采购管理"])
def list_suppliers(keyword: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Supplier)
    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(
            models.Supplier.name.ilike(kw) |
            models.Supplier.code.ilike(kw) |
            models.Supplier.contact.ilike(kw)
        )
    items = query.all()
    result = []
    for s in items:
        sup_mats = db.query(models.Material).filter(models.Material.default_supplier_id == s.id).all()
        result.append({
            "id": s.id,
            "code": s.code or "",
            "name": s.name or "",
            "contact": s.contact or "",
            "phone": s.phone or "",
            "email": s.email or "",
            "address": s.address or "",
            "on_time_rate": float(s.on_time_rate) if s.on_time_rate else 0,
            "quality_rate": float(s.quality_rate) if s.quality_rate else 0,
            "history_price": float(s.history_price) if s.history_price else 0,
            "materials": [m.name for m in sup_mats],
            "material_count": len(sup_mats),
            "status": "active",  # 现有模型无status字段，默认为active
            "rating": 0,  # 现有模型无rating字段
        })
    return make_response(True, {"items": result})


@router.get("/suppliers/export", tags=["采购管理"])
def export_suppliers(db: Session = Depends(get_db)):
    """导出供应商台账（含供应物料清单）"""
    from fastapi.responses import StreamingResponse
    import openpyxl
    from urllib.parse import quote
    suppliers = db.query(models.Supplier).order_by(models.Supplier.code).all()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "供应商台账"
    headers = ["供应商编码", "供应商名称", "联系人", "电话", "邮箱", "地址", "准时交付率%", "质量合格率%", "历史参考价", "供应物料", "物料数"]
    ws.append(headers)
    for s in suppliers:
        sup_mats = db.query(models.Material).filter(models.Material.default_supplier_id == s.id).all()
        ws.append([
            s.code or "", s.name or "", s.contact or "", s.phone or "", s.email or "", s.address or "",
            round(float(s.on_time_rate), 1) if s.on_time_rate else 0,
            round(float(s.quality_rate), 1) if s.quality_rate else 0,
            float(s.history_price) if s.history_price else 0,
            "、".join(m.name for m in sup_mats),
            len(sup_mats),
        ])
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 16
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    fname = quote("供应商台账")
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{fname}.xlsx"})


# ============================================================
# 采购合同（填写式合同文书 + 法律声明）
# ============================================================

_DEFAULT_LEGAL_DECLARATION = """1. 本合同经双方授权代表签字并加盖公章（或合同专用章）后生效，具有法律约束力，双方应严格履行。
2. 双方保证具备签署及履行本合同所需的合法经营资格与授权，签署本合同系双方真实意思表示，不存在欺诈、胁迫或重大误解情形。
3. 任何一方提供虚假资质、虚假信息或以欺诈手段订立合同的，另一方有权解除合同、要求赔偿全部损失并依法追究其法律责任。
4. 未经对方书面同意，任何一方不得将本合同项下权利义务全部或部分转让给第三方。
5. 双方对履行本合同过程中知悉的对方商业秘密、技术资料及价格信息负有保密义务，未经书面许可不得向第三方披露。
6. 因不可抗力致使合同不能履行的，根据不可抗力的影响程度，部分或全部免除违约责任，但应及时通知对方并提供证明。
7. 本合同未尽事宜，双方可另行签订补充协议；补充协议与本合同具有同等法律效力。
8. 本合同一式两份，甲乙双方各执一份，自双方签字盖章之日起生效。"""

_DEFAULT_QUALITY_TERMS = "货物应符合国家标准、行业标准及乙方明示的质量要求，随货提供合格证/质检报告；质量保证期不少于约定期限。"
_DEFAULT_ACCEPTANCE_TERMS = "货到后甲方应在7个工作日内按订单及送货单验收数量、外观、规格；质量异议应在验收后15日内书面提出，乙方负责退换货并承担费用。"


def _gen_contract_no(db: Session) -> str:
    import uuid
    while True:
        no = f"CT-{datetime.date.today().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        if not db.query(models.PurchaseContract).filter(models.PurchaseContract.contract_no == no).first():
            return no


def _contract_dict(c: models.PurchaseContract, with_items: bool = False) -> dict:
    d = {
        "id": c.id,
        "contract_no": c.contract_no,
        "title": c.title,
        "supplier_id": c.supplier_id,
        "supplier_name": (c.supplier.name if c.supplier else "") or "",
        "purchase_order_id": c.purchase_order_id,
        "project_id": c.project_id,
        "party_a_name": c.party_a_name or "",
        "party_a_address": c.party_a_address or "",
        "party_a_contact": c.party_a_contact or "",
        "party_a_phone": c.party_a_phone or "",
        "party_b_name": c.party_b_name or "",
        "party_b_address": c.party_b_address or "",
        "party_b_contact": c.party_b_contact or "",
        "party_b_phone": c.party_b_phone or "",
        "total_amount": float(c.total_amount or 0),
        "sign_date": c.sign_date.isoformat() if c.sign_date else "",
        "delivery_date": c.delivery_date.isoformat() if c.delivery_date else "",
        "delivery_location": c.delivery_location or "",
        "payment_terms": c.payment_terms or "",
        "quality_terms": c.quality_terms or "",
        "acceptance_terms": c.acceptance_terms or "",
        "warranty_months": int(c.warranty_months or 0),
        "breach_rate": float(c.breach_rate or 0),
        "special_terms": c.special_terms or "",
        "legal_declaration": c.legal_declaration or "",
        "status": c.status or "DRAFT",
        "remark": c.remark or "",
        "created_at": c.created_at.isoformat() if c.created_at else "",
    }
    if with_items:
        d["items"] = [{
            "id": i.id,
            "line_no": i.line_no or 0,
            "material_code": i.material_code or "",
            "material_name": i.material_name or "",
            "spec": i.spec or "",
            "quantity": float(i.quantity or 0),
            "unit": i.unit or "",
            "unit_price": float(i.unit_price or 0),
            "amount": float(i.amount or 0),
            "delivery_date": i.delivery_date.isoformat() if i.delivery_date else "",
            "remark": i.remark or "",
        } for i in sorted(c.items, key=lambda x: (x.line_no or 0, x.id))]
    return d


def _parse_contract_date(v):
    if not v:
        return None
    if isinstance(v, datetime.date):
        return v
    try:
        return datetime.date.fromisoformat(str(v).strip()[:10])
    except Exception:
        return None


@router.get("/contracts/export", tags=["采购管理"])
def export_contracts(db: Session = Depends(get_db)):
    """导出采购合同台账Excel"""
    from fastapi.responses import StreamingResponse
    import openpyxl
    from urllib.parse import quote
    rows_q = db.query(models.PurchaseContract).order_by(models.PurchaseContract.created_at.desc()).all()
    status_map = {"DRAFT": "草稿", "SIGNED": "已签署", "CANCELLED": "已作废"}
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "采购合同台账"
    headers = ["合同编号", "合同名称", "供应商", "合同金额", "签订日期", "交付日期", "交付地点",
               "付款方式", "质保期(月)", "违约金比例%", "状态", "甲方", "乙方", "备注"]
    ws.append(headers)
    for c in rows_q:
        ws.append([
            c.contract_no or "", c.title or "",
            (c.supplier.name if c.supplier else "") or (c.party_b_name or ""),
            float(c.total_amount or 0),
            c.sign_date.isoformat() if c.sign_date else "",
            c.delivery_date.isoformat() if c.delivery_date else "",
            c.delivery_location or "", c.payment_terms or "",
            int(c.warranty_months or 0), float(c.breach_rate or 0),
            status_map.get(c.status or "", c.status or ""),
            c.party_a_name or "", c.party_b_name or "", c.remark or "",
        ])
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 16
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    fname = quote("采购合同台账")
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{fname}.xlsx"})


@router.get("/contracts", tags=["采购管理"])
def list_contracts(keyword: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.PurchaseContract)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(models.PurchaseContract.title.ilike(kw) |
                     models.PurchaseContract.contract_no.ilike(kw) |
                     models.PurchaseContract.party_b_name.ilike(kw))
    if status:
        q = q.filter(models.PurchaseContract.status == status)
    rows = q.order_by(models.PurchaseContract.created_at.desc()).all()
    return make_response(True, {"items": [_contract_dict(c) for c in rows], "total": len(rows)})


@router.post("/contracts", tags=["采购管理"])
def create_contract(data: dict, db: Session = Depends(get_db)):
    title = (data.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="合同名称不能为空")
    c = models.PurchaseContract(
        account_set_id=data.get("account_set_id", 1),
        contract_no=(data.get("contract_no") or "").strip() or _gen_contract_no(db),
        title=title,
        supplier_id=data.get("supplier_id") or None,
        purchase_order_id=data.get("purchase_order_id") or None,
        project_id=data.get("project_id") or None,
        party_a_name=data.get("party_a_name") or "",
        party_a_address=data.get("party_a_address") or "",
        party_a_contact=data.get("party_a_contact") or "",
        party_a_phone=data.get("party_a_phone") or "",
        party_b_name=data.get("party_b_name") or "",
        party_b_address=data.get("party_b_address") or "",
        party_b_contact=data.get("party_b_contact") or "",
        party_b_phone=data.get("party_b_phone") or "",
        total_amount=float(data.get("total_amount") or 0),
        sign_date=_parse_contract_date(data.get("sign_date")),
        delivery_date=_parse_contract_date(data.get("delivery_date")),
        delivery_location=data.get("delivery_location") or "",
        payment_terms=data.get("payment_terms") or "",
        quality_terms=data.get("quality_terms") or _DEFAULT_QUALITY_TERMS,
        acceptance_terms=data.get("acceptance_terms") or _DEFAULT_ACCEPTANCE_TERMS,
        warranty_months=int(data.get("warranty_months") or 12),
        breach_rate=float(data.get("breach_rate") or 5),
        special_terms=data.get("special_terms") or "",
        legal_declaration=data.get("legal_declaration") or _DEFAULT_LEGAL_DECLARATION,
        status=data.get("status") or "DRAFT",
        remark=data.get("remark") or "",
    )
    db.add(c)
    db.flush()
    for idx, it in enumerate(data.get("items") or [], 1):
        name = (it.get("material_name") or "").strip()
        if not name:
            continue
        db.add(models.PurchaseContractItem(
            contract_id=c.id, line_no=it.get("line_no") or idx,
            material_code=it.get("material_code") or "",
            material_name=name, spec=it.get("spec") or "",
            quantity=float(it.get("quantity") or 1), unit=it.get("unit") or "",
            unit_price=float(it.get("unit_price") or 0),
            amount=float(it.get("amount") or (float(it.get("quantity") or 1) * float(it.get("unit_price") or 0))),
            delivery_date=_parse_contract_date(it.get("delivery_date")),
            remark=it.get("remark") or "",
        ))
    db.commit()
    db.refresh(c)
    return make_response(True, _contract_dict(c, with_items=True), "合同已创建")


@router.get("/contracts/{cid}", tags=["采购管理"])
def get_contract(cid: int, db: Session = Depends(get_db)):
    c = db.query(models.PurchaseContract).filter(models.PurchaseContract.id == cid).first()
    if not c:
        raise HTTPException(status_code=404, detail="合同不存在")
    return make_response(True, _contract_dict(c, with_items=True))


@router.put("/contracts/{cid}", tags=["采购管理"])
def update_contract(cid: int, data: dict, db: Session = Depends(get_db)):
    c = db.query(models.PurchaseContract).filter(models.PurchaseContract.id == cid).first()
    if not c:
        raise HTTPException(status_code=404, detail="合同不存在")
    if c.status == "CANCELLED":
        raise HTTPException(status_code=400, detail="已作废合同不可编辑")
    fields = ["title", "party_a_name", "party_a_address", "party_a_contact", "party_a_phone",
              "party_b_name", "party_b_address", "party_b_contact", "party_b_phone",
              "delivery_location", "payment_terms", "quality_terms", "acceptance_terms",
              "special_terms", "legal_declaration", "remark", "status"]
    for f in fields:
        if f in data:
            setattr(c, f, data.get(f) or ("" if f not in ("title",) else c.title))
    if "supplier_id" in data:
        c.supplier_id = data.get("supplier_id") or None
    if "total_amount" in data:
        c.total_amount = float(data.get("total_amount") or 0)
    if "warranty_months" in data:
        c.warranty_months = int(data.get("warranty_months") or 12)
    if "breach_rate" in data:
        c.breach_rate = float(data.get("breach_rate") or 5)
    if "sign_date" in data:
        c.sign_date = _parse_contract_date(data.get("sign_date"))
    if "delivery_date" in data:
        c.delivery_date = _parse_contract_date(data.get("delivery_date"))
    # 明细整体替换
    if "items" in data:
        db.query(models.PurchaseContractItem).filter(models.PurchaseContractItem.contract_id == cid).delete()
        for idx, it in enumerate(data.get("items") or [], 1):
            name = (it.get("material_name") or "").strip()
            if not name:
                continue
            db.add(models.PurchaseContractItem(
                contract_id=cid, line_no=it.get("line_no") or idx,
                material_code=it.get("material_code") or "",
                material_name=name, spec=it.get("spec") or "",
                quantity=float(it.get("quantity") or 1), unit=it.get("unit") or "",
                unit_price=float(it.get("unit_price") or 0),
                amount=float(it.get("amount") or (float(it.get("quantity") or 1) * float(it.get("unit_price") or 0))),
                delivery_date=_parse_contract_date(it.get("delivery_date")),
                remark=it.get("remark") or "",
            ))
    db.commit()
    db.refresh(c)
    return make_response(True, _contract_dict(c, with_items=True), "合同已保存")


@router.delete("/contracts/{cid}", tags=["采购管理"])
def delete_contract(cid: int, db: Session = Depends(get_db)):
    c = db.query(models.PurchaseContract).filter(models.PurchaseContract.id == cid).first()
    if not c:
        raise HTTPException(status_code=404, detail="合同不存在")
    db.query(models.PurchaseContractItem).filter(models.PurchaseContractItem.contract_id == cid).delete()
    db.delete(c)
    db.commit()
    return make_response(True, None, "合同已删除")


@router.get("/contracts/{cid}/print", tags=["采购管理"])
def print_contract(cid: int, db: Session = Depends(get_db)):
    """生成正式采购合同文书（HTML，可直接浏览器打印/另存PDF）"""
    from fastapi.responses import HTMLResponse
    from html import escape
    c = db.query(models.PurchaseContract).filter(models.PurchaseContract.id == cid).first()
    if not c:
        raise HTTPException(status_code=404, detail="合同不存在")
    d = _contract_dict(c, with_items=True)
    status_map = {"DRAFT": "草稿", "SIGNED": "已签署", "CANCELLED": "已作废"}

    item_rows = "".join(
        f"<tr><td>{escape(str(i['line_no']))}</td>"
        f"<td>{escape(i['material_code'])}</td>"
        f"<td style='text-align:left;'>{escape(i['material_name'])}</td>"
        f"<td>{escape(i['spec'])}</td>"
        f"<td>{i['quantity']:g}</td>"
        f"<td>{escape(i['unit'])}</td>"
        f"<td style='text-align:right;'>{i['unit_price']:,.2f}</td>"
        f"<td style='text-align:right;'>{i['amount']:,.2f}</td>"
        f"<td>{escape(i['delivery_date'])}</td></tr>"
        for i in d["items"]
    ) or "<tr><td colspan='9' style='text-align:center;color:#999;'>（无明细，请在合同中补充约定）</td></tr>"

    def _num_cn(v: float) -> str:
        """人民币大写"""
        if v <= 0:
            return "零元整"
        digits = "零壹贰叁肆伍陆柒捌玖"
        units = ["", "拾", "佰", "仟"]
        bigs = ["", "万", "亿", "万亿"]
        n = int(round(v * 100))
        jiao, fen = n // 10 % 10, n % 10
        n //= 100
        int_part = ""
        if n > 0:
            groups = []
            while n > 0:
                groups.append(n % 10000)
                n //= 10000
            text = ""
            zero_pending = False
            for gi in range(len(groups) - 1, -1, -1):
                g = groups[gi]
                if g == 0:
                    zero_pending = True
                    continue
                gtxt = ""
                zero_in = False
                for di in range(3, -1, -1):
                    dv = (g // (10 ** di)) % 10
                    if dv == 0:
                        if gtxt:
                            zero_in = True
                    else:
                        if zero_in:
                            gtxt += "零"
                            zero_in = False
                        gtxt += digits[dv] + units[di]
                if zero_pending and text:
                    text += "零"
                text += gtxt + bigs[gi]
                zero_pending = False
            int_part = text + "元"
        parts = [int_part] if int_part else []
        if jiao == 0 and fen == 0:
            parts.append("整")
        else:
            if jiao > 0:
                parts.append(digits[jiao] + "角")
            elif parts and fen > 0:
                parts.append("零")
            if fen > 0:
                parts.append(digits[fen] + "分")
        return "".join(parts)

    total = d["total_amount"]
    legal_html = "".join(f"<p style='margin:4px 0;text-indent:2em;'>{escape(line)}</p>"
                         for line in (d["legal_declaration"] or "").splitlines() if line.strip())
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>采购合同 {escape(d['contract_no'])}</title>
<style>
  body{{font-family:"SimSun","Songti SC","Microsoft YaHei",serif;color:#111;max-width:820px;margin:0 auto;padding:28px 34px;font-size:14px;line-height:1.8;}}
  h1{{text-align:center;font-size:22px;letter-spacing:6px;margin:0 0 6px;}}
  .sub{{text-align:center;color:#555;font-size:12px;margin-bottom:18px;}}
  .badge{{display:inline-block;border:1px solid #888;border-radius:4px;padding:0 8px;font-size:12px;color:#444;margin-left:8px;}}
  table{{width:100%;border-collapse:collapse;margin:8px 0 14px;font-size:13px;}}
  th,td{{border:1px solid #444;padding:6px 8px;text-align:center;}}
  th{{background:#f2f2f2;}}
  .meta{{width:100%;border:none;font-size:13px;margin-bottom:12px;}}
  .meta td{{border:none;padding:2px 4px;}}
  h2{{font-size:15px;margin:16px 0 6px;}}
  .clause p{{margin:4px 0;text-indent:2em;}}
  .party{{border:1px solid #444;padding:10px 14px;margin:8px 0;}}
  .party b{{font-size:14px;}}
  .party table{{margin:4px 0 0;}}
  .party td{{border:none;text-align:left;padding:1px 6px;}}
  .sign{{display:flex;justify-content:space-between;margin-top:34px;gap:30px;}}
  .sign .box{{flex:1;border:1px dashed #666;padding:14px 18px;min-height:150px;}}
  .no-print{{position:fixed;top:12px;right:14px;display:flex;gap:8px;}}
  .no-print button{{padding:8px 18px;font-size:14px;border:none;border-radius:6px;background:#1e40af;color:#fff;cursor:pointer;}}
  .no-print button.ghost{{background:#fff;color:#1e40af;border:1px solid #1e40af;}}
  @media print{{.no-print{{display:none;}} body{{padding:0;}}}}
  @page{{margin:18mm 16mm;}}
</style></head><body>
<div class="no-print"><button class="ghost" onclick="history.back()">返回</button><button onclick="window.print()">🖨 打印 / 另存PDF</button></div>
<h1>采 购 合 同</h1>
<div class="sub">合同编号：{escape(d['contract_no'])}<span class="badge">{status_map.get(d['status'], d['status'])}</span></div>
<table class="meta"><tr>
  <td style="width:33%;">签订日期：{escape(d['sign_date']) or '____年__月__日'}</td>
  <td style="width:33%;">合同名称：{escape(d['title'])}</td>
  <td>合同金额（含税）：￥{total:,.2f}</td>
</tr></table>
<div class="party"><b>甲方（采购方）：</b>
  <table><tr><td style="width:50%;">单位名称：{escape(d['party_a_name']) or '____________________'}</td><td>地址：{escape(d['party_a_address']) or '____________________'}</td></tr>
  <tr><td>联系人：{escape(d['party_a_contact']) or '____________'}</td><td>电话：{escape(d['party_a_phone']) or '____________'}</td></tr></table>
</div>
<div class="party"><b>乙方（供货方）：</b>
  <table><tr><td style="width:50%;">单位名称：{escape(d['party_b_name']) or '____________________'}</td><td>地址：{escape(d['party_b_address']) or '____________________'}</td></tr>
  <tr><td>联系人：{escape(d['party_b_contact']) or '____________'}</td><td>电话：{escape(d['party_b_phone']) or '____________'}</td></tr></table>
</div>
<p>根据《中华人民共和国民法典》及相关法律法规，甲乙双方本着平等自愿、诚实信用的原则，就甲方向乙方采购货物事宜协商一致，订立本合同共同遵守。</p>
<h2>第一条 采购标的</h2>
<table><thead><tr><th>序号</th><th>物料编码</th><th>物料名称</th><th>规格型号</th><th>数量</th><th>单位</th><th>单价（元）</th><th>金额（元）</th><th>交付日期</th></tr></thead>
<tbody>{item_rows}</tbody>
<tfoot><tr><td colspan="7" style="text-align:right;font-weight:bold;">合计（含税）</td><td style="text-align:right;font-weight:bold;">￥{total:,.2f}</td><td></td></tr></tfoot></table>
<p style="text-align:right;font-size:13px;">金额大写：人民币 {_num_cn(total)}</p>
<h2>第二条 质量标准</h2>
<div class="clause">{escape(d['quality_terms'])}</div>
<h2>第三条 交付与运输</h2>
<div class="clause"><p>交付日期：{escape(d['delivery_date']) or '____年__月__日'}；交付地点：{escape(d['delivery_location']) or '甲方指定地点'}。运输方式及费用由乙方承担（另有约定除外），货物毁损灭失风险交付前由乙方承担。</p></div>
<h2>第四条 验收</h2>
<div class="clause">{escape(d['acceptance_terms'])}</div>
<h2>第五条 付款方式</h2>
<div class="clause">{escape(d['payment_terms']) or '____________（如：预付30%，到货验收后付60%，质保金10%满一年支付）'}</div>
<h2>第六条 质量保证</h2>
<div class="clause"><p>质保期 {d['warranty_months']} 个月，自验收合格之日起算。质保期内因产品质量问题造成的损失，由乙方负责维修、更换或赔偿。</p></div>
<h2>第七条 违约责任</h2>
<div class="clause"><p>乙方逾期交付的，每逾期一日按合同金额的 {d['breach_rate']:g}% 向甲方支付违约金；甲方逾期付款的，每逾期一日按未付金额的 {d['breach_rate']:g}% 向乙方支付违约金。违约金总额以不超过合同金额的 20% 为限；给对方造成损失超过违约金的，还应赔偿差额。</p></div>
<h2>第八条 特别约定</h2>
<div class="clause">{escape(d['special_terms']) or '<p style="color:#999;">（无）</p>'}</div>
<h2>第九条 法律声明</h2>
<div class="clause">{legal_html}</div>
<h2>第十条 争议解决</h2>
<div class="clause"><p>因本合同引起的争议，双方应友好协商解决；协商不成的，任何一方可向甲方所在地有管辖权的人民法院提起诉讼。</p></div>
<div class="sign">
  <div class="box"><b>甲方（盖章）：</b><br><br>
    授权代表签字：________________<br><br>
    签订日期：______年____月____日
  </div>
  <div class="box"><b>乙方（盖章）：</b><br><br>
    授权代表签字：________________<br><br>
    签订日期：______年____月____日
  </div>
</div>
</body></html>"""
    return HTMLResponse(html)


# ============================================================
# 采购订单列表
# ============================================================
@router.get("/orders", tags=["采购管理"])
def list_orders(
    status: Optional[str] = None,
    supplier_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.PurchaseOrder)
    if status:
        query = query.filter(models.PurchaseOrder.status == status)
    if supplier_id:
        query = query.filter(models.PurchaseOrder.supplier_id == supplier_id)
    orders = query.order_by(models.PurchaseOrder.created_at.desc()).all()
    result = []
    for o in orders:
        items = db.query(models.PurchaseOrderItem).filter(
            models.PurchaseOrderItem.purchase_order_id == o.id
        ).all()
        proj = db.query(models.WBSProject).filter(models.WBSProject.id == o.project_id).first() if o.project_id else None
        result.append({
            "id": o.id,
            "order_no": o.po_no or "",
            "po_no": o.po_no or "",
            "supplier_id": o.supplier_id,
            "supplier_name": o.supplier.name if o.supplier else "",
            "order_date": _fmt_date(o.order_date),
            "expected_date": _fmt_date(o.expected_date),
            "status": o.status or "PENDING",
            "payment_terms": o.payment_terms or "",
            "transport_type": o.transport_type or "",
            "total_amount": float(o.total_amount) if o.total_amount else 0,
            "project_id": o.project_id,
            "project_name": proj.project_name if proj else "",
            "project_no": proj.project_no if proj else "",
            "remark": o.remark or "",
            "items": [{
                "id": i.id,
                "material_id": i.material_id,
                "material_name": i.material.name if i.material else "",
                "material_spec": i.material.spec if i.material else "",
                "material_code": (i.remark or ""),
                "unit": i.unit or "",
                "supplier_name": (i.supplier_name or ""),
                "delivery_date": _fmt_date(i.delivery_date),
                "quantity": float(i.quantity) if i.quantity else 0,
                "unit_price": float(i.unit_price) if i.unit_price else 0,
                "amount": float(i.amount) if i.amount else 0,
                "received_qty": float(i.received_qty) if i.received_qty else 0,
                "source_no": i.source_no or "",
            } for i in items]
        })
    return make_response(True, {"items": result})


# ============================================================
# 采购订单明细改价（手动输入单价）
# ============================================================
@router.put("/orders/{oid}/items/{item_id}", tags=["采购管理"])
def update_order_item_price(oid: int, item_id: int, data: dict = Body(...), db: Session = Depends(get_db)):
    it = db.query(models.PurchaseOrderItem).filter(
        models.PurchaseOrderItem.id == item_id,
        models.PurchaseOrderItem.purchase_order_id == oid
    ).first()
    if not it:
        return make_response(False, None, "订单明细不存在", "40401")
    o = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == oid).first()
    if o and o.status not in ("DRAFT", "PENDING"):
        return make_response(False, None, "订单已审核，不能改价", "40003")
    price = float(data.get("unit_price") or 0)
    if price < 0:
        return make_response(False, None, "单价不能为负数", "40004")
    it.unit_price = price
    it.amount = round(float(it.quantity or 0) * price, 2)
    # 行级供应商与交付日期
    if "supplier_name" in data:
        it.supplier_name = (data.get("supplier_name") or "").strip() or None
        if it.supplier_name:
            m = db.query(models.Material).filter(models.Material.id == it.material_id).first()
            if m:
                key = it.supplier_name.replace(" ", "").lower()
                sup = None
                for s in db.query(models.Supplier).all():
                    if (s.name or "").replace(" ", "").lower() == key:
                        sup = s
                        break
                if not sup:
                    cnt = db.query(models.Supplier).count()
                    sup = models.Supplier(
                        account_set_id=o.account_set_id if o.account_set_id else 1,
                        name=it.supplier_name,
                        code=f"GYS-{cnt+1:03d}",
                        is_overseas=False,
                    )
                    db.add(sup)
                    db.flush()
                m.default_supplier_id = sup.id
    if "delivery_date" in data:
        dd = (data.get("delivery_date") or "").strip()
        if dd:
            try:
                it.delivery_date = datetime.date.fromisoformat(dd)
            except ValueError:
                try:
                    it.delivery_date = datetime.datetime.strptime(dd, "%Y/%m/%d").date()
                except ValueError:
                    pass
        else:
            it.delivery_date = None
    if o:
        total = 0.0
        for x in db.query(models.PurchaseOrderItem).filter(
            models.PurchaseOrderItem.purchase_order_id == oid
        ).all():
            total += float(x.amount or (float(x.unit_price or 0) * float(x.quantity or 0)))
        o.total_amount = round(total, 2)
    # 回写物料最近采购价
    m = db.query(models.Material).filter(models.Material.id == it.material_id).first()
    if m and price > 0:
        m.last_purchase_price = price
    db.commit()
    return make_response(True, {
        "unit_price": price,
        "amount": float(it.amount or 0),
        "total_amount": float(o.total_amount or 0) if o else 0,
    }, "单价已保存")


# ============================================================
# 手动指定订单供应商（自动建档+供应物料编入供应商管理）
# ============================================================
@router.put("/orders/{oid}/supplier", tags=["采购管理"])
def assign_order_supplier(oid: int, data: dict = Body(...), db: Session = Depends(get_db)):
    name = (data.get("supplier_name") or "").strip()
    if not name:
        return make_response(False, None, "请输入供应商名称", "40001")
    o = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == oid).first()
    if not o:
        return make_response(False, None, "订单不存在", "40401")
    if o.status not in ("DRAFT", "PENDING"):
        return make_response(False, None, "订单已审核，不能更换供应商", "40003")
    # 按名称查找供应商（忽略空格与大小写），不存在则自动建档
    key = name.replace(" ", "").lower()
    sup = None
    for s in db.query(models.Supplier).all():
        if (s.name or "").replace(" ", "").lower() == key:
            sup = s
            break
    created = False
    if not sup:
        cnt = db.query(models.Supplier).count()
        sup = models.Supplier(
            account_set_id=o.account_set_id if o.account_set_id else 1,
            name=name,
            code=f"GYS-{cnt+1:03d}",
            is_overseas=False,
        )
        db.add(sup)
        db.commit()
        db.refresh(sup)
        created = True
    o.supplier_id = sup.id
    # 订单物料编入该供应商名下（供应物料）
    mats = []
    for it in db.query(models.PurchaseOrderItem).filter(
        models.PurchaseOrderItem.purchase_order_id == oid
    ).all():
        if it.material_id:
            m = db.query(models.Material).filter(models.Material.id == it.material_id).first()
            if m:
                m.default_supplier_id = sup.id
                mats.append(m.name or "")
    db.commit()
    return make_response(True, {
        "supplier_id": sup.id,
        "supplier_code": sup.code,
        "supplier_name": sup.name,
        "created": created,
        "materials": [m for m in mats if m],
    }, (f"供应商「{sup.name}」已建档并绑定订单" if created else f"已绑定现有供应商「{sup.name}」") + f"，{len(mats)}项物料已编入其供应清单")


# ============================================================
# 采购订单明细 Excel 导出 / 导入
# ============================================================
@router.get("/orders/{oid}/export", tags=["采购管理"])
def export_order_items(oid: int, db: Session = Depends(get_db)):
    """导出订单明细Excel（物料编码/名称/规格/数量/单位/单价/金额/供应商/交付日期）"""
    from fastapi.responses import StreamingResponse
    import openpyxl
    o = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == oid).first()
    if not o:
        raise HTTPException(404, "订单不存在")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "采购订单明细"
    headers = ["物料编码", "物料名称", "规格", "数量", "单位", "单价", "金额", "供应商", "交付日期"]
    ws.append(headers)
    items = db.query(models.PurchaseOrderItem).filter(
        models.PurchaseOrderItem.purchase_order_id == oid
    ).all()
    for i in items:
        ws.append([
            i.remark or "",
            i.material.name if i.material else "",
            i.material.spec if i.material else "",
            float(i.quantity or 0),
            i.unit or "",
            float(i.unit_price or 0),
            float(i.amount or 0),
            i.supplier_name or "",
            i.delivery_date.strftime("%Y-%m-%d") if i.delivery_date else "",
        ])
    ws.append([])
    ws.append(["合计", "", "", "", "", "", o.total_amount or 0, "", ""])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    fname = (getattr(o, "po_no", "") or getattr(o, "order_no", "") or f"PO-{oid}").replace("/", "-")
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={fname}.xlsx"})


@router.post("/orders/{oid}/import", tags=["采购管理"])
async def import_order_items(oid: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """导入订单明细Excel：按物料编码匹配行，批量更新单价/供应商/交付日期"""
    import openpyxl
    o = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == oid).first()
    if not o:
        return make_response(False, None, "订单不存在", "40401")
    if o.status not in ("DRAFT", "PENDING"):
        return make_response(False, None, "订单已审核，不能导入", "40003")
    content = await file.read()
    try:
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
    except Exception:
        return make_response(False, None, "Excel文件无法读取，请用导出的格式填写", "40001")
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return make_response(False, None, "表格为空", "40001")
    headers = [str(h).strip() if h is not None else "" for h in rows[0]]

    def col(*names):
        for n in names:
            for idx, h in enumerate(headers):
                if h and n in h.replace(" ", ""):
                    return idx
        return -1
    c_code, c_price = col("物料编码", "编码"), col("单价")
    c_sup, c_dd = col("供应商"), col("交付日期", "交期", "交货日期")
    if c_code < 0:
        return make_response(False, None, "缺少「物料编码」列", "40001")
    all_sups = db.query(models.Supplier).all()
    sup_cnt = len(all_sups)
    ok_cnt, fail_rows = 0, []
    items = db.query(models.PurchaseOrderItem).filter(
        models.PurchaseOrderItem.purchase_order_id == oid
    ).all()
    for rn, row in enumerate(rows[1:], start=2):
        code = str(row[c_code]).strip() if c_code >= 0 and row[c_code] is not None else ""
        if not code or code in ("合计", "总计", "小计"):
            continue
        it = next((x for x in items if (x.remark or "") == code), None)
        if not it:
            fail_rows.append(f"第{rn}行: 编码{code}不在本订单中")
            continue
        changed = False
        if c_price >= 0 and row[c_price] is not None and str(row[c_price]).strip() != "":
            try:
                price = float(row[c_price])
                if price >= 0:
                    it.unit_price = price
                    it.amount = round(float(it.quantity or 0) * price, 2)
                    changed = True
            except (TypeError, ValueError):
                fail_rows.append(f"第{rn}行: 单价「{row[c_price]}」不是数字")
        if c_sup >= 0 and row[c_sup] is not None and str(row[c_sup]).strip():
            name = str(row[c_sup]).strip()
            key = name.replace(" ", "").lower()
            sup = next((s for s in all_sups if (s.name or "").replace(" ", "").lower() == key), None)
            if not sup:
                sup_cnt += 1
                sup = models.Supplier(
                    account_set_id=o.account_set_id if o.account_set_id else 1,
                    name=name, code=f"GYS-{sup_cnt:03d}", is_overseas=False,
                )
                db.add(sup); db.flush(); all_sups.append(sup)
            it.supplier_name = sup.name
            m = db.query(models.Material).filter(models.Material.id == it.material_id).first()
            if m:
                m.default_supplier_id = sup.id
            if not o.supplier_id:
                o.supplier_id = sup.id
            changed = True
        if c_dd >= 0 and row[c_dd] is not None:
            v = row[c_dd]
            dd = None
            if isinstance(v, datetime.datetime):
                dd = v.date()
            elif isinstance(v, datetime.date):
                dd = v
            else:
                s = str(v).strip()
                for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y年%m月%d日"):
                    try:
                        dd = datetime.datetime.strptime(s, fmt).date()
                        break
                    except ValueError:
                        continue
                if dd is None:
                    fail_rows.append(f"第{rn}行: 交付日期「{s}」格式不认识")
            if dd:
                it.delivery_date = dd
                changed = True
        if changed:
            ok_cnt += 1
    # 重算订单总额
    total = 0.0
    for x in db.query(models.PurchaseOrderItem).filter(
        models.PurchaseOrderItem.purchase_order_id == oid
    ).all():
        total += float(x.amount or (x.unit_price or 0) * (x.quantity or 0))
    o.total_amount = round(total, 2)
    db.commit()
    msg = f"导入完成：成功{ok_cnt}条"
    if fail_rows:
        msg += f"，失败{len(fail_rows)}条"
    return make_response(True, {"ok": ok_cnt, "fail": len(fail_rows), "fail_rows": fail_rows[:10]}, msg)


# ============================================================
# 采购订单详情
# ============================================================
@router.get("/orders/{oid}", tags=["采购管理"])
def get_order(oid: int, db: Session = Depends(get_db)):
    o = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == oid).first()
    if not o:
        return make_response(False, None, "订单不存在", "40401")
    items = db.query(models.PurchaseOrderItem).filter(
        models.PurchaseOrderItem.purchase_order_id == o.id
    ).all()
    # Get communications
    comms = db.query(models.PurchaseCommunication).filter(
        models.PurchaseCommunication.purchase_order_id == o.id
    ).order_by(models.PurchaseCommunication.communication_date.desc()).all()
    result = {
        "id": o.id,
        "order_no": o.po_no,
        "supplier_id": o.supplier_id,
        "supplier_name": o.supplier.name if o.supplier else "",
        "order_date": _fmt_date(o.order_date),
        "expected_date": _fmt_date(o.expected_date),
        "status": o.status or "PENDING",
        "payment_terms": o.payment_terms or "",
        "transport_type": o.transport_type or "",
        "warehouse_id": o.warehouse_id,
        "total_amount": float(o.total_amount) if o.total_amount else 0,
        "remark": o.remark or "",
        "items": [{
            "id": i.id,
            "line_no": i.line_no,
            "material_id": i.material_id,
            "material_name": i.material.name if i.material else "",
            "material_spec": i.material.spec if i.material else "",
            "unit": i.unit or "",
            "supplier_name": (i.supplier_name or ""),
            "delivery_date": _fmt_date(i.delivery_date),
            "quantity": float(i.quantity) if i.quantity else 0,
            "unit_price": float(i.unit_price) if i.unit_price else 0,
            "amount": float(i.amount) if i.amount else 0,
            "tax_rate": float(i.tax_rate) if i.tax_rate else 0,
            "tax_amount": float(i.tax_amount) if i.tax_amount else 0,
            "total_amount": float(i.total_amount) if i.total_amount else 0,
            "received_qty": float(i.received_qty) if i.received_qty else 0,
            "source_no": i.source_no or "",
            "delivery_date": _fmt_date(i.delivery_date),
        } for i in items],
        "communications": [{
            "id": c.id,
            "contact_type": c.contact_type or "",
            "content": c.content or "",
            "communicator": c.communicator or "",
            "communication_date": _fmt_date(c.communication_date),
        } for c in comms]
    }
    return make_response(True, result)


# ============================================================
# 创建采购订单
# ============================================================
@router.post("/orders", tags=["采购管理"])
def create_order(data: dict, db: Session = Depends(get_db)):
    supplier_id = data.get("supplier_id")
    if not supplier_id:
        return make_response(False, None, "必须选择供应商", "40001")
    
    # Generate order number
    today = datetime.date.today()
    date_str = today.strftime("%Y%m%d")
    existing = db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.po_no.like(f"PO-{date_str}%")
    ).count()
    order_no = f"PO-{date_str}-{existing + 1:05d}"
    
    # Handle dates
    order_date = data.get("order_date")
    if isinstance(order_date, str):
        try: order_date = datetime.date.fromisoformat(order_date)
        except: order_date = today
    elif not order_date:
        order_date = today
    
    expected_date = data.get("expected_date")
    if isinstance(expected_date, str):
        try: expected_date = datetime.date.fromisoformat(expected_date)
        except: expected_date = None
    
    order = models.PurchaseOrder(
        account_set_id=ACCOUNT_SET_ID,
        po_no=order_no,
        supplier_id=supplier_id,
        order_date=order_date,
        expected_date=expected_date,
        status=data.get("status", "DRAFT"),
        payment_terms=data.get("payment_terms", ""),
        transport_type=data.get("transport_type", ""),
        warehouse_id=data.get("warehouse_id"),
        remark=data.get("remark", ""),
    )
    db.add(order)
    db.flush()
    
    # Add items
    items_data = data.get("items", [])
    total = Decimal("0")
    for idx, item in enumerate(items_data):
        qty = Decimal(str(item.get("quantity", 0)))
        price = Decimal(str(item.get("unit_price", 0)))
        amount = qty * price
        total += amount
        
        # Handle item delivery date
        item_delivery = item.get("delivery_date")
        if isinstance(item_delivery, str):
            try: item_delivery = datetime.date.fromisoformat(item_delivery)
            except: item_delivery = None
        
        po_item = models.PurchaseOrderItem(
            purchase_order_id=order.id,
            line_no=idx + 1,
            material_id=item.get("material_id"),
            quantity=qty,
            unit_price=price,
            amount=amount,
            source_no=item.get("source_no", ""),
            delivery_date=item_delivery,
            remark=item.get("remark", ""),
        )
        db.add(po_item)
    
    order.total_amount = total
    db.commit()
    db.refresh(order)
    
    return make_response(True, {"id": order.id, "order_no": order_no})


# ============================================================
# 采购订单审核
# ============================================================
@router.post("/orders/{oid}/approve", tags=["采购管理"])
def approve_order(oid: int, data: Optional[dict] = Body(default=None), db: Session = Depends(get_db)):
    data = data or {}
    o = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == oid).first()
    if not o:
        return make_response(False, None, "订单不存在", "40401")

    action = (data.get("action") or "approve")
    if action == "approve":
        if o.status == "DRAFT":
            o.status = "PENDING"  # 草稿 → 待审核
        elif o.status == "PENDING":
            o.status = "POSTED"  # 待审核 → 已下达
        else:
            return make_response(False, None, f"当前状态({o.status})不可审核", "40002")
        o.approved_at = datetime.datetime.now()
        # 供应商信息统一录入供应商管理（填写完毕审核时兜底：漏填的行级供应商、整单供应商都自动建档）
        all_sups = db.query(models.Supplier).all()
        sup_cnt = len(all_sups)
        _gys_nums = [int(s.code[4:]) for s in all_sups if (s.code or '').startswith('GYS-') and s.code[4:].isdigit()]
        _next_gys = max(_gys_nums, default=0)

        def _get_or_create(name):
            nonlocal sup_cnt, all_sups, _next_gys
            key = name.replace(" ", "").lower()
            for s in all_sups:
                if (s.name or "").replace(" ", "").lower() == key:
                    return s
            sup_cnt += 1
            _next_gys += 1
            _code = f"GYS-{_next_gys:03d}"
            while any((s.code or '') == _code for s in all_sups):
                _next_gys += 1
                _code = f"GYS-{_next_gys:03d}"
            sup = models.Supplier(
                account_set_id=o.account_set_id if o.account_set_id else 1,
                name=name.strip(),
                code=_code,
                is_overseas=False,
            )
            db.add(sup)
            db.flush()
            all_sups.append(sup)
            return sup
        if o.supplier_id:
            pass  # 整单供应商已绑定
        its = db.query(models.PurchaseOrderItem).filter(
            models.PurchaseOrderItem.purchase_order_id == oid
        ).all()
        for it in its:
            m = db.query(models.Material).filter(models.Material.id == it.material_id).first() if it.material_id else None
            # 行级供应商建档 + 物料挂靠
            if it.supplier_name and (it.supplier_name or "").strip():
                sup = _get_or_create(it.supplier_name)
                if m:
                    m.default_supplier_id = sup.id
                # 整单没绑定供应商时，用第一个行级供应商作为订单供应商
                if not o.supplier_id:
                    o.supplier_id = sup.id
            # 未填供应商的行，跟随整单供应商
            elif o.supplier_id and m and not m.default_supplier_id:
                m.default_supplier_id = o.supplier_id
    elif action == "reject":
        o.status = "CANCELLED"

    db.commit()
    # 采购正式下达（待审核→已下达）：自动把采购成本记入财务（借 原材料 / 贷 应付账款）
    if action == "approve" and o.status == "POSTED":
        try:
            _auto_purchase_cost_voucher(db, o)
        except Exception as _e:
            import traceback
            traceback.print_exc()
    # 跨部门通知：审核结果上大厅新闻播报
    if o.status == "PENDING":
        push_notification(db, f"采购订单 {o.po_no or o.order_no or oid} 已审核通过", "供应商已自动建档，请仓库留意到货安排", category="采购", source=o.po_no or "")
    elif o.status == "CANCELLED":
        push_notification(db, f"采购订单 {o.po_no or o.order_no or oid} 已驳回", "如需重新下单请修改后再审核", category="采购", source=o.po_no or "")
    elif o.status == "POSTED":
        push_notification(db, f"采购订单 {o.po_no or oid} 已正式下达", f"采购成本 ¥{float(o.total_amount or 0):.2f} 已自动记入财务（应付账款），请财务关注", category="财务", source=o.po_no or "")
    return make_response(True, {"id": o.id, "status": o.status})


def _auto_purchase_cost_voucher(db, o):
    """采购订单正式下达 → 自动生成已过账记账凭证：借 1402在途物资 / 贷 2202应付账款。
    （货未到先入"在途物资"，待质检入库时再由 _auto_inbound_voucher 转入"原材料"。）
    幂等：同一采购订单（reference_doc=po_no, reference_type=PURCHASE_ORDER）只记一次。"""
    amount = float(o.total_amount or 0)
    if amount <= 0:
        return  # 无金额（如未填单价）不记账
    po_ref = o.po_no or f"PO-{o.id}"
    exists = db.query(models.VoucherDB).filter(
        models.VoucherDB.reference_type == "PURCHASE_ORDER",
        models.VoucherDB.reference_doc == po_ref
    ).first()
    if exists:
        return
    asid = o.account_set_id or 1

    def _subj(code, default_name):
        s = db.query(models.AccountingSubject).filter(
            models.AccountingSubject.account_set_id == asid,
            models.AccountingSubject.code == code).first()
        return (s.code, s.name) if s else (code, default_name)

    transit_code, transit_name = _subj("1402", "在途物资")
    pay_code, pay_name = _subj("2202", "应付账款")
    today = datetime.date.today()
    # 凭证号：CG-YYYYMMDD-短uuid，保证唯一
    import uuid
    vno = f"CG-{today.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    vdb = models.VoucherDB(
        account_set_id=asid,
        voucher_no=vno,
        voucher_type=models.VoucherType.PURCHASE,
        voucher_date=today,
        status=models.VoucherStatus.POSTED,
        preparer="系统自动",
        poster="系统自动",
        reference_doc=po_ref,
        reference_type="PURCHASE_ORDER",
        approved_at=datetime.datetime.now(),
        posted_at=datetime.datetime.now(),
    )
    db.add(vdb)
    db.flush()
    summary = f"采购下单·货在途（{po_ref}）"
    db.add(models.VoucherEntry(
        voucher_id=vdb.id, account_code=transit_code, account_name=transit_name,
        debit=round(amount, 2), credit=0, summary=summary,
        supplier_id=o.supplier_id, project_id=o.project_id))
    db.add(models.VoucherEntry(
        voucher_id=vdb.id, account_code=pay_code, account_name=pay_name,
        debit=0, credit=round(amount, 2), summary=summary,
        supplier_id=o.supplier_id, project_id=o.project_id))
    db.commit()


def _auto_inbound_voucher(db, ib):
    """采购入库质检通过(POSTED)时，按【每笔入库单】自动生成一张已过账凭证：
      借 1401 原材料          —— 实际合格到货金额(received_qty × unit_price)
      借 6602 管理费用-物料损耗 —— 到料短缺损耗((ordered-received)×price)，进利润表；无损耗则无此条
      贷 1402 在途物资        —— 本笔采购成本转出(=合格+损耗)，冲减订单下达时的在途
    借贷自动平衡。幂等：按入库单号(reference_type=PURCHASE_INBOUND, reference_doc=inbound_no)去重。
    返回原材料入库金额。"""
    ordered = float(ib.ordered_qty or 0)
    received = float(ib.received_qty or 0)
    price = float(ib.unit_price or 0)
    if received <= 0 or price <= 0:
        return  # 无实际到货或无单价，不记账
    ref = ib.inbound_no or f"IN-{ib.id}"
    exists = db.query(models.VoucherDB).filter(
        models.VoucherDB.reference_type == "PURCHASE_INBOUND",
        models.VoucherDB.reference_doc == ref).first()
    if exists:
        return
    po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == ib.purchase_order_id).first()
    asid = ib.account_set_id or (po.account_set_id if po else 1) or 1
    project_id = po.project_id if po else None
    supplier_id = getattr(ib, "supplier_id", None) or (po.supplier_id if po else None)

    def _subj(code, default_name):
        s = db.query(models.AccountingSubject).filter(
            models.AccountingSubject.account_set_id == asid,
            models.AccountingSubject.code == code).first()
        return (s.code, s.name) if s else (code, default_name)

    raw_code, raw_name = _subj("1401", "原材料")
    transit_code, transit_name = _subj("1402", "在途物资")
    mfee_code, mfee_name = _subj("6602", "管理费用")

    in_amount = round(received * price, 2)                   # 合格入库 → 原材料
    loss_qty = round(max(ordered - received, 0), 4)          # 到料损耗数量
    loss_amount = round(loss_qty * price, 2)                 # 损耗金额
    out_amount = round(in_amount + loss_amount, 2)           # 贷在途 = 合格 + 损耗（平衡）

    today = ib.inbound_date or datetime.date.today()
    import uuid
    vno = f"RK-{today.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    vdb = models.VoucherDB(
        account_set_id=asid, voucher_no=vno,
        voucher_type=models.VoucherType.PURCHASE,
        voucher_date=today, status=models.VoucherStatus.POSTED,
        preparer="系统自动", poster="系统自动",
        reference_doc=ref, reference_type="PURCHASE_INBOUND",
        approved_at=datetime.datetime.now(), posted_at=datetime.datetime.now())
    db.add(vdb)
    db.flush()
    mat = db.query(models.Material).filter(models.Material.id == ib.material_id).first()
    mat_name = mat.name if mat else "物料"
    # 借：原材料（实际合格到货部分）
    db.add(models.VoucherEntry(
        voucher_id=vdb.id, account_code=raw_code, account_name=raw_name,
        debit=in_amount, credit=0, summary=f"采购入库 {ref}（{mat_name} 到货{received:g}）",
        supplier_id=supplier_id, project_id=project_id, material_id=ib.material_id))
    # 借：管理费用-物料损耗（短缺部分，进利润表）
    if loss_amount > 0:
        db.add(models.VoucherEntry(
            voucher_id=vdb.id, account_code=mfee_code, account_name=mfee_name,
            debit=loss_amount, credit=0, summary=f"采购到料损耗 {ref}（{mat_name} 损耗{loss_qty:g}）",
            supplier_id=supplier_id, project_id=project_id, material_id=ib.material_id))
    # 贷：在途物资（本笔采购成本转出）
    db.add(models.VoucherEntry(
        voucher_id=vdb.id, account_code=transit_code, account_name=transit_name,
        debit=0, credit=out_amount, summary=f"在途转入库 {ref}（{mat_name}）",
        supplier_id=supplier_id, project_id=project_id, material_id=ib.material_id))
    db.commit()
    # 大厅新闻播报
    try:
        if loss_amount > 0:
            push_notification(db,
                f"入库单 {ref} 已入库 ¥{in_amount:.2f}，损耗 ¥{loss_amount:.2f} 已自动记账",
                f"{mat_name} 订购{ordered:g}、到货{received:g}、损耗{loss_qty:g}；合格部分转入原材料，损耗计入管理费用（利润表）。",
                category="财务", source=ref)
        else:
            push_notification(db,
                f"入库单 {ref} 已入库 ¥{in_amount:.2f}，自动结转原材料",
                f"{mat_name} 到货{received:g}，采购成本由在途物资转入原材料（资产负债表存货）。",
                category="财务", source=ref)
    except Exception:
        pass
    return in_amount
