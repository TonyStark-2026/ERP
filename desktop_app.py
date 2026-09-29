# -*- coding: utf-8 -*-
"""
ERP VIBE CODING - 桌面窗口App（像普通软件一样使用）
依赖：pywebview
安装方法：pip install pywebview
功能：
1. 内嵌启动后端API服务
2. 打开独立桌面窗口加载ERP系统
3. 关闭窗口自动停止服务
4. 窗口最小尺寸、标题栏、任务栏图标
"""

import subprocess
import sys
import os
import time
import threading
import urllib.request
import socket

# ========== 配置 ==========
PORT = 8765  # 桌面App使用独立端口，避免和浏览器版冲突
APP_TITLE = "ERP智能系统"
WINDOW_WIDTH = 1366
WINDOW_HEIGHT = 820
MIN_WIDTH = 1100
MIN_HEIGHT = 700
PYTHON_CANDIDATES = [
    r"C:\Users\ruancanling\AppData\Local\Programs\Python\Python38\python.exe",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".venv", "Scripts", "python.exe"),
    "python",
]
# ===========================

backend_proc = None
script_dir = os.path.dirname(os.path.abspath(__file__))


def find_python():
    for py in PYTHON_CANDIDATES:
        try:
            r = subprocess.run(
                [py, "-c", "import fastapi, uvicorn; print('OK')"],
                capture_output=True, text=True, timeout=10
            )
            if r.returncode == 0 and "OK" in r.stdout:
                return py
        except Exception:
            continue
    return None


def is_port_used(p):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", p))
            return False
        except OSError:
            return True


def kill_port_owner(p):
    if os.name != "nt":
        return
    try:
        r = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        for line in r.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 5 and f":{p}" in parts[1] and parts[3] == "LISTENING":
                pid = parts[-1]
                if pid.isdigit() and int(pid) > 1000:
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
                    time.sleep(1)
    except Exception:
        pass


def wait_server(url, timeout=120):
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ERP-DesktopApp"})
            r = urllib.request.urlopen(req, timeout=3)
            if r.status == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def start_backend():
    """启动后端子进程"""
    global backend_proc
    python_exe = find_python()
    if not python_exe:
        return False, "未找到Python环境或缺少依赖(fastapi/uvicorn)"

    if is_port_used(PORT):
        kill_port_owner(PORT)
        time.sleep(1)

    cmd = [
        python_exe, "-m", "uvicorn",
        "backend.app:app",
        "--host", "127.0.0.1",
        "--port", str(PORT),
        "--log-level", "warning",
    ]
    try:
        backend_proc = subprocess.Popen(
            cmd,
            cwd=script_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=dict(os.environ, PYTHONIOENCODING="utf-8"),
        )
    except Exception as e:
        return False, f"启动后端失败: {e}"

    ok = wait_server(f"http://127.0.0.1:{PORT}/health")
    if not ok:
        stop_backend()
        return False, "后端服务启动超时（请检查是否端口冲突或依赖缺失）"
    return True, ""


def stop_backend():
    global backend_proc
    if backend_proc:
        try:
            backend_proc.terminate()
            try:
                backend_proc.wait(timeout=5)
            except Exception:
                backend_proc.kill()
        except Exception:
            try:
                backend_proc.kill()
            except Exception:
                pass
        backend_proc = None


def build_splash_html():
    """启动画面HTML（在后端启动期间显示）"""
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  html,body {{ margin:0;padding:0;height:100%;background:linear-gradient(135deg,#1e3c72 0%,#2a5298 100%);
    font-family:"Microsoft YaHei","PingFang SC",sans-serif;color:#fff;overflow:hidden; }}
  .wrap {{ height:100%;display:flex;flex-direction:column;justify-content:center;align-items:center; }}
  .logo {{ font-size:72px;margin-bottom:20px;animation:bounce 2s infinite; }}
  .title {{ font-size:36px;font-weight:bold;margin-bottom:10px;letter-spacing:4px; }}
  .subtitle {{ font-size:16px;opacity:.85;margin-bottom:40px; }}
  .loader {{ width:60px;height:60px;border:5px solid rgba(255,255,255,.2);border-top-color:#fff;
    border-radius:50%;animation:spin 1s linear infinite;margin-bottom:20px; }}
  .status {{ font-size:14px;opacity:.9; }}
  @keyframes spin {{ to {{ transform:rotate(360deg); }} }}
  @keyframes bounce {{ 0%,100% {{ transform:translateY(0); }} 50% {{ transform:translateY(-10px); }} }}
</style>
</head>
<body>
<div class="wrap">
  <div class="logo">🏢</div>
  <div class="title">ERP智能系统</div>
  <div class="subtitle">企业资源管理系统 · 智慧经营 高效协同</div>
  <div class="loader"></div>
  <div class="status" id="s">正在启动服务，请稍候...</div>
</div>
<script>
var msgs = ["正在初始化模块...","正在连接数据库...","正在加载配置...","准备就绪，即将打开系统..."];
var i=0;setInterval(function(){{ if(i<msgs.length){{document.getElementById('s').innerText=msgs[i++];}} }},1500);
</script>
</body>
</html>
"""


def run_app():
    """主函数：启动后端 + 创建窗口"""
    # 尝试导入pywebview，如果没安装给出友好提示
    try:
        import webview
    except ImportError:
        msg = (
            "❌ 缺少依赖包 pywebview！\n\n"
            "请打开命令提示符(CMD)或PowerShell，执行以下命令安装：\n\n"
            "   pip install pywebview\n\n"
            "或者使用一键启动器版本（双击【启动ERP系统.bat】无需安装额外包）。"
        )
        # Windows下用messagebox弹出提示
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, msg, APP_TITLE, 0x30)
        except Exception:
            print(msg)
            input("按回车键退出...")
        sys.exit(1)

    # 1. 先启动后端（在独立线程中启动，避免阻塞窗口创建）
    backend_ok = [False]
    backend_err = [""]

    def backend_thread():
        ok, err = start_backend()
        backend_ok[0] = ok
        backend_err[0] = err

    t = threading.Thread(target=backend_thread, daemon=True)
    t.start()

    # 2. 创建窗口，先显示启动画面
    splash_html = build_splash_html()

    class ApiBridge:
        """JS <-> Python 通信桥梁（预留扩展）"""
        def __init__(self):
            pass

        def get_app_info(self):
            return {
                "title": APP_TITLE,
                "version": "1.0.0",
                "port": PORT,
                "mode": "desktop",
            }

    api = ApiBridge()

    window = webview.create_window(
        title=APP_TITLE,
        html=splash_html,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=(MIN_WIDTH, MIN_HEIGHT),
        resizable=True,
        fullscreen=False,
        confirm_close=False,
        background_color="#1e3c72",
        js_api=api,
        text_select=True,
    )

    # 3. 窗口显示后，检查后端就绪后跳转
    def check_and_load():
        """定时检查后端是否就绪，就绪后加载ERP页面"""
        t.join(timeout=120)
        max_wait = 120
        waited = 0
        while waited < max_wait:
            if backend_ok[0]:
                # 加载成功
                app_url = f"http://127.0.0.1:{PORT}/"
                try:
                    window.load_url(app_url)
                    # 加载完成后动态修改一次标题（避免某些情况下标题不更新）
                    time.sleep(1.5)
                    try:
                        window.evaluate_js(f"document.title = '{APP_TITLE}';")
                    except Exception:
                        pass
                except Exception as e:
                    error_html = f"""
                    <div style="padding:40px;font-family:Microsoft YaHei;">
                    <h2 style="color:#c0392b;">❌ 加载失败</h2>
                    <p style="color:#555;">错误信息: {e}</p>
                    <p>请尝试重新启动App，或使用【启动ERP系统.bat】浏览器版。</p>
                    </div>
                    """
                    window.load_html(error_html)
                return
            if backend_err[0]:
                # 后端启动失败
                err_html = f"""
                <div style="padding:40px;font-family:Microsoft YaHei;background:#fff;">
                <h2 style="color:#c0392b;">❌ 服务启动失败</h2>
                <p style="color:#555;font-size:14px;">{backend_err[0]}</p>
                <hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
                <h3>建议方案：</h3>
                <ul style="line-height:2;color:#333;">
                  <li>方案一：双击使用 <b>启动ERP系统.bat</b>（浏览器版，兼容性最好）</li>
                  <li>方案二：检查Python 3.8+是否安装，依赖包是否齐全</li>
                  <li>方案三：关闭占用端口 {PORT} 的其他软件</li>
                </ul>
                </div>
                """
                window.load_html(err_html)
                return
            time.sleep(1)
            waited += 1
        # 超时
        err_html = f"""
        <div style="padding:40px;font-family:Microsoft YaHei;">
        <h2 style="color:#c0392b;">⏱️ 启动超时</h2>
        <p>后端服务未能在规定时间内启动，请使用【启动ERP系统.bat】浏览器版。</p>
        </div>
        """
        window.load_html(err_html)

    # 窗口显示后执行检查逻辑
    try:
        webview.start(check_and_load, gui="edgechromium")
    except Exception:
        # edgechromium失败，回退到默认gui
        try:
            webview.start(check_and_load)
        except Exception as e:
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(
                    0,
                    f"创建桌面窗口失败：{e}\n\n建议使用【启动ERP系统.bat】浏览器版。",
                    APP_TITLE, 0x30
                )
            except Exception:
                print(f"桌面App启动失败: {e}")
    finally:
        stop_backend()


if __name__ == "__main__":
    os.chdir(script_dir)
    run_app()
