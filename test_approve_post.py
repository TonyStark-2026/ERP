import urllib.request
import json

base = "http://127.0.0.1:8000"

# Test approve
try:
    data = json.dumps({"approver": "test_user"}).encode()
    req = urllib.request.Request(f"{base}/api/v1/vouchers/1/approve", data=data, headers={"Content-Type": "application/json"}, method="POST")
    r = urllib.request.urlopen(req, timeout=5)
    print("1. Approve OK:", json.loads(r.read()))
except urllib.error.HTTPError as e:
    print("1. Approve FAIL:", e.code, e.read().decode())
except Exception as e:
    print("1. Approve FAIL:", e)

# Check detail
try:
    r = urllib.request.urlopen(f"{base}/api/v1/vouchers/1", timeout=5)
    data = json.loads(r.read())
    print("2. Detail OK - status:", data["data"]["status"], "entries:", len(data["data"]["entries"]))
except Exception as e:
    print("2. Detail FAIL:", e)

# Test post
try:
    req = urllib.request.Request(f"{base}/api/v1/vouchers/1/post", method="POST")
    r = urllib.request.urlopen(req, timeout=5)
    print("3. Post OK:", json.loads(r.read()))
except urllib.error.HTTPError as e:
    print("3. Post FAIL:", e.code, e.read().decode())
except Exception as e:
    print("3. Post FAIL:", e)

# Final list
try:
    r = urllib.request.urlopen(f"{base}/api/v1/vouchers", timeout=5)
    data = json.loads(r.read())
    for v in data["data"]["items"]:
        print(f"4. Voucher {v['voucher_no']}: status={v['status']}, total={v['total_debit']}")
except Exception as e:
    print("4. List FAIL:", e)

# Stats
try:
    r = urllib.request.urlopen(f"{base}/api/v1/vouchers/stats/overview", timeout=5)
    print("5. Stats OK:", json.loads(r.read()))
except Exception as e:
    print("5. Stats FAIL:", e)
