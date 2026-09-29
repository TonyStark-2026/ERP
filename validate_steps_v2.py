# -*- coding: utf-8 -*-
"""补全版 Step B1(精确) + C(语法) + D1(修复账号) + D6(详情) + E(跨网卡)"""
import urllib.request
import urllib.error
import json
import time
import re
import gzip
import sys
import os
import subprocess

TEMP_DIR = os.environ.get('TEMP', os.path.dirname(os.path.abspath(__file__)))
HTML_SNAPSHOT = os.path.join(TEMP_DIR, 'homepage_snapshot.html')
JS_SNAPSHOT = os.path.join(TEMP_DIR, 'inline_scripts.js')

# ========= 先下载首页 =========
print("=" * 70)
print("重新下载首页 HTML (保证 snapshot 最新)")
print("=" * 70)
req = urllib.request.Request('http://127.0.0.1:8000/', headers={'Accept-Encoding': 'gzip, deflate, br'})
with urllib.request.urlopen(req, timeout=10) as resp:
    raw_data = resp.read()
    encoding = resp.headers.get('Content-Encoding', '')
    if encoding == 'gzip':
        html = gzip.decompress(raw_data).decode('utf-8', errors='replace')
    else:
        html = raw_data.decode('utf-8', errors='replace')
    print(f"下载成功: {len(raw_data)} bytes (gzip={encoding=='gzip'})")
with open(HTML_SNAPSHOT, 'w', encoding='utf-8') as f:
    f.write(html)

# ========= Step B1 精确版 =========
print()
print("=" * 70)
print("Step B1 精确版: 检查 apiBase / authHeaders 声明")
print("=" * 70)
# 严格模式：const apiBase = '/api/v1' 直接字面量
b1_direct = re.search(r"""const\s+apiBase\s*=\s*['"]\/api\/v1['"]""", html)
# 间接模式：const API_BASE = '/api/v1'; const apiBase = API_BASE;
b1_api_base_lit = re.search(r"""const\s+API_BASE\s*=\s*['"]\/api\/v1['"]""", html)
b1_apibase_assign = re.search(r'const\s+apiBase\s*=\s*API_BASE\b', html)
b1_indirect_ok = bool(b1_api_base_lit and b1_apibase_assign)

auth_headers = re.search(r'const\s+authHeaders\s*=\s*\{', html)

print(f"B1 直接声明 const apiBase = '/api/v1'?        {'YES' if b1_direct else 'NO'}")
if b1_direct:
    print(f"   片段: {b1_direct.group(0)}")
print(f"B1 间接 const API_BASE = '/api/v1'?             {'YES' if b1_api_base_lit else 'NO'}")
if b1_api_base_lit:
    s = max(0, b1_api_base_lit.start()-5); e = min(len(html), b1_api_base_lit.end()+20)
    print(f"   片段: ...{html[s:e]}...")
print(f"B1 兼容声明 const apiBase = API_BASE?            {'YES' if b1_apibase_assign else 'NO'}")
if b1_apibase_assign:
    s = max(0, b1_apibase_assign.start()-5); e = min(len(html), b1_apibase_assign.end()+10)
    print(f"   片段: ...{html[s:e]}...")
print(f"B1 (结论) apiBase == '/api/v1' (直接或间接)?     {'YES' if (b1_direct or b1_indirect_ok) else 'NO'}")

print(f"B1 const authHeaders 对象声明存在?               {'YES' if auth_headers else 'NO'}")
if auth_headers:
    s = max(0, auth_headers.start()-5); e = min(len(html), auth_headers.end()+120)
    block = html[s:e].replace('\n', ' ').replace('  ', ' ')
    print(f"   片段: ...{block[:200]}...")

# ========= Step C 语法检查 =========
print()
print("=" * 70)
print("Step C: 语法 parse + Reference 检查 (使用 py_mini_racer)")
print("=" * 70)
scripts = []
for m in re.finditer(r'<script([^>]*)>([\s\S]*?)</script>', html, re.IGNORECASE):
    attrs = m.group(1)
    body = m.group(2).strip()
    if not body or re.search(r"""\bsrc\s*=""", attrs, re.IGNORECASE):
        continue
    scripts.append(body)
combined_js = "\n// ---- SCRIPT BOUNDARY ----\n".join(scripts)
print(f"[INFO] 提取 {len(scripts)} 个内联 script, 共 {len(combined_js)} 字符")
with open(JS_SNAPSHOT, 'w', encoding='utf-8') as f:
    f.write(combined_js)

syntax_error = None
ref_apiBase = 'unknown'
ref_authHeaders = 'unknown'
sim_result = None

# 方案 A: 尝试系统 node (完整路径查找)
node_path = None
for candidate in [
    r'C:\Program Files\nodejs\node.exe',
    r'C:\Program Files (x86)\nodejs\node.exe',
    os.path.expandvars(r'%APPDATA%\npm\node.cmd'),
]:
    if os.path.exists(candidate):
        node_path = candidate
        break
if not node_path:
    # 尝试 where
    try:
        r = subprocess.run(['where', 'node'], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            lines = [l.strip() for l in r.stdout.splitlines() if l.strip()]
            if lines:
                node_path = lines[0]
    except Exception:
        pass

parser_name = None
if node_path:
    parser_name = f"Node ({node_path})"
    print(f"[INFO] 找到 node.exe: {node_path}")
    # 语法检查
    r = subprocess.run([node_path, '--check', JS_SNAPSHOT], capture_output=True, text=True, timeout=20)
    if r.returncode == 0:
        syntax_error = False
        print("[PASS] node --check: 无 SyntaxError")
    else:
        syntax_error = True
        print("[FAIL] SyntaxError 存在:")
        for ln in r.stderr.splitlines()[:25]:
            print("   >", ln)
    # Reference check: 提取声明
    decls = []
    for line in combined_js.splitlines():
        s = line.strip()
        if s.startswith(('const API_BASE', 'const apiBase', 'const authHeaders',
                         'let API_BASE', 'let apiBase', 'let authHeaders',
                         'var API_BASE', 'var apiBase', 'var authHeaders')):
            decls.append(s.rstrip(';') + ';')
            if len(decls) >= 20: break
    probe = "\n".join(decls) + "\n"
    probe += "console.log(JSON.stringify({apiBase: String(typeof apiBase)+'='+String(apiBase), authHeaders: typeof authHeaders, API_BASE: String(typeof API_BASE)+'='+String(API_BASE)}));\n"
    probe_path = JS_SNAPSHOT + '.probe.js'
    with open(probe_path, 'w', encoding='utf-8') as f:
        f.write(probe)
    r2 = subprocess.run([node_path, probe_path], capture_output=True, text=True, timeout=10)
    if r2.returncode == 0:
        try:
            obj = json.loads(r2.stdout.strip().splitlines()[-1])
            print(f"[INFO] Reference 探针: {json.dumps(obj, ensure_ascii=False)}")
            ref_apiBase = 'NO' if (obj.get('apiBase','').startswith('string=') or obj.get('apiBase','').endswith('/api/v1')) else 'YES'
            # 更严格: 没有 ReferenceError 抛出来且不是 undefined 就算 NO（无错）
            if obj.get('apiBase','').startswith('undefined'): ref_apiBase = 'YES'
            if obj.get('authHeaders') == 'undefined': ref_authHeaders = 'YES'
            else: ref_authHeaders = 'NO'
            if obj.get('apiBase','').startswith(('string=','number=')) and not obj.get('apiBase','').startswith('string=undefined'):
                ref_apiBase = 'NO'
        except Exception as e:
            print(f"[WARN] 探针解析失败: {e}, out={r2.stdout[:200]}")
    else:
        print(f"[FAIL] 探针出错: {r2.stderr[:500]}")
        if 'ReferenceError' in r2.stderr:
            if 'apiBase' in r2.stderr.lower(): ref_apiBase = 'YES'
            if 'authHeaders' in r2.stderr.lower(): ref_authHeaders = 'YES'

    # 伪 DOM 模拟
    print()
    print("--- C.ext: 伪 DOM 模拟 loadModule('dashboard') 按钮高亮 ---")
    pseudo = r"""
const __fakeButtons = [
  { dataset: { module: 'dashboard' }, classList: { add(){}, remove(){} }, _hl:false, _rm:[] },
  { dataset: { module: 'materials' }, classList: { add(){}, remove(){} }, _hl:false, _rm:[] },
  { dataset: { module: 'plan' },      classList: { add(){}, remove(){} }, _hl:false, _rm:[] },
  { dataset: { module: 'production' },classList: { add(){}, remove(){} }, _hl:false, _rm:[] },
  { dataset: { module: 'procurement' },classList:{ add(){}, remove(){} }, _hl:false, _rm:[] },
  { dataset: { module: 'finance' },   classList: { add(){}, remove(){} }, _hl:false, _rm:[] },
  { dataset: { module: 'report' },    classList: { add(){}, remove(){} }, _hl:false, _rm:[] },
  { dataset: { module: 'system' },    classList: { add(){}, remove(){} }, _hl:false, _rm:[] },
];
__fakeButtons.forEach(b => {
  b.classList.add = function(c){ if (c==='active') b._hl = true; };
  b.classList.remove = function(c){ b._rm.push(c); };
  b.classList.contains = function(c){ return c==='active' ? b._hl : false; };
});
const __sidebar = { querySelectorAll: () => __fakeButtons };
const __content = { innerHTML: '' };
const document = {
  getElementById: function(id){
    if (id === 'sidebar-menu' || id==='sidebar') return __sidebar;
    if (id === 'content' || id==='main-content' || id==='module-content' || id==='app-content') return __content;
    return null;
  },
  querySelector: (sel) => null,
  querySelectorAll: (sel) => [],
  body: { innerHTML: '' },
  addEventListener: () => {},
  createElement: () => ({ innerHTML:'', appendChild(){}, classList:{add(){},remove(){},contains(){return false}}, style:{}, dataset:{} }),
};
const window = { addEventListener: () => {}, location: { hash: '', href: '', pathname:'/' }, localStorage: {getItem:()=>null,setItem(){},removeItem(){}} };
const localStorage = window.localStorage;
const sessionStorage = localStorage;
const fetch = async () => ({ ok: true, status:200, json: async () => ({ success: true, data: {} }), text: async () => '<div>mock</div>' });
const console = { log(){}, warn(){}, error(){}, info(){} };
const $ = () => ({ on(){}, off(){}, click(){}, collapse(){}, addClass(){}, removeClass(){}, tab(){} });
$.ajax = () => Promise.resolve({});
const bootstrap = { Modal: class { show(){} hide(){}}, Tab: class { show(){} } };
const Chart = class { constructor(){} destroy(){} update(){} };
const echarts = { init: () => ({ setOption(){}, dispose(){}, resize(){}, off(){} }) };
const toastr = { success(){}, error(){}, warning(){}, info(){} };
const Swal = { fire: () => Promise.resolve({ isConfirmed: true, value:'' }), mixin: () => Swal };
const hljs = { highlightElement(){} };
const QRCode = class { constructor(){} makeCode(){} clear(){} };
const jsQR = () => null;
window.addEventListener = () => {};
document.addEventListener = () => {};
"""
    sim = pseudo + "\n" + combined_js + "\n"
    sim += r"""
(async () => {
  try {
    // 执行 loadModule('dashboard')
    await loadModule('dashboard');
    const out = __fakeButtons.map(b => ({ module: b.dataset.module, active: b._hl, removed: b._rm }));
    process.stdout.write('SIMRESULT=' + JSON.stringify({ok:true, dash: out[0].active, states: out}) + '\n');
  } catch (e) {
    process.stdout.write('SIMRESULT=' + JSON.stringify({ok:false, err: String(e), stack: String(e && e.stack || '').slice(0,500)}) + '\n');
  }
})();
"""
    simp = JS_SNAPSHOT + '.sim.js'
    with open(simp, 'w', encoding='utf-8') as f:
        f.write(sim)
    rs = subprocess.run([node_path, simp], capture_output=True, text=True, timeout=20)
    out = rs.stdout + rs.stderr
    m = re.search(r'SIMRESULT=(\{.*\})', out)
    if m:
        try:
            sim_result = json.loads(m.group(1))
            print(f"  模拟结果: {json.dumps(sim_result, ensure_ascii=False, indent=2)}")
            if sim_result.get('ok') and sim_result.get('dash'):
                print("[PASS] dashboard 按钮高亮 (active class 添加成功)")
            elif sim_result.get('ok'):
                print("[WARN] 模拟无异常但 dashboard 未高亮 active，需人工复核")
            else:
                print(f"[WARN] 模拟抛出异常: {sim_result.get('err')}")
                if sim_result.get('stack'):
                    print("       stack 前400字符:", sim_result['stack'][:400])
        except Exception as pe:
            print(f"[WARN] 模拟结果解析失败: {pe}")
            print("       RAW:", out[:500])
    else:
        print("[WARN] 未捕获 SIMRESULT，输出:")
        print((rs.stdout[:300] + " |STDERR| " + rs.stderr[:300]))

else:
    # 方案 B: py_mini_racer
    print("[INFO] node 未找到，回退到 py_mini_racer")
    try:
        from py_mini_racer import MiniRacer
        parser_name = "py_mini_racer"
        ctx = MiniRacer()
        try:
            ctx.execute(combined_js)
            syntax_error = False
            print("[PASS] py_mini_racer 执行无 SyntaxError")
        except Exception as se:
            syntax_error = True
            print(f"[FAIL] SyntaxError: {se}")
        try:
            a = ctx.eval("typeof apiBase + ':' + String(apiBase)")
            h = ctx.eval("typeof authHeaders")
            print(f"[INFO] typeof apiBase={a}, typeof authHeaders={h}")
            ref_apiBase = 'NO' if (a and not a.startswith('undefined:')) else 'YES'
            ref_authHeaders = 'NO' if (h and h != 'undefined') else 'YES'
        except Exception as ree:
            print(f"[FAIL] Reference 检查抛错: {ree}")
            if 'apiBase' in str(ree).lower(): ref_apiBase = 'YES'
            if 'authHeaders' in str(ree).lower(): ref_authHeaders = 'YES'
    except ImportError:
        parser_name = None
        print("[FAIL] py_mini_racer 也未安装，无法做语法/引用检查")

print()
print("[Step C 汇总]")
print(f"  使用解析器: {parser_name or 'NONE (无法验证)'}")
print(f"  SyntaxError = {'YES' if syntax_error is True else 'NO' if syntax_error is False else '未知(未执行)'}")
print(f"  ReferenceError(apiBase)     = {ref_apiBase.upper()}")
print(f"  ReferenceError(authHeaders) = {ref_authHeaders.upper()}")


# ========= Step D + E (修复版) =========
print()
print("=" * 70)
print("Step D: 全链路 API 验证 (登录凭据修复为 超级臭屁/123456)")
print("=" * 70)

def do_req(method, url, data=None, token=None, timeout=10):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    body = json.dumps(data).encode('utf-8') if data is not None else None
    try:
        req = urllib.request.Request(url, data=body, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            rb = resp.read()
            ct = resp.headers.get('Content-Type','') or ''
            try:
                if 'json' in ct.lower() or rb[:1] in (b'{', b'['):
                    j = json.loads(rb.decode('utf-8', errors='replace'))
                else:
                    j = {'_raw': rb.decode('utf-8', errors='replace')[:200]}
            except Exception:
                j = {'_raw_head': rb[:100]}
            return resp.status, j, None
    except urllib.error.HTTPError as he:
        rb = he.read()
        try:
            j = json.loads(rb.decode('utf-8', errors='replace'))
        except:
            j = {'_raw': rb.decode('utf-8', errors='replace')[:200]}
        return he.code, j, str(he)
    except Exception as e:
        return None, None, str(e)

LOGIN = {'username': '超级臭屁', 'password': '123456'}
st, sj, err = do_req('POST', 'http://127.0.0.1:8000/api/v1/auth/login', LOGIN)
print(f"D1. POST /api/v1/auth/login  (超级臭屁/123456)")
print(f"    状态码: {st}, 错误: {err}")
token = None
login_ok = False
if isinstance(sj, dict):
    success = sj.get('success')
    data = sj.get('data') or {}
    token = data.get('token') or data.get('access_token') or sj.get('token')
    login_ok = (st in (200,201) and (success is True or token))
    print(f"    success={success}, token 存在={bool(token)}")
    print(f"    body 预览: {json.dumps(sj, ensure_ascii=False)[:400]}")
print(f"    结果: {'PASS' if login_ok else 'FAIL'}")

def check(label, method, sub):
    url = 'http://127.0.0.1:8000/api/v1' + sub
    st, sj, err = do_req(method, url, token=token)
    code_ok = isinstance(st, int) and 200 <= st < 300
    sf = sj.get('success') if isinstance(sj, dict) else None
    ok = code_ok and (sf is True)
    print(f"{label}. {method} {sub}")
    print(f"    状态码: {st}, err: {err}")
    if isinstance(sj, dict):
        preview = json.dumps(sj, ensure_ascii=False)[:400]
        if st == 500:
            print(f"    [500 详情] message={sj.get('message')}, error_code={sj.get('error_code')}")
        print(f"    success={sf}, keys={list(sj.keys())[:8]}")
        print(f"    body={preview}")
    else:
        print(f"    body={str(sj)[:200]}")
    print(f"    结果: {'PASS' if ok else 'FAIL'}")
    return ok

print()
d2 = check("D2", "GET", "/materials/product-catalog")
print()
d3 = check("D3", "GET", "/plan/forecast-orders")
print()
d4 = check("D4", "GET", "/procurement/purchase-requests")
print()
d5 = check("D5", "GET", "/materials/")
print()
d6 = check("D6", "GET", "/finance/reports/balance-sheet")

print()
print(f"[Step D 汇总]  D1={'PASS' if login_ok else 'FAIL'}  D2={'PASS' if d2 else 'FAIL'}  D3={'PASS' if d3 else 'FAIL'}  D4={'PASS' if d4 else 'FAIL'}  D5={'PASS' if d5 else 'FAIL'}  D6={'PASS' if d6 else 'FAIL'}")

# Step E
print()
print("=" * 70)
print("Step E: 跨网卡登录 (192.168.3.93:8000) 证明手机端接口可达")
print("=" * 70)
st, sj, err = do_req('POST', 'http://192.168.3.93:8000/api/v1/auth/login', LOGIN, timeout=8)
print(f"E1. POST http://192.168.3.93:8000/api/v1/auth/login")
print(f"    状态码: {st}, 错误: {err}")
ok = False
if isinstance(sj, dict):
    sf = sj.get('success')
    data = sj.get('data') or {}
    tk = data.get('token') or data.get('access_token') or sj.get('token')
    ok = (isinstance(st,int) and 200<=st<300 and (sf is True or tk))
    print(f"    success={sf}, token 存在={bool(tk)}")
    print(f"    body 预览: {json.dumps(sj, ensure_ascii=False)[:400]}")
elif sj is not None:
    print(f"    body(non-dict): {str(sj)[:200]}")
print(f"    结论: {'PASS - 同WiFi手机接口可达 (跨网卡登录成功)' if ok else 'FAIL - 接口不可达或登录失败'}")

print()
print("==== 验证完毕 ====")
