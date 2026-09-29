import urllib.request, json

r = urllib.request.urlopen('http://127.0.0.1:8000/api/v1/pm/suggestions')
d = json.loads(r.read())
print('Total suggestions:', d['data']['total'])
for item in d['data']['items'][:10]:
    print(f"  {item['suggestion_no']} | {item.get('material_name','')} | {item['status']}")

# Also check purchase orders
r2 = urllib.request.urlopen('http://127.0.0.1:8000/api/v1/purchase/orders')
d2 = json.loads(r2.read())
print('\nTotal purchase orders:', d2['data']['total'])
for item in d2['data']['items'][:5]:
    print(f"  {item['po_no']} | {item['status']}")
