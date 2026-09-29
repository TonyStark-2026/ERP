import urllib.request

# 测试按条形码搜索(扫码枪场景)
r = urllib.request.urlopen('http://localhost:8000/api/v1/materials/search?q=PO260819-001')
print("按条形码搜索:", r.read().decode()[:300])

# 测试快速入库
import json
data = json.dumps({
    "account_set_id": 1,
    "items": [{"material_id": 1, "quantity": 10, "unit_price": 25.5}]
}).encode('utf-8')
req = urllib.request.Request('http://localhost:8000/api/v1/inventory/quick-inbound', data=data, headers={'Content-Type': 'application/json'}, method='POST')
r = urllib.request.urlopen(req)
print("\n快速入库:", r.read().decode())
