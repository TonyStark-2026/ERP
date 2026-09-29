import urllib.request, json, time
time.sleep(2)
base = "http://127.0.0.1:8000"

tests = [
    ("GET", "/api/v1/reports/account-balance?year_month=2026-08", "Account balance"),
    ("GET", "/api/v1/reports/aging-analysis?aux_type=customer&year_month=2026-08", "Aging customer"),
    ("GET", "/api/v1/reports/aging-analysis?aux_type=supplier&year_month=2026-08", "Aging supplier"),
    ("GET", "/api/v1/reports/period-expense?year_month=2026-08", "Period expense"),
    ("GET", "/api/v1/reports/inventory-detail?year_month=2026-08", "Inventory detail"),
    ("GET", "/api/v1/reports/vat?year_month=2026-08", "VAT report"),
    ("GET", "/api/v1/reports/surtax?year_month=2026-08", "Surtax report"),
    ("GET", "/api/v1/reports/versions?report_type=balance_sheet", "Report versions"),
    ("GET", "/api/v1/reports/trace?account_code=1401&year_month=2026-08", "Trace account"),
]

for method, path, name in tests:
    try:
        r = urllib.request.urlopen(f"{base}{path}", timeout=5)
        d = json.loads(r.read())
        success = d.get('success', False)
        data_keys = list(d.get('data', {}).keys()) if isinstance(d.get('data'), dict) else 'N/A'
        print(f"[{'OK' if success else 'FAIL'}] {name}: keys={data_keys}")
    except Exception as e:
        print(f"[FAIL] {name}: {e}")
