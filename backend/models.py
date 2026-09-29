from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, DECIMAL, Text, Enum, Boolean
from sqlalchemy.orm import relationship
from .database import Base
import datetime
from enum import Enum as PyEnum

class CostType(PyEnum):
    RAW_MATERIAL = "RAW_MATERIAL"
    DIRECT_LABOR = "DIRECT_LABOR"
    MANUFACTURING_OVERHEAD = "MANUFACTURING_OVERHEAD"

class AlertLevel(PyEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class WorkOrderStatus(PyEnum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class TransactionType(PyEnum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"
    ADJUSTMENT = "ADJUSTMENT"
    STOCKTAKE = "STOCKTAKE"

class StockType(PyEnum):
    RAW_MATERIAL = "RAW_MATERIAL"
    WORK_IN_PROGRESS = "WORK_IN_PROGRESS"
    FINISHED_GOODS = "FINISHED_GOODS"

class ContractType(PyEnum):
    SALES = "SALES"
    PURCHASE = "PURCHASE"

class ContractStatus(PyEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    TERMINATED = "TERMINATED"

class ApprovalStatus(PyEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    WAITING_SUPPLEMENT = "WAITING_SUPPLEMENT"

class CompanyScale(PyEnum):
    SINGLE_USER = "SINGLE_USER"
    SMALL_TEAM = "SMALL_TEAM"
    LARGE_TEAM = "LARGE_TEAM"

class BusinessComplexity(PyEnum):
    TRADE_ONLY = "TRADE_ONLY"
    SIMPLE_PROCESSING = "SIMPLE_PROCESSING"
    COMPLEX_MANUFACTURING = "COMPLEX_MANUFACTURING"

class PriceType(PyEnum):
    RETAIL = "RETAIL"
    WHOLESALE = "WHOLESALE"
    MEMBER = "MEMBER"
    PROMOTION = "PROMOTION"

class TradeTerm(PyEnum):
    FOB = "FOB"
    CIF = "CIF"
    DDP = "DDP"
    DAP = "DAP"

class MaterialType(PyEnum):
    RAW_MATERIAL = "RAW_MATERIAL"
    SEMI_FINISHED = "SEMI_FINISHED"
    FINISHED_GOODS = "FINISHED_GOODS"
    ENGINEERING_MATERIAL = "ENGINEERING_MATERIAL"  # 工程物资
    SPARE_PARTS = "SPARE_PARTS"  # 备品备件

class MaterialProperty(PyEnum):
    PURCHASE = "PURCHASE"
    OUTSOURCING = "OUTSOURCING"
    INHOUSE = "INHOUSE"

class VoucherStatus(PyEnum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    POSTED = "POSTED"

class VoucherType(PyEnum):
    GENERAL = "GENERAL"
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    PAYMENT = "PAYMENT"
    RECEIPT = "RECEIPT"

class CashFlowCategory(PyEnum):
    OPERATING = "OPERATING"
    INVESTING = "INVESTING"
    FINANCING = "FINANCING"

class AccountSet(Base):
    __tablename__ = "account_sets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    company_name = Column(String(200), nullable=False)
    tax_id = Column(String(50), nullable=True)
    currency = Column(String(10), default="CNY")
    timezone = Column(String(50), default="Asia/Shanghai")
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    materials = relationship("Material", back_populates="account_set")
    suppliers = relationship("Supplier", back_populates="account_set")
    customers = relationship("Customer", back_populates="account_set")
    purchase_orders = relationship("PurchaseOrder", back_populates="account_set")
    sales_orders = relationship("SalesOrder", back_populates="account_set")
    work_orders = relationship("ProductionWorkOrder", back_populates="account_set")
    contracts = relationship("Contract", back_populates="account_set")
    employees = relationship("Employee", back_populates="account_set")
    vouchers = relationship("VoucherDB", back_populates="account_set")
    system_config = relationship("SystemConfig", back_populates="account_set", uselist=False)

class SystemConfig(Base):
    __tablename__ = "system_configs"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    company_scale = Column(Enum(CompanyScale), default=CompanyScale.SINGLE_USER)
    business_complexity = Column(Enum(BusinessComplexity), default=BusinessComplexity.TRADE_ONLY)
    approval_enabled = Column(Boolean, default=True)
    auto_voucher_enabled = Column(Boolean, default=True)
    multi_price_enabled = Column(Boolean, default=True)
    crossborder_enabled = Column(Boolean, default=False)
    labor_compliance_enabled = Column(Boolean, default=True)
    cva_abc_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet", back_populates="system_config")

class Material(Base):
    __tablename__ = "materials"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)
    barcode = Column(String(100), nullable=True)
    spec = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    unit_price = Column(DECIMAL(18, 4), nullable=False, default=0.0)
    unit = Column(String(20), nullable=False)
    hs_code = Column(String(20), nullable=True)
    type = Column(Enum(MaterialType), default=MaterialType.RAW_MATERIAL)
    property = Column(Enum(MaterialProperty), default=MaterialProperty.PURCHASE)
    lead_time = Column(Integer, default=0)
    safety_stock = Column(DECIMAL(18, 4), default=0)
    batch_rule = Column(String(20), default="FIXED")
    batch_size = Column(DECIMAL(18, 4), default=1)
    loss_rate = Column(DECIMAL(5, 2), default=0)
    min_stock = Column(Integer, default=0)
    max_stock = Column(Integer, default=1000)
    criticality = Column(Integer, nullable=True)
    value_score = Column(DECIMAL(5, 2), nullable=True)
    cva_abc_class = Column(String(10), nullable=True)
    cva_class = Column(String(5), nullable=True)
    abc_class = Column(String(5), nullable=True)
    classification_coefficient = Column(DECIMAL(5, 2), default=1.0)
    batch_tracking_enabled = Column(Boolean, default=False)
    is_slow_moving = Column(Boolean, default=False)
    shelf_life_days = Column(Integer, nullable=True)
    reorder_point = Column(Integer, default=0)
    default_supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    # 新增：存货科目编码（凭证自动生成时使用）
    inventory_account_code = Column(String(50), nullable=True)
    # 新增：收入科目编码（销售出库/开票时使用）
    income_account_code = Column(String(50), nullable=True)
    # 新增：成本科目编码（结转销售成本时使用）
    cost_account_code = Column(String(50), nullable=True)
    # 新增：领料模式 1=按单领料 2=配料制 3=集中配送 4=倒冲
    picking_mode = Column(Integer, default=1)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet", back_populates="materials")
    inventory_records = relationship("InventoryRecord", back_populates="material")
    transactions = relationship("InventoryTransaction", back_populates="material")
    bom_items = relationship("BOMItem", back_populates="material")
    default_supplier = relationship("Supplier")

class MaterialCategory(Base):
    """物料分类编码规则表（三级分类 + 编码规则 + 规格标准）"""
    __tablename__ = "material_categories"
    id = Column(Integer, primary_key=True, index=True)
    level = Column(Integer, nullable=False)  # 1=一级 2=二级 3=三级
    parent_id = Column(Integer, ForeignKey("material_categories.id"), nullable=True)
    # 分类名称
    name = Column(String(100), nullable=False)
    # 分类代号（一级2位/二级2位/三级3位）
    code = Column(String(10), nullable=False)
    # 完整路径代号（如 1.01.005）
    full_code = Column(String(50), nullable=True)
    # 物料名称（三级才有，如"铁板"）
    material_name = Column(String(100), nullable=True)
    # 规格描述标准（如"厚(t)×宽×长"）
    spec_standard = Column(String(200), nullable=True)
    # 特性（如"厚度""直径""功率"）
    characteristic = Column(String(50), nullable=True)
    # 流水号当前值（用于自动生成）
    current_sequence = Column(Integer, default=0)
    # 排序
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    parent = relationship("MaterialCategory", remote_side=[id], backref="children")

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)
    tax_id = Column(String(50), nullable=True)
    tax_id_expiry = Column(Date, nullable=True)
    contact = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    history_price = Column(DECIMAL(18, 4), nullable=True)
    on_time_rate = Column(DECIMAL(5, 2), nullable=True)
    quality_rate = Column(DECIMAL(5, 2), nullable=True)
    compliance_rating = Column(String(10), nullable=True)
    # 工程导向型：综合评级（质量×0.6 + 交期×0.4）
    rating_score = Column(DECIMAL(5, 2), nullable=True)
    # 是否海外贸易（海外供应商需填贸易术语如FOB/CIF）
    is_overseas = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet", back_populates="suppliers")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")
    contracts = relationship("Contract", back_populates="supplier")

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)
    tax_id = Column(String(50), nullable=True)
    contact = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    credit_limit = Column(DECIMAL(18, 2), default=0)
    credit_used = Column(DECIMAL(18, 2), default=0)
    customer_level = Column(String(20), default="NORMAL")
    # 是否海外贸易（海外客户需填贸易术语如FOB/CIF）
    is_overseas = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet", back_populates="customers")
    sales_orders = relationship("SalesOrder", back_populates="customer")
    contracts = relationship("Contract", back_populates="customer")

class PurchaseOrderTemplate(Base):
    __tablename__ = "purchase_order_templates"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    tax_rate = Column(DECIMAL(5, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    items = relationship("PurchaseOrderTemplateItem", back_populates="template")

class PurchaseOrderTemplateItem(Base):
    __tablename__ = "purchase_order_template_items"
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("purchase_order_templates.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(18, 4), nullable=False)
    is_gift = Column(Boolean, default=False)

    template = relationship("PurchaseOrderTemplate", back_populates="items")
    material = relationship("Material")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    po_no = Column(String(50), unique=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    template_id = Column(Integer, ForeignKey("purchase_order_templates.id"), nullable=True)
    status = Column(String(20), nullable=False, default="PENDING")
    approval_status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    is_emergency = Column(Boolean, default=False)
    need_supplement = Column(Boolean, default=False)
    tax_rate = Column(DECIMAL(5, 2), nullable=False)
    discount_amount = Column(DECIMAL(18, 4), default=0)
    discount_rate = Column(DECIMAL(5, 2), nullable=True)
    # V2 扩展字段
    order_date = Column(Date, nullable=True)
    expected_date = Column(Date, nullable=True)
    payment_terms = Column(String(100), nullable=True)
    transport_type = Column(String(50), nullable=True)
    warehouse_id = Column(Integer, nullable=True)
    total_amount = Column(DECIMAL(18, 4), default=0)
    # 工程导向型：项目关联 + BOM行项关联
    project_id = Column(Integer, ForeignKey("wbs_projects.id"), nullable=True)
    bom_line_ref = Column(String(100), nullable=True)  # BOM行项引用
    remark = Column(Text, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet", back_populates="purchase_orders")
    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order")

class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(18, 4), nullable=False)
    is_gift = Column(Boolean, default=False)
    special_price = Column(DECIMAL(18, 4), nullable=True)
    allocated_discount = Column(DECIMAL(18, 4), default=0)
    # V2 扩展字段
    line_no = Column(Integer, nullable=True)
    unit = Column(String(20), nullable=True)
    amount = Column(DECIMAL(18, 4), nullable=True)
    source_no = Column(String(50), nullable=True)
    delivery_date = Column(Date, nullable=True)
    supplier_name = Column(String(100), nullable=True)  # 行级供应商（每个零件可不同供应商）
    received_qty = Column(DECIMAL(18, 4), default=0)
    tax_rate = Column(DECIMAL(5, 2), nullable=True)
    tax_amount = Column(DECIMAL(18, 4), nullable=True)
    total_amount = Column(DECIMAL(18, 4), nullable=True)
    remark = Column(Text, nullable=True)

    purchase_order = relationship("PurchaseOrder", back_populates="items")
    material = relationship("Material")

class PurchaseContract(Base):
    """采购合同（采购管理专用，可填写生成正式合同文书含法律声明）"""
    __tablename__ = "purchase_contracts"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False, default=1)
    contract_no = Column(String(50), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("wbs_projects.id"), nullable=True)
    # 甲方（采购方）
    party_a_name = Column(String(200), nullable=True)
    party_a_address = Column(String(300), nullable=True)
    party_a_contact = Column(String(50), nullable=True)
    party_a_phone = Column(String(50), nullable=True)
    # 乙方（供货方）
    party_b_name = Column(String(200), nullable=True)
    party_b_address = Column(String(300), nullable=True)
    party_b_contact = Column(String(50), nullable=True)
    party_b_phone = Column(String(50), nullable=True)
    # 商务条款
    total_amount = Column(DECIMAL(18, 2), default=0)
    sign_date = Column(Date, nullable=True)
    delivery_date = Column(Date, nullable=True)
    delivery_location = Column(String(300), nullable=True)
    payment_terms = Column(String(500), nullable=True)
    quality_terms = Column(Text, nullable=True)
    acceptance_terms = Column(Text, nullable=True)
    warranty_months = Column(Integer, default=12)
    breach_rate = Column(DECIMAL(5, 2), default=5)  # 违约金比例%
    special_terms = Column(Text, nullable=True)
    legal_declaration = Column(Text, nullable=True)  # 法律声明（可编辑，默认标准条款）
    status = Column(String(20), nullable=False, default="DRAFT")  # DRAFT/SIGNED/CANCELLED
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    supplier = relationship("Supplier")
    items = relationship("PurchaseContractItem", back_populates="contract", cascade="all, delete-orphan")

class PurchaseContractItem(Base):
    __tablename__ = "purchase_contract_items"
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("purchase_contracts.id"), nullable=False)
    line_no = Column(Integer, default=0)
    material_code = Column(String(50), nullable=True)
    material_name = Column(String(200), nullable=False)
    spec = Column(String(200), nullable=True)
    quantity = Column(DECIMAL(18, 4), default=1)
    unit = Column(String(20), nullable=True)
    unit_price = Column(DECIMAL(18, 4), default=0)
    amount = Column(DECIMAL(18, 4), default=0)
    delivery_date = Column(Date, nullable=True)
    remark = Column(Text, nullable=True)

    contract = relationship("PurchaseContract", back_populates="items")

class PriceList(Base):
    __tablename__ = "price_lists"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    price_type = Column(Enum(PriceType), nullable=False)
    customer_level = Column(String(20), nullable=True)
    price = Column(DECIMAL(18, 4), nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    material = relationship("Material")

class SalesOrder(Base):
    __tablename__ = "sales_orders"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    so_no = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    status = Column(String(20), nullable=False, default="PENDING")
    trade_term = Column(Enum(TradeTerm), nullable=True)
    currency = Column(String(10), default="CNY")
    exchange_rate = Column(DECIMAL(10, 4), default=1.0)
    credit_check_passed = Column(Boolean, default=True)
    delivery_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet", back_populates="sales_orders")
    customer = relationship("Customer", back_populates="sales_orders")
    items = relationship("SalesOrderItem", back_populates="sales_order")

class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"
    id = Column(Integer, primary_key=True, index=True)
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(18, 4), nullable=False)
    is_gift = Column(Boolean, default=False)
    allocated_discount = Column(DECIMAL(18, 4), default=0)
    price_type = Column(Enum(PriceType), nullable=True)

    sales_order = relationship("SalesOrder", back_populates="items")
    material = relationship("Material")

class BOM(Base):
    __tablename__ = "boms"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    bom_code = Column(String(50), nullable=True)  # BOM编号
    name = Column(String(200), nullable=True)  # BOM名称
    product_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    version = Column(String(20), default="V1")
    # BOM类型：EBOM工程BOM / MBOM制造BOM
    bom_type = Column(String(10), default="EBOM")
    effective_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(String(20), default="ACTIVE")  # DRAFT草稿/ACTIVE生效/EXPIRED失效
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    product = relationship("Material")
    items = relationship("BOMItem", back_populates="bom")

class BOMItem(Base):
    __tablename__ = "bom_items"
    id = Column(Integer, primary_key=True, index=True)
    bom_id = Column(Integer, ForeignKey("boms.id"), nullable=False)
    # 树形结构：父BOM明细ID（用于BOM内部层级）
    parent_item_id = Column(Integer, ForeignKey("bom_items.id"), nullable=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    material_code = Column(String(50), nullable=True)  # 冗余便于展示
    material_name = Column(String(200), nullable=True)
    spec = Column(String(200), nullable=True)  # 规格
    quantity = Column(DECIMAL(18, 4), nullable=False)
    unit = Column(String(20), nullable=False)
    loss_rate = Column(DECIMAL(5, 2), default=0)  # 损耗率(%)
    scrap_rate = Column(DECIMAL(5, 2), default=0)  # 兼容旧字段
    # 工件类型：MACHINABLE可加工 / STANDARD标准件 / PURCHASE外购 / OUTSOURCE外协 / ASSEMBLY装配
    item_type = Column(String(20), default="PURCHASE")
    process_name = Column(String(100), nullable=True)  # 工艺/工序名称
    # 新增扩展字段
    material_grade = Column(String(100), nullable=True)  # 材质
    surface_treatment = Column(String(100), nullable=True)  # 表面处理
    bom_level = Column(Integer, default=1)  # BOM层级
    remark = Column(String(200), nullable=True)
    sequence = Column(Integer, default=0)
    level = Column(Integer, default=1)

    bom = relationship("BOM", back_populates="items")
    material = relationship("Material")


class InTransitMaterial(Base):
    """在途物料：采购/外协订单已下单未到货的物料"""
    __tablename__ = "in_transit_materials"
    id = Column(Integer, primary_key=True, index=True)
    material_code = Column(String(50), nullable=True)
    material_name = Column(String(200), nullable=False)
    specification = Column(String(200), nullable=True)
    quantity = Column(DECIMAL(18, 4), nullable=False, default=0)
    unit = Column(String(20), default="个")
    # 在途类型：PURCHASE采购在途 / OUTSOURCE外协在途
    transit_type = Column(String(20), default="PURCHASE")
    supplier = Column(String(100), nullable=True)
    order_no = Column(String(50), nullable=True)  # 关联采购/外协单号
    # 状态：ORDERED已下单 / SHIPPED已发货 / ARRIVED已到货
    status = Column(String(20), default="ORDERED")
    expected_arrival = Column(Date, nullable=True)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

class ProductionWorkOrder(Base):
    __tablename__ = "production_workorders"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    work_order_no = Column(String(50), unique=True, nullable=False)
    product_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    bom_id = Column(Integer, ForeignKey("boms.id"), nullable=True)
    planned_qty = Column(Integer, nullable=False)
    completed_qty = Column(Integer, nullable=False, default=0)
    in_progress_qty = Column(Integer, nullable=False, default=0)
    completion_ratio = Column(DECIMAL(5, 2), nullable=True)
    status = Column(Enum(WorkOrderStatus), nullable=False, default=WorkOrderStatus.PLANNED)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    actual_material_cost = Column(DECIMAL(18, 4), default=0)
    actual_labor_cost = Column(DECIMAL(18, 4), default=0)
    actual_overhead_cost = Column(DECIMAL(18, 4), default=0)
    standard_cost = Column(DECIMAL(18, 4), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    project_id = Column(Integer, nullable=True)
    routing_id = Column(Integer, nullable=True)
    work_center_id = Column(Integer, nullable=True)
    priority = Column(String(20), default="NORMAL")

    account_set = relationship("AccountSet", back_populates="work_orders")
    product = relationship("Material")
    bom = relationship("BOM")
    costs = relationship("ProductionCost", back_populates="work_order")
    allocations = relationship("CostAllocation", back_populates="work_order")

class ProductionCost(Base):
    __tablename__ = "production_costs"
    id = Column(Integer, primary_key=True, index=True)
    work_order_id = Column(Integer, ForeignKey("production_workorders.id"), nullable=False)
    cost_type = Column(Enum(CostType), nullable=False)
    amount = Column(DECIMAL(18, 4), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    work_order = relationship("ProductionWorkOrder", back_populates="costs")

class CostAllocation(Base):
    __tablename__ = "cost_allocations"
    id = Column(Integer, primary_key=True, index=True)
    work_order_id = Column(Integer, ForeignKey("production_workorders.id"), nullable=False)
    total_input_cost = Column(DECIMAL(18, 4), nullable=False)
    equivalent_output = Column(DECIMAL(18, 4), nullable=False)
    cost_per_equivalent = Column(DECIMAL(18, 4), nullable=False)
    completed_allocation = Column(DECIMAL(18, 4), nullable=False)
    in_progress_allocation = Column(DECIMAL(18, 4), nullable=False)
    material_ratio = Column(DECIMAL(5, 2), nullable=True)
    labor_ratio = Column(DECIMAL(5, 2), nullable=True)
    overhead_ratio = Column(DECIMAL(5, 2), nullable=True)
    allocated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    work_order = relationship("ProductionWorkOrder", back_populates="allocations")

class InventoryRecord(Base):
    __tablename__ = "inventory_records"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    location_code = Column(String(50), nullable=False)
    batch_no = Column(String(50), nullable=True)
    expiry_date = Column(Date, nullable=True)
    quantity = Column(Integer, nullable=False)
    stock_type = Column(Enum(StockType), nullable=False)
    unit_cost = Column(DECIMAL(18, 4), default=0)

    account_set = relationship("AccountSet")
    material = relationship("Material", back_populates="inventory_records")

class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    quantity = Column(Integer, nullable=False)
    before_qty = Column(Integer, nullable=False)
    after_qty = Column(Integer, nullable=False)
    reference_no = Column(String(50), nullable=True)
    operator = Column(String(50), nullable=False)
    unit_cost = Column(DECIMAL(18, 4), nullable=True)
    total_cost = Column(DECIMAL(18, 4), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    material = relationship("Material", back_populates="transactions")

class StocktakingTask(Base):
    __tablename__ = "stocktaking_tasks"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    task_no = Column(String(50), unique=True, nullable=False)
    status = Column(String(20), default="PLANNED")
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    location_code = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    account_set = relationship("AccountSet")
    items = relationship("StocktakingItem", back_populates="task")

class StocktakingItem(Base):
    __tablename__ = "stocktaking_items"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("stocktaking_tasks.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    location_code = Column(String(50), nullable=False)
    book_qty = Column(Integer, nullable=False)
    actual_qty = Column(Integer, nullable=True)
    variance = Column(Integer, nullable=True)
    variance_amount = Column(DECIMAL(18, 4), nullable=True)
    reason = Column(Text, nullable=True)

    task = relationship("StocktakingTask", back_populates="items")
    material = relationship("Material")

class Contract(Base):
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    contract_no = Column(String(50), unique=True, nullable=False)
    contract_type = Column(Enum(ContractType), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    status = Column(Enum(ContractStatus), default=ContractStatus.DRAFT)
    amount = Column(DECIMAL(18, 2), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    payment_due_dates = Column(Text, nullable=True)
    delivery_dates = Column(Text, nullable=True)
    # 工程导向型：项目关联 + 里程碑付款计划
    project_id = Column(Integer, ForeignKey("wbs_projects.id"), nullable=True)
    milestone_payments = Column(Text, nullable=True)  # JSON: [{stage, ratio, amount, due_date, status}]
    contract_amount = Column(DECIMAL(18, 2), nullable=True)  # 合同总额（工程合同专用）
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet", back_populates="contracts")
    customer = relationship("Customer", back_populates="contracts")
    supplier = relationship("Supplier", back_populates="contracts")

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    employee_no = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    id_card = Column(String(20), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    department = Column(String(50), nullable=True)
    position = Column(String(50), nullable=True)
    hire_date = Column(Date, nullable=False)
    contract_start_date = Column(Date, nullable=True)
    contract_end_date = Column(Date, nullable=True)
    probation_end_date = Column(Date, nullable=True)
    social_security_start_date = Column(Date, nullable=True)
    status = Column(String(20), default="ACTIVE")
    base_salary = Column(DECIMAL(18, 2), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet", back_populates="employees")

class VoucherDB(Base):
    __tablename__ = "vouchers"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    voucher_no = Column(String(50), unique=True, nullable=False)
    voucher_type = Column(Enum(VoucherType), default=VoucherType.GENERAL)
    voucher_date = Column(Date, nullable=False)
    status = Column(Enum(VoucherStatus), default=VoucherStatus.DRAFT)
    attachments = Column(Integer, default=0)
    preparer = Column(String(50), nullable=True)
    approver = Column(String(50), nullable=True)
    poster = Column(String(50), nullable=True)
    reference_doc = Column(String(100), nullable=True)
    reference_type = Column(String(30), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    posted_at = Column(DateTime, nullable=True)

    account_set = relationship("AccountSet", back_populates="vouchers")
    entries = relationship("VoucherEntry", back_populates="voucher")

class VoucherEntry(Base):
    __tablename__ = "voucher_entries"
    id = Column(Integer, primary_key=True, index=True)
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=False)
    account_code = Column(String(50), nullable=False)
    account_name = Column(String(100), nullable=False)
    debit = Column(DECIMAL(18, 2), nullable=True)
    credit = Column(DECIMAL(18, 2), nullable=True)
    summary = Column(String(200), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    department_id = Column(Integer, nullable=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    project_id = Column(Integer, nullable=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    voucher = relationship("VoucherDB", back_populates="entries")
    customer = relationship("Customer")
    supplier = relationship("Supplier")
    employee = relationship("Employee")
    material = relationship("Material")

class CashFlowItem(Base):
    __tablename__ = "cash_flow_items"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    item_code = Column(String(50), nullable=False)
    item_name = Column(String(100), nullable=False)
    category = Column(Enum(CashFlowCategory), nullable=False)
    parent_item_code = Column(String(50), nullable=True)
    account_codes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")

class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    from_currency = Column(String(10), nullable=False)
    to_currency = Column(String(10), nullable=False)
    rate = Column(DECIMAL(12, 6), nullable=False)
    rate_date = Column(Date, nullable=False)
    source = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")

class ComplianceAlert(Base):
    __tablename__ = "compliance_alerts"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    alert_type = Column(String(30), nullable=False)
    level = Column(Enum(AlertLevel), nullable=False)
    reference_id = Column(Integer, nullable=True)
    reference_type = Column(String(30), nullable=True)
    message = Column(Text, nullable=False)
    suggestion = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="PENDING")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    account_set = relationship("AccountSet")

class HsCode(Base):
    __tablename__ = "hs_codes"
    id = Column(Integer, primary_key=True, index=True)
    hs_code = Column(String(20), unique=True, nullable=False)
    description_cn = Column(Text, nullable=False)
    description_en = Column(Text, nullable=True)
    unit = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

class CountryTaxRule(Base):
    __tablename__ = "country_tax_rules"
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), nullable=False)
    country_name = Column(String(100), nullable=False)
    vat_rate = Column(DECIMAL(5, 2), nullable=True)
    import_tax_rate = Column(DECIMAL(5, 2), nullable=True)
    currency_code = Column(String(10), nullable=False)
    invoice_language = Column(String(20), nullable=True)
    tax_free_threshold = Column(DECIMAL(18, 2), nullable=True)
    tax_id_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=True)
    role = Column(String(20), default="USER")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")

class BatchRule(Base):
    __tablename__ = "batch_rules"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    name = Column(String(100), nullable=False)
    rule_pattern = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")

class StorageLocation(Base):
    __tablename__ = "storage_locations"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    location_code = Column(String(50), unique=True, nullable=False)
    location_name = Column(String(100), nullable=False)
    parent_code = Column(String(50), nullable=True)
    level = Column(Integer, default=1)
    max_capacity = Column(Integer, nullable=True)
    max_weight = Column(DECIMAL(18, 2), nullable=True)
    current_capacity = Column(Integer, default=0)
    current_weight = Column(DECIMAL(18, 2), default=0)
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")

class UnitConversion(Base):
    __tablename__ = "unit_conversions"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    from_unit = Column(String(20), nullable=False)
    to_unit = Column(String(20), nullable=False)
    conversion_rate = Column(DECIMAL(18, 4), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    material = relationship("Material")

class PurchaseAgreement(Base):
    __tablename__ = "purchase_agreements"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    agreement_no = Column(String(50), unique=True, nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    unit_price = Column(DECIMAL(18, 4), nullable=False)
    min_order_qty = Column(Integer, default=1)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    supplier = relationship("Supplier")
    material = relationship("Material")

class PreReceipt(Base):
    __tablename__ = "pre_receipts"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    pre_receipt_no = Column(String(50), unique=True, nullable=False)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    expected_arrival_date = Column(Date, nullable=True)
    actual_arrival_date = Column(Date, nullable=True)
    delivery_no = Column(String(50), nullable=True)
    status = Column(String(20), default="PENDING")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    purchase_order = relationship("PurchaseOrder")
    supplier = relationship("Supplier")
    items = relationship("PreReceiptItem", back_populates="pre_receipt")

class PreReceiptItem(Base):
    __tablename__ = "pre_receipt_items"
    id = Column(Integer, primary_key=True, index=True)
    pre_receipt_id = Column(Integer, ForeignKey("pre_receipts.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    expected_qty = Column(Integer, nullable=False)
    actual_qty = Column(Integer, nullable=True)
    unit_price = Column(DECIMAL(18, 4), nullable=True)
    batch_no = Column(String(50), nullable=True)
    expiry_date = Column(Date, nullable=True)
    location_code = Column(String(50), nullable=True)

    pre_receipt = relationship("PreReceipt", back_populates="items")
    material = relationship("Material")

class InboundOrder(Base):
    __tablename__ = "inbound_orders"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    inbound_no = Column(String(50), unique=True, nullable=False)
    pre_receipt_id = Column(Integer, ForeignKey("pre_receipts.id"), nullable=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    inbound_date = Column(Date, nullable=False)
    status = Column(String(20), default="PENDING")
    quality_status = Column(String(20), default="PENDING")
    operator = Column(String(50), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    pre_receipt = relationship("PreReceipt")
    purchase_order = relationship("PurchaseOrder")
    supplier = relationship("Supplier")
    items = relationship("InboundOrderItem", back_populates="inbound_order")

class InboundOrderItem(Base):
    __tablename__ = "inbound_order_items"
    id = Column(Integer, primary_key=True, index=True)
    inbound_order_id = Column(Integer, ForeignKey("inbound_orders.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    batch_no = Column(String(50), nullable=False)
    expiry_date = Column(Date, nullable=True)
    location_code = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(18, 4), nullable=False)
    quality_status = Column(String(20), default="PENDING")
    variance_qty = Column(Integer, default=0)
    variance_reason = Column(String(200), nullable=True)

    inbound_order = relationship("InboundOrder", back_populates="items")
    material = relationship("Material")

class OutboundOrder(Base):
    __tablename__ = "outbound_orders"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    outbound_no = Column(String(50), unique=True, nullable=False)
    outbound_type = Column(String(20), nullable=False)
    source_order_id = Column(Integer, nullable=True)
    source_order_no = Column(String(50), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    department_id = Column(Integer, nullable=True)
    outbound_date = Column(Date, nullable=False)
    status = Column(String(20), default="PENDING")
    operator = Column(String(50), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    customer = relationship("Customer")
    items = relationship("OutboundOrderItem", back_populates="outbound_order")

class OutboundOrderItem(Base):
    __tablename__ = "outbound_order_items"
    id = Column(Integer, primary_key=True, index=True)
    outbound_order_id = Column(Integer, ForeignKey("outbound_orders.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    batch_no = Column(String(50), nullable=False)
    location_code = Column(String(50), nullable=False)
    requested_qty = Column(Integer, nullable=False)
    actual_qty = Column(Integer, nullable=True)
    unit_cost = Column(DECIMAL(18, 4), nullable=True)
    total_cost = Column(DECIMAL(18, 4), nullable=True)

    outbound_order = relationship("OutboundOrder", back_populates="items")
    material = relationship("Material")

class BatchInventory(Base):
    __tablename__ = "batch_inventory"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    batch_no = Column(String(50), nullable=False)
    location_code = Column(String(50), nullable=False)
    expiry_date = Column(Date, nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(DECIMAL(18, 4), nullable=False)
    total_cost = Column(DECIMAL(18, 4), nullable=False)
    quality_status = Column(String(20), default="AVAILABLE")
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)
    inbound_date = Column(Date, nullable=True)
    last_movement_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    material = relationship("Material")
    supplier = relationship("Supplier")
    purchase_order = relationship("PurchaseOrder")

class BatchMovement(Base):
    __tablename__ = "batch_movements"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    batch_no = Column(String(50), nullable=False)
    movement_type = Column(String(20), nullable=False)
    quantity = Column(Integer, nullable=False)
    location_code = Column(String(50), nullable=False)
    to_location_code = Column(String(50), nullable=True)
    reference_no = Column(String(50), nullable=True)
    reference_type = Column(String(30), nullable=True)
    operator = Column(String(50), nullable=False)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    material = relationship("Material")

class DeliveryNote(Base):
    __tablename__ = "delivery_notes"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    delivery_no = Column(String(50), unique=True, nullable=False)
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    delivery_date = Column(Date, nullable=False)
    status = Column(String(20), default="PENDING")
    ship_to_address = Column(Text, nullable=True)
    operator = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    sales_order = relationship("SalesOrder")
    customer = relationship("Customer")
    items = relationship("DeliveryNoteItem", back_populates="delivery_note")

class DeliveryNoteItem(Base):
    __tablename__ = "delivery_note_items"
    id = Column(Integer, primary_key=True, index=True)
    delivery_note_id = Column(Integer, ForeignKey("delivery_notes.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    batch_no = Column(String(50), nullable=True)
    quantity = Column(Integer, nullable=False)
    shipped_qty = Column(Integer, default=0)
    unit_price = Column(DECIMAL(18, 4), nullable=True)

    delivery_note = relationship("DeliveryNote", back_populates="items")
    material = relationship("Material")

class SalesOutbound(Base):
    __tablename__ = "sales_outbound"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    outbound_no = Column(String(50), unique=True, nullable=False)
    delivery_note_id = Column(Integer, ForeignKey("delivery_notes.id"), nullable=True)
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    outbound_date = Column(Date, nullable=False)
    status = Column(String(20), default="PENDING")
    payment_type = Column(String(20), nullable=True)
    is_credit = Column(Boolean, default=False)
    operator = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    delivery_note = relationship("DeliveryNote")
    sales_order = relationship("SalesOrder")
    customer = relationship("Customer")
    items = relationship("SalesOutboundItem", back_populates="sales_outbound")

class SalesOutboundItem(Base):
    __tablename__ = "sales_outbound_items"
    id = Column(Integer, primary_key=True, index=True)
    sales_outbound_id = Column(Integer, ForeignKey("sales_outbound.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    batch_no = Column(String(50), nullable=False)
    location_code = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(DECIMAL(18, 4), nullable=True)
    unit_price = Column(DECIMAL(18, 4), nullable=True)
    total_amount = Column(DECIMAL(18, 4), nullable=True)

    sales_outbound = relationship("SalesOutbound", back_populates="items")
    material = relationship("Material")

class Forecast(Base):
    __tablename__ = "forecasts"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    forecast_no = Column(String(50), unique=True, nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    forecast_qty = Column(Integer, nullable=False)
    forecast_date = Column(Date, nullable=False)
    status = Column(String(20), default="PENDING")
    source_type = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    material = relationship("Material")

class MRPResult(Base):
    __tablename__ = "mrp_results"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    mrp_run_no = Column(String(50), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    parent_material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    bom_level = Column(Integer, default=0)
    gross_requirement = Column(DECIMAL(18, 4), default=0)
    on_hand_qty = Column(DECIMAL(18, 4), default=0)
    on_order_qty = Column(DECIMAL(18, 4), default=0)
    safety_stock = Column(DECIMAL(18, 4), default=0)
    net_requirement = Column(DECIMAL(18, 4), default=0)
    planned_order_qty = Column(DECIMAL(18, 4), default=0)
    planned_date = Column(Date, nullable=True)
    planned_release_date = Column(Date, nullable=True)
    planned_type = Column(String(20), nullable=True)
    material_property = Column(String(20), nullable=True)
    loss_rate = Column(DECIMAL(5, 2), default=0)
    source_order_id = Column(Integer, nullable=True)
    source_order_no = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    material = relationship("Material", foreign_keys=[material_id])
    parent_material = relationship("Material", foreign_keys=[parent_material_id])

class PlannedOrder(Base):
    __tablename__ = "planned_orders"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    planned_no = Column(String(50), unique=True, nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    planned_qty = Column(Integer, nullable=False)
    planned_date = Column(Date, nullable=False)
    order_type = Column(String(20), nullable=False)
    source_type = Column(String(20), nullable=True)
    source_id = Column(Integer, nullable=True)
    status = Column(String(20), default="PENDING")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    material = relationship("Material")

class QualityInspection(Base):
    __tablename__ = "quality_inspections"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    inspection_no = Column(String(50), unique=True, nullable=False)
    source_type = Column(String(20), nullable=False)
    source_id = Column(Integer, nullable=False)
    inspection_date = Column(Date, nullable=False)
    status = Column(String(20), default="PENDING")
    inspector = Column(String(50), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    items = relationship("QualityInspectionItem", back_populates="inspection")

class QualityInspectionItem(Base):
    __tablename__ = "quality_inspection_items"
    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("quality_inspections.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    batch_no = Column(String(50), nullable=True)
    sample_qty = Column(Integer, nullable=False)
    inspected_qty = Column(Integer, default=0)
    qualified_qty = Column(Integer, default=0)
    unqualified_qty = Column(Integer, default=0)
    quality_status = Column(String(20), default="PENDING")
    defect_desc = Column(Text, nullable=True)
    disposal_method = Column(String(100), nullable=True)

    inspection = relationship("QualityInspection", back_populates="items")
    material = relationship("Material")

class OutsourcingRequest(Base):
    __tablename__ = "outsourcing_requests"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    request_no = Column(String(50), unique=True, nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    requested_qty = Column(Integer, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    planned_date = Column(Date, nullable=False)
    status = Column(String(20), default="PENDING")
    planned_order_id = Column(Integer, ForeignKey("planned_orders.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    material = relationship("Material")
    supplier = relationship("Supplier")
    planned_order = relationship("PlannedOrder")

class OutsourcingOrder(Base):
    __tablename__ = "outsourcing_orders"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    order_no = Column(String(50), unique=True, nullable=False)
    request_id = Column(Integer, ForeignKey("outsourcing_requests.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    ordered_qty = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(18, 4), nullable=True)
    planned_date = Column(Date, nullable=False)
    status = Column(String(20), default="PENDING")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    request = relationship("OutsourcingRequest")
    supplier = relationship("Supplier")
    material = relationship("Material")

class OutsourcingIssue(Base):
    __tablename__ = "outsourcing_issues"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    issue_no = Column(String(50), unique=True, nullable=False)
    outsourcing_order_id = Column(Integer, ForeignKey("outsourcing_orders.id"), nullable=False)
    issue_date = Column(Date, nullable=False)
    status = Column(String(20), default="PENDING")
    operator = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    outsourcing_order = relationship("OutsourcingOrder")
    items = relationship("OutsourcingIssueItem", back_populates="issue")

class OutsourcingIssueItem(Base):
    __tablename__ = "outsourcing_issue_items"
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("outsourcing_issues.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    batch_no = Column(String(50), nullable=True)
    location_code = Column(String(50), nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(DECIMAL(18, 4), nullable=True)

    issue = relationship("OutsourcingIssue", back_populates="items")
    material = relationship("Material")

class OutsourcingReplenish(Base):
    __tablename__ = "outsourcing_replenishes"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    replenish_no = Column(String(50), unique=True, nullable=False)
    outsourcing_order_id = Column(Integer, ForeignKey("outsourcing_orders.id"), nullable=False)
    issue_id = Column(Integer, ForeignKey("outsourcing_issues.id"), nullable=True)
    replenish_date = Column(Date, nullable=False)
    status = Column(String(20), default="PENDING")
    operator = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    outsourcing_order = relationship("OutsourcingOrder")
    issue = relationship("OutsourcingIssue")
    items = relationship("OutsourcingReplenishItem", back_populates="replenish")

class OutsourcingReplenishItem(Base):
    __tablename__ = "outsourcing_replenish_items"
    id = Column(Integer, primary_key=True, index=True)
    replenish_id = Column(Integer, ForeignKey("outsourcing_replenishes.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    batch_no = Column(String(50), nullable=True)
    location_code = Column(String(50), nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(DECIMAL(18, 4), nullable=True)

    replenish = relationship("OutsourcingReplenish", back_populates="items")
    material = relationship("Material")

class OutsourcingReturn(Base):
    __tablename__ = "outsourcing_returns"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    return_no = Column(String(50), unique=True, nullable=False)
    outsourcing_order_id = Column(Integer, ForeignKey("outsourcing_orders.id"), nullable=False)
    issue_id = Column(Integer, ForeignKey("outsourcing_issues.id"), nullable=True)
    return_date = Column(Date, nullable=False)
    status = Column(String(20), default="PENDING")
    return_reason = Column(Text, nullable=True)
    operator = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    outsourcing_order = relationship("OutsourcingOrder")
    issue = relationship("OutsourcingIssue")
    items = relationship("OutsourcingReturnItem", back_populates="return_order")

class OutsourcingReturnItem(Base):
    __tablename__ = "outsourcing_return_items"
    id = Column(Integer, primary_key=True, index=True)
    return_id = Column(Integer, ForeignKey("outsourcing_returns.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    batch_no = Column(String(50), nullable=True)
    location_code = Column(String(50), nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(DECIMAL(18, 4), nullable=True)

    return_order = relationship("OutsourcingReturn", back_populates="items")
    material = relationship("Material")

class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    request_no = Column(String(50), unique=True, nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    requested_qty = Column(Integer, nullable=False)
    required_date = Column(Date, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    status = Column(String(20), default="PENDING")
    planned_order_id = Column(Integer, ForeignKey("planned_orders.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    material = relationship("Material")
    supplier = relationship("Supplier")
    planned_order = relationship("PlannedOrder")


# ==================== 采购管理 V2 扩展 ====================

class PurchaseSuggestion(Base):
    """采购建议：MRP/备库/手工产生的待处理采购需求"""
    __tablename__ = "purchase_suggestions"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    suggestion_no = Column(String(50), unique=True, nullable=False, index=True)
    source_type = Column(String(20), nullable=False)  # MRP / STOCK / MANUAL
    source_no = Column(String(50), nullable=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    material_spec = Column(String(200), nullable=True)
    requested_qty = Column(DECIMAL(18, 4), nullable=False)
    suggested_qty = Column(DECIMAL(18, 4), nullable=False)
    unit = Column(String(20), nullable=True)
    expected_date = Column(Date, nullable=True)
    status = Column(String(20), default="PENDING")
    converted_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    material = relationship("Material")
    purchase_order = relationship("PurchaseOrder")
    account_set = relationship("AccountSet")


class SupplierEvaluation(Base):
    """供应商评估"""
    __tablename__ = "supplier_evaluations"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    period_month = Column(String(7), nullable=False)
    price_score = Column(DECIMAL(3, 1), default=3)
    on_time_score = Column(DECIMAL(3, 1), default=3)
    quality_score = Column(DECIMAL(3, 1), default=3)
    cooperation_score = Column(DECIMAL(3, 1), default=3)
    composite_score = Column(DECIMAL(4, 2), default=0)
    rank_level = Column(String(10), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    supplier = relationship("Supplier")
    account_set = relationship("AccountSet")


class PurchaseQuotation(Base):
    """采购询价单"""
    __tablename__ = "purchase_quotations"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    quotation_no = Column(String(50), unique=True, nullable=False, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    material_spec = Column(String(200), nullable=True)
    quantity = Column(DECIMAL(18, 4), nullable=False)
    expected_date = Column(Date, nullable=True)
    status = Column(String(20), default="DRAFT")
    winner_supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    material = relationship("Material")
    winner_supplier = relationship("Supplier", foreign_keys=[winner_supplier_id])
    account_set = relationship("AccountSet")


class PurchaseQuotationReply(Base):
    """询价回复"""
    __tablename__ = "purchase_quotation_replies"
    id = Column(Integer, primary_key=True, index=True)
    quotation_id = Column(Integer, ForeignKey("purchase_quotations.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    unit_price = Column(DECIMAL(18, 4), nullable=False)
    lead_time_days = Column(Integer, nullable=True)
    reply_date = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    is_selected = Column(Boolean, default=False)

    quotation = relationship("PurchaseQuotation")
    supplier = relationship("Supplier")


class PurchaseInbound(Base):
    """采购入库单"""
    __tablename__ = "purchase_inbounds"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    inbound_no = Column(String(50), unique=True, nullable=False, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    ordered_qty = Column(DECIMAL(18, 4), nullable=False)
    received_qty = Column(DECIMAL(18, 4), nullable=False)
    unit_price = Column(DECIMAL(18, 4), nullable=False)
    amount = Column(DECIMAL(18, 2), nullable=False)
    tax_rate = Column(DECIMAL(5, 2), nullable=True)
    difference_type = Column(String(20), nullable=True)
    quality_status = Column(String(20), default="PENDING")
    warehouse_id = Column(Integer, nullable=True)
    inbound_date = Column(Date, nullable=False)
    operator = Column(String(50), nullable=True)
    status = Column(String(20), default="DRAFT")
    has_invoice = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    purchase_order = relationship("PurchaseOrder")
    supplier = relationship("Supplier")
    material = relationship("Material")
    account_set = relationship("AccountSet")


class PurchaseCommunication(Base):
    """采购订单沟通记录"""
    __tablename__ = "purchase_communications"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    contact_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    communicator = Column(String(50), nullable=True)
    communication_date = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    purchase_order = relationship("PurchaseOrder")
    account_set = relationship("AccountSet")


class PurchaseArrivalNotice(Base):
    """到货通知"""
    __tablename__ = "purchase_arrival_notices"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    notice_no = Column(String(50), unique=True, nullable=False)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    expected_date = Column(Date, nullable=False)
    actual_date = Column(Date, nullable=True)
    status = Column(String(20), default="PENDING")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    purchase_order = relationship("PurchaseOrder")
    supplier = relationship("Supplier")
    account_set = relationship("AccountSet")

class OutsourcingReceive(Base):
    __tablename__ = "outsourcing_receives"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    receive_no = Column(String(50), unique=True, nullable=False)
    outsourcing_order_id = Column(Integer, ForeignKey("outsourcing_orders.id"), nullable=False)
    expected_arrival_date = Column(Date, nullable=True)
    actual_arrival_date = Column(Date, nullable=True)
    status = Column(String(20), default="PENDING")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    outsourcing_order = relationship("OutsourcingOrder")
    items = relationship("OutsourcingReceiveItem", back_populates="receive")

class OutsourcingReceiveItem(Base):
    __tablename__ = "outsourcing_receive_items"
    id = Column(Integer, primary_key=True, index=True)
    receive_id = Column(Integer, ForeignKey("outsourcing_receives.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    expected_qty = Column(Integer, nullable=False)
    actual_qty = Column(Integer, nullable=True)
    unit_price = Column(DECIMAL(18, 4), nullable=True)
    batch_no = Column(String(50), nullable=True)
    expiry_date = Column(Date, nullable=True)
    location_code = Column(String(50), nullable=True)

    receive = relationship("OutsourcingReceive", back_populates="items")
    material = relationship("Material")

class OutsourcingInvoice(Base):
    __tablename__ = "outsourcing_invoices"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    invoice_no = Column(String(50), unique=True, nullable=False)
    outsourcing_order_id = Column(Integer, ForeignKey("outsourcing_orders.id"), nullable=True)
    receive_id = Column(Integer, ForeignKey("outsourcing_receives.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    amount = Column(DECIMAL(18, 2), nullable=False)
    tax_amount = Column(DECIMAL(18, 2), nullable=True)
    total_amount = Column(DECIMAL(18, 2), nullable=False)
    invoice_date = Column(Date, nullable=False)
    status = Column(String(20), default="PENDING")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    outsourcing_order = relationship("OutsourcingOrder")
    receive = relationship("OutsourcingReceive")
    supplier = relationship("Supplier")

class OutsourcingEstimate(Base):
    __tablename__ = "outsourcing_estimates"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    estimate_no = Column(String(50), unique=True, nullable=False)
    receive_id = Column(Integer, ForeignKey("outsourcing_receives.id"), nullable=False)
    outsourcing_order_id = Column(Integer, ForeignKey("outsourcing_orders.id"), nullable=True)
    estimated_amount = Column(DECIMAL(18, 4), nullable=False)
    status = Column(String(20), default="PENDING")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    receive = relationship("OutsourcingReceive")
    outsourcing_order = relationship("OutsourcingOrder")
    items = relationship("OutsourcingEstimateItem", back_populates="estimate")

class OutsourcingEstimateItem(Base):
    __tablename__ = "outsourcing_estimate_items"
    id = Column(Integer, primary_key=True, index=True)
    estimate_id = Column(Integer, ForeignKey("outsourcing_estimates.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    estimated_unit_cost = Column(DECIMAL(18, 4), nullable=False)
    estimated_total_cost = Column(DECIMAL(18, 4), nullable=False)

    estimate = relationship("OutsourcingEstimate", back_populates="items")
    material = relationship("Material")

class OutsourcingAccount(Base):
    __tablename__ = "outsourcing_accounts"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    account_no = Column(String(50), unique=True, nullable=False)
    estimate_id = Column(Integer, ForeignKey("outsourcing_estimates.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("outsourcing_invoices.id"), nullable=True)
    receive_id = Column(Integer, ForeignKey("outsourcing_receives.id"), nullable=True)
    actual_amount = Column(DECIMAL(18, 4), nullable=False)
    estimated_amount = Column(DECIMAL(18, 4), nullable=False)
    variance_amount = Column(DECIMAL(18, 4), default=0)
    status = Column(String(20), default="PENDING")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    estimate = relationship("OutsourcingEstimate")
    invoice = relationship("OutsourcingInvoice")
    receive = relationship("OutsourcingReceive")


# ============================================================
# 自动凭证系统：凭证模板 + 自动生成的凭证
# ============================================================
class VoucherTemplate(Base):
    """凭证生成规则模板：定义业务单据类型 → 借贷科目映射"""
    __tablename__ = "voucher_templates"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    template_code = Column(String(50), unique=True, nullable=False)
    template_name = Column(String(100), nullable=False)
    doc_type = Column(String(50), nullable=False)  # INBOUND/PURCHASE_INVOICE/SALES_OUTBOUND/SALES_INVOICE/RECEIPT/PAYMENT/PROD_PICK/PROD_COMPLETE/INVENTORY_PROFIT/INVENTORY_LOSS
    description = Column(Text, nullable=True)
    # 借贷映射定义（JSON格式）
    # 示例：[{"side":"debit","account":"原材料","account_field":"inventory_account_code","summary":"{doc_no} 入库 {supplier}"}, ...]
    debit_rules = Column(Text, nullable=False)  # JSON
    credit_rules = Column(Text, nullable=False)  # JSON
    summary_template = Column(String(200), nullable=True)  # 摘要模板，如 "{doc_type} {doc_no} {counterparty}"
    enabled = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)  # 系统内置模板不可删除
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")


# ============================================================
# 📦 生产单据体系（Production Docs）
# 核心思想：单据流转，而非模块堆砌
# 8种单据：工单/组件清单/工序计划/领料/退料/补料/完工入库/完工退库
# 通过 document_links 通用关系表实现下推与双向追溯
# ============================================================

class ProdDocStatus(PyEnum):
    """生产单据状态"""
    DRAFT = "草稿"
    CONFIRMED = "已确认"
    RELEASED = "已下达"
    IN_PROGRESS = "生产中"
    COMPLETED = "已完工"
    CLOSED = "已关闭"
    CANCELLED = "已取消"


class ProdDocType(PyEnum):
    """生产单据类型"""
    WORK_ORDER = "生产工单"
    COMPONENT_LIST = "组件清单"
    PROCESS_PLAN = "工序计划"
    PICK = "生产领料单"
    MATERIAL_RETURN = "生产退料单"
    REPLENISH = "生产补料单"
    INBOUND = "完工入库单"
    RETURN_INBOUND = "完工退库单"


class ProductionWorkOrderDoc(Base):
    """生产工单（核心单据，发起整个生产流程）"""
    __tablename__ = "prod_doc_work_orders"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    doc_no = Column(String(50), unique=True, nullable=False)  # 工单号
    product_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    product_code = Column(String(50), nullable=True)
    product_name = Column(String(200), nullable=True)
    planned_qty = Column(DECIMAL(18, 4), nullable=False, default=0)  # 计划产量
    completed_qty = Column(DECIMAL(18, 4), nullable=False, default=0)  # 已完工入库数量（回写）
    issued_qty = Column(DECIMAL(18, 4), nullable=False, default=0)  # 已领料数量（回写）
    status = Column(Enum(ProdDocStatus), nullable=False, default=ProdDocStatus.DRAFT)
    planned_start = Column(Date, nullable=True)
    planned_end = Column(Date, nullable=True)
    actual_start = Column(Date, nullable=True)
    actual_end = Column(Date, nullable=True)
    workshop = Column(String(100), nullable=True)  # 车间/工作中心
    priority = Column(String(20), nullable=True, default="normal")  # normal/high/urgent
    remark = Column(Text, nullable=True)
    created_by = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    product = relationship("Material")


class ProductionComponentList(Base):
    """组件清单（BOM快照，工单下达时自动生成）"""
    __tablename__ = "prod_doc_component_lists"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    doc_no = Column(String(50), unique=True, nullable=False)
    work_order_id = Column(Integer, ForeignKey("prod_doc_work_orders.id"), nullable=True)
    work_order_no = Column(String(50), nullable=True)
    product_name = Column(String(200), nullable=True)
    items_json = Column(Text, nullable=True)  # 组件明细JSON
    status = Column(Enum(ProdDocStatus), nullable=False, default=ProdDocStatus.CONFIRMED)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    work_order = relationship("ProductionWorkOrderDoc")


class ProductionProcessPlan(Base):
    """工序计划（工单下达时自动生成）"""
    __tablename__ = "prod_doc_process_plans"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    doc_no = Column(String(50), unique=True, nullable=False)
    work_order_id = Column(Integer, ForeignKey("prod_doc_work_orders.id"), nullable=True)
    work_order_no = Column(String(50), nullable=True)
    product_name = Column(String(200), nullable=True)
    steps_json = Column(Text, nullable=True)  # 工序明细JSON
    status = Column(Enum(ProdDocStatus), nullable=False, default=ProdDocStatus.CONFIRMED)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    work_order = relationship("ProductionWorkOrderDoc")


class ProductionPick(Base):
    """生产领料单"""
    __tablename__ = "prod_doc_picks"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    doc_no = Column(String(50), unique=True, nullable=False)
    work_order_id = Column(Integer, ForeignKey("prod_doc_work_orders.id"), nullable=True)
    work_order_no = Column(String(50), nullable=True)
    pick_date = Column(Date, nullable=True)
    items_json = Column(Text, nullable=True)  # 领料明细JSON
    status = Column(Enum(ProdDocStatus), nullable=False, default=ProdDocStatus.DRAFT)
    warehouse = Column(String(100), nullable=True)
    remark = Column(Text, nullable=True)
    created_by = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    work_order = relationship("ProductionWorkOrderDoc")


class ProductionMaterialReturn(Base):
    """生产退料单"""
    __tablename__ = "prod_doc_material_returns"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    doc_no = Column(String(50), unique=True, nullable=False)
    pick_id = Column(Integer, ForeignKey("prod_doc_picks.id"), nullable=True)
    pick_no = Column(String(50), nullable=True)
    work_order_id = Column(Integer, ForeignKey("prod_doc_work_orders.id"), nullable=True)
    work_order_no = Column(String(50), nullable=True)
    return_date = Column(Date, nullable=True)
    items_json = Column(Text, nullable=True)
    status = Column(Enum(ProdDocStatus), nullable=False, default=ProdDocStatus.DRAFT)
    warehouse = Column(String(100), nullable=True)
    remark = Column(Text, nullable=True)
    created_by = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    pick = relationship("ProductionPick")
    work_order = relationship("ProductionWorkOrderDoc")


class ProductionReplenish(Base):
    """生产补料单"""
    __tablename__ = "prod_doc_replenishes"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    doc_no = Column(String(50), unique=True, nullable=False)
    work_order_id = Column(Integer, ForeignKey("prod_doc_work_orders.id"), nullable=True)
    work_order_no = Column(String(50), nullable=True)
    replenish_date = Column(Date, nullable=True)
    items_json = Column(Text, nullable=True)
    status = Column(Enum(ProdDocStatus), nullable=False, default=ProdDocStatus.DRAFT)
    warehouse = Column(String(100), nullable=True)
    reason = Column(String(200), nullable=True)
    remark = Column(Text, nullable=True)
    created_by = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    work_order = relationship("ProductionWorkOrderDoc")


class ProductionInbound(Base):
    """完工入库单"""
    __tablename__ = "prod_doc_inbounds"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    doc_no = Column(String(50), unique=True, nullable=False)
    work_order_id = Column(Integer, ForeignKey("prod_doc_work_orders.id"), nullable=True)
    work_order_no = Column(String(50), nullable=True)
    product_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    product_name = Column(String(200), nullable=True)
    inbound_date = Column(Date, nullable=True)
    qty = Column(DECIMAL(18, 4), nullable=False, default=0)
    qualified_qty = Column(DECIMAL(18, 4), nullable=False, default=0)
    defective_qty = Column(DECIMAL(18, 4), nullable=False, default=0)
    warehouse = Column(String(100), nullable=True)
    location = Column(String(100), nullable=True)
    status = Column(Enum(ProdDocStatus), nullable=False, default=ProdDocStatus.DRAFT)
    remark = Column(Text, nullable=True)
    created_by = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    work_order = relationship("ProductionWorkOrderDoc")
    product = relationship("Material")


class ProductionReturnInbound(Base):
    """完工退库单"""
    __tablename__ = "prod_doc_return_inbounds"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    doc_no = Column(String(50), unique=True, nullable=False)
    inbound_id = Column(Integer, ForeignKey("prod_doc_inbounds.id"), nullable=True)
    inbound_no = Column(String(50), nullable=True)
    work_order_id = Column(Integer, ForeignKey("prod_doc_work_orders.id"), nullable=True)
    work_order_no = Column(String(50), nullable=True)
    return_date = Column(Date, nullable=True)
    qty = Column(DECIMAL(18, 4), nullable=False, default=0)
    reason = Column(String(200), nullable=True)
    status = Column(Enum(ProdDocStatus), nullable=False, default=ProdDocStatus.DRAFT)
    remark = Column(Text, nullable=True)
    created_by = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    inbound = relationship("ProductionInbound")
    work_order = relationship("ProductionWorkOrderDoc")


class DocumentLink(Base):
    """通用单据关系表：支持所有单据类型之间的下推、自动生成、追溯"""
    __tablename__ = "prod_document_links"
    id = Column(Integer, primary_key=True, index=True)
    source_doc_type = Column(String(50), nullable=False)
    source_doc_id = Column(Integer, nullable=False)
    source_doc_no = Column(String(50), nullable=True)
    target_doc_type = Column(String(50), nullable=False)
    target_doc_id = Column(Integer, nullable=False)
    target_doc_no = Column(String(50), nullable=True)
    link_type = Column(String(20), nullable=False, default="push")  # auto/push
    is_reverse = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)


class AutoVoucher(Base):
    """自动生成的凭证草稿"""
    __tablename__ = "auto_vouchers"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    voucher_no = Column(String(50), nullable=False)  # 如：记-202607-001
    voucher_date = Column(Date, nullable=False)
    status = Column(String(20), default="DRAFT")  # DRAFT/PENDING/APPROVED/POSTED/REJECTED
    source_doc_type = Column(String(50), nullable=False)  # 来源单据类型
    source_doc_id = Column(Integer, nullable=False)  # 来源单据ID
    source_doc_no = Column(String(50), nullable=True)  # 来源单据编号
    summary = Column(String(300), nullable=True)  # 凭证摘要
    template_code = Column(String(50), nullable=True)  # 使用的模板
    total_debit = Column(DECIMAL(18, 2), default=0)
    total_credit = Column(DECIMAL(18, 2), default=0)
    error_message = Column(Text, nullable=True)  # 异常信息
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String(50), nullable=True)
    reject_reason = Column(Text, nullable=True)

    account_set = relationship("AccountSet")
    entries = relationship("AutoVoucherEntry", back_populates="auto_voucher", cascade="all, delete-orphan")


class AutoVoucherEntry(Base):
    """自动凭证明细分录"""
    __tablename__ = "auto_voucher_entries"
    id = Column(Integer, primary_key=True, index=True)
    auto_voucher_id = Column(Integer, ForeignKey("auto_vouchers.id"), nullable=False)
    account_code = Column(String(50), nullable=False)
    account_name = Column(String(100), nullable=False)
    side = Column(String(10), nullable=False)  # debit/credit
    amount = Column(DECIMAL(18, 2), nullable=False)
    summary = Column(String(200), nullable=True)
    # 辅助核算
    customer_id = Column(Integer, nullable=True)
    supplier_id = Column(Integer, nullable=True)
    department_id = Column(Integer, nullable=True)
    work_order_id = Column(Integer, nullable=True)
    material_id = Column(Integer, nullable=True)
    employee_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    auto_voucher = relationship("AutoVoucher", back_populates="entries")


# ============================================================
# 模块1：基础设置 — 会计科目表、编码规则、会计期间
# ============================================================

class AccountingSubject(Base):
    """会计科目表"""
    __tablename__ = "accounting_subjects"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    parent_code = Column(String(50), nullable=True)
    level = Column(Integer, default=1)
    category = Column(String(20), nullable=False)  # ASSET/LIABILITY/EQUITY/REVENUE/EXPENSE/COST
    balance_direction = Column(String(10), default="DEBIT")  # DEBIT/CREDIT
    is_leaf = Column(Boolean, default=True)
    opening_balance = Column(DECIMAL(18, 2), default=0)
    current_balance = Column(DECIMAL(18, 2), default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")


class CodingRule(Base):
    """编码规则配置"""
    __tablename__ = "coding_rules"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    entity_type = Column(String(30), nullable=False)  # MATERIAL/SUPPLIER/CUSTOMER/PO/SO/WO/VOUCHER
    prefix = Column(String(20), nullable=True)
    date_format = Column(String(20), nullable=True)  # YYYYMMDD/YYYYMM/none
    seq_length = Column(Integer, default=4)
    reset_cycle = Column(String(20), default="YEARLY")  # YEARLY/MONTHLY/DAILY/NEVER
    separator = Column(String(5), default="-")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)


class AccountingPeriod(Base):
    """会计期间"""
    __tablename__ = "accounting_periods"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    period_code = Column(String(10), nullable=False)  # 2026-08
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), default="OPEN")  # OPEN/CLOSED
    closed_at = Column(DateTime, nullable=True)
    closed_by = Column(String(50), nullable=True)


class Role(Base):
    """角色"""
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=True)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(Text, nullable=True)  # JSON string
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)


class OperationLog(Base):
    """操作日志审计"""
    __tablename__ = "operation_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String(50), nullable=True)
    module = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    target_type = Column(String(50), nullable=True)
    target_id = Column(String(50), nullable=True)
    detail = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)


# ============================================================
# 模块3：销售管理 — 报价、退货、应收、收款
# ============================================================

class SalesQuotation(Base):
    """销售报价单"""
    __tablename__ = "sales_quotations"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    quotation_no = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    quotation_date = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=True)
    currency = Column(String(10), default="CNY")
    exchange_rate = Column(DECIMAL(10, 4), default=1.0)
    status = Column(String(20), default="DRAFT")  # DRAFT/SENT/ACCEPTED/REJECTED/EXPIRED
    total_amount = Column(DECIMAL(18, 4), default=0)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    customer = relationship("Customer")
    items = relationship("SalesQuotationItem", back_populates="quotation")


class SalesQuotationItem(Base):
    """销售报价单明细"""
    __tablename__ = "sales_quotation_items"
    id = Column(Integer, primary_key=True, index=True)
    quotation_id = Column(Integer, ForeignKey("sales_quotations.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity = Column(DECIMAL(18, 4), nullable=False)
    unit_price = Column(DECIMAL(18, 4), nullable=False)
    amount = Column(DECIMAL(18, 4), nullable=False)
    price_type = Column(String(20), nullable=True)
    remark = Column(Text, nullable=True)

    quotation = relationship("SalesQuotation", back_populates="items")
    material = relationship("Material")


class SalesReturn(Base):
    """销售退货单"""
    __tablename__ = "sales_returns"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    return_no = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    sales_order_id = Column(Integer, ForeignKey("sales_orders.id"), nullable=True)
    outbound_id = Column(Integer, ForeignKey("sales_outbound.id"), nullable=True)
    return_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default="PENDING")  # PENDING/INSPECTING/ACCEPTED/REJECTED
    total_amount = Column(DECIMAL(18, 4), default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    customer = relationship("Customer")
    items = relationship("SalesReturnItem", back_populates="sales_return")


class SalesReturnItem(Base):
    """销售退货单明细"""
    __tablename__ = "sales_return_items"
    id = Column(Integer, primary_key=True, index=True)
    return_id = Column(Integer, ForeignKey("sales_returns.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity = Column(DECIMAL(18, 4), nullable=False)
    unit_price = Column(DECIMAL(18, 4), nullable=False)
    amount = Column(DECIMAL(18, 4), nullable=False)
    reason = Column(Text, nullable=True)

    sales_return = relationship("SalesReturn", back_populates="items")
    material = relationship("Material")


class Receivable(Base):
    """应收单"""
    __tablename__ = "receivables"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    receivable_no = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    source_type = Column(String(30), nullable=False)  # SALES_OUTBOUND/SALES_ORDER
    source_no = Column(String(50), nullable=True)
    amount = Column(DECIMAL(18, 2), nullable=False)
    received_amount = Column(DECIMAL(18, 2), default=0)
    balance = Column(DECIMAL(18, 2), nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(String(20), default="PENDING")  # PENDING/PARTIAL/SETTLED/OVERDUE
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    customer = relationship("Customer")


class Receipt(Base):
    """收款单"""
    __tablename__ = "receipts"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    receipt_no = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    receipt_date = Column(Date, nullable=False)
    amount = Column(DECIMAL(18, 2), nullable=False)
    payment_method = Column(String(30), nullable=True)  # CASH/BANK/ALIPAY/WECHAT
    receivable_id = Column(Integer, ForeignKey("receivables.id"), nullable=True)
    remark = Column(Text, nullable=True)
    status = Column(String(20), default="CONFIRMED")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    customer = relationship("Customer")
    receivable = relationship("Receivable")


# ============================================================
# 模块4：库存管理 — 仓库、库位、呆滞库存
# ============================================================

class Warehouse(Base):
    """仓库"""
    __tablename__ = "warehouses"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    # 工程导向型：仓库类型 RAW原材料仓 / SEMI半成品仓 / FINISHED成品仓 / PROJECT_SITE项目现场仓
    warehouse_type = Column(String(30), default="RAW")
    address = Column(Text, nullable=True)
    manager = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    # 基础数据：盘点周期 / 库位编码规则（如 A-{货架}-{层}）
    stocktake_cycle = Column(String(20), nullable=True)
    location_rule = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)


class CostItem(Base):
    """成本项目（财务中心基础数据：要素费用 + 成本分配标准）"""
    __tablename__ = "cost_items"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    # 要素费用：直接材料 / 直接人工 / 制造费用 / 其他
    cost_element = Column(String(20), default="OVERHEAD")
    # 成本分配标准：按工时 / 按产量 / 按材料 / 不分配
    allocation_basis = Column(String(20), default="MANUAL")
    is_active = Column(Boolean, default=True)
    remark = Column(String(200), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)


class InventoryBatch(Base):
    """库存批次管理（工程导向型：批次追溯）"""
    __tablename__ = "inventory_batches"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    batch_no = Column(String(50), nullable=False, index=True)  # 批次号
    quantity = Column(DECIMAL(18, 4), nullable=False, default=0)
    unit_cost = Column(DECIMAL(18, 4), default=0)
    total_cost = Column(DECIMAL(18, 4), default=0)
    production_date = Column(Date, nullable=True)  # 生产日期
    expiry_date = Column(Date, nullable=True)  # 有效期
    inbound_date = Column(Date, nullable=True)  # 入库日期
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("wbs_projects.id"), nullable=True)  # 关联项目（现场仓批次）
    source_doc_no = Column(String(100), nullable=True)  # 来源单据号
    status = Column(String(20), default="NORMAL")  # NORMAL/LOCKED/EXPIRED/USED
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    material = relationship("Material")
    warehouse = relationship("Warehouse")


class SlowMovingInventory(Base):
    """呆滞库存"""
    __tablename__ = "slow_moving_inventories"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    last_move_date = Column(Date, nullable=True)
    days_idle = Column(Integer, default=0)
    quantity = Column(DECIMAL(18, 4), default=0)
    value = Column(DECIMAL(18, 4), default=0)
    status = Column(String(20), default="PENDING")  # PENDING/PROCESSING/RESOLVED
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    material = relationship("Material")


# ============================================================
# 模块5：生产管理 — 工艺路线、领料、报工
# ============================================================

class Routing(Base):
    """工艺路线"""
    __tablename__ = "routings"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    name = Column(String(100), nullable=False)
    version = Column(String(20), default="V1")
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    product = relationship("Material")
    operations = relationship("RoutingOperation", back_populates="routing")


class RoutingOperation(Base):
    """工艺路线工序"""
    __tablename__ = "routing_operations"
    id = Column(Integer, primary_key=True, index=True)
    routing_id = Column(Integer, ForeignKey("routings.id"), nullable=False)
    sequence = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    standard_time = Column(DECIMAL(10, 2), nullable=False)  # 标准工时(分钟)
    equipment = Column(String(100), nullable=True)
    work_center = Column(String(50), nullable=True)
    labor_type = Column(String(50), nullable=True)

    routing = relationship("Routing", back_populates="operations")


class MaterialRequisition(Base):
    """生产领料单"""
    __tablename__ = "material_requisitions"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    requisition_no = Column(String(50), unique=True, nullable=False)
    work_order_id = Column(Integer, ForeignKey("production_workorders.id"), nullable=False)
    requisition_date = Column(Date, nullable=False)
    status = Column(String(20), default="PENDING")  # PENDING/APPROVED/ISSUED/CANCELLED
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    work_order = relationship("ProductionWorkOrder")
    items = relationship("MaterialRequisitionItem", back_populates="requisition")


class MaterialRequisitionItem(Base):
    """领料单明细"""
    __tablename__ = "material_requisition_items"
    id = Column(Integer, primary_key=True, index=True)
    requisition_id = Column(Integer, ForeignKey("material_requisitions.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    required_qty = Column(DECIMAL(18, 4), nullable=False)
    issued_qty = Column(DECIMAL(18, 4), default=0)
    unit_cost = Column(DECIMAL(18, 4), nullable=True)
    location_code = Column(String(50), nullable=True)
    batch_no = Column(String(50), nullable=True)

    requisition = relationship("MaterialRequisition", back_populates="items")
    material = relationship("Material")


class WorkReport(Base):
    """工序报工单"""
    __tablename__ = "work_reports"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    report_no = Column(String(50), unique=True, nullable=False)
    work_order_id = Column(Integer, ForeignKey("production_workorders.id"), nullable=False)
    routing_operation_id = Column(Integer, ForeignKey("routing_operations.id"), nullable=True)
    worker = Column(String(50), nullable=False)
    report_date = Column(Date, nullable=False)
    completed_qty = Column(Integer, default=0)
    qualified_qty = Column(Integer, default=0)
    defective_qty = Column(Integer, default=0)
    actual_time = Column(DECIMAL(10, 2), nullable=True)  # 实际工时(分钟)
    status = Column(String(20), default="SUBMITTED")
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    work_order = relationship("ProductionWorkOrder")


# ============================================================
# 模块6：财务管理 — 期末处理
# ============================================================

class PeriodClosing(Base):
    """期末处理记录"""
    __tablename__ = "period_closings"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    period_code = Column(String(10), nullable=False)
    closing_type = Column(String(30), nullable=False)  # FOREX/PNL_SETTLE/CLOSE
    status = Column(String(20), default="PENDING")  # PENDING/COMPLETED
    voucher_no = Column(String(50), nullable=True)
    operated_by = Column(String(50), nullable=True)
    operated_at = Column(DateTime, nullable=True)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)


# ============================================================
# 模块7：成本会计 — 标准成本、差异分析
# ============================================================

class CostStandard(Base):
    """标准成本"""
    __tablename__ = "cost_standards"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    standard_material_cost = Column(DECIMAL(18, 4), default=0)
    standard_labor_cost = Column(DECIMAL(18, 4), default=0)
    standard_overhead_cost = Column(DECIMAL(18, 4), default=0)
    standard_total_cost = Column(DECIMAL(18, 4), default=0)
    effective_date = Column(Date, nullable=False)
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)


class CostVariance(Base):
    """成本差异分析"""
    __tablename__ = "cost_variances"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    work_order_id = Column(Integer, ForeignKey("production_workorders.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    variance_type = Column(String(30), nullable=False)  # MATERIAL/LABOR/OVERHEAD
    standard_cost = Column(DECIMAL(18, 4), nullable=False)
    actual_cost = Column(DECIMAL(18, 4), nullable=False)
    variance_amount = Column(DECIMAL(18, 4), nullable=False)
    variance_rate = Column(DECIMAL(5, 2), nullable=True)
    analysis = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)


# ============================================================
# 模块9：经济法合规 — 发票校验
# ============================================================

class InvoiceCheck(Base):
    """发票合规性校验"""
    __tablename__ = "invoice_checks"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    invoice_no = Column(String(50), nullable=False)
    invoice_type = Column(String(30), nullable=False)  # PURCHASE/SALES
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    invoice_date = Column(Date, nullable=False)
    amount = Column(DECIMAL(18, 2), nullable=False)
    tax_amount = Column(DECIMAL(18, 2), nullable=False)
    tax_rate = Column(DECIMAL(5, 2), nullable=True)
    input_tax_rate = Column(DECIMAL(5, 2), nullable=True)
    output_tax_rate = Column(DECIMAL(5, 2), nullable=True)
    tax_rate_diff = Column(DECIMAL(5, 2), nullable=True)
    is_deductible = Column(Boolean, default=True)
    check_result = Column(String(50), nullable=True)
    warning_msg = Column(Text, nullable=True)
    status = Column(String(20), default="CHECKED")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)


class ImportedFinancialStatement(Base):
    """导入的外部财务报表数据（利润表/资产负债表/现金流量表）
    来源：用户上传 Excel/HTML 报表，系统自动解析关键指标后存储
    statement_type: PL(利润表)/BS(资产负债表)/CF(现金流量表)
    """
    __tablename__ = "imported_financials"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    company_name = Column(String(200), nullable=True)
    statement_type = Column(String(20), nullable=False)  # PL/BS/CF
    period = Column(String(20), nullable=True)  # 报表期间，如 20241231
    item_code = Column(String(50), nullable=True)
    item_name = Column(String(100), nullable=False)
    amount = Column(DECIMAL(20, 2), nullable=False, default=0)
    unit = Column(String(10), nullable=True, default="元")
    remark = Column(String(200), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)


# ============================================================
# 模块10：报表与分析 — 自定义报表、仪表盘
# ============================================================

class CustomReport(Base):
    """自定义报表"""
    __tablename__ = "custom_reports"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    data_source = Column(String(50), nullable=False)  # PURCHASE/SALES/INVENTORY/PRODUCTION/FINANCE
    filter_config = Column(Text, nullable=True)  # JSON
    dimension_config = Column(Text, nullable=True)  # JSON
    display_config = Column(Text, nullable=True)  # JSON
    creator = Column(String(50), nullable=True)
    is_shared = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class DashboardConfig(Base):
    """管理驾驶舱配置"""
    __tablename__ = "dashboard_configs"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    user_id = Column(Integer, nullable=True)
    name = Column(String(100), nullable=False)
    widgets = Column(Text, nullable=True)  # JSON array of widget configs
    layout = Column(Text, nullable=True)  # JSON layout
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)


# =============== 工程导向型专属模型 ===============

class ECOChangeOrder(Base):
    """ECO工程变更单：变更申请→审批→BOM版本升级→影响分析"""
    __tablename__ = "eco_change_orders"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    eco_no = Column(String(50), unique=True, nullable=False)
    product_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    product_name = Column(String(200), nullable=True)
    old_bom_id = Column(Integer, ForeignKey("boms.id"), nullable=True)
    old_version = Column(String(20), nullable=True)
    change_type = Column(String(30), nullable=False, default="material_substitute")
    change_reason = Column(Text, nullable=True)
    change_content = Column(Text, nullable=True)
    impact_analysis = Column(Text, nullable=True)
    status = Column(String(20), default="DRAFT")
    requested_by = Column(String(50), nullable=True)
    approved_by = Column(String(50), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    effective_date = Column(Date, nullable=True)
    new_bom_id = Column(Integer, ForeignKey("boms.id"), nullable=True)
    new_version = Column(String(20), nullable=True)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    product = relationship("Material")
    old_bom = relationship("BOM", foreign_keys=[old_bom_id])
    new_bom = relationship("BOM", foreign_keys=[new_bom_id])


class WBSProject(Base):
    """WBS项目：工程型项目制管理"""
    __tablename__ = "wbs_projects"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    project_no = Column(String(50), unique=True, nullable=False)
    project_name = Column(String(200), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    customer_name = Column(String(100), nullable=True)
    contract_amount = Column(DECIMAL(18, 2), nullable=False, default=0)
    currency = Column(String(10), default="CNY")
    delivery_mode = Column(String(20), default="MTO")  # MTS/MTO/ATO/ETO
    budget_cost = Column(DECIMAL(18, 2), nullable=False, default=0)
    incurred_cost = Column(DECIMAL(18, 2), nullable=False, default=0)
    # 自动归集成本（来源于已过账凭证）：直接材料 + 分摊制造费用
    material_cost = Column(DECIMAL(18, 2), nullable=False, default=0)   # 直接材料成本
    overhead_cost = Column(DECIMAL(18, 2), nullable=False, default=0)   # 分摊制造费用（水电等车间共同费用）
    net_profit = Column(DECIMAL(18, 2), nullable=False, default=0)      # 净利润 = 合同额 - 已发生成本
    gross_margin = Column(DECIMAL(6, 2), nullable=False, default=0)     # 毛利率% = 净利润 / 合同额
    estimated_total_cost = Column(DECIMAL(18, 2), nullable=False, default=0)
    progress_pct = Column(DECIMAL(5, 2), nullable=False, default=0)
    recognized_revenue = Column(DECIMAL(18, 2), nullable=False, default=0)
    status = Column(String(20), default="PLANNING")
    planned_start = Column(Date, nullable=True)
    planned_end = Column(Date, nullable=True)
    actual_start = Column(Date, nullable=True)
    actual_end = Column(Date, nullable=True)
    manager = Column(String(50), nullable=True)
    # 业务模式：A=大批量单品种(批次项目) / B=小批量多品种(合同项目)
    business_mode = Column(String(10), default="B")
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    customer = relationship("Customer")
    wbs_nodes = relationship("WBSNode", back_populates="project", cascade="all, delete-orphan")
    deliverables = relationship("ProjectDeliverable", back_populates="project", cascade="all, delete-orphan")


class ProjectDeliverable(Base):
    """项目交付物料清单：立项时从合同Excel导入或手动录入"""
    __tablename__ = "project_deliverables"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("wbs_projects.id"), nullable=False)
    material_code = Column(String(50), nullable=True)
    material_name = Column(String(200), nullable=False)
    specification = Column(String(200), nullable=True)
    quantity = Column(DECIMAL(18, 4), nullable=False, default=1)
    unit = Column(String(20), default="个")
    unit_price = Column(DECIMAL(18, 2), nullable=True)
    remark = Column(Text, nullable=True)
    source = Column(String(20), default="manual")  # manual / excel
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    project = relationship("WBSProject", back_populates="deliverables")


class ProjectProductionTask(Base):
    """项目生产派工任务：跨部门流转状态机
    状态流转：CONTRACT_SIGNED → PRODUCTION_RECEIVED → STEPS_DEFINED
             → MATERIALS_UPLOADED → PROCUREMENT_DISPATCHED → PURCHASING → COMPLETED
    """
    __tablename__ = "project_production_tasks"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("wbs_projects.id"), nullable=False)
    task_no = Column(String(50), unique=True, nullable=False)  # 派工单号
    # 状态机
    status = Column(String(30), default="CONTRACT_SIGNED")
    # 生产步骤（JSON数组：[{seq:1, name:"下料", desc:"...", operator:"..."}]）
    production_steps = Column(Text, nullable=True)
    # 各时间节点
    contract_signed_at = Column(DateTime, nullable=True)
    production_received_at = Column(DateTime, nullable=True)
    steps_defined_at = Column(DateTime, nullable=True)
    materials_uploaded_at = Column(DateTime, nullable=True)
    procurement_dispatched_at = Column(DateTime, nullable=True)
    purchasing_completed_at = Column(DateTime, nullable=True)
    # 负责人
    production_owner = Column(String(50), nullable=True)
    procurement_owner = Column(String(50), nullable=True)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    project = relationship("WBSProject")
    material_requirements = relationship("ProjectMaterialRequirement", back_populates="task", cascade="all, delete-orphan")


class ProjectMaterialRequirement(Base):
    """项目原材料需求清单：生产部门上传，采购部门执行
    与ProjectDeliverable的区别：Deliverable是卖给客户的成品，Requirement是生产需要采购的原料
    """
    __tablename__ = "project_material_requirements"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("project_production_tasks.id"), nullable=False)
    material_code = Column(String(50), nullable=True)
    material_name = Column(String(200), nullable=False)
    specification = Column(String(200), nullable=True)
    quantity = Column(DECIMAL(18, 4), nullable=False, default=1)
    unit = Column(String(20), default="个")
    unit_price = Column(DECIMAL(18, 2), nullable=True)
    # 采购状态：PENDING待采购 / PURCHASING采购中 / ARRIVED已到货 / CANCELLED已取消
    purchase_status = Column(String(20), default="PENDING")
    remark = Column(Text, nullable=True)
    source = Column(String(20), default="manual")  # manual / excel
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    task = relationship("ProjectProductionTask", back_populates="material_requirements")


class TechnicalDecomposition(Base):
    """技术分解零件清单：技术部从合同交付物料拆解为采购/加工/装配三类
    下发后分别进入采购需求池/委派加工单/生产任务
    """
    __tablename__ = "technical_decompositions"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("wbs_projects.id"), nullable=False)
    deliverable_id = Column(Integer, ForeignKey("project_deliverables.id"), nullable=True)
    part_code = Column(String(50), nullable=True)
    part_name = Column(String(200), nullable=False)
    specification = Column(String(200), nullable=True)
    quantity = Column(DECIMAL(18, 4), nullable=False, default=1)
    unit = Column(String(20), default="个")
    # 三分类：PURCHASABLE可采购 / MANUFACTURABLE可加工 / ASSEMBLABLE可装配
    category = Column(String(20), default="PURCHASABLE")
    # 下发状态：PENDING待下发 / DISPATCHED已下发
    dispatch_status = Column(String(20), default="PENDING")
    bom_item_id = Column(Integer, ForeignKey("bom_items.id"), nullable=True)
    source = Column(String(20), default="excel")  # excel / manual
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    project = relationship("WBSProject")


# ============================================================
# PMC模块：生产物料控制（主计划→排产→物料需求联动）
# ============================================================

class PMCProductionLine(Base):
    """PMC生产线/设备组：定义产能、班次、加班能力"""
    __tablename__ = "pmc_production_lines"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    line_code = Column(String(50), nullable=False)  # 生产线编号
    line_name = Column(String(200), nullable=False)  # 生产线名称
    workshop = Column(String(100), nullable=True)  # 车间
    # 产能配置
    daily_capacity = Column(DECIMAL(18, 4), default=0)  # 每日标准产能（件/天）
    shift_hours = Column(DECIMAL(5, 2), default=8)  # 每班工时
    shift_count = Column(Integer, default=1)  # 每日班次
    max_overtime_hours = Column(DECIMAL(5, 2), default=3)  # 最大加班工时/班
    # 关联工序（逗号分隔的工序编码，如 CNC,打磨,组装）
    process_codes = Column(String(500), nullable=True)
    equipment_ids = Column(String(500), nullable=True)  # 关联设备ID（逗号分隔）
    status = Column(String(20), default="ACTIVE")  # ACTIVE启用/MAINTENANCE维护中/DISABLED停用
    remark = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")


class PMCCapacityPlan(Base):
    """PMC产能主计划：按时间段规划各工序产能负荷，预警瓶颈"""
    __tablename__ = "pmc_capacity_plans"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    plan_no = Column(String(50), nullable=False)  # 计划编号
    plan_name = Column(String(200), nullable=True)  # 计划名称
    period_start = Column(Date, nullable=False)  # 计划开始日期
    period_end = Column(Date, nullable=False)  # 计划结束日期
    # 产能负荷汇总（JSON: {工序: {demand, capacity, utilization, bottleneck}}）
    capacity_summary = Column(Text, nullable=True)
    status = Column(String(20), default="DRAFT")  # DRAFT草稿/CONFIRMED已确认/ARCHIVED已归档
    remark = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")


class PMCSchedule(Base):
    """PMC排产单：从销售订单/生产工单生成的排产主单"""
    __tablename__ = "pmc_schedules"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    schedule_no = Column(String(50), nullable=False)  # 排产单号
    # 来源关联
    sales_order_id = Column(Integer, nullable=True)  # 销售订单ID
    work_order_id = Column(Integer, ForeignKey("production_workorders.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    product_name = Column(String(200), nullable=True)
    bom_id = Column(Integer, ForeignKey("boms.id"), nullable=True)
    # 排产需求
    demand_qty = Column(DECIMAL(18, 4), nullable=False, default=0)  # 需求数量
    completed_qty = Column(DECIMAL(18, 4), default=0)  # 已完成数量
    # 排产时间
    plan_start_date = Column(Date, nullable=False)  # 计划开始日期
    plan_end_date = Column(Date, nullable=False)  # 计划结束日期
    # 排产配置
    line_id = Column(Integer, ForeignKey("pmc_production_lines.id"), nullable=True)  # 指定生产线
    priority = Column(String(20), default="NORMAL")  # URGENT紧急/HIGH高/NORMAL正常/LOW低
    is_insert = Column(Integer, default=0)  # 是否插单 0否1是
    # 状态
    status = Column(String(20), default="PLANNED")  # PLANNED已排产/RUNNING生产中/COMPLETED已完成/PAUSED暂停/CANCELLED已取消
    # 物料齐套状态
    material_ready_status = Column(String(20), default="UNKNOWN")  # UNKNOWN未知/READY齐套/PARTIAL部分齐套/SHORTAGE缺料
    remark = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    product = relationship("Material")
    line = relationship("PMCProductionLine")


class PMCScheduleItem(Base):
    """PMC排产明细：每日每设备每工序的排产安排（支持加班调节）"""
    __tablename__ = "pmc_schedule_items"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("pmc_schedules.id"), nullable=False)
    line_id = Column(Integer, ForeignKey("pmc_production_lines.id"), nullable=True)
    equipment_id = Column(Integer, ForeignKey("equipments.id"), nullable=True)
    schedule_date = Column(Date, nullable=False)  # 排产日期
    process_code = Column(String(50), nullable=True)  # 工序编码
    process_name = Column(String(100), nullable=True)  # 工序名称
    planned_qty = Column(DECIMAL(18, 4), default=0)  # 计划数量
    completed_qty = Column(DECIMAL(18, 4), default=0)  # 完成数量
    # 加班调节
    base_hours = Column(DECIMAL(5, 2), default=8)  # 基础工时
    overtime_hours = Column(DECIMAL(5, 2), default=0)  # 加班工时
    # 状态
    status = Column(String(20), default="PLANNED")  # PLANNED/RUNNING/COMPLETED/PAUSED
    remark = Column(String(300), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    schedule = relationship("PMCSchedule", backref="items")
    line = relationship("PMCProductionLine")


class PMCMaterialDemand(Base):
    """PMC物料需求：排产联动MRP，按排产日期倒推物料到位时间"""
    __tablename__ = "pmc_material_demands"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("pmc_schedules.id"), nullable=True)
    schedule_item_id = Column(Integer, ForeignKey("pmc_schedule_items.id"), nullable=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    material_code = Column(String(50), nullable=True)
    material_name = Column(String(200), nullable=True)
    spec = Column(String(200), nullable=True)
    # 需求计算
    unit_qty = Column(DECIMAL(18, 4), default=0)  # 单耗
    total_demand = Column(DECIMAL(18, 4), default=0)  # 总需求量
    stock_qty = Column(DECIMAL(18, 4), default=0)  # 现有库存
    intransit_qty = Column(DECIMAL(18, 4), default=0)  # 在途数量
    deficit_qty = Column(DECIMAL(18, 4), default=0)  # 缺料量
    # 时间
    lead_time_days = Column(Integer, default=0)  # 采购提前期
    schedule_date = Column(Date, nullable=True)  # 排产日期（物料需到位日期）
    required_date = Column(Date, nullable=True)  # 需求日期（=排产日期-提前期）
    # 状态
    ready_status = Column(String(20), default="UNKNOWN")  # UNKNOWN/READY齐告/PARTIAL/SHORTAGE缺料
    purchase_status = Column(String(20), default="NONE")  # NONE无采购/PENDING待下单/ORDERED已采购/ARRIVED已到货
    remark = Column(String(300), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    account_set = relationship("AccountSet")
    material = relationship("Material")
    schedule = relationship("PMCSchedule")


class TechOutsourcingOrder(Base):
    """技术委派加工单：可加工零件下发到生产管理的委外加工模块"""
    __tablename__ = "tech_outsourcing_orders"
    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, nullable=False)
    project_id = Column(Integer, ForeignKey("wbs_projects.id"), nullable=False)
    decomposition_id = Column(Integer, ForeignKey("technical_decompositions.id"), nullable=True)
    part_name = Column(String(200), nullable=False)
    specification = Column(String(200), nullable=True)
    quantity = Column(DECIMAL(18, 4), nullable=False, default=1)
    unit = Column(String(20), default="个")
    process_name = Column(String(100), nullable=True)
    supplier = Column(String(100), nullable=True)
    # 状态：PENDING待加工 / PROCESSING加工中 / COMPLETED已完成 / CANCELLED已取消
    status = Column(String(20), default="PENDING")
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    project = relationship("WBSProject")


class WBSNode(Base):
    """WBS节点：项目分解结构，成本归集最小单元"""
    __tablename__ = "wbs_nodes"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("wbs_projects.id"), nullable=False)
    node_code = Column(String(50), nullable=False)
    node_name = Column(String(200), nullable=False)
    parent_id = Column(Integer, ForeignKey("wbs_nodes.id"), nullable=True)
    level = Column(Integer, default=1)
    # 节点类型：TASK任务 / MILESTONE里程碑 / COST_POINT成本归集点
    node_type = Column(String(20), default="TASK")
    # 预算拆分（人工/材料/外协/其他）
    budget_labor = Column(DECIMAL(18, 2), default=0)
    budget_material = Column(DECIMAL(18, 2), default=0)
    budget_outsource = Column(DECIMAL(18, 2), default=0)
    budget_other = Column(DECIMAL(18, 2), default=0)
    budget_cost = Column(DECIMAL(18, 2), default=0)  # 总预算 = 以上四项之和
    incurred_cost = Column(DECIMAL(18, 2), default=0)
    # 计划/实际日期
    plan_start = Column(Date, nullable=True)
    plan_end = Column(Date, nullable=True)
    actual_start = Column(Date, nullable=True)
    actual_end = Column(Date, nullable=True)
    progress = Column(DECIMAL(5, 2), default=0)  # 完成百分比
    work_order_id = Column(Integer, ForeignKey("prod_doc_work_orders.id"), nullable=True)
    status = Column(String(20), default="PLANNING")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    project = relationship("WBSProject", back_populates="wbs_nodes")
    parent = relationship("WBSNode", remote_side=[id])
    work_order = relationship("ProductionWorkOrderDoc")


class Equipment(Base):
    """设备台账"""
    __tablename__ = "equipments"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    equipment_code = Column(String(50), unique=True, nullable=False)
    equipment_name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=True)
    model = Column(String(100), nullable=True)
    manufacturer = Column(String(100), nullable=True)
    workshop = Column(String(100), nullable=True)
    work_center = Column(String(50), nullable=True)  # 工作中心
    commission_date = Column(Date, nullable=True)  # 投用日期
    purchase_date = Column(Date, nullable=True)
    status = Column(String(20), default="RUNNING")  # RUNNING运行/IDLE停机/MAINTENANCE维修/SCRAPPED报废
    oee = Column(DECIMAL(5, 2), default=0)
    availability = Column(DECIMAL(5, 2), default=0)
    performance = Column(DECIMAL(5, 2), default=0)
    quality_rate = Column(DECIMAL(5, 2), default=0)
    last_maintenance = Column(Date, nullable=True)
    next_maintenance = Column(Date, nullable=True)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class QualityTrace(Base):
    """质量追溯记录：批次→工序→物料双向追溯"""
    __tablename__ = "quality_traces"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    batch_no = Column(String(50), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    work_order_id = Column(Integer, ForeignKey("prod_doc_work_orders.id"), nullable=True)
    process_step = Column(String(100), nullable=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    qc_result = Column(String(20), default="PENDING")
    qc_quantity = Column(DECIMAL(18, 4), default=0)
    defect_description = Column(Text, nullable=True)
    inspector = Column(String(50), nullable=True)
    inspect_date = Column(Date, nullable=True)
    supplier = Column(String(100), nullable=True)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    product = relationship("Material", foreign_keys=[product_id])
    material = relationship("Material", foreign_keys=[material_id])
    work_order = relationship("ProductionWorkOrderDoc")


class ProductionSchedule(Base):
    """生产排程：甘特图数据"""
    __tablename__ = "production_schedules"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    work_order_id = Column(Integer, ForeignKey("prod_doc_work_orders.id"), nullable=True)
    work_order_no = Column(String(50), nullable=True)
    product_name = Column(String(200), nullable=True)
    workshop = Column(String(100), nullable=True)
    equipment_id = Column(Integer, ForeignKey("equipments.id"), nullable=True)
    process_step = Column(String(100), nullable=True)
    planned_start = Column(DateTime, nullable=True)
    planned_end = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    planned_qty = Column(DECIMAL(18, 4), default=0)
    completed_qty = Column(DECIMAL(18, 4), default=0)
    status = Column(String(20), default="PLANNED")
    priority = Column(String(20), default="normal")
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    work_order = relationship("ProductionWorkOrderDoc")
    equipment = relationship("Equipment")


# ============================================================
# 工程导向型ERP扩展模块（7大核心模块数据模型）
# ============================================================

class CostCollection(Base):
    """成本归集表：四条路径自动归集到WBS节点"""
    __tablename__ = "cost_collections"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("wbs_projects.id"), nullable=False)
    wbs_id = Column(Integer, ForeignKey("wbs_nodes.id"), nullable=True)
    cost_type = Column(String(20), nullable=False)  # 材料/人工/外协/其他
    amount = Column(DECIMAL(18, 2), nullable=False, default=0)
    source_type = Column(String(30), nullable=False)  # 采购/报工/外协/报销
    source_id = Column(Integer, nullable=True)  # 来源单据ID
    source_no = Column(String(100), nullable=True)  # 来源单据号
    record_date = Column(Date, nullable=False, default=datetime.date.today)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    project = relationship("WBSProject")
    wbs_node = relationship("WBSNode")


class RevenueRecognition(Base):
    """收入确认表：完工百分比法"""
    __tablename__ = "revenue_recognitions"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("wbs_projects.id"), nullable=False)
    confirm_date = Column(Date, nullable=False, default=datetime.date.today)
    progress_percent = Column(DECIMAL(5, 2), nullable=False, default=0)  # 本次完工进度
    total_revenue = Column(DECIMAL(18, 2), nullable=False, default=0)  # 应确认收入(合同额×进度)
    cumulative_revenue = Column(DECIMAL(18, 2), nullable=False, default=0)  # 累计已确认收入
    current_revenue = Column(DECIMAL(18, 2), nullable=False, default=0)  # 本次确认收入
    voucher_id = Column(Integer, ForeignKey("auto_vouchers.id"), nullable=True)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    project = relationship("WBSProject")


class Milestone(Base):
    """里程碑表：项目关键节点"""
    __tablename__ = "milestones"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("wbs_projects.id"), nullable=False)
    name = Column(String(100), nullable=False)
    target_progress = Column(DECIMAL(5, 2), nullable=False, default=0)  # 目标完成百分比
    actual_progress = Column(DECIMAL(5, 2), default=0)
    status = Column(String(20), default="PENDING")  # PENDING/IN_PROGRESS/ACHIEVED
    target_date = Column(Date, nullable=True)
    achieve_date = Column(Date, nullable=True)
    confirm_date = Column(Date, nullable=True)  # 触发收入确认日期
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    project = relationship("WBSProject")


class Downtime(Base):
    """停机记录表"""
    __tablename__ = "downtimes"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    equipment_id = Column(Integer, ForeignKey("equipments.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration = Column(DECIMAL(10, 2), default=0)  # 停机时长(分钟)
    reason = Column(String(50), nullable=False)  # 故障/缺料/换模/待工/其他
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    equipment = relationship("Equipment")


class MaintenancePlan(Base):
    """维护计划表：预防性维护"""
    __tablename__ = "maintenance_plans"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    equipment_id = Column(Integer, ForeignKey("equipments.id"), nullable=False)
    cycle_type = Column(String(10), default="MONTH")  # DAY/WEEK/MONTH
    cycle_value = Column(Integer, default=1)
    last_maint_date = Column(Date, nullable=True)
    next_maint_date = Column(Date, nullable=True)
    content = Column(Text, nullable=True)  # 维护内容
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    equipment = relationship("Equipment")


class Inspection(Base):
    """检验单表：IQC来料/IPQC过程/FQC成品"""
    __tablename__ = "inspections"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    inspect_type = Column(String(10), nullable=False)  # IQC/IPQC/FQC
    source_type = Column(String(20), nullable=True)  # 采购/工单/成品
    source_id = Column(Integer, nullable=True)
    source_no = Column(String(100), nullable=True)
    batch_no = Column(String(50), nullable=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    result = Column(String(20), default="PENDING")  # PASS/FAIL/CONCESSION
    inspector = Column(String(50), nullable=True)
    inspect_date = Column(Date, nullable=True)
    qualified_qty = Column(DECIMAL(18, 4), default=0)
    unqualified_qty = Column(DECIMAL(18, 4), default=0)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    material = relationship("Material")
    items = relationship("InspectionItem", back_populates="inspection", cascade="all, delete-orphan")


class InspectionItem(Base):
    """检验明细表"""
    __tablename__ = "inspection_items"
    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id"), nullable=False)
    item_name = Column(String(100), nullable=False)
    standard = Column(String(200), nullable=True)
    actual_value = Column(String(200), nullable=True)
    result = Column(String(20), default="PENDING")  # PASS/FAIL

    inspection = relationship("Inspection", back_populates="items")


class EcoImpact(Base):
    """ECO影响表：变更影响范围分析"""
    __tablename__ = "eco_impacts"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    eco_id = Column(Integer, ForeignKey("eco_change_orders.id"), nullable=True)  # 关联ECO单
    impact_type = Column(String(20), nullable=False)  # BOM/工单/采购/库存
    target_id = Column(Integer, nullable=True)
    target_desc = Column(String(200), nullable=True)
    cost_impact = Column(DECIMAL(18, 2), default=0)  # 成本影响
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)


class WorkOrderProcess(Base):
    """工单工序表：生产排程核心"""
    __tablename__ = "work_order_processes"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False)
    work_order_no = Column(String(50), nullable=False)
    project_id = Column(Integer, ForeignKey("wbs_projects.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    process_seq = Column(Integer, nullable=False, default=1)
    process_name = Column(String(100), nullable=False)
    work_center = Column(String(50), nullable=True)
    plan_start = Column(DateTime, nullable=True)
    plan_end = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    quantity = Column(Integer, default=0)
    status = Column(String(20), default="PENDING")  # PENDING/SCHEDULED/RUNNING/COMPLETED
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    project = relationship("WBSProject")
    product = relationship("Material")


# =============== 企业级配置（单例模式，全局唯一）===============

class EnterpriseConfig(Base):
    """企业级配置：行业类型、业务模式、收入确认方式、领料方式等全局配置
    设计为单例（id=1），整个企业只有一条记录
    """
    __tablename__ = "enterprise_config"
    id = Column(Integer, primary_key=True, index=True)
    # 行业类型：engineering(工程导向)/agility(敏捷导向)/compliance(合规导向)/subscription(订阅导向)
    industry_type = Column(String(50), default="engineering")
    # 业务模式：A=大批量单品种, B=小批量多品种
    business_mode = Column(String(10), default="B")
    # 收入确认方式：percentage_of_completion(完工百分比) / on_delivery(发货确认)
    revenue_method = Column(String(50), default="percentage_of_completion")
    # 领料方式（JSON数组，可多选）：by_order(按单领料)/batch_prep(批量备料)/central(中央领料)/backflush(倒冲)
    picking_modes = Column(Text, default='["by_order"]')
    # 细分行业（用于自动判断A/B模式）
    sub_industry = Column(String(100), nullable=True)
    # 资金成本率（年化，用于EOQ计算）
    capital_cost_rate = Column(Float, default=0.08)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


# =============== API对接中心 ===============

class ApiIntegration(Base):
    """外部API对接配置：存储第三方API的连接信息、认证方式等"""
    __tablename__ = "api_integrations"
    id = Column(Integer, primary_key=True, index=True)
    # 对接名称
    name = Column(String(100), nullable=False)
    # 对接类型：taobao/1688/jd/shopify/custom/wechat/feishu
    api_type = Column(String(50), default="custom")
    # API基础URL
    base_url = Column(String(500), nullable=False)
    # 认证方式：bearer/basic/apikey/oauth2
    auth_type = Column(String(20), default="bearer")
    # API Key/Token（加密存储，这里简化为明文）
    api_key = Column(Text, nullable=True)
    # API Secret
    api_secret = Column(Text, nullable=True)
    # App ID
    app_id = Column(String(100), nullable=True)
    # 额外配置（JSON）
    extra_config = Column(Text, nullable=True)
    # 状态：active/inactive
    status = Column(String(20), default="active")
    # 最后测试时间
    last_tested_at = Column(DateTime, nullable=True)
    # 最后测试结果
    last_test_result = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


# =============== 我的工厂：设备台账 + 每日产能上报 ===============

class FactoryEquipment(Base):
    """工厂设备台账：录入工厂全部设备信息"""
    __tablename__ = "factory_equipments"
    id = Column(Integer, primary_key=True, index=True)
    # 设备编码（唯一）
    equipment_code = Column(String(50), unique=True, nullable=False, index=True)
    # 设备名称
    equipment_name = Column(String(200), nullable=False)
    # 设备类别：加工设备/装配设备/检测与调试设备/辅助设备
    category = Column(String(50), default="加工设备")
    # 规格型号
    specification = Column(String(200), nullable=True)
    # 所在位置
    location = Column(String(200), nullable=True)
    # 状态：running(运行)/idle(闲置)/maintenance(维修)/scrapped(报废)
    status = Column(String(20), default="running")
    # 日产能目标
    daily_capacity_target = Column(Float, default=0)
    # 产能单位
    unit = Column(String(50), default="件")
    # 备注
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    capacity_reports = relationship("EquipmentCapacityDaily", back_populates="equipment", cascade="all, delete-orphan")


class EquipmentCapacityDaily(Base):
    """设备每日产能上报：工人们统计上报每天每台机器的产能"""
    __tablename__ = "equipment_capacity_daily"
    id = Column(Integer, primary_key=True, index=True)
    # 关联设备
    equipment_id = Column(Integer, ForeignKey("factory_equipments.id"), nullable=False, index=True)
    # 上报日期
    report_date = Column(Date, nullable=False, index=True)
    # 班次：day(白班)/night(夜班)/full(全天)
    shift = Column(String(20), default="day")
    # 实际产量
    actual_output = Column(Float, default=0)
    # 目标产量（当天目标，默认取设备日产能目标）
    target_output = Column(Float, default=0)
    # 操作人/工人
    operator = Column(String(100), nullable=True)
    # 备注
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    equipment = relationship("FactoryEquipment", back_populates="capacity_reports")


class UtilityFeeRecord(Base):
    """设备每日水电费（模拟数据/实际录入）：每台机器每天耗费的水电，自动计提进财务制造费用"""
    __tablename__ = "utility_fee_records"
    id = Column(Integer, primary_key=True, index=True)
    account_set_id = Column(Integer, ForeignKey("account_sets.id"), nullable=False, default=1)
    equipment_id = Column(Integer, ForeignKey("factory_equipments.id"), nullable=False, index=True)
    equipment_code = Column(String(50), nullable=True)
    equipment_name = Column(String(100), nullable=True)
    fee_date = Column(Date, nullable=False, index=True)          # 费用归属日期
    electric_fee = Column(DECIMAL(18, 2), default=0)             # 电费（元/天）
    water_fee = Column(DECIMAL(18, 2), default=0)                # 水费（元/天）
    total_amount = Column(DECIMAL(18, 2), default=0)             # 合计
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=True)  # 已生成的凭证
    source = Column(String(20), default="auto")                  # auto自动模拟 / manual手工
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    equipment = relationship("FactoryEquipment")


class CrossDeptNotification(Base):
    """跨部门通知（大厅新闻播报）：业务关键节点统一推送，大厅动态滚动展示"""
    __tablename__ = "cross_dept_notifications"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    category = Column(String(30), default="综合")  # 采购/生产/仓库/质检/财务/技术/综合
    source = Column(String(100), nullable=True)    # 来源模块或单号
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# ==============================
# 总账管理（General Ledger）模型
# ==============================

class GlLedger(Base):
    """账套：一套独立核算的账"""
    __tablename__ = "gl_ledgers"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, default=1)            # 租户ID（多租户隔离）
    name = Column(String(200), nullable=False)         # 账套名称
    code = Column(String(50), unique=True, nullable=False)  # 账套编码
    fiscal_year = Column(Integer, default=1)           # 会计年度起始月（1=1月，9=9月学年制）
    currency = Column(String(10), default="CNY")       # 本位币
    accounting_std = Column(String(50), default="企业会计准则")  # 会计准则
    status = Column(String(20), default="ACTIVE")      # 状态
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    accounts = relationship("GlAccount", back_populates="ledger")
    vouchers = relationship("GlVoucher", back_populates="ledger")
    periods = relationship("GlPeriod", back_populates="ledger")
    balances = relationship("GlBalance", back_populates="ledger")


class GlAccount(Base):
    """会计科目：记账的分类骨架"""
    __tablename__ = "gl_accounts"
    id = Column(Integer, primary_key=True, index=True)
    ledger_id = Column(Integer, ForeignKey("gl_ledgers.id"), nullable=False)
    code = Column(String(20), nullable=False)          # 科目编码（如 1001、6001）
    name = Column(String(200), nullable=False)         # 科目名称
    parent_id = Column(Integer, ForeignKey("gl_accounts.id"), nullable=True)
    level = Column(Integer, default=1)                 # 科目级次
    category = Column(String(20), nullable=False)      # 资产/负债/权益/收入/费用/成本
    direction = Column(String(10), default="借")       # 余额方向：借/贷
    is_leaf = Column(Boolean, default=True)            # 是否末级科目（只有末级能记账）
    aux_required = Column(Text, default="[]")          # 需要的辅助核算类型编码（JSON数组）
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    ledger = relationship("GlLedger", back_populates="accounts")
    children = relationship("GlAccount", back_populates="parent", remote_side=[id])
    parent = relationship("GlAccount", back_populates="children", remote_side=[parent_id])
    entries = relationship("GlVoucherEntry", back_populates="account")


class GlAuxType(Base):
    """辅助核算类型：科目核算的额外维度"""
    __tablename__ = "gl_aux_types"
    id = Column(Integer, primary_key=True, index=True)
    ledger_id = Column(Integer, ForeignKey("gl_ledgers.id"), nullable=False)
    code = Column(String(50), nullable=False)          # 类型编码（campus/department/customer）
    name = Column(String(100), nullable=False)         # 类型名称（校区/部门/客户）
    source_type = Column(String(20), default="内置")   # 内置/外部表
    source_table = Column(String(100), nullable=True)  # 来源表名
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)


class GlAuxValue(Base):
    """辅助核算值：每个维度的具体值"""
    __tablename__ = "gl_aux_values"
    id = Column(Integer, primary_key=True, index=True)
    aux_type_id = Column(Integer, ForeignKey("gl_aux_types.id"), nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    parent_id = Column(Integer, ForeignKey("gl_aux_values.id"), nullable=True)
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    aux_type = relationship("GlAuxType")
    children = relationship("GlAuxValue", back_populates="parent", remote_side=[id])
    parent = relationship("GlAuxValue", back_populates="children", remote_side=[parent_id])


class GlVoucher(Base):
    """凭证：一次记账的记录"""
    __tablename__ = "gl_vouchers"
    id = Column(Integer, primary_key=True, index=True)
    ledger_id = Column(Integer, ForeignKey("gl_ledgers.id"), nullable=False)
    voucher_no = Column(String(50), nullable=False)    # 凭证号（按期间连续）
    voucher_date = Column(Date, nullable=False)        # 凭证日期
    period_id = Column(Integer, ForeignKey("gl_periods.id"), nullable=False)
    voucher_type = Column(String(30), default="记账凭证")  # 记账凭证/转账凭证/收付凭证
    source_type = Column(String(30), default="手工")   # 手工/应收/应付/资产/预算
    source_id = Column(Integer, nullable=True)         # 来源单据ID
    summary = Column(String(200), nullable=True)       # 摘要
    status = Column(String(20), default="草稿")        # 草稿/已审核/已过账/已作废
    created_by = Column(String(50), nullable=True)     # 制单人
    audited_by = Column(String(50), nullable=True)     # 审核人
    posted_at = Column(DateTime, nullable=True)        # 过账时间
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    ledger = relationship("GlLedger", back_populates="vouchers")
    period = relationship("GlPeriod", back_populates="vouchers")
    entries = relationship("GlVoucherEntry", back_populates="voucher", order_by="GlVoucherEntry.line_no")


class GlVoucherEntry(Base):
    """凭证分录：凭证的借贷明细行"""
    __tablename__ = "gl_voucher_entries"
    id = Column(Integer, primary_key=True, index=True)
    voucher_id = Column(Integer, ForeignKey("gl_vouchers.id"), nullable=False)
    line_no = Column(Integer, nullable=False)          # 行号
    account_id = Column(Integer, ForeignKey("gl_accounts.id"), nullable=False)
    summary = Column(String(200), nullable=True)       # 摘要
    debit_amount = Column(DECIMAL(18, 2), default=0)   # 借方金额
    credit_amount = Column(DECIMAL(18, 2), default=0)  # 贷方金额
    currency = Column(String(10), default="CNY")       # 币种
    exchange_rate = Column(DECIMAL(10, 4), default=1)  # 汇率
    original_amount = Column(DECIMAL(18, 2), default=0)  # 原币金额
    aux_values = Column(Text, default="{}")            # 辅助核算值（JSON）

    voucher = relationship("GlVoucher", back_populates="entries")
    account = relationship("GlAccount", back_populates="entries")


class GlPeriod(Base):
    """会计期间"""
    __tablename__ = "gl_periods"
    id = Column(Integer, primary_key=True, index=True)
    ledger_id = Column(Integer, ForeignKey("gl_ledgers.id"), nullable=False)
    year = Column(Integer, nullable=False)             # 年份
    month = Column(Integer, nullable=False)            # 月份
    start_date = Column(Date, nullable=False)          # 开始日期
    end_date = Column(Date, nullable=False)            # 结束日期
    status = Column(String(20), default="未结账")      # 未结账/已结账/已关闭
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    ledger = relationship("GlLedger", back_populates="periods")
    vouchers = relationship("GlVoucher", back_populates="period")
    balances = relationship("GlBalance", back_populates="period")


class GlBalance(Base):
    """余额表：按科目+辅助核算组合记录期末余额"""
    __tablename__ = "gl_balances"
    id = Column(Integer, primary_key=True, index=True)
    ledger_id = Column(Integer, ForeignKey("gl_ledgers.id"), nullable=False)
    period_id = Column(Integer, ForeignKey("gl_periods.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("gl_accounts.id"), nullable=False)
    aux_values = Column(Text, default="{}")            # 辅助核算值（JSON）
    begin_debit = Column(DECIMAL(18, 2), default=0)    # 期初借方
    begin_credit = Column(DECIMAL(18, 2), default=0)   # 期初贷方
    period_debit = Column(DECIMAL(18, 2), default=0)   # 本期借方
    period_credit = Column(DECIMAL(18, 2), default=0)  # 本期贷方
    end_debit = Column(DECIMAL(18, 2), default=0)      # 期末借方
    end_credit = Column(DECIMAL(18, 2), default=0)     # 期末贷方
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    ledger = relationship("GlLedger", back_populates="balances")
    period = relationship("GlPeriod", back_populates="balances")
    account = relationship("GlAccount")