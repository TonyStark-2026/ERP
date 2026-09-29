"""清空所有业务模拟数据，保留表结构、admin账号和企业配置"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'erp_data.db')
print(f"数据库路径: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 清空所有业务表（保留用户表、企业配置表、会计科目表、账户集表）
tables_to_clear = [
    # 物料相关
    'materials',
    # 采购相关
    'purchase_orders', 'purchase_order_items', 'purchase_order_templates',
    'purchase_requests', 'purchase_suggestions', 'purchase_quotations',
    'purchase_quotation_replies', 'purchase_inbounds', 'supplier_evaluations',
    'purchase_communications', 'purchase_arrival_notices',
    # 销售相关
    'sales_orders', 'sales_order_items', 'contracts',
    # 生产相关
    'production_work_orders', 'production_costs', 'cost_allocations',
    'production_work_order_docs', 'production_component_lists',
    'production_process_plans', 'production_picks', 'production_material_returns',
    'production_replenishes', 'production_schedules',
    # 库存相关
    'inventory_records', 'inventory_transactions', 'stocktaking_tasks', 'stocktaking_items',
    'batch_inventory', 'batch_movements', 'delivery_notes', 'delivery_note_items',
    'sales_outbounds', 'sales_outbound_items', 'storage_locations',
    # BOM相关
    'boms', 'bom_items',
    # 工程模块
    'wbs_projects', 'wbs_nodes', 'eco_change_orders', 'eco_impacts',
    'cost_collections', 'revenue_recognitions', 'milestones',
    'downtimes', 'maintenance_plans', 'inspections', 'inspection_items',
    'work_order_processes',
    # 财务相关
    'vouchers', 'voucher_entries', 'cash_flow_items', 'exchange_rates',
    'voucher_templates', 'auto_vouchers',
    # 其他
    'suppliers', 'customers', 'employees', 'forecasts', 'mrp_results', 'planned_orders',
    'quality_inspections', 'quality_inspection_items',
    'outsourcing_requests', 'outsourcing_orders', 'outsourcing_issues',
    'outsourcing_issue_items', 'outsourcing_replenishes', 'outsourcing_replenish_items',
    'outsourcing_returns', 'outsourcing_return_items', 'outsourcing_receives',
    'outsourcing_receive_items', 'outsourcing_invoices', 'outsourcing_estimates',
    'outsourcing_estimate_items', 'outsourcing_accounts',
    'pre_receipts', 'pre_receipt_items', 'inbound_orders', 'inbound_order_items',
    'outbound_orders', 'outbound_order_items',
    'compliance_alerts', 'hs_codes', 'country_tax_rules',
    'batch_rules', 'unit_conversions', 'purchase_agreements',
    'price_lists',
]

cleared = 0
for table in tables_to_clear:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        cursor.execute(f"DELETE FROM {table}")
        cleared += count
        if count > 0:
            print(f"  [清空] {table}: {count} 条")
    except Exception as e:
        # 表不存在则跳过
        pass

# 重置自增序列
try:
    cursor.execute("DELETE FROM sqlite_sequence WHERE name IN (" + ",".join([f"'{t}'" for t in tables_to_clear]) + ")")
except Exception:
    pass

conn.commit()
conn.close()
print(f"\n✅ 清理完成！共清空 {cleared} 条模拟数据")
print("   保留：admin账号、企业配置、会计科目、账户集、角色权限")
