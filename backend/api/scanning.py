from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime

from .. import crud, schemas, models
from ..database import get_db
from ..utils.algorithms import allocate_cost

router = APIRouter()

# 单据类型枚举
class DocumentType:
    SALES_ORDER = "sales_order"
    PURCHASE_ORDER = "purchase_order"
    CONTRACT = "contract"
    INVOICE = "invoice"
    RECEIPT = "receipt"
    PAYMENT = "payment"

# 根据单据类型获取对应的会计科目
def get_account_subject(doc_type: str, amount: float = 0):
    """根据单据类型自动判断借贷方科目"""
    subjects = {
        DocumentType.SALES_ORDER: {
            "debit": {"科目": "应收账款", "金额": amount, "摘要": "销售货款"},
            "credit": {"科目": "主营业务收入", "金额": amount, "摘要": "销售收入"}
        },
        DocumentType.PURCHASE_ORDER: {
            "debit": {"科目": "库存商品", "金额": amount, "摘要": "购买库存商品"},
            "credit": {"科目": "应付账款", "金额": amount, "摘要": "应付货款"}
        },
        DocumentType.CONTRACT: {
            "debit": {"科目": "应收账款", "金额": amount, "摘要": "合同应收款"},
            "credit": {"科目": "预收账款", "金额": amount, "摘要": "预收定金"}
        },
        DocumentType.INVOICE: {
            "debit": {"科目": "应交税费-进项税额", "金额": amount * 0.13, "摘要": "进项税额"},
            "credit": {"科目": "应付账款", "金额": amount, "摘要": "应付货款"}
        },
        DocumentType.RECEIPT: {
            "debit": {"科目": "银行存款", "金额": amount, "摘要": "收到货款"},
            "credit": {"科目": "应收账款", "金额": amount, "摘要": "收回货款"}
        },
        DocumentType.PAYMENT: {
            "debit": {"科目": "应付账款", "金额": amount, "摘要": "支付货款"},
            "credit": {"科目": "银行存款", "金额": amount, "摘要": "银行付款"}
        }
    }
    return subjects.get(doc_type, {})

@router.post("/scan", tags=["扫码录入"])
def scan_document(
    barcode: str,
    db: Session = Depends(get_db)
):
    """
    扫描单据条码/二维码，获取单据信息并生成凭证草稿
    
    :param barcode: 扫描到的单据编号
    :return: 单据信息和凭证草稿
    """
    # 尝试从不同表中查找单据
    document = None
    doc_type = None
    
    # 1. 查找采购订单
    purchase_order = crud.get_purchase_order_by_po_no(db, barcode)
    if purchase_order:
        document = purchase_order
        doc_type = DocumentType.PURCHASE_ORDER
    
    # 2. 查找生产工单
    if not document:
        work_order = crud.get_production_workorder_by_no(db, barcode)
        if work_order:
            document = work_order
            doc_type = DocumentType.SALES_ORDER
    
    # 3. 如果都找不到，尝试作为普通单据号查找
    if not document:
        # 检查是否为发票二维码格式 (QR_CODE_XXX)
        if barcode.startswith("QR_"):
            doc_type = DocumentType.INVOICE
            document = {
                "id": 0,
                "document_no": barcode,
                "amount": 0,
                "description": "发票扫描",
                "created_at": datetime.datetime.now()
            }
        else:
            raise HTTPException(status_code=404, detail=f"未找到单据: {barcode}")
    
    # 构建响应数据
    result = {
        "document_no": barcode,
        "document_type": doc_type,
        "document_info": {},
        "voucher_draft": {}
    }
    
    # 根据单据类型提取信息
    if doc_type == DocumentType.PURCHASE_ORDER and purchase_order:
        material = crud.get_material(db, purchase_order.material_id)
        result["document_info"] = {
            "单据编号": purchase_order.po_no,
            "物料名称": material.name if material else "未知",
            "供应商": crud.get_supplier(db, purchase_order.supplier_id).name if purchase_order.supplier_id else "未知",
            "数量": purchase_order.quantity,
            "单价": purchase_order.unit_price,
            "税率": purchase_order.tax_rate,
            "总金额": purchase_order.quantity * purchase_order.unit_price,
            "创建时间": purchase_order.created_at.isoformat() if purchase_order.created_at else None
        }
        amount = purchase_order.quantity * purchase_order.unit_price
        result["voucher_draft"] = get_account_subject(doc_type, amount)
    
    elif doc_type == DocumentType.SALES_ORDER and work_order:
        product = crud.get_material(db, work_order.product_id)
        result["document_info"] = {
            "工单号": work_order.work_order_no,
            "产品名称": product.name if product else "未知",
            "计划数量": work_order.planned_qty,
            "完成数量": work_order.completed_qty,
            "状态": work_order.status.value if hasattr(work_order.status, 'value') else work_order.status,
            "开始日期": work_order.start_date.isoformat() if work_order.start_date else None,
            "创建时间": work_order.created_at.isoformat() if work_order.created_at else None
        }
        amount = work_order.completed_qty * (product.unit_price if product else 0)
        result["voucher_draft"] = get_account_subject(doc_type, amount)
    
    elif doc_type == DocumentType.INVOICE:
        result["document_info"] = {
            "发票编号": barcode,
            "描述": "待识别发票",
            "扫描时间": datetime.datetime.now().isoformat()
        }
        result["voucher_draft"] = get_account_subject(doc_type, 0)
    
    return {"success": True, "data": result, "message": "扫描成功"}

@router.post("/scan/batch", tags=["扫码录入"])
def scan_batch_documents(
    barcodes: List[str],
    db: Session = Depends(get_db)
):
    """
    批量扫描多个单据条码，生成凭证汇总表
    
    :param barcodes: 扫描到的单据编号列表
    :return: 所有单据信息和汇总凭证
    """
    results = []
    total_debit = 0
    total_credit = 0
    
    for barcode in barcodes:
        try:
            result = scan_document(barcode, db)
            results.append(result["data"])
            if result["data"]["voucher_draft"]:
                debit = result["data"]["voucher_draft"].get("debit", {}).get("金额", 0)
                credit = result["data"]["voucher_draft"].get("credit", {}).get("金额", 0)
                total_debit += debit
                total_credit += credit
        except HTTPException as e:
            results.append({
                "document_no": barcode,
                "error": e.detail,
                "success": False
            })
    
    summary = {
        "扫描单据总数": len(barcodes),
        "成功识别": len([r for r in results if r.get("success", True)]),
        "失败": len([r for r in results if not r.get("success", True)]),
        "借方合计": round(total_debit, 2),
        "贷方合计": round(total_credit, 2),
        "平衡检查": "平衡" if abs(total_debit - total_credit) < 0.01 else "不平衡"
    }
    
    return {
        "success": True,
        "data": {
            "documents": results,
            "summary": summary
        },
        "message": "批量扫描完成"
    }

@router.post("/voucher/generate", tags=["扫码录入"])
def generate_voucher(
    document_no: str,
    db: Session = Depends(get_db)
):
    """
    根据单据编号生成正式凭证
    
    :param document_no: 单据编号
    :return: 生成的凭证信息
    """
    # 先扫描获取单据信息
    scan_result = scan_document(document_no, db)
    document_data = scan_result["data"]
    
    # 创建凭证记录
    voucher_data = {
        "document_no": document_data["document_no"],
        "document_type": document_data["document_type"],
        "debit_subject": document_data["voucher_draft"].get("debit", {}).get("科目", ""),
        "debit_amount": document_data["voucher_draft"].get("debit", {}).get("金额", 0),
        "credit_subject": document_data["voucher_draft"].get("credit", {}).get("科目", ""),
        "credit_amount": document_data["voucher_draft"].get("credit", {}).get("金额", 0),
        "status": "draft",
        "created_at": datetime.datetime.now()
    }
    
    return {
        "success": True,
        "data": voucher_data,
        "message": "凭证生成成功"
    }

@router.post("/voucher/batch-generate", tags=["扫码录入"])
def batch_generate_vouchers(
    barcodes: List[str],
    db: Session = Depends(get_db)
):
    """
    批量生成凭证
    
    :param barcodes: 单据编号列表
    :return: 生成的凭证列表和汇总
    """
    vouchers = []
    total_debit = 0
    total_credit = 0
    
    for barcode in barcodes:
        try:
            result = generate_voucher(barcode, db)
            vouchers.append(result["data"])
            total_debit += result["data"]["debit_amount"]
            total_credit += result["data"]["credit_amount"]
        except HTTPException as e:
            vouchers.append({
                "document_no": barcode,
                "error": e.detail
            })
    
    summary = {
        "单据总数": len(barcodes),
        "成功生成凭证": len([v for v in vouchers if not v.get("error")]),
        "失败": len([v for v in vouchers if v.get("error")]),
        "借方合计": round(total_debit, 2),
        "贷方合计": round(total_credit, 2),
        "平衡检查": "平衡" if abs(total_debit - total_credit) < 0.01 else "不平衡"
    }
    
    return {
        "success": True,
        "data": {
            "vouchers": vouchers,
            "summary": summary
        },
        "message": "批量凭证生成完成"
    }

@router.get("/document/types", tags=["扫码录入"])
def get_document_types():
    """获取支持的单据类型列表"""
    return {
        "success": True,
        "data": [
            {"type": "purchase_order", "name": "采购订单", "description": "采购入库单据"},
            {"type": "sales_order", "name": "销售订单", "description": "销售出库单据"},
            {"type": "contract", "name": "合同", "description": "销售/采购合同"},
            {"type": "invoice", "name": "发票", "description": "增值税发票"},
            {"type": "receipt", "name": "收款单", "description": "银行收款回单"},
            {"type": "payment", "name": "付款单", "description": "银行付款回单"}
        ],
        "message": "获取成功"
    }