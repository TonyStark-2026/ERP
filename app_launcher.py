# -*- coding: utf-8 -*-
"""
ERP VIBE CODING - 一键启动器
功能：
1. 自动启动后端API服务（端口8000，监听0.0.0.0支持手机/局域网访问）
2. 健康检查等待服务就绪
3. 自动打开浏览器跳转到ERP系统
4. 控制台显示启动日志
5. 自动获取局域网IP + 生成二维码，手机扫码即可访问
6. 提示将PWA添加到手机主屏幕，像普通App一样使用
"""

import subprocess
import sys
import os
import time
import webbrowser
import urllib.request
import socket
import platform
import traceback

# ============== 配置 ==============
PORT = 8000
APP_TITLE = "ERP智能系统"
PYTHON_CANDIDATES = [
    r"C:\Users\ruancanling\AppData\Local\Programs\Python\Python38\python.exe",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "Scripts", "python.exe"),
    "python",
    "python3",
]
# ==================================


def find_python():
    for py in PYTHON_CANDIDATES:
        try:
            result = subprocess.run(
                [py, "-c", "import fastapi, uvicorn; print('OK')"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and "OK" in result.stdout:
                return py
        except Exception:
            continue
    return None


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("0.0.0.0", port))
            return False
        except OSError:
            return True


def wait_for_server(url, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ERP-Launcher"})
            resp = urllib.request.urlopen(req, timeout=3)
            if resp.status == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
        elapsed = int(time.time() - start)
        print(f"  ⏳ 正在启动服务... ({elapsed}s / {timeout}s)")
    return False


def get_lan_ips():
    """
    获取本机所有局域网IPv4地址列表（排除127.0.0.1和虚拟网卡）
    返回类似 ['192.168.1.23', '10.0.0.5']
    """
    ips = []
    try:
        # 方式一：Windows下用ipconfig
        if platform.system() == "Windows":
            try:
                r = subprocess.run(["ipconfig"], capture_output=True, text=True, encoding="gbk", errors="ignore")
                lines = r.stdout.splitlines() + (r.stderr or "").splitlines()
                current_adapter_ok = False
                for line in lines:
                    line = line.strip()
                    # 判定是否是真实网卡适配器
                    if any(k in line for k in ["无线局域网适配器", "以太网适配器", "WLAN", "Ethernet", "本地连接"]):
                        # 排除虚拟、VPN、VMware、Hyper-V、蓝牙等
                        bad = any(b in line.lower() for b in [
                            "virtual", "vmware", "hyper-v", "vpn", "bluetooth", "蓝牙",
                            "loopback", "pseudo", "wan", "microsoft km-test",
                        ])
                        current_adapter_ok = not bad
                        continue
                    if "IPv4" in line or "IPV4" in line or "ipv4" in line or "IP 地址" in line:
                        parts = line.split(":")
                        if len(parts) >= 2:
                            ip = parts[-1].strip()
                            if _is_valid_lan_ip(ip) and current_adapter_ok and ip not in ips:
                                ips.append(ip)
            except Exception:
                pass
        # 方式二：socket.gethostbyname_ex（通用）
        try:
            hostname = socket.gethostname()
            for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
                ip = info[4][0]
                if _is_valid_lan_ip(ip) and ip not in ips:
                    ips.append(ip)
        except Exception:
            pass
        # 方式三：连接外网探测得到出口本地IP
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                if _is_valid_lan_ip(ip) and ip not in ips:
                    ips.insert(0, ip)
        except Exception:
            pass
    except Exception:
        traceback.print_exc()
    # 排序：优先常用的192.168.*
    def sort_key(ip):
        if ip.startswith("192.168."):
            return 0
        if ip.startswith("10."):
            return 1
        if ip.startswith("172."):
            return 2
        return 3
    ips.sort(key=sort_key)
    return ips


def _is_valid_lan_ip(ip):
    """判断是否是内网IPv4（排除0.0.0.0/127.*/*.*.*.*格式错误）"""
    try:
        parts = [int(x) for x in ip.split(".")]
        if len(parts) != 4:
            return False
        if any(p < 0 or p > 255 for p in parts):
            return False
        if parts[0] == 127 or parts[0] == 0:
            return False
        if parts[0] == 192 and parts[1] == 168:
            return True
        if parts[0] == 10:
            return True
        if parts[0] == 172 and 16 <= parts[1] <= 31:
            return True
        return False
    except Exception:
        return False


def print_ascii_qr(url, version=None, error_correct="M"):
    """在控制台打印ASCII二维码（黑白方块字符），兼容Windows CMD"""
    try:
        import qrcode
        qr = qrcode.QRCode(version=version, error_correction=getattr(qrcode.constants, "ERROR_CORRECT_" + error_correct),
                           box_size=1, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        mat = qr.get_matrix()
        # Unicode方块字符：上下两行合并成一个字符（更紧凑好看）
        BLACK = "\u2588"  # 全黑
        TOP = "\u2580"    # 上半
        BOT = "\u2584"    # 下半
        SP = " "
        lines = []
        for y in range(0, len(mat), 2):
            row = []
            for x in range(len(mat[y])):
                up = bool(mat[y][x])
                if y + 1 < len(mat):
                    lo = bool(mat[y + 1][x])
                else:
                    lo = False
                if up and lo:
                    row.append(BLACK)
                elif up and not lo:
                    row.append(TOP)
                elif (not up) and lo:
                    row.append(BOT)
                else:
                    row.append(SP)
            lines.append("".join(row))
        print("\n".join("  " + ln for ln in lines))
        return True
    except Exception as e:
        print(f"  ⚠️  ASCII二维码生成失败: {e}")
        return False


def save_qr_png(url, out_path):
    """保存二维码为PNG图片，返回是否成功"""
    try:
        import qrcode
        from qrcode.constants import ERROR_CORRECT_H
        qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_H,
                           box_size=10, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1e3c72", back_color="white")
        img.save(out_path, "PNG")
        return True
    except Exception as e:
        print(f"  ⚠️  PNG二维码保存失败: {e}")
        return False


def kill_existing_backend(port):
    if os.name != "nt":
        return
    try:
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 5 and f":{port}" in parts[1] and parts[3] == "LISTENING":
                pid = parts[-1]
                if pid.isdigit() and int(pid) > 1000:
                    print(f"  🧹 清理旧进程 PID: {pid}")
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
                    time.sleep(1)
    except Exception:
        pass


def main():
    print("=" * 66)
    print(f"  🚀 {APP_TITLE}")
    print("  💻 本机使用 · 📱 手机扫码使用（同WiFi）")
    print("=" * 66)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # 1. 查找Python
    print("\n[1/5] 🔍 查找Python运行环境...")
    python_exe = find_python()
    if not python_exe:
        print("  ❌ 未找到可用的Python环境！请先安装Python 3.8+ 及依赖(fastapi, uvicorn, sqlalchemy, pydantic)")
        print("     安装命令: pip install fastapi uvicorn sqlalchemy pydantic qrcode[pil]")
        input("\n按回车键退出...")
        sys.exit(1)
    print(f"  ✅ 使用Python: {python_exe}")

    # 2. 清理旧进程
    print("\n[2/5] 🧹 检查并清理旧进程...")
    if is_port_in_use(PORT):
        print(f"  ⚠️  端口 {PORT} 已被占用，尝试清理...")
        kill_existing_backend(PORT)
        time.sleep(2)
    else:
        print(f"  ✅ 端口 {PORT} 空闲（监听0.0.0.0支持手机访问）")

    # 3. 启动后端服务（监听0.0.0.0，局域网可访问）
    print(f"\n[3/5] 🖥️  启动ERP后端服务 (端口 {PORT})...")
    backend_cmd = [
        python_exe, "-m", "uvicorn",
        "backend.app:app",
        "--host", "0.0.0.0",
        "--port", str(PORT),
        "--log-level", "warning",
    ]
    try:
        backend_proc = subprocess.Popen(
            backend_cmd, cwd=script_dir,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, universal_newlines=True,
            env=dict(os.environ, PYTHONIOENCODING="utf-8"),
        )
    except Exception as e:
        print(f"  ❌ 启动后端失败: {e}")
        input("\n按回车键退出...")
        sys.exit(1)

    # 4. 等待服务就绪
    print("\n[4/5] ⏳ 等待服务启动...")
    local_url = f"http://localhost:{PORT}/"
    health_url = f"http://localhost:{PORT}/health"

    if not wait_for_server(health_url, timeout=90):
        print("  ❌ 服务启动超时！")
        print("     后端日志如下：")
        try:
            for _ in range(30):
                line = backend_proc.stdout.readline()
                if line:
                    print(f"     | {line.rstrip()}")
                else:
                    break
        except Exception:
            pass
        backend_proc.kill()
        input("\n按回车键退出...")
        sys.exit(1)
    print("  ✅ 服务启动成功！")

    # 5. 收集访问地址（本机 + 局域网）
    print("\n[5/5] 📡 正在获取局域网访问地址...")
    lan_ips = get_lan_ips()
    # 优先选择质量最高的IP
    primary_lan_ip = lan_ips[0] if lan_ips else None
    lan_urls = [f"http://{ip}:{PORT}/" for ip in lan_ips]
    primary_lan_url = lan_urls[0] if lan_urls else None
    print(f"  ✅ 本机地址:      {local_url}")
    if primary_lan_url:
        print(f"  ✅ 手机/局域网:   {primary_lan_url}")
    if len(lan_urls) > 1:
        for extra in lan_urls[1:]:
            print(f"       备用地址:  {extra}")
    if not lan_urls:
        print("  ⚠️  未获取到局域网IP，手机可能无法访问（请检查WiFi连接）")

    # 6. 生成二维码（ASCII + PNG）
    qr_png_path = os.path.join(script_dir, "手机访问ERP二维码.png")
    if primary_lan_url:
        print("\n" + "=" * 66)
        print("  📱【手机扫码访问ERP】  手机和电脑连接同一个WiFi后扫码：")
        print("-" * 66)
        print_ascii_qr(primary_lan_url)
        print("-" * 66)
        if save_qr_png(primary_lan_url, qr_png_path):
            print(f"  💾 二维码已保存: {qr_png_path}")
            print(f"     （可发送到手机，或直接让手机对着屏幕扫码）")
    else:
        print("\n  ⚠️  无有效局域网IP，跳过二维码生成。请检查电脑是否已连接WiFi/有线网络。")

    # 7. 打开本机浏览器
    print(f"\n🌐 正在本机打开ERP系统: {local_url}")
    try:
        webbrowser.open(local_url, new=2)
    except Exception:
        print(f"  ⚠️  无法自动打开浏览器，请手动访问: {local_url}")

    # 8. 输出使用总结
    print("\n" + "=" * 66)
    print(f"  ✅ {APP_TITLE} 已启动成功！")
    print("=" * 66)
    print(f"  💻 本机电脑:  {local_url}")
    if primary_lan_url:
        print(f"  📱 手机访问:  {primary_lan_url}")
        print(f"     (或直接扫上方二维码，手机必须和电脑连同一个WiFi)")
    print(f"  📡 API文档:   http://localhost:{PORT}/docs")
    print()
    print("  📲 手机安装成App使用方法（PWA，像微信一样有图标）:")
    print("    ▸ Android (Chrome/Edge浏览器): 打开网址 → 右上角菜单 → 添加到主屏幕")
    print("    ▸ iPhone (Safari浏览器):       打开网址 → 分享 → 添加到主屏幕")
    print("    ▸ 添加后桌面出现【VIBE ERP】图标，像普通App一样打开使用")
    print()
    print("  ⚠️  关闭此控制台窗口 = 停止ERP服务（手机和电脑都将无法访问）")
    print("=" * 66)
    print("\n💡 提示: Ctrl+C 安全停止服务\n")

    # 保持运行，实时输出异常/错误日志
    try:
        while True:
            line = backend_proc.stdout.readline()
            if line:
                stripped = line.rstrip()
                if stripped and ("ERROR" in stripped.upper() or "Exception" in stripped or "Traceback" in stripped):
                    print(f"  📝 {stripped}")
            else:
                break
    except KeyboardInterrupt:
        print("\n\n🛑 正在停止服务...")
    finally:
        try:
            backend_proc.terminate()
            backend_proc.wait(timeout=5)
        except Exception:
            try:
                backend_proc.kill()
            except Exception:
                pass
        print("✅ 服务已停止，感谢使用ERP智能系统！")


if __name__ == "__main__":
    main()
