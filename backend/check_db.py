import sqlite3

conn = sqlite3.connect('backend.db')
cursor = conn.cursor()

# 列出所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("数据库表:")
for t in tables:
    print(f"  - {t[0]}")

# 检查users表
print("\n=== users表 ===")
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()
print(f"共 {len(rows)} 条记录")
for r in rows:
    print(f"  {r}")

# 检查materials表
print("\n=== materials表 ===")
cursor.execute("SELECT id, code, name, account_set_id FROM materials")
rows = cursor.fetchall()
print(f"共 {len(rows)} 条记录")
for r in rows:
    print(f"  {r}")

# 检查account_sets表
print("\n=== account_sets表 ===")
cursor.execute("SELECT * FROM account_sets")
rows = cursor.fetchall()
print(f"共 {len(rows)} 条记录")
for r in rows:
    print(f"  {r}")

conn.close()
