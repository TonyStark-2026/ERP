"""
迁移脚本：创建所有补充模块的数据表
"""
import sqlite3
import os
import sys

DB_PATH = r"c:\Users\ruancanling\Desktop\ERP VIBE CODING\backend.db"

# 所有新表名
NEW_TABLES = [
    "accounting_subjects", "coding_rules", "accounting_periods", "roles", "operation_logs",
    "sales_quotations", "sales_quotation_items", "sales_returns", "sales_return_items",
    "receivables", "receipts",
    "warehouses", "slow_moving_inventories",
    "routings", "routing_operations", "material_requisitions", "material_requisition_items", "work_reports",
    "period_closings",
    "cost_standards", "cost_variances",
    "invoice_checks",
    "custom_reports", "dashboard_configs",
]

def migrate():
    # 先通过SQLAlchemy建表
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backend.database import engine, Base
    import backend.models as models
    
    print("通过SQLAlchemy创建所有新表...")
    # 只创建新表（不重建已有表）
    Base.metadata.create_all(engine, tables=[
        models.AccountingSubject.__table__,
        models.CodingRule.__table__,
        models.AccountingPeriod.__table__,
        models.Role.__table__,
        models.OperationLog.__table__,
        models.SalesQuotation.__table__,
        models.SalesQuotationItem.__table__,
        models.SalesReturn.__table__,
        models.SalesReturnItem.__table__,
        models.Receivable.__table__,
        models.Receipt.__table__,
        models.Warehouse.__table__,
        models.SlowMovingInventory.__table__,
        models.Routing.__table__,
        models.RoutingOperation.__table__,
        models.MaterialRequisition.__table__,
        models.MaterialRequisitionItem.__table__,
        models.WorkReport.__table__,
        models.PeriodClosing.__table__,
        models.CostStandard.__table__,
        models.CostVariance.__table__,
        models.InvoiceCheck.__table__,
        models.CustomReport.__table__,
        models.DashboardConfig.__table__,
    ])
    print("[OK] 所有新表创建完成")
    
    # 验证
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    all_tables = [r[0] for r in cursor.fetchall()]
    conn.close()
    
    created = [t for t in NEW_TABLES if t in all_tables]
    missing = [t for t in NEW_TABLES if t not in all_tables]
    
    print(f"\n已创建: {len(created)}/{len(NEW_TABLES)} 张表")
    if missing:
        print(f"缺失: {missing}")
    else:
        print("[OK] 全部创建成功！")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    migrate()