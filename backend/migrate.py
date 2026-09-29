import sqlite3

conn = sqlite3.connect('backend.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE materials ADD COLUMN barcode VARCHAR(100)")
    print("Added barcode column")
except sqlite3.OperationalError:
    print("barcode column already exists")

try:
    cursor.execute("ALTER TABLE materials ADD COLUMN default_supplier_id INTEGER")
    print("Added default_supplier_id column")
except sqlite3.OperationalError:
    print("default_supplier_id column already exists")

cursor.execute("CREATE TABLE IF NOT EXISTS suppliers (id INTEGER PRIMARY KEY AUTOINCREMENT)")

conn.commit()
conn.close()
print("Migration completed successfully")