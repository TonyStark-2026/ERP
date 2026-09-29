"""迁移脚本：为物料表增加科目字段，创建自动凭证系统表"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "backend.db")

def run():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Material 表增加科目字段
    for col, default in [
        ("inventory_account_code", "'1401'"),
        ("income_account_code", "'6001'"),
        ("cost_account_code", "'6401'"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE materials ADD COLUMN {col} VARCHAR(50) DEFAULT {default}")
            print(f"✓ materials.{col} 已添加")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print(f"- materials.{col} 已存在，跳过")
            else:
                raise

    # 2. VoucherTemplate 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voucher_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_set_id INTEGER NOT NULL,
            template_code VARCHAR(50) UNIQUE NOT NULL,
            template_name VARCHAR(100) NOT NULL,
            doc_type VARCHAR(50) NOT NULL,
            description TEXT,
            debit_rules TEXT NOT NULL,
            credit_rules TEXT NOT NULL,
            summary_template VARCHAR(200),
            enabled BOOLEAN DEFAULT 1,
            is_system BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ voucher_templates 表已创建")

    # 3. AutoVoucher 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auto_vouchers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_set_id INTEGER NOT NULL,
            voucher_no VARCHAR(50) NOT NULL,
            voucher_date DATE NOT NULL,
            status VARCHAR(20) DEFAULT 'DRAFT',
            source_doc_type VARCHAR(50) NOT NULL,
            source_doc_id INTEGER NOT NULL,
            source_doc_no VARCHAR(50),
            summary VARCHAR(300),
            template_code VARCHAR(50),
            total_debit DECIMAL(18,2) DEFAULT 0,
            total_credit DECIMAL(18,2) DEFAULT 0,
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            approved_at DATETIME,
            approved_by VARCHAR(50),
            reject_reason TEXT
        )
    """)
    print("✓ auto_vouchers 表已创建")

    # 4. AutoVoucherEntry 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auto_voucher_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            auto_voucher_id INTEGER NOT NULL,
            account_code VARCHAR(50) NOT NULL,
            account_name VARCHAR(100) NOT NULL,
            side VARCHAR(10) NOT NULL,
            amount DECIMAL(18,2) NOT NULL,
            summary VARCHAR(200),
            customer_id INTEGER,
            supplier_id INTEGER,
            department_id INTEGER,
            work_order_id INTEGER,
            material_id INTEGER,
            employee_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (auto_voucher_id) REFERENCES auto_vouchers(id) ON DELETE CASCADE
        )
    """)
    print("✓ auto_voucher_entries 表已创建")

    # 5. 更新现有物料的默认科目编码
    cursor.execute("UPDATE materials SET inventory_account_code = '1401' WHERE inventory_account_code IS NULL")
    cursor.execute("UPDATE materials SET income_account_code = '6001' WHERE income_account_code IS NULL")
    cursor.execute("UPDATE materials SET cost_account_code = '6401' WHERE cost_account_code IS NULL")
    print("✓ 现有物料科目编码已更新")

    conn.commit()
    conn.close()
    print("\n✅ 迁移完成！")

if __name__ == "__main__":
    run()
