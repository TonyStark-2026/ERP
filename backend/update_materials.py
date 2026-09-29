import urllib.request
import json

materials = [
    {"id": 1, "barcode": "BC001"},
    {"id": 2, "barcode": "BC002"},
    {"id": 3, "barcode": "BC003"},
    {"id": 4, "barcode": "BC004"}
]

for mat in materials:
    url = f"http://localhost:8000/api/v1/materials/{mat['id']}"
    data = json.dumps({"barcode": mat["barcode"]}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='PUT')
    try:
        r = urllib.request.urlopen(req)
        print(f"Updated material {mat['id']}: {r.read().decode()}")
    except Exception as e:
        print(f"Failed to update material {mat['id']}: {e}")

print("Done")