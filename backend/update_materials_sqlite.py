import sqlite3

conn = sqlite3.connect('backend.db')
cursor = conn.cursor()

cursor.execute("UPDATE materials SET barcode = 'BC001' WHERE id = 1")
cursor.execute("UPDATE materials SET barcode = 'BC002' WHERE id = 2")
cursor.execute("UPDATE materials SET barcode = 'BC003' WHERE id = 3")
cursor.execute("UPDATE materials SET barcode = 'BC004' WHERE id = 4")

conn.commit()
cursor.execute("SELECT id, code, name, barcode FROM materials")
rows = cursor.fetchall()
for row in rows:
    print(f"Material {row[0]}: code={row[1]}, name={row[2]}, barcode={row[3]}")

conn.close()
print("Done")