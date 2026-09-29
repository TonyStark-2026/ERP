import sqlite3

conn = sqlite3.connect('backend.db')
cursor = conn.cursor()

# 查找用户"超级臭屁"及其account_set_id
cursor.execute("SELECT id, username, account_set_id FROM users WHERE username = '超级臭屁'")
user = cursor.fetchone()
print(f"用户信息: {user}")

if user:
    user_id = user[0]
    account_set_id = user[2]
    print(f"用户ID: {user_id}, 账套ID: {account_set_id}")

    if account_set_id:
        # 查询该账套下所有物料
        cursor.execute("SELECT id, code, name FROM materials WHERE account_set_id = ?", (account_set_id,))
        materials = cursor.fetchall()
        print(f"\n该账套下共有 {len(materials)} 个物料:")
        for m in materials:
            print(f"  - ID:{m[0]}, 编码:{m[1]}, 名称:{m[2]}")

        material_ids = [m[0] for m in materials]

        if material_ids:
            # 删除关联数据
            # 1. 库存记录
            cursor.execute("DELETE FROM inventory_records WHERE account_set_id = ?", (account_set_id,))
            print(f"\n已删除库存记录: {cursor.rowcount} 条")

            # 2. 库存交易
            cursor.execute("DELETE FROM inventory_transactions WHERE account_set_id = ?", (account_set_id,))
            print(f"已删除库存交易: {cursor.rowcount} 条")

            # 3. BOM子件
            placeholders = ','.join(['?' for _ in material_ids])
            cursor.execute(f"DELETE FROM bom_items WHERE material_id IN ({placeholders}) OR parent_material_id IN ({placeholders})", material_ids + material_ids)
            print(f"已删除BOM子件: {cursor.rowcount} 条")

            # 4. BOM
            cursor.execute("DELETE FROM boms WHERE account_set_id = ?", (account_set_id,))
            print(f"已删除BOM: {cursor.rowcount} 条")

            # 5. 批次库存
            cursor.execute("DELETE FROM batch_inventories WHERE account_set_id = ?", (account_set_id,))
            print(f"已删除批次库存: {cursor.rowcount} 条")

            # 6. 批次变动
            cursor.execute("DELETE FROM batch_movements WHERE account_set_id = ?", (account_set_id,))
            print(f"已删除批次变动: {cursor.rowcount} 条")

            # 7. 入库单子项
            cursor.execute(f"DELETE FROM inbound_order_items WHERE material_id IN ({placeholders})", material_ids)
            print(f"已删除入库单子项: {cursor.rowcount} 条")

            # 8. 入库单
            cursor.execute("DELETE FROM inbound_orders WHERE account_set_id = ?", (account_set_id,))
            print(f"已删除入库单: {cursor.rowcount} 条")

            # 9. 出库单子项
            cursor.execute(f"DELETE FROM outbound_order_items WHERE material_id IN ({placeholders})", material_ids)
            print(f"已删除出库单子项: {cursor.rowcount} 条")

            # 10. 出库单
            cursor.execute("DELETE FROM outbound_orders WHERE account_set_id = ?", (account_set_id,))
            print(f"已删除出库单: {cursor.rowcount} 条")

            # 11. 销售订单
            cursor.execute("DELETE FROM sales_orders WHERE account_set_id = ?", (account_set_id,))
            print(f"已删除销售订单: {cursor.rowcount} 条")

            # 12. 采购订单
            cursor.execute("DELETE FROM purchase_orders WHERE account_set_id = ?", (account_set_id,))
            print(f"已删除采购订单: {cursor.rowcount} 条")

            # 13. MRP结果
            cursor.execute("DELETE FROM mrp_results WHERE account_set_id = ?", (account_set_id,))
            print(f"已删除MRP结果: {cursor.rowcount} 条")

            # 14. 计划订单
            cursor.execute("DELETE FROM planned_orders WHERE account_set_id = ?", (account_set_id,))
            print(f"已删除计划订单: {cursor.rowcount} 条")

            # 15. 采购申请
            cursor.execute("DELETE FROM purchase_requests WHERE account_set_id = ?", (account_set_id,))
            print(f"已删除采购申请: {cursor.rowcount} 条")

            # 16. 最后删除物料
            cursor.execute("DELETE FROM materials WHERE account_set_id = ?", (account_set_id,))
            print(f"已删除物料: {cursor.rowcount} 条")

            conn.commit()
            print("\n✅ 所有商品数据已清空!")
        else:
            print("\n该账套下没有物料数据")
    else:
        print("\n该用户没有关联的账套")
else:
    print("未找到用户'超级臭屁'")

conn.close()
