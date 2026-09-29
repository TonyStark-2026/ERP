# -*- coding: utf-8 -*-
"""
ERP智能系统 独立软件 EXE 打包脚本（PyInstaller onedir 模式）
目标：生成一个完整的"独立软件文件夹"，里面包含：
  - ERP智能系统.exe （双击即可启动，无需用户安装Python）
  - 内嵌完整Python运行时 + 所有依赖包
  - backend/ 代码、frontend/ 页面(PWA/manifest/icons)、erp.db 数据库
  - 运行时自动：启动后端 → 打开浏览器 → 显示手机访问二维码

使用方法：
  python build_exe.py
  打包完成后，在 dist/ERP智能系统/ 目录下找到 ERP智能系统.exe
  整个 ERP智能系统 文件夹就是完整的独立软件，可以拷贝到其他电脑直接使用（Win10/11）
"""
import os
import sys
import shutil
import subprocess
import time

PYEXE = r"C:\Users\ruancanling\AppData\Local\Programs\Python\Python38\python.exe"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_NAME = "ERP智能系统"
DIST_DIR = os.path.join(PROJECT_DIR, "dist")
BUILD_DIR = os.path.join(PROJECT_DIR, "build")
OUTPUT_DIR = os.path.join(DIST_DIR, APP_NAME)


def check_pyinstaller():
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__} 已就绪")
        return True
    except ImportError:
        print("⚠️  PyInstaller未安装，正在安装...")
        subprocess.check_call([PYEXE, "-m", "pip", "install", "pyinstaller"])
        return True


def create_embedded_launcher():
    """
    使用已有的 _exe_embedded_launcher.py（pywebview原生窗口版本）
    如果不存在则创建默认版本
    """
    launcher_path = os.path.join(PROJECT_DIR, "_exe_embedded_launcher.py")
    if os.path.exists(launcher_path):
        print("  已存在 _exe_embedded_launcher.py，使用现有版本（pywebview原生窗口版）")
    else:
        print("  未找到启动器，创建默认版本...")
        # 如果不存在，创建一个基础版本
        with open(launcher_path, "w", encoding="utf-8") as f:
            f.write("# -*- coding: utf-8 -*-\nimport webview, sys\nsys.exit('请先安装pywebview')\n")
    return launcher_path


def run_pyinstaller(launcher_path):
    print("\n🔨 开始使用PyInstaller打包独立EXE...")
    # 清理旧输出
    for d in [BUILD_DIR, OUTPUT_DIR]:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)

    args = [
        PYEXE, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",  # 目录模式（数据库能持久写入exe旁）
        "--name", APP_NAME,
        # 隐藏导入：PyInstaller无法自动发现的模块
        "--hidden-import", "uvicorn",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "fastapi",
        "--hidden-import", "pydantic",
        "--hidden-import", "pydantic.dataclasses",
        "--hidden-import", "sqlalchemy",
        "--hidden-import", "sqlalchemy.dialects",
        "--hidden-import", "sqlalchemy.dialects.sqlite",
        "--hidden-import", "qrcode",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL.Image",
        # pywebview 原生桌面窗口
        "--hidden-import", "webview",
        "--hidden-import", "webview.platforms.edgechromium",
        "--hidden-import", "webview.platforms.mshtml",
        "--hidden-import", "webview.platforms.winforms",
        "--hidden-import", "webview.platforms.gtk",
        "--hidden-import", "webview.platforms.gtkloader",
        "--hidden-import", "webview.http",
        "--hidden-import", "webview.http.staticfiles",
        "--hidden-import", "webview.util",
        "--hidden-import", "clr",
        "--hidden-import", "pythonnet",
        "--collect-all", "webview",
        # 后端所有api模块（importlib.import_module不会被自动扫描）
        "--hidden-import", "backend",
        "--hidden-import", "backend.app",
        "--hidden-import", "backend.models",
        "--hidden-import", "backend.schemas",
        "--hidden-import", "backend.crud",
        "--hidden-import", "backend.database",
        "--hidden-import", "backend.api",
        "--hidden-import", "backend.api.auth",
        "--hidden-import", "backend.api.bom",
        "--hidden-import", "backend.api.materials",
        "--hidden-import", "backend.api.finance",
        "--hidden-import", "backend.api.plan",
        "--hidden-import", "backend.api.sales",
        "--hidden-import", "backend.api.purchase",
        "--hidden-import", "backend.api.production",
        "--hidden-import", "backend.api.inventory",
        "--hidden-import", "backend.api.procurement",
        "--hidden-import", "backend.api.employees",
        "--hidden-import", "backend.api.compliance",
        "--hidden-import", "backend.api.crossborder",
        "--hidden-import", "backend.api.scanning",
        "--hidden-import", "backend.api.invoice_recognition",
        "--hidden-import", "backend.api.config_center",
        "--hidden-import", "backend.api.contracts",
        # 收集数据文件：frontend/ 和 backend/ 目录（注意：代码会自动复制完整的到输出目录，这里只复制必要的）
        "--add-data", f"{PROJECT_DIR}\\frontend{os.pathsep}frontend",
        # 不把backend用add-data打包（复制原目录过去更可靠）
        "--console",  # 控制台窗口（显示日志和二维码）
        # 图标（可选）
        # "--icon", os.path.join(PROJECT_DIR, "frontend", "icons", "icon-512.png"),
        launcher_path,
    ]

    print("  执行命令:", " ".join(args[:6]) + " ...")
    start = time.time()
    result = subprocess.run(args, cwd=PROJECT_DIR)
    elapsed = int(time.time() - start)
    if result.returncode != 0:
        print(f"  ❌ PyInstaller打包失败（返回码{result.returncode}），耗时 {elapsed}s")
        return False
    print(f"  ✅ PyInstaller 基础打包完成，耗时 {elapsed}s")
    return True


def copy_runtime_assets():
    """把运行时需要的完整资源复制到输出目录（数据库、后端代码等）"""
    print("\n📦 复制运行时资源到独立软件目录...")

    # 1. 复制完整的 backend/ 代码（覆盖PyInstaller的扫描结果，保证源码完整可import）
    src_backend = os.path.join(PROJECT_DIR, "backend")
    dst_backend = os.path.join(OUTPUT_DIR, "backend")
    if os.path.exists(dst_backend):
        shutil.rmtree(dst_backend, ignore_errors=True)
    shutil.copytree(src_backend, dst_backend,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "erp.db"))
    print("  ✅ backend/ 代码")

    # 2. 复制完整的 frontend/ （覆盖PyInstaller，保证manifest/icons等齐全）
    src_frontend = os.path.join(PROJECT_DIR, "frontend")
    dst_frontend = os.path.join(OUTPUT_DIR, "frontend")
    if os.path.exists(dst_frontend):
        shutil.rmtree(dst_frontend, ignore_errors=True)
    shutil.copytree(src_frontend, dst_frontend,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print("  ✅ frontend/ 页面 (PWA manifest icons)")

    # 3. 复制数据库（backend.db 是实际使用的数据库，erp.db 是备用）
    for db_name in ["backend.db", "erp.db"]:
        src_db = os.path.join(PROJECT_DIR, db_name)
        if os.path.exists(src_db) and os.path.getsize(src_db) > 0:
            dst_db = os.path.join(OUTPUT_DIR, db_name)
            shutil.copy2(src_db, dst_db)
            print(f"  ✅ 数据库 {db_name} ({os.path.getsize(src_db)} bytes)")
        else:
            print(f"  ⚠️  数据库 {db_name} 不存在或为空，跳过")

    # 4. 复制使用说明
    readme_text = f"""========================================
ERP智能系统 - 独立软件版
========================================

【使用方法】
1. 双击 ERP智能系统.exe 启动（无需安装Python）
2. 等待几秒，会自动弹出原生桌面窗口（非浏览器标签页）
3. 控制台会显示"手机访问二维码"，手机和电脑连同一WiFi后扫码即可在手机上使用

【桌面窗口特点】
  - 独立原生窗口，不是浏览器标签页
  - 无地址栏、无标签栏，看起来就是一个普通软件
  - 关闭窗口即停止服务

【手机安装成App（PWA）】
  - Android（Chrome/Edge）：打开网址 → 右上角菜单 → 添加到主屏幕
  - iPhone（Safari）：       打开网址 → 分享 → 添加到主屏幕
添加后桌面出现【ERP智能系统】图标，像普通软件一样使用。

【数据保存位置】
  所有业务数据保存在本文件夹中的 backend.db 文件（SQLite数据库）
  建议定期备份 backend.db 以防数据丢失

【注意事项】
  - 关闭控制台窗口 = 停止ERP服务，手机和电脑都无法访问
  - 如需开机自启：将 ERP智能系统.exe 的快捷方式放到
    C:\\Users\\<用户名>\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup
  - 建议在 Win10 或 Win11 64位系统上运行
  - 本软件为绿色免安装版，整个文件夹复制到任何电脑都能直接使用
"""
    readme_path = os.path.join(OUTPUT_DIR, "使用说明.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_text)
    print("  ✅ 使用说明.txt")

    # 5. 生成一个"桌面快捷方式创建.bat"
    bat_code = f"""@echo off
chcp 65001 > nul
title 创建ERP智能系统桌面快捷方式
cd /d "%~dp0"
set "TARGET=%~dp0ERP智能系统.exe"
set "LNKNAME=ERP智能系统"
set "DESKTOP=%USERPROFILE%\\Desktop"
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%DESKTOP%\\%LNKNAME%.lnk');$s.TargetPath='%TARGET%';$s.WorkingDirectory='%~dp0';$s.Description='ERP智能系统 独立软件版（双击即用 免安装Python）';$s.WindowStyle=1;$s.Save()"
if exist "%DESKTOP%\\%LNKNAME%.lnk" (
  echo ✅ 已创建桌面快捷方式: %DESKTOP%\\%LNKNAME%.lnk
) else (
  echo ❌ 创建失败，请手动发送ERP智能系统.exe到桌面快捷方式
)
pause
"""
    with open(os.path.join(OUTPUT_DIR, "创建桌面快捷方式.bat"), "w", encoding="utf-8") as f:
        f.write(bat_code)
    print("  ✅ 创建桌面快捷方式.bat")


def show_summary():
    size_bytes = 0
    for root, _, files in os.walk(OUTPUT_DIR):
        for f in files:
            try:
                size_bytes += os.path.getsize(os.path.join(root, f))
            except Exception:
                pass
    size_mb = size_bytes / (1024 * 1024)
    exe_path = os.path.join(OUTPUT_DIR, f"{APP_NAME}.exe")
    ok = os.path.exists(exe_path)
    print()
    print("=" * 70)
    print("  🎉 独立软件打包完成！")
    print("=" * 70)
    print(f"  📁 完整软件目录: {OUTPUT_DIR}")
    print(f"  🚀 主程序EXE:    {exe_path}" + ("  ✅" if ok else "  ❌ 缺失！"))
    print(f"  📦 总体积:        {size_mb:.1f} MB")
    print()
    print("  📦 把整个文件夹复制到其他Windows电脑，即可双击EXE使用（免安装Python）")
    print("  🖥️  首次使用请双击【创建桌面快捷方式.bat】创建桌面图标")
    print("  📱 启动后控制台显示手机访问二维码，扫码即可手机端使用")
    print("=" * 70)


def copy_to_desktop():
    """将完整的独立软件文件夹复制到桌面"""
    desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
    target_dir = os.path.join(desktop_dir, APP_NAME)
    target_exe = os.path.join(target_dir, f"{APP_NAME}.exe")

    # 如果桌面已存在旧版本，先删除
    if os.path.exists(target_dir):
        print(f"  🔄 检测到桌面已有旧版本，正在更新...")
        shutil.rmtree(target_dir, ignore_errors=True)

    # 复制整个文件夹到桌面
    print(f"  📋 正在复制到桌面: {target_dir}")
    shutil.copytree(OUTPUT_DIR, target_dir)

    if os.path.exists(target_exe):
        print(f"  ✅ EXE已复制到桌面: {target_exe}")
    else:
        print(f"  ❌ EXE复制失败！")
    return target_exe


def main():
    print("=" * 70)
    print("  🛠️  ERP智能系统 独立EXE打包工具")
    print("=" * 70)
    check_pyinstaller()
    launcher_path = create_embedded_launcher()
    ok = run_pyinstaller(launcher_path)
    if not ok:
        print("❌ 打包失败")
        sys.exit(1)
    copy_runtime_assets()
    show_summary()
    # === 自动复制到桌面 ===
    print("\n📋 正在将软件复制到桌面...")
    desktop_exe = copy_to_desktop()
    if desktop_exe:
        print(f"\n🎉 桌面快捷路径: {desktop_exe}")
        print("   双击即可运行 ERP智能系统！")


if __name__ == "__main__":
    main()
