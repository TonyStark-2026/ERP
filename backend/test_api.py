import urllib.request
import json

# 测试编码生成
r = urllib.request.urlopen('http://localhost:8000/api/v1/materials/generate-code')
print("生成编码:", r.read().decode())

# 测试创建物料
data = json.dumps({
    "account_set_id": 1,
    "name": "测试材料A",
    "spec": "100x50mm",
    "unit": "个",
    "unit_price": 25.5,
    "type": "RAW_MATERIAL",
    "property": "PURCHASE",
    "abc_class": "C",
    "cva_class": "M",
    "safety_stock": 0,
    "min_stock": 0,
    "max_stock": 9999,
    "reorder_point": 0,
    "batch_rule": "FIXED",
    "batch_size": 1,
    "loss_rate": 0,
    "lead_time": 0
}).encode('utf-8')

req = urllib.request.Request('http://localhost:8000/api/v1/materials/', data=data, headers={'Content-Type': 'application/json'}, method='POST')
r = urllib.request.urlopen(req)
print("\n创建物料:", r.read().decode())

# 测试搜索
r = urllib.request.urlopen('http://localhost:8000/api/v1/materials/search?q=PO')
print("\n搜索结果:", r.read().decode()[:500])
