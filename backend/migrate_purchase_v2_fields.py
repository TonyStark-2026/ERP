"""
迁移脚本：为 PurchaseOrder 和 PurchaseOrderItem 添加 V2 扩展字段
"""
import sqlite3
import os

DB_PATH = r"c:\Users\ruancanling\Desktop\ERP VIBE CODING\backend.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # PurchaseOrder 新字段
    po_columns = [
        ("order_date", "DATE"),
        ("expected_date", "DATE"),
        ("payment_terms", "VARCHAR(100)"),
        ("transport_type", "VARCHAR(50)"),
        ("warehouse_id", "INTEGER"),
        ("total_amount", "DECIMAL(18,4) DEFAULT 0"),
        ("remark", "TEXT"),
        ("approved_at", "DATETIME"),
    ]
    
    for col_name, col_type in po_columns:
        try:
            cursor.execute(f"ALTER TABLE purchase_orders ADD COLUMN {col_name} {col_type}")
            print(f"✓ Added purchase_orders.{col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print(f"- Column purchase_orders.{col_name} already exists")
            else:
                print(f"✗ Error adding purchase_orders.{col_name}: {e}")
    
    # PurchaseOrderItem 新字段
    poi_columns = [
        ("line_no", "INTEGER"),
        ("unit", "VARCHAR(20)"),
        ("amount", "DECIMAL(18,4)"),
        ("source_no", "VARCHAR(50)"),
        ("delivery_date", "DATE"),
        ("received_qty", "DECIMAL(18,4) DEFAULT 0"),
        ("tax_rate", "DECIMAL(5,2)"),
        ("tax_amount", "DECIMAL(18,4)"),
        ("total_amount", "DECIMAL(18,4)"),
        ("remark", "TEXT"),
    ]
    
    for col_name, col_type in poi_columns:
        try:
            cursor.execute(f"ALTER TABLE purchase_order_items ADD COLUMN {col_name} {col_type}")
            print(f"✓ Added purchase_order_items.{col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print(f"- Column purchase_order_items.{col_name} already exists")
            else:
                print(f"✗ Error adding purchase_order_items.{col_name}: {e}")
    
    conn.commit()
    conn.close()
    print("\n迁移完成！")

if __name__ == "__main__":
    migrate()