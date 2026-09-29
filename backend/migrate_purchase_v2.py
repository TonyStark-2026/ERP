"""采购模块V2迁移脚本 - 新增采购建议/评估/询价/入库/沟通/到货通知表"""
import sys
sys.path.insert(0, ".")
from backend.database import engine
from backend import models

# 只创建新表
new_tables = [
    models.PurchaseSuggestion.__table__,
    models.SupplierEvaluation.__table__,
    models.PurchaseQuotation.__table__,
    models.PurchaseQuotationReply.__table__,
    models.PurchaseInbound.__table__,
    models.PurchaseCommunication.__table__,
    models.PurchaseArrivalNotice.__table__,
]

from sqlalchemy import inspect
insp = inspect(engine)
existing = set(insp.get_table_names())
created = 0
with engine.begin() as conn:
    for t in new_tables:
        if t.name not in existing:
            t.create(bind=conn)
            print(f"[OK] 建表: {t.name}")
            created += 1
        else:
            print(f"[SKIP] 已存在: {t.name}")

print(f"\n完成，共创建 {created} 张新表")
