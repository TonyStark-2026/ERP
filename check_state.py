import urllib.request, json, os, subprocess, sys, time, socket

# Check if server is running
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = s.connect_ex(('127.0.0.1', 8620))
s.close()

if result != 0:
    print("Server not running, starting...")
    subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True)
    time.sleep(2)
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8620", "--log-level", "error"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=r"c:\Users\ruancanling\Desktop\ERP VIBE CODING",
        creationflags=0x00000008
    )
    time.sleep(7)
else:
    print("Server already running")

# Check existing data
base = "http://127.0.0.1:8620/api/v1"
headers = {"Content-Type": "application/json", "X-Account-Set": "1"}

# Get auth token first
try:
    r = urllib.request.Request(base + "/auth/login", data=json.dumps({"username":"超级臭屁","password":"admin123"}).encode(), headers=headers, method="POST")
    resp = urllib.request.urlopen(r, timeout=5)
    auth_data = json.loads(resp.read())
    print("Auth:", auth_data.get("success"))
    token = auth_data.get("data", {}).get("access_token", "")
    headers["Authorization"] = f"Bearer {token}"
except Exception as e:
    print(f"Auth error: {e}")
    # Try without auth
    pass

# Check key data
endpoints = [
    ("GET", "/sm/contracts", "销售合同"),
    ("GET", "/sm/sales-orders", "销售订单"),
    ("GET", "/pm2/production-plans", "生产计划"),
    ("GET", "/pm2/work-orders", "生产工单"),
    ("GET", "/pm2/mrp-results", "MRP结果"),
    ("GET", "/pm2/dispatches", "派工单"),
    ("GET", "/pm2/outsourcing-orders", "委外订单"),
    ("GET", "/pm2/inspections", "质检记录"),
    ("GET", "/pm2/work-reports", "报工单"),
    ("GET", "/pm2/equipments", "设备"),
    ("GET", "/inv2/inventory", "库存"),
    ("GET", "/fn2/vouchers", "凭证"),
]

print("\n=== 现有数据概况 ===")
for method, ep, label in endpoints:
    try:
        r = urllib.request.Request(base + ep, headers=headers, method="GET")
        resp = urllib.request.urlopen(r, timeout=5)
        data = json.loads(resp.read())
        if data.get("success"):
            d = data.get("data")
            if isinstance(d, list):
                count = len(d)
            elif isinstance(d, dict) and "items" in d:
                count = len(d["items"])
            elif isinstance(d, dict):
                count = len(d)
            else:
                count = 0
            print(f"  {label:12s} ({ep:30s}): {count} 条")
        else:
            print(f"  {label:12s} ({ep:30s}): ERROR - {data.get('message','')[:50]}")
    except Exception as e:
        print(f"  {label:12s} ({ep:30s}): FAIL - {str(e)[:50]}")
