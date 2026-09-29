"""
广州机器人项目 — ERP全流程演示
从立项 → 采购 → 生产 → 交付 → 财务
"""
import urllib.request, json, os, subprocess, sys, time, socket

BASE = "http://127.0.0.1:8620/api/v1"
HEADERS = {"Content-Type": "application/json"}

def api(method, path, data=None):
    url = BASE + path
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        return result
    except urllib.error.HTTPError as e:
        try:
            result = json.loads(e.read())
            return result
        except:
            return {"success": False, "message": f"HTTP {e.code}"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def sep(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def step(n, title):
    print(f"\n  [{n}] {title}")

def ok(msg):
    print(f"      OK  {msg}")

def fail(msg):
    print(f"      XX  {msg}")

def info(msg):
    print(f"      >>  {msg}")

# ============================================================
# 启动检查
# ============================================================
sep("广州机器人项目 — ERP全流程演示")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
if s.connect_ex(('127.0.0.1', 8620)) != 0:
    print("  服务器未启动，正在启动...")
    subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True)
    time.sleep(2)
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8620", "--log-level", "error"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=r"c:\Users\ruancanling\Desktop\ERP VIBE CODING",
        creationflags=0x00000008
    )
    time.sleep(7)
else:
    print("  服务器已运行")

r = api("GET", "/pm2/overview")
if r.get("success"):
    d = r["data"]
    print(f"  系统概览：工单{d.get('active_work_orders',0)} 计划{d.get('plan_count',0)} MRP{d.get('mrp_count',0)} 派工{d.get('dispatch_count',0)} 委外{d.get('outsourcing_count',0)}")

# ============================================================
# 1. 立项阶段
# ============================================================
sep("1. 项目立项")

step("1.1", "项目WBS")
# 查询WBS项目
r = api("GET", "/eng-modules/sales-orders")
data = r.get("data", r) if isinstance(r, dict) else r
if isinstance(data, list):
    for so in data[:5]:
        info(f"销售订单: {so.get('order_no','')} 状态:{so.get('status','')} 金额:¥{so.get('total_amount',0)}")
elif isinstance(data, dict) and isinstance(data.get("data"), list):
    for so in data["data"][:5]:
        info(f"销售订单: {so.get('order_no','')} 状态:{so.get('status','')} 金额:¥{so.get('total_amount',0)}")

# 查询合同
r = api("GET", "/pm/contracts")
if r.get("success"):
    contracts = r.get("data", [])
    if isinstance(contracts, list):
        for c in contracts[:3]:
            info(f"合同 {c.get('contract_no','')}: {c.get('contract_name','')} ¥{c.get('contract_amount',0):,}")
    elif isinstance(contracts, dict) and "items" in contracts:
        for c in contracts["items"][:3]:
            info(f"合同 {c.get('contract_no','')}: {c.get('contract_name','')} ¥{c.get('contract_amount',0):,}")
else:
    info(f"合同API: {r.get('message','')}")

# 查询物料
r = api("GET", "/materials/")
mats = r.get("data", []) if isinstance(r, dict) else (r if isinstance(r, list) else [])
info(f"物料编码库: {len(mats)} 条")

step("1.2", "BOM物料清单")
# 查询BOM
r = api("GET", "/bom/")
boms = r.get("data", []) if isinstance(r, dict) else (r if isinstance(r, list) else [])
info(f"BOM数量: {len(boms)}")
for b in boms[:3]:
    info(f"  BOM #{b.get('id')}: {b.get('name','')} 版本{b.get('version','')} 状态:{b.get('status','')}")

# ============================================================
# 2. 采购阶段
# ============================================================
sep("2. 采购管理")

step("2.1", "MRP物料需求分析")
r = api("GET", "/pm2/mrp-results")
if r.get("success"):
    data = r.get("data", {})
    items = data.get("items", []) if isinstance(data, dict) else data
    info(f"MRP运算批次: {data.get('mrp_run_no','') if isinstance(data,dict) else ''}")
    info(f"物料需求明细: {len(items)} 条")
    purchase_items = [m for m in items if m.get("planned_type") == "PURCHASE"]
    production_items = [m for m in items if m.get("planned_type") == "PRODUCTION"]
    info(f"  需采购: {len(purchase_items)} 种物料")
    info(f"  需生产: {len(production_items)} 种物料")
    for m in items[:5]:
        info(f"  {m.get('material_code','')} {m.get('material_name','')}: 毛需求{m.get('gross_requirement',0)} 净需求{m.get('net_requirement',0)} → {m.get('planned_type_label','')}")

step("2.2", "采购订单")
r = api("GET", "/pm/orders")
orders = r.get("data", []) if isinstance(r, dict) else (r if isinstance(r, list) else [])
if isinstance(orders, list):
    info(f"采购订单: {len(orders)} 张")
    for o in orders[:3]:
        info(f"  {o.get('order_no','')}: 供应商={o.get('supplier_name','') or o.get('supplier_id','')} 状态={o.get('status','')}")
elif isinstance(orders, dict) and "items" in orders:
    info(f"采购订单: {len(orders['items'])} 张")
    for o in orders["items"][:3]:
        info(f"  {o.get('order_no','')}: 供应商={o.get('supplier_name','') or o.get('supplier_id','')} 状态={o.get('status','')}")

step("2.3", "采购入库")
r = api("GET", "/pm/inbounds")
inbounds = r.get("data", []) if isinstance(r, dict) else (r if isinstance(r, list) else [])
if isinstance(inbounds, list):
    info(f"入库单: {len(inbounds)} 张")
elif isinstance(inbounds, dict) and "items" in inbounds:
    info(f"入库单: {len(inbounds['items'])} 张")

# ============================================================
# 3. 生产阶段
# ============================================================
sep("3. 生产管理")

step("3.1", "生产计划")
r = api("GET", "/pm2/production-plans")
if r.get("success"):
    plans = r.get("data", [])
    info(f"生产计划: {len(plans)} 张")
    for p in plans[:4]:
        info(f"  {p.get('plan_no','')}: {p.get('plan_type_label','')} 状态={p.get('status_label','')} 总量={p.get('total_qty',0)}")
        items = p.get("items", [])
        for it in items[:2]:
            info(f"    → {it.get('product_code','')} {it.get('product_name','')}: {it.get('quantity',0)}件")

step("3.2", "工艺路线")
r = api("GET", "/pm2/routings")
if r.get("success"):
    data = r.get("data", {})
    items = data.get("items", []) if isinstance(data, dict) else data
    info(f"工艺路线: {len(items)} 条")
    for rt in items[:3]:
        info(f"  {rt.get('name','')} 版本{rt.get('version','')} 工序数:{rt.get('operation_count',0)}道")

step("3.3", "生产工单")
r = api("GET", "/pm2/work-orders?status=ALL")
if r.get("success"):
    wos = r.get("data", [])
    info(f"生产工单: {len(wos)} 张")
    total_cost = 0
    for wo in wos:
        cost = wo.get("actual_total", 0)
        total_cost += cost
        ratio = wo.get("completion_ratio", 0)
        info(f"  {wo.get('work_order_no','')}: {wo.get('product_code','')} {wo.get('product_name','')} 计划{wo.get('planned_qty',0)} 完工{wo.get('completed_qty',0)} ({int(ratio)}%) ¥{cost:,.0f} {wo.get('status_label','')}")
    info(f"  生产成本合计: ¥{total_cost:,.2f}")

step("3.4", "派工管理")
r = api("GET", "/pm2/dispatches?status=ALL")
if r.get("success"):
    disps = r.get("data", [])
    info(f"派工单: {len(disps)} 张")
    for d in disps[:5]:
        info(f"  {d.get('dispatch_no','')}: {d.get('product_name','')} 工序={d.get('process_name','')} 数量={d.get('dispatch_qty',0)} 操作工={d.get('operator','')} {d.get('status_label','')}")

step("3.5", "工序报工")
r = api("GET", "/pm2/work-reports")
if r.get("success"):
    data = r.get("data", {})
    items = data.get("items", []) if isinstance(data, dict) else data
    info(f"报工单: {len(items)} 张")
    total_completed = sum(w.get("completed_qty",0) for w in items)
    total_qualified = sum(w.get("qualified_qty",0) for w in items)
    total_defective = sum(w.get("defective_qty",0) for w in items)
    total_time = sum(w.get("actual_time",0) for w in items)
    for w in items[:5]:
        rate = (w.get("qualified_qty",0)/w.get("completed_qty",1)*100) if w.get("completed_qty") else 0
        info(f"  {w.get('report_no','')}: 工人={w.get('worker','')} 完工{w.get('completed_qty',0)} 合格{w.get('qualified_qty',0)} 废品{w.get('defective_qty',0)} ({rate:.1f}%) 工时{w.get('actual_time',0)}分")
    info(f"  合计: 完工{total_completed} 合格{total_qualified} 废品{total_defective} 工时{total_time}分")

step("3.6", "质量检验")
r = api("GET", "/pm2/inspections")
if r.get("success"):
    qis = r.get("data", [])
    info(f"质检记录: {len(qis)} 条")
    for q in qis[:3]:
        info(f"  {q.get('inspection_no','')}: 来源={q.get('source_type','')} 检验员={q.get('inspector','')} 结果={q.get('status_label','')}")

step("3.7", "委外加工")
r = api("GET", "/pm2/outsourcing-orders?status=ALL")
if r.get("success"):
    outs = r.get("data", [])
    info(f"委外订单: {len(outs)} 张")
    for o in outs[:3]:
        info(f"  {o.get('order_no','')}: {o.get('material_name','')} 工序={o.get('process_name','')} 数量={o.get('ordered_qty',0)} ¥{o.get('total_fee',0):,} {o.get('status_label','')}")

step("3.8", "设备状态")
r = api("GET", "/pm2/equipments")
if r.get("success"):
    eqs = r.get("data", [])
    info(f"设备: {len(eqs)} 台")
    for e in eqs[:4]:
        info(f"  {e.get('equipment_code','')} {e.get('equipment_name','')}: OEE={e.get('oee',0)}% 可用率={e.get('availability',0)}% {e.get('status_label','')}")

# ============================================================
# 4. 交付阶段
# ============================================================
sep("4. 交付管理")

step("4.1", "销售出库")
r = api("GET", "/sales/sales_outbound/")
outs = r.get("data", []) if isinstance(r, dict) else (r if isinstance(r, list) else [])
info(f"销售出库单: {len(outs)} 张")
for o in outs[:3]:
    info(f"  #{o.get('id','')}: 状态={o.get('status','')}")

step("4.2", "发货单")
r = api("GET", "/sales/delivery_notes/")
dns = r.get("data", []) if isinstance(r, dict) else (r if isinstance(r, list) else [])
info(f"发货单: {len(dns)} 张")
for d in dns[:3]:
    info(f"  #{d.get('id','')}: 状态={d.get('status','')}")

step("4.3", "销售订单")
r = api("GET", "/sales/sales_orders/")
sos = r.get("data") if isinstance(r, dict) else r
if sos is None: sos = []
if not isinstance(sos, list): sos = []
info(f"销售订单: {len(sos)} 张")
for so in sos[:3]:
    info(f"  {so.get('order_no','')}: 状态={so.get('status','')} 金额=¥{so.get('total_amount',0)}")

# ============================================================
# 5. 财务阶段
# ============================================================
sep("5. 财务管理")

step("5.1", "财务概览")
r = api("GET", "/fn2/overview")
if r.get("success"):
    d = r.get("data", {})
    info(f"财务数据概览: {json.dumps(d, ensure_ascii=False)[:200]}")
else:
    info(f"财务概览: {r.get('message','')}")

step("5.2", "收付款记录")
r = api("GET", "/sm/receipts")
receipts = r.get("data", []) if isinstance(r, dict) else r
if not isinstance(receipts, list): receipts = []
info(f"收款单: {len(receipts)} 张")
for rc in receipts[:3]:
    if isinstance(rc, dict):
        info(f"  #{rc.get('id','')}: 金额=¥{rc.get('amount',0)} 状态={rc.get('status','')}")

step("5.3", "应收账款")
r = api("GET", "/sm/receivables")
recs = r.get("data", []) if isinstance(r, dict) else r
if not isinstance(recs, list): recs = []
info(f"应收账款: {len(recs)} 条")
for rc in recs[:3]:
    if isinstance(rc, dict):
        info(f"  #{rc.get('id','')}: 金额=¥{rc.get('amount',0)} 状态={rc.get('status','')}")

step("5.4", "库存概览")
r = api("GET", "/inv2/overview")
d = r.get("data", {}) if isinstance(r, dict) else {}
if d:
    info(f"库存数据: {json.dumps(d, ensure_ascii=False)[:200]}")
else:
    info(f"库存概览: {r.get('message','') if isinstance(r,dict) else 'N/A'}")

step("5.5", "仓库管理")
r = api("GET", "/inv2/warehouses")
whs = r.get("data", []) if isinstance(r, dict) else r
if not isinstance(whs, list): whs = []
info(f"仓库: {len(whs)} 个")
for w in whs[:3]:
    if isinstance(w, dict):
        info(f"  {w.get('code','')}: {w.get('name','')}")

# ============================================================
# 汇总
# ============================================================
sep("流程汇总")

r = api("GET", "/pm2/overview")
if r.get("success"):
    d = r["data"]
    print(f"""
  广州机器人项目全流程数据汇总:
  ────────────────────────────────────
  生产计划:    {d.get('plan_count',0)} 张
  MRP运算:     {d.get('mrp_count',0)} 批
  生产工单:    {d.get('active_work_orders',0)} 张活跃
  工艺路线:    {d.get('routing_count',0)} 条
  派工单:      {d.get('dispatch_count',0)} 张
  报工单:      {d.get('work_report_count',0)} 张
  委外订单:    {d.get('outsourcing_count',0)} 张
  设备:        {d.get('equipment_count',0)} 台
  ────────────────────────────────────
  系统地址:    http://localhost:8620
  用户名:      超级臭屁
  角色:        超级管理员
""")
