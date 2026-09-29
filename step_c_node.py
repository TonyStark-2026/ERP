# -*- coding: utf-8 -*-
"""使用 tools/node.exe 完成 Step C 的全部子任务"""
import os, re, json, tempfile, subprocess, sys

NODE = r"c:\Users\ruancanling\Desktop\ERP VIBE CODING\tools\node.exe"
HTML_FILE = os.path.join(tempfile.gettempdir(), 'homepage_snapshot.html')
JS_FILE   = os.path.join(tempfile.gettempdir(), 'inline_scripts.js')
PROJ = r"c:\Users\ruancanling\Desktop\ERP VIBE CODING"

# 如果 snapshot 不在，就下载
if not os.path.exists(HTML_FILE):
    import urllib.request, gzip
    req = urllib.request.Request('http://127.0.0.1:8000/', headers={'Accept-Encoding':'gzip,deflate'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read()
        enc = resp.headers.get('Content-Encoding','')
        html = gzip.decompress(raw).decode('utf-8','replace') if enc=='gzip' else raw.decode('utf-8','replace')
    with open(HTML_FILE,'w',encoding='utf-8') as f: f.write(html)
else:
    with open(HTML_FILE, encoding='utf-8') as f: html = f.read()

scripts = []
for m in re.finditer(r'<script([^>]*)>([\s\S]*?)</script>', html, re.IGNORECASE):
    if re.search(r"""\bsrc\s*=""", m.group(1), re.I): continue
    b = m.group(2).strip()
    if b: scripts.append(b)
combined_js = "\n".join(scripts)
with open(JS_FILE, 'w', encoding='utf-8') as f: f.write(combined_js)
print(f"[INFO] {len(scripts)} 个内联 script, 合计 {len(combined_js)} chars, saved -> {JS_FILE}")
print()

# ====== C1: SyntaxError ======
print("[C1] Syntax 检查 (node --check inline_scripts.js)")
r = subprocess.run([NODE, '--check', JS_FILE], capture_output=True, text=True, timeout=30)
syntax_error = (r.returncode != 0)
if r.returncode == 0:
    print("  PASS: SyntaxError = NO")
else:
    print("  FAIL: SyntaxError = YES")
    for ln in r.stderr.splitlines()[:30]:
        print("   >", ln)
    # 查找所有 createTmpMat( 调用点，看是不是都错
    matches = [(m.start(), m.group(0)) for m in re.finditer(r'createTmpMat\([^)]*\)', combined_js)]
    print(f"\n  找到 {len(matches)} 处 createTmpMat(...) 调用:")
    for pos, s in matches:
        line_no = combined_js[:pos].count('\n') + 1
        print(f"    行{line_no}: {s!r}")
print()

# ====== C2: ReferenceError(apiBase/authHeaders) ======
print("[C2] ReferenceError 检查 (apiBase / authHeaders)")
probe_js = combined_js + """
// 上面脚本可能有 SyntaxError，下面 try...catch 包裹没用 —— SyntaxError 会让整个文件无法 parse。
// 所以这里换一个思路：先只拿"前置声明片段"（SyntaxError 在后面，不影响前 N 行），然后在独立文件里 eval。
"""
# 从 combined_js 提取前 100 行（通常包含所有 top-level const 声明）
safe_decl_lines = []
for i, line in enumerate(combined_js.splitlines(), 1):
    safe_decl_lines.append(line)
    if i >= 80: break
safe_src = "\n".join(safe_decl_lines) + "\n"
safe_src += "globalThis.__probeResult = JSON.stringify({\n"
safe_src += "  apiBase_t: typeof apiBase, apiBase_v: String(apiBase),\n"
safe_src += "  API_BASE_t: typeof API_BASE, API_BASE_v: String(API_BASE),\n"
safe_src += "  authHeaders_t: typeof authHeaders\n"
safe_src += "});\nconsole.log(globalThis.__probeResult);\n"

# 注意：如果 SyntaxError 存在于前 80 行之后，safe_src 应该能 parse 通过
safe_path = os.path.join(PROJ, "_probe_ref.js")
with open(safe_path, 'w', encoding='utf-8') as f: f.write(safe_src)
r2 = subprocess.run([NODE, safe_path], capture_output=True, text=True, timeout=15)
ref_apiBase = None; ref_authHeaders = None
if r2.returncode == 0:
    try:
        last = [ln for ln in r2.stdout.splitlines() if ln.strip()][-1]
        obj = json.loads(last)
        print(f"  probe结果: {json.dumps(obj, ensure_ascii=False)}")
        ref_apiBase     = 'NO' if obj.get('apiBase_t') != 'undefined' else 'YES'
        ref_authHeaders = 'NO' if obj.get('authHeaders_t') != 'undefined' else 'YES'
        if ref_apiBase == 'NO' and obj.get('apiBase_v') != '/api/v1':
            print(f"  [注意] apiBase 值 = {obj.get('apiBase_v')!r}, 非 '/api/v1'")
    except Exception as e:
        print(f"  解析 probe 输出失败: {e}")
        print("  STDOUT:", r2.stdout[:400])
else:
    print(f"  probe 执行失败(rc={r2.returncode})")
    # 可能 SyntaxError 就在前 80 行之内
    print("  STDERR 前20行:")
    for ln in r2.stderr.splitlines()[:20]:
        print("   >", ln)
    # 尝试更短：只取前 30 行
    safe_short = "\n".join(combined_js.splitlines()[:30]) + "\nconsole.log(JSON.stringify({t1:typeof API_BASE, t2:typeof apiBase, t3:typeof authHeaders}));\n"
    sp2 = os.path.join(PROJ, "_probe_ref_short.js")
    with open(sp2, 'w', encoding='utf-8') as f: f.write(safe_short)
    r2b = subprocess.run([NODE, sp2], capture_output=True, text=True, timeout=15)
    if r2b.returncode == 0:
        try:
            obj = json.loads([l for l in r2b.stdout.splitlines() if l.strip()][-1])
            print(f"  [备用] 前30行探针: {obj}")
            ref_apiBase = 'NO' if obj.get('t2') != 'undefined' else 'YES'
            ref_authHeaders = 'NO' if obj.get('t3') != 'undefined' else 'YES'
        except Exception as e:
            print(f"  [备用] 解析失败: {e}, stdout={r2b.stdout[:200]}")
    else:
        print(f"  [备用] 也失败: {r2b.stderr[:400]}")
print()

# ====== C3: 伪 DOM 模拟 loadModule('dashboard') 按钮高亮 ======
print("[C3] 伪 DOM 模拟 loadModule('dashboard') 并检查 sidebar 按钮高亮")
# 首先: SyntaxError 在 2197 行，所以 combined_js 整段 parse 失败。
# 策略: 把 `createTmpMat(${idx});` 替换成 `createTmpMat(idx);` (去掉模板字面量 ${}，因为 idx 本来就是普通变量)
# 注意：不是真的修改源文件，只在"模拟检查"时临时替换，避免 SyntaxError 阻塞后续高亮检查
fixed_js = combined_js.replace("createTmpMat(${idx});", "createTmpMat(idx);")
# 看看有没有其他类似问题
other_bad = list(re.finditer(r'\$\{[^}]+\}\s*\)', fixed_js))
if other_bad:
    print(f"  [INFO] 修复 createTmpMat 后，仍找到 {len(other_bad)} 处可疑的 ${...}) 模式：")
    for mm in other_bad[:5]:
        print(f"    行{fixed_js[:mm.start()].count(chr(10))+1}: {mm.group(0)!r}")
        # 周围上下文
        s = max(0, mm.start()-30); e = min(len(fixed_js), mm.end()+30)
        print(f"      ctx: {fixed_js[s:e]!r}")

# 验证 fixed_js 是否通过 node --check
FIXED_JS = os.path.join(PROJ, "_inline_fixed_for_sim.js")
with open(FIXED_JS, 'w', encoding='utf-8') as f: f.write(fixed_js)
rfix = subprocess.run([NODE, '--check', FIXED_JS], capture_output=True, text=True, timeout=30)
if rfix.returncode == 0:
    print("  [OK] 修复 createTmpMat 后，node --check 通过 (SyntaxError 消除)")
else:
    print("  [WARN] 修复 createTmpMat 后，仍有 SyntaxError:")
    for ln in rfix.stderr.splitlines()[:20]:
        print("   >", ln)

# 构造伪 DOM + 模拟
SIM_PATH = os.path.join(PROJ, "_sim_loadModule.js")
sim_code = r"""
// ============== 伪 DOM / BOM stub ==============
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
var __scan = { addEventListener:function(){}, focus:function(){}, blur:function(){} };

var window = {
  addEventListener: function(){},
  location: { hash: '', href: 'http://127.0.0.1:8000/', pathname:'/' },
  localStorage: { getItem:function(k){return k==='lang'?'zh':null;}, setItem:function(){}, removeItem:function(){} }
};
var document = {
  getElementById: function(id){
    if (id==='sidebar-menu' || id==='sidebar') return __sidebar;
    if (id==='content' || id==='module-content' || id==='main-content' || id==='app-content' || id==='content-area') return __content;
    if (id==='scan-bar' || id==='scanInput' || id==='scan-bar-input') return __scan;
    return null;
  },
  querySelector: function(sel){
    if (!sel) return null;
    if (sel.indexOf('sidebar-menu')>=0) return __sidebar;
    if (sel.indexOf('#content')>=0 || sel.indexOf('.content-area')>=0) return __content;
    return null;
  },
  querySelectorAll: function(sel){
    if (!sel) return [];
    if (/button.*data-module|\.sidebar-menu\s*button|#sidebar-menu\s*button/i.test(sel)) return __buttons;
    if (/sidebar-menu/i.test(sel)) return [__sidebar];
    return [];
  },
  addEventListener: function(){},
  body: { innerHTML: '' },
  createElement: function(){
    return { innerHTML:'', appendChild:function(){}, classList:{add:function(){},remove:function(){},contains:function(){return false;}}, style:{}, dataset:{}, setAttribute:function(){}, removeAttribute:function(){} };
  },
  cookie: ''
};
var localStorage = window.localStorage;
var sessionStorage = localStorage;
var fetch = function(){
  return Promise.resolve({
    ok: true, status: 200,
    json: function(){ return Promise.resolve({success:true, data:{items:[], total:0}}); },
    text: function(){ return Promise.resolve('<div class="module-container">mock module page content</div>'); }
  });
};
var $ = function(){ return {on:function(){return this;}, off:function(){return this;}, click:function(){return this;}, collapse:function(){return this;}, addClass:function(){return this;}, removeClass:function(){return this;}, tab:function(){return this;}, modal:function(){return this;}, show:function(){return this;}, hide:function(){return this;}, html:function(){return this;}, text:function(){return this;}, val:function(){return '';}, attr:function(){return null;}, data:function(){return null;}, serialize:function(){return '';}, serializeArray:function(){return [];}, ajaxSubmit:function(){} }; };
$.ajax = function(opts){
  if (opts && typeof opts.success === 'function') opts.success({success:true, data:{}});
  if (opts && typeof opts.complete === 'function') opts.complete();
  return Promise.resolve({success:true,data:{}});
};
$.get = function(url, cb){ if (cb) cb({}); return Promise.resolve({}); };
$.post = function(url, d, cb){ if (cb) cb({}); return Promise.resolve({}); };
var bootstrap = { Modal: function(){this.show=function(){}; this.hide=function(){}; this.dispose=function(){};}, Tab: function(){this.show=function(){};} };
var Chart = function(){ this.destroy=function(){}; this.update=function(){}; this.resize=function(){}; this.setOption=function(){}; };
var echarts = { init: function(){ return { setOption:function(){}, dispose:function(){}, resize:function(){}, off:function(){}, on:function(){} }; } };
var toastr = { success:function(){}, error:function(){}, warning:function(){}, info:function(){} };
var Swal = { fire: function(){ return Promise.resolve({isConfirmed:true, value:''}); }, mixin: function(){ return Swal; } };
var hljs = { highlightElement:function(){} };
var QRCode = function(el, opt){ this.makeCode=function(txt){this.__txt=txt;}; this.clear=function(){}; };
var jsQR = function(){ return null; };
var console = { log:function(){}, warn:function(){}, error:function(){}, info:function(){}, debug:function(){} };

// ============== 注入修复后的 JS ==============
""" + "\n// ---- INLINE_JS_BEGIN ----\n" + fixed_js + "\n// ---- INLINE_JS_END ----\n"

sim_code += r"""
// ============== 执行 loadModule('dashboard') 并取结果 ==============
(async function(){
  try {
    await loadModule('dashboard');
    var res = __buttons.map(function(b){ return { module: b.dataset.module, active: b._hl }; });
    process.stdout.write('SIMRESULT=' + JSON.stringify({ok:true, dashActive: res[0].active, states: res}) + '\n');
  } catch (e) {
    process.stdout.write('SIMRESULT=' + JSON.stringify({ok:false, err: String(e), stack: String(e && e.stack || '').slice(0,500)}) + '\n');
  }
})();
"""
with open(SIM_PATH, 'w', encoding='utf-8') as f: f.write(sim_code)
print(f"  [INFO] 生成模拟脚本 {SIM_PATH} ({len(sim_code)} chars)，运行中...")
rsim = subprocess.run([NODE, SIM_PATH], capture_output=True, text=True, timeout=30)
combined_out = rsim.stdout + rsim.stderr
mm = re.search(r'SIMRESULT=(\{.*\})', combined_out)
sim_ok = False
if mm:
    try:
        res = json.loads(mm.group(1))
        print(f"  [模拟结果] {json.dumps(res, ensure_ascii=False, indent=2)}")
        if res.get('ok'):
            sim_ok = True
            if res.get('dashActive'):
                print("  PASS: loadModule('dashboard') 后 dashboard 按钮高亮(active class)正常")
            else:
                print("  WARN: dashboard 未高亮。各按钮状态:")
                for b in res.get('states', []):
                    print(f"    module={b['module']:15s} active={b['active']}")
        else:
            print(f"  FAIL: loadModule('dashboard') 抛出异常: {res.get('err')}")
            if res.get('stack'):
                print("    Stack 前 500:", res['stack'][:500])
    except Exception as pe:
        print(f"  解析模拟结果失败: {pe}")
        print("    RAW:", combined_out[:500])
else:
    print(f"  未捕获 SIMRESULT (rc={rsim.returncode})")
    print("  STDOUT 前 500:", rsim.stdout[:500])
    print("  STDERR 前 500:", rsim.stderr[:500])

print()
print("===== [Step C 最终汇总] =====")
print(f"  解析器                         : Node.js v20.17.0 (portable @ tools/node.exe)")
print(f"  SyntaxError                    : {'YES (实锤: createTmpMat(${idx}); 行2197)' if syntax_error else 'NO'}")
print(f"  ReferenceError(apiBase)        : {ref_apiBase if ref_apiBase is not None else '未知'}")
print(f"  ReferenceError(authHeaders)    : {ref_authHeaders if ref_authHeaders is not None else '未知'}")
print(f"  loadModule 伪DOM 模拟          : {'PASS(dashboard高亮)' if sim_ok and res.get('dashActive') else ('WARN(未高亮)' if sim_ok else 'FAIL(抛异常)')}")
