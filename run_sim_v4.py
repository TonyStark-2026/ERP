# -*- coding: utf-8 -*-
"""v4: 给伪 button 补全 onclick 属性和 textContent，让高亮匹配逻辑命中"""
import os, re, json, tempfile, subprocess

NODE = r"c:\Users\ruancanling\Desktop\ERP VIBE CODING\tools\node.exe"
PROJ = r"c:\Users\ruancanling\Desktop\ERP VIBE CODING"
JS_FILE = os.path.join(tempfile.gettempdir(), 'inline_scripts.js')
with open(JS_FILE, encoding='utf-8') as f: combined_js = f.read()

fixed_js = combined_js.replace("createTmpMat(${idx})", "createTmpMat(idx)")
SIM = os.path.join(PROJ, "_sim_v4.js")

# 模块名 -> 中文标签 (textContent)
MOD_LABEL = {
    'dashboard':'仪表盘 / 概览', 'materials':'物料管理', 'plan':'计划管理 / 预测',
    'production':'生产管理', 'procurement':'采购管理 / 采购申请', 'finance':'财务管理',
    'report':'报表', 'system':'系统管理',
    'sales':'销售', 'purchase':'采购', 'crossborder':'跨境', 'scanning':'扫码录入',
    'invoice':'发票'
}

stub = r"""
function mkButton(mod){
  var label = """ + json.dumps(MOD_LABEL, ensure_ascii=False) + r"""[mod] || mod;
  var b = {
    dataset:{module:mod}, _hl:false, _rm:[],
    _attrs:{
      'data-module':mod,
      'type':'button',
      'class':'',
      'onclick':"loadModule('" + mod + "')"   // ← 高亮逻辑所需！
    },
    innerHTML:label, innerText:label, textContent:label,  // ← 高亮逻辑 textContent 分支备选
    id:'', name:''
  };
  b.getAttribute = function(k){
    if (k==='data-module') return b.dataset.module;
    if (k==='onclick') return b._attrs['onclick'] || null;
    return b._attrs[k] !== undefined ? b._attrs[k] : null;
  };
  b.setAttribute = function(k,v){ b._attrs[k]=v; };
  b.hasAttribute = function(k){ return b.getAttribute(k) !== null; };
  b.removeAttribute = function(k){ delete b._attrs[k]; };
  b.addEventListener = function(){}; b.removeEventListener = function(){};
  b.click = function(){};
  b.matches = function(sel){
    if(!sel) return false;
    if(sel.indexOf('button')>=0){
      if(sel.indexOf('active')>=0) return b._hl;
      if(sel.indexOf('data-module')>=0 && sel.indexOf(mod)>=0) return true;
      return true;
    }
    return false;
  };
  b.classList = {
    add: function(c){
      if (c==='active') b._hl = true;
      var parts=(b._attrs['class']||'').split(/\s+/).filter(Boolean);
      if (parts.indexOf(c)===-1) parts.push(c); b._attrs['class']=parts.join(' ');
    },
    remove: function(c){
      b._rm.push(c);
      var parts=(b._attrs['class']||'').split(/\s+/).filter(Boolean);
      b._attrs['class']=parts.filter(function(x){return x!==c;}).join(' ');
    },
    contains: function(c){
      if (c==='active') return b._hl;
      return ((b._attrs['class']||'').split(/\s+/).indexOf(c) !== -1);
    },
    toggle: function(c){ this.contains(c)? this.remove(c):this.add(c); }
  };
  return b;
}
var __buttons = [mkButton('dashboard'),mkButton('materials'),mkButton('plan'),mkButton('production'),mkButton('procurement'),mkButton('finance'),mkButton('report'),mkButton('system')];
var __ulList = __buttons.map(function(b){
  var li = {
    dataset:{}, classList:{add(){},remove(){},contains(){return false;}},
    appendChild:function(){}, querySelector:function(s){if (s==='button') return b; return null;}
  };
  b.parentElement = li; return li;
});
var __sidebar = {
  querySelectorAll: function(sel){
    if(!sel) return [];
    var s = String(sel);
    var m = s.match(/button\[data-module[^\]]*=["']?([^"'\]]+)/i);
    if (m) { var f = __buttons.filter(function(b){return b.dataset.module===m[1];}); if(f.length) return f; }
    if (/\.sidebar-menu\s*button|#sidebar-menu\s*button/i.test(s)) return __buttons.slice();
    if (/button/i.test(s) && s.indexOf('active')===-1) return __buttons.slice();
    if (/li/i.test(s) && /sidebar/.test(s)) return __ulList.slice();
    if (/\.sidebar-menu|#sidebar-menu/.test(s)) return [__sidebar];
    return [];
  },
  querySelector: function(sel){ return (__sidebar.querySelectorAll(sel)||[])[0] || null; },
  addEventListener: function(){}, classList:{add(){},remove(){},contains(){return false;}}, innerHTML:''
};
var __content = {
  innerHTML:'', appendChild:function(){}, classList:{add(){},remove(){},contains(){return false;}},
  querySelectorAll:function(){return [];}, querySelector:function(){return null;}, addEventListener:function(){}
};
var __scan = { addEventListener:function(){}, focus:function(){}, blur:function(){}, value:'', classList:{add(){},remove(){},contains(){return false;}} };

var __loginBox = { _hidden:false, style:{display:''}, innerHTML:'' };
__loginBox.classList = {
  add:function(c){ if (c==='d-none'||c==='hidden') __loginBox._hidden=true; },
  remove:function(c){ if (c==='d-none'||c==='hidden') __loginBox._hidden=false; },
  contains:function(c){ return (c==='d-none'||c==='hidden') ? !!__loginBox._hidden : false; }
};
var __appBox = { _hidden:false, style:{display:''}, innerHTML:'' };
__appBox.classList = {
  add:function(c){ if (c==='d-none'||c==='hidden') __appBox._hidden=true; },
  remove:function(c){ if (c==='d-none'||c==='hidden') __appBox._hidden=false; },
  contains:function(c){ return (c==='d-none'||c==='hidden') ? !!__appBox._hidden : false; }
};
var __headerUsr = { textContent:'', innerText:'', classList:{add(){},remove(){},contains(){return false;}} };
var __toastArea = { innerHTML:'' };

var window = {
  addEventListener: function(){},
  location: { hash:'', href:'http://127.0.0.1:8000/', pathname:'/', search:'' },
  localStorage: {
    _d:{lang:'zh'},
    getItem:function(k){return this._d[k]===undefined?null:this._d[k];},
    setItem:function(k,v){this._d[k]=String(v);},
    removeItem:function(k){delete this._d[k];}
  },
  navigator: { userAgent:'pseudo-DOM', language:'zh-CN', clipboard:{writeText:function(){return Promise.resolve();}} },
  history: { pushState:function(){}, replaceState:function(){}, back:function(){} },
  setTimeout: setTimeout, clearTimeout: clearTimeout,
  setInterval: setInterval, clearInterval: clearInterval,
  Promise: Promise,
  getSelection: function(){return null;}
};
var localStorage = window.localStorage; var sessionStorage = localStorage;
var document = {
  getElementById: function(id){
    switch(id){
      case 'sidebar-menu': case 'sidebar': return __sidebar;
      case 'content': case 'module-content': case 'main-content': case 'app-content': case 'content-area': return __content;
      case 'scan-bar': case 'scanInput': case 'scan-bar-input': return __scan;
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
    var mb = s.match(/button\[data-module\s*=\s*["']([^"']+)["']/);
    if (mb) { for (var i=0;i<__buttons.length;i++) if (__buttons[i].dataset.module===mb[1]) return __buttons[i]; }
    if (/\.sidebar-menu|#sidebar-menu/.test(s)) return __sidebar;
    if (/#content|\.content-area|#module-content|#main-content/.test(s)) return __content;
    if (/#login-box|#loginBox/.test(s)) return __loginBox;
    if (/#main-app|#appBox|#app-container/.test(s)) return __appBox;
    if (s==='button.active' || s==='.sidebar-menu button.active') {
      for(var j=0;j<__buttons.length;j++) if (__buttons[j]._hl) return __buttons[j]; return null;
    }
    return null;
  },
  querySelectorAll: function(sel){
    if (!sel) return [];
    var s = String(sel);
    if (/\.sidebar-menu\s*button|#sidebar-menu\s*button|button\[data-module|button\.active/i.test(s)) return __buttons.slice();
    if (/button/i.test(s)) return __buttons.slice();
    if (/\.sidebar-menu|#sidebar-menu/.test(s)) return [__sidebar];
    if (/li/i.test(s) && /sidebar/.test(s)) return __ulList.slice();
    return [];
  },
  addEventListener: function(){},
  body: { innerHTML:'', appendChild:function(){}, classList:{add(){},remove(){},contains(){return false;}}, style:{}, querySelector:function(){return null;}, querySelectorAll:function(){return [];} },
  documentElement: { classList:{add(){},remove(){},contains(){return false;}}, style:{}, scrollTop:0 },
  head: { innerHTML:'', appendChild:function(){} },
  createElement: function(tag){
    tag = String(tag||'').toLowerCase();
    if (tag==='button') return mkButton('');
    var el = {
      tagName: tag.toUpperCase(), dataset:{}, innerHTML:'', innerText:'', textContent:'', value:'', id:'', name:'', type:'text',
      style:{}, checked:false, disabled:false, files:[], options:[], selectedIndex:-1, _attrs:{},
      addEventListener:function(){}, removeEventListener:function(){},
      appendChild:function(){}, removeChild:function(){}, insertBefore:function(){},
      getAttribute:function(k){return this._attrs[k]===undefined?null:this._attrs[k];},
      setAttribute:function(k,v){this._attrs[k]=String(v);},
      hasAttribute:function(k){return this.getAttribute(k)!==null;},
      removeAttribute:function(k){delete this._attrs[k];},
      classList:{add(){},remove(){},contains(){return false;}, toggle(){}},
      matches:function(){return false;}, focus:function(){}, blur:function(){}, click:function(){}, submit:function(){}
    };
    return el;
  },
  createTextNode: function(t){return {nodeValue:t, textContent:String(t)};},
  createDocumentFragment: function(){return {appendChild:function(){}, children:[]};},
  cookie:'', title:'ERP', readyState:'complete'
};
var console = {log:function(){},warn:function(){},error:function(){},info:function(){},debug:function(){}};

var fetch = function(url, opt){
  var path = String(url);
  var ret = { success:true, data:{} };
  if (path.indexOf('product-catalog')>=0) ret.data=[];
  if (path.indexOf('forecast-orders')>=0 || path.indexOf('purchase-requests')>=0) ret.data={items:[],total:0};
  if (path.endsWith('/materials/') || path.endsWith('/materials')) ret.data={items:[],total:0};
  if (path.indexOf('materials/')>=0) ret.data={items:[],total:0};
  if (path.indexOf('balance-sheet')>=0) ret.data={};
  if (path.indexOf('dashboard')>=0) ret.data={stats:{}};
  return Promise.resolve({ok:true,status:200,json:function(){return Promise.resolve(ret);},text:function(){return Promise.resolve('<div>Dashboard mock HTML</div>');}});
};
var $ = function(sel){
  return {0:null,length:0,selector:sel,
    on:function(){return this;},off:function(){return this;},one:function(){return this;},trigger:function(){return this;},
    click:function(){return this;},change:function(){return this;},submit:function(){return this;},collapse:function(){return this;},
    addClass:function(){return this;},removeClass:function(){return this;},toggleClass:function(){return this;},
    tab:function(){return this;},modal:function(){return this;},tooltip:function(){return this;},popover:function(){return this;},dropdown:function(){return this;},
    show:function(){return this;},hide:function(){return this;},fadeIn:function(){return this;},fadeOut:function(){return this;},slideDown:function(){return this;},slideUp:function(){return this;},
    html:function(){return this;},text:function(){return this;},append:function(){return this;},prepend:function(){return this;},empty:function(){return this;},remove:function(){return this;},
    val:function(){return '';},attr:function(){return null;},data:function(){return null;},prop:function(){return false;},
    find:function(s){return $(s);},parent:function(){return $();},closest:function(){return $();},
    serialize:function(){return '';},serializeArray:function(){return [];},each:function(){return this;},
    ajaxSubmit:function(){return this;}, toArray:function(){return [];}
  };
};
$.ajax=function(){return Promise.resolve({});};
$.get=function(u,cb){if (cb) cb({}); return Promise.resolve({});};
$.post=function(u,d,cb){if (typeof d==='function') cb=d; if (cb) cb({}); return Promise.resolve({});};
$.getJSON=function(u,cb){if (cb) cb({success:true,data:{}}); return Promise.resolve({});};
$.param=function(){return '';};

var bootstrap = {
  Modal: function(){this.show=function(){};this.hide=function(){};this.dispose=function(){};this.handleUpdate=function(){};},
  Tab: function(){this.show=function(){};this.dispose=function(){};},
  Tooltip:function(){},Popover:function(){},Dropdown:function(){},Collapse:function(){}
};
var Chart = function(){this.destroy=function(){};this.update=function(){};this.resize=function(){};this.setOption=function(){};};
var echarts = {init:function(){return {setOption:function(){},dispose:function(){},resize:function(){},off:function(){},on:function(){},clear:function(){}};},connect:function(){},dispose:function(){}};
var toastr = {success:function(){return {};},error:function(){return {};},warning:function(){return {};},info:function(){return {};},options:function(){}};
var Swal = {fire:function(){return Promise.resolve({isConfirmed:true,isDenied:false,isDismissed:false,value:''});},mixin:function(){return Swal;},close:function(){}};
var hljs = {highlightElement:function(){},highlightAll:function(){}};
var QRCode = function(){this.makeCode=function(t){this.__t=String(t);};this.clear=function(){this.__t='';};};
var jsQR = function(){return null;};
"""

sim_code = stub + "\n" + fixed_js + "\n"
sim_code += r"""
(async function(){
  try {
    if (typeof showMainApp === 'function') { try { await showMainApp(); } catch(e){ /* ignore */ } }
    // 重置
    __buttons.forEach(function(b){ b._hl=false; b._rm=[]; b._attrs['class']=''; });
    await loadModule('dashboard');
    var states = __buttons.map(function(b){
      return {
        module: b.dataset.module,
        hl: b._hl,
        classAttr: b._attrs['class'] || '',
        contains: b.classList.contains('active'),
        onclickAttr: b.getAttribute('onclick'),
        textContent: (b.textContent||'').slice(0,20)
      };
    });
    process.stdout.write('SIMRESULT=' + JSON.stringify({
      ok:true, dashActive:states[0].hl, dashContains:states[0].contains,
      dashClass:states[0].classAttr, dashOnclick:states[0].onclickAttr, states:states
    }) + '\n');
  } catch (e) {
    process.stdout.write('SIMRESULT=' + JSON.stringify({
      ok:false, err:String(e), stack:String(e && e.stack||'').slice(0,700)
    }) + '\n');
  }
})();
"""

with open(SIM, 'w', encoding='utf-8') as f: f.write(sim_code)
print(f"[SIM] {SIM} ({len(sim_code)} chars)")

r1 = subprocess.run([NODE, '--check', SIM], capture_output=True, text=True, timeout=25)
print(f"[语法] node --check rc={r1.returncode}")
if r1.returncode != 0:
    for ln in r1.stderr.splitlines()[:12]: print("  >", ln)

r2 = subprocess.run([NODE, SIM], capture_output=True, text=True, timeout=30)
combined = r2.stdout + r2.stderr
mm = re.search(r'SIMRESULT=(\{.*\})', combined)
if mm:
    try:
        r = json.loads(mm.group(1))
        print("\n[模拟结果]")
        print(json.dumps(r, ensure_ascii=False, indent=2))
        if r.get('ok'):
            if r.get('dashActive') or r.get('dashContains'):
                print("\n✅ PASS: dashboard 侧边按钮高亮成功 (active class 命中)")
            else:
                print("\n⚠️  WARN: dashboard 仍未高亮")
                print(f"   调试: dashOnclick={r.get('dashOnclick')!r}")
                print(f"   调试: dashClass={r.get('dashClass')!r}")
                # 打印每个按钮状态
                for b in r.get('states',[]):
                    mark = '*' if b['hl'] else ' '
                    print(f"   {mark} module={b['module']:15s} hl={b['hl']} onclick={b['onclickAttr']!r}  class={b['classAttr']!r}")
        else:
            print(f"\n❌ FAIL: {r.get('err')}")
            if r.get('stack'): print("   Stack:", r['stack'][:600])
    except Exception as pe:
        print("parse fail:", pe)
        print("RAW:", combined[:400])
else:
    print(f"no SIMRESULT rc={r2.returncode}")
    print("STDOUT:", r2.stdout[:500])
    print("STDERR:", r2.stderr[:500])
