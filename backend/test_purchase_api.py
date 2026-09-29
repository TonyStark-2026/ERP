"""
测试采购管理V2 API端点（使用urllib）
"""
import urllib.request
import json

BASE = "http://127.0.0.1:8000/api/v1/pm"

def test(name, method, path, data=None):
    url = BASE + path
    try:
        req = urllib.request.Request(url, method=method)
        req.add_header('Content-Type', 'application/json')
        req.add_header('Accept', 'application/json')
        if data:
            req.data = json.dumps(data).encode('utf-8')
        with urllib.request.urlopen(req) as resp:
            d = json.loads(resp.read().decode('utf-8'))
            success = d.get("success", False)
            print(f"[{'✓' if success else '✗'}] {name}: {d.get('message', '')}")
            if not success:
                print(f"    Response: {json.dumps(d, ensure_ascii=False)[:200]}")
            return d
    except Exception as e:
        print(f"[✗] {name}: {e}")
        return None

# 1. 供应商列表
print("=== 供应商管理 ===")
test("供应商列表", "GET", "/suppliers")

# 2. 采购订单列表
print("\n=== 采购订单管理 ===")
test("采购订单列表", "GET", "/orders")

# 3. 采购建议
print("\n=== 采购建议 ===")
test("采购建议列表", "GET", "/suggestions?status=PENDING")

# 4. 入库单
print("\n=== 入库单 ===")
test("入库单列表", "GET", "/inbounds")

# 5. 订单跟踪
print("\n=== 订单跟踪 ===")
test("订单跟踪", "GET", "/order-tracking")

# 6. 询价比价
print("\n=== 询价比价 ===")
test("询价列表", "GET", "/quotations")

# 7. 报表
print("\n=== 采购报表 ===")
test("订单执行报表", "GET", "/reports/order-execution")
test("供应商绩效报表", "GET", "/reports/supplier-performance")

print("\n测试完成！")