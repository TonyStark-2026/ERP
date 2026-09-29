import sqlite3
import os

# Check all possible DB paths
paths = [
    r"c:\Users\ruancanling\Desktop\ERP VIBE CODING\backend.db",
    r"c:\Users\ruancanling\Desktop\ERP VIBE CODING\backend\erp.db",
    r"c:\Users\ruancanling\Desktop\ERP VIBE CODING\backend\backend.db",
]

for path in paths:
    if os.path.exists(path):
        size = os.path.getsize(path)
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in cursor.fetchall()]
        print(f"\n{path} ({size} bytes): {len(tables)} tables")
        for t in tables[:5]:
            print(f"  - {t}")
        if len(tables) > 5:
            print(f"  ... and {len(tables)-5} more")
        conn.close()