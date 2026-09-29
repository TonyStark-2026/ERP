import urllib.request, json

# Try different docs paths
paths_to_try = [
    "http://127.0.0.1:8620/docs",
    "http://127.0.0.1:8620/api/v1/docs",
    "http://127.0.0.1:8620/openapi.json",
    "http://127.0.0.1:8620/api/v1/openapi.json",
    "http://127.0.0.1:8620/redoc",
    "http://127.0.0.1:8620/health",
]

for p in paths_to_try:
    try:
        r = urllib.request.urlopen(p, timeout=3)
        content = r.read()
        print(f"OK   {p:50s} {len(content)} bytes")
        if 'openapi' in p.lower():
            spec = json.loads(content)
            all_paths = list(spec.get("paths",{}).keys())
            print(f"  Total routes: {len(all_paths)}")
            # Show all non-pm2 routes
            for route in sorted(all_paths):
                if any(k in route for k in ['/sm/','/sales','/contract','/fn2','/inv2','/purchase','/pm/']):
                    methods = list(spec["paths"][route].keys())
                    print(f"  {route:50s} {methods}")
    except Exception as e:
        print(f"FAIL {p:50s} {str(e)[:60]}")
