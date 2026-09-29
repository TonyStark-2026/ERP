from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional, List
import datetime

from . import models, schemas
from .models import WorkOrderStatus

def get_material(db: Session, material_id: int):
    return db.query(models.Material).filter(models.Material.id == material_id).first()

def get_material_by_name(db: Session, name: str):
    return db.query(models.Material).filter(models.Material.name == name).first()

def get_material_by_code(db: Session, code: str):
    return db.query(models.Material).filter(models.Material.code == code).first()

def get_material_by_barcode(db: Session, barcode: str):
    return db.query(models.Material).filter(models.Material.barcode == barcode).first()

def search_material(db: Session, keyword: str):
    return db.query(models.Material).filter(
        models.Material.code == keyword |
        models.Material.barcode == keyword |
        models.Material.name.contains(keyword)
    ).first()

def get_materials(db: Session, skip: int = 0, limit: int = 100, name: str = None, code: str = None):
    query = db.query(models.Material)
    if name:
        query = query.filter(models.Material.name.contains(name))
    if code:
        query = query.filter(models.Material.code.contains(code))
    return query.offset(skip).limit(limit).all()

def get_materials_count(db: Session, name: str = None, code: str = None):
    query = db.query(func.count(models.Material.id))
    if name:
        query = query.filter(models.Material.name.contains(name))
    if code:
        query = query.filter(models.Material.code.contains(code))
    return query.scalar()

def create_material(db: Session, material: schemas.MaterialCreate):
    db_material = models.Material(**material.dict())
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material

def update_material(db: Session, material_id: int, material: schemas.MaterialCreate):
    db_material = get_material(db, material_id)
    if not db_material:
        return None
    for key, value in material.dict(exclude_unset=True).items():
        setattr(db_material, key, value)
    db.commit()
    db.refresh(db_material)
    return db_material

def update_material_cva(db: Session, material_id: int, value_score: float, cva_abc_class: str):
    db_material = get_material(db, material_id)
    if db_material:
        db_material.value_score = value_score
        db_material.cva_abc_class = cva_abc_class
        db.commit()
        db.refresh(db_material)
    return db_material

def delete_material(db: Session, material_id: int):
    db_material = get_material(db, material_id)
    if not db_material:
        return False
    db.delete(db_material)
    db.commit()
    return True

def generate_po_code(db: Session, account_set_id: int = 1, abc_class: str = "C", product_code: str = "0000") -> str:
    """生成采购入库编码: PO + YYYYMMDD + ABC分类 + 4位产品编号 + 3位流水号
    示例: PO20260819A0301001
    """
    today = datetime.date.today()
    date_str = today.strftime("%Y%m%d")
    abc = (abc_class or "C").upper()[0]
    prefix = f"PO{date_str}{abc}{product_code}"

    # 查询当天同产品最大的流水号
    last_material = db.query(models.Material).filter(
        models.Material.code.like(f"{prefix}%")
    ).order_by(models.Material.code.desc()).first()

    if last_material:
        try:
            seq = int(last_material.code[-3:]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1

    return f"{prefix}{seq:03d}"

def get_supplier(db: Session, supplier_id: int):
    return db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()

def get_suppliers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Supplier).offset(skip).limit(limit).all()

def get_suppliers_count(db: Session):
    return db.query(func.count(models.Supplier.id)).scalar()

def get_suppliers_with_expiring_tax(db: Session, expiry_date: datetime.date):
    return db.query(models.Supplier).filter(
        models.Supplier.tax_id_expiry <= expiry_date
    ).all()

def create_supplier(db: Session, supplier: schemas.SupplierCreate):
    db_supplier = models.Supplier(**supplier.dict())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

def get_purchase_order(db: Session, order_id: int):
    return db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == order_id).first()

def get_purchase_order_by_no(db: Session, po_no: str):
    return db.query(models.PurchaseOrder).filter(models.PurchaseOrder.po_no == po_no).first()

def get_purchase_orders(db: Session, account_set_id: int = None, skip: int = 0, limit: int = 100, status: str = None):
    query = db.query(models.PurchaseOrder)
    if account_set_id:
        query = query.filter(models.PurchaseOrder.account_set_id == account_set_id)
    if status:
        query = query.filter(models.PurchaseOrder.status == status)
    return query.offset(skip).limit(limit).all()

def get_purchase_orders_count(db: Session, status: str = None):
    query = db.query(func.count(models.PurchaseOrder.id))
    if status:
        query = query.filter(models.PurchaseOrder.status == status)
    return query.scalar()

def create_purchase_order(db: Session, order: schemas.PurchaseOrderCreate):
    db_order = models.PurchaseOrder(**order.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def update_purchase_order(db: Session, order_id: int, order: schemas.PurchaseOrderCreate):
    db_order = get_purchase_order(db, order_id)
    if not db_order:
        return None
    for key, value in order.dict(exclude_unset=True).items():
        setattr(db_order, key, value)
    db.commit()
    db.refresh(db_order)
    return db_order

def delete_purchase_order(db: Session, order_id: int):
    db_order = get_purchase_order(db, order_id)
    if not db_order:
        return False
    db.delete(db_order)
    db.commit()
    return True

def get_workorder(db: Session, workorder_id: int):
    return db.query(models.ProductionWorkOrder).filter(models.ProductionWorkOrder.id == workorder_id).first()

def get_workorder_by_no(db: Session, work_order_no: str):
    return db.query(models.ProductionWorkOrder).filter(models.ProductionWorkOrder.work_order_no == work_order_no).first()

def get_workorders(db: Session, skip: int = 0, limit: int = 100, status: str = None):
    query = db.query(models.ProductionWorkOrder)
    if status:
        query = query.filter(models.ProductionWorkOrder.status == status)
    return query.offset(skip).limit(limit).all()

def get_workorders_count(db: Session, status: str = None):
    query = db.query(func.count(models.ProductionWorkOrder.id))
    if status:
        query = query.filter(models.ProductionWorkOrder.status == status)
    return query.scalar()

def create_workorder(db: Session, workorder: schemas.ProductionWorkOrderCreate):
    db_workorder = models.ProductionWorkOrder(**workorder.dict())
    db.add(db_workorder)
    db.commit()
    db.refresh(db_workorder)
    return db_workorder

def update_workorder_progress(db: Session, workorder_id: int, completed_qty: int, in_progress_qty: int, completion_ratio: float):
    db_workorder = get_workorder(db, workorder_id)
    if db_workorder:
        db_workorder.completed_qty = completed_qty
        db_workorder.in_progress_qty = in_progress_qty
        db_workorder.completion_ratio = completion_ratio
        if completed_qty > 0 and in_progress_qty == 0:
            db_workorder.status = WorkOrderStatus.COMPLETED
        else:
            db_workorder.status = WorkOrderStatus.IN_PROGRESS
        db.commit()
        db.refresh(db_workorder)
    return db_workorder

def get_production_costs(db: Session, work_order_id: int = None):
    query = db.query(models.ProductionCost)
    if work_order_id:
        query = query.filter(models.ProductionCost.work_order_id == work_order_id)
    return query.all()

def create_production_cost(db: Session, cost: schemas.ProductionCostCreate):
    db_cost = models.ProductionCost(**cost.dict())
    db.add(db_cost)
    db.commit()
    db.refresh(db_cost)
    return db_cost

def get_cost_allocations(db: Session, work_order_id: int = None):
    query = db.query(models.CostAllocation)
    if work_order_id:
        query = query.filter(models.CostAllocation.work_order_id == work_order_id)
    return query.all()

def create_cost_allocation(db: Session, allocation: schemas.CostAllocationCreate):
    db_allocation = models.CostAllocation(**allocation.dict())
    db.add(db_allocation)
    db.commit()
    db.refresh(db_allocation)
    return db_allocation

def get_inventory_record(db: Session, material_id: int, location_code: str, batch_no: str = None):
    query = db.query(models.InventoryRecord).filter(
        models.InventoryRecord.material_id == material_id,
        models.InventoryRecord.location_code == location_code
    )
    if batch_no:
        query = query.filter(models.InventoryRecord.batch_no == batch_no)
    return query.first()

def get_inventory_records(db: Session, material_id: int = None, location_code: str = None):
    query = db.query(models.InventoryRecord)
    if material_id:
        query = query.filter(models.InventoryRecord.material_id == material_id)
    if location_code:
        query = query.filter(models.InventoryRecord.location_code == location_code)
    return query.all()

def create_inventory_record(db: Session, record: schemas.InventoryRecordCreate):
    db_record = models.InventoryRecord(**record.dict())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def update_inventory_record(db: Session, record_id: int, quantity: int):
    db_record = db.query(models.InventoryRecord).filter(models.InventoryRecord.id == record_id).first()
    if db_record:
        db_record.quantity = quantity
        db.commit()
        db.refresh(db_record)
    return db_record

def get_inventory_transactions(db: Session, material_id: int = None, transaction_type: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.InventoryTransaction)
    if material_id:
        query = query.filter(models.InventoryTransaction.material_id == material_id)
    if transaction_type:
        query = query.filter(models.InventoryTransaction.transaction_type == transaction_type)
    return query.order_by(models.InventoryTransaction.created_at.desc()).offset(skip).limit(limit).all()

def get_inventory_transactions_count(db: Session, material_id: int = None, transaction_type: str = None):
    query = db.query(func.count(models.InventoryTransaction.id))
    if material_id:
        query = query.filter(models.InventoryTransaction.material_id == material_id)
    if transaction_type:
        query = query.filter(models.InventoryTransaction.transaction_type == transaction_type)
    return query.scalar()

def create_inventory_transaction(db: Session, transaction: schemas.InventoryTransactionCreate):
    db_transaction = models.InventoryTransaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_compliance_alert(db: Session, alert_id: int):
    return db.query(models.ComplianceAlert).filter(models.ComplianceAlert.id == alert_id).first()

def get_compliance_alerts(db: Session, level: str = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.ComplianceAlert)
    if level:
        query = query.filter(models.ComplianceAlert.level == level)
    if status:
        query = query.filter(models.ComplianceAlert.status == status)
    return query.order_by(models.ComplianceAlert.created_at.desc()).offset(skip).limit(limit).all()

def get_compliance_alerts_count(db: Session, level: str = None, status: str = None):
    query = db.query(func.count(models.ComplianceAlert.id))
    if level:
        query = query.filter(models.ComplianceAlert.level == level)
    if status:
        query = query.filter(models.ComplianceAlert.status == status)
    return query.scalar()

def create_compliance_alert(db: Session, alert: schemas.ComplianceAlertCreate):
    db_alert = models.ComplianceAlert(**alert.dict())
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert

def resolve_compliance_alert(db: Session, alert_id: int):
    db_alert = get_compliance_alert(db, alert_id)
    if not db_alert:
        return False
    db_alert.status = "RESOLVED"
    db_alert.resolved_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(db_alert)
    return True

def get_hs_code(db: Session, hs_code: str):
    return db.query(models.HsCode).filter(models.HsCode.hs_code == hs_code).first()

def get_hs_codes(db: Session, skip: int = 0, limit: int = 100, search: str = None):
    query = db.query(models.HsCode)
    if search:
        query = query.filter(or_(
            models.HsCode.hs_code.contains(search),
            models.HsCode.description_cn.contains(search),
            models.HsCode.description_en.contains(search)
        ))
    return query.offset(skip).limit(limit).all()

def get_hs_codes_count(db: Session, search: str = None):
    query = db.query(func.count(models.HsCode.id))
    if search:
        query = query.filter(or_(
            models.HsCode.hs_code.contains(search),
            models.HsCode.description_cn.contains(search),
            models.HsCode.description_en.contains(search)
        ))
    return query.scalar()

def create_hs_code(db: Session, hs_code: schemas.HsCodeCreate):
    db_hs = models.HsCode(**hs_code.dict())
    db.add(db_hs)
    db.commit()
    db.refresh(db_hs)
    return db_hs

def get_country_tax_rule(db: Session, country_code: str):
    return db.query(models.CountryTaxRule).filter(models.CountryTaxRule.country_code == country_code).first()

def get_country_tax_rules(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.CountryTaxRule).offset(skip).limit(limit).all()

def get_country_tax_rules_count(db: Session):
    return db.query(func.count(models.CountryTaxRule.id)).scalar()

def create_country_tax_rule(db: Session, rule: schemas.CountryTaxRuleCreate):
    db_rule = models.CountryTaxRule(**rule.dict())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    import hashlib
    hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
    db_user = models.User(
        username=user.username,
        password=hashed_password,
        email=user.email,
        phone=user.phone
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def verify_user(db: Session, username: str, password: str):
    import hashlib
    db_user = get_user_by_username(db, username)
    if not db_user:
        return None
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    if db_user.password == hashed_password:
        return db_user
    return None

def get_account_set(db: Session, account_set_id: int):
    return db.query(models.AccountSet).filter(models.AccountSet.id == account_set_id).first()

def get_account_set_by_code(db: Session, code: str):
    return db.query(models.AccountSet).filter(models.AccountSet.code == code).first()

def get_account_sets(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.AccountSet).offset(skip).limit(limit).all()

def get_account_sets_count(db: Session):
    return db.query(func.count(models.AccountSet.id)).scalar()

def create_account_set(db: Session, account_set: schemas.AccountSetCreate):
    db_set = models.AccountSet(**account_set.dict())
    db.add(db_set)
    db.commit()
    db.refresh(db_set)
    return db_set

def update_account_set(db: Session, account_set_id: int, account_set: schemas.AccountSetCreate):
    db_set = get_account_set(db, account_set_id)
    if not db_set:
        return None
    for key, value in account_set.dict(exclude_unset=True).items():
        setattr(db_set, key, value)
    db.commit()
    db.refresh(db_set)
    return db_set

def delete_account_set(db: Session, account_set_id: int):
    db_set = get_account_set(db, account_set_id)
    if not db_set:
        return False
    db.delete(db_set)
    db.commit()
    return True

def get_system_config(db: Session, account_set_id: int):
    return db.query(models.SystemConfig).filter(models.SystemConfig.account_set_id == account_set_id).first()

def create_system_config(db: Session, config: schemas.SystemConfigCreate):
    db_config = models.SystemConfig(**config.dict())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

def update_system_config(db: Session, config_id: int, config: schemas.SystemConfigCreate):
    db_config = db.query(models.SystemConfig).filter(models.SystemConfig.id == config_id).first()
    if not db_config:
        return None
    for key, value in config.dict(exclude_unset=True).items():
        setattr(db_config, key, value)
    db.commit()
    db.refresh(db_config)
    return db_config

def get_customer(db: Session, customer_id: int):
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()

def get_customer_by_code(db: Session, code: str):
    return db.query(models.Customer).filter(models.Customer.code == code).first()

def get_customers(db: Session, account_set_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.Customer)
    if account_set_id:
        query = query.filter(models.Customer.account_set_id == account_set_id)
    return query.offset(skip).limit(limit).all()

def get_customers_count(db: Session, account_set_id: int = None):
    query = db.query(func.count(models.Customer.id))
    if account_set_id:
        query = query.filter(models.Customer.account_set_id == account_set_id)
    return query.scalar()

def create_customer(db: Session, customer: schemas.CustomerCreate):
    db_customer = models.Customer(**customer.dict())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def update_customer(db: Session, customer_id: int, customer: schemas.CustomerCreate):
    db_customer = get_customer(db, customer_id)
    if not db_customer:
        return None
    for key, value in customer.dict(exclude_unset=True).items():
        setattr(db_customer, key, value)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def delete_customer(db: Session, customer_id: int):
    db_customer = get_customer(db, customer_id)
    if not db_customer:
        return False
    db.delete(db_customer)
    db.commit()
    return True

def get_price_list(db: Session, price_list_id: int):
    return db.query(models.PriceList).filter(models.PriceList.id == price_list_id).first()

def get_price_lists(db: Session, account_set_id: int = None, material_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.PriceList)
    if account_set_id:
        query = query.filter(models.PriceList.account_set_id == account_set_id)
    if material_id:
        query = query.filter(models.PriceList.material_id == material_id)
    return query.offset(skip).limit(limit).all()

def get_price_lists_count(db: Session, account_set_id: int = None, material_id: int = None):
    query = db.query(func.count(models.PriceList.id))
    if account_set_id:
        query = query.filter(models.PriceList.account_set_id == account_set_id)
    if material_id:
        query = query.filter(models.PriceList.material_id == material_id)
    return query.scalar()

def create_price_list(db: Session, price_list: schemas.PriceListCreate):
    db_price = models.PriceList(**price_list.dict())
    db.add(db_price)
    db.commit()
    db.refresh(db_price)
    return db_price

def get_purchase_order_template(db: Session, template_id: int):
    return db.query(models.PurchaseOrderTemplate).filter(models.PurchaseOrderTemplate.id == template_id).first()

def get_purchase_order_templates(db: Session, account_set_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.PurchaseOrderTemplate)
    if account_set_id:
        query = query.filter(models.PurchaseOrderTemplate.account_set_id == account_set_id)
    return query.offset(skip).limit(limit).all()

def create_purchase_order_template(db: Session, template: schemas.PurchaseOrderTemplateCreate):
    items_data = template.dict().pop('items', [])
    db_template = models.PurchaseOrderTemplate(**template.dict())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    for item_data in items_data:
        item_data['template_id'] = db_template.id
        db_item = models.PurchaseOrderTemplateItem(**item_data)
        db.add(db_item)
    db.commit()
    db.refresh(db_template)
    return db_template

def get_sales_order(db: Session, sales_order_id: int):
    return db.query(models.SalesOrder).filter(models.SalesOrder.id == sales_order_id).first()

def get_sales_order_by_no(db: Session, so_no: str):
    return db.query(models.SalesOrder).filter(models.SalesOrder.so_no == so_no).first()

def get_sales_orders(db: Session, account_set_id: int = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.SalesOrder)
    if account_set_id:
        query = query.filter(models.SalesOrder.account_set_id == account_set_id)
    if status:
        query = query.filter(models.SalesOrder.status == status)
    return query.offset(skip).limit(limit).all()

def get_sales_orders_count(db: Session, account_set_id: int = None, status: str = None):
    query = db.query(func.count(models.SalesOrder.id))
    if account_set_id:
        query = query.filter(models.SalesOrder.account_set_id == account_set_id)
    if status:
        query = query.filter(models.SalesOrder.status == status)
    return query.scalar()

def create_sales_order(db: Session, sales_order: schemas.SalesOrderCreate):
    items_data = sales_order.items
    db_order = models.SalesOrder(**sales_order.dict(exclude={'items'}))
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    for item_data in items_data:
        item_dict = item_data.dict() if hasattr(item_data, 'dict') else item_data
        item_dict['sales_order_id'] = db_order.id
        db_item = models.SalesOrderItem(**item_dict)
        db.add(db_item)
    db.commit()
    db.refresh(db_order)
    return db_order

def update_sales_order(db: Session, sales_order_id: int, sales_order: schemas.SalesOrderCreate):
    db_order = get_sales_order(db, sales_order_id)
    if not db_order:
        return None
    for key, value in sales_order.dict(exclude_unset=True).items():
        if key != 'items':
            setattr(db_order, key, value)
    db.commit()
    db.refresh(db_order)
    return db_order

def delete_sales_order(db: Session, sales_order_id: int):
    db_order = get_sales_order(db, sales_order_id)
    if not db_order:
        return False
    db.query(models.SalesOrderItem).filter(models.SalesOrderItem.sales_order_id == sales_order_id).delete()
    db.delete(db_order)
    db.commit()
    return True

def get_bom(db: Session, bom_id: int):
    return db.query(models.BOM).filter(models.BOM.id == bom_id).first()

def get_boms(db: Session, account_set_id: int = None, product_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.BOM)
    if account_set_id:
        query = query.filter(models.BOM.account_set_id == account_set_id)
    if product_id:
        query = query.filter(models.BOM.product_id == product_id)
    return query.offset(skip).limit(limit).all()

def create_bom(db: Session, bom: schemas.BOMCreate):
    items_data = bom.items
    db_bom = models.BOM(**bom.dict(exclude={'items'}))
    db.add(db_bom)
    db.commit()
    db.refresh(db_bom)
    for item_data in items_data:
        item_dict = item_data.dict() if hasattr(item_data, 'dict') else item_data
        item_dict['bom_id'] = db_bom.id
        db_item = models.BOMItem(**item_dict)
        db.add(db_item)
    db.commit()
    db.refresh(db_bom)
    return db_bom

def get_contract(db: Session, contract_id: int):
    return db.query(models.Contract).filter(models.Contract.id == contract_id).first()

def get_contract_by_no(db: Session, contract_no: str):
    return db.query(models.Contract).filter(models.Contract.contract_no == contract_no).first()

def get_contracts(db: Session, account_set_id: int = None, contract_type: str = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.Contract)
    if account_set_id:
        query = query.filter(models.Contract.account_set_id == account_set_id)
    if contract_type:
        query = query.filter(models.Contract.contract_type == contract_type)
    if status:
        query = query.filter(models.Contract.status == status)
    return query.offset(skip).limit(limit).all()

def get_contracts_count(db: Session, account_set_id: int = None, contract_type: str = None, status: str = None):
    query = db.query(func.count(models.Contract.id))
    if account_set_id:
        query = query.filter(models.Contract.account_set_id == account_set_id)
    if contract_type:
        query = query.filter(models.Contract.contract_type == contract_type)
    if status:
        query = query.filter(models.Contract.status == status)
    return query.scalar()

def create_contract(db: Session, contract: schemas.ContractCreate):
    db_contract = models.Contract(**contract.dict())
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    return db_contract

def update_contract(db: Session, contract_id: int, contract: schemas.ContractCreate):
    db_contract = get_contract(db, contract_id)
    if not db_contract:
        return None
    for key, value in contract.dict(exclude_unset=True).items():
        setattr(db_contract, key, value)
    db.commit()
    db.refresh(db_contract)
    return db_contract

def get_employee(db: Session, employee_id: int):
    return db.query(models.Employee).filter(models.Employee.id == employee_id).first()

def get_employee_by_no(db: Session, employee_no: str):
    return db.query(models.Employee).filter(models.Employee.employee_no == employee_no).first()

def get_employees(db: Session, account_set_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.Employee)
    if account_set_id:
        query = query.filter(models.Employee.account_set_id == account_set_id)
    return query.offset(skip).limit(limit).all()

def get_employees_count(db: Session, account_set_id: int = None):
    query = db.query(func.count(models.Employee.id))
    if account_set_id:
        query = query.filter(models.Employee.account_set_id == account_set_id)
    return query.scalar()

def create_employee(db: Session, employee: schemas.EmployeeCreate):
    db_employee = models.Employee(**employee.dict())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

def update_employee(db: Session, employee_id: int, employee: schemas.EmployeeCreate):
    db_employee = get_employee(db, employee_id)
    if not db_employee:
        return None
    for key, value in employee.dict(exclude_unset=True).items():
        setattr(db_employee, key, value)
    db.commit()
    db.refresh(db_employee)
    return db_employee

def delete_employee(db: Session, employee_id: int):
    db_employee = get_employee(db, employee_id)
    if not db_employee:
        return False
    db.delete(db_employee)
    db.commit()
    return True

def get_voucher(db: Session, voucher_id: int):
    return db.query(models.VoucherDB).filter(models.VoucherDB.id == voucher_id).first()

def get_voucher_by_no(db: Session, voucher_no: str):
    return db.query(models.VoucherDB).filter(models.VoucherDB.voucher_no == voucher_no).first()

def get_vouchers(db: Session, account_set_id: int = None, status: str = None,
                 start_date=None, end_date=None, voucher_type: str = None,
                 skip: int = 0, limit: int = 100):
    query = db.query(models.VoucherDB)
    if account_set_id:
        query = query.filter(models.VoucherDB.account_set_id == account_set_id)
    if status:
        query = query.filter(models.VoucherDB.status == status)
    if start_date is not None:
        try:
            import datetime as _dt
            sd = start_date
            if isinstance(sd, str):
                sd = _dt.date.fromisoformat(sd[:10])
            if hasattr(models.VoucherDB, 'voucher_date'):
                query = query.filter(models.VoucherDB.voucher_date >= sd)
        except Exception:
            pass
    if end_date is not None:
        try:
            import datetime as _dt
            ed = end_date
            if isinstance(ed, str):
                ed = _dt.date.fromisoformat(ed[:10])
            if hasattr(models.VoucherDB, 'voucher_date'):
                query = query.filter(models.VoucherDB.voucher_date <= ed)
        except Exception:
            pass
    if voucher_type:
        if hasattr(models.VoucherDB, 'voucher_type'):
            query = query.filter(models.VoucherDB.voucher_type == voucher_type)
    return query.order_by(models.VoucherDB.voucher_date.desc()).offset(skip).limit(limit).all()

def get_vouchers_count(db: Session, account_set_id: int = None, status: str = None,
                       start_date=None, end_date=None, voucher_type: str = None):
    query = db.query(func.count(models.VoucherDB.id))
    if account_set_id:
        query = query.filter(models.VoucherDB.account_set_id == account_set_id)
    if status:
        query = query.filter(models.VoucherDB.status == status)
    if start_date is not None:
        try:
            import datetime as _dt
            sd = start_date
            if isinstance(sd, str):
                sd = _dt.date.fromisoformat(sd[:10])
            if hasattr(models.VoucherDB, 'voucher_date'):
                query = query.filter(models.VoucherDB.voucher_date >= sd)
        except Exception:
            pass
    if end_date is not None:
        try:
            import datetime as _dt
            ed = end_date
            if isinstance(ed, str):
                ed = _dt.date.fromisoformat(ed[:10])
            if hasattr(models.VoucherDB, 'voucher_date'):
                query = query.filter(models.VoucherDB.voucher_date <= ed)
        except Exception:
            pass
    if voucher_type:
        if hasattr(models.VoucherDB, 'voucher_type'):
            query = query.filter(models.VoucherDB.voucher_type == voucher_type)
    return query.scalar()

def create_voucher(db: Session, voucher: schemas.VoucherDBCreate):
    entries_data = voucher.dict().pop('entries', [])
    db_voucher = models.VoucherDB(**voucher.dict())
    db.add(db_voucher)
    db.commit()
    db.refresh(db_voucher)
    for entry_data in entries_data:
        entry_data['voucher_id'] = db_voucher.id
        db_entry = models.VoucherEntry(**entry_data)
        db.add(db_entry)
    db.commit()
    db.refresh(db_voucher)
    return db_voucher

def update_voucher_status(db: Session, voucher_id: int, status: str, approver: str = None, poster: str = None):
    db_voucher = get_voucher(db, voucher_id)
    if not db_voucher:
        return None
    db_voucher.status = status
    if approver:
        db_voucher.approver = approver
        db_voucher.approved_at = datetime.datetime.utcnow()
    if poster:
        db_voucher.poster = poster
        db_voucher.posted_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(db_voucher)
    return db_voucher

def get_cash_flow_items(db: Session, account_set_id: int = None, category: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.CashFlowItem)
    if account_set_id:
        query = query.filter(models.CashFlowItem.account_set_id == account_set_id)
    if category:
        query = query.filter(models.CashFlowItem.category == category)
    return query.offset(skip).limit(limit).all()

def create_cash_flow_item(db: Session, item: schemas.CashFlowItemCreate):
    db_item = models.CashFlowItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_exchange_rate(db: Session, from_currency: str, to_currency: str, rate_date: datetime.date):
    return db.query(models.ExchangeRate).filter(
        models.ExchangeRate.from_currency == from_currency,
        models.ExchangeRate.to_currency == to_currency,
        models.ExchangeRate.rate_date == rate_date
    ).first()

def get_exchange_rates(db: Session, account_set_id: int = None, from_currency: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.ExchangeRate)
    if account_set_id:
        query = query.filter(models.ExchangeRate.account_set_id == account_set_id)
    if from_currency:
        query = query.filter(models.ExchangeRate.from_currency == from_currency)
    return query.order_by(models.ExchangeRate.rate_date.desc()).offset(skip).limit(limit).all()

def create_exchange_rate(db: Session, rate: schemas.ExchangeRateCreate):
    db_rate = models.ExchangeRate(**rate.dict())
    db.add(db_rate)
    db.commit()
    db.refresh(db_rate)
    return db_rate

def get_stocktaking_task(db: Session, task_id: int):
    return db.query(models.StocktakingTask).filter(models.StocktakingTask.id == task_id).first()

def get_stocktaking_tasks(db: Session, account_set_id: int = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.StocktakingTask)
    if account_set_id:
        query = query.filter(models.StocktakingTask.account_set_id == account_set_id)
    if status:
        query = query.filter(models.StocktakingTask.status == status)
    return query.order_by(models.StocktakingTask.start_date.desc()).offset(skip).limit(limit).all()

def create_stocktaking_task(db: Session, task: schemas.StocktakingTaskCreate):
    db_task = models.StocktakingTask(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_stocktaking_task_status(db: Session, task_id: int, status: str):
    db_task = get_stocktaking_task(db, task_id)
    if not db_task:
        return None
    db_task.status = status
    if status == "COMPLETED":
        db_task.completed_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(db_task)
    return db_task

def get_stocktaking_item(db: Session, item_id: int):
    return db.query(models.StocktakingItem).filter(models.StocktakingItem.id == item_id).first()

def create_stocktaking_item(db: Session, item: schemas.StocktakingItemCreate):
    db_item = models.StocktakingItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_stocktaking_item(db: Session, item_id: int, actual_qty: int, variance: int, variance_amount: float, reason: str = None):
    db_item = get_stocktaking_item(db, item_id)
    if not db_item:
        return None
    db_item.actual_qty = actual_qty
    db_item.variance = variance
    db_item.variance_amount = variance_amount
    db_item.reason = reason
    db.commit()
    db.refresh(db_item)
    return db_item

def get_batch_rule(db: Session, rule_id: int):
    return db.query(models.BatchRule).filter(models.BatchRule.id == rule_id).first()

def get_batch_rules(db: Session, account_set_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.BatchRule)
    if account_set_id:
        query = query.filter(models.BatchRule.account_set_id == account_set_id)
    return query.offset(skip).limit(limit).all()

def create_batch_rule(db: Session, rule: schemas.BatchRuleCreate):
    db_rule = models.BatchRule(**rule.dict())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

def update_batch_rule(db: Session, rule_id: int, rule: schemas.BatchRuleCreate):
    db_rule = get_batch_rule(db, rule_id)
    if not db_rule:
        return None
    for key, value in rule.dict(exclude_unset=True).items():
        setattr(db_rule, key, value)
    db.commit()
    db.refresh(db_rule)
    return db_rule

def delete_batch_rule(db: Session, rule_id: int):
    db_rule = get_batch_rule(db, rule_id)
    if not db_rule:
        return False
    db.delete(db_rule)
    db.commit()
    return True

def get_storage_location(db: Session, location_id: int):
    return db.query(models.StorageLocation).filter(models.StorageLocation.id == location_id).first()

def get_storage_location_by_code(db: Session, location_code: str):
    return db.query(models.StorageLocation).filter(models.StorageLocation.location_code == location_code).first()

def get_storage_locations(db: Session, account_set_id: int = None, parent_code: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.StorageLocation)
    if account_set_id:
        query = query.filter(models.StorageLocation.account_set_id == account_set_id)
    if parent_code is not None:
        query = query.filter(models.StorageLocation.parent_code == parent_code)
    return query.offset(skip).limit(limit).all()

def create_storage_location(db: Session, location: schemas.StorageLocationCreate):
    db_location = models.StorageLocation(**location.dict())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

def update_storage_location(db: Session, location_id: int, location: schemas.StorageLocationCreate):
    db_location = get_storage_location(db, location_id)
    if not db_location:
        return None
    for key, value in location.dict(exclude_unset=True).items():
        setattr(db_location, key, value)
    db.commit()
    db.refresh(db_location)
    return db_location

def delete_storage_location(db: Session, location_id: int):
    db_location = get_storage_location(db, location_id)
    if not db_location:
        return False
    db.delete(db_location)
    db.commit()
    return True

def get_unit_conversion(db: Session, conversion_id: int):
    return db.query(models.UnitConversion).filter(models.UnitConversion.id == conversion_id).first()

def get_unit_conversions(db: Session, account_set_id: int = None, material_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.UnitConversion)
    if account_set_id:
        query = query.filter(models.UnitConversion.account_set_id == account_set_id)
    if material_id:
        query = query.filter(models.UnitConversion.material_id == material_id)
    return query.offset(skip).limit(limit).all()

def create_unit_conversion(db: Session, conversion: schemas.UnitConversionCreate):
    db_conversion = models.UnitConversion(**conversion.dict())
    db.add(db_conversion)
    db.commit()
    db.refresh(db_conversion)
    return db_conversion

def delete_unit_conversion(db: Session, conversion_id: int):
    db_conversion = get_unit_conversion(db, conversion_id)
    if not db_conversion:
        return False
    db.delete(db_conversion)
    db.commit()
    return True

def get_purchase_agreement(db: Session, agreement_id: int):
    return db.query(models.PurchaseAgreement).filter(models.PurchaseAgreement.id == agreement_id).first()

def get_purchase_agreement_by_no(db: Session, agreement_no: str):
    return db.query(models.PurchaseAgreement).filter(models.PurchaseAgreement.agreement_no == agreement_no).first()

def get_purchase_agreements(db: Session, account_set_id: int = None, supplier_id: int = None, material_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.PurchaseAgreement)
    if account_set_id:
        query = query.filter(models.PurchaseAgreement.account_set_id == account_set_id)
    if supplier_id:
        query = query.filter(models.PurchaseAgreement.supplier_id == supplier_id)
    if material_id:
        query = query.filter(models.PurchaseAgreement.material_id == material_id)
    return query.offset(skip).limit(limit).all()

def create_purchase_agreement(db: Session, agreement: schemas.PurchaseAgreementCreate):
    db_agreement = models.PurchaseAgreement(**agreement.dict())
    db.add(db_agreement)
    db.commit()
    db.refresh(db_agreement)
    return db_agreement

def update_purchase_agreement(db: Session, agreement_id: int, agreement: schemas.PurchaseAgreementCreate):
    db_agreement = get_purchase_agreement(db, agreement_id)
    if not db_agreement:
        return None
    for key, value in agreement.dict(exclude_unset=True).items():
        setattr(db_agreement, key, value)
    db.commit()
    db.refresh(db_agreement)
    return db_agreement

def delete_purchase_agreement(db: Session, agreement_id: int):
    db_agreement = get_purchase_agreement(db, agreement_id)
    if not db_agreement:
        return False
    db.delete(db_agreement)
    db.commit()
    return True

def get_pre_receipt(db: Session, pre_receipt_id: int):
    return db.query(models.PreReceipt).filter(models.PreReceipt.id == pre_receipt_id).first()

def get_pre_receipt_by_no(db: Session, pre_receipt_no: str):
    return db.query(models.PreReceipt).filter(models.PreReceipt.pre_receipt_no == pre_receipt_no).first()

def get_pre_receipts(db: Session, account_set_id: int = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.PreReceipt)
    if account_set_id:
        query = query.filter(models.PreReceipt.account_set_id == account_set_id)
    if status:
        query = query.filter(models.PreReceipt.status == status)
    return query.order_by(models.PreReceipt.created_at.desc()).offset(skip).limit(limit).all()

def create_pre_receipt(db: Session, pre_receipt: schemas.PreReceiptCreate):
    items_data = pre_receipt.dict().pop('items', [])
    db_pre_receipt = models.PreReceipt(**pre_receipt.dict())
    db.add(db_pre_receipt)
    db.commit()
    db.refresh(db_pre_receipt)
    for item_data in items_data:
        item_data['pre_receipt_id'] = db_pre_receipt.id
        db_item = models.PreReceiptItem(**item_data)
        db.add(db_item)
    db.commit()
    db.refresh(db_pre_receipt)
    return db_pre_receipt

def update_pre_receipt(db: Session, pre_receipt_id: int, pre_receipt: schemas.PreReceiptCreate):
    db_pre_receipt = get_pre_receipt(db, pre_receipt_id)
    if not db_pre_receipt:
        return None
    for key, value in pre_receipt.dict(exclude_unset=True).items():
        if key != 'items':
            setattr(db_pre_receipt, key, value)
    db.commit()
    db.refresh(db_pre_receipt)
    return db_pre_receipt

def get_inbound_order(db: Session, inbound_id: int):
    return db.query(models.InboundOrder).filter(models.InboundOrder.id == inbound_id).first()

def get_inbound_order_by_no(db: Session, inbound_no: str):
    return db.query(models.InboundOrder).filter(models.InboundOrder.inbound_no == inbound_no).first()

def get_inbound_orders(db: Session, account_set_id: int = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.InboundOrder)
    if account_set_id:
        query = query.filter(models.InboundOrder.account_set_id == account_set_id)
    if status:
        query = query.filter(models.InboundOrder.status == status)
    return query.order_by(models.InboundOrder.inbound_date.desc()).offset(skip).limit(limit).all()

def create_inbound_order(db: Session, inbound_order: schemas.InboundOrderCreate):
    items_data = inbound_order.dict().pop('items', [])
    db_inbound = models.InboundOrder(**inbound_order.dict())
    db.add(db_inbound)
    db.commit()
    db.refresh(db_inbound)
    for item_data in items_data:
        item_data['inbound_order_id'] = db_inbound.id
        db_item = models.InboundOrderItem(**item_data)
        db.add(db_item)
    db.commit()
    db.refresh(db_inbound)
    return db_inbound

def update_inbound_order_status(db: Session, inbound_id: int, status: str, quality_status: str = None):
    db_inbound = get_inbound_order(db, inbound_id)
    if not db_inbound:
        return None
    db_inbound.status = status
    if quality_status:
        db_inbound.quality_status = quality_status
    db.commit()
    db.refresh(db_inbound)
    return db_inbound

def get_outbound_order(db: Session, outbound_id: int):
    return db.query(models.OutboundOrder).filter(models.OutboundOrder.id == outbound_id).first()

def get_outbound_order_by_no(db: Session, outbound_no: str):
    return db.query(models.OutboundOrder).filter(models.OutboundOrder.outbound_no == outbound_no).first()

def get_outbound_orders(db: Session, account_set_id: int = None, outbound_type: str = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.OutboundOrder)
    if account_set_id:
        query = query.filter(models.OutboundOrder.account_set_id == account_set_id)
    if outbound_type:
        query = query.filter(models.OutboundOrder.outbound_type == outbound_type)
    if status:
        query = query.filter(models.OutboundOrder.status == status)
    return query.order_by(models.OutboundOrder.outbound_date.desc()).offset(skip).limit(limit).all()

def create_outbound_order(db: Session, outbound_order: schemas.OutboundOrderCreate):
    items_data = outbound_order.dict().pop('items', [])
    db_outbound = models.OutboundOrder(**outbound_order.dict())
    db.add(db_outbound)
    db.commit()
    db.refresh(db_outbound)
    for item_data in items_data:
        item_data['outbound_order_id'] = db_outbound.id
        db_item = models.OutboundOrderItem(**item_data)
        db.add(db_item)
    db.commit()
    db.refresh(db_outbound)
    return db_outbound

def update_outbound_order_status(db: Session, outbound_id: int, status: str):
    db_outbound = get_outbound_order(db, outbound_id)
    if not db_outbound:
        return None
    db_outbound.status = status
    db.commit()
    db.refresh(db_outbound)
    return db_outbound

def get_batch_inventory(db: Session, inventory_id: int):
    return db.query(models.BatchInventory).filter(models.BatchInventory.id == inventory_id).first()

def get_batch_inventories(db: Session, account_set_id: int = None, material_id: int = None, location_code: str = None, batch_no: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.BatchInventory)
    if account_set_id:
        query = query.filter(models.BatchInventory.account_set_id == account_set_id)
    if material_id:
        query = query.filter(models.BatchInventory.material_id == material_id)
    if location_code:
        query = query.filter(models.BatchInventory.location_code == location_code)
    if batch_no:
        query = query.filter(models.BatchInventory.batch_no == batch_no)
    return query.offset(skip).limit(limit).all()

def create_batch_inventory(db: Session, inventory: schemas.BatchInventoryCreate):
    total_cost = inventory.quantity * inventory.unit_cost
    db_inventory = models.BatchInventory(**inventory.dict(), total_cost=total_cost)
    db.add(db_inventory)
    db.commit()
    db.refresh(db_inventory)
    return db_inventory

def update_batch_inventory(db: Session, inventory_id: int, quantity: int, unit_cost: float = None):
    db_inventory = get_batch_inventory(db, inventory_id)
    if not db_inventory:
        return None
    db_inventory.quantity = quantity
    if unit_cost is not None:
        db_inventory.unit_cost = unit_cost
    db_inventory.total_cost = db_inventory.quantity * db_inventory.unit_cost
    db_inventory.last_movement_date = datetime.date.today()
    db.commit()
    db.refresh(db_inventory)
    return db_inventory

def get_batch_movements(db: Session, account_set_id: int = None, material_id: int = None, batch_no: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.BatchMovement)
    if account_set_id:
        query = query.filter(models.BatchMovement.account_set_id == account_set_id)
    if material_id:
        query = query.filter(models.BatchMovement.material_id == material_id)
    if batch_no:
        query = query.filter(models.BatchMovement.batch_no == batch_no)
    return query.order_by(models.BatchMovement.created_at.desc()).offset(skip).limit(limit).all()

def create_batch_movement(db: Session, movement: schemas.BatchMovementCreate):
    db_movement = models.BatchMovement(**movement.dict())
    db.add(db_movement)
    db.commit()
    db.refresh(db_movement)
    return db_movement

def get_delivery_note(db: Session, delivery_note_id: int):
    return db.query(models.DeliveryNote).filter(models.DeliveryNote.id == delivery_note_id).first()

def get_delivery_note_by_no(db: Session, delivery_no: str):
    return db.query(models.DeliveryNote).filter(models.DeliveryNote.delivery_no == delivery_no).first()

def get_delivery_notes(db: Session, account_set_id: int = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.DeliveryNote)
    if account_set_id:
        query = query.filter(models.DeliveryNote.account_set_id == account_set_id)
    if status:
        query = query.filter(models.DeliveryNote.status == status)
    return query.order_by(models.DeliveryNote.created_at.desc()).offset(skip).limit(limit).all()

def create_delivery_note(db: Session, delivery_note: schemas.DeliveryNoteCreate):
    items_data = delivery_note.dict().pop('items', [])
    db_note = models.DeliveryNote(**delivery_note.dict())
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    for item_data in items_data:
        item_data['delivery_note_id'] = db_note.id
        db_item = models.DeliveryNoteItem(**item_data)
        db.add(db_item)
    db.commit()
    db.refresh(db_note)
    return db_note

def update_delivery_note_status(db: Session, delivery_note_id: int, status: str):
    db_note = get_delivery_note(db, delivery_note_id)
    if not db_note:
        return None
    db_note.status = status
    db.commit()
    db.refresh(db_note)
    return db_note

def get_sales_outbound(db: Session, outbound_id: int):
    return db.query(models.SalesOutbound).filter(models.SalesOutbound.id == outbound_id).first()

def get_sales_outbound_by_no(db: Session, outbound_no: str):
    return db.query(models.SalesOutbound).filter(models.SalesOutbound.outbound_no == outbound_no).first()

def get_sales_outbounds(db: Session, account_set_id: int = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.SalesOutbound)
    if account_set_id:
        query = query.filter(models.SalesOutbound.account_set_id == account_set_id)
    if status:
        query = query.filter(models.SalesOutbound.status == status)
    return query.order_by(models.SalesOutbound.outbound_date.desc()).offset(skip).limit(limit).all()

def create_sales_outbound(db: Session, outbound: schemas.SalesOutboundCreate):
    items_data = outbound.dict().pop('items', [])
    db_outbound = models.SalesOutbound(**outbound.dict())
    db.add(db_outbound)
    db.commit()
    db.refresh(db_outbound)
    for item_data in items_data:
        item_data['sales_outbound_id'] = db_outbound.id
        db_item = models.SalesOutboundItem(**item_data)
        db.add(db_item)
    db.commit()
    db.refresh(db_outbound)
    return db_outbound

def update_sales_outbound_status(db: Session, outbound_id: int, status: str):
    db_outbound = get_sales_outbound(db, outbound_id)
    if not db_outbound:
        return None
    db_outbound.status = status
    db.commit()
    db.refresh(db_outbound)
    return db_outbound

def get_forecast(db: Session, forecast_id: int):
    return db.query(models.Forecast).filter(models.Forecast.id == forecast_id).first()

def get_forecast_by_no(db: Session, forecast_no: str):
    return db.query(models.Forecast).filter(models.Forecast.forecast_no == forecast_no).first()

def get_forecasts(db: Session, account_set_id: int = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.Forecast)
    if account_set_id:
        query = query.filter(models.Forecast.account_set_id == account_set_id)
    if status:
        query = query.filter(models.Forecast.status == status)
    return query.order_by(models.Forecast.forecast_date.desc()).offset(skip).limit(limit).all()

def get_forecasts_count(db: Session, account_set_id: int = None, status: str = None):
    query = db.query(func.count(models.Forecast.id))
    if account_set_id:
        query = query.filter(models.Forecast.account_set_id == account_set_id)
    if status:
        query = query.filter(models.Forecast.status == status)
    return query.scalar()

def create_forecast(db: Session, forecast: schemas.ForecastCreate):
    db_forecast = models.Forecast(**forecast.dict())
    db.add(db_forecast)
    db.commit()
    db.refresh(db_forecast)
    return db_forecast

def update_forecast_status(db: Session, forecast_id: int, status: str):
    db_forecast = get_forecast(db, forecast_id)
    if not db_forecast:
        return None
    db_forecast.status = status
    db.commit()
    db.refresh(db_forecast)
    return db_forecast

def get_mrp_results(db: Session, mrp_run_no: str = None, account_set_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.MRPResult)
    if mrp_run_no:
        query = query.filter(models.MRPResult.mrp_run_no == mrp_run_no)
    if account_set_id:
        query = query.filter(models.MRPResult.account_set_id == account_set_id)
    return query.offset(skip).limit(limit).all()

def get_mrp_runs(db: Session, account_set_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.MRPResult).distinct(models.MRPResult.mrp_run_no)
    if account_set_id:
        query = query.filter(models.MRPResult.account_set_id == account_set_id)
    runs = []
    for result in query.offset(skip).limit(limit).all():
        run_data = {
            "mrp_run_no": result.mrp_run_no,
            "run_time": result.created_at,
            "account_set_id": result.account_set_id
        }
        runs.append(run_data)
    return runs

def create_mrp_result(db: Session, result: schemas.MRPResultCreate):
    db_result = models.MRPResult(**result.dict())
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result

def get_production_workorders(db: Session, account_set_id: int = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.ProductionWorkOrder)
    if account_set_id:
        query = query.filter(models.ProductionWorkOrder.account_set_id == account_set_id)
    if status:
        query = query.filter(models.ProductionWorkOrder.status == status)
    return query.offset(skip).limit(limit).all()

def create_production_workorder(db: Session, work_order: schemas.ProductionWorkOrderCreate):
    db_work_order = models.ProductionWorkOrder(**work_order.dict())
    db.add(db_work_order)
    db.commit()
    db.refresh(db_work_order)
    return db_work_order

def get_planned_order(db: Session, planned_order_id: int):
    return db.query(models.PlannedOrder).filter(models.PlannedOrder.id == planned_order_id).first()

def get_planned_order_by_no(db: Session, planned_no: str):
    return db.query(models.PlannedOrder).filter(models.PlannedOrder.planned_no == planned_no).first()

def get_planned_orders(db: Session, account_set_id: int = None, order_type: str = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.PlannedOrder)
    if account_set_id:
        query = query.filter(models.PlannedOrder.account_set_id == account_set_id)
    if order_type:
        query = query.filter(models.PlannedOrder.order_type == order_type)
    if status:
        query = query.filter(models.PlannedOrder.status == status)
    return query.order_by(models.PlannedOrder.planned_date).offset(skip).limit(limit).all()

def create_planned_order(db: Session, planned_order: schemas.PlannedOrderCreate):
    db_order = models.PlannedOrder(**planned_order.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def update_planned_order_status(db: Session, planned_order_id: int, status: str):
    db_order = get_planned_order(db, planned_order_id)
    if not db_order:
        return None
    db_order.status = status
    db.commit()
    db.refresh(db_order)
    return db_order

def delete_planned_order(db: Session, planned_order_id: int):
    db_order = get_planned_order(db, planned_order_id)
    if not db_order:
        return False
    db.delete(db_order)
    db.commit()
    return True

def get_quality_inspection(db: Session, inspection_id: int):
    return db.query(models.QualityInspection).filter(models.QualityInspection.id == inspection_id).first()

def get_quality_inspection_by_no(db: Session, inspection_no: str):
    return db.query(models.QualityInspection).filter(models.QualityInspection.inspection_no == inspection_no).first()

def get_quality_inspections(db: Session, account_set_id: int = None, source_type: str = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.QualityInspection)
    if account_set_id:
        query = query.filter(models.QualityInspection.account_set_id == account_set_id)
    if source_type:
        query = query.filter(models.QualityInspection.source_type == source_type)
    if status:
        query = query.filter(models.QualityInspection.status == status)
    return query.order_by(models.QualityInspection.inspection_date.desc()).offset(skip).limit(limit).all()

def create_quality_inspection(db: Session, inspection: schemas.QualityInspectionCreate):
    items_data = inspection.dict().pop('items', [])
    db_inspection = models.QualityInspection(**inspection.dict())
    db.add(db_inspection)
    db.commit()
    db.refresh(db_inspection)
    for item_data in items_data:
        item_data['inspection_id'] = db_inspection.id
        db_item = models.QualityInspectionItem(**item_data)
        db.add(db_item)
    db.commit()
    db.refresh(db_inspection)
    return db_inspection

def update_quality_inspection(db: Session, inspection_id: int, results: List[dict]):
    db_inspection = get_quality_inspection(db, inspection_id)
    if not db_inspection:
        return None
    
    all_passed = True
    for result in results:
        item = db.query(models.QualityInspectionItem).filter(
            models.QualityInspectionItem.id == result["item_id"]
        ).first()
        if item:
            item.inspected_qty = result.get("inspected_qty", item.inspected_qty)
            item.qualified_qty = result.get("qualified_qty", item.qualified_qty)
            item.unqualified_qty = result.get("unqualified_qty", item.unqualified_qty)
            item.quality_status = result.get("quality_status", item.quality_status)
            item.defect_desc = result.get("defect_desc", item.defect_desc)
            item.disposal_method = result.get("disposal_method", item.disposal_method)
            if result.get("quality_status") != "PASS":
                all_passed = False
    
    db_inspection.status = "COMPLETED"
    
    db.commit()
    db.refresh(db_inspection)
    return db_inspection

def get_outsourcing_request(db: Session, request_id: int):
    return db.query(models.OutsourcingRequest).filter(models.OutsourcingRequest.id == request_id).first()

def get_outsourcing_request_by_no(db: Session, request_no: str):
    return db.query(models.OutsourcingRequest).filter(models.OutsourcingRequest.request_no == request_no).first()

def get_outsourcing_requests(db: Session, account_set_id: int = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.OutsourcingRequest)
    if account_set_id:
        query = query.filter(models.OutsourcingRequest.account_set_id == account_set_id)
    if status:
        query = query.filter(models.OutsourcingRequest.status == status)
    return query.order_by(models.OutsourcingRequest.planned_date).offset(skip).limit(limit).all()

def create_outsourcing_request(db: Session, request: schemas.OutsourcingRequestCreate):
    db_request = models.OutsourcingRequest(**request.dict())
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

def update_outsourcing_request_status(db: Session, request_id: int, status: str):
    db_request = get_outsourcing_request(db, request_id)
    if not db_request:
        return None
    db_request.status = status
    db.commit()
    db.refresh(db_request)
    return db_request

def get_outsourcing_order(db: Session, order_id: int):
    return db.query(models.OutsourcingOrder).filter(models.OutsourcingOrder.id == order_id).first()

def get_outsourcing_order_by_no(db: Session, order_no: str):
    return db.query(models.OutsourcingOrder).filter(models.OutsourcingOrder.order_no == order_no).first()

def get_outsourcing_orders(db: Session, account_set_id: int = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.OutsourcingOrder)
    if account_set_id:
        query = query.filter(models.OutsourcingOrder.account_set_id == account_set_id)
    if status:
        query = query.filter(models.OutsourcingOrder.status == status)
    return query.order_by(models.OutsourcingOrder.planned_date).offset(skip).limit(limit).all()

def create_outsourcing_order(db: Session, order: schemas.OutsourcingOrderCreate):
    db_order = models.OutsourcingOrder(**order.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def update_outsourcing_order_status(db: Session, order_id: int, status: str):
    db_order = get_outsourcing_order(db, order_id)
    if not db_order:
        return None
    db_order.status = status
    db.commit()
    db.refresh(db_order)
    return db_order

def get_outsourcing_issue(db: Session, issue_id: int):
    return db.query(models.OutsourcingIssue).filter(models.OutsourcingIssue.id == issue_id).first()

def get_outsourcing_issues(db: Session, account_set_id: int = None, outsourcing_order_id: int = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.OutsourcingIssue)
    if account_set_id:
        query = query.filter(models.OutsourcingIssue.account_set_id == account_set_id)
    if outsourcing_order_id:
        query = query.filter(models.OutsourcingIssue.outsourcing_order_id == outsourcing_order_id)
    if status:
        query = query.filter(models.OutsourcingIssue.status == status)
    return query.order_by(models.OutsourcingIssue.issue_date.desc()).offset(skip).limit(limit).all()

def create_outsourcing_issue(db: Session, issue: schemas.OutsourcingIssueCreate):
    items_data = issue.dict().pop('items', [])
    db_issue = models.OutsourcingIssue(**issue.dict())
    db.add(db_issue)
    db.commit()
    db.refresh(db_issue)
    for item_data in items_data:
        item_data['issue_id'] = db_issue.id
        db_item = models.OutsourcingIssueItem(**item_data)
        db.add(db_item)
    db.commit()
    db.refresh(db_issue)
    return db_issue

def update_outsourcing_issue_status(db: Session, issue_id: int, status: str):
    db_issue = get_outsourcing_issue(db, issue_id)
    if not db_issue:
        return None
    db_issue.status = status
    db.commit()
    db.refresh(db_issue)
    return db_issue

def get_outsourcing_replenish(db: Session, replenish_id: int):
    return db.query(models.OutsourcingReplenish).filter(models.OutsourcingReplenish.id == replenish_id).first()

def get_outsourcing_replenishes(db: Session, account_set_id: int = None, outsourcing_order_id: int = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.OutsourcingReplenish)
    if account_set_id:
        query = query.filter(models.OutsourcingReplenish.account_set_id == account_set_id)
    if outsourcing_order_id:
        query = query.filter(models.OutsourcingReplenish.outsourcing_order_id == outsourcing_order_id)
    if status:
        query = query.filter(models.OutsourcingReplenish.status == status)
    return query.order_by(models.OutsourcingReplenish.replenish_date.desc()).offset(skip).limit(limit).all()

def create_outsourcing_replenish(db: Session, replenish: schemas.OutsourcingReplenishCreate):
    items_data = replenish.dict().pop('items', [])
    db_replenish = models.OutsourcingReplenish(**replenish.dict())
    db.add(db_replenish)
    db.commit()
    db.refresh(db_replenish)
    for item_data in items_data:
        item_data['replenish_id'] = db_replenish.id
        db_item = models.OutsourcingReplenishItem(**item_data)
        db.add(db_item)
    db.commit()
    db.refresh(db_replenish)
    return db_replenish

def update_outsourcing_replenish_status(db: Session, replenish_id: int, status: str):
    db_replenish = get_outsourcing_replenish(db, replenish_id)
    if not db_replenish:
        return None
    db_replenish.status = status
    db.commit()
    db.refresh(db_replenish)
    return db_replenish

def get_outsourcing_return(db: Session, return_id: int):
    return db.query(models.OutsourcingReturn).filter(models.OutsourcingReturn.id == return_id).first()

def get_outsourcing_returns(db: Session, account_set_id: int = None, outsourcing_order_id: int = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.OutsourcingReturn)
    if account_set_id:
        query = query.filter(models.OutsourcingReturn.account_set_id == account_set_id)
    if outsourcing_order_id:
        query = query.filter(models.OutsourcingReturn.outsourcing_order_id == outsourcing_order_id)
    if status:
        query = query.filter(models.OutsourcingReturn.status == status)
    return query.order_by(models.OutsourcingReturn.return_date.desc()).offset(skip).limit(limit).all()

def create_outsourcing_return(db: Session, return_order: schemas.OutsourcingReturnCreate):
    items_data = return_order.dict().pop('items', [])
    db_return = models.OutsourcingReturn(**return_order.dict())
    db.add(db_return)
    db.commit()
    db.refresh(db_return)
    for item_data in items_data:
        item_data['return_id'] = db_return.id
        db_item = models.OutsourcingReturnItem(**item_data)
        db.add(db_item)
    db.commit()
    db.refresh(db_return)
    return db_return

def update_outsourcing_return_status(db: Session, return_id: int, status: str):
    db_return = get_outsourcing_return(db, return_id)
    if not db_return:
        return None
    db_return.status = status
    db.commit()
    db.refresh(db_return)
    return db_return

def get_purchase_request(db: Session, request_id: int):
    return db.query(models.PurchaseRequest).filter(models.PurchaseRequest.id == request_id).first()

def get_purchase_request_by_no(db: Session, request_no: str):
    return db.query(models.PurchaseRequest).filter(models.PurchaseRequest.request_no == request_no).first()

def get_purchase_requests(db: Session, account_set_id: int = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.PurchaseRequest)
    if account_set_id:
        query = query.filter(models.PurchaseRequest.account_set_id == account_set_id)
    if status:
        query = query.filter(models.PurchaseRequest.status == status)
    return query.order_by(models.PurchaseRequest.created_at.desc()).offset(skip).limit(limit).all()

def get_purchase_requests_count(db: Session, account_set_id: int = None, status: str = None):
    query = db.query(func.count(models.PurchaseRequest.id))
    if account_set_id:
        query = query.filter(models.PurchaseRequest.account_set_id == account_set_id)
    if status:
        query = query.filter(models.PurchaseRequest.status == status)
    return query.scalar()

def create_purchase_request(db: Session, request: schemas.PurchaseRequestCreate):
    db_request = models.PurchaseRequest(**request.dict())
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

def update_purchase_request_status(db: Session, request_id: int, status: str):
    db_request = get_purchase_request(db, request_id)
    if not db_request:
        return None
    db_request.status = status
    db.commit()
    db.refresh(db_request)
    return db_request

def get_purchase_orders_count(db: Session, account_set_id: int = None, status: str = None):
    query = db.query(func.count(models.PurchaseOrder.id))
    if account_set_id:
        query = query.filter(models.PurchaseOrder.account_set_id == account_set_id)
    if status:
        query = query.filter(models.PurchaseOrder.status == status)
    return query.scalar()

def create_purchase_order_with_items(db: Session, order: schemas.PurchaseOrderCreate):
    items_data = order.items
    db_order = models.PurchaseOrder(**order.dict(exclude={'items'}))
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    for item_data in items_data:
        item_dict = item_data.dict() if hasattr(item_data, 'dict') else item_data
        item_dict['purchase_order_id'] = db_order.id
        db_item = models.PurchaseOrderItem(**item_dict)
        db.add(db_item)
    db.commit()
    db.refresh(db_order)
    return db_order

def get_pre_receipts_count(db: Session, account_set_id: int = None, status: str = None):
    query = db.query(func.count(models.PreReceipt.id))
    if account_set_id:
        query = query.filter(models.PreReceipt.account_set_id == account_set_id)
    if status:
        query = query.filter(models.PreReceipt.status == status)
    return query.scalar()

def get_inbound_orders_count(db: Session, account_set_id: int = None, status: str = None):
    query = db.query(func.count(models.InboundOrder.id))
    if account_set_id:
        query = query.filter(models.InboundOrder.account_set_id == account_set_id)
    if status:
        query = query.filter(models.InboundOrder.status == status)
    return query.scalar()

def get_outsourcing_requests_count(db: Session, account_set_id: int = None, status: str = None):
    query = db.query(func.count(models.OutsourcingRequest.id))
    if account_set_id:
        query = query.filter(models.OutsourcingRequest.account_set_id == account_set_id)
    if status:
        query = query.filter(models.OutsourcingRequest.status == status)
    return query.scalar()

def get_outsourcing_order(db: Session, order_id: int):
    return db.query(models.OutsourcingOrder).filter(models.OutsourcingOrder.id == order_id).first()

def get_outsourcing_orders(db: Session, account_set_id: int = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.OutsourcingOrder)
    if account_set_id:
        query = query.filter(models.OutsourcingOrder.account_set_id == account_set_id)
    if status:
        query = query.filter(models.OutsourcingOrder.status == status)
    return query.order_by(models.OutsourcingOrder.planned_date).offset(skip).limit(limit).all()

def get_outsourcing_orders_count(db: Session, account_set_id: int = None, status: str = None):
    query = db.query(func.count(models.OutsourcingOrder.id))
    if account_set_id:
        query = query.filter(models.OutsourcingOrder.account_set_id == account_set_id)
    if status:
        query = query.filter(models.OutsourcingOrder.status == status)
    return query.scalar()

def get_outsourcing_issue(db: Session, issue_id: int):
    return db.query(models.OutsourcingIssue).filter(models.OutsourcingIssue.id == issue_id).first()

def get_outsourcing_issues(db: Session, account_set_id: int = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.OutsourcingIssue)
    if account_set_id:
        query = query.filter(models.OutsourcingIssue.account_set_id == account_set_id)
    if status:
        query = query.filter(models.OutsourcingIssue.status == status)
    return query.order_by(models.OutsourcingIssue.issue_date.desc()).offset(skip).limit(limit).all()

def get_outsourcing_issues_count(db: Session, account_set_id: int = None, status: str = None):
    query = db.query(func.count(models.OutsourcingIssue.id))
    if account_set_id:
        query = query.filter(models.OutsourcingIssue.account_set_id == account_set_id)
    if status:
        query = query.filter(models.OutsourcingIssue.status == status)
    return query.scalar()

def get_outsourcing_receive(db: Session, receive_id: int):
    return db.query(models.OutsourcingReceive).filter(models.OutsourcingReceive.id == receive_id).first()

def get_outsourcing_receives(db: Session, account_set_id: int = None, status: str = None, skip: int = 0, limit: int = 100):
    query = db.query(models.OutsourcingReceive)
    if account_set_id:
        query = query.filter(models.OutsourcingReceive.account_set_id == account_set_id)
    if status:
        query = query.filter(models.OutsourcingReceive.status == status)
    return query.order_by(models.OutsourcingReceive.expected_arrival_date).offset(skip).limit(limit).all()

def get_outsourcing_receives_count(db: Session, account_set_id: int = None, status: str = None):
    query = db.query(func.count(models.OutsourcingReceive.id))
    if account_set_id:
        query = query.filter(models.OutsourcingReceive.account_set_id == account_set_id)
    if status:
        query = query.filter(models.OutsourcingReceive.status == status)
    return query.scalar()