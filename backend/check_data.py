import sqlite3
import os

# 查找所有数据库文件
for root, dirs, files in os.walk('.'):
    for f in files:
        if f.endswith('.db'):
            db_path = os.path.join(root, f)
            print(f"\n=== 数据库: {db_path} ===")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT id, username, account_set_id FROM users")
                users = cursor.fetchall()
                print(f"用户列表 ({len(users)} 个):")
                for u in users:
                    print(f"  - ID:{u[0]}, 用户名:{u[1]}, 账套ID:{u[2]}")
            except Exception as e:
                print(f"  查询失败: {e}")
            conn.close()
