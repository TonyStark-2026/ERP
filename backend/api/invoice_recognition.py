from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import datetime
import re
import os

router = APIRouter()

# 发票识别结果模型
class InvoiceInfo(BaseModel):
    invoice_number: Optional[str] = None
    invoice_code: Optional[str] = None
    invoice_date: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_tax_id: Optional[str] = None
    seller_name: Optional[str] = None
    seller_tax_id: Optional[str] = None
    total_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    total_with_tax: Optional[float] = None
    items: Optional[list] = None

# 模拟发票数据（用于演示）
mock_invoices = {
    "sample1": {
        "invoice_number": "259520000000163105682",
        "invoice_code": "044032400111",
        "invoice_date": "2025-08-08",
        "buyer_name": "温泉县克鲁格营地酒店管理有限公司",
        "buyer_tax_id": "91652723MA776TTE7A",
        "seller_name": "深圳市境物家居有限公司",
        "seller_tax_id": "91440300MAE4BXGG0W",
        "total_amount": 631.81,
        "tax_amount": 6.32,
        "total_with_tax": 638.13,
        "items": [
            {"name": "*家具配件*家居摆件", "quantity": 2, "unit_price": 315.905940594059, "amount": 631.81, "tax_rate": 0.01, "tax_amount": 6.32}
        ]
    },
    "sample2": {
        "invoice_number": "123456789012345678",
        "invoice_code": "033001900111",
        "invoice_date": "2025-08-10",
        "buyer_name": "北京科技有限公司",
        "buyer_tax_id": "91110108MA01234567",
        "seller_name": "上海贸易有限公司",
        "seller_tax_id": "91310105MA76543210",
        "total_amount": 1000.00,
        "tax_amount": 130.00,
        "total_with_tax": 1130.00,
        "items": [
            {"name": "办公用品", "quantity": 10, "unit_price": 100.00, "amount": 1000.00, "tax_rate": 0.13, "tax_amount": 130.00}
        ]
    }
}

@router.post("/upload", tags=["发票识别"])
async def upload_invoice(file: UploadFile = File(...)):
    """
    上传发票 PDF 文件并识别关键信息
    
    :param file: PDF 文件
    :return: 识别的发票信息和凭证草稿
    """
    # 检查文件类型
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持 PDF 文件")
    
    # 保存上传的文件
    file_path = f"uploads/{file.filename}"
    os.makedirs("uploads", exist_ok=True)
    
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    # 模拟发票识别（实际项目中会调用 OCR 引擎）
    # 根据文件名或内容选择模拟数据
    if "sample" in file.filename.lower():
        invoice_info = mock_invoices.get("sample1")
    else:
        invoice_info = mock_invoices.get("sample1")
    
    if not invoice_info:
        # 如果没有匹配的模拟数据，尝试从文件名提取信息
        invoice_info = extract_from_filename(file.filename)
    
    # 生成凭证草稿
    voucher_draft = generate_voucher_draft(invoice_info)
    
    return {
        "success": True,
        "data": {
            "invoice_info": invoice_info,
            "voucher_draft": voucher_draft
        },
        "message": "发票识别成功"
    }

@router.post("/recognize/text", tags=["发票识别"])
async def recognize_invoice_text(text: str):
    """
    通过文本内容识别发票信息
    
    :param text: 发票文本内容（OCR 识别结果）
    :return: 识别的发票信息和凭证草稿
    """
    invoice_info = parse_invoice_text(text)
    voucher_draft = generate_voucher_draft(invoice_info)
    
    return {
        "success": True,
        "data": {
            "invoice_info": invoice_info,
            "voucher_draft": voucher_draft
        },
        "message": "发票识别成功"
    }

def extract_from_filename(filename: str) -> dict:
    """从文件名提取发票信息"""
    info = {
        "invoice_number": None,
        "invoice_code": None,
        "invoice_date": None,
        "buyer_name": None,
        "buyer_tax_id": None,
        "seller_name": None,
        "seller_tax_id": None,
        "total_amount": None,
        "tax_amount": None,
        "total_with_tax": None,
        "items": []
    }
    
    # 尝试从文件名提取日期
    date_match = re.search(r'(\d{4})[-_](\d{2})[-_](\d{2})', filename)
    if date_match:
        info["invoice_date"] = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
    
    # 尝试提取金额
    amount_match = re.search(r'(\d+(?:\.\d{2}))', filename)
    if amount_match:
        info["total_with_tax"] = float(amount_match.group(1))
    
    return info

def parse_invoice_text(text: str) -> dict:
    """解析发票文本内容"""
    info = {
        "invoice_number": None,
        "invoice_code": None,
        "invoice_date": None,
        "buyer_name": None,
        "buyer_tax_id": None,
        "seller_name": None,
        "seller_tax_id": None,
        "total_amount": None,
        "tax_amount": None,
        "total_with_tax": None,
        "items": []
    }
    
    # 匹配发票号码
    invoice_no_match = re.search(r'发票号码[号:：]\s*([\d]+)', text)
    if invoice_no_match:
        info["invoice_number"] = invoice_no_match.group(1)
    
    # 匹配发票代码
    invoice_code_match = re.search(r'发票代码[号:：]\s*([\d]+)', text)
    if invoice_code_match:
        info["invoice_code"] = invoice_code_match.group(1)
    
    # 匹配开票日期
    date_match = re.search(r'开票日期[期:：]\s*(\d{4}年\d{2}月\d{2}日)', text)
    if date_match:
        date_str = date_match.group(1)
        info["invoice_date"] = date_str.replace('年', '-').replace('月', '-').replace('日', '')
    
    # 匹配购买方名称
    buyer_match = re.search(r'购买方名称[称:：]\s*([^\n]+)', text)
    if buyer_match:
        info["buyer_name"] = buyer_match.group(1).strip()
    
    # 匹配购买方税号
    buyer_tax_match = re.search(r'购买方.*税号[号:：]\s*([A-Za-z0-9]+)', text)
    if not buyer_tax_match:
        buyer_tax_match = re.search(r'统一社会信用代码[码:：]\s*([A-Za-z0-9]+)', text)
    if buyer_tax_match:
        info["buyer_tax_id"] = buyer_tax_match.group(1)
    
    # 匹配销售方名称
    seller_match = re.search(r'销售方名称[称:：]\s*([^\n]+)', text)
    if seller_match:
        info["seller_name"] = seller_match.group(1).strip()
    
    # 匹配销售方税号
    seller_tax_match = re.search(r'销售方.*税号[号:：]\s*([A-Za-z0-9]+)', text)
    if not seller_tax_match:
        seller_tax_match = re.search(r'销售方.*统一社会信用代码[码:：]\s*([A-Za-z0-9]+)', text)
    if seller_tax_match:
        info["seller_tax_id"] = seller_tax_match.group(1)
    
    # 匹配金额（价税合计）
    total_match = re.search(r'价税合计[计:：]\s*[（(]小写[）)]?\s*¥?\s*([\d,]+(?:\.\d{2}))', text)
    if not total_match:
        total_match = re.search(r'合计[计:：]\s*¥?\s*([\d,]+(?:\.\d{2}))', text)
    if total_match:
        info["total_with_tax"] = float(total_match.group(1).replace(',', ''))
    
    # 匹配不含税金额
    amount_match = re.search(r'金额[额:：]\s*¥?\s*([\d,]+(?:\.\d{2}))', text)
    if amount_match:
        info["total_amount"] = float(amount_match.group(1).replace(',', ''))
    
    # 匹配税额
    tax_match = re.search(r'税额[额:：]\s*¥?\s*([\d,]+(?:\.\d{2}))', text)
    if tax_match:
        info["tax_amount"] = float(tax_match.group(1).replace(',', ''))
    
    return info

def generate_voucher_draft(invoice_info: dict) -> dict:
    """根据发票信息生成凭证草稿"""
    total_amount = invoice_info.get("total_amount") or invoice_info.get("total_with_tax") or 0
    tax_amount = invoice_info.get("tax_amount") or 0
    
    # 判断是采购发票还是销售发票
    # 如果有税额，通常是采购进项发票
    if tax_amount > 0:
        return {
            "debit": {
                "科目": "库存商品",
                "金额": round(total_amount - tax_amount, 2),
                "摘要": "购买货物"
            },
            "debit_tax": {
                "科目": "应交税费-应交增值税-进项税额",
                "金额": round(tax_amount, 2),
                "摘要": "进项税额"
            },
            "credit": {
                "科目": "应付账款",
                "金额": round(total_amount, 2),
                "摘要": "应付货款"
            }
        }
    else:
        return {
            "debit": {
                "科目": "应收账款",
                "金额": round(total_amount, 2),
                "摘要": "销售货款"
            },
            "credit": {
                "科目": "主营业务收入",
                "金额": round(total_amount, 2),
                "摘要": "销售收入"
            }
        }

@router.get("/sample", tags=["发票识别"])
def get_sample_invoice():
    """获取示例发票数据（用于演示）"""
    invoice_info = mock_invoices.get("sample1")
    voucher_draft = generate_voucher_draft(invoice_info)
    
    return {
        "success": True,
        "data": {
            "invoice_info": invoice_info,
            "voucher_draft": voucher_draft
        },
        "message": "获取示例发票成功"
    }

@router.get("/fields", tags=["发票识别"])
def get_recognizable_fields():
    """获取可识别的发票字段列表"""
    return {
        "success": True,
        "data": [
            {"field": "invoice_number", "name": "发票号码", "description": "发票上的唯一编号"},
            {"field": "invoice_code", "name": "发票代码", "description": "发票分类代码"},
            {"field": "invoice_date", "name": "开票日期", "description": "发票开具日期"},
            {"field": "buyer_name", "name": "购买方名称", "description": "购买方企业名称"},
            {"field": "buyer_tax_id", "name": "购买方税号", "description": "购买方统一社会信用代码"},
            {"field": "seller_name", "name": "销售方名称", "description": "销售方企业名称"},
            {"field": "seller_tax_id", "name": "销售方税号", "description": "销售方统一社会信用代码"},
            {"field": "total_amount", "name": "不含税金额", "description": "商品不含税总价"},
            {"field": "tax_amount", "name": "税额", "description": "增值税税额"},
            {"field": "total_with_tax", "name": "价税合计", "description": "含税总金额"},
            {"field": "items", "name": "商品明细", "description": "商品项目列表"}
        ],
        "message": "获取字段列表成功"
    }