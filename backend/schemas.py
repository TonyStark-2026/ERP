from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

class ApiResponse(BaseModel):
    success: bool
    data: Any = None
    message: str = ""
    error_code: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class AccountSetBase(BaseModel):
    name: str
    code: str
    company_name: str
    tax_id: Optional[str] = None
    currency: str = "CNY"
    timezone: str = "Asia/Shanghai"

class AccountSetCreate(AccountSetBase):
    pass

class AccountSet(AccountSetBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CompanyScale(str, Enum):
    SINGLE_USER = "SINGLE_USER"
    SMALL_TEAM = "SMALL_TEAM"
    LARGE_TEAM = "LARGE_TEAM"

class BusinessComplexity(str, Enum):
    TRADE_ONLY = "TRADE_ONLY"
    SIMPLE_PROCESSING = "SIMPLE_PROCESSING"
    COMPLEX_MANUFACTURING = "COMPLEX_MANUFACTURING"

class SystemConfigBase(BaseModel):
    company_scale: CompanyScale = CompanyScale.SINGLE_USER
    business_complexity: BusinessComplexity = BusinessComplexity.TRADE_ONLY
    approval_enabled: bool = True
    auto_voucher_enabled: bool = True
    multi_price_enabled: bool = True
    crossborder_enabled: bool = False
    labor_compliance_enabled: bool = True
    cva_abc_enabled: bool = True

class SystemConfigCreate(SystemConfigBase):
    account_set_id: int

class SystemConfig(SystemConfigBase):
    id: int
    account_set_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MaterialBase(BaseModel):
    name: str
    code: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    unit_price: Decimal = 0.0
    unit: str = "个"
    hs_code: Optional[str] = None
    criticality: Optional[int] = None
    value_score: Optional[Decimal] = None
    cva_abc_class: Optional[str] = None
    safety_stock: int = 0
    min_stock: int = 0
    max_stock: int = 1000
    cva_class: Optional[str] = None
    abc_class: Optional[str] = None
    classification_coefficient: Decimal = 1.0
    batch_tracking_enabled: bool = False
    is_slow_moving: bool = False
    shelf_life_days: Optional[int] = None
    reorder_point: int = 0
    default_supplier_id: Optional[int] = None

class MaterialCreate(MaterialBase):
    account_set_id: int

class Material(MaterialBase):
    id: int
    account_set_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SupplierBase(BaseModel):
    name: str
    code: str
    tax_id: Optional[str] = None
    tax_id_expiry: Optional[date] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    history_price: Optional[Decimal] = None
    on_time_rate: Optional[Decimal] = None
    quality_rate: Optional[Decimal] = None
    compliance_rating: Optional[str] = None
    is_overseas: bool = False

class SupplierCreate(SupplierBase):
    account_set_id: int

class Supplier(SupplierBase):
    id: int
    account_set_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CustomerBase(BaseModel):
    name: str
    code: str
    tax_id: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    credit_limit: Optional[Decimal] = 0
    credit_used: Optional[Decimal] = 0
    customer_level: Optional[str] = "NORMAL"
    is_overseas: bool = False

class CustomerCreate(CustomerBase):
    account_set_id: int

class Customer(CustomerBase):
    id: int
    account_set_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PriceType(str, Enum):
    RETAIL = "RETAIL"
    WHOLESALE = "WHOLESALE"
    MEMBER = "MEMBER"
    PROMOTION = "PROMOTION"

class PriceListBase(BaseModel):
    material_id: int
    price_type: PriceType
    customer_level: Optional[str] = None
    price: Decimal
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool = True

class PriceListCreate(PriceListBase):
    account_set_id: int

class PriceList(PriceListBase):
    id: int
    account_set_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PurchaseOrderTemplateItemBase(BaseModel):
    material_id: int
    quantity: int
    unit_price: Decimal
    is_gift: bool = False

class PurchaseOrderTemplateItemCreate(PurchaseOrderTemplateItemBase):
    template_id: int

class PurchaseOrderTemplateItem(PurchaseOrderTemplateItemBase):
    id: int
    template_id: int

    class Config:
        from_attributes = True

class PurchaseOrderTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    supplier_id: Optional[int] = None
    tax_rate: Decimal
    is_active: bool = True

class PurchaseOrderTemplateCreate(PurchaseOrderTemplateBase):
    account_set_id: int
    items: List[PurchaseOrderTemplateItemBase]

class PurchaseOrderTemplate(PurchaseOrderTemplateBase):
    id: int
    account_set_id: int
    items: List[PurchaseOrderTemplateItem]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    WAITING_SUPPLEMENT = "WAITING_SUPPLEMENT"

class PurchaseOrderItemBase(BaseModel):
    material_id: int
    quantity: int
    unit_price: Decimal
    is_gift: bool = False
    special_price: Optional[Decimal] = None
    allocated_discount: Decimal = 0

class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    purchase_order_id: int

class PurchaseOrderItem(PurchaseOrderItemBase):
    id: int
    purchase_order_id: int

    class Config:
        from_attributes = True

class PurchaseOrderBase(BaseModel):
    po_no: str
    supplier_id: Optional[int] = None
    template_id: Optional[int] = None
    status: str = "PENDING"
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    is_emergency: bool = False
    need_supplement: bool = False
    tax_rate: Decimal
    discount_amount: Decimal = 0
    discount_rate: Optional[Decimal] = None

class PurchaseOrderCreate(PurchaseOrderBase):
    account_set_id: int
    items: List[PurchaseOrderItemBase]

class PurchaseOrder(PurchaseOrderBase):
    id: int
    account_set_id: int
    items: List[PurchaseOrderItem]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TradeTerm(str, Enum):
    FOB = "FOB"
    CIF = "CIF"
    DDP = "DDP"
    DAP = "DAP"

class SalesOrderItemBase(BaseModel):
    material_id: int
    quantity: int
    unit_price: Decimal
    # 数据库这两列允许为空（历史数据存的是 NULL），必须可空，否则读取接口会 500
    is_gift: Optional[bool] = False
    allocated_discount: Optional[Decimal] = 0
    price_type: Optional[PriceType] = None

class SalesOrderItemCreate(SalesOrderItemBase):
    sales_order_id: int

class SalesOrderItem(SalesOrderItemBase):
    id: int
    sales_order_id: int

    class Config:
        from_attributes = True

class SalesOrderBase(BaseModel):
    so_no: str
    customer_id: Optional[int] = None
    status: str = "PENDING"
    trade_term: Optional[TradeTerm] = None
    currency: str = "CNY"
    exchange_rate: Decimal = 1.0
    credit_check_passed: bool = True

class SalesOrderCreate(SalesOrderBase):
    account_set_id: int
    items: List[SalesOrderItemBase]

class SalesOrder(SalesOrderBase):
    id: int
    account_set_id: int
    items: List[SalesOrderItem]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BOMItemBase(BaseModel):
    material_id: int
    quantity: Decimal
    unit: str
    scrap_rate: Decimal = 0
    sequence: int = 0
    level: int = 1

class BOMItemCreate(BOMItemBase):
    bom_id: int

class BOMItem(BOMItemBase):
    id: int
    bom_id: int

    class Config:
        from_attributes = True

class BOMBase(BaseModel):
    product_id: int
    version: str = "V1"
    effective_date: Optional[date] = None
    status: str = "ACTIVE"

class BOMCreate(BOMBase):
    account_set_id: int
    items: List[BOMItemBase]

class BOM(BOMBase):
    id: int
    account_set_id: int
    items: List[BOMItem]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WorkOrderStatus(str, Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class ProductionWorkOrderBase(BaseModel):
    work_order_no: str
    product_id: int
    bom_id: Optional[int] = None
    planned_qty: int
    completed_qty: int = 0
    in_progress_qty: int = 0
    completion_ratio: Optional[Decimal] = None
    status: WorkOrderStatus = WorkOrderStatus.PLANNED
    start_date: date
    end_date: Optional[date] = None
    actual_material_cost: Decimal = 0
    actual_labor_cost: Decimal = 0
    actual_overhead_cost: Decimal = 0
    standard_cost: Optional[Decimal] = None

class ProductionWorkOrderCreate(ProductionWorkOrderBase):
    account_set_id: int

class ProductionWorkOrder(ProductionWorkOrderBase):
    id: int
    account_set_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CostType(str, Enum):
    RAW_MATERIAL = "RAW_MATERIAL"
    DIRECT_LABOR = "DIRECT_LABOR"
    MANUFACTURING_OVERHEAD = "MANUFACTURING_OVERHEAD"

class ProductionCostBase(BaseModel):
    cost_type: CostType
    amount: Decimal
    description: Optional[str] = None

class ProductionCostCreate(ProductionCostBase):
    work_order_id: int

class ProductionCost(ProductionCostBase):
    id: int
    work_order_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CostAllocationBase(BaseModel):
    total_input_cost: Decimal
    equivalent_output: Decimal
    cost_per_equivalent: Decimal
    completed_allocation: Decimal
    in_progress_allocation: Decimal
    material_ratio: Optional[Decimal] = None
    labor_ratio: Optional[Decimal] = None
    overhead_ratio: Optional[Decimal] = None

class CostAllocationCreate(CostAllocationBase):
    work_order_id: int

class CostAllocation(CostAllocationBase):
    id: int
    work_order_id: int
    allocated_at: datetime

    class Config:
        from_attributes = True

class CostAllocationRequest(BaseModel):
    work_order_id: int
    completed_qty: int
    in_progress_qty: int
    completion_ratio: Decimal
    material_ratio: Optional[Decimal] = None
    labor_ratio: Optional[Decimal] = None
    overhead_ratio: Optional[Decimal] = None

class StockType(str, Enum):
    RAW_MATERIAL = "RAW_MATERIAL"
    WORK_IN_PROGRESS = "WORK_IN_PROGRESS"
    FINISHED_GOODS = "FINISHED_GOODS"

class TransactionType(str, Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"
    ADJUSTMENT = "ADJUSTMENT"
    STOCKTAKE = "STOCKTAKE"

class InventoryRecordBase(BaseModel):
    material_id: int
    location_code: str
    batch_no: Optional[str] = None
    expiry_date: Optional[date] = None
    quantity: int
    stock_type: StockType
    unit_cost: Decimal = 0

class InventoryRecordCreate(InventoryRecordBase):
    account_set_id: int

class InventoryRecord(InventoryRecordBase):
    id: int
    account_set_id: int

    class Config:
        from_attributes = True

class InventoryTransactionBase(BaseModel):
    material_id: int
    transaction_type: TransactionType
    quantity: int
    before_qty: int
    after_qty: int
    reference_no: Optional[str] = None
    operator: str
    unit_cost: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None

class InventoryTransactionCreate(InventoryTransactionBase):
    account_set_id: int

class InventoryTransaction(InventoryTransactionBase):
    id: int
    account_set_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class StocktakingItemBase(BaseModel):
    material_id: int
    location_code: str
    book_qty: int
    actual_qty: Optional[int] = None
    variance: Optional[int] = None
    variance_amount: Optional[Decimal] = None
    reason: Optional[str] = None

class StocktakingItemCreate(StocktakingItemBase):
    task_id: int

class StocktakingItem(StocktakingItemBase):
    id: int
    task_id: int

    class Config:
        from_attributes = True

class StocktakingTaskBase(BaseModel):
    task_no: str
    status: str = "PLANNED"
    start_date: date
    end_date: Optional[date] = None
    location_code: Optional[str] = None

class StocktakingTaskCreate(StocktakingTaskBase):
    account_set_id: int

class StocktakingTask(StocktakingTaskBase):
    id: int
    account_set_id: int
    items: List[StocktakingItem]
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ContractType(str, Enum):
    SALES = "SALES"
    PURCHASE = "PURCHASE"

class ContractStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    TERMINATED = "TERMINATED"

class ContractBase(BaseModel):
    contract_no: str
    contract_type: ContractType
    customer_id: Optional[int] = None
    supplier_id: Optional[int] = None
    status: ContractStatus = ContractStatus.DRAFT
    amount: Decimal
    start_date: date
    end_date: date
    payment_due_dates: Optional[str] = None
    delivery_dates: Optional[str] = None

class ContractCreate(ContractBase):
    account_set_id: int

class Contract(ContractBase):
    id: int
    account_set_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EmployeeBase(BaseModel):
    employee_no: str
    name: str
    id_card: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: date
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    probation_end_date: Optional[date] = None
    social_security_start_date: Optional[date] = None
    status: str = "ACTIVE"
    base_salary: Optional[Decimal] = None

class EmployeeCreate(EmployeeBase):
    account_set_id: int

class Employee(EmployeeBase):
    id: int
    account_set_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class VoucherType(str, Enum):
    GENERAL = "GENERAL"
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    PAYMENT = "PAYMENT"
    RECEIPT = "RECEIPT"

class VoucherStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    POSTED = "POSTED"

class VoucherEntryBase(BaseModel):
    account_code: str
    account_name: str
    debit: Optional[Decimal] = None
    credit: Optional[Decimal] = None
    summary: Optional[str] = None
    customer_id: Optional[int] = None
    supplier_id: Optional[int] = None
    department_id: Optional[int] = None
    employee_id: Optional[int] = None
    project_id: Optional[int] = None
    material_id: Optional[int] = None

class VoucherEntryCreate(VoucherEntryBase):
    voucher_id: int

class VoucherEntry(VoucherEntryBase):
    id: int
    voucher_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class VoucherDBBase(BaseModel):
    voucher_no: str
    voucher_type: VoucherType = VoucherType.GENERAL
    voucher_date: date
    status: VoucherStatus = VoucherStatus.DRAFT
    attachments: int = 0
    preparer: Optional[str] = None
    approver: Optional[str] = None
    poster: Optional[str] = None
    reference_doc: Optional[str] = None
    reference_type: Optional[str] = None

class VoucherDBCreate(VoucherDBBase):
    account_set_id: int
    entries: List[VoucherEntryBase]

class VoucherDB(VoucherDBBase):
    id: int
    account_set_id: int
    entries: List[VoucherEntry]
    created_at: datetime
    approved_at: Optional[datetime] = None
    posted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CashFlowCategory(str, Enum):
    OPERATING = "OPERATING"
    INVESTING = "INVESTING"
    FINANCING = "FINANCING"

class CashFlowItemBase(BaseModel):
    item_code: str
    item_name: str
    category: CashFlowCategory
    parent_item_code: Optional[str] = None
    account_codes: Optional[str] = None

class CashFlowItemCreate(CashFlowItemBase):
    account_set_id: int

class CashFlowItem(CashFlowItemBase):
    id: int
    account_set_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ExchangeRateBase(BaseModel):
    from_currency: str
    to_currency: str
    rate: Decimal
    rate_date: date
    source: Optional[str] = None

class ExchangeRateCreate(ExchangeRateBase):
    account_set_id: int

class ExchangeRate(ExchangeRateBase):
    id: int
    account_set_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class AlertLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class ComplianceAlertBase(BaseModel):
    alert_type: str
    level: AlertLevel
    reference_id: Optional[int] = None
    reference_type: Optional[str] = None
    message: str
    suggestion: Optional[str] = None
    status: str = "PENDING"

class ComplianceAlertCreate(ComplianceAlertBase):
    account_set_id: int

class ComplianceAlert(ComplianceAlertBase):
    id: int
    account_set_id: int
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TaxCheckRequest(BaseModel):
    purchase_order_id: int
    invoice_tax_rate: Decimal

class InvoiceCheckRequest(BaseModel):
    invoice_no: Optional[str] = None
    supplier_tax_rate: Optional[Decimal] = None
    company_tax_rate: Optional[Decimal] = None
    items: Optional[List[dict]] = None
    total_amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None

class HsCodeBase(BaseModel):
    hs_code: str
    description_cn: str
    description_en: Optional[str] = None
    unit: Optional[str] = None

class HsCodeCreate(HsCodeBase):
    pass

class HsCode(HsCodeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CountryTaxRuleBase(BaseModel):
    country_code: str
    country_name: str
    vat_rate: Optional[Decimal] = None
    import_tax_rate: Optional[Decimal] = None
    currency_code: str
    invoice_language: Optional[str] = None
    tax_free_threshold: Optional[Decimal] = None
    tax_id_type: Optional[str] = None

class CountryTaxRuleCreate(CountryTaxRuleBase):
    pass

class CountryTaxRule(CountryTaxRuleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class TaxEstimateRequest(BaseModel):
    hs_code: str
    country_code: str
    declared_value: Decimal
    currency: str = "CNY"

class CostSplitRequest(BaseModel):
    incoterm: str
    currency: str = "CNY"
    domestic_cost: Decimal = 0
    international_freight: Decimal = 0
    insurance: Decimal = 0
    declared_value: Decimal = 0
    hs_code: Optional[str] = None
    country_code: Optional[str] = None

class ExchangeRateBase(BaseModel):
    currency: str
    rate: Decimal

class ExchangeRateCreate(ExchangeRateBase):
    pass

class ExchangeRate(ExchangeRateBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class BatchRuleBase(BaseModel):
    name: str
    rule_pattern: str
    description: Optional[str] = None
    is_active: bool = True

class BatchRuleCreate(BatchRuleBase):
    account_set_id: int

class BatchRule(BatchRuleBase):
    id: int
    account_set_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StorageLocationBase(BaseModel):
    location_code: str
    location_name: str
    parent_code: Optional[str] = None
    level: int = 1
    max_capacity: Optional[int] = None
    max_weight: Optional[Decimal] = None
    status: str = "ACTIVE"

class StorageLocationCreate(StorageLocationBase):
    account_set_id: int

class StorageLocation(StorageLocationBase):
    id: int
    account_set_id: int
    current_capacity: int
    current_weight: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UnitConversionBase(BaseModel):
    material_id: int
    from_unit: str
    to_unit: str
    conversion_rate: Decimal
    is_active: bool = True

class UnitConversionCreate(UnitConversionBase):
    account_set_id: int

class UnitConversion(UnitConversionBase):
    id: int
    account_set_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PurchaseAgreementBase(BaseModel):
    supplier_id: int
    agreement_no: str
    material_id: int
    unit_price: Decimal
    min_order_qty: int = 1
    start_date: date
    end_date: date
    status: str = "ACTIVE"

class PurchaseAgreementCreate(PurchaseAgreementBase):
    account_set_id: int

class PurchaseAgreement(PurchaseAgreementBase):
    id: int
    account_set_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PreReceiptItemCreate(BaseModel):
    material_id: int
    expected_qty: int
    unit_price: Optional[Decimal] = None

class PreReceiptBase(BaseModel):
    purchase_order_id: Optional[int] = None
    supplier_id: Optional[int] = None
    expected_arrival_date: Optional[date] = None
    delivery_no: Optional[str] = None

class PreReceiptCreate(PreReceiptBase):
    account_set_id: int
    items: List[PreReceiptItemCreate] = []

class PreReceipt(PreReceiptBase):
    id: int
    account_set_id: int
    pre_receipt_no: str
    actual_arrival_date: Optional[date] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class InboundOrderItemCreate(BaseModel):
    material_id: int
    batch_no: str
    expiry_date: Optional[date] = None
    location_code: str
    quantity: int
    unit_price: Decimal
    variance_qty: int = 0
    variance_reason: Optional[str] = None

class InboundOrderBase(BaseModel):
    pre_receipt_id: Optional[int] = None
    purchase_order_id: Optional[int] = None
    supplier_id: Optional[int] = None
    inbound_date: date
    operator: Optional[str] = None
    remarks: Optional[str] = None

class InboundOrderCreate(InboundOrderBase):
    account_set_id: int
    items: List[InboundOrderItemCreate] = []

class InboundOrder(InboundOrderBase):
    id: int
    account_set_id: int
    inbound_no: str
    status: str
    quality_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OutboundOrderItemCreate(BaseModel):
    material_id: int
    batch_no: str
    location_code: str
    requested_qty: int

class OutboundOrderBase(BaseModel):
    outbound_type: str
    source_order_id: Optional[int] = None
    source_order_no: Optional[str] = None
    customer_id: Optional[int] = None
    department_id: Optional[int] = None
    outbound_date: date
    operator: Optional[str] = None
    remarks: Optional[str] = None

class OutboundOrderCreate(OutboundOrderBase):
    account_set_id: int
    items: List[OutboundOrderItemCreate] = []

class OutboundOrder(OutboundOrderBase):
    id: int
    account_set_id: int
    outbound_no: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BatchInventoryBase(BaseModel):
    material_id: int
    batch_no: str
    location_code: str
    expiry_date: Optional[date] = None
    quantity: int
    unit_cost: Decimal
    quality_status: str = "AVAILABLE"
    supplier_id: Optional[int] = None
    purchase_order_id: Optional[int] = None
    inbound_date: Optional[date] = None

class BatchInventoryCreate(BatchInventoryBase):
    account_set_id: int

class BatchInventory(BatchInventoryBase):
    id: int
    account_set_id: int
    total_cost: Decimal
    last_movement_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BatchMovementBase(BaseModel):
    material_id: int
    batch_no: str
    movement_type: str
    quantity: int
    location_code: str
    to_location_code: Optional[str] = None
    reference_no: Optional[str] = None
    reference_type: Optional[str] = None
    operator: str
    remarks: Optional[str] = None

class BatchMovementCreate(BatchMovementBase):
    account_set_id: int

class BatchMovement(BatchMovementBase):
    id: int
    account_set_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    account_set_id: Optional[int] = None
    role: str = "USER"

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class DeliveryNoteItemBase(BaseModel):
    material_id: int
    batch_no: Optional[str] = None
    quantity: int
    shipped_qty: int = 0
    unit_price: Optional[Decimal] = None

class DeliveryNoteItemCreate(DeliveryNoteItemBase):
    delivery_note_id: int

class DeliveryNoteItem(DeliveryNoteItemBase):
    id: int
    delivery_note_id: int

    class Config:
        from_attributes = True

class DeliveryNoteBase(BaseModel):
    sales_order_id: int
    customer_id: Optional[int] = None
    delivery_date: date
    status: str = "PENDING"
    ship_to_address: Optional[str] = None
    operator: Optional[str] = None

class DeliveryNoteCreate(DeliveryNoteBase):
    account_set_id: int
    items: List[DeliveryNoteItemBase] = []

class DeliveryNote(DeliveryNoteBase):
    id: int
    account_set_id: int
    delivery_no: str
    items: List[DeliveryNoteItem] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SalesOutboundItemBase(BaseModel):
    material_id: int
    batch_no: str
    location_code: str
    quantity: int
    unit_cost: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None

class SalesOutboundItemCreate(SalesOutboundItemBase):
    sales_outbound_id: int

class SalesOutboundItem(SalesOutboundItemBase):
    id: int
    sales_outbound_id: int

    class Config:
        from_attributes = True

class SalesOutboundBase(BaseModel):
    delivery_note_id: Optional[int] = None
    sales_order_id: Optional[int] = None
    customer_id: Optional[int] = None
    outbound_date: date
    status: str = "PENDING"
    payment_type: Optional[str] = None
    is_credit: bool = False
    operator: Optional[str] = None

class SalesOutboundCreate(SalesOutboundBase):
    account_set_id: int
    items: List[SalesOutboundItemBase] = []

class SalesOutbound(SalesOutboundBase):
    id: int
    account_set_id: int
    outbound_no: str
    items: List[SalesOutboundItem] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ForecastBase(BaseModel):
    material_id: int
    forecast_qty: int
    forecast_date: date
    status: str = "PENDING"
    source_type: Optional[str] = None

class ForecastCreate(ForecastBase):
    account_set_id: int

class Forecast(ForecastBase):
    id: int
    account_set_id: int
    forecast_no: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MRPResultBase(BaseModel):
    mrp_run_no: str
    material_id: int
    parent_material_id: Optional[int] = None
    bom_level: int = 0
    gross_requirement: float = 0.0
    on_hand_qty: float = 0.0
    on_order_qty: float = 0.0
    safety_stock: float = 0.0
    net_requirement: float = 0.0
    planned_order_qty: float = 0.0
    planned_date: Optional[date] = None
    planned_release_date: Optional[date] = None
    planned_type: Optional[str] = None
    material_property: Optional[str] = None
    loss_rate: float = 0.0
    source_order_id: Optional[int] = None
    source_order_no: Optional[str] = None

class MRPRunRequest(BaseModel):
    account_set_id: int
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    demand_date: Optional[date] = None

class MRPResultCreate(MRPResultBase):
    account_set_id: int

class MRPResult(MRPResultBase):
    id: int
    account_set_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PlannedOrderBase(BaseModel):
    material_id: int
    planned_qty: float
    planned_date: date
    order_type: str
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    status: str = "PENDING"

class PlannedOrderCreate(PlannedOrderBase):
    account_set_id: int
    planned_no: str

class PlannedOrder(PlannedOrderBase):
    id: int
    account_set_id: int
    planned_no: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class QualityInspectionItemBase(BaseModel):
    material_id: int
    batch_no: Optional[str] = None
    sample_qty: int
    inspected_qty: int = 0
    qualified_qty: int = 0
    unqualified_qty: int = 0
    quality_status: str = "PENDING"
    defect_desc: Optional[str] = None
    disposal_method: Optional[str] = None

class QualityInspectionItemCreate(QualityInspectionItemBase):
    inspection_id: int

class QualityInspectionItem(QualityInspectionItemBase):
    id: int
    inspection_id: int

    class Config:
        from_attributes = True

class QualityInspectionBase(BaseModel):
    source_type: str
    source_id: int
    inspection_date: date
    status: str = "PENDING"
    inspector: Optional[str] = None
    remarks: Optional[str] = None

class QualityInspectionCreate(QualityInspectionBase):
    account_set_id: int
    items: List[QualityInspectionItemBase] = []

class QualityInspection(QualityInspectionBase):
    id: int
    account_set_id: int
    inspection_no: str
    items: List[QualityInspectionItem] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OutsourcingRequestBase(BaseModel):
    material_id: int
    requested_qty: int
    supplier_id: Optional[int] = None
    planned_date: date
    status: str = "PENDING"
    planned_order_id: Optional[int] = None

class OutsourcingRequestCreate(OutsourcingRequestBase):
    account_set_id: int

class OutsourcingRequest(OutsourcingRequestBase):
    id: int
    account_set_id: int
    request_no: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OutsourcingOrderBase(BaseModel):
    request_id: Optional[int] = None
    supplier_id: int
    material_id: int
    ordered_qty: int
    unit_price: Optional[Decimal] = None
    planned_date: date
    status: str = "PENDING"

class OutsourcingOrderCreate(OutsourcingOrderBase):
    account_set_id: int

class OutsourcingOrder(OutsourcingOrderBase):
    id: int
    account_set_id: int
    order_no: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OutsourcingIssueItemBase(BaseModel):
    material_id: int
    batch_no: Optional[str] = None
    location_code: Optional[str] = None
    quantity: int
    unit_cost: Optional[Decimal] = None

class OutsourcingIssueItemCreate(OutsourcingIssueItemBase):
    issue_id: int

class OutsourcingIssueItem(OutsourcingIssueItemBase):
    id: int
    issue_id: int

    class Config:
        from_attributes = True

class OutsourcingIssueBase(BaseModel):
    outsourcing_order_id: int
    issue_date: date
    status: str = "PENDING"
    operator: Optional[str] = None

class OutsourcingIssueCreate(OutsourcingIssueBase):
    account_set_id: int
    items: List[OutsourcingIssueItemBase] = []

class OutsourcingIssue(OutsourcingIssueBase):
    id: int
    account_set_id: int
    issue_no: str
    items: List[OutsourcingIssueItem] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OutsourcingReplenishItemBase(BaseModel):
    material_id: int
    batch_no: Optional[str] = None
    location_code: Optional[str] = None
    quantity: int
    unit_cost: Optional[Decimal] = None

class OutsourcingReplenishItemCreate(OutsourcingReplenishItemBase):
    replenish_id: int

class OutsourcingReplenishItem(OutsourcingReplenishItemBase):
    id: int
    replenish_id: int

    class Config:
        from_attributes = True

class OutsourcingReplenishBase(BaseModel):
    outsourcing_order_id: int
    issue_id: Optional[int] = None
    replenish_date: date
    status: str = "PENDING"
    operator: Optional[str] = None

class OutsourcingReplenishCreate(OutsourcingReplenishBase):
    account_set_id: int
    items: List[OutsourcingReplenishItemBase] = []

class OutsourcingReplenish(OutsourcingReplenishBase):
    id: int
    account_set_id: int
    replenish_no: str
    items: List[OutsourcingReplenishItem] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OutsourcingReturnItemBase(BaseModel):
    material_id: int
    batch_no: Optional[str] = None
    location_code: Optional[str] = None
    quantity: int
    unit_cost: Optional[Decimal] = None

class OutsourcingReturnItemCreate(OutsourcingReturnItemBase):
    return_id: int

class OutsourcingReturnItem(OutsourcingReturnItemBase):
    id: int
    return_id: int

    class Config:
        from_attributes = True

class OutsourcingReturnBase(BaseModel):
    outsourcing_order_id: int
    issue_id: Optional[int] = None
    return_date: date
    status: str = "PENDING"
    return_reason: Optional[str] = None
    operator: Optional[str] = None

class OutsourcingReturnCreate(OutsourcingReturnBase):
    account_set_id: int
    items: List[OutsourcingReturnItemBase] = []

class OutsourcingReturn(OutsourcingReturnBase):
    id: int
    account_set_id: int
    return_no: str
    items: List[OutsourcingReturnItem] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PurchaseRequestBase(BaseModel):
    material_id: int
    requested_qty: int
    required_date: date
    supplier_id: Optional[int] = None
    status: str = "PENDING"
    planned_order_id: Optional[int] = None

class PurchaseRequestCreate(PurchaseRequestBase):
    account_set_id: int

class PurchaseRequest(PurchaseRequestBase):
    id: int
    account_set_id: int
    request_no: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OutsourcingReceiveItemBase(BaseModel):
    material_id: int
    expected_qty: int
    actual_qty: Optional[int] = None
    unit_price: Optional[Decimal] = None
    batch_no: Optional[str] = None
    expiry_date: Optional[date] = None
    location_code: Optional[str] = None

class OutsourcingReceiveItemCreate(OutsourcingReceiveItemBase):
    receive_id: int

class OutsourcingReceiveItem(OutsourcingReceiveItemBase):
    id: int
    receive_id: int

    class Config:
        from_attributes = True

class OutsourcingReceiveBase(BaseModel):
    outsourcing_order_id: int
    expected_arrival_date: Optional[date] = None
    actual_arrival_date: Optional[date] = None
    status: str = "PENDING"

class OutsourcingReceiveCreate(OutsourcingReceiveBase):
    account_set_id: int
    items: List[OutsourcingReceiveItemBase] = []

class OutsourcingReceive(OutsourcingReceiveBase):
    id: int
    account_set_id: int
    receive_no: str
    items: List[OutsourcingReceiveItem] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OutsourcingInvoiceBase(BaseModel):
    outsourcing_order_id: Optional[int] = None
    receive_id: Optional[int] = None
    supplier_id: int
    amount: Decimal
    tax_amount: Optional[Decimal] = None
    total_amount: Decimal
    invoice_date: date
    status: str = "PENDING"

class OutsourcingInvoiceCreate(OutsourcingInvoiceBase):
    account_set_id: int

class OutsourcingInvoice(OutsourcingInvoiceBase):
    id: int
    account_set_id: int
    invoice_no: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OutsourcingEstimateItemBase(BaseModel):
    material_id: int
    quantity: int
    estimated_unit_cost: Decimal
    estimated_total_cost: Decimal

class OutsourcingEstimateItemCreate(OutsourcingEstimateItemBase):
    estimate_id: int

class OutsourcingEstimateItem(OutsourcingEstimateItemBase):
    id: int
    estimate_id: int

    class Config:
        from_attributes = True

class OutsourcingEstimateBase(BaseModel):
    receive_id: int
    outsourcing_order_id: Optional[int] = None
    estimated_amount: Decimal
    status: str = "PENDING"

class OutsourcingEstimateCreate(OutsourcingEstimateBase):
    account_set_id: int
    items: List[OutsourcingEstimateItemBase] = []

class OutsourcingEstimate(OutsourcingEstimateBase):
    id: int
    account_set_id: int
    estimate_no: str
    items: List[OutsourcingEstimateItem] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OutsourcingAccountBase(BaseModel):
    estimate_id: int
    invoice_id: Optional[int] = None
    receive_id: Optional[int] = None
    actual_amount: Decimal
    estimated_amount: Decimal
    variance_amount: Decimal = 0
    status: str = "PENDING"

class OutsourcingAccountCreate(OutsourcingAccountBase):
    account_set_id: int

class OutsourcingAccount(OutsourcingAccountBase):
    id: int
    account_set_id: int
    account_no: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
