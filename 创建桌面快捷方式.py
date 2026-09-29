# -*- coding: utf-8 -*-
"""
生成ERP系统桌面快捷方式
运行后会在Windows桌面上创建两个快捷方式：
1. ERP智能系统（浏览器版） -> 指向 启动ERP系统.bat
2. ERP智能系统 桌面版     -> 指向 ERP桌面版.bat
"""

import os
import sys
import pythoncom  # pywin32
from win32com.client import Dispatch  # pywin32


def install_pywin32():
    """尝试自动安装pywin32"""
    import subprocess
    candidates = [
        r"C:\Users\ruancanling\AppData\Local\Programs\Python\Python38\python.exe",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "Scripts", "python.exe"),
        "python",
    ]
    for py in candidates:
        try:
            subprocess.check_call([py, "-m", "pip", "install", "pywin32"])
            return True
        except Exception:
            continue
    return False


def create_shortcut(target_path, shortcut_name, icon_path=None, description=""):
    """创建桌面快捷方式"""
    try:
        pythoncom.CoInitialize()
        shell = Dispatch("WScript.Shell")
        desktop = shell.SpecialFolders("Desktop")
        shortcut_path = os.path.join(desktop, shortcut_name + ".lnk")

        shortcut = shell.CreateShortcut(shortcut_path)
        shortcut.TargetPath = target_path
        shortcut.WorkingDirectory = os.path.dirname(target_path)
        shortcut.Description = description or shortcut_name
        if icon_path and os.path.exists(icon_path):
            shortcut.IconLocation = icon_path
        shortcut.WindowStyle = 1  # 1=正常窗口, 3=最大化, 7=最小化
        shortcut.save()
        pythoncom.CoUninitialize()
        return True, shortcut_path
    except ImportError as e:
        return False, f"缺少依赖pywin32: {e}"
    except Exception as e:
        return False, str(e)


def main():
    print("=" * 60)
    print("  🏢 ERP智能系统 - 桌面快捷方式生成器")
    print("=" * 60)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    launcher_bat = os.path.join(script_dir, "启动ERP系统.bat")
    desktop_bat = os.path.join(script_dir, "ERP桌面版.bat")

    # 检查文件是否存在
    for f in [launcher_bat, desktop_bat]:
        if not os.path.exists(f):
            print(f"❌ 缺少文件: {f}")
            input("按回车键退出...")
            sys.exit(1)

    # 先尝试导入依赖
    try:
        import pythoncom
        from win32com.client import Dispatch
    except ImportError:
        print("\n⚠️  需要安装 pywin32 才能创建快捷方式")
        ans = input("是否自动安装？(Y/n): ").strip().lower()
        if ans in ("", "y", "yes"):
            print("正在安装 pywin32...")
            if not install_pywin32():
                print("❌ 自动安装失败，请手动执行: pip install pywin32")
                print("   或者手动右键【启动ERP系统.bat】 -> 发送到 -> 桌面快捷方式")
                input("按回车键退出...")
                sys.exit(1)
            print("✅ 安装成功！")
            try:
                import pythoncom
                from win32com.client import Dispatch
            except Exception as e:
                print(f"❌ 导入依然失败: {e}")
                input("按回车键退出...")
                sys.exit(1)
        else:
            print("已取消。您也可以手动右键bat文件 -> 发送到 -> 桌面快捷方式")
            input("按回车键退出...")
            sys.exit(0)

    print("\n📝 正在创建桌面快捷方式...\n")

    # 快捷方式1：浏览器版
    ok, path = create_shortcut(
        launcher_bat,
        "ERP智能系统",
        description="ERP智能系统 企业管理系统（浏览器版）- 双击启动后自动打开浏览器"
    )
    if ok:
        print(f"  ✅ 已创建: {path}")
    else:
        print(f"  ❌ 创建失败: {path}")

    # 快捷方式2：桌面窗口版
    ok2, path2 = create_shortcut(
        desktop_bat,
        "ERP智能系统 桌面版",
        description="ERP智能系统 企业管理系统（桌面窗口版）- 独立窗口，像普通软件一样使用"
    )
    if ok2:
        print(f"  ✅ 已创建: {path2}")
    else:
        print(f"  ❌ 创建失败: {path2}")

    print("\n" + "=" * 60)
    print("  ✅ 完成！现在可以在桌面上双击图标启动ERP系统了")
    print("")
    print("  📘 使用说明:")
    print("    方式一：【ERP智能系统】         -> 自动打开浏览器使用（推荐，兼容性最好）")
    print("    方式二：【ERP智能系统 桌面版】   -> 独立窗口（像Excel一样的软件）")
    print("=" * 60)
    print()
    input("按回车键退出...")


if __name__ == "__main__":
    main()
