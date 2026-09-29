# -*- coding: utf-8 -*-
"""Step C standalone: 使用 Python38 + 手动解压的 py_mini_racer 做语法检查 + 伪 DOM 模拟"""
import sys, os, re, json, tempfile

sys.path.insert(0, r'c:\Users\ruancanling\Desktop\ERP VIBE CODING\site-packages')
from py_mini_racer import MiniRacer

JS_FILE = os.path.join(tempfile.gettempdir(), 'inline_scripts.js')
HTML_FILE = os.path.join(tempfile.gettempdir(), 'homepage_snapshot.html')

# 如果 snapshot 不存在，再下载一次
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
print(f"[INFO] 提取 {len(scripts)} 个内联 script, 合计 {len(combined_js)} chars")

# ===== 语法检查 =====
print("\n[Step C] 使用 py_mini_racer (Python 3.8 x64 @ 解压 wheel) 执行语法 parse...")
syntax_error = None
ctx = MiniRacer()

# 注意: py_mini_racer 的 V8 一次 parse 整段脚本会抛 JS 内部 SyntaxError 或直接抛 Python 异常。
try:
    ctx.execute(combined_js)
    syntax_error = False
    print("[PASS] SyntaxError = NO (整段 243K JS 解析 + 顶层执行均无 SyntaxError)")
except Exception as e:
    estr = str(e)
    if 'SyntaxError' in estr:
        syntax_error = True
        print(f"[FAIL] SyntaxError = YES")
        # 打印头部 500 字符
        print("       :", estr[:1200])
    else:
        # 可能是 ReferenceError 或运行时错误 (非 SyntaxError)
        syntax_error = False
        print(f"[PASS] SyntaxError = NO (无 SyntaxError)")
        print(f"       (但顶层运行时抛错: {estr[:400]})")

# ===== ReferenceError(apiBase, authHeaders) 检查 =====
# 方法: 使用新 context (避免上一个 ctx 已污染)，仅执行声明探针 + 伪 stub (document/window 等)
print("\n[Step C] ReferenceError 检查 (新 context, 带最小 browser stub)")
ctx2 = MiniRacer()

# 最小 stub (仅用于不立即崩溃，不模拟功能)
minimal_stub = """
var window = { addEventListener: function(){}, location:{hash:'',href:''}, localStorage:{getItem:function(){return null;},setItem:function(){},removeItem:function(){}} };
var document = { getElementById:function(){return null;}, querySelector:function(){return null;}, querySelectorAll:function(){return [];}, addEventListener:function(){}, body:{innerHTML:''}, createElement:function(){return {innerHTML:'',appendChild:function(){},classList:{add:function(){},remove:function(){},contains:function(){return false;}},style:{},dataset:{}}; } };
var localStorage = window.localStorage;
var sessionStorage = localStorage;
var fetch = function(){ return Promise.resolve({ok:true,json:function(){return Promise.resolve({});},text:function(){return Promise.resolve('');}}); };
var $ = function(){ return {on:function(){},off:function(){},click:function(){},collapse:function(){},addClass:function(){},removeClass:function(){},tab:function(){} }; };
$.ajax = function(){};
var bootstrap = { Modal: function(){this.show=function(){};this.hide=function(){};}, Tab: function(){this.show=function(){};} };
var Chart = function(){};
var echarts = {init:function(){return {setOption:function(){},dispose:function(){},resize:function(){},off:function(){};}};};
var toastr = {success:function(){},error:function(){},warning:function(){},info:function(){}};
var Swal = {fire:function(){return Promise.resolve({isConfirmed:true});}, mixin:function(){return Swal;}};
var hljs = {highlightElement:function(){}};
var QRCode = function(){};
var jsQR = function(){return null;};
var console = {log:function(){},warn:function(){},error:function(){},info:function(){}};
"""

# 执行 minimal_stub
try:
    ctx2.execute(minimal_stub)
except Exception as ee:
    print(f"[WARN] stub 自身抛错(通常不会): {ee}")

# 分段加载 combined_js (如果 243K 太大 parse 失败，分块)
# 但其实 243K 对 V8 不大。直接 try 执行
try:
    ctx2.execute(combined_js)
    print("[INFO] 整段脚本在带 stub 的 context 中执行完毕 (无 SyntaxError)")
except Exception as e:
    estr = str(e)
    if 'SyntaxError' in estr:
        if not syntax_error:
            syntax_error = True
            print(f"[FAIL] SyntaxError = YES: {estr[:800]}")
    else:
        print(f"[INFO] 运行时抛错(非 Syntax): {estr[:300]}")

# 现在检查 typeof apiBase / authHeaders
try:
    r_api = ctx2.eval("JSON.stringify({apiBase_t: typeof apiBase, apiBase_v: String(apiBase), API_BASE_t: typeof API_BASE, API_BASE_v: String(API_BASE)})")
    r_api = json.loads(r_api)
    print(f"[INFO] apiBase 检查: typeof={r_api.get('apiBase_t')}, value={str(r_api.get('apiBase_v'))[:60]}")
    print(f"[INFO] API_BASE 检查: typeof={r_api.get('API_BASE_t')}, value={str(r_api.get('API_BASE_v'))[:60]}")
    ref_apiBase = 'NO' if (r_api.get('apiBase_t') not in ('undefined', None)) else 'YES'
except Exception as e:
    estr = str(e)
    print(f"[REF] apiBase 探针抛错: {estr[:300]}")
    ref_apiBase = 'YES' if ('ReferenceError' in estr and 'apiBase' in estr.lower()) else 'YES(抛错但不确定)'

try:
    r_ah = ctx2.eval("JSON.stringify({ah_t: typeof authHeaders})")
    r_ah = json.loads(r_ah)
    print(f"[INFO] authHeaders typeof = {r_ah.get('ah_t')}")
    ref_authHeaders = 'NO' if r_ah.get('ah_t') != 'undefined' else 'YES'
except Exception as e:
    estr = str(e)
    print(f"[REF] authHeaders 探针抛错: {estr[:300]}")
    ref_authHeaders = 'YES' if ('ReferenceError' in estr and 'authHeaders' in estr.lower()) else 'YES(抛错但不确定)'

# ===== 伪 DOM 模拟 loadModule('dashboard') 按钮高亮 =====
print("\n[C.ext] 伪 DOM 模拟 loadModule('dashboard') 并检查 sidebar 按钮高亮")
ctx3 = MiniRacer()

# 精心构造伪 DOM: sidebar-menu 含按钮，content 存在，并提供所有 3rd-party mock
sim_stub = r"""
// ===== 伪 buttons =====
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
var __sidebarEl = { querySelectorAll: function(){ return __buttons; } };
var __contentEl = { innerHTML: '' };
var __scanBarEl = { addEventListener:function(){}, focus:function(){}, blur:function(){} };
var __loginBox = { classList:{ add:function(){}, remove:function(){}, contains:function(){return false;} } };
var __appBox = { classList:{ add:function(){}, remove:function(){}, contains:function(){return false;} } };
var __toastArea = {};

// ===== 全局 browser / lib stubs =====
var window = {
  addEventListener: function(){},
  location: { hash: '', href: 'http://127.0.0.1:8000/', pathname:'/' },
  localStorage: { getItem:function(k){return k==='token'?null:(k==='lang'?'zh':null);}, setItem:function(){}, removeItem:function(){} }
};
var document = {
  getElementById: function(id){
    if (id==='sidebar-menu' || id==='sidebar') return __sidebarEl;
    if (id==='content' || id==='module-content' || id==='main-content' || id==='app-content' || id==='content-area') return __contentEl;
    if (id==='scan-bar' || id==='scanInput') return __scanBarEl;
    if (id==='login-box' || id==='loginBox') return __loginBox;
    if (id==='main-app' || id==='app' || id==='mainApp' || id==='appBox') return __appBox;
    if (id==='toast-area' || id==='toastArea') return __toastArea;
    return null;
  },
  querySelector: function(sel){
    // 处理选择器字符串（仅粗匹配）
    if (sel.indexOf('sidebar-menu') >= 0) return __sidebarEl;
    if (sel.indexOf('#content') >= 0) return __contentEl;
    if (sel.indexOf('.content-area') >= 0) return __contentEl;
    if (sel.indexOf('#scan-bar') >= 0) return __scanBarEl;
    return null;
  },
  querySelectorAll: function(sel){
    if (sel.indexOf('.sidebar-menu button') >= 0 || sel.indexOf('#sidebar-menu button') >= 0 || sel.indexOf('button[data-module]')>=0) return __buttons;
    if (sel.indexOf('.sidebar-menu') >= 0 || sel.indexOf('#sidebar-menu') >= 0) return [__sidebarEl];
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
    json: function(){ return Promise.resolve({success:true, data:{}}); },
    text: function(){ return Promise.resolve('<div class="module-page">mock module html</div>'); }
  });
};
var $ = function(sel){
  return {
    on: function(){return this;}, off: function(){return this;},
    click: function(){return this;}, collapse: function(){return this;},
    addClass: function(){return this;}, removeClass: function(){return this;},
    tab: function(){return this;}, modal: function(){return this;},
    show: function(){return this;}, hide: function(){return this;},
    html: function(){return this;}, text: function(){return this;},
    val: function(){return '';}, attr: function(){return null;},
    data: function(){return null;}
  };
};
$.ajax = function(opts){
  if (opts && typeof opts.success === 'function') opts.success({success:true,data:{}});
  if (opts && typeof opts.complete === 'function') opts.complete();
  return Promise.resolve({success:true,data:{}});
};
var bootstrap = {
  Modal: function(){this.show=function(){}; this.hide=function(){}; this.dispose=function(){};},
  Tab: function(){this.show=function(){};}
};
var Chart = function(el, cfg){ this.destroy=function(){}; this.update=function(){}; this.resize=function(){}; this.setOption=function(){}; };
var echarts = {
  init: function(el){ return { setOption:function(){}, dispose:function(){}, resize:function(){}, off:function(){}, on:function(){} }; }
};
var toastr = {
  success: function(msg){ __lastToast = {type:'success',msg:msg};},
  error:   function(msg){ __lastToast = {type:'error',msg:msg};},
  warning: function(msg){ __lastToast = {type:'warning',msg:msg};},
  info:    function(msg){ __lastToast = {type:'info',msg:msg};}
};
var __lastToast = null;
var Swal = {
  fire: function(){ return Promise.resolve({isConfirmed:true, value:''}); },
  mixin: function(){ return Swal; }
};
var hljs = { highlightElement:function(){} };
var QRCode = function(el, opt){ this.makeCode=function(txt){this.__txt=txt;}; this.clear=function(){}; };
var jsQR = function(data, w, h){ return null; };
var console = { log:function(){}, warn:function(){}, error:function(){}, info:function(){}, debug:function(){} };

// ===== 暴露给 Python 的结果读取 =====
var __simResult = null;
"""

try:
    ctx3.execute(sim_stub)
except Exception as e:
    print(f"[FATAL] sim_stub 执行失败: {e}")
    sys.exit(1)

# 执行整段首页 JS
try:
    ctx3.execute(combined_js)
    print("[INFO] 首页 JS 在伪 DOM 环境中执行完毕 (无 SyntaxError)")
except Exception as e:
    estr = str(e)
    if 'SyntaxError' in estr:
        if not syntax_error: syntax_error = True
        print(f"[FAIL] SyntaxError (在伪 DOM context) = YES")
        print("       :", estr[:800])
    else:
        print(f"[INFO] 运行时抛错 (非 Syntax): {estr[:300]}")

# 调用 loadModule('dashboard')，拿到按钮高亮状态
try:
    call_js = """
    (async function(){
      try {
        await loadModule('dashboard');
        var summary = __buttons.map(function(b){ return { module: b.dataset.module, active: b._hl }; });
        __simResult = JSON.stringify({ok:true, dashActive: summary[0].active, buttons: summary, lastToast: __lastToast});
        return __simResult;
      } catch (e) {
        __simResult = JSON.stringify({ok:false, err: String(e), stack: String(e && e.stack || '').slice(0,400)});
        return __simResult;
      }
    })();
    """
    # py_mini_racer 返回 Promise 对象 -> 需用回调或等一下；老版 MiniRacer 需要 eval 得到 JSObject。
    # 简单起见：直接调用，用 setTimeout 把结果写入全局 __simResult，稍后读取
    # 其实更稳妥：把 async 立即执行函数转成"同步获取"不可能，改用另一种同步写法：
    # 先将 loadModule('dashboard') 的同步部分跑完，再读高亮状态 (很多 fetch 是异步，但高亮逻辑通常是同步的)
    sync_js = """
    (function(){
      try {
        // 如果 loadModule 是 async，直接调用它同步部分直到第一个 await
        // 先执行 loadModule，返回 Promise 没关系，高亮在 await 之前应已完成
        var p = loadModule('dashboard');
        var summary = __buttons.map(function(b){ return { module: b.dataset.module, active: b._hl, removed: b._rm }; });
        __simResult = JSON.stringify({ok:true, dashActive: summary[0].active, buttons: summary, note: 'async后续未等待'});
      } catch (e) {
        __simResult = JSON.stringify({ok:false, err: String(e), stack: String(e && e.stack || '').slice(0,400)});
      }
      return __simResult;
    })();
    """
    sim_raw = ctx3.eval(sync_js)
    try:
        sim = json.loads(sim_raw)
        print(f"[C.ext 模拟结果] {json.dumps(sim, ensure_ascii=False, indent=2)}")
        if sim.get('ok'):
            if sim.get('dashActive'):
                print("[PASS] loadModule('dashboard') 后 dashboard 按钮已被高亮 (active class 添加成功)")
            else:
                print("[WARN] loadModule('dashboard') 后 dashboard 未高亮。需检查高亮逻辑是否仍使用了 onclick 属性选择器或 ID/类名不对")
                # 看看其他按钮有无高亮
                print("       所有按钮状态:")
                for b in sim.get('buttons', []):
                    print(f"         module={b['module']:15s} active={b['active']}")
        else:
            print(f"[FAIL] loadModule('dashboard') 抛错: {sim.get('err')}")
            if sim.get('stack'):
                print("       Stack:", sim['stack'][:400])
    except Exception as pe:
        print(f"[WARN] 模拟结果解析失败: {pe}  raw={sim_raw[:300]}")
except Exception as e:
    print(f"[FAIL] 伪 DOM 模拟 loadModule 异常: {e}")

print("\n===== [Step C 最终汇总] =====")
print(f"  解析器                       : py_mini_racer 0.6.0 (V8)")
print(f"  SyntaxError                  : {'YES' if syntax_error else 'NO'}")
print(f"  ReferenceError(apiBase)      : {ref_apiBase}")
print(f"  ReferenceError(authHeaders)  : {ref_authHeaders}")
