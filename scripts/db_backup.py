# -*- coding: utf-8 -*-
"""
ERP 数据库每日自动备份
- 源数据库：项目根目录 erp_data.db
- 备份位置：项目根目录 backups/
- 文件名：erp_data_YYYYMMDD_HHMMSS.db
- 自动删除超过保留份数的旧备份
- 使用 SQLite 在线备份接口，服务运行中也能安全备份
"""
import os
import sys
import sqlite3
import datetime

# 保留的备份份数（每份=一次备份，默认每天一次即保留30天）
KEEP_COUNT = 30

# 项目根目录（本文件在 scripts/ 下，根目录是上一级）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DB = os.path.join(BASE_DIR, "erp_data.db")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
LOG_FILE = os.path.join(BACKUP_DIR, "backup.log")


def log(msg):
    line = "[%s] %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line)


def main():
    if not os.path.exists(SRC_DB):
        log("失败：找不到数据库文件 %s" % SRC_DB)
        sys.exit(1)

    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dst_file = os.path.join(BACKUP_DIR, "erp_data_%s.db" % stamp)

    # 在线热备份（服务运行中也安全，不会复制到半截数据）
    try:
        src = sqlite3.connect(SRC_DB)
        dst = sqlite3.connect(dst_file)
        src.backup(dst)
        dst.close()
        src.close()
    except Exception as e:
        log("备份失败：%s" % e)
        sys.exit(1)

    size_kb = os.path.getsize(dst_file) / 1024.0
    log("备份成功：%s（%.1f KB）" % (os.path.basename(dst_file), size_kb))

    # 清理旧备份，只保留最新的 KEEP_COUNT 份
    try:
        files = [f for f in os.listdir(BACKUP_DIR)
                 if f.startswith("erp_data_") and f.endswith(".db")]
        files.sort(reverse=True)  # 文件名带时间戳，新的在前
        for old in files[KEEP_COUNT:]:
            os.remove(os.path.join(BACKUP_DIR, old))
            log("已清理旧备份：%s" % old)
        log("当前保留备份 %d 份" % min(len(files), KEEP_COUNT))
    except Exception as e:
        log("清理旧备份时出错：%s" % e)


if __name__ == "__main__":
    main()
