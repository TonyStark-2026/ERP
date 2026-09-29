import sqlite3

conn = sqlite3.connect('backend.db')
cursor = conn.cursor()

# 先查看有哪些物料
cursor.execute("SELECT id, code, name, account_set_id FROM materials")
materials = cursor.fetchall()
print(f"当前共有 {len(materials)} 个物料:")
for m in materials:
    print(f"  - ID:{m[0]}, 编码:{m[1]}, 名称:{m[2]}, 账套:{m[3]}")

material_ids = [m[0] for m in materials]
account_set_ids = list(set(m[3] for m in materials))

if material_ids:
    placeholders = ','.join(['?' for _ in material_ids])

    # 清除所有关联数据
    tables_to_clear = [
        ("inventory_records", f"material_id IN ({placeholders})", material_ids),
        ("inventory_transactions", f"material_id IN ({placeholders})", material_ids),
        ("bom_items", f"material_id IN ({placeholders}) OR parent_material_id IN ({placeholders})", material_ids + material_ids),
        ("batch_inventory", f"material_id IN ({placeholders})", material_ids),
        ("batch_movements", f"material_id IN ({placeholders})", material_ids),
        ("inbound_order_items", f"material_id IN ({placeholders})", material_ids),
        ("outbound_order_items", f"material_id IN ({placeholders})", material_ids),
        ("quality_inspection_items", f"material_id IN ({placeholders})", material_ids),
        ("mrp_results", f"material_id IN ({placeholders})", material_ids),
    ]

    print("\n开始清除数据...")
    for table, condition, params in tables_to_clear:
        try:
            cursor.execute(f"DELETE FROM {table} WHERE {condition}", params)
            print(f"  {table}: 已删除 {cursor.rowcount} 条")
        except Exception as e:
            print(f"  {table}: 跳过 ({e})")

    # 清除按account_set_id关联的表
    for asid in account_set_ids:
        for table in ["boms", "inbound_orders", "outbound_orders", "sales_orders",
                       "purchase_orders", "planned_orders", "purchase_requests",
                       "forecasts", "production_workorders", "delivery_notes",
                       "pre_receipts", "outsourcing_requests", "outsourcing_orders"]:
            try:
                cursor.execute(f"DELETE FROM {table} WHERE account_set_id = ?", (asid,))
                if cursor.rowcount > 0:
                    print(f"  {table}(账套{asid}): 已删除 {cursor.rowcount} 条")
            except Exception as e:
                pass

    # 最后删除物料
    cursor.execute("DELETE FROM materials")
    print(f"\n✅ 已删除全部物料: {cursor.rowcount} 条")

    conn.commit()
    print("\n所有商品数据已清空!")
else:
    print("没有物料数据需要清空")

conn.close()
