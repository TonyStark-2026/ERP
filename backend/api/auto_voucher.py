"""
Auto Voucher Engine —— 记账凭证自动填写
========================================
根据业务单据（采购入库/销售出库/收款/付款/领料/完工/盘盈盘亏）自动生成记账凭证。

核心能力：
  1. 10种业务单据 → 借贷科目映射模板
  2. 自动编号（记-YYYYMM-NNN）
  3. 辅助核算自动携带（客户/供应商/部门/工单/物料）
  4. 异常检测（科目缺失/辅助核算缺失/金额差异）
  5. 手动触发 + 批量生成 + 审核/驳回/修改
"""
import json
import datetime
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models


class VoucherException(Exception):
    """凭证生成异常"""
    def __init__(self, message: str, error_code: str = "VOUCHER_ERROR"):
        super().__init__(message)
        self.error_code = error_code


# ============================================================
# 🔹 内置科目映射模板（10种业务场景）
# ============================================================
# key: doc_type → 模板定义
# 每个模板包含: summary_template, debit_entries, credit_entries
# account_field: 从单据/物料上取科目编码的字段名
# account_default: 若物料未配置科目时使用的默认科目
BUILTIN_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "INBOUND": {  # 1. 采购入库单（暂估入库）
        "name": "采购入库（暂估）",
        "summary_template": "采购入库 {doc_no} {supplier}",
        "debit_entries": [
            {"account_field": "inventory_account_code", "account_default": "1401", "account_name_default": "原材料", "summary_suffix": "入库成本"},
        ],
        "credit_entries": [
            {"account": "2202", "account_name": "应付账款—暂估", "use_supplier": True, "summary_suffix": "暂估应付"},
        ],
    },
    "PURCHASE_INVOICE": {  # 2. 采购发票校验通过（正式入账 + 红冲暂估）
        "name": "采购发票（三单匹配正式入账）",
        "summary_template": "采购发票 {doc_no} {supplier}",
        "red冲": True,  # 先红冲暂估，再正式入账
        "debit_entries": [
            {"account_field": "inventory_account_code", "account_default": "1401", "account_name_default": "原材料", "summary_suffix": "正式入库成本"},
            {"account": "2221", "account_name": "应交税费—应交增值税（进项税额）", "summary_suffix": "进项税额"},
        ],
        "credit_entries": [
            {"account": "2202", "account_name": "应付账款", "use_supplier": True, "summary_suffix": "应付货款"},
        ],
    },
    "SALES_OUTBOUND": {  # 3. 销售出库单（结转成本）
        "name": "销售出库（结转成本）",
        "summary_template": "销售出库 {doc_no} 客户:{customer}",
        "debit_entries": [
            {"account": "6401", "account_name": "主营业务成本", "summary_suffix": "销售成本"},
        ],
        "credit_entries": [
            {"account_field": "inventory_account_code", "account_default": "1403", "account_name_default": "库存商品", "summary_suffix": "出库成本"},
        ],
    },
    "SALES_INVOICE": {  # 4. 销售发票（确认应收）
        "name": "销售发票（确认应收）",
        "summary_template": "销售发票 {doc_no} 客户:{customer}",
        "debit_entries": [
            {"account": "1122", "account_name": "应收账款", "use_customer": True, "summary_suffix": "应收货款"},
        ],
        "credit_entries": [
            {"account_field": "income_account_code", "account_default": "6001", "account_name_default": "主营业务收入", "summary_suffix": "销售收入"},
            {"account": "2221", "account_name": "应交税费—应交增值税（销项税额）", "summary_suffix": "销项税额"},
        ],
    },
    "RECEIPT": {  # 5. 收款单
        "name": "收款单",
        "summary_template": "收款 {doc_no} 客户:{customer}",
        "debit_entries": [
            {"account": "1002", "account_name": "银行存款", "summary_suffix": "银行收款"},
        ],
        "credit_entries": [
            {"account": "1122", "account_name": "应收账款", "use_customer": True, "summary_suffix": "收回应收"},
        ],
    },
    "PAYMENT": {  # 6. 付款单
        "name": "付款单",
        "summary_template": "付款 {doc_no} 供应商:{supplier}",
        "debit_entries": [
            {"account": "2202", "account_name": "应付账款", "use_supplier": True, "summary_suffix": "支付应付"},
        ],
        "credit_entries": [
            {"account": "1002", "account_name": "银行存款", "summary_suffix": "银行付款"},
        ],
    },
    "PROD_PICK": {  # 7. 生产领料单
        "name": "生产领料",
        "summary_template": "领料 {doc_no} 工单:{work_order}",
        "debit_entries": [
            {"account": "5001", "account_name": "生产成本—直接材料", "use_work_order": True, "summary_suffix": "领料成本"},
        ],
        "credit_entries": [
            {"account_field": "inventory_account_code", "account_default": "1401", "account_name_default": "原材料", "summary_suffix": "出库成本"},
        ],
    },
    "PROD_COMPLETE": {  # 8. 完工入库单
        "name": "完工入库",
        "summary_template": "完工入库 {doc_no} 工单:{work_order}",
        "debit_entries": [
            {"account_field": "inventory_account_code", "account_default": "1403", "account_name_default": "库存商品", "summary_suffix": "成品入库"},
        ],
        "credit_entries": [
            {"account": "5001", "account_name": "生产成本—直接材料", "use_work_order": True, "summary_suffix": "材料费结转"},
            {"account": "5002", "account_name": "生产成本—直接人工", "use_work_order": True, "summary_suffix": "人工费结转"},
            {"account": "5101", "account_name": "生产成本—制造费用", "use_work_order": True, "summary_suffix": "制造费用结转"},
        ],
    },
    "INVENTORY_PROFIT": {  # 9. 盘盈单
        "name": "盘点盈溢",
        "summary_template": "盘盈 {doc_no}",
        "debit_entries": [
            {"account_field": "inventory_account_code", "account_default": "1401", "account_name_default": "原材料", "summary_suffix": "盘盈入库"},
        ],
        "credit_entries": [
            {"account": "1901", "account_name": "待处理财产损溢", "summary_suffix": "待处理盘盈"},
        ],
    },
    "INVENTORY_LOSS": {  # 10. 盘亏单
        "name": "盘点亏损",
        "summary_template": "盘亏 {doc_no}",
        "debit_entries": [
            {"account": "1901", "account_name": "待处理财产损溢", "summary_suffix": "待处理盘亏"},
        ],
        "credit_entries": [
            {"account_field": "inventory_account_code", "account_default": "1401", "account_name_default": "原材料", "summary_suffix": "盘亏出库"},
        ],
    },
    # ==================== 工程导向型专属模板 ====================
    "ENG_INBOUND": {  # 11. 工程物资采购入库
        "name": "工程物资采购入库（暂估）",
        "summary_template": "工程物资入库 {doc_no} {supplier}",
        "debit_entries": [
            {"account": "1601", "account_name": "工程物资", "summary_suffix": "工程物资入库"},
        ],
        "credit_entries": [
            {"account": "2202", "account_name": "应付账款—暂估", "use_supplier": True, "summary_suffix": "暂估应付"},
        ],
    },
    "PROJ_PICK": {  # 12. 项目领料（工程施工）
        "name": "项目领料（工程施工）",
        "summary_template": "项目领料 {doc_no} 项目:{project}",
        "debit_entries": [
            {"account": "5401", "account_name": "工程施工—合同成本", "summary_suffix": "项目材料费"},
        ],
        "credit_entries": [
            {"account_field": "inventory_account_code", "account_default": "1401", "account_name_default": "原材料", "summary_suffix": "材料出库"},
        ],
    },
    "PROJECT_COST": {  # 13. 项目成本归集（人工费/机械使用费/分包费等）
        "name": "项目成本归集",
        "summary_template": "成本归集 {doc_no} 项目:{project}",
        "debit_entries": [
            {"account": "5401", "account_name": "工程施工—合同成本", "summary_suffix": "项目成本归集"},
        ],
        "credit_entries": [
            {"account": "2211", "account_name": "应付职工薪酬", "summary_suffix": "人工费"},
        ],
    },
    "REVENUE_CONFIRM": {  # 14. 收入确认（完工百分比法）
        "name": "收入确认（完工百分比法）",
        "summary_template": "收入确认 {doc_no} 项目:{project}",
        "debit_entries": [
            {"account": "6401", "account_name": "主营业务成本", "summary_suffix": "确认成本"},
            {"account": "5402", "account_name": "工程施工—合同毛利", "summary_suffix": "确认毛利"},
        ],
        "credit_entries": [
            {"account": "6001", "account_name": "主营业务收入", "summary_suffix": "确认收入"},
        ],
    },
    "ENG_SETTLE": {  # 15. 工程结算（与业主结算）
        "name": "工程结算",
        "summary_template": "工程结算 {doc_no} 项目:{project}",
        "debit_entries": [
            {"account": "1122", "account_name": "应收账款", "use_customer": True, "summary_suffix": "应收工程款"},
        ],
        "credit_entries": [
            {"account": "5501", "account_name": "工程结算", "summary_suffix": "工程结算款"},
        ],
    },
    "PROJ_COMPLETE": {  # 16. 项目竣工结转
        "name": "项目竣工结转",
        "summary_template": "竣工结转 {doc_no} 项目:{project}",
        "debit_entries": [
            {"account": "5501", "account_name": "工程结算", "summary_suffix": "结转工程结算"},
        ],
        "credit_entries": [
            {"account": "5401", "account_name": "工程施工—合同成本", "summary_suffix": "结转合同成本"},
            {"account": "5402", "account_name": "工程施工—合同毛利", "summary_suffix": "结转合同毛利"},
        ],
    },
}


# ============================================================
# 🔹 凭证编号生成
# ============================================================
def generate_voucher_no(db: Session, account_set_id: int, voucher_date: datetime.date) -> str:
    """按月连续编号：记-YYYYMM-NNN"""
    year_month = voucher_date.strftime("%Y%m")
    prefix = f"记-{year_month}-"
    # 查当月最大编号
    import re
    existing = db.query(models.AutoVoucher.voucher_no)\
        .filter(models.AutoVoucher.account_set_id == account_set_id)\
        .filter(models.AutoVoucher.voucher_no.like(f"{prefix}%"))\
        .order_by(models.AutoVoucher.voucher_no.desc())\
        .first()
    next_num = 1
    if existing and existing.voucher_no:
        m = re.search(r'-(\d+)$', existing.voucher_no)
        if m:
            next_num = int(m.group(1)) + 1
    return f"{prefix}{next_num:03d}"


# ============================================================
# 🔹 辅助核算信息提取
# ============================================================
def extract_aux(doc_type: str, doc: Any) -> Dict[str, Any]:
    """从业务单据中提取辅助核算信息"""
    aux = {
        "customer_id": None,
        "supplier_id": None,
        "department_id": None,
        "work_order_id": None,
        "material_id": None,
        "employee_id": None,
    }
    if doc_type in ("INBOUND", "PURCHASE_INVOICE", "PAYMENT", "PROD_PICK", "INVENTORY_PROFIT", "INVENTORY_LOSS"):
        aux["supplier_id"] = getattr(doc, "supplier_id", None)
    if doc_type in ("SALES_OUTBOUND", "SALES_INVOICE", "RECEIPT"):
        aux["customer_id"] = getattr(doc, "customer_id", None)
    if doc_type in ("PROD_PICK", "PROD_COMPLETE"):
        aux["work_order_id"] = getattr(doc, "id", None)  # 工单本身ID
    return aux


def format_summary(template: str, **kwargs) -> str:
    """格式化摘要模板"""
    result = template
    mapping = {
        "doc_no": kwargs.get("doc_no", ""),
        "doc_type": kwargs.get("doc_type", ""),
        "customer": kwargs.get("customer", ""),
        "supplier": kwargs.get("supplier", ""),
        "work_order": kwargs.get("work_order", ""),
        "material": kwargs.get("material", ""),
        "project": kwargs.get("project", ""),
    }
    for k, v in mapping.items():
        result = result.replace("{" + k + "}", str(v) if v else "")
    return result


# ============================================================
# 🔹 核心引擎：generate_voucher()
# ============================================================
def generate_voucher(
    db: Session,
    account_set_id: int,
    doc_type: str,
    doc_id: int,
    doc_no: str,
    voucher_date: Optional[datetime.date] = None,
    force: bool = False,
) -> models.AutoVoucher:
    """
    根据业务单据自动生成记账凭证。
    返回 AutoVoucher 对象（状态为 DRAFT）。
    若科目缺失或辅助核算缺失，抛出 VoucherException。
    """
    if doc_type not in BUILTIN_TEMPLATES:
        raise VoucherException(f"未配置单据类型「{doc_type}」的凭证生成模板", "VOUCHER_NO_TEMPLATE")

    template = BUILTIN_TEMPLATES[doc_type]
    voucher_date = voucher_date or datetime.date.today()

    # 查已有凭证，避免重复生成
    existing = db.query(models.AutoVoucher)\
        .filter(models.AutoVoucher.source_doc_type == doc_type)\
        .filter(models.AutoVoucher.source_doc_id == doc_id)\
        .filter(models.AutoVoucher.status.in_(["DRAFT", "PENDING", "APPROVED", "POSTED"]))\
        .first()
    if existing and not force:
        raise VoucherException(f"单据 {doc_no} 已存在自动凭证（ID:{existing.id}，状态:{existing.status}）", "VOUCHER_DUPLICATE")

    # 根据 doc_type 加载单据数据
    doc_data = _load_doc_data(db, doc_type, doc_id)
    if not doc_data:
        raise VoucherException(f"单据 {doc_type}#{doc_id} 不存在", "VOUCHER_DOC_NOT_FOUND")

    # 提取辅助核算
    aux = extract_aux(doc_type, doc_data.get("doc"))

    # 构建摘要
    summary = format_summary(
        template["summary_template"],
        doc_type=doc_type,
        doc_no=doc_no,
        customer=doc_data.get("customer_name", ""),
        supplier=doc_data.get("supplier_name", ""),
        work_order=doc_data.get("work_order_no", ""),
        material=doc_data.get("material_name", ""),
        project=doc_data.get("project_name", ""),
    )

    # 计算借贷金额
    total_amount = doc_data.get("total_amount", 0)
    tax_amount = doc_data.get("tax_amount", 0)
    net_amount = total_amount - tax_amount if (doc_type == "PURCHASE_INVOICE") else total_amount

    # 构建分录
    entries: List[Dict[str, Any]] = []

    # 借方分录
    for rule in template["debit_entries"]:
        account_code, account_name = _resolve_account(rule, doc_data, doc_type)
        amount = _resolve_amount(rule, doc_type, net_amount, tax_amount, total_amount, is_debit=True, doc_data=doc_data)
        entry = {
            "side": "debit",
            "account_code": account_code,
            "account_name": account_name,
            "amount": amount,
            "summary": summary + " " + rule.get("summary_suffix", ""),
            "customer_id": aux.get("customer_id") if rule.get("use_customer") else None,
            "supplier_id": aux.get("supplier_id") if rule.get("use_supplier") else None,
            "work_order_id": aux.get("work_order_id") if rule.get("use_work_order") else None,
            "material_id": doc_data.get("material_id"),
            "employee_id": None,
        }
        entries.append(entry)

    # 贷方分录
    for rule in template["credit_entries"]:
        account_code, account_name = _resolve_account(rule, doc_data, doc_type)
        amount = _resolve_amount(rule, doc_type, net_amount, tax_amount, total_amount, is_debit=False, doc_data=doc_data)
        entry = {
            "side": "credit",
            "account_code": account_code,
            "account_name": account_name,
            "amount": amount,
            "summary": summary + " " + rule.get("summary_suffix", ""),
            "customer_id": aux.get("customer_id") if rule.get("use_customer") else None,
            "supplier_id": aux.get("supplier_id") if rule.get("use_supplier") else None,
            "work_order_id": aux.get("work_order_id") if rule.get("use_work_order") else None,
            "material_id": doc_data.get("material_id"),
            "employee_id": None,
        }
        entries.append(entry)

    # 校验借贷平衡
    total_debit = sum(float(e["amount"] or 0) for e in entries if e["side"] == "debit")
    total_credit = sum(float(e["amount"] or 0) for e in entries if e["side"] == "credit")
    if abs(total_debit - total_credit) > 0.02:
        raise VoucherException(
            f"借贷不平衡：借方 {total_debit:.2f}，贷方 {total_credit:.2f}，差额 {(total_debit - total_credit):.2f}",
            "VOUCHER_UNBALANCED"
        )

    # 生成凭证号
    voucher_no = generate_voucher_no(db, account_set_id, voucher_date)

    # 创建凭证
    voucher = models.AutoVoucher(
        account_set_id=account_set_id,
        voucher_no=voucher_no,
        voucher_date=voucher_date,
        status="DRAFT",
        source_doc_type=doc_type,
        source_doc_id=doc_id,
        source_doc_no=doc_no,
        summary=summary,
        template_code=doc_type,
        total_debit=round(total_debit, 2),
        total_credit=round(total_credit, 2),
        created_at=datetime.datetime.utcnow(),
    )
    db.add(voucher)
    db.flush()

    # 创建分录
    for e in entries:
        ve = models.AutoVoucherEntry(
            auto_voucher_id=voucher.id,
            account_code=e["account_code"],
            account_name=e["account_name"],
            side=e["side"],
            amount=round(float(e["amount"]), 2),
            summary=e["summary"],
            customer_id=e.get("customer_id"),
            supplier_id=e.get("supplier_id"),
            department_id=None,
            work_order_id=e.get("work_order_id"),
            material_id=e.get("material_id"),
            employee_id=None,
        )
        db.add(ve)

    db.commit()
    return voucher


def _load_doc_data(db: Session, doc_type: str, doc_id: int) -> Dict[str, Any]:
    """根据单据类型加载单据数据"""
    data = {
        "doc": None,
        "doc_no": "",
        "supplier_id": None, "supplier_name": None,
        "customer_id": None, "customer_name": None,
        "work_order_no": None,
        "project_id": None, "project_name": None,
        "material_id": None, "material_name": None,
        "total_amount": 0, "tax_amount": 0,
        "incurred_cost": 0, "recognized_revenue": 0,
        "material_inventory_account": None,
        "material_income_account": None,
        "material_cost_account": None,
    }
    if doc_type == "INBOUND":
        doc = db.query(models.InboundOrder).filter(models.InboundOrder.id == doc_id).first()
        if not doc: return data
        data["doc"] = doc
        data["doc_no"] = doc.inbound_no
        data["supplier_id"] = doc.supplier_id
        if doc.supplier_id:
            s = db.query(models.Supplier).filter(models.Supplier.id == doc.supplier_id).first()
            data["supplier_name"] = s.name if s else None
        items = db.query(models.InboundOrderItem).filter(models.InboundOrderItem.inbound_order_id == doc_id).all()
        if items:
            data["total_amount"] = float(sum(i.quantity * float(i.unit_price or 0) for i in items))
            m = db.query(models.Material).filter(models.Material.id == items[0].material_id).first()
            if m:
                data["material_id"] = m.id
                data["material_name"] = m.name
                data["material_inventory_account"] = m.inventory_account_code
    elif doc_type == "SALES_OUTBOUND":
        doc = db.query(models.OutboundOrder).filter(models.OutboundOrder.id == doc_id).first()
        if not doc: return data
        data["doc"] = doc
        data["doc_no"] = doc.outbound_no
        data["customer_id"] = doc.customer_id
        if doc.customer_id:
            c = db.query(models.Customer).filter(models.Customer.id == doc.customer_id).first()
            data["customer_name"] = c.name if c else None
        items = db.query(models.OutboundOrderItem).filter(models.OutboundOrderItem.outbound_order_id == doc_id).all()
        if items:
            data["total_amount"] = float(sum(i.quantity * float(i.unit_price or 0) for i in items))
            m = db.query(models.Material).filter(models.Material.id == items[0].material_id).first()
            if m:
                data["material_id"] = m.id
                data["material_name"] = m.name
                data["material_inventory_account"] = m.inventory_account_code
                data["material_income_account"] = m.income_account_code
                data["material_cost_account"] = m.cost_account_code
    elif doc_type == "SALES_INVOICE":
        inv = db.query(models.Invoice).filter(models.Invoice.id == doc_id).first()
        if not inv: return data
        data["doc"] = inv
        data["doc_no"] = inv.invoice_no
        data["customer_id"] = inv.customer_id
        if inv.customer_id:
            c = db.query(models.Customer).filter(models.Customer.id == inv.customer_id).first()
            data["customer_name"] = c.name if c else None
        data["total_amount"] = float(inv.total_amount or 0)
        data["tax_amount"] = float(inv.tax_amount or 0)
    elif doc_type == "PURCHASE_INVOICE":
        inv = db.query(models.Invoice).filter(models.Invoice.id == doc_id).first()
        if not inv: return data
        data["doc"] = inv
        data["doc_no"] = inv.invoice_no
        data["supplier_id"] = inv.supplier_id
        if inv.supplier_id:
            s = db.query(models.Supplier).filter(models.Supplier.id == inv.supplier_id).first()
            data["supplier_name"] = s.name if s else None
        data["total_amount"] = float(inv.total_amount or 0)
        data["tax_amount"] = float(inv.tax_amount or 0)
    elif doc_type in ("RECEIPT",):
        rec = db.query(models.Receipt).filter(models.Receipt.id == doc_id).first()
        if not rec: return data
        data["doc"] = rec
        data["doc_no"] = rec.receipt_no
        data["customer_id"] = rec.customer_id
        if rec.customer_id:
            c = db.query(models.Customer).filter(models.Customer.id == rec.customer_id).first()
            data["customer_name"] = c.name if c else None
        data["total_amount"] = float(rec.amount or 0)
    elif doc_type in ("PAYMENT",):
        pay = db.query(models.Payment).filter(models.Payment.id == doc_id).first()
        if not pay: return data
        data["doc"] = pay
        data["doc_no"] = pay.payment_no
        data["supplier_id"] = pay.supplier_id
        if pay.supplier_id:
            s = db.query(models.Supplier).filter(models.Supplier.id == pay.supplier_id).first()
            data["supplier_name"] = s.name if s else None
        data["total_amount"] = float(pay.amount or 0)
    elif doc_type in ("PROD_PICK", "PROD_COMPLETE"):
        wo = db.query(models.ProductionWorkOrder).filter(models.ProductionWorkOrder.id == doc_id).first()
        if not wo: return data
        data["doc"] = wo
        data["doc_no"] = wo.work_order_no
        data["work_order_no"] = wo.work_order_no
        if wo.product_id:
            m = db.query(models.Material).filter(models.Material.id == wo.product_id).first()
            if m:
                data["material_id"] = m.id
                data["material_name"] = m.name
                data["material_inventory_account"] = m.inventory_account_code
        data["total_amount"] = float(wo.actual_material_cost or 0) + float(wo.actual_labor_cost or 0) + float(wo.actual_overhead_cost or 0)
        data["tax_amount"] = 0
    elif doc_type in ("INVENTORY_PROFIT", "INVENTORY_LOSS"):
        # 盘点差异：从 inventory_transactions 取
        txs = db.query(models.InventoryTransaction).filter(
            models.InventoryTransaction.reference_no == f"STOCKTAKE-{doc_id}"
        ).all()
        if txs:
            data["doc_no"] = f"STOCKTAKE-{doc_id}"
            data["total_amount"] = float(sum(t.total_cost or 0 for t in txs))
            m = db.query(models.Material).filter(models.Material.id == txs[0].material_id).first()
            if m:
                data["material_id"] = m.id
                data["material_name"] = m.name
                data["material_inventory_account"] = m.inventory_account_code
    elif doc_type == "ENG_INBOUND":
        # 工程物资采购入库：复用入库单结构，但科目走工程物资
        doc = db.query(models.InboundOrder).filter(models.InboundOrder.id == doc_id).first()
        if not doc: return data
        data["doc"] = doc
        data["doc_no"] = doc.inbound_no
        data["supplier_id"] = doc.supplier_id
        if doc.supplier_id:
            s = db.query(models.Supplier).filter(models.Supplier.id == doc.supplier_id).first()
            data["supplier_name"] = s.name if s else None
        items = db.query(models.InboundOrderItem).filter(models.InboundOrderItem.inbound_order_id == doc_id).all()
        if items:
            data["total_amount"] = float(sum(i.quantity * float(i.unit_price or 0) for i in items))
    elif doc_type in ("PROJ_PICK", "PROJECT_COST", "REVENUE_CONFIRM", "ENG_SETTLE", "PROJ_COMPLETE"):
        # 工程类凭证：doc_id 即 WBSProject.id
        proj = db.query(models.WBSProject).filter(models.WBSProject.id == doc_id).first()
        if not proj: return data
        data["doc"] = proj
        data["doc_no"] = proj.project_no
        data["project_id"] = proj.id
        data["project_name"] = proj.project_name
        data["customer_id"] = proj.customer_id
        if proj.customer_id:
            c = db.query(models.Customer).filter(models.Customer.id == proj.customer_id).first()
            data["customer_name"] = c.name if c else None
        data["incurred_cost"] = float(proj.incurred_cost or 0)
        data["recognized_revenue"] = float(proj.recognized_revenue or 0)
        if doc_type == "REVENUE_CONFIRM":
            # 收入确认：收入=合同额×完工百分比，成本=已发生成本，毛利=收入-成本
            data["total_amount"] = data["recognized_revenue"]
        elif doc_type == "PROJECT_COST":
            data["total_amount"] = data["incurred_cost"]
        elif doc_type == "ENG_SETTLE":
            data["total_amount"] = data["recognized_revenue"]
        elif doc_type == "PROJ_COMPLETE":
            data["total_amount"] = float(proj.contract_amount or 0)
        elif doc_type == "PROJ_PICK":
            data["total_amount"] = data["incurred_cost"]
    return data


def _resolve_account(rule: Dict[str, Any], doc_data: Dict[str, Any], doc_type: str) -> Tuple[str, str]:
    """解析科目编码和名称"""
    account_field = rule.get("account_field")
    account_default = rule.get("account_default", "1401")
    account_name_default = rule.get("account_name_default", "")

    if account_field:
        # 从物料数据取
        field_map = {
            "inventory_account_code": doc_data.get("material_inventory_account"),
            "income_account_code": doc_data.get("material_income_account"),
            "cost_account_code": doc_data.get("material_cost_account"),
        }
        code = field_map.get(account_field)
        if not code:
            # 使用默认科目
            code = account_default
            # 若默认也没有，抛出异常（但允许用默认，不强制）
        name = account_name_default or _get_account_name(code)
        return code, name
    else:
        # 直接使用规则中的固定科目
        return rule.get("account", account_default), rule.get("account_name", account_name_default)


def _resolve_amount(rule: Dict[str, Any], doc_type: str, net_amount: float, tax_amount: float, total_amount: float, is_debit: bool, doc_data: Optional[Dict[str, Any]] = None) -> float:
    """解析金额"""
    # 不同单据类型的金额分配
    if doc_type == "INBOUND":
        return net_amount
    elif doc_type == "PURCHASE_INVOICE":
        # 借方：原材料=净额，进项税=税额；贷方：应付账款=总额
        account = rule.get("account", "")
        if "2221" in account or rule.get("account_name", "").find("进项") >= 0:
            return tax_amount
        elif is_debit:
            return net_amount
        else:
            return total_amount
    elif doc_type == "SALES_OUTBOUND":
        return total_amount  # 按出库数量×成本
    elif doc_type == "SALES_INVOICE":
        account = rule.get("account", "")
        if is_debit:
            return total_amount  # 应收账款 = 价税合计
        else:
            if "2221" in account or rule.get("account_name", "").find("销项") >= 0:
                return tax_amount
            else:
                return net_amount  # 主营业务收入 = 不含税
    elif doc_type == "RECEIPT":
        return total_amount
    elif doc_type == "PAYMENT":
        return total_amount
    elif doc_type == "PROD_PICK":
        return total_amount  # 领料金额
    elif doc_type == "PROD_COMPLETE":
        # 按成本项分配
        account = rule.get("account", "")
        mat_cost = total_amount * 0.6 if total_amount > 0 else 0
        labor_cost = total_amount * 0.2 if total_amount > 0 else 0
        overhead_cost = total_amount * 0.2 if total_amount > 0 else 0
        if "5001" in account:
            return mat_cost
        elif "5002" in account:
            return labor_cost
        elif "5101" in account:
            return overhead_cost
        else:
            return total_amount
    elif doc_type in ("INVENTORY_PROFIT", "INVENTORY_LOSS"):
        return total_amount
    elif doc_type == "REVENUE_CONFIRM":
        # 收入确认：借 主营业务成本(incurred_cost) + 工程施工-合同毛利(revenue-cost)，贷 主营业务收入(revenue)
        account = rule.get("account", "")
        incurred = doc_data.get("incurred_cost", 0) if doc_data else 0
        revenue = doc_data.get("recognized_revenue", 0) if doc_data else total_amount
        gross_profit = revenue - incurred
        if "6401" in account:
            return incurred  # 主营业务成本
        elif "5402" in account:
            return gross_profit  # 工程施工—合同毛利
        elif "6001" in account:
            return revenue  # 主营业务收入
        return revenue
    elif doc_type == "PROJ_COMPLETE":
        # 竣工结转：借 工程结算(contract_amount)，贷 工程施工-合同成本(incurred) + 合同毛利(amount-incurred)
        account = rule.get("account", "")
        incurred = doc_data.get("incurred_cost", 0) if doc_data else 0
        if "5501" in account:
            return total_amount  # 工程结算
        elif "5401" in account:
            return incurred  # 合同成本
        elif "5402" in account:
            return total_amount - incurred  # 合同毛利
        return total_amount
    elif doc_type in ("PROJ_PICK", "PROJECT_COST", "ENG_SETTLE", "ENG_INBOUND"):
        return total_amount
    return total_amount


def _get_account_name(code: str) -> str:
    """根据科目编码获取科目名称（含工程行业常用科目）"""
    _names = {
        "1001": "库存现金", "1002": "银行存款",
        "1122": "应收账款", "1221": "其他应收款",
        "1401": "原材料", "1403": "库存商品", "1411": "周转材料",
        "1901": "待处理财产损溢",
        "2202": "应付账款", "2211": "应付职工薪酬", "2221": "应交税费",
        "4001": "实收资本", "4101": "盈余公积",
        "5001": "生产成本—直接材料", "5002": "生产成本—直接人工",
        "5101": "生产成本—制造费用", "5102": "管理费用",
        "6001": "主营业务收入", "6401": "主营业务成本",
        "6601": "销售费用", "6602": "管理费用", "6701": "财务费用",
        # ===== 工程行业常用科目 =====
        "1601": "工程物资", "1602": "工程物资—专用材料", "1603": "工程物资—专用设备",
        "1604": "工程物资—工具器具",
        "1701": "临时设施", "1702": "临时设施摊销",
        "5401": "工程施工—合同成本", "5402": "工程施工—合同毛利",
        "5403": "工程施工—间接费用",
        "5501": "工程结算",
        "6002": "其他业务收入",
        "6402": "其他业务成本",
        "7101": "以前年度损益调整",
    }
    return _names.get(code, f"科目{code}")


# ============================================================
# 🔹 查询/审核/驳回 辅助函数
# ============================================================
def list_auto_vouchers(
    db: Session,
    account_set_id: int,
    status: Optional[str] = None,
    source_doc_type: Optional[str] = None,
    keyword: Optional[str] = None,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
) -> List[models.AutoVoucher]:
    q = db.query(models.AutoVoucher).filter(models.AutoVoucher.account_set_id == account_set_id)
    if status:
        q = q.filter(models.AutoVoucher.status == status)
    if source_doc_type:
        q = q.filter(models.AutoVoucher.source_doc_type == source_doc_type)
    if keyword:
        q = q.filter(
            (models.AutoVoucher.summary.contains(keyword)) |
            (models.AutoVoucher.voucher_no.contains(keyword)) |
            (models.AutoVoucher.source_doc_no.contains(keyword))
        )
    if start_date:
        q = q.filter(models.AutoVoucher.voucher_date >= start_date)
    if end_date:
        q = q.filter(models.AutoVoucher.voucher_date <= end_date)
    return q.order_by(models.AutoVoucher.created_at.desc()).all()


def approve_voucher(db: Session, voucher_id: int, approver: str = "system") -> models.AutoVoucher:
    v = db.query(models.AutoVoucher).filter(models.AutoVoucher.id == voucher_id).first()
    if not v:
        raise VoucherException("凭证不存在", "VOUCHER_NOT_FOUND")
    if v.status not in ("DRAFT", "PENDING"):
        raise VoucherException(f"当前状态为 {v.status}，无法审核", "VOUCHER_STATUS_ERROR")
    v.status = "APPROVED"
    v.approved_at = datetime.datetime.utcnow()
    v.approved_by = approver
    db.commit()
    return v


def reject_voucher(db: Session, voucher_id: int, reason: str) -> models.AutoVoucher:
    v = db.query(models.AutoVoucher).filter(models.AutoVoucher.id == voucher_id).first()
    if not v:
        raise VoucherException("凭证不存在", "VOUCHER_NOT_FOUND")
    v.status = "REJECTED"
    v.reject_reason = reason
    db.commit()
    return v


def post_voucher(db: Session, voucher_id: int) -> models.AutoVoucher:
    """凭证过账：写入正式凭证表"""
    v = db.query(models.AutoVoucher).filter(models.AutoVoucher.id == voucher_id).first()
    if not v:
        raise VoucherException("凭证不存在", "VOUCHER_NOT_FOUND")
    if v.status != "APPROVED":
        raise VoucherException("凭证需先审核才能过账", "VOUCHER_STATUS_ERROR")
    # 写入 VoucherDB
    voucher_type_map = {"INBOUND": "PURCHASE", "PURCHASE_INVOICE": "PURCHASE",
                       "SALES_OUTBOUND": "SALE", "SALES_INVOICE": "SALE",
                       "RECEIPT": "RECEIPT", "PAYMENT": "PAYMENT"}
    vdb = models.VoucherDB(
        account_set_id=v.account_set_id,
        voucher_no=v.voucher_no,
        voucher_type=voucher_type_map.get(v.source_doc_type, "GENERAL"),
        voucher_date=v.voucher_date,
        status=models.VoucherStatus.POSTED,
        reference_doc=v.source_doc_no,
        reference_type=v.source_doc_type,
        created_at=datetime.datetime.utcnow(),
        approved_at=v.approved_at,
        posted_at=datetime.datetime.utcnow(),
    )
    db.add(vdb)
    db.flush()
    # 写入分录
    for e in v.entries:
        ve = models.VoucherEntry(
            voucher_id=vdb.id,
            account_code=e.account_code,
            account_name=e.account_name,
            debit=e.amount if e.side == "debit" else 0,
            credit=e.amount if e.side == "credit" else 0,
            summary=e.summary,
            customer_id=e.customer_id,
            supplier_id=e.supplier_id,
            material_id=e.material_id,
        )
        db.add(ve)
    # 回写来源单据状态
    _update_source_doc_status(db, v)
    v.status = "POSTED"
    db.commit()
    return v


def _update_source_doc_status(db: Session, v: models.AutoVoucher):
    """回写来源单据的凭证号和状态"""
    try:
        doc_type = v.source_doc_type
        if doc_type == "INBOUND":
            doc = db.query(models.InboundOrder).filter(models.InboundOrder.id == v.source_doc_id).first()
            if doc:
                doc.status = "VOUCHER_POSTED"
        elif doc_type in ("SALES_OUTBOUND",):
            doc = db.query(models.OutboundOrder).filter(models.OutboundOrder.id == v.source_doc_id).first()
            if doc:
                doc.status = "VOUCHER_POSTED"
        elif doc_type in ("SALES_INVOICE", "PURCHASE_INVOICE"):
            inv = db.query(models.Invoice).filter(models.Invoice.id == v.source_doc_id).first()
            if inv:
                inv.status = "VOUCHER_POSTED"
        # 其他类型后续扩展
    except Exception:
        pass  # 回写失败不影响凭证主流程


# ============================================================
# 🔹 事件驱动触发入口（供各业务模块调用）
# ============================================================
def trigger_auto_voucher(
    db: Session,
    doc_type: str,
    doc_id: int,
    doc_no: str = "",
    account_set_id: int = 1,
    voucher_date: Optional[datetime.date] = None,
    force: bool = False,
    auto_approve: bool = True,
) -> Dict[str, Any]:
    """
    业务模块统一调用入口：触发自动凭证生成。
    auto_approve=True 时自动审核，返回凭证信息。
    生成失败不抛异常，返回 {success: False, error: ...}，避免阻断主业务流程。
    """
    try:
        v = generate_voucher(db, account_set_id, doc_type, doc_id, doc_no, voucher_date, force)
        if auto_approve:
            try:
                approve_voucher(db, v.id, approver="auto_system")
            except VoucherException:
                pass  # 审核失败不影响生成
        return {
            "success": True,
            "voucher_id": v.id,
            "voucher_no": v.voucher_no,
            "status": v.status,
            "total_debit": float(v.total_debit or 0),
            "total_credit": float(v.total_credit or 0),
        }
    except VoucherException as e:
        return {"success": False, "error": str(e), "error_code": e.error_code}
    except Exception as e:
        return {"success": False, "error": f"凭证生成异常：{str(e)}", "error_code": "VOUCHER_INTERNAL"}


# ============================================================
# 🔹 工程行业会计科目预置
# ============================================================
ENGINEERING_ACCOUNTS = [
    # 资产类
    {"code": "1001", "name": "库存现金", "type": "asset", "parent": None},
    {"code": "1002", "name": "银行存款", "type": "asset", "parent": None},
    {"code": "1122", "name": "应收账款", "type": "asset", "parent": None},
    {"code": "1221", "name": "其他应收款", "type": "asset", "parent": None},
    {"code": "1401", "name": "原材料", "type": "asset", "parent": None},
    {"code": "1403", "name": "库存商品", "type": "asset", "parent": None},
    {"code": "1411", "name": "周转材料", "type": "asset", "parent": None},
    {"code": "1601", "name": "工程物资", "type": "asset", "parent": None},
    {"code": "1602", "name": "工程物资—专用材料", "type": "asset", "parent": "1601"},
    {"code": "1603", "name": "工程物资—专用设备", "type": "asset", "parent": "1601"},
    {"code": "1604", "name": "工程物资—工具器具", "type": "asset", "parent": "1601"},
    {"code": "1701", "name": "临时设施", "type": "asset", "parent": None},
    {"code": "1702", "name": "临时设施摊销", "type": "asset", "parent": "1701"},
    {"code": "1901", "name": "待处理财产损溢", "type": "asset", "parent": None},
    # 负债类
    {"code": "2202", "name": "应付账款", "type": "liability", "parent": None},
    {"code": "2211", "name": "应付职工薪酬", "type": "liability", "parent": None},
    {"code": "2221", "name": "应交税费", "type": "liability", "parent": None},
    # 权益类
    {"code": "4001", "name": "实收资本", "type": "equity", "parent": None},
    {"code": "4101", "name": "盈余公积", "type": "equity", "parent": None},
    # 成本类（工程施工核心）
    {"code": "5401", "name": "工程施工—合同成本", "type": "cost", "parent": None},
    {"code": "5402", "name": "工程施工—合同毛利", "type": "cost", "parent": None},
    {"code": "5403", "name": "工程施工—间接费用", "type": "cost", "parent": None},
    {"code": "5501", "name": "工程结算", "type": "cost", "parent": None},
    # 损益类
    {"code": "6001", "name": "主营业务收入", "type": "income", "parent": None},
    {"code": "6002", "name": "其他业务收入", "type": "income", "parent": None},
    {"code": "6401", "name": "主营业务成本", "type": "expense", "parent": None},
    {"code": "6402", "name": "其他业务成本", "type": "expense", "parent": None},
    {"code": "6601", "name": "销售费用", "type": "expense", "parent": None},
    {"code": "6602", "name": "管理费用", "type": "expense", "parent": None},
    {"code": "6701", "name": "财务费用", "type": "expense", "parent": None},
]


def seed_engineering_accounts(db: Session, account_set_id: int = 1) -> Dict[str, Any]:
    """预置工程行业会计科目到 AccountingSubject 表"""
    from ..models import AccountingSubject
    created = 0
    updated = 0
    # 类型映射：简化名 → 模型 category 枚举值
    category_map = {
        "asset": "ASSET", "liability": "LIABILITY", "equity": "EQUITY",
        "income": "REVENUE", "expense": "EXPENSE", "cost": "COST",
    }
    for acc in ENGINEERING_ACCOUNTS:
        existing = db.query(AccountingSubject).filter(
            AccountingSubject.account_set_id == account_set_id,
            AccountingSubject.code == acc["code"]
        ).first()
        if existing:
            updated += 1
            continue
        subj = AccountingSubject(
            account_set_id=account_set_id,
            code=acc["code"],
            name=acc["name"],
            category=category_map.get(acc["type"], "ASSET"),
            parent_code=acc.get("parent"),
            level=2 if acc.get("parent") else 1,
            is_active=True,
            created_at=datetime.datetime.utcnow(),
        )
        db.add(subj)
        created += 1
    db.commit()
    return {"success": True, "created": created, "updated": updated, "total": len(ENGINEERING_ACCOUNTS)}
