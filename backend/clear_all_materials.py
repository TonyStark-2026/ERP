import sqlite3

conn = sqlite3.connect('backend.db')
cursor = conn.cursor()

# 查看现有物料
cursor.execute("SELECT id, code, name FROM materials")
materials = cursor.fetchall()
print(f"现有物料 {len(materials)} 个:")
for m in materials:
    print(f"  - ID:{m[0]}, 编码:{m[1]}, 名称:{m[2]}")

material_ids = [m[0] for m in materials]

if material_ids:
    placeholders = ','.join(['?' for _ in material_ids])

    # 清除所有关联表
    tables = [
        ("inventory_records", f"material_id IN ({placeholders})"),
        ("inventory_transactions", f"material_id IN ({placeholders})"),
        ("batch_inventory", f"material_id IN ({placeholders})"),
        ("batch_movements", f"material_id IN ({placeholders})"),
        ("inbound_order_items", f"material_id IN ({placeholders})"),
        ("outbound_order_items", f"material_id IN ({placeholders})"),
        ("quality_inspection_items", f"material_id IN ({placeholders})"),
        ("mrp_results", f"material_id IN ({placeholders})"),
    ]
    for table, cond in tables:
        try:
            cursor.execute(f"DELETE FROM {table} WHERE {cond}", material_ids)
            if cursor.rowcount > 0:
                print(f"  {table}: 已删除 {cursor.rowcount} 条")
        except Exception as e:
            print(f"  {table}: 跳过 ({e})")

    # 清除按account_set关联的表
    for table in ["boms", "bom_items", "inbound_orders", "outbound_orders",
                   "sales_orders", "sales_order_items", "purchase_orders",
                   "purchase_order_items", "planned_orders", "purchase_requests",
                   "forecasts", "production_workorders", "delivery_notes",
                   "delivery_note_items", "pre_receipts", "pre_receipt_items",
                   "outsourcing_requests", "outsourcing_orders",
                   "outsourcing_issues", "outsourcing_issue_items",
                   "outsourcing_replenishes", "outsourcing_replenish_items",
                   "outsourcing_returns", "outsourcing_return_items",
                   "outsourcing_receives", "outsourcing_receive_items",
                   "outsourcing_invoices", "outsourcing_estimates",
                   "outsourcing_estimate_items", "outsourcing_accounts"]:
        try:
            cursor.execute(f"DELETE FROM {table}")
            if cursor.rowcount > 0:
                print(f"  {table}: 已删除 {cursor.rowcount} 条")
        except:
            pass

    # 删除物料
    cursor.execute("DELETE FROM materials")
    print(f"\n已删除全部物料: {cursor.rowcount} 条")
    conn.commit()
    print("所有商品数据已清空!")
else:
    print("没有物料数据需要清空")

conn.close()
