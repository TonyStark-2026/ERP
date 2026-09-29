# -*- coding: utf-8 -*-
"""重跑 C3: 补全伪 button 的 getAttribute/setAttribute 方法 + 修复其他可能的 stub 缺口"""
import os, re, json, tempfile, subprocess

NODE = r"c:\Users\ruancanling\Desktop\ERP VIBE CODING\tools\node.exe"
PROJ = r"c:\Users\ruancanling\Desktop\ERP VIBE CODING"
JS_FILE = os.path.join(tempfile.gettempdir(), 'inline_scripts.js')
with open(JS_FILE, encoding='utf-8') as f: combined_js = f.read()

# 修补 SyntaxError (所有 createTmpMat(${idx}) -> createTmpMat(idx))
# 其他真的在模板字符串内部的 ${...} 别乱改
# 找所有 `createTmpMat(${idx})` 且上下文不是在 `` 包裹内的
fixed_js = combined_js
# 更安全：先替换所有 createTmpMat(${idx}) (非模板字符串内部情况会错，真模板字符串内部也不会更错)
# 实际上 createTmpMat(${idx}) 在 2157/2197 两处都在 onclick="..." 属性字符串里，不是模板字符串内
fixed_js = fixed_js.replace("createTmpMat(${idx})", "createTmpMat(idx)")

SIM = os.path.join(PROJ, "_sim_loadModule_v2.js")

stub = r"""
// ============== 伪 button factory (补齐 HTMLElement 相关方法) ==============
function mkButton(mod){
  var b = {
    dataset: { module: mod },
    _hl: false,
    _rm: [],
    _attrs: { 'data-module': mod, type:'button', class:'' },
    innerHTML: '', innerText:'', textContent:'', id:'',
    addEventListener: function(){},
    removeEventListener: function(){},
    click: function(){}
  };
  b.getAttribute = function(k){
    if (k==='data-module' || k==='module') return b.dataset.module;
    return b._attrs[k] !== undefined ? b._attrs[k] : null;
  };
  b.setAttribute = function(k,v){ b._attrs[k]=v; };
  b.hasAttribute = function(k){ return b.getAttribute(k) !== null; };
  b.removeAttribute = function(k){ delete b._attrs[k]; };
  b.classList = {
    add: function(c){
      if (c==='active') b._hl = true;
      var parts = (b._attrs['class']||'').split(/\s+/).filter(Boolean);
      if (parts.indexOf(c)===-1) parts.push(c);
      b._attrs['class'] = parts.join(' ');
    },
    remove: function(c){
      b._rm.push(c);
      var parts = (b._attrs['class']||'').split(/\s+/).filter(Boolean);
      b._attrs['class'] = parts.filter(function(x){return x!==c;}).join(' ');
    },
    contains: function(c){
      if (c==='active') return b._hl;
      return ((b._attrs['class']||'').split(/\s+/).indexOf(c) !== -1);
    },
    toggle: function(c){
      if (this.contains(c)) this.remove(c); else this.add(c);
    }
  };
  b.matches = function(sel){
    if (!sel) return false;
    if (sel.indexOf('[data-module="'+mod+'"]') >= 0) return true;
    if (sel.indexOf('.active')>=0) return b._hl;
    if (sel.indexOf('button')>=0) return true;
    return false;
  };
  return b;
}
var __buttons = [
  mkButton('dashboard'),
  mkButton('materials'),
  mkButton('plan'),
  mkButton('production'),
  mkButton('procurement'),
  mkButton('finance'),
  mkButton('report'),
  mkButton('system'),
];
var __ulList = [];  // ul.li.button 结构
__buttons.forEach(function(b){
  var li = {
    dataset:{}, innerHTML:'', appendChild:function(){}, classList:{add(){},remove(){},contains(){return false;}},
    querySelector: function(s){ if (s==='button') return b; return null; }
  };
  b.parentElement = li;
  __ulList.push(li);
});
var __sidebar = {
  __proto__: null,
  querySelectorAll: function(sel){
    if (!sel) return [];
    // button[data-module=...] 选择器按 module 过滤
    if (/button\[data-module[^\]]*=["']?([^"'\]]+)/i.test(sel)) {
      var m = sel.match(/button\[data-module[^\]]*=["']?([^"'\]]+)/i);
      var target = m && m[1];
      if (target) {
        var f = __buttons.filter(function(x){return x.dataset.module===target;});
        if (f.length) return f;
      }
    }
    if (sel && (sel.indexOf('button')>=0)) return __buttons.slice();
    if (sel && (sel.indexOf('li')>=0)) return __ulList.slice();
    if (/\.sidebar-menu|#sidebar-menu/.test(sel)) return [__sidebar];
    return [];
  },
  querySelector: function(sel){ return __sidebar.querySelectorAll(sel)[0] || null; },
  addEventListener: function(){},
  classList: { add(){}, remove(){}, contains(){return false;} },
  innerHTML: ''
};
var __content = {
  innerHTML: '', appendChild:function(){}, classList:{add(){},remove(){},contains(){return false;}},
  querySelectorAll: function(){return [];}, querySelector: function(){return null;}
};
var __scan = { addEventListener:function(){}, focus:function(){}, blur:function(){}, value:'', classList:{add(){},remove(){},contains(){return false;}} };
var __loginBox = { classList: { add:function(c){ if (c==='d-none'||c==='hidden') __loginBox._hidden=true; }, remove:function(c){ if (c==='d-none'||c==='hidden') __loginBox._hidden=false; }, contains:function(c){return !!__loginBox._hidden;} } }, _hidden:false, style:{display:''} };
var __appBox = { classList: { add:function(c){ if (c==='d-none'||c==='hidden') __appBox._hidden=true; }, remove:function(c){ if (c==='d-none'||c==='hidden') __appBox._hidden=false; }, contains:function(c){return !!__appBox._hidden;} } }, _hidden:false, style:{display:''}, innerHTML:'' };
var __headerUsr = { textContent:'', innerText:'', classList:{add(){},remove(){},contains(){return false;}} };
var __toastArea = { innerHTML:'' };

var window = {
  addEventListener: function(){},
  location: { hash: '', href: 'http://127.0.0.1:8000/', pathname:'/', search:'' },
  localStorage: {
    _d:{lang:'zh'},
    getItem:function(k){return this._d[k]===undefined?null:this._d[k];},
    setItem:function(k,v){this._d[k]=String(v);},
    removeItem:function(k){delete this._d[k];}
  },
  getSelection: function(){ return null; },
  navigator: { userAgent:'Mozilla/5.0 (pseudo-DOM)', language:'zh-CN', clipboard:{writeText:function(){return Promise.resolve();}} },
  history: { pushState:function(){}, replaceState:function(){}, back:function(){} },
  btoa: function(s){ return Buffer.from(s,'latin1').toString('base64'); },
  atob: function(s){ return Buffer.from(s,'base64').toString('latin1'); },
  matchMedia: function(){ return { matches:false, addListener:function(){} }; },
  setTimeout: setTimeout, clearTimeout: clearTimeout,
  setInterval: setInterval, clearInterval: clearInterval,
  Promise: Promise
};
var document = {
  getElementById: function(id){
    switch(id){
      case 'sidebar-menu': case 'sidebar': return __sidebar;
      case 'content': case 'module-content': case 'main-content': case 'app-content': case 'content-area': case 'content-main': return __content;
      case 'scan-bar': case 'scanInput': case 'scan-bar-input': case 'scanInputField': return __scan;
      case 'login-box': case 'loginBox': case 'loginContainer': return __loginBox;
      case 'main-app': case 'app': case 'mainApp': case 'appBox': case 'app-container': return __appBox;
      case 'header-username': case 'user-info': case 'current-user': return __headerUsr;
      case 'toast-area': case 'toastArea': case 'toasts': return __toastArea;
      default: return null;
    }
  },
  querySelector: function(sel){
    if (!sel) return null;
    var s = String(sel);
    // 精确匹配按钮
    var mb = s.match(/button\[data-module\s*=\s*["']([^"']+)["']/);
    if (mb) {
      var fb = __buttons.filter(function(b){return b.dataset.module===mb[1];});
      if (fb.length) return fb[0];
    }
    if (/\.sidebar-menu|#sidebar-menu/.test(s)) return __sidebar;
    if (/#content|\.content-area|#module-content|#main-content/.test(s)) return __content;
    if (/#login-box|#loginBox/.test(s)) return __loginBox;
    if (/#main-app|#appBox|#app-container/.test(s)) return __appBox;
    // 选择器 "button.active" 等简单匹配
    if (s==='button.active' || s==='.sidebar-menu button.active') {
      var act = __buttons.filter(function(b){return b._hl;});
      return act[0] || null;
    }
    return null;
  },
  querySelectorAll: function(sel){
    if (!sel) return [];
    var s = String(sel);
    if (/button\[data-module|\.sidebar-menu\s+button|#sidebar-menu\s+button|button\.active|\s+button\s*$/i.test(s)) return __buttons.slice();
    if (/\.sidebar-menu|#sidebar-menu/.test(s)) return [__sidebar];
    if (/\.sidebar-menu\s*li|#sidebar-menu\s*li/i.test(s)) return __ulList.slice();
    return [];
  },
  addEventListener: function(){},
  body: {
    innerHTML: '',
    appendChild:function(){},
    classList: {add(){},remove(){},contains(){return false;}},
    style: {},
    querySelector: function(){return null;},
    querySelectorAll: function(){return [];}
  },
  documentElement: { classList: {add(){},remove(){},contains(){return false;}}, style:{}, scrollTop:0 },
  head: { innerHTML:'', appendChild:function(){} },
  createElement: function(tag){
    tag = String(tag||'').toLowerCase();
    if (tag==='button') return mkButton('');
    var el = {
      tagName: tag.toUpperCase(),
      dataset: {},
      innerHTML: '', innerText:'', textContent:'', value:'', id:'', name:'', type:'text',
      style: {},
      checked: false, disabled: false,
      _attrs: {},
      addEventListener: function(){}, removeEventListener: function(){},
      appendChild: function(){}, removeChild: function(){},
      getAttribute: function(k){return this._attrs[k]===undefined?null:this._attrs[k];},
      setAttribute: function(k,v){this._attrs[k]=String(v);},
      hasAttribute: function(k){return this.getAttribute(k)!==null;},
      removeAttribute: function(k){delete this._attrs[k];},
      classList: {add(){},remove(){},contains(){return false;}, toggle(){}},
      matches: function(){return false;},
      focus: function(){}, blur: function(){},
      click: function(){}, submit: function(){},
      files: [], options: [], selectedIndex: -1
    };
    return el;
  },
  createTextNode: function(t){ return { nodeValue: t, textContent: String(t) }; },
  createDocumentFragment: function(){ return { appendChild:function(){}, children:[] }; },
  cookie: '',
  title: 'ERP',
  readyState: 'complete'
};
var localStorage = window.localStorage;
var sessionStorage = localStorage;
var console = { log:function(){}, warn:function(){}, error:function(){}, info:function(){}, debug:function(){} };

// ============== 网络 / 第三方库 stub ==============
var fetch = function(url, opt){
  // 模拟 fetch 返回 JSON
  var path = String(url);
  var retData = { success: true, data: {} };
  if (path.indexOf('product-catalog')>=0) retData.data = [];
  if (path.indexOf('forecast-orders')>=0) retData.data = { items:[], total:0 };
  if (path.indexOf('purchase-requests')>=0) retData.data = { items:[], total:0 };
  if (path.endsWith('/materials/') || path.endsWith('/materials')) retData.data = { items:[], total:0 };
  if (path.indexOf('balance-sheet')>=0) retData.data = {};
  if (path.indexOf('materials/')>=0 && path.indexOf('catalog')===-1 && path.indexOf('product')===-1) retData.data = { items:[], total:0 };
  return Promise.resolve({
    ok: true, status: 200,
    json: function(){ return Promise.resolve(retData); },
    text: function(){ return Promise.resolve('<div class="dashboard"><div class="module-header"><h2>仪表盘</h2></div></div>'); }
  });
};
var $ = function(sel){
  return {
    0: null, length: 0, selector: sel,
    on:function(ev, cb){return this;}, off:function(){return this;},
    one:function(){return this;}, trigger:function(){return this;},
    click:function(cb){return this;}, change:function(){return this;},
    submit:function(){return this;}, collapse:function(a){return this;},
    addClass:function(c){return this;}, removeClass:function(c){return this;}, toggleClass:function(){return this;},
    tab:function(){return this;}, modal:function(a){return this;},
    show:function(){return this;}, hide:function(){return this;},
    html:function(h){return this;}, text:function(t){return this;},
    val:function(v){return (v===undefined)?'':this;},
    attr:function(k,v){return (v===undefined)?null:this;},
    data:function(k,v){return (v===undefined)?null:this;},
    prop:function(k,v){return (v===undefined)?false:this;},
    append:function(){return this;}, prepend:function(){return this;},
    empty:function(){return this;}, remove:function(){return this;},
    find:function(s){return $(s);},
    parent:function(){return $();},
    closest:function(s){return $();},
    serialize:function(){return '';}, serializeArray:function(){return [];},
    serializeObject:function(){return {};},
    ajaxSubmit:function(){return this;},
    each:function(fn){return this;},
    fadeIn:function(){return this;}, fadeOut:function(){return this;}, slideDown:function(){return this;}, slideUp:function(){return this;},
    tooltip:function(){return this;}, popover:function(){return this;},
    dropdown:function(){return this;},
    toArray:function(){return [];}
  };
};
$.ajax = function(o){ return Promise.resolve({}); };
$.get = function(u,cb){ if (cb) cb({}); return Promise.resolve({}); };
$.post = function(u,d,cb){ if (typeof d==='function') { cb=d; } if (cb) cb({}); return Promise.resolve({}); };
$.getJSON = function(u,cb){ if (cb) cb({success:true,data:{}}); return Promise.resolve({}); };
$.param = function(){return '';};

var bootstrap = {
  Modal: function(el, opt){ this.show=function(){}; this.hide=function(){}; this.dispose=function(){}; this.handleUpdate=function(){}; },
  Tab: function(el){ this.show=function(){}; this.dispose=function(){}; },
  Tooltip: function(){}, Popover: function(){}, Dropdown: function(){}, Collapse: function(){}
};
var Chart = function(el, cfg){ this.destroy=function(){}; this.update=function(){}; this.resize=function(){}; this.setOption=function(){}; this.render=function(){}; };
var echarts = { init: function(el, t, cfg){ return { setOption:function(){}, dispose:function(){}, resize:function(){}, off:function(){}, on:function(){}, clear:function(){} }; }, connect:function(){}, dispose:function(){} };
var toastr = {
  _last: null,
  success:function(msg, t, o){ this._last = {type:'success',msg:msg}; return {}; },
  error:function(msg){ this._last = {type:'error',msg:msg}; return { }; },
  warning:function(msg){ this._last = {type:'warning',msg:msg}; return {}; },
  info:function(msg){ this._last = {type:'info',msg:msg}; return {}; },
  options:function(){}
};
var Swal = {
  fire: function(){
    var args = Array.prototype.slice.call(arguments);
    return Promise.resolve({ isConfirmed: true, isDenied:false, isDismissed:false, value: args[0] && (typeof args[0].input !== 'undefined') ? '' : args[2] || args[0] || '' });
  },
  mixin: function(){ return Swal; },
  close: function(){}
};
var hljs = { highlightElement:function(el){}, highlightAll:function(){} };
var QRCode = function(el, opt){ this.makeCode=function(txt){ this.__txt = String(txt); }; this.clear=function(){this.__txt='';}; };
var jsQR = function(imgdata, w, h, opts){ return null; };
var AMap = null;  // 高德地图 stub (如用到)
var BMap = null;

// ============== 注入修复后的前端 JS ==============
"""

# 把 combined_js 的 SyntaxError 修复合并进来
# 同时补全一个可能的缺口：后端给前端返回的 JSON 如果有 data/dashboard/stats 之类，fetch 已经 mock
sim_code = stub + "\n" + fixed_js + "\n"

sim_code += r"""
// ============== 模拟入口 ==============
(async function(){
  try {
    // 先执行 showMainApp （如果有），确保主 UI 已进入
    if (typeof showMainApp === 'function') {
      try { await showMainApp(); } catch(e){ /* 忽略 showMainApp 里的 UI stub 不完整问题 */ }
    }
    // 初始 active 清空
    __buttons.forEach(function(b){ b._hl = false; b._rm = []; b.classList.remove('active'); });
    await loadModule('dashboard');
    var states = __buttons.map(function(b){
      return {
        module: b.dataset.module,
        hl: b._hl,
        classAttr: (b._attrs && b._attrs['class']) || '',
        hasActiveContains: b.classList.contains('active')
      };
    });
    process.stdout.write('SIMRESULT=' + JSON.stringify({
      ok: true,
      dashActive: states[0].hl,
      dashContains: states[0].hasActiveContains,
      dashClass: states[0].classAttr,
      states: states
    }) + '\n');
  } catch (e) {
    process.stdout.write('SIMRESULT=' + JSON.stringify({
      ok: false, err: String(e),
      stack: String(e && e.stack || '').slice(0,700)
    }) + '\n');
  }
})();
"""

with open(SIM, 'w', encoding='utf-8') as f: f.write(sim_code)
print(f"生成 {SIM} ({len(sim_code)} chars)")

# node --check 先验证
print("\n[1/2] node --check 模拟脚本...")
rc = subprocess.run([NODE, '--check', SIM], capture_output=True, text=True, timeout=25)
if rc.returncode == 0:
    print("  PASS: 模拟脚本语法无错")
else:
    print("  FAIL: 模拟脚本仍有语法错:")
    for ln in rc.stderr.splitlines()[:15]: print("   >", ln)

print("\n[2/2] 运行模拟脚本...")
rs = subprocess.run([NODE, SIM], capture_output=True, text=True, timeout=30)
combined = rs.stdout + rs.stderr
mm = re.search(r'SIMRESULT=(\{.*\})', combined)
if mm:
    try:
        res = json.loads(mm.group(1))
        print("\n[模拟结果]")
        print(json.dumps(res, ensure_ascii=False, indent=2))
        if res.get('ok'):
            if res.get('dashActive') or res.get('dashContains'):
                print("\n✅ PASS: dashboard 侧边栏按钮 active 高亮逻辑正常")
            else:
                print("\n⚠️  WARN: 模拟执行无错，但 dashboard 未高亮。各按钮状态：")
                for b in res.get('states', []):
                    print(f"    module={b['module']:15s} hl={b['hl']} contains={b['hasActiveContains']} class={b['classAttr']!r}")
        else:
            print(f"\n❌ FAIL: loadModule 抛异常: {res.get('err')}")
            if res.get('stack'):
                print("   Stack 片段:", res['stack'][:600])
    except Exception as pe:
        print(f"模拟结果 JSON 失败: {pe}")
        print("RAW:", combined[:500])
else:
    print(f"无 SIMRESULT，rc={rs.returncode}")
    print("STDOUT 前600:", rs.stdout[:600])
    print("STDERR 前600:", rs.stderr[:600])
