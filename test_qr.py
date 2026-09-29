import subprocess
import time
import urllib.request
import urllib.error
import json
import sys
import os

BASE_URL = "http://127.0.0.1:8620"
PYTHON = r"C:\Users\ruancanling\AppData\Local\Programs\Python\Python38\python.exe"
WORK_DIR = r"c:\Users\ruancanling\Desktop\ERP VIBE CODING"

# Change to working directory
os.chdir(WORK_DIR)

results = []

def log(test_name, status, detail=""):
    entry = {"test": test_name, "status": status, "detail": detail}
    results.append(entry)
    icon = "PASS" if status == "PASS" else "FAIL" if status == "FAIL" else "WARN"
    print(f"[{icon}] {test_name}")
    if detail:
        print(f"       {detail}")

def make_request(method, url, data=None, headers=None):
    try:
        if data and isinstance(data, dict):
            data = json.dumps(data).encode('utf-8')
            if headers is None:
                headers = {}
            headers['Content-Type'] = 'application/json'
        
        req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode('utf-8')
            try:
                body = json.loads(body)
            except:
                pass
            return resp.status, body, None
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        try:
            body = json.loads(body)
        except:
            pass
        return e.code, body, str(e)
    except Exception as e:
        return None, None, str(e)

# Start server
print("=" * 60)
print("Starting backend server...")
proc = subprocess.Popen(
    [PYTHON, '-m', 'uvicorn', 'backend.app:app', '--host', '0.0.0.0', '--port', '8620'],
    creationflags=0x08000000
)
print(f"Server PID: {proc.pid}")
print("Waiting 5 seconds...")
time.sleep(5)

# Test 1: Health check
print("\n" + "=" * 60)
print("TEST 1: Health Check (/health)")
status, body, err = make_request('GET', f"{BASE_URL}/health")
if status == 200 and body and body.get('success'):
    log("健康检查 /health", "PASS", f"Status: {status}, Response: {json.dumps(body, ensure_ascii=False)}")
else:
    log("健康检查 /health", "FAIL", f"Status: {status}, Error: {err}, Body: {body}")

# Test 2: QR code generation
print("\n" + "=" * 60)
print("TEST 2: QR Code Generation (/api/v1/materials/qr-image)")
status, body, err = make_request('GET', f"{BASE_URL}/api/v1/materials/qr-image?text=TEST_MATERIAL_001")
if status == 200:
    # Check if response is an image or JSON
    if isinstance(body, dict):
        log("二维码生成 /api/v1/materials/qr-image", "PASS", 
            f"Status: {status}, Response: {json.dumps(body, ensure_ascii=False)[:500]}")
    else:
        log("二维码生成 /api/v1/materials/qr-image", "PASS", 
            f"Status: {status}, Binary/image response (type check)")
else:
    log("二维码生成 /api/v1/materials/qr-image", "FAIL", 
        f"Status: {status}, Error: {err}, Body: {str(body)[:500]}")

# Test 3: Login
print("\n" + "=" * 60)
print("TEST 3: Login (/api/v1/auth/login)")
status, body, err = make_request('POST', f"{BASE_URL}/api/v1/auth/login", 
    data={"username": "超级臭屁", "password": "123456"})
if status == 200:
    if isinstance(body, dict) and body.get('success'):
        log("登录接口 /api/v1/auth/login", "PASS", 
            f"Status: {status}, User: {body.get('data', {}).get('username', 'N/A') if isinstance(body.get('data'), dict) else body.get('data')}")
    else:
        log("登录接口 /api/v1/auth/login", "FAIL", 
            f"Status: {status}, Response: {json.dumps(body, ensure_ascii=False)[:500]}")
else:
    log("登录接口 /api/v1/auth/login", "FAIL", 
        f"Status: {status}, Error: {err}, Body: {str(body)[:500]}")

# Test 4: Quick inbound
print("\n" + "=" * 60)
print("TEST 4: Quick Inbound (/api/v1/inventory/quick-inbound)")
status, body, err = make_request('POST', f"{BASE_URL}/api/v1/inventory/quick-inbound",
    data={"account_set_id": 1, "items": []})
if status == 200:
    log("快速入库 /api/v1/inventory/quick-inbound", "PASS", 
        f"Status: {status}, Response: {json.dumps(body, ensure_ascii=False)[:500]}")
else:
    log("快速入库 /api/v1/inventory/quick-inbound", "FAIL", 
        f"Status: {status}, Error: {err}, Body: {str(body)[:500]}")

# Summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
pass_count = sum(1 for r in results if r['status'] == 'PASS')
fail_count = sum(1 for r in results if r['status'] == 'FAIL')
for r in results:
    icon = "PASS" if r['status'] == 'PASS' else "FAIL"
    print(f"  [{icon}] {r['test']}")
    if r['detail']:
        print(f"         {r['detail'][:200]}")
print(f"\nTotal: {len(results)} | Passed: {pass_count} | Failed: {fail_count}")

# Cleanup
print("\nShutting down server...")
try:
    proc.terminate()
    proc.wait(timeout=5)
    print("Server stopped.")
except:
    try:
        proc.kill()
        print("Server killed.")
    except:
        pass