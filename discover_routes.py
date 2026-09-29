import urllib.request, json

base = "http://127.0.0.1:8620/api/v1"
headers = {"Content-Type": "application/json"}

# Try various endpoint paths
test_paths = [
    # Sales
    "/sales/orders",
    "/sales/contracts",
    "/sales/customers/",
    # Contracts
    "/contracts/",
    # Inventory
    "/inventory/",
    "/inv2/batches",
    "/inv2/inventory-records",
    # Finance
    "/finance/",
    "/fn2/vouchers",
    "/fn2/voucher-entries",
    # Production
    "/production/",
    # Plan
    "/plan/",
    # PMC
    "/pp/",
    # BOM
    "/bom/",
    # Procurement
    "/procurement/",
    # Purchase
    "/purchase/",
    "/pm/purchase-orders",
]

print("=== API Route Discovery ===")
for ep in test_paths:
    try:
        r = urllib.request.Request(base + ep, headers=headers, method="GET")
        resp = urllib.request.urlopen(r, timeout=3)
        data = json.loads(resp.read())
        if data.get("success"):
            d = data.get("data")
            if isinstance(d, list):
                count = len(d)
            elif isinstance(d, dict):
                count = len(d)
            else:
                count = 0
            print(f"  OK   {ep:35s} {count} items")
        else:
            print(f"  ERR  {ep:35s} {data.get('message','')[:60]}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            pass  # skip
        elif e.code == 401:
            print(f"  AUTH {ep:35s} needs auth")
        elif e.code == 422:
            print(f"  OK   {ep:35s} (needs params)")
        else:
            print(f"  {e.code}   {ep:35s}")
    except Exception as e:
        pass

# Check OpenAPI docs for all routes
try:
    r = urllib.request.urlopen(base + "/openapi.json", timeout=5)
    spec = json.loads(r.read())
    pm2_routes = [p for p in spec.get("paths",{}) if "/pm2/" in p]
    print("\n=== PM2 Routes ===")
    for p in sorted(pm2_routes):
        methods = list(spec["paths"][p].keys())
        print(f"  {p:45s} {methods}")

    fn2_routes = [p for p in spec.get("paths",{}) if "/fn2/" in p]
    print("\n=== FN2 Routes ===")
    for p in sorted(fn2_routes)[:10]:
        methods = list(spec["paths"][p].keys())
        print(f"  {p:45s} {methods}")

    inv2_routes = [p for p in spec.get("paths",{}) if "/inv2/" in p]
    print("\n=== INV2 Routes ===")
    for p in sorted(inv2_routes)[:10]:
        methods = list(spec["paths"][p].keys())
        print(f"  {p:45s} {methods}")

    sm_routes = [p for p in spec.get("paths",{}) if "/sm/" in p]
    print("\n=== SM Routes ===")
    for p in sorted(sm_routes)[:10]:
        methods = list(spec["paths"][p].keys())
        print(f"  {p:45s} {methods}")

    contract_routes = [p for p in spec.get("paths",{}) if "/contracts" in p]
    print("\n=== Contract Routes ===")
    for p in sorted(contract_routes):
        methods = list(spec["paths"][p].keys())
        print(f"  {p:45s} {methods}")
except Exception as e:
    print(f"OpenAPI error: {e}")
