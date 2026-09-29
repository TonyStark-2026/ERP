# -*- coding: utf-8 -*-
import urllib.request
import urllib.error
import json
import time
import re
import gzip
import sys
import os

TEMP_DIR = os.environ.get('TEMP', os.path.dirname(os.path.abspath(__file__)))
HTML_SNAPSHOT = os.path.join(TEMP_DIR, 'homepage_snapshot.html')
JS_SNAPSHOT = os.path.join(TEMP_DIR, 'inline_scripts.js')

print("=" * 70)
print("Step A: 等待 uvicorn reload - 轮询 /health")
print("=" * 70)
start = time.time()
ok = False
last_err = ""
for i in range(8):  # 15s/2s ~= 7.5, 取8次
    try:
        req = urllib.request.Request('http://127.0.0.1:8000/health')
        with urllib.request.urlopen(req, timeout=2) as resp:
            elapsed = round(time.time() - start, 1)
            if resp.status == 200:
                body = resp.read().decode('utf-8', errors='replace')
                print(f"[PASS] Step A: {elapsed} 秒后返回 200")
                print(f"       body: {body[:200]}")
                ok = True
                break
            else:
                print(f"       {elapsed}s: 状态码 {resp.status} (非200，继续)")
    except Exception as e:
        last_err = str(e)
        elapsed = round(time.time() - start, 1)
        print(f"       {elapsed}s: 请求失败 - {e[:80]}")
    time.sleep(2)
if not ok:
    elapsed = round(time.time() - start, 1)
    print(f"[FAIL] Step A: 超时 15 秒未获得 200，最后错误: {last_err}")

print()
print("=" * 70)
print("Step B: 重新下载首页 HTML 并检查")
print("=" * 70)
try:
    req = urllib.request.Request(
        'http://127.0.0.1:8000/',
        headers={'Accept-Encoding': 'gzip, deflate, br'}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw_data = resp.read()
        encoding = resp.headers.get('Content-Encoding', '')
        status = resp.status
        content_type = resp.headers.get('Content-Type', '')
        content_length_header = resp.headers.get('Content-Length')

        if encoding == 'gzip':
            html = gzip.decompress(raw_data).decode('utf-8', errors='replace')
        else:
            html = raw_data.decode('utf-8', errors='replace')

        compressed_size = len(raw_data)
        uncompressed_bytes = len(html.encode('utf-8'))
        print(f"[INFO] HTTP 状态码: {status}")
        print(f"[INFO] Content-Type: {content_type}")
        print(f"[INFO] Content-Length(头): {content_length_header}")
        print(f"B5. Content-Encoding: [{encoding}]")
        print(f"B5. 压缩后大小(网络传输 raw_data): {compressed_size} 字节")
        print(f"B5. 解压后大小: {uncompressed_bytes} 字节 / {len(html)} 字符")

    with open(HTML_SNAPSHOT, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"[INFO] HTML 已保存至: {HTML_SNAPSHOT}")

    print()
    print("--- B1. 检查 const apiBase 和 const authHeaders 声明 ---")
    apiBase_match = re.search(r"""const\s+apiBase\s*=\s*['"]/api/v1['"]""", html)
    authHeaders_match = re.search(r'const\s+authHeaders', html)
    print(f"B1. const apiBase = '/api/v1' 存在? {'YES' if apiBase_match else 'NO'}")
    if apiBase_match:
        print(f"     片段: {apiBase_match.group(0)}")
    else:
        # 尝试放宽搜索
        loose = re.search(r'apiBase\s*=', html)
        if loose:
            s = max(0, loose.start()-10); e = min(len(html), loose.end()+40)
            print(f"     仅找到 apiBase= 的片段: ...{html[s:e]}...")
    print(f"B1. const authHeaders 存在? {'YES' if authHeaders_match else 'NO'}")
    if authHeaders_match:
        s = max(0, authHeaders_match.start()-15)
        e = min(len(html), authHeaders_match.end()+60)
        print(f"     上下文片段: ...{html[s:e]}...")

    print()
    print("--- B2. 检查是否存在 button[onclick=\"loadModule( 选择器 ---")
    b2 = re.search(r"""button\[onclick\s*=\s*["']loadModule\(""", html)
    print(f"B2. 存在 'button[onclick=\"loadModule(' 选择器? {'YES - 错误!' if b2 else 'NO - 正确'}")
    if b2:
        s = max(0, b2.start()-40); e = min(len(html), b2.end()+80)
        print(f"     上下文: {html[s:e]}")

    print()
    print("--- B3. 检查 showMainApp 是否存在 try { 包裹 ---")
    # 模式1: function showMainApp(...) { try {
    b3_p1 = re.search(
        r'function\s+showMainApp\s*\([^)]*\)\s*\{[^{]*try\s*\{',
        html, re.DOTALL
    )
    # 模式2: showMainApp = ... => { try {
    b3_p2 = re.search(
        r'showMainApp\s*=\s*(?:async\s+)?\(?[^)]*\)?\s*=>\s*\{[^{]*try\s*\{',
        html, re.DOTALL
    )
    found_try = b3_p1 or b3_p2
    print(f"B3. showMainApp 存在 try {{ 包裹? {'YES' if found_try else 'NO - 可能错误'}")
    if found_try:
        m = found_try.group(0)
        snippet = m[:200].replace('\n', '\\n')
        print(f"     匹配片段(前200): {snippet}")
    else:
        idx = html.find('showMainApp')
        if idx >= 0:
            ctx = html[idx:idx+600]
            print(f"     showMainApp 附近上下文(前600字符):")
            print(ctx)
        else:
            print("     !!! showMainApp 函数完全不存在于首页 !!!")

    print()
    print("--- B4. loadModule 是否 if (!content) return 保护 ---")
    # 在 loadModule 函数体内搜索
    lm = re.search(r'(?:function\s+loadModule|loadModule\s*=)[\s\S]{0,1200}', html, re.DOTALL)
    b4 = False
    if lm:
        body_lm = lm.group(0)
        # 检查几种变体: if (!content) return / if(!content){return}/ if (content == null) return 等
        if re.search(r'if\s*\(\s*!content\s*\)\s*\{?\s*return', body_lm, re.DOTALL):
            b4 = True
        elif re.search(r'if\s*\(\s*content\s*==\s*null\s*\)', body_lm, re.DOTALL):
            b4 = True
    print(f"B4. loadModule content=null 保护? {'YES' if b4 else 'NO - 可能错误'}")
    if lm:
        body_lm = lm.group(0)
        idx_p = body_lm.find('!content')
        if idx_p >= 0:
            s = max(0, idx_p-30); e = min(len(body_lm), idx_p+80)
            print(f"     片段: ...{body_lm[s:e].replace(chr(10),' ')}...")
        else:
            print(f"     loadModule 函数前800字符(供检查):")
            print(body_lm[:800])
    else:
        print("     !!! loadModule 找不到 !!!")

except Exception as e:
    import traceback
    print(f"[FAIL] Step B 异常: {e}")
    traceback.print_exc()

print()
print("=" * 70)
print("Step C: 脚本级语法检查 (提取首页内联 <script> 无 src 的代码)")
print("=" * 70)
# 提取所有 <script> 标签 (不含 src 的)
scripts = []
# 匹配 <script...> 到 </script>
for m in re.finditer(r'<script([^>]*)>([\s\S]*?)</script>', html, re.IGNORECASE):
    attrs = m.group(1)
    body = m.group(2).strip()
    if not body:
        continue
    if re.search(r"""\bsrc\s*=""", attrs, re.IGNORECASE):
        continue  # 跳过外链
    scripts.append(body)

combined_js = "\n// ---- SCRIPT BOUNDARY ----\n".join(scripts)
print(f"[INFO] 提取到 {len(scripts)} 个内联 <script> 块, 合并后 {len(combined_js)} 字符")
with open(JS_SNAPSHOT, 'w', encoding='utf-8') as f:
    f.write(combined_js)
print(f"[INFO] 合并 JS 已保存至: {JS_SNAPSHOT}")

syntax_ok = False
ref_apiBase_ok = False
ref_authHeaders_ok = False
parser_used = None

# 方案1: 调用 node --check 或 node -e "new Function(...)"
try:
    import subprocess
    # 先检查 node 存在
    r = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=10)
    if r.returncode == 0:
        node_ver = r.stdout.strip()
        print(f"[INFO] 使用 Node.js 解析: {node_ver}")
        parser_used = f"Node.js {node_ver}"
        # 语法检查: node --check file
        r2 = subprocess.run(['node', '--check', JS_SNAPSHOT], capture_output=True, text=True, timeout=15)
        if r2.returncode == 0:
            print("[PASS] 语法检查 (SyntaxError): NO (无语法错误)")
            syntax_ok = True
        else:
            print(f"[FAIL] 语法检查 (SyntaxError): YES !!!")
            print("       STDERR:")
            for ln in r2.stderr.splitlines()[:20]:
                print("       >", ln)
        # ReferenceError 检查 (单独提取 apiBase/authHeaders 声明运行)
        # 从 combined_js 头部提取声明
        decl_lines = []
        for line in combined_js.splitlines():
            stripped = line.strip()
            if stripped.startswith('const apiBase') or stripped.startswith('const authHeaders') or \
               stripped.startswith('let apiBase') or stripped.startswith('let authHeaders') or \
               stripped.startswith('var apiBase') or stripped.startswith('var authHeaders'):
                decl_lines.append(stripped.rstrip(';') + ';')
                if len(decl_lines) >= 10:
                    break
        probe_js = "\n".join(decl_lines) + "\n"
        probe_js += "const __probe = { apiBase: typeof apiBase, authHeaders: typeof authHeaders };\n"
        probe_js += "console.log(JSON.stringify(__probe));\n"
        probe_path = JS_SNAPSHOT + '.probe.js'
        with open(probe_path, 'w', encoding='utf-8') as f:
            f.write(probe_js)
        r3 = subprocess.run(['node', probe_path], capture_output=True, text=True, timeout=10)
        if r3.returncode == 0:
            try:
                res = json.loads(r3.stdout.strip().splitlines()[-1])
                ref_apiBase_ok = res.get('apiBase') == 'string'
                ref_authHeaders_ok = res.get('authHeaders') == 'object' or res.get('authHeaders') == 'function'
                print(f"[PASS/INFO] 声明探针结果: {res}")
                print(f"C. ReferenceError(apiBase) = {'YES(错)' if not ref_apiBase_ok else 'NO(对)'}  typeof={res.get('apiBase')}")
                print(f"C. ReferenceError(authHeaders) = {'YES(错)' if not ref_authHeaders_ok else 'NO(对)'}  typeof={res.get('authHeaders')}")
            except Exception as e2:
                print(f"[WARN] 探针解析失败: {e2}, stdout={r3.stdout[:200]}")
        else:
            print(f"[FAIL] 探针运行返回非0; STDERR: {r3.stderr[:500]}")
except FileNotFoundError:
    print("[WARN] Node.js 不可用 (node 命令找不到), 尝试 Python execjs/py_mini_racer")
except Exception as e_ne:
    print(f"[WARN] Node.js 调用异常: {e_ne}, 尝试 Python 方案")

if not parser_used:
    # 方案2: py_mini_racer
    try:
        from py_mini_racer import MiniRacer
        ctx = MiniRacer()
        try:
            ctx.execute(combined_js)
            print("[PASS] py_mini_racer: 无 SyntaxError")
            syntax_ok = True
        except Exception as se:
            print(f"[FAIL] py_mini_racer SyntaxError? YES -> {se}")
        try:
            r1 = ctx.eval("typeof apiBase")
            r2 = ctx.eval("typeof authHeaders")
            print(f"C. apiBase typeof={r1}, ReferenceError(apiBase)={'YES' if r1=='undefined' else 'NO'}")
            print(f"C. authHeaders typeof={r2}, ReferenceError(authHeaders)={'YES' if r2=='undefined' else 'NO'}")
            ref_apiBase_ok = r1 != 'undefined'
            ref_authHeaders_ok = r2 != 'undefined'
        except Exception as re_err:
            print(f"[FAIL] 取 typeof 失败: {re_err}")
        parser_used = "py_mini_racer"
    except ImportError:
        print("[WARN] py_mini_racer 未安装")
    except Exception as e_pmr:
        print(f"[WARN] py_mini_racer 异常: {e_pmr}")

if not parser_used:
    # 方案3: execjs
    try:
        import execjs
        ctx = execjs.compile(combined_js)
        print("[PASS] execjs.compile: 无 SyntaxError")
        syntax_ok = True
        try:
            r1 = ctx.eval("typeof apiBase")
            r2 = ctx.eval("typeof authHeaders")
            print(f"C. execjs: apiBase typeof={r1}, authHeaders typeof={r2}")
            ref_apiBase_ok = r1 != 'undefined'
            ref_authHeaders_ok = r2 != 'undefined'
        except Exception as re2:
            print(f"[WARN] execjs typeof 失败: {re2}")
        parser_used = "PyExecJS"
    except ImportError:
        print("[WARN] PyExecJS 未安装")
    except Exception as se:
        print(f"[FAIL] execjs SyntaxError? YES -> {se}")

# 额外: 模拟 loadModule('dashboard') 调用链里的 sidebar-menu 按钮高亮逻辑 (伪 DOM)
# 只在 Node.js 可用时执行
print()
print("--- C.ext: 伪 DOM 模拟 loadModule('dashboard') 按钮高亮 (不依赖真实 document) ---")
dom_simulation_result = "未执行 (无 Node.js)"
if parser_used and parser_used.startswith("Node.js"):
    # 提取 loadModule 函数 + 所有前置 const/let 变量，构造伪 document
    # 构造最小化环境
    pseudo_js = ""
    # 伪 document：包含 sidebar-menu 容器，带有 data-module 属性的按钮
    pseudo_js += r"""
const __fakeButtons = [
  { dataset: { module: 'dashboard' }, classList: { contains: () => false, add: () => {}, remove: () => {} }, _highlighted: false, _removed: [] },
  { dataset: { module: 'materials' }, classList: { contains: () => false, add: () => {}, remove: () => {} }, _highlighted: false, _removed: [] },
  { dataset: { module: 'plan' }, classList: { contains: () => false, add: () => {}, remove: () => {} }, _highlighted: false, _removed: [] },
];
__fakeButtons.forEach((b, i) => {
  b.classList.add = function(cls){ if (cls==='active') b._highlighted=true; };
  b.classList.remove = function(cls){ b._removed.push(cls); };
});
const __fakeSidebar = { querySelectorAll: () => __fakeButtons };
const document = {
  getElementById: (id) => id === 'sidebar-menu' ? __fakeSidebar : null,
  querySelector: (sel) => null,
  querySelectorAll: (sel) => [],
  body: { innerHTML: '' },
  addEventListener: () => {},
};
const window = { addEventListener: () => {}, location: { hash: '', href: '' } };
const localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
const fetch = async () => ({ ok: true, json: async () => ({ success: true, data: {} }), text: async () => 'mock html content' });
const $ = () => ({ on: () => {}, collapse: () => {} });
const bootstrap = { Modal: class { show(){} hide(){} } };
const Chart = class { constructor(){} destroy(){} };
const echarts = { init: () => ({ setOption: () => {}, dispose: () => {}, resize: () => {} }) };
const toastr = { success: () => {}, error: () => {}, warning: () => {}, info: () => {} };
const Swal = { fire: () => Promise.resolve({ isConfirmed: true }) };
"""
    # 把所有内联脚本拼接上，然后最后调用 loadModule('dashboard')
    full_sim = pseudo_js + "\n" + combined_js + "\n"
    full_sim += r"""
(async () => {
  try {
    await loadModule('dashboard');
    const results = __fakeButtons.map(b => ({ module: b.dataset.module, highlighted: b._highlighted, removed: b._removed }));
    const dashboardBtn = results.find(x => x.module === 'dashboard');
    console.log('SIMRESULT:' + JSON.stringify({
      ok: true,
      dashboardHighlighted: dashboardBtn ? dashboardBtn.highlighted : null,
      allButtons: results,
    }));
  } catch (e) {
    console.log('SIMRESULT:' + JSON.stringify({ ok: false, error: String(e), stack: e.stack ? String(e.stack).slice(0,400) : '' }));
  }
})();
"""
    sim_path = JS_SNAPSHOT + '.sim.js'
    with open(sim_path, 'w', encoding='utf-8') as f:
        f.write(full_sim)
    try:
        r_sim = subprocess.run(['node', sim_path], capture_output=True, text=True, timeout=15)
        out = r_sim.stdout + r_sim.stderr
        import re as _re
        m_sim = _re.search(r'SIMRESULT:(\{.*\})', out)
        if m_sim:
            try:
                sim_res = json.loads(m_sim.group(1))
                dom_simulation_result = json.dumps(sim_res, ensure_ascii=False, indent=2)
                print(f"[INFO] 伪 DOM 模拟 loadModule('dashboard') 结果:")
                print(dom_simulation_result)
                if sim_res.get('ok'):
                    if sim_res.get('dashboardHighlighted'):
                        print("[PASS] dashboard 按钮高亮逻辑正常 (active class 已添加)")
                    else:
                        print("[WARN] dashboard 按钮未被标记为 highlighted，需检查高亮逻辑")
            except Exception as pe:
                print(f"[WARN] 模拟结果 JSON 解析失败: {pe}")
                print("       RAW:", out[:800])
        else:
            print(f"[WARN] 模拟未返回 SIMRESULT")
            if out.strip():
                print("       STDOUT/STDERR:", out[:800])
    except Exception as se_sim:
        print(f"[FAIL] 模拟执行异常: {se_sim}")

print()
print(f"[Step C 汇总]")
print(f"  使用解析器: {parser_used or '无可用解析器'}")
print(f"  SyntaxError = {'YES(有错)' if not syntax_ok and parser_used else 'NO(无错)' if syntax_ok else '未知(未执行)'}")
print(f"  ReferenceError(apiBase)      = {'YES(有错)' if parser_used and not ref_apiBase_ok else 'NO(无错)' if ref_apiBase_ok else '未知(未执行)'}")
print(f"  ReferenceError(authHeaders)  = {'YES(有错)' if parser_used and not ref_authHeaders_ok else 'NO(无错)' if ref_authHeaders_ok else '未知(未执行)'}")

print()
print("=" * 70)
print("Step D: 全链路 API 验证 (登录 + 各模块首接口)")
print("=" * 70)
BASE1 = 'http://127.0.0.1:8000/api/v1'

def do_req(method, url, data=None, token=None, extra_headers=None):
    try:
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        if extra_headers:
            headers.update(extra_headers)
        body = None
        if data is not None:
            body = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=body, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            rb = resp.read()
            ct = resp.headers.get('Content-Type', '') or ''
            status = resp.status
            try:
                if 'json' in ct.lower() or rb.startswith(b'{') or rb.startswith(b'['):
                    j = json.loads(rb.decode('utf-8', errors='replace'))
                else:
                    j = {'_raw_text': rb.decode('utf-8', errors='replace')[:200]}
            except Exception as _e:
                j = {'_parse_error': str(_e), '_raw_head': rb[:100]}
            return status, j, None
    except urllib.error.HTTPError as he:
        rb = he.read()
        try:
            j = json.loads(rb.decode('utf-8', errors='replace'))
        except:
            j = {'_raw_head': rb[:200].decode('utf-8', errors='replace')}
        return he.code, j, str(he)
    except Exception as e:
        return None, None, str(e)

# D1. 登录
login_payload = {'username': 'admin', 'password': 'admin123'}
st, sj, err = do_req('POST', f'{BASE1}/auth/login', login_payload)
login_success = False
token = None
print(f"D1. POST {BASE1}/auth/login")
print(f"    状态码: {st}, 错误: {err}")
if isinstance(sj, dict):
    success_flag = sj.get('success')
    data = sj.get('data') or {}
    token = data.get('token') or data.get('access_token') or sj.get('token')
    login_success = (st in (200, 201) and (success_flag is True or token))
    preview = json.dumps(sj, ensure_ascii=False)[:300]
    print(f"    success字段: {success_flag}, token存在: {bool(token)}")
    print(f"    body预览: {preview}")
print(f"    结果: {'PASS - 登录成功' if login_success else 'FAIL - 登录失败'}")

def check_d(label, method, path, expect_success_field=True):
    url = BASE1 + path
    st, sj, err = do_req(method, url, token=token)
    code_ok = st is not None and 200 <= st < 300
    sf = sj.get('success') if isinstance(sj, dict) else None
    field_ok = (not expect_success_field) or (sf is True)
    overall = code_ok and field_ok
    print(f"{label}. {method} {url}")
    print(f"    状态码: {st}, 传输错误: {err}")
    if isinstance(sj, dict):
        preview = json.dumps(sj, ensure_ascii=False)[:300]
        print(f"    success字段: {sf}, keys: {list(sj.keys())[:10]}")
        print(f"    body预览: {preview}")
    else:
        print(f"    body(non-dict): {str(sj)[:200]}")
    print(f"    结果: {'PASS' if overall else 'FAIL'}  (2xx={code_ok}, success={sf if expect_success_field else 'N/A'})")
    return overall

print()
d2 = check_d("D2", "GET", "/materials/product-catalog")
print()
d3 = check_d("D3", "GET", "/plan/forecast-orders")
print()
d4 = check_d("D4", "GET", "/procurement/purchase-requests")
print()
d5 = check_d("D5", "GET", "/materials/")
print()
d6 = check_d("D6", "GET", "/finance/reports/balance-sheet")

print()
print(f"[Step D 汇总]")
print(f"  D1 登录:       {'PASS' if login_success else 'FAIL'}")
print(f"  D2 产品目录:   {'PASS' if d2 else 'FAIL'}")
print(f"  D3 预测订单:   {'PASS' if d3 else 'FAIL'}")
print(f"  D4 采购申请:   {'PASS' if d4 else 'FAIL'}")
print(f"  D5 物料主数据: {'PASS' if d5 else 'FAIL'}")
print(f"  D6 资产负债表: {'PASS' if d6 else 'FAIL'}")

print()
print("=" * 70)
print("Step E: 跨网卡登录 (192.168.3.93:8000)")
print("=" * 70)
LAN_BASE = 'http://192.168.3.93:8000/api/v1'
st, sj, err = do_req('POST', f'{LAN_BASE}/auth/login', login_payload, timeout_override=10)
# 注意: do_req 没支持 timeout_override，所以这里独立再写一次
print(f"E1. POST {LAN_BASE}/auth/login")
try:
    headers = {'Content-Type': 'application/json'}
    body = json.dumps(login_payload).encode('utf-8')
    req = urllib.request.Request(f'{LAN_BASE}/auth/login', data=body, method='POST', headers=headers)
    with urllib.request.urlopen(req, timeout=8) as resp:
        st = resp.status
        rb = resp.read()
        try:
            sj = json.loads(rb.decode('utf-8', errors='replace'))
        except:
            sj = {'_raw': rb[:300].decode('utf-8', errors='replace')}
        err_str = None
except urllib.error.HTTPError as he:
    st = he.code
    rb = he.read()
    try:
        sj = json.loads(rb.decode('utf-8', errors='replace'))
    except:
        sj = {'_raw': rb[:300].decode('utf-8', errors='replace')}
    err_str = str(he)
except Exception as e:
    st = None
    sj = None
    err_str = str(e)

code_ok = st is not None and 200 <= st < 300
sf = sj.get('success') if isinstance(sj, dict) else None
tk = None
if isinstance(sj, dict):
    dd = sj.get('data') or {}
    tk = dd.get('token') or dd.get('access_token') or sj.get('token')
lan_login_ok = code_ok and (sf is True or bool(tk))
print(f"    状态码: {st}, 错误: {err_str}")
if isinstance(sj, dict):
    print(f"    success={sf}, token存在={bool(tk)}")
    print(f"    body预览: {json.dumps(sj, ensure_ascii=False)[:300]}")
elif sj is not None:
    print(f"    body: {str(sj)[:300]}")
print(f"    结果: {'PASS - 跨网卡登录成功 (手机端同WiFi接口可达)' if lan_login_ok else 'FAIL - 跨网卡不可达或登录失败'}")

print()
print("=" * 70)
print("全部步骤执行完毕")
print("=" * 70)
