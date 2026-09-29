# -*- coding: utf-8 -*-
"""Step C/D/E 补全版，JS 语法检查三重兜底: node -> py_mini_racer -> cscript(JScript)"""
import urllib.request, urllib.error, json, re, gzip, os, sys, subprocess, tempfile

TEMP_DIR = tempfile.gettempdir()
HTML_SNAPSHOT = os.path.join(TEMP_DIR, 'homepage_snapshot.html')
JS_SNAPSHOT   = os.path.join(TEMP_DIR, 'inline_scripts.js')

html = None
# 下载首页 (用带 gzip 头的请求)
req = urllib.request.Request('http://127.0.0.1:8000/', headers={'Accept-Encoding':'gzip, deflate'})
with urllib.request.urlopen(req, timeout=10) as resp:
    raw = resp.read()
    enc = resp.headers.get('Content-Encoding','')
    content_length_net = len(raw)
    html = gzip.decompress(raw).decode('utf-8', errors='replace') if enc=='gzip' else raw.decode('utf-8', errors='replace')
print(f"[INFO] 首页下载成功: 网络传输 {content_length_net} bytes, gzip={enc=='gzip'}, HTML={len(html)} chars")
with open(HTML_SNAPSHOT, 'w', encoding='utf-8') as f: f.write(html)

# ================ Step B1 精确版 ================
print("\n"+"="*70)
print("Step B1 精确版: apiBase / authHeaders")
print("="*70)
b1_direct        = re.search(r"""const\s+apiBase\s*=\s*['"]/api/v1['"]""", html)
b1_api_base_lit  = re.search(r"""const\s+API_BASE\s*=\s*['"]/api/v1['"]""", html)
b1_apibase_assign= re.search(r'const\s+apiBase\s*=\s*API_BASE\b', html)
b1_indirect = bool(b1_api_base_lit and b1_apibase_assign)
auth_decl = re.search(r'const\s+authHeaders\s*=\s*\{', html)
print(f"B1 直接 const apiBase='/api/v1'?       {'YES' if b1_direct else 'NO'}")
if b1_direct: print("   片段:", b1_direct.group(0))
print(f"B1 声明 const API_BASE='/api/v1'?      {'YES' if b1_api_base_lit else 'NO'}")
if b1_api_base_lit:
    s=max(0,b1_api_base_lit.start()-4); e=min(len(html), b1_api_base_lit.end()+15)
    print("   片段:", html[s:e].replace('\n','\\n'))
print(f"B1 兼容 const apiBase=API_BASE?        {'YES' if b1_apibase_assign else 'NO'}")
if b1_apibase_assign:
    s=max(0,b1_apibase_assign.start()-4); e=min(len(html), b1_apibase_assign.end()+10)
    print("   片段:", html[s:e].replace('\n','\\n'))
print(f"B1 结论 apiBase=='/api/v1'(直/间接)?   {'YES' if (b1_direct or b1_indirect) else 'NO'}")
print(f"B1 const authHeaders = {{ ... 存在?    {'YES' if auth_decl else 'NO'}")
if auth_decl:
    s=max(0,auth_decl.start()-4); e=min(len(html), auth_decl.end()+150)
    block = html[s:e].replace('\n',' ')
    while '  ' in block: block = block.replace('  ',' ')
    print("   片段:", block[:200])

# ================ Step C 语法检查 ================
print("\n"+"="*70)
print("Step C: 脚本语法 parse / ReferenceError 检查")
print("="*70)
scripts = []
for m in re.finditer(r'<script([^>]*)>([\s\S]*?)</script>', html, re.IGNORECASE):
    if re.search(r"""\bsrc\s*=""", m.group(1), re.I): continue
    b = m.group(2).strip()
    if b: scripts.append(b)
combined_js = "\n".join(scripts)
print(f"[INFO] 提取 {len(scripts)} 个内联 script, 合计 {len(combined_js)} chars")
with open(JS_SNAPSHOT, 'w', encoding='utf-8') as f: f.write(combined_js)

parser_name = None
syntax_error = None  # True/False/None
ref_apiBase = '未知'
ref_authHeaders = '未知'
sim_result = None

# --- Tool 1: Node (查找路径) ---
node = None
for cand in [r'C:\Program Files\nodejs\node.exe', r'C:\Program Files (x86)\nodejs\node.exe']:
    if os.path.exists(cand): node = cand; break
if not node:
    try:
        r = subprocess.run(['where','node'], capture_output=True, text=True, timeout=8)
        if r.returncode==0 and r.stdout.strip():
            for ln in r.stdout.splitlines():
                ln = ln.strip()
                if ln.lower().endswith('node.exe') and os.path.exists(ln):
                    node = ln; break
    except Exception: pass

def _run_node_ref_check(node_path, decls_src):
    pp = JS_SNAPSHOT+'.probe.js'
    with open(pp, 'w', encoding='utf-8') as f:
        f.write(decls_src+"""
(function(){
  try {
    var o = {
      API_BASE_type: typeof API_BASE, API_BASE_val: String(API_BASE),
      apiBase_type: typeof apiBase,   apiBase_val: String(apiBase),
      authHeaders_type: typeof authHeaders,
      ok: true
    };
    WScript.Echo(JSON.stringify(o));
  } catch (e) { WScript.Echo(JSON.stringify({ok:false, err:String(e)})); }
})();
""".replace('WScript.Echo', 'console.log'))
    r = subprocess.run([node_path, pp], capture_output=True, text=True, timeout=12)
    if r.returncode==0:
        try:
            last = [ln for ln in r.stdout.splitlines() if ln.strip()][-1]
            return json.loads(last)
        except Exception: return {"ok":False, "err":"parse stdout failed: "+r.stdout[:200]}
    return {"ok":False, "err":r.stderr[:300] or ("rc="+str(r.returncode))}

def _run_dom_sim(node_path):
    # 伪 DOM：不依赖 document/window 真实对象
    pseudo = """
var __buttons = [
  { dataset:{module:'dashboard'},   _hl:false, _rm:[] },
  { dataset:{module:'materials'},   _hl:false, _rm:[] },
  { dataset:{module:'plan'},        _hl:false, _rm:[] },
  { dataset:{module:'production'},  _hl:false, _rm:[] },
  { dataset:{module:'procurement'}, _hl:false, _rm:[] },
  { dataset:{module:'finance'},     _hl:false, _rm:[] },
  { dataset:{module:'report'},      _hl:false, _rm:[] },
  { dataset:{module:'system'},      _hl:false, _rm:[] },
];
__buttons.forEach(function(b){
  b.classList = {
    add: function(c){ if (c==='active') b._hl = true; },
    remove: function(c){ b._rm.push(c); },
    contains: function(c){ return c==='active' ? b._hl : false; }
  };
});
var __sidebar = { querySelectorAll: function(){ return __buttons; } };
var __content = { innerHTML: '' };
var document = {
  getElementById: function(id){
    if (id==='sidebar-menu' || id==='sidebar') return __sidebar;
    if (id==='content' || id==='module-content' || id==='main-content' || id==='app-content' || id==='content-area') return __content;
    return null;
  },
  querySelector: function(){ return null; },
  querySelectorAll: function(){ return []; },
  body: { innerHTML: '' },
  addEventListener: function(){},
  createElement: function(){
    return { innerHTML:'', appendChild:function(){}, classList:{add(){},remove(){},contains(){return false;}}, style:{}, dataset:{} };
  }
};
var window = {
  addEventListener: function(){},
  location: { hash:'', href:'', pathname:'/' },
  localStorage: { getItem:function(){return null;}, setItem:function(){}, removeItem:function(){} }
};
var localStorage = window.localStorage, sessionStorage = localStorage;
var fetch = function(){ return Promise.resolve({ ok:true, status:200, json:function(){return Promise.resolve({success:true,data:{}});}, text:function(){return Promise.resolve('<div></div>');} }); };
var $ = function(){ return { on:function(){}, off:function(){}, click:function(){}, collapse:function(){}, addClass:function(){}, removeClass:function(){}, tab:function(){} }; };
$.ajax = function(){ return Promise.resolve({}); };
var bootstrap = { Modal: function(){ this.show=function(){}; this.hide=function(){}; }, Tab: function(){this.show=function(){};} };
var Chart = function(){ this.destroy=function(){}; this.update=function(){}; };
var echarts = { init: function(){ return { setOption:function(){}, dispose:function(){}, resize:function(){}, off:function(){} }; } };
var toastr = { success:function(){}, error:function(){}, warning:function(){}, info:function(){} };
var Swal = { fire: function(){ return Promise.resolve({isConfirmed:true, value:''}); }, mixin: function(){ return Swal; } };
var hljs = { highlightElement:function(){} };
var QRCode = function(){ this.makeCode=function(){}; this.clear=function(){}; };
var jsQR = function(){ return null; };
"""
    full = pseudo + "\n" + combined_js + "\n"
    full += """
(async function(){
  try {
    await loadModule('dashboard');
    var out = __buttons.map(function(b){ return { module: b.dataset.module, active: b._hl }; });
    console.log('SIMRESULT=' + JSON.stringify({ok:true, dashActive: out[0].active, buttons: out}));
  } catch (e) {
    console.log('SIMRESULT=' + JSON.stringify({ok:false, err: String(e), stack: String(e && e.stack || '').slice(0,400)}));
  }
})();
"""
    sp = JS_SNAPSHOT + '.sim.js'
    with open(sp, 'w', encoding='utf-8') as f: f.write(full)
    r = subprocess.run([node_path, sp], capture_output=True, text=True, timeout=20)
    out = r.stdout + r.stderr
    m = re.search(r'SIMRESULT=(\{.*\})', out)
    if m:
        try: return json.loads(m.group(1))
        except Exception as e: return {"ok":False,"err":"parse simresult fail: "+str(e)}
    return {"ok":False, "err":"no SIMRESULT, raw out: "+(out[:600] if out else '(empty)')}

if node:
    parser_name = f"Node.js @ {node}"
    print(f"[INFO] 使用 {parser_name}")
    # 语法检查
    r = subprocess.run([node, '--check', JS_SNAPSHOT], capture_output=True, text=True, timeout=20)
    if r.returncode == 0:
        syntax_error = False
        print("[PASS] SyntaxError = NO (node --check 通过)")
    else:
        syntax_error = True
        print("[FAIL] SyntaxError = YES (node --check 不通过)")
        for ln in r.stderr.splitlines()[:30]: print("   >", ln)
    # Reference check: 提取前置声明
    decls = []
    for line in combined_js.splitlines():
        s = line.strip().rstrip(';')
        if s.startswith(('const API_BASE','const apiBase','const authHeaders',
                         'let API_BASE','let apiBase','let authHeaders',
                         'var API_BASE','var apiBase','var authHeaders')):
            decls.append(s+';')
        if len(decls) >= 30: break
    decl_src = "\n".join(decls)
    r2 = _run_node_ref_check(node, decl_src)
    print(f"[INFO] Reference 探针结果: {json.dumps(r2, ensure_ascii=False)}")
    if r2.get('ok'):
        ref_apiBase     = 'NO' if r2.get('apiBase_type') not in ('undefined', None) else 'YES'
        ref_authHeaders = 'NO' if r2.get('authHeaders_type') not in ('undefined', None) else 'YES'
        # 同时验证值是否 /api/v1
        if r2.get('apiBase_val') != '/api/v1':
            print(f"[WARN] apiBase 值是 '{r2.get('apiBase_val')}'，而非 '/api/v1'")
            if r2.get('API_BASE_val') == '/api/v1':
                print(f"       但 API_BASE = '/api/v1'，所以运行时等效")
    else:
        if 'ReferenceError' in r2.get('err',''):
            if 'apiBase' in r2['err'].lower(): ref_apiBase = 'YES'
            if 'authHeaders' in r2['err'].lower(): ref_authHeaders = 'YES'
        print(f"[WARN] 探针异常: {r2.get('err')}")
    # 伪 DOM 模拟
    print("\n[C.ext] 伪 DOM 模拟 loadModule('dashboard') 按钮高亮")
    sim_result = _run_dom_sim(node)
    print(f"        模拟结果: {json.dumps(sim_result, ensure_ascii=False, indent=2)}")
    if sim_result.get('ok'):
        if sim_result.get('dashActive'):
            print("[PASS] dashboard 侧边按钮 active 高亮逻辑正常")
        else:
            print("[WARN] 模拟完成但 dashboard 未高亮 active，需核对高亮逻辑")
    else:
        print(f"[WARN] 模拟抛出异常: {sim_result.get('err')}")
        if sim_result.get('stack'):
            print("       Stack:", sim_result['stack'][:300])

# --- Tool 2: py_mini_racer (兜底) ---
if not parser_name:
    try:
        from py_mini_racer import MiniRacer
        parser_name = "py_mini_racer"
        print(f"[INFO] 使用 {parser_name}")
        ctx = MiniRacer()
        try:
            ctx.execute(combined_js)
            syntax_error = False
            print("[PASS] SyntaxError = NO")
        except Exception as e:
            syntax_error = True
            print(f"[FAIL] SyntaxError = YES: {e}")
        try:
            a = ctx.eval("[typeof apiBase, String(apiBase)]")
            h = ctx.eval("typeof authHeaders")
            print(f"[INFO] apiBase typeof={a[0]} val={a[1][:50]}, authHeaders typeof={h}")
            ref_apiBase = 'NO' if a[0] != 'undefined' else 'YES'
            ref_authHeaders = 'NO' if h != 'undefined' else 'YES'
        except Exception as ee:
            print(f"[WARN] ref 探针失败: {ee}")
            emsg = str(ee).lower()
            if 'apibase' in emsg: ref_apiBase = 'YES'
            if 'authheaders' in emsg: ref_authHeaders = 'YES'
    except ImportError:
        pass

# --- Tool 3: cscript.exe (JScript/ES5) 纯语法 check 兜底 (去掉 const/let/await/async 后用 JScript 解析检查) ---
# JScript 仅支持 ES3，不能直接跑 ES6+，但我们可以用 "抛 SyntaxError 说明解析错误" 方式粗略验证
# 实际上更稳妥：这里不做真 ES6 解析，只标记未执行
if not parser_name:
    print("[WARN] 未找到 node.exe，py_mini_racer 也未安装 -> 跳过 JS 语法/Reference 真实验证")
    print("       (提示: 可用全局 pip install --user py_mini_racer 或安装 Node.js 补跑 Step C)")

print("\n[Step C 汇总]")
print(f"  使用解析器                : {parser_name or '无 (未执行)'}")
se_str = 'YES' if syntax_error is True else ('NO' if syntax_error is False else '未知(未执行)')
print(f"  SyntaxError               : {se_str}")
print(f"  ReferenceError(apiBase)   : {ref_apiBase.upper()}")
print(f"  ReferenceError(authHeaders): {ref_authHeaders.upper()}")

# ================ Step D & E ================
def do_req(method, url, data=None, token=None, timeout=10):
    headers = {'Content-Type':'application/json'}
    if token: headers['Authorization'] = 'Bearer '+token
    body = json.dumps(data).encode('utf-8') if data is not None else None
    try:
        req = urllib.request.Request(url, data=body, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            rb = resp.read()
            ct = resp.headers.get('Content-Type','') or ''
            try:
                if 'json' in ct.lower() or rb[:1] in (b'{',b'['):
                    j = json.loads(rb.decode('utf-8', errors='replace'))
                else:
                    j = {'_raw': rb.decode('utf-8', errors='replace')[:200]}
            except Exception:
                j = {'_raw_head': rb[:120]}
            return resp.status, j, None
    except urllib.error.HTTPError as he:
        rb = he.read()
        try: j = json.loads(rb.decode('utf-8', errors='replace'))
        except: j = {'_raw': rb.decode('utf-8', errors='replace')[:200]}
        return he.code, j, str(he)
    except Exception as e:
        return None, None, str(e)

LOGIN = {'username':'超级臭屁','password':'123456'}

print("\n"+"="*70)
print("Step D: 全链路 API 验证 (账号=超级臭屁/123456)")
print("="*70)

st, sj, err = do_req('POST','http://127.0.0.1:8000/api/v1/auth/login', LOGIN)
print(f"D1. POST /api/v1/auth/login")
print(f"    状态码={st}, 错误={err}")
token = None; d1ok=False
if isinstance(sj, dict):
    succ = sj.get('success')
    data = sj.get('data') or {}
    token = data.get('token') or data.get('access_token') or sj.get('token')
    d1ok = (isinstance(st,int) and 200<=st<300 and (succ is True or token))
    print(f"    success={succ}, token存在={bool(token)}")
    print(f"    body预览={json.dumps(sj, ensure_ascii=False)[:500]}")
print(f"    结果={'PASS' if d1ok else 'FAIL'}")

def chk(label, method, sub):
    url = 'http://127.0.0.1:8000/api/v1'+sub
    st,sj,err = do_req(method, url, token=token)
    code_ok = isinstance(st,int) and 200<=st<300
    sf = sj.get('success') if isinstance(sj,dict) else None
    ok = code_ok and (sf is True)
    print(f"\n{label}. {method} /api/v1{sub}")
    print(f"    状态码={st}, 错误={err}")
    if isinstance(sj, dict):
        if st == 500:
            print(f"    [500 错误详情] message={sj.get('message')!r}, error_code={sj.get('error_code')!r}")
        print(f"    success={sf}, keys={list(sj.keys())[:10]}")
        print(f"    body预览={json.dumps(sj, ensure_ascii=False)[:400]}")
    else:
        print(f"    body={str(sj)[:200]}")
    print(f"    结果={'PASS' if ok else 'FAIL'}")
    return ok

d2 = chk("D2","GET","/materials/product-catalog")
d3 = chk("D3","GET","/plan/forecast-orders")
d4 = chk("D4","GET","/procurement/purchase-requests")
d5 = chk("D5","GET","/materials/")
d6 = chk("D6","GET","/finance/reports/balance-sheet")

print(f"\n[Step D 汇总] D1={'PASS' if d1ok else 'FAIL'} | D2={'PASS' if d2 else 'FAIL'} | D3={'PASS' if d3 else 'FAIL'} | D4={'PASS' if d4 else 'FAIL'} | D5={'PASS' if d5 else 'FAIL'} | D6={'PASS' if d6 else 'FAIL'}")

print("\n"+"="*70)
print("Step E: 跨网卡登录 (http://192.168.3.93:8000)")
print("="*70)
st,sj,err = do_req('POST','http://192.168.3.93:8000/api/v1/auth/login', LOGIN, timeout=8)
print(f"E1. POST http://192.168.3.93:8000/api/v1/auth/login")
print(f"    状态码={st}, 错误={err}")
e1ok=False
if isinstance(sj, dict):
    sf = sj.get('success'); data = sj.get('data') or {}
    tk = data.get('token') or data.get('access_token') or sj.get('token')
    e1ok = (isinstance(st,int) and 200<=st<300 and (sf is True or tk))
    print(f"    success={sf}, token存在={bool(tk)}")
    print(f"    body预览={json.dumps(sj, ensure_ascii=False)[:500]}")
elif sj is not None:
    print(f"    body={str(sj)[:200]}")
print(f"    结果={'PASS - 跨网卡可达 (同WiFi手机接口可用)' if e1ok else 'FAIL - 不可达或登录失败'}")

print("\n=== 全部步骤打印完毕 ===")
