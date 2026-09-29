# -*- coding: utf-8 -*-
"""
一键同步：源代码更新后，自动同步到独立软件目录
运行: python sync_to_exe.py
"""
import shutil
import os
import sqlite3

PROJECT = r"c:\Users\ruancanling\Desktop\ERP VIBE CODING"
DIST = os.path.join(PROJECT, "dist", "ERP智能系统")

def sync():
    print("=" * 60)
    print("  ERP智能系统 - 一键同步到独立软件")
    print("=" * 60)

    if not os.path.exists(DIST):
        print("  [ERROR] 独立软件目录不存在，请先运行 build_exe.py 打包")
        return

    # 1. 同步前端
    print("\n[1/4] 同步 frontend/...")
    src = os.path.join(PROJECT, "frontend")
    dst = os.path.join(DIST, "frontend")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print("  OK")

    dst2 = os.path.join(DIST, "_internal", "frontend")
    if os.path.exists(dst2):
        shutil.rmtree(dst2)
    shutil.copytree(src, dst2)
    print("  OK (_internal)")

    # 2. 同步后端代码
    print("\n[2/4] 同步 backend/...")
    src = os.path.join(PROJECT, "backend")
    dst = os.path.join(DIST, "backend")
    if os.path.exists(dst):
        shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "erp.db"))
    print("  OK")

    # 3. 同步数据库（用sqlite backup避免锁定）
    print("\n[3/4] 同步 backend.db...")
    src_db = os.path.join(PROJECT, "backend.db")
    dst_db = os.path.join(DIST, "backend.db")
    if os.path.exists(src_db):
        try:
            shutil.copy2(src_db, dst_db)
        except PermissionError:
            # 文件被锁定，用sqlite backup
            conn = sqlite3.connect(src_db)
            backup = sqlite3.connect(dst_db)
            conn.backup(backup)
            backup.close()
            conn.close()
        print(f"  OK ({os.path.getsize(dst_db)} bytes)")

    # 4. 同步启动器
    print("\n[4/4] 同步启动器脚本...")
    launcher = os.path.join(PROJECT, "_exe_embedded_launcher.py")
    if os.path.exists(launcher):
        # 已编译进EXE，无法直接替换，提示需要重新打包
        print("  [NOTE] 启动器已编译进EXE，如修改了启动器需重新运行 build_exe.py")
    else:
        print("  [SKIP] 无启动器脚本")

    print("\n" + "=" * 60)
    print("  同步完成！独立软件已更新")
    print("=" * 60)
    print(f"  目录: {DIST}")
    print(f"  EXE:  {os.path.join(DIST, 'ERP智能系统.exe')}")
    print()
    print("  注意:")
    print("  - 如果修改了 _exe_embedded_launcher.py，需重新 build_exe.py")
    print("  - 如果只修改了 frontend/ 或 backend/，运行本脚本即可")
    print("  - 同步后需重启 EXE 才能生效")
    print("=" * 60)

if __name__ == "__main__":
    sync()
