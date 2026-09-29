import subprocess
import time
import webbrowser
import sys
import os

PORT = 8080

def start_backend():
    """启动后端服务"""
    print("正在启动ERP系统后端服务...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_cmd = [sys.executable, "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", str(PORT)]
    return subprocess.Popen(backend_cmd, cwd=script_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    # 启动后端服务
    proc = start_backend()
    
    # 等待服务启动
    print("等待服务启动...")
    time.sleep(3)
    
    # 检查服务是否启动成功
    try:
        import urllib.request
        # 测试API端点
        urllib.request.urlopen(f"http://localhost:{PORT}/api/v1/finance/reports/balance-sheet", timeout=5)
        print("服务启动成功！")
    except Exception as e:
        print(f"服务启动失败: {e}")
        proc.kill()
        input("按回车键退出...")
        return
    
    # 打开前端页面
    print("正在打开ERP系统...")
    webbrowser.open(f"http://localhost:{PORT}", new=1)
    
    # 保持服务运行
    print(f"ERP系统已启动！访问地址: http://localhost:{PORT}")
    print("按 Ctrl+C 停止服务。")
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        proc.kill()
        print("服务已停止。")

if __name__ == "__main__":
    main()