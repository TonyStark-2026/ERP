import urllib.request
import json

# 1. 测试产品目录
r = urllib.request.urlopen('http://localhost:8000/api/v1/materials/product-catalog')
print("产品目录:", r.read().decode()[:300])

# 2. 测试新编码生成 (A类, 产品0301)
r = urllib.request.urlopen('http://localhost:8000/api/v1/materials/generate-code?abc_class=A&product_code=0301')
print("\n生成编码(A/0301):", r.read().decode())

# 3. 测试创建物料
data = json.dumps({
    "account_set_id": 1,
    "name": "进口橡木板",
    "code": "PO20260819A0301001",
    "barcode": "PO20260819A0301001",
    "spec": "1200x2400x18mm",
    "unit": "块",
    "unit_price": 280.00,
    "type": "RAW_MATERIAL",
    "property": "PURCHASE",
    "abc_class": "A",
    "cva_class": "M",
    "safety_stock": 0,
    "min_stock": 0,
    "max_stock": 9999,
    "reorder_point": 0,
    "batch_rule": "FIXED",
    "batch_size": 1,
    "loss_rate": 0,
    "lead_time": 0,
    "description": '{"product_code": "0301"}'
}).encode('utf-8')
req = urllib.request.Request('http://localhost:8000/api/v1/materials/', data=data, headers={'Content-Type': 'application/json'}, method='POST')
r = urllib.request.urlopen(req)
print("\n创建物料:", r.read().decode()[:400])

# 4. 测试扫码搜索
r = urllib.request.urlopen('http://localhost:8000/api/v1/materials/search?q=PO20260819A0301001')
print("\n扫码搜索:", r.read().decode()[:300])
