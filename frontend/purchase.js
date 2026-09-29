/* ============================================================
 * 采购管理 V2 前端模块
 * 独立文件，通过 <script src> 引入 index.html
 * ============================================================ */

// 安全兜底：确保escapeHtml存在（apiBase和authHeaders由index.html的const声明提供）
if (typeof escapeHtml === 'undefined') {
    window.escapeHtml = function(s) {
        if (!s) return '';
        var d = document.createElement('div');
        d.textContent = String(s);
        return d.innerHTML;
    };
}

var _purchaseTab = 'overview';

function _renderPurchaseModule() {
    setTimeout(() => switchPurchaseTab('overview'), 80);
    return `
    <div style="padding:16px;">
        <div class="card">
            <div class="card-title" style="display:flex;justify-content:space-between;align-items:center;background:linear-gradient(135deg,#0ea5e9,#6366f1);color:#fff;border-radius:8px 8px 0 0;padding:12px 16px;margin:-16px -16px 12px -16px;">
                <span style="font-size:16px;font-weight:bold;">🛒 采购管理</span>
                <span style="font-size:12px;">连接生产计划与物料入库的核心枢纽</span>
            </div>
            <div style="padding:12px 16px;">
                <!-- Tab 导航 -->
                <div style="display:flex;gap:4px;border-bottom:2px solid #0ea5e9;margin-bottom:16px;flex-wrap:wrap;">
                    <button class="btn pur-tab-btn active" data-p-tab="overview" onclick="switchPurchaseTab('overview')">📊 流程概览</button>
                    <button class="btn pur-tab-btn" data-p-tab="suggestions" onclick="switchPurchaseTab('suggestions')">📋 采购建议</button>
                    <button class="btn pur-tab-btn" data-p-tab="suppliers" onclick="switchPurchaseTab('suppliers')">🏭 供应商管理</button>
                    <button class="btn pur-tab-btn" data-p-tab="orders" onclick="switchPurchaseTab('orders')">📑 采购订单</button>
                    <button class="btn pur-tab-btn" data-p-tab="contracts" onclick="switchPurchaseTab('contracts')">📜 采购合同</button>
                    <button class="btn pur-tab-btn" data-p-tab="tracking" onclick="switchPurchaseTab('tracking')">🔍 订单跟踪</button>
                    <button class="btn pur-tab-btn" data-p-tab="inbound" onclick="switchPurchaseTab('inbound')">📦 入库质检</button>
                    <button class="btn pur-tab-btn" data-p-tab="reports" onclick="switchPurchaseTab('reports')">📈 采购报表</button>
                    <button class="btn pur-tab-btn" data-p-tab="eoq" onclick="switchPurchaseTab('eoq')">🧮 最优批量计算</button>
                </div>

                <div id="pur-tab-overview" class="pur-tab-panel">${renderPurchaseOverview()}</div>
                <div id="pur-tab-suggestions" class="pur-tab-panel" style="display:none;"></div>
                <div id="pur-tab-suppliers" class="pur-tab-panel" style="display:none;"></div>
                <div id="pur-tab-orders" class="pur-tab-panel" style="display:none;"></div>
                <div id="pur-tab-contracts" class="pur-tab-panel" style="display:none;"></div>
                <div id="pur-tab-tracking" class="pur-tab-panel" style="display:none;"></div>
                <div id="pur-tab-inbound" class="pur-tab-panel" style="display:none;"></div>
                <div id="pur-tab-reports" class="pur-tab-panel" style="display:none;"></div>
                <div id="pur-tab-eoq" class="pur-tab-panel" style="display:none;"></div>
            </div>
        </div>
    </div>
    <style>
        .pur-tab-btn{padding:4px 12px;font-size:12px;border:1px solid #e5e7eb;background:#fff;color:#666;border-radius:6px;cursor:pointer;transition:all .2s;}
        .pur-tab-btn:hover{background:#eff6ff;border-color:#0ea5e9;}
        .pur-tab-btn.active{background:linear-gradient(135deg,#0ea5e9,#6366f1);color:#fff;border-color:transparent;}
        .pur-stat-card{background:linear-gradient(135deg,#f0f9ff,#e0f2fe);border:1px solid #bae6fd;border-radius:10px;padding:14px;text-align:center;}
        .pur-stat-card .num{font-size:24px;font-weight:bold;color:#0369a1;}
        .pur-stat-card .lbl{font-size:11px;color:#666;margin-top:4px;}
        .pur-process-node{display:flex;flex-direction:column;align-items:center;gap:4px;min-width:70px;}
        .pur-process-node .icon{width:48px;height:48px;border-radius:50%;background:linear-gradient(135deg,#0ea5e9,#6366f1);color:#fff;display:flex;align-items:center;justify-content:center;font-size:20px;box-shadow:0 4px 10px rgba(14,165,233,.3);}
        .pur-process-node .label{font-size:11px;color:#374151;font-weight:bold;text-align:center;}
        .pur-process-arrow{display:flex;align-items:center;color:#94a3b8;font-size:20px;font-weight:bold;}
    </style>`;
}

function switchPurchaseTab(tab) {
    _purchaseTab = tab;
    document.querySelectorAll('.pur-tab-btn').forEach(b => b.classList.toggle('active', b.getAttribute('data-p-tab') === tab));
    document.querySelectorAll('.pur-tab-panel').forEach(p => p.style.display = 'none');
    const map = { overview:'pur-tab-overview', suggestions:'pur-tab-suggestions', suppliers:'pur-tab-suppliers',
                  orders:'pur-tab-orders', contracts:'pur-tab-contracts', tracking:'pur-tab-tracking',
                  inbound:'pur-tab-inbound', reports:'pur-tab-reports', eoq:'pur-tab-eoq' };
    const el = document.getElementById(map[tab]);
    if (!el) return;
    el.style.display = 'block';
    if (tab === 'overview') initPurchaseOverviewStats();
    if (tab === 'suggestions') el.innerHTML = `<div style="color:#888;padding:30px;text-align:center;">加载中...</div>`, setTimeout(loadPurchaseSuggestions, 50);
    if (tab === 'suppliers') el.innerHTML = renderSuppliers(), setTimeout(loadSuppliers, 30);
    if (tab === 'orders') el.innerHTML = renderOrdersUI(), setTimeout(loadOrders, 30);
    if (tab === 'contracts') el.innerHTML = renderContractsUI(), setTimeout(loadContracts, 30);
    if (tab === 'tracking') el.innerHTML = renderTrackingUI(), setTimeout(loadTracking, 30);
    if (tab === 'inbound') el.innerHTML = renderInboundUI(), setTimeout(loadInbound, 30);
    if (tab === 'reports') el.innerHTML = renderReportsUI(), setTimeout(loadPurchaseReports, 30);
    if (tab === 'eoq') el.innerHTML = renderEoqCalculator(), setTimeout(initEoqCalculator, 30);
}

// ========== 概览（流程图） ==========
function renderPurchaseOverview() {
    return `
    <div style="margin-bottom:20px;">
        <div style="background:linear-gradient(135deg,#eff6ff,#e0e7ff);border-radius:12px;padding:20px;border:1px solid #c7d2fe;">
            <h3 style="margin:0 0 16px;color:#1e40af;text-align:center;font-size:15px;">🔄 采购业务流程图</h3>
            <div style="display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:6px;">
                <div class="pur-process-node" onclick="switchPurchaseTab('suggestions')" style="cursor:pointer;"><div class="icon">📊</div><div class="label">MRP运算</div></div>
                <div class="pur-process-arrow">→</div>
                <div class="pur-process-node" onclick="switchPurchaseTab('suggestions')" style="cursor:pointer;"><div class="icon">📋</div><div class="label">采购建议</div></div>
                <div class="pur-process-arrow">→</div>
                <div class="pur-process-node" onclick="switchPurchaseTab('orders')" style="cursor:pointer;"><div class="icon">💬</div><div class="label">询价比价</div></div>
                <div class="pur-process-arrow">→</div>
                <div class="pur-process-node" onclick="switchPurchaseTab('suppliers')" style="cursor:pointer;"><div class="icon">🏭</div><div class="label">供应商选定</div></div>
                <div class="pur-process-arrow">→</div>
                <div class="pur-process-node" onclick="switchPurchaseTab('orders')" style="cursor:pointer;"><div class="icon">📑</div><div class="label">采购订单</div></div>
            </div>
            <div style="display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:6px;margin-top:12px;">
                <div class="pur-process-node" onclick="switchPurchaseTab('tracking')" style="cursor:pointer;"><div class="icon">🔍</div><div class="label">订单跟踪</div></div>
                <div class="pur-process-arrow">→</div>
                <div class="pur-process-node" onclick="switchPurchaseTab('inbound')" style="cursor:pointer;"><div class="icon">📦</div><div class="label">扫码入库</div></div>
                <div class="pur-process-arrow">→</div>
                <div class="pur-process-node" onclick="switchPurchaseTab('inbound')" style="cursor:pointer;"><div class="icon">✅</div><div class="label">质检通过</div></div>
                <div class="pur-process-arrow">→</div>
                <div class="pur-process-node" onclick="switchPurchaseTab('contracts')" style="cursor:pointer;"><div class="icon">💰</div><div class="label">财务结算</div></div>
                <div class="pur-process-arrow">→</div>
                <div class="pur-process-node" onclick="switchPurchaseTab('reports')" style="cursor:pointer;"><div class="icon">📈</div><div class="label">成本分析</div></div>
            </div>
        </div>
    </div>
    <div style="background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin-bottom:20px;">
        <h3 style="margin:0 0 12px;color:#1e40af;font-size:14px;">📊 采购全流程进度</h3>
        <div style="display:flex;align-items:center;gap:12px;">
            <div style="flex:1;height:14px;background:#e5e7eb;border-radius:7px;overflow:hidden;">
                <div id="pur-progress-fill" style="height:100%;width:0%;background:#dc2626;border-radius:7px;transition:width .4s,background .4s;"></div>
            </div>
            <span id="pur-progress-pct" style="font-size:16px;font-weight:bold;color:#dc2626;min-width:56px;text-align:right;">0%</span>
        </div>
        <div id="pur-progress-sub" style="font-size:11px;color:#9ca3af;margin-top:4px;">整体到货达成率</div>
        <div id="pur-progress-stages" style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-top:14px;"></div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px;margin-bottom:20px;">
        <div class="pur-stat-card"><div class="num" id="stat-suggestion">-</div><div class="lbl">待处理采购建议</div></div>
        <div class="pur-stat-card"><div class="num" id="stat-po">-</div><div class="lbl">本月采购订单</div></div>
        <div class="pur-stat-card"><div class="num" id="stat-supplier">-</div><div class="lbl">已准入供应商</div></div>
        <div class="pur-stat-card"><div class="num" id="stat-inbound">-</div><div class="lbl">本月入库单数</div></div>
    </div>
    <div id="pur-overview-alerts" style="background:#fef3c7;border:1px solid #fcd34d;border-radius:8px;padding:12px;display:none;"></div>`;
}

function initPurchaseOverviewStats() {
    fetch(apiBase+'/pm/suggestions?status=PENDING',{headers:authHeaders}).then(r=>r.json()).then(d=>{
        const el = document.getElementById('stat-suggestion'); if(el) el.textContent=d?.data?.total||0;
    }).catch(()=>{});
    Promise.all([
        fetch(apiBase+'/pm/orders',{headers:authHeaders}).then(r=>r.json()).catch(()=>({})),
        fetch(apiBase+'/pm/order-tracking',{headers:authHeaders}).then(r=>r.json()).catch(()=>({})),
        fetch(apiBase+'/pm/inbounds',{headers:authHeaders}).then(r=>r.json()).catch(()=>({})),
        fetch(apiBase+'/pm/suppliers',{headers:authHeaders}).then(r=>r.json()).catch(()=>({}))
    ]).then(([od,td,id,sd])=>{
        const el = document.getElementById('stat-po'); if(el) el.textContent=(od?.data?.items||[]).length||0;
        const elS = document.getElementById('stat-supplier'); if(elS) elS.textContent=(sd?.data?.items||[]).length||0;
        const elI = document.getElementById('stat-inbound'); if(elI) elI.textContent=(id?.data?.items||[]).length||0;
        _renderPurOverallProgress(od?.data?.items||[], td?.data?.items||[], id?.data?.items||[]);
    });
}
function _renderPurOverallProgress(orders, trackings, inbounds){
    const poTotal = orders.length;
    const cnt = st => orders.filter(o=>o.status===st).length;
    const approved = cnt('APPROVED'), posted = cnt('POSTED'), closed = cnt('CLOSED');
    const totalQty = trackings.reduce((s,t)=>s+Number(t.total_qty||0),0);
    const recvQty = trackings.reduce((s,t)=>s+Number(t.received_qty||0),0);
    const rate = totalQty>0 ? Math.min(recvQty/totalQty*100, 100) : 0;
    const col = totalQty===0 ? '#9ca3af' : (rate>=100?'#16a34a':(rate>=80?'#f59e0b':'#dc2626'));
    const fill = document.getElementById('pur-progress-fill');
    const pct = document.getElementById('pur-progress-pct');
    if(fill){ fill.style.width = rate.toFixed(1)+'%'; fill.style.background = col; }
    if(pct){ pct.textContent = Math.round(rate)+'%'; pct.style.color = col; }
    const sub = document.getElementById('pur-progress-sub');
    if(sub) sub.textContent = totalQty>0 ? `整体到货达成率：已到货 ${recvQty} / 应到货 ${totalQty} 件` : '暂无采购订单数据，创建订单后自动计算进度';
    const stages = [
        {icon:'📋', label:'待处理建议', n:0, tab:'suggestions'},
        {icon:'📑', label:'全部订单', n:poTotal, tab:'orders'},
        {icon:'📝', label:'待审核草稿', n:cnt('DRAFT'), tab:'orders'},
        {icon:'✅', label:'已审核在途', n:approved, tab:'tracking'},
        {icon:'📦', label:'已入库', n:inbounds.filter(i=>i.status==='POSTED').length, tab:'inbound'},
        {icon:'💰', label:'已关闭', n:closed, tab:'orders'}
    ];
    const sugEl = document.getElementById('stat-suggestion');
    const sugN = sugEl ? parseInt(sugEl.textContent)||0 : 0;
    stages[0].n = sugN;
    const stageEl = document.getElementById('pur-progress-stages');
    if(stageEl) stageEl.innerHTML = stages.map(s=>{
        const active = s.n>0;
        return `<div onclick="switchPurchaseTab('${s.tab}')" title="点击查看" style="cursor:pointer;background:${active?'linear-gradient(135deg,#f0f9ff,#e0f2fe)':'#f9fafb'};border:1px solid ${active?'#bae6fd':'#e5e7eb'};border-radius:10px;padding:8px 14px;text-align:center;min-width:96px;transition:transform .15s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform=''">
            <div style="font-size:18px;${active?'':'filter:grayscale(1);opacity:.45;'}">${s.icon}</div>
            <div style="font-size:17px;font-weight:bold;color:${active?'#0369a1':'#9ca3af'};">${s.n}</div>
            <div style="font-size:11px;color:#666;">${s.label}</div>
        </div>`;
    }).join('');
}

// ========== 采购建议 ==========
function loadPurchaseSuggestions() {
    const el = document.getElementById('pur-tab-suggestions');
    if (!el) return;
    el.innerHTML = `
        <div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;">
            <button class="btn btn-primary" onclick="generateMRPSuggestions()">🔄 运行MRP生成建议</button>
            <select id="pur-sug-status" onchange="loadPurchaseSuggestions()" style="padding:5px;border:1px solid #ccc;border-radius:4px;">
                <option value="">全部状态</option>
                <option value="PENDING" selected>待处理</option>
                <option value="CONVERTED">已转单</option>
            </select>
            <button class="btn btn-primary" onclick="batchConvertSelected()">📋 批量转采购订单</button>
        </div>
        <div id="pur-sug-list"><div style="color:#888;padding:20px;">加载中...</div></div>`;
    _loadSugList();
}
function _loadSugList() {
    const status = (document.getElementById('pur-sug-status')||{}).value||'';
    fetch(`${apiBase}/pm/suggestions?status=${status}`, {headers:authHeaders})
        .then(r=>r.json()).then(d=>{
            const el = document.getElementById('pur-sug-list');
            if(!el) return;
            const items = d?.data?.items||[];
            if(!items.length){ el.innerHTML='<div style="color:#999;padding:30px;text-align:center;">暂无采购建议，点击"运行MRP生成建议"创建</div>'; return; }
            el.innerHTML = `<table style="width:100%;border-collapse:collapse;font-size:12px;table-layout:fixed;">
                <thead><tr style="background:#f5f5f5;">
                    <th style="border:1px solid #d1d5db;padding:6px 8px;width:30px;"><input type="checkbox" id="sug-check-all" onchange="toggleAllSug(this)"></th>
                    <th style="border:1px solid #d1d5db;padding:6px 8px;width:110px;">建议编号</th>
                    <th style="border:1px solid #d1d5db;padding:6px 8px;width:100px;">需求来源</th>
                    <th style="border:1px solid #d1d5db;padding:6px 8px;width:140px;">物料编码/名称</th>
                    <th style="border:1px solid #d1d5db;padding:6px 8px;width:80px;">需求数量</th>
                    <th style="border:1px solid #d1d5db;padding:6px 8px;width:80px;">建议数量</th>
                    <th style="border:1px solid #d1d5db;padding:6px 8px;width:110px;">到货日期</th>
                    <th style="border:1px solid #d1d5db;padding:6px 8px;width:80px;">状态</th>
                    <th style="border:1px solid #d1d5db;padding:6px 8px;width:150px;">操作</th>
                </tr></thead>
                <tbody>${items.map(s=>`<tr>
                    <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">${s.status==='PENDING'?'<input type="checkbox" class="sug-check" data-sid="'+s.id+'">':''}</td>
                    <td style="border:1px solid #e5e7eb;padding:6px 8px;font-weight:bold;">${escapeHtml(s.suggestion_no)}</td>
                    <td style="border:1px solid #e5e7eb;padding:6px 8px;">${escapeHtml(s.source_type_label)}<br><span style="font-size:10px;color:#888;">${escapeHtml(s.source_no||'')}</span></td>
                    <td style="border:1px solid #e5e7eb;padding:6px 8px;">${escapeHtml(s.material_code)}<br>${escapeHtml(s.material_name)}</td>
                    <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:right;">${s.requested_qty}</td>
                    <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:right;font-weight:bold;color:#b45309;">${s.suggested_qty}</td>
                    <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">${s.expected_date}</td>
                    <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;"><span style="padding:2px 8px;border-radius:10px;font-size:10px;background:${s.status==='CONVERTED'?'#dcfce7;color:#16a34a':'#fef3c7;color:#b45309;'};">${s.status}</span></td>
                    <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">
                        ${s.status==='PENDING'?`<select id="sug-sel-${s.id}" style="padding:2px;border:1px solid #ccc;font-size:11px;"><option value="">选供应商</option></select><button class="btn btn-primary" style="padding:2px 6px;font-size:11px;" onclick="convertOneSuggestion(${s.id})">转单</button>`:'—'}
                    </td></tr>`).join('')}</tbody></table>`;
            fillSupplierSelects();
    });
}
function fillSupplierSelects(){
    fetch(apiBase+'/pm/suppliers',{headers:authHeaders}).then(r=>r.json()).then(d=>{
        const items = d?.data?.items||[];
        document.querySelectorAll('[id^=sug-sel-]').forEach(sel=>{
            sel.innerHTML = '<option value="">选供应商</option>' + items.map(s=>`<option value="${s.id}">${escapeHtml(s.name)}</option>`).join('');
        });
    });
}
function toggleAllSug(cb){ document.querySelectorAll('.sug-check').forEach(c=>c.checked=cb.checked); }
function generateMRPSuggestions(){
    fetch(apiBase+'/pm/suggestions/generate-mrp',{method:'POST',headers:authHeaders}).then(r=>r.json()).then(d=>{
        showToast(d.message||(d.success?'MRP运算完成':'运算失败'), d.success?'success':'error');
        if(d.success) loadPurchaseSuggestions();
    });
}
function convertOneSuggestion(sid){
    const sel = document.getElementById('sug-sel-'+sid);
    const supId = sel?.value;
    if(!supId){ showToast('请先选择供应商', 'warning'); return; }
    fetch(apiBase+'/pm/suggestions/'+sid+'/convert?supplier_id='+supId,{method:'POST',headers:authHeaders}).then(r=>r.json()).then(d=>{
        if(d.success){ showToast('已转采购订单：'+d.data.po_no, 'success'); loadPurchaseSuggestions(); }
        else showToast(d.message||'失败', 'error');
    });
}
function batchConvertSelected(){
    const checked = Array.from(document.querySelectorAll('.sug-check:checked')).map(c=>parseInt(c.dataset.sid));
    if(!checked.length){ showToast('请先勾选采购建议', 'warning'); return; }
    const supId = prompt('请输入批量转单的供应商ID（默认选第一个）:') || '';
    if(!supId){ showToast('需要供应商ID', 'warning'); return; }
    fetch(apiBase+'/pm/suggestions/batch-convert',{method:'POST',headers:authHeaders,body:JSON.stringify({ids:checked,supplier_id:parseInt(supId)})}).then(r=>r.json()).then(d=>{
        if(d.success){ showToast('已转单 '+d.data.converted+' 条', 'success'); loadPurchaseSuggestions(); }
    });
}

// ========== 供应商管理 ==========
function renderSuppliers(){ return `<div id="pur-suppliers"><div style="color:#888;padding:20px;">加载中...</div></div>`; }
function loadSuppliers(){
    fetch(apiBase+'/pm/suppliers',{headers:authHeaders}).then(r=>r.json()).then(d=>{
        var el = document.getElementById('pur-suppliers');
        if(!el) return;
        var items = (d && d.data && d.data.items) || [];
        var html = '';
        html += '<div style="display:flex;gap:8px;margin-bottom:12px;">';
        html += '<button class="btn btn-primary" onclick="showAddSupplier()">➕ 新增供应商</button>';
        html += '<button class="btn btn-secondary" onclick="window.open(apiBase+\'/pm/suppliers/export\')">📤 导出Excel</button>';
        html += '<input id="pur-sup-kw" type="text" placeholder="搜索供应商..." style="flex:1;padding:5px;border:1px solid #ccc;border-radius:4px;" onkeydown="if(event.key===\'Enter\')filterSuppliers()">';
        html += '<button class="btn btn-secondary" onclick="filterSuppliers()">🔍</button>';
        html += '</div>';
        html += '<table style="width:100%;border-collapse:collapse;font-size:12px;table-layout:fixed;">';
        html += '<thead><tr style="background:#f5f5f5;">';
        html += '<th style="border:1px solid #d1d5db;padding:6px 8px;width:90px;">编码</th>';
        html += '<th style="border:1px solid #d1d5db;padding:6px 8px;width:140px;">供应商名称</th>';
        html += '<th style="border:1px solid #d1d5db;padding:6px 8px;width:80px;">贸易类型</th>';
        html += '<th style="border:1px solid #d1d5db;padding:6px 8px;width:80px;">联系人</th>';
        html += '<th style="border:1px solid #d1d5db;padding:6px 8px;width:90px;">电话</th>';
        html += '<th style="border:1px solid #d1d5db;padding:6px 8px;width:120px;">邮箱</th>';
        html += '<th style="border:1px solid #d1d5db;padding:6px 8px;width:100px;">地址</th>';
        html += '<th style="border:1px solid #d1d5db;padding:6px 8px;width:80px;">准时率</th>';
        html += '<th style="border:1px solid #d1d5db;padding:6px 8px;width:80px;">合格率</th>';
        html += '<th style="border:1px solid #d1d5db;padding:6px 8px;width:170px;">供应物料</th>';
        html += '<th style="border:1px solid #d1d5db;padding:6px 8px;width:120px;">操作</th>';
        html += '</tr></thead><tbody>';
        items.forEach(function(s) {
            html += '<tr style="cursor:pointer;" ondblclick="viewSupplier(' + s.id + ')">';
            html += '<td style="border:1px solid #e5e7eb;padding:6px 8px;">' + escapeHtml(s.code) + '</td>';
            html += '<td style="border:1px solid #e5e7eb;padding:6px 8px;font-weight:bold;">' + escapeHtml(s.name) + '</td>';
            html += '<td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">' + (s.is_overseas ? '<span style="color:#0369a1;font-size:11px;">🌍 海外</span>' : '<span style="color:#64748b;font-size:11px;">🇨🇳 国内</span>') + '</td>';
            html += '<td style="border:1px solid #e5e7eb;padding:6px 8px;">' + escapeHtml(s.contact || '') + '</td>';
            html += '<td style="border:1px solid #e5e7eb;padding:6px 8px;">' + escapeHtml(s.phone || '') + '</td>';
            html += '<td style="border:1px solid #e5e7eb;padding:6px 8px;">' + escapeHtml(s.email || '') + '</td>';
            html += '<td style="border:1px solid #e5e7eb;padding:6px 8px;font-size:11px;">' + escapeHtml(s.address || '') + '</td>';
            var onTimeColor = s.on_time_rate > 90 ? '#059669' : (s.on_time_rate > 70 ? '#b45309' : '#dc2626');
            html += '<td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;color:' + onTimeColor + ';">' + (s.on_time_rate || 0) + '%</td>';
            var qualityColor = s.quality_rate > 90 ? '#059669' : '#dc2626';
            html += '<td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;color:' + qualityColor + ';">' + (s.quality_rate || 0) + '%</td>';
            var mats = s.materials || [];
            var matsShow = mats.length ? (mats.slice(0, 3).join('、') + (mats.length > 3 ? ' 等' + mats.length + '项' : '')) : '<span style="color:#cbd5e1;">暂无</span>';
            html += '<td style="border:1px solid #e5e7eb;padding:6px 8px;font-size:11px;">' + matsShow + '</td>';
            html += '<td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">';
            html += '<button class="btn btn-primary" style="padding:2px 6px;font-size:11px;" onclick="editSupplierInfo(' + s.id + ')" title="完善信息">✏</button>';
            html += '<button class="btn btn-secondary" style="padding:2px 6px;font-size:11px;margin-left:4px;" onclick="evaluateSupplier(' + s.id + ')">📝 评估</button>';
            html += '</td></tr>';
        });
        html += '</tbody></table>';
        el.innerHTML = html;
    });
}
function filterSuppliers(){ const kw=(document.getElementById('pur-sup-kw')?.value||'').toLowerCase(); if(!kw){ loadSuppliers(); return; }
    fetch(apiBase+'/pm/suppliers',{headers:authHeaders}).then(r=>r.json()).then(d=>{
        const items=(d?.data?.items||[]).filter(s=>(s.name||'').toLowerCase().includes(kw)||(s.code||'').toLowerCase().includes(kw));
        document.getElementById('pur-suppliers').innerHTML='<table style="width:100%;border-collapse:collapse;font-size:12px;">'+items.map(s=>'<tr><td>'+escapeHtml(s.code)+'</td><td>'+escapeHtml(s.name)+'</td></tr>').join('')+'</table>';
    }); }
let _supModal = null;
function showAddSupplier(){
    if (_supModal) _supModal.remove();
    _supModal = document.createElement('div');
    _supModal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    _supModal.innerHTML = `
        <div style="background:#fff;border-radius:12px;padding:24px;width:560px;max-width:95%;max-height:90vh;overflow-y:auto;">
            <h3 style="margin:0 0 16px 0;font-size:16px;">➕ 新增供应商</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
                <div><label style="font-size:12px;color:#666;">供应商名称 *</label><input id="sup-name" class="form-control" style="width:100%;" placeholder="如：某某机械有限公司"></div>
                <div><label style="font-size:12px;color:#666;">供应商编码 *</label><input id="sup-code" class="form-control" style="width:100%;" placeholder="如：S001"></div>
                <div><label style="font-size:12px;color:#666;">联系人</label><input id="sup-contact" class="form-control" style="width:100%;" placeholder="可选"></div>
                <div><label style="font-size:12px;color:#666;">电话</label><input id="sup-phone" class="form-control" style="width:100%;" placeholder="可选"></div>
                <div style="grid-column:1/3;"><label style="font-size:12px;color:#666;">地址</label><input id="sup-address" class="form-control" style="width:100%;" placeholder="可选"></div>
            </div>
            <div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:10px 12px;margin-bottom:16px;">
                <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:13px;color:#0369a1;">
                    <input type="checkbox" id="sup-overseas" style="width:16px;height:16px;">
                    🌍 海外贸易供应商（勾选后采购订单需填写贸易术语如FOB/CIF）
                </label>
            </div>
            <div style="display:flex;gap:8px;justify-content:flex-end;">
                <button class="btn btn-default" onclick="_supModal.remove()">取消</button>
                <button class="btn btn-primary" onclick="saveSupplier()">保存供应商</button>
            </div>
        </div>`;
    document.body.appendChild(_supModal);
    // 默认编码
    setTimeout(() => { const c=document.getElementById('sup-code'); if(c) c.value='S'+Date.now().toString().slice(-4); }, 50);
}
function saveSupplier(){
    const name=document.getElementById('sup-name').value.trim();
    const code=document.getElementById('sup-code').value.trim();
    if(!name){ showToast('请输入供应商名称', 'warning'); return; }
    if(!code){ showToast('请输入供应商编码', 'warning'); return; }
    const isOverseas=document.getElementById('sup-overseas').checked;
    const data={
        name:name, code:code,
        contact:document.getElementById('sup-contact').value||null,
        phone:document.getElementById('sup-phone').value||null,
        address:document.getElementById('sup-address').value||null,
        is_overseas:isOverseas,
        account_set_id:1
    };
    fetch('/api/v1/purchase/suppliers',{method:'POST',headers:authHeaders,body:JSON.stringify(data)}).then(r=>r.json()).then(d=>{
        if(d.success||d.id){
            showToast('✅ 供应商创建成功！' + (isOverseas?'\n🌍 已标记为海外贸易供应商':''), 'success', 5000);
            _supModal.remove();
            loadSuppliers();
        } else {
            showToast('创建失败：' + (d.message||JSON.stringify(d)), 'error');
        }
    }).catch(e=>showToast('请求失败：'+e, 'error'));
}
function viewSupplier(id){ window.open(apiBase+'/pm/suppliers/'+id+'/evaluation','_blank'); showToast('请在浏览器地址栏查看：/pm/suppliers/'+id+'/evaluation', 'warning'); }
// 编辑/完善供应商信息（大厅提醒入口、列表✏按钮共用）
function editSupplierInfo(id){
    fetch(apiBase+'/pm/suppliers',{headers:authHeaders}).then(r=>r.json()).then(d=>{
        const s=((d&&d.data&&d.data.items)||[]).find(x=>x.id===id);
        if(!s){ showToast('未找到该供应商','error'); return; }
        if(_supModal) _supModal.remove();
        _supModal=document.createElement('div');
        _supModal.style.cssText='position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
        _supModal.innerHTML=`
        <div style="background:#fff;border-radius:12px;padding:24px;width:560px;max-width:95%;max-height:90vh;overflow-y:auto;">
            <h3 style="margin:0 0 16px 0;font-size:16px;">✏ 完善供应商信息</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
                <div><label style="font-size:12px;color:#666;">供应商名称 *</label><input id="sup-name" class="form-control" style="width:100%;" value="${escapeHtml(s.name||'')}"></div>
                <div><label style="font-size:12px;color:#666;">供应商编码</label><input class="form-control" style="width:100%;background:#f5f5f5;" value="${escapeHtml(s.code||'')}" readonly></div>
                <div><label style="font-size:12px;color:#666;">联系人</label><input id="sup-contact" class="form-control" style="width:100%;" value="${escapeHtml(s.contact||'')}"></div>
                <div><label style="font-size:12px;color:#666;">电话</label><input id="sup-phone" class="form-control" style="width:100%;" value="${escapeHtml(s.phone||'')}"></div>
                <div><label style="font-size:12px;color:#666;">邮箱</label><input id="sup-email" class="form-control" style="width:100%;" value="${escapeHtml(s.email||'')}"></div>
                <div><label style="font-size:12px;color:#666;">地址</label><input id="sup-address" class="form-control" style="width:100%;" value="${escapeHtml(s.address||'')}"></div>
            </div>
            <div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:10px 12px;margin-bottom:16px;">
                <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:13px;color:#0369a1;">
                    <input type="checkbox" id="sup-overseas" style="width:16px;height:16px;" ${s.is_overseas?'checked':''}>
                    🌍 海外贸易供应商
                </label>
            </div>
            <div style="display:flex;gap:8px;justify-content:flex-end;">
                <button class="btn btn-default" onclick="_supModal.remove()">取消</button>
                <button class="btn btn-primary" onclick="updateSupplierInfo(${id})">保存</button>
            </div>
        </div>`;
        document.body.appendChild(_supModal);
    });
}
function updateSupplierInfo(id){
    const name=document.getElementById('sup-name').value.trim();
    if(!name){ showToast('请输入供应商名称','warning'); return; }
    const data={
        name:name,
        contact:document.getElementById('sup-contact').value.trim(),
        phone:document.getElementById('sup-phone').value.trim(),
        email:document.getElementById('sup-email').value.trim(),
        address:document.getElementById('sup-address').value.trim(),
        is_overseas:document.getElementById('sup-overseas').checked
    };
    fetch(apiBase+'/pm/suppliers/'+id,{method:'PUT',headers:Object.assign({'Content-Type':'application/json'},authHeaders),body:JSON.stringify(data)}).then(r=>r.json()).then(d=>{
        if(d.success){ showToast('✅ 供应商信息已保存','success'); if(typeof _supModal!=='undefined' && _supModal) _supModal.remove(); loadSuppliers(); }
        else showToast('保存失败：'+(d.message||''),'error');
    }).catch(e=>showToast('请求失败：'+e,'error'));
}
function evaluateSupplier(id){
    const price=prompt('价格评分(1-5):','3'); if(!price) return;
    const ontime=prompt('交期评分(1-5):','3'); if(!ontime) return;
    const quality=prompt('质量评分(1-5):','3'); if(!quality) return;
    const coop=prompt('配合度评分(1-5):','3'); if(!coop) return;
    fetch(apiBase+'/pm/suppliers/'+id+'/evaluation',{method:'POST',headers:authHeaders,body:JSON.stringify({price_score:parseFloat(price),on_time_score:parseFloat(ontime),quality_score:parseFloat(quality),cooperation_score:parseFloat(coop)})}).then(r=>r.json()).then(d=>{
        showToast(d.message||('综合评分：'+(d.data?.composite_score||0)+'  等级：'+(d.data?.rank_level||'')), 'success');
    });
}

// ========== 询价比价 ==========
function renderQuotationUI(){ return `<div id="pur-quot"><div style="color:#888;padding:20px;">加载中...</div></div>`; }
function loadQuotations(){
    fetch(apiBase+'/pm/quotations',{headers:authHeaders}).then(r=>r.json()).then(d=>{
        const el=document.getElementById('pur-quot'); if(!el) return;
        el.innerHTML=`<div style="display:flex;gap:8px;margin-bottom:12px;">
            <button class="btn btn-primary" onclick="showAddQuotation()">➕ 新建询价单</button>
            <select id="pur-qu-status" onchange="loadQuotations()" style="padding:5px;border:1px solid #ccc;"><option value="">全部</option><option>DRAFT</option><option>REPLIED</option><option>AWARDED</option></select>
        </div>
        <table style="width:100%;border-collapse:collapse;font-size:12px;">
            <thead><tr style="background:#f5f5f5;">
                <th style="border:1px solid #d1d5db;padding:6px 8px;">询价单号</th><th style="border:1px solid #d1d5db;padding:6px 8px;">物料</th>
                <th style="border:1px solid #d1d5db;padding:6px 8px;">数量</th><th style="border:1px solid #d1d5db;padding:6px 8px;">回复数</th>
                <th style="border:1px solid #d1d5db;padding:6px 8px;">状态</th><th style="border:1px solid #d1d5db;padding:6px 8px;">操作</th>
            </tr></thead><tbody>${(d.data?.items||[]).map(q=>`<tr>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;">${escapeHtml(q.quotation_no)}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;">${escapeHtml(q.material_name)}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:right;">${q.quantity}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">${q.reply_count}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">${q.status}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">
                    <button class="btn btn-primary" style="padding:2px 6px;font-size:11px;" onclick="replyQuotation(${q.id})">录入回复</button>
                    <button class="btn btn-secondary" style="padding:2px 6px;font-size:11px;" onclick="awardQuotation(${q.id})">定标</button>
                </td></tr>`).join('')}</tbody></table>`;
    });
}
function showAddQuotation(){
    fetch(apiBase+'/materials',{headers:authHeaders}).then(r=>r.json()).then(d=>{
        const items=d.data?.items||[];
        const code=prompt('物料编码:'); const m=items.find(x=>x.code===code);
        if(!m){ showToast('物料不存在', 'warning'); return; }
        const qty=prompt('询价数量:','100'); if(!qty) return;
        const expDate=prompt('期望到货日期 (YYYY-MM-DD):','2026-09-30');
        fetch(apiBase+'/pm/quotations',{method:'POST',headers:authHeaders,body:JSON.stringify({material_id:m.id,material_spec:m.spec||'',quantity:parseFloat(qty),expected_date:expDate})}).then(r=>r.json()).then(d=>{
            showToast(d.message||(d.success?'询价单创建成功':'创建失败'), d.success?'success':'error'); if(d.success) loadQuotations();
        });
    });
}
function replyQuotation(qid){
    fetch(apiBase+'/pm/suppliers',{headers:authHeaders}).then(r=>r.json()).then(d=>{
        const items=d.data?.items||[];
        const supId=prompt('供应商ID (可用的：'+items.slice(0,3).map(s=>s.id+':'+s.name).join(', ')+'):');
        if(!supId) return;
        const price=prompt('报价单价:'); if(!price) return;
        const lead=prompt('交期(天):','7')||'7';
        fetch(apiBase+'/pm/quotations/'+qid+'/reply',{method:'POST',headers:authHeaders,body:JSON.stringify({supplier_id:parseInt(supId),unit_price:parseFloat(price),lead_time_days:parseInt(lead)})}).then(r=>r.json()).then(d=>{
            showToast(d.message||'已录入', 'success');
        });
    });
}
function awardQuotation(qid){
    fetch(apiBase+'/pm/quotations/'+qid,{headers:authHeaders}).then(r=>r.json()).then(d=>{
        // 简化：让用户选择一个回复
        if(!d.success){ showToast(d.message, 'error'); return; }
        showToast('请在数据库中选择回复ID进行定标（演示版本：默认第一个回复）', 'warning');
    });
}

// ========== 采购订单 ==========
function renderOrdersUI(){ return `<div id="pur-pool"></div><div id="pur-orders"><div style="color:#888;padding:20px;">加载中...</div></div>`; }
function loadOrders(){
    Promise.all([
        fetch(apiBase+'/pm/suppliers',{headers:authHeaders}).then(r=>r.json()).catch(()=>({})),
        fetch(apiBase+'/pm/order-tracking',{headers:authHeaders}).then(r=>r.json()).catch(()=>({}))
    ]).then(([sd,td])=>{
        window._supplierNames = (((sd||{}).data||{}).items||[]).map(s=>s.name).filter(Boolean);
        window._poTracking = {};
        (((td||{}).data||{}).items||[]).forEach(t=>{ if(t.po_no) window._poTracking[t.po_no]=t; });
        fetch(apiBase+'/pm/orders',{headers:authHeaders}).then(r=>r.json()).then(d=>{
            _renderOrdersBody(d);
        });
        loadPurchasePoolPanel();  // 采购需求池（迁自生产管理，采购订单页顶部）
    });
}
// ==================== 采购需求池（采购订单页顶部）====================
let _poolOpen = true;
async function loadPurchasePoolPanel(){
    const el=document.getElementById('pur-pool'); if(!el) return;
    el.innerHTML='<div style="text-align:center;color:#999;padding:14px;font-size:12px;">需求池加载中...</div>';
    try{
        const r=await fetch('/api/v1/eng/procurement/pool');
        const tasks=await r.json();
        if(!tasks||!tasks.length){ el.innerHTML='<div style="background:#f8fafc;border:1px dashed #d1d5db;border-radius:10px;padding:14px 18px;text-align:center;color:#9ca3af;font-size:12px;">🛒 采购需求池为空 — 生产/BOM下发的待采购物料会自动出现在这里</div>'; return; }
        const pending=tasks.reduce((n,t)=>n+(t.materials||[]).filter(m=>m.purchase_status==='PENDING').length,0);
        const bodyHtml=tasks.map(t=>{
            const stMap={'PROCUREMENT_DISPATCHED':['待采购','#fef3c7','#92400e'],'PURCHASING':['采购中','#dbeafe','#1e40af'],'COMPLETED':['已完成','#dcfce7','#166534']};
            const st=stMap[t.status]||[t.status,'#f3f4f6','#6b7280'];
            const rows=(t.materials||[]).map(m=>{
                const pMap={'PENDING':['⏳待采购','#fef3c7','#92400e'],'PURCHASING':['🔵采购中','#dbeafe','#1e40af'],'ARRIVED':['✅已到货','#dcfce7','#166534'],'CANCELLED':['✖已取消','#f3f4f6','#6b7280']};
                const ps=pMap[m.purchase_status]||[m.purchase_status,'#f3f4f6','#6b7280'];
                return `<tr style="border-bottom:1px solid #f3f4f6;">
                    <td style="padding:5px 8px;">${m.material_code||'-'}</td>
                    <td style="padding:5px 8px;font-weight:500;">${m.material_name}</td>
                    <td style="padding:5px 8px;color:#6b7280;">${m.specification||'-'}</td>
                    <td style="padding:5px 8px;text-align:right;">${m.quantity}</td>
                    <td style="padding:5px 8px;">${m.unit||''}</td>
                    <td style="padding:5px 8px;text-align:right;">${m.unit_price?'¥'+m.unit_price.toLocaleString():'-'}</td>
                    <td style="padding:5px 8px;text-align:center;"><span style="padding:2px 8px;border-radius:10px;font-size:10px;background:${ps[1]};color:${ps[2]};">${ps[0]}</span></td>
                </tr>`;}).join('');
            return `<div style="border:1px solid #e5e7eb;border-radius:8px;margin-bottom:8px;overflow:hidden;">
                <div style="display:flex;align-items:center;gap:10px;padding:8px 12px;background:#f8fafc;flex-wrap:wrap;">
                    <span style="font-weight:600;font-size:13px;">📁 ${t.project_name||'项目'}</span>
                    <span style="font-size:11px;color:#9ca3af;">${t.project_no||''}</span>
                    <span style="padding:2px 8px;border-radius:10px;font-size:10px;background:${st[1]};color:${st[2]};">${st[0]}</span>
                    <span style="font-size:11px;color:#6b7280;margin-left:auto;">物料 ${t.material_count} 项 · 预估 ¥${(t.total_amount||0).toLocaleString()}</span>
                </div>
                <table style="width:100%;border-collapse:collapse;font-size:11px;"><thead><tr style="background:#fbfcfe;color:#6b7280;">
                    <th style="padding:5px 8px;text-align:left;">物料编码</th><th style="padding:5px 8px;text-align:left;">物料名称</th><th style="padding:5px 8px;text-align:left;">规格</th><th style="padding:5px 8px;text-align:right;">数量</th><th style="padding:5px 8px;text-align:left;">单位</th><th style="padding:5px 8px;text-align:right;">单价</th><th style="padding:5px 8px;text-align:center;">状态</th>
                </tr></thead><tbody>${rows}</tbody></table>
            </div>`;}).join('');
        el.innerHTML=`
        <div style="background:#fff;border:1px solid #e5e7eb;border-left:4px solid #7c3aed;border-radius:10px;margin-bottom:16px;overflow:hidden;">
            <div onclick="_poolOpen=!_poolOpen;loadPurchasePoolPanel()" style="display:flex;align-items:center;gap:10px;padding:12px 16px;cursor:pointer;flex-wrap:wrap;">
                <span style="font-size:18px;">🛒</span>
                <span style="font-weight:bold;font-size:14px;color:#1f2937;">采购需求池</span>
                ${pending>0?`<span style="padding:2px 10px;border-radius:12px;font-size:11px;background:#fee2e2;color:#dc2626;font-weight:bold;">${pending} 项待采购</span>`:''}
                <span style="font-size:11px;color:#9ca3af;">共 ${tasks.length} 个需求任务</span>
                <span style="margin-left:auto;display:flex;gap:8px;align-items:center;">
                    ${pending>0?`<button class="btn btn-primary" style="padding:6px 14px;font-size:12px;" onclick="event.stopPropagation();purchaseAllPool()">🛒 全部采购</button>`:''}
                    <span style="font-size:11px;color:#9ca3af;">${_poolOpen?'收起 ▲':'展开 ▼'}</span>
                </span>
            </div>
            ${_poolOpen?`<div style="padding:0 16px 14px;">${bodyHtml}</div>`:''}
        </div>`;
    }catch(e){ el.innerHTML='<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:10px;padding:12px 18px;color:#dc2626;font-size:12px;">需求池加载失败：'+e.message+'</div>'; }
}
async function purchaseAllPool(){
    if(!confirm('把采购需求池中所有「待采购」物料一键转成采购订单？\n（按项目自动分单，生成待审核草稿，可在下方订单列表中处理）')) return;
    try{
        const r=await fetch('/api/v1/eng/procurement/purchase-all',{method:'POST',headers:Object.assign({'Content-Type':'application/json'},authHeaders)});
        const d=await r.json();
        if(d.success){
            const dd=d.data||{};
            showToast(`✅ 一键采购完成：${dd.items} 项物料已转 ${dd.orders} 张采购订单（${(dd.po_nos||[]).slice(0,2).join('、')}${(dd.po_nos||[]).length>2?' 等':''}）`,'success');
            loadPurchasePoolPanel();
            fetch(apiBase+'/pm/orders',{headers:authHeaders}).then(r=>r.json()).then(x=>_renderOrdersBody(x));
        } else showToast(d.message||'一键采购失败','warning');
    }catch(e){ showToast('请求失败：'+e.message,'error'); }
}
// 单笔订单四步进度：建单→供应商→审核→入库
function _poSteps(o){
    const trk = (window._poTracking||{})[o.po_no] || (window._poTracking||{})[o.order_no] || {};
    const steps = [
        {label:'建单', done:true},
        {label:'供应商', done: !!(o.supplier_name || (o.items||[]).every(i=>i.supplier_name) && (o.items||[]).length>0)},
        {label:'审核', done: o.status!=='DRAFT'},
        {label:'入库', done: o.status==='POSTED'||o.status==='CLOSED'}
    ];
    const doneCount = steps.filter(s=>s.done).length;
    return {steps:steps, doneCount:doneCount, trk:trk};
}
function _poMiniBar(o){
    const p = _poSteps(o);
    const rec = Number(p.trk.received_qty||0), tq = Number(p.trk.total_qty||0);
    const bar = p.steps.map((s,i)=>`<div title="${s.label}${s.done?' ✓':''}" style="flex:1;height:6px;border-radius:3px;background:${s.done?'#0ea5e9':(i===p.doneCount?'#fbbf24':'#e5e7eb')};"></div>`).join('');
    return `<div style="display:flex;align-items:center;gap:10px;padding:0 16px 8px 52px;">
        <div style="flex:1;display:flex;gap:3px;max-width:260px;">${bar}</div>
        <span style="font-size:11px;color:#6b7280;">${p.doneCount}/4 步${tq>0?` · 到货 ${rec}/${tq}`:''}</span>
    </div>`;
}
function _renderOrdersBody(d){
        const el=document.getElementById('pur-orders'); if(!el) return;
        const items=d.data?.items||[];
        window._projPoOpen = window._projPoOpen || {};
        const projPOs = items.filter(o=>o.project_id && o.remark==='BOM导入自动生成');
        const normal = items.filter(o=>!(o.project_id && o.remark==='BOM导入自动生成'));
        const projCard = o=>{
            const total = o.items.reduce((s,i)=>s+Number(i.amount||i.unit_price*i.quantity||0),0);
            const open = !!window._projPoOpen[o.id];
            const stMap = {DRAFT:['待确认','#6b7280','#f3f4f6'],APPROVED:['已审核','#d97706','#fef3c7'],POSTED:['已入库','#059669','#d1fae5'],CLOSED:['已关闭','#9ca3af','#f3f4f6']};
            const st = stMap[o.status]||[o.status,'#6b7280','#f3f4f6'];
            return `<div style="border:1px solid #e5e7eb;border-left:4px solid #2563eb;border-radius:10px;margin-bottom:10px;background:#fff;overflow:hidden;">
                <div onclick="toggleProjPo(${o.id})" style="display:flex;align-items:center;gap:12px;padding:12px 16px;cursor:pointer;flex-wrap:wrap;">
                    <div style="font-size:20px;">📁</div>
                    <div style="flex:1;min-width:200px;">
                        <div style="font-size:14px;font-weight:bold;color:#1f2937;">${escapeHtml(o.project_name||'项目')} <span style="color:#6b7280;font-weight:normal;font-size:12px;">${escapeHtml(o.project_no||'')}</span></div>
                        <div style="font-size:11px;color:#9ca3af;margin-top:2px;">单号 ${escapeHtml(o.order_no)} · ${o.items.length}项标准件 · ${o.supplier_name?('供应商：'+escapeHtml(o.supplier_name)):'供应商待定'}</div>
                    </div>
                    <span style="padding:3px 10px;border-radius:12px;font-size:11px;background:${st[2]};color:${st[1]};font-weight:bold;">${st[0]}</span>
                    <div style="font-size:15px;font-weight:bold;color:#b45309;">¥${total.toFixed(2)}</div>
                    <span style="font-size:11px;color:#2563eb;">${open?'收起 ▲':'标准件清单 ▼'}</span>
                </div>
                ${_poMiniBar(o)}
                ${open?`<div style="border-top:1px dashed #e5e7eb;background:#f8fafc;padding:10px 16px;">
                    ${o.status==='DRAFT'?`<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap;background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:8px 12px;">
                        <span style="font-size:12px;font-weight:bold;color:#1e40af;">🏢 选择供应商（整单）：</span>
                        <select id="po-sup-sel-${o.id}" style="padding:4px 6px;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;min-width:180px;">
                            <option value="">— 请选择 —</option>
                            ${(window._supplierNames||[]).map(n=>`<option value="${escapeHtml(n)}" ${o.supplier_name===n?'selected':''}>${escapeHtml(n)}</option>`).join('')}
                        </select>
                        <button class="btn btn-primary" style="padding:4px 12px;font-size:11px;" onclick="event.stopPropagation();assignProjPoSupplier(${o.id})">💾 绑定</button>
                        <span style="font-size:11px;color:#6b7280;">绑定后自动建档进供应商管理；每个零件还可单独指定不同供应商（下方清单内）</span>
                    </div>`:''}
                    ${o.status==='DRAFT'?'<div style="font-size:11px;color:#92400e;margin-bottom:6px;">💡 单价/供应商/交付日期均可直接输入，回车或点别处自动保存，金额与合计实时重算</div>':''}
                    <table style="width:100%;border-collapse:collapse;font-size:12px;background:#fff;">
                        <thead><tr style="background:#eef2ff;">
                            <th style="border:1px solid #e5e7eb;padding:5px 8px;">序号</th>
                            <th style="border:1px solid #e5e7eb;padding:5px 8px;">物料编码</th>
                            <th style="border:1px solid #e5e7eb;padding:5px 8px;">物料名称</th>
                            <th style="border:1px solid #e5e7eb;padding:5px 8px;">规格</th>
                            <th style="border:1px solid #e5e7eb;padding:5px 8px;">数量</th>
                            <th style="border:1px solid #e5e7eb;padding:5px 8px;">单位</th>
                            <th style="border:1px solid #e5e7eb;padding:5px 8px;">单价</th>
                            <th style="border:1px solid #e5e7eb;padding:5px 8px;">金额</th>
                            <th style="border:1px solid #e5e7eb;padding:5px 8px;">供应商</th>
                            <th style="border:1px solid #e5e7eb;padding:5px 8px;">交付日期</th>
                        </tr></thead>
                        <tbody>${o.items.map((i,idx)=>`<tr>
                            <td style="border:1px solid #e5e7eb;padding:5px 8px;text-align:center;">${idx+1}</td>
                            <td style="border:1px solid #e5e7eb;padding:5px 8px;font-family:monospace;">${escapeHtml(i.material_code||'-')}</td>
                            <td style="border:1px solid #e5e7eb;padding:5px 8px;font-weight:bold;">${escapeHtml(i.material_name||'-')}</td>
                            <td style="border:1px solid #e5e7eb;padding:5px 8px;color:#6b7280;">${escapeHtml(i.material_spec||'-')}</td>
                            <td style="border:1px solid #e5e7eb;padding:5px 8px;text-align:right;">${i.quantity}</td>
                            <td style="border:1px solid #e5e7eb;padding:5px 8px;text-align:center;">${escapeHtml(i.unit||'-')}</td>
                            <td style="border:1px solid #e5e7eb;padding:5px 8px;text-align:right;">${o.status==='DRAFT'
                                ? `<input type="number" min="0" step="0.01" value="${Number(i.unit_price||0).toFixed(2)}" onchange="updatePoItemPrice(${o.id},${i.id},this.value,'unit_price')" style="width:95px;padding:3px 6px;border:1px solid #cbd5e1;border-radius:4px;text-align:right;font-size:12px;">`
                                : `¥${Number(i.unit_price||0).toFixed(2)}`}</td>
                            <td style="border:1px solid #e5e7eb;padding:5px 8px;text-align:right;color:#b45309;">¥${Number(i.amount||(i.unit_price*i.quantity)).toFixed(2)}</td>
                            <td style="border:1px solid #e5e7eb;padding:5px 8px;">${o.status==='DRAFT'
                                ? `<input type="text" value="${escapeHtml(i.supplier_name||'')}" placeholder="供应商名称" onchange="updatePoItemPrice(${o.id},${i.id},this.value,'supplier_name')" style="width:130px;padding:3px 6px;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;">`
                                : escapeHtml(i.supplier_name||'-')}</td>
                            <td style="border:1px solid #e5e7eb;padding:5px 8px;">${o.status==='DRAFT'
                                ? `<input type="date" value="${escapeHtml(i.delivery_date||'')}" onchange="updatePoItemPrice(${o.id},${i.id},this.value,'delivery_date')" style="padding:3px 6px;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;">`
                                : escapeHtml(i.delivery_date||'-')}</td>
                        </tr>`).join('')}</tbody>
                        <tfoot><tr style="background:#fffbeb;font-weight:bold;">
                            <td colspan="6" style="border:1px solid #e5e7eb;padding:5px 8px;text-align:right;">合计</td>
                            <td colspan="4" style="border:1px solid #e5e7eb;padding:5px 8px;text-align:right;color:#b45309;">¥${total.toFixed(2)}</td>
                        </tr></tfoot>
                    </table>
                    <div style="margin-top:8px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">
                        <div style="display:flex;gap:6px;align-items:center;">
                            <button class="btn btn-secondary" style="padding:3px 10px;font-size:11px;" onclick="event.stopPropagation();exportPOExcel(${o.id})">📤 导出Excel</button>
                            <label class="btn btn-secondary" style="padding:3px 10px;font-size:11px;cursor:pointer;margin:0;">📥 导入Excel
                                <input type="file" accept=".xlsx,.xls" style="display:none;" onchange="importPOExcel(${o.id}, this)">
                            </label>
                            <span style="font-size:11px;color:#9ca3af;">导出后填单价/供应商/交付日期，再导入批量更新</span>
                        </div>
                        <div>
                            <button class="btn btn-secondary" style="padding:3px 10px;font-size:11px;" onclick="event.stopPropagation();viewOrderDetail(${o.id})">👁 完整详情</button>
                            ${o.status==='DRAFT'?'<button class="btn btn-primary" style="padding:3px 10px;font-size:11px;margin-left:6px;" onclick="event.stopPropagation();approvePO('+o.id+')">✅ 审核订单</button>':''}
                        </div>
                    </div>
                </div>`:''}
            </div>`;
        };
        el.innerHTML=`<div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;">
            <select id="pur-po-status" onchange="loadOrders()" style="padding:5px;border:1px solid #ccc;">
                <option value="">全部状态</option><option>DRAFT</option><option>APPROVED</option><option>POSTED</option><option>CLOSED</option>
            </select>
            <button class="btn btn-primary" style="padding:5px 12px;font-size:12px;" onclick="showPurchaseOrderForm()">➕ 新建采购订单</button>
            <span style="font-size:12px;color:#666;align-self:center;">共 ${items.length} 张订单（${projPOs.length} 张项目订单）</span>
        </div>
        ${projPOs.length?`<div style="margin-bottom:16px;">
            <div style="font-size:13px;font-weight:bold;color:#1e40af;margin-bottom:8px;">📁 项目标准件采购 <span style="color:#9ca3af;font-weight:normal;font-size:11px;">点击项目卡片展开标准件购买清单</span></div>
            ${projPOs.map(projCard).join('')}
        </div>`:''}
        ${normal.length?`<table style="width:100%;border-collapse:collapse;font-size:12px;">
            <thead><tr style="background:#f5f5f5;">
                <th style="border:1px solid #d1d5db;padding:6px 8px;">订单号</th><th style="border:1px solid #d1d5db;padding:6px 8px;">供应商</th>
                <th style="border:1px solid #d1d5db;padding:6px 8px;">物料/数量</th><th style="border:1px solid #d1d5db;padding:6px 8px;">金额</th>
                <th style="border:1px solid #d1d5db;padding:6px 8px;">进度</th>
                <th style="border:1px solid #d1d5db;padding:6px 8px;">状态</th><th style="border:1px solid #d1d5db;padding:6px 8px;">操作</th>
            </tr></thead><tbody>${normal.slice(0,50).map(o=>{
                const s = o.supplier || {};
                const its = o.items || [];
                const total = its.reduce((sum,i)=>sum+Number(i.unit_price||0)*Number(i.quantity||0),0);
                const trk = (window._poTracking||{})[o.po_no] || (window._poTracking||{})[o.order_no] || {};
                const tq = Number(trk.total_qty||0), rc = Number(trk.received_qty||0);
                const rate = tq>0 ? Math.min(rc/tq*100,100) : 0;
                const rateCol = tq===0 ? '#9ca3af' : (rate>=100?'#16a34a':(rate>=80?'#f59e0b':'#dc2626'));
                return `<tr ondblclick="viewOrderDetail(${o.id})">
                <td style="border:1px solid #e5e7eb;padding:6px 8px;font-weight:bold;">${escapeHtml(o.order_no||o.po_no||'')}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;">${escapeHtml(s.name||o.supplier_name||'')}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;font-size:11px;">${its.map(i=>`${escapeHtml(i.material_name||'物料')} × ${i.quantity}`).join(', ')}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:right;color:#b45309;font-weight:bold;">${total.toFixed(2)}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;min-width:110px;">
                    <div style="display:flex;align-items:center;gap:6px;">
                        <div style="flex:1;height:8px;background:#e5e7eb;border-radius:4px;overflow:hidden;min-width:56px;">
                            <div style="height:100%;width:${rate}%;background:${rateCol};border-radius:4px;"></div>
                        </div>
                        <span style="font-size:11px;color:${rateCol};min-width:36px;text-align:right;">${Math.round(rate)}%</span>
                    </div>
                </td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">${o.status||'—'}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">
                    <button class="btn btn-primary" style="padding:2px 6px;font-size:11px;" onclick="event.stopPropagation();viewOrderDetail(${o.id})">👁</button>
                    ${o.status==='DRAFT'?'<button class="btn btn-secondary" style="padding:2px 6px;font-size:11px;" onclick="event.stopPropagation();approvePO('+o.id+')">✅ 审核</button>':''}
                </td></tr>`;
            }).join('')}</tbody></table>`:''}`;
}
function toggleProjPo(id){
    window._projPoOpen[id] = !window._projPoOpen[id];
    loadOrders();
}
function exportPOExcel(oid){
    window.open(apiBase+'/pm/orders/'+oid+'/export', '_blank');
}
function importPOExcel(oid, input){
    const f = input.files[0];
    if (!f) return;
    const fd = new FormData();
    fd.append('file', f);
    fetch(apiBase+'/pm/orders/'+oid+'/import', { method:'POST', headers: authHeaders, body: fd })
        .then(r=>r.json()).then(d=>{
            let msg = d.message || (d.success ? '导入成功' : '导入失败');
            if (d.success && d.data && d.data.fail_rows && d.data.fail_rows.length) msg += '；' + d.data.fail_rows.join('；');
            showToast(msg, d.success ? (d.data && d.data.fail ? 'warning' : 'success') : 'error');
            input.value = '';
            if (d.success) loadOrders();
        }).catch(()=>showToast('网络错误','warning'));
}
function updatePoItemPrice(oid, iid, val, field){
    field = field || 'unit_price';
    const body = {};
    if (field === 'unit_price') {
        const price = parseFloat(val);
        if (isNaN(price) || price < 0) { showToast('请输入有效的单价', 'warning'); loadOrders(); return; }
        body.unit_price = price;
    } else if (field === 'delivery_date') {
        body.delivery_date = val || '';
    } else {
        body.supplier_name = (val || '').trim();
        if (!body.supplier_name) { showToast('请输入供应商名称', 'warning'); loadOrders(); return; }
    }
    fetch(apiBase+'/pm/orders/'+oid+'/items/'+iid, {
        method: 'PUT', headers: Object.assign({'Content-Type':'application/json'}, authHeaders),
        body: JSON.stringify(body)
    }).then(r=>r.json()).then(d=>{
        if (d.success) { loadOrders(); }
        else showToast(d.message || '保存失败', 'warning');
    }).catch(()=>showToast('网络错误','warning'));
}
function assignProjPoSupplier(oid){
    const sel = document.getElementById('po-sup-sel-'+oid);
    const name = sel ? sel.value.trim() : '';
    if (!name) { showToast('请先选择供应商', 'warning'); return; }
    fetch(apiBase+'/pm/orders/'+oid+'/supplier', {
        method: 'PUT', headers: Object.assign({'Content-Type':'application/json'}, authHeaders),
        body: JSON.stringify({supplier_name: name})
    }).then(r=>r.json()).then(d=>{
        showToast(d.message || (d.success ? '供应商已绑定' : '绑定失败'), d.success ? 'success' : 'error');
        if (d.success) loadOrders();
    }).catch(()=>showToast('网络错误','warning'));
}
function viewOrderDetail(id){
    fetch(apiBase+'/pm/orders/'+id,{headers:authHeaders}).then(r=>r.json()).then(d=>{
        const o=d.data; if(!o) return;
        const items=o.items||[];
        const s=o.supplier||{};
        const total=items.reduce((sum,i)=>sum+Number(i.unit_price||0)*Number(i.quantity||0),0);
        const overlay=document.createElement('div'); overlay.id='po-overlay';
        overlay.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:10001;display:flex;align-items:center;justify-content:center;';
        overlay.onclick=function(e){if(e.target===this)this.remove();};
        overlay.innerHTML=`<div style="background:#fff;border-radius:8px;max-width:900px;width:95%;max-height:90vh;overflow:auto;">
            <div style="background:#1f2937;color:#fff;padding:10px 16px;display:flex;justify-content:space-between;align-items:center;border-radius:8px 8px 0 0;">
                <b>📑 采购订单详情 — ${escapeHtml(o.po_no)}</b>
                <button onclick="document.getElementById('po-overlay').remove()" style="background:rgba(255,255,255,.2);border:none;color:#fff;padding:4px 8px;border-radius:4px;cursor:pointer;">✕</button>
            </div>
            <div style="padding:16px;">
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;font-size:13px;">
                    <div><b>供应商：</b>${o.status==='DRAFT'
                        ? `<span style="display:inline-flex;gap:4px;align-items:center;">
                            <input id="po-sup-name" type="text" value="${escapeHtml(o.supplier_name||'')}" placeholder="手动输入供应商名称" style="width:170px;padding:3px 6px;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;">
                            <button class="btn btn-primary" style="padding:3px 10px;font-size:11px;" onclick="savePOSupplier(${o.id})">💾 保存</button>
                            ${o.supplier_name?'<span style="color:#059669;font-size:11px;">已绑定</span>':'<span style="color:#b45309;font-size:11px;">未绑定</span>'}
                           </span>`
                        : escapeHtml(o.supplier_name||'—')}</div>
                    <div><b>订单日期：</b>${o.created_at?o.created_at.slice(0,10):''}</div>
                    <div><b>订单状态：</b>${o.status}</div>
                    <div><b>订单金额：</b><span style="color:#b45309;font-weight:bold;">¥${Number(o.total_amount||total).toFixed(2)}</span></div>
                </div>
                ${o.status==='DRAFT'?'<div style="font-size:11px;color:#92400e;background:#fffbeb;border:1px solid #fde68a;border-radius:6px;padding:5px 10px;margin-bottom:10px;">💡 手动输入供应商名称保存后：新供应商自动建档进「供应商管理」，订单物料自动编入其供应清单</div>':''}
                <h4 style="border-bottom:2px solid #0ea5e9;padding-bottom:4px;">📦 物料明细</h4>
                <table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:16px;">
                    <thead><tr style="background:#f5f5f5;">
                        <th style="border:1px solid #d1d5db;padding:6px 8px;">物料</th><th style="border:1px solid #d1d5db;padding:6px 8px;">数量</th>
                        <th style="border:1px solid #d1d5db;padding:6px 8px;">单价</th><th style="border:1px solid #d1d5db;padding:6px 8px;">金额</th>
                    </tr></thead>
                    <tbody>${items.map(i=>{
                        const amt=Number(i.unit_price||0)*Number(i.quantity||0);
                        return `<tr><td style="border:1px solid #e5e7eb;padding:6px 8px;"><b>${escapeHtml(i.material_name||'')}</b>${i.material_spec?` <span style="color:#6b7280;font-size:11px;">${escapeHtml(i.material_spec)}</span>`:''}</td>
                        <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:right;">${i.quantity}</td>
                        <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:right;">${Number(i.unit_price||0).toFixed(2)}</td>
                        <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:right;">${amt.toFixed(2)}</td></tr>`;
                    }).join('')}</tbody>
                    <tfoot><tr style="font-weight:bold;"><td colspan="3" style="border:1px solid #d1d5db;padding:6px 8px;text-align:right;">合计</td>
                        <td style="border:1px solid #d1d5db;padding:6px 8px;text-align:right;color:#b45309;">${total.toFixed(2)}</td></tr></tfoot>
                </table>
                <h4 style="border-bottom:2px solid #0ea5e9;padding-bottom:4px;">💬 沟通记录</h4>
                <div id="po-comms" style="max-height:150px;overflow:auto;margin-bottom:8px;"></div>
                <div style="display:flex;gap:6px;margin-bottom:8px;">
                    <select id="po-com-type" style="padding:4px;border:1px solid #ccc;font-size:12px;"><option value="PHONE">电话</option><option value="EMAIL">邮件</option><option value="MEETING">会议</option></select>
                    <input id="po-com-content" type="text" placeholder="沟通内容..." style="flex:1;padding:4px;border:1px solid #ccc;font-size:12px;">
                    <button class="btn btn-primary" style="padding:4px 8px;font-size:12px;" onclick="addPOComm(${o.id})">➕ 添加</button>
                </div>
            </div></div>`;
        document.body.appendChild(overlay);
        // load comms
        fetch(apiBase+'/pm/orders/'+id+'/communications',{headers:authHeaders}).then(r=>r.json()).then(d=>{
            const el=document.getElementById('po-comms'); if(!el) return;
            el.innerHTML=(d.data?.items||[]).map(c=>`<div style="padding:4px 8px;border-left:3px solid #0ea5e9;margin-bottom:4px;background:#f0f9ff;font-size:12px;"><b>[${c.contact_type}]</b> ${escapeHtml(c.content)} <span style="color:#888;font-size:10px;">-${c.communication_date}</span></div>`).join('')||'<div style="color:#999;font-size:12px;text-align:center;padding:8px;">暂无沟通记录</div>';
        });
    });
}
function addPOComm(oid){
    const type=document.getElementById('po-com-type').value;
    const content=document.getElementById('po-com-content').value.trim();
    if(!content) return;
    fetch(apiBase+'/pm/orders/'+oid+'/communication',{method:'POST',headers:authHeaders,body:JSON.stringify({contact_type:type,content:content,communicator:'采购员'})}).then(r=>r.json()).then(d=>{
        if(d.success){ document.getElementById('po-com-content').value=''; viewOrderDetail(oid); }
    });
}
function savePOSupplier(oid){
    const name=(document.getElementById('po-sup-name')?.value||'').trim();
    if(!name){ showToast('请输入供应商名称','warning'); return; }
    fetch(apiBase+'/pm/orders/'+oid+'/supplier',{
        method:'PUT', headers: Object.assign({'Content-Type':'application/json'}, authHeaders),
        body: JSON.stringify({supplier_name:name})
    }).then(r=>r.json()).then(d=>{
        showToast(d.message||(d.success?'供应商已保存':'保存失败'), d.success?'success':'error');
        if(d.success){ loadOrders(); viewOrderDetail(oid); }
    }).catch(()=>showToast('网络错误','warning'));
}
function approvePO(id){
    fetch(apiBase+'/pm/orders/'+id+'/approve',{method:'POST',headers:Object.assign({'Content-Type':'application/json'},authHeaders),body:JSON.stringify({action:'approve'})}).then(r=>r.json()).then(d=>{
        showToast(d.message||(d.success?'审核成功':'失败'), d.success?'success':'error'); if(d.success) loadOrders();
    }).catch(()=>showToast('网络错误','warning'));
}

// ========== 订单跟踪 ==========
function renderTrackingUI(){ return `<div id="pur-track"><div style="color:#888;padding:20px;">加载中...</div></div>`; }
function loadTracking(){
    fetch(apiBase+'/pm/order-tracking',{headers:authHeaders}).then(r=>r.json()).then(d=>{
        const el=document.getElementById('pur-track'); if(!el) return;
        const items=d.data?.items||[];
        const warnCount=items.filter(i=>i.pending_qty>0).length;
        el.innerHTML=`<div style="background:${warnCount>0?'#fef3c7':'#dcfce7'};border-radius:8px;padding:10px 16px;margin-bottom:12px;font-size:13px;">
            ${warnCount>0?`⚠️ 有 ${warnCount} 个订单存在未到货`:'✅ 所有订单执行顺利'}
        </div>
        <table style="width:100%;border-collapse:collapse;font-size:12px;">
            <thead><tr style="background:#f5f5f5;">
                <th style="border:1px solid #d1d5db;padding:6px 8px;">订单号</th><th style="border:1px solid #d1d5db;padding:6px 8px;">供应商</th>
                <th style="border:1px solid #d1d5db;padding:6px 8px;">物料</th><th style="border:1px solid #d1d5db;padding:6px 8px;">订单/到货/未到</th>
                <th style="border:1px solid #d1d5db;padding:6px 8px;">到料率</th>
                <th style="border:1px solid #d1d5db;padding:6px 8px;">物料损耗率</th>
                <th style="border:1px solid #d1d5db;padding:6px 8px;">状态</th><th style="border:1px solid #d1d5db;padding:6px 8px;">预警</th>
            </tr></thead><tbody>${items.map(o=>{
                const warn=o.pending_qty>0?'<span style="color:#b45309;">⚠️ 未到货</span>':'<span style="color:#16a34a;">✅ 已完成</span>';
                const ar=Number(o.arrival_rate||0), lr=Number(o.loss_rate||0), la=Number(o.loss_amount||0), lq=Number(o.loss_qty||0);
                const arColor=ar>=100?'#16a34a':ar>=50?'#d97706':'#dc2626';
                const lossCell = lq>0
                    ? `<span style="color:#dc2626;font-weight:700;">${lr}%</span><br><span style="font-size:10px;color:#dc2626;">损耗${lq}件 ¥${la.toLocaleString()}</span>`
                    : (o.received_qty>0 ? '<span style="color:#16a34a;">0%</span>' : '<span style="color:#9ca3af;">—</span>');
                return `<tr>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;">${escapeHtml(o.po_no)}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;">${escapeHtml(o.supplier_name)}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;font-size:11px;">${escapeHtml(o.material_names)}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">${o.total_qty}/${o.received_qty}/${o.pending_qty}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;min-width:90px;">
                    <div style="background:#e5e7eb;border-radius:4px;height:14px;overflow:hidden;"><div style="width:${Math.min(ar,100)}%;background:${arColor};height:14px;"></div></div>
                    <span style="font-size:11px;font-weight:700;color:${arColor};">${ar}%</span>
                </td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">${lossCell}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">${o.status}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">${warn}</td></tr>`;
            }).join('')}</tbody></table>
        <div style="margin-top:8px;font-size:11px;color:#9ca3af;">说明：到料率=累计合格入库/订单总量；物料损耗率=（订购-实际到货）/已到货批次订购，损耗金额自动计入「管理费用-物料损耗」（利润表）并冲减「原材料」（资产负债表存货），可在财务凭证中查看 SH- 开头凭证。</div>`;
    });
}

// ========== 入库质检 ==========
function renderInboundUI(){ return `<div id="pur-inb"><div style="color:#888;padding:20px;">加载中...</div></div>`; }
var INB_STATUS = { DRAFT:['待审核','#b45309','#fffbeb'], APPROVED:['待质检','#1d4ed8','#dbeafe'], POSTED:['已入库','#047857','#d1fae5'], REJECTED:['已驳回','#b91c1c','#fee2e2'], CLOSED:['已关闭','#6b7280','#f3f4f6'] };
function loadInbound(){
    fetch(apiBase+'/pm/inbounds',{headers:authHeaders}).then(r=>r.json()).then(d=>{
        const el=document.getElementById('pur-inb'); if(!el) return;
        const items=d.data?.items||[];
        el.innerHTML=`<div id="inb-fail-panel"></div>
        <div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;">
            <button class="btn btn-primary" onclick="showAddInbound()">➕ 创建入库单</button>
            <button class="btn btn-secondary" onclick="window.open(apiBase+'/pm/inbounds/template')">📋 下载入库单模板</button>
            <label class="btn btn-secondary" style="cursor:pointer;">📥 导入入库单Excel<input type="file" accept=".xlsx,.xls" onchange="importInboundExcel(this)" style="display:none;"></label>
            <span style="font-size:12px;color:#666;align-self:center;">流程：下载模板→填写→导入(待审核)→审核通过→质检→入库（共 ${items.length} 条）</span>
        </div>
        <table style="width:100%;border-collapse:collapse;font-size:12px;">
            <thead><tr style="background:#f5f5f5;">
                <th style="border:1px solid #d1d5db;padding:6px 8px;">入库单号</th><th style="border:1px solid #d1d5db;padding:6px 8px;">采购订单</th>
                <th style="border:1px solid #d1d5db;padding:6px 8px;">物料</th><th style="border:1px solid #d1d5db;padding:6px 8px;">数量(订单/实收)</th>
                <th style="border:1px solid #d1d5db;padding:6px 8px;">金额</th><th style="border:1px solid #d1d5db;padding:6px 8px;">状态</th>
                <th style="border:1px solid #d1d5db;padding:6px 8px;">质检</th>
                <th style="border:1px solid #d1d5db;padding:6px 8px;">操作</th>
            </tr></thead><tbody>${items.map(i=>{
                const st=INB_STATUS[i.status]||[i.status,'#666','#f3f4f6'];
                const canQC=(i.status==='APPROVED'||i.status==='POSTED'||i.status==='CLOSED')&&i.quality_status==='PENDING';
                return `<tr>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;">${escapeHtml(i.inbound_no)}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;">${escapeHtml(i.po_no)}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;">${escapeHtml(i.material_name)}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">${i.ordered_qty}/${i.received_qty}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:right;color:#b45309;">${i.amount.toFixed(2)}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">
                    <span style="padding:2px 8px;border-radius:10px;font-size:10px;background:${st[2]};color:${st[1]};">${st[0]}</span>
                </td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">
                    <span style="padding:2px 8px;border-radius:10px;font-size:10px;background:${i.quality_status==='PASSED'?'#dcfce7;color:#16a34a':i.quality_status==='FAILED'?'#fee2e2;color:#dc2626':'#fef3c7;color:#b45309;'};">${i.quality_status==='PENDING'?'待检':i.quality_status==='PASSED'?'合格':'不合格'}</span>
                </td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;white-space:nowrap;">
                    ${i.status==='DRAFT'||i.status==='REJECTED'?`<button class="btn btn-primary" style="padding:2px 6px;font-size:11px;" onclick="auditInbound(${i.id},'approve')">✅ 审核</button>
                    <button class="btn btn-danger" style="padding:2px 6px;font-size:11px;margin-left:4px;" onclick="auditInbound(${i.id},'reject')">❌ 驳回</button>
                    <button class="btn btn-danger" style="padding:2px 6px;font-size:11px;margin-left:4px;" onclick="deleteInbound(${i.id})">🗑</button>`:''}
                    ${canQC?`<button class="btn btn-primary" style="padding:2px 6px;font-size:11px;" onclick="inspectInbound(${i.id},'PASSED')">✅ 合格</button>
                    <button class="btn btn-danger" style="padding:2px 6px;font-size:11px;margin-left:4px;" onclick="inspectInbound(${i.id},'FAILED')">❌ 不合格</button>`:''}
                    ${i.status==='POSTED'||i.status==='CLOSED'?'<span style="color:#999;">—</span>':''}
                </td></tr>`;}).join('')}</tbody></table>`;
    });
}
function auditInbound(iid,action){
    const tip=action==='approve'?'确认审核通过？通过后进入质检环节':'确认驳回该入库单？';
    if(!confirm(tip)) return;
    fetch(apiBase+'/pm/inbounds/'+iid+'/audit',{method:'POST',headers:Object.assign({'Content-Type':'application/json'},authHeaders),body:JSON.stringify({action})}).then(r=>r.json()).then(d=>{
        showToast(d.message||(d.success?'操作成功':'失败'), d.success?'success':'error'); if(d.success) loadInbound();
    }).catch(()=>showToast('操作失败','error'));
}
function importInboundExcel(input){
    const f=input.files[0]; if(!f) return;
    const fd=new FormData(); fd.append('file',f);
    fetch(apiBase+'/pm/inbounds/import',{method:'POST',headers:authHeaders||{},body:fd}).then(r=>r.json()).then(d=>{
        const el=document.getElementById('inb-fail-panel');
        if(el&&d.data&&d.data.fail_rows&&d.data.fail_rows.length){
            el.innerHTML='<div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:10px 14px;margin-bottom:12px;font-size:12px;color:#b91c1c;">'
                +'<b>导入失败明细（成功 '+((d.data&&d.data.imported)||0)+' 行）：</b><br>'+d.data.fail_rows.map(escapeHtml).join('<br>')+'</div>';
        } else if(el){ el.innerHTML=''; }
        showToast(d.message||(d.success?'导入成功':'导入失败'), d.success?((d.data&&d.data.fail_rows&&d.data.fail_rows.length)?'warning':'success'):'error');
        input.value='';
        if(d.success) loadInbound();
    }).catch(()=>showToast('导入失败','error'));
}
function showAddInbound(){
    fetch(apiBase+'/pm/orders',{headers:authHeaders}).then(r=>r.json()).then(d=>{
        const pos=d.data?.items||[];
        if(!pos.length){ showToast('暂无采购订单', 'warning'); return; }
        const poId=parseInt(prompt('采购订单ID:',pos[0].id)); if(!poId) return;
        const po=pos.find(p=>p.id===poId);
        if(!po){ showToast('订单不存在', 'warning'); return; }
        const items=po.items||[];
        if(!items.length){ showToast('订单无明细', 'warning'); return; }
        const item=items[0];
        const recvQty=parseFloat(prompt('实收数量:',item.quantity)); if(!recvQty) return;
        const price=parseFloat(prompt('单价:',item.unit_price)); if(isNaN(price)) return;
        fetch(apiBase+'/pm/inbounds',{method:'POST',headers:authHeaders,body:JSON.stringify({
            purchase_order_id:poId,material_id:item.material_id,
            ordered_qty:item.quantity,received_qty:recvQty,unit_price:price,
            inbound_date:prompt('入库日期 (YYYY-MM-DD):',new Date().toISOString().slice(0,10)),
            operator:prompt('操作员:','仓管员'),status:'DRAFT'
        })}).then(r=>r.json()).then(d=>{
            showToast(d.message||(d.success?'入库单创建成功':'创建失败'), d.success?'success':'error'); if(d.success) loadInbound();
        });
    });
}
function deleteInbound(iid){
    if(!confirm('确定删除该入库单？删除后需重新导入。')) return;
    fetch(apiBase+'/pm/inbounds/'+iid,{method:'DELETE',headers:authHeaders}).then(r=>r.json()).then(d=>{
        showToast(d.message||(d.success?'已删除':'删除失败'), d.success?'success':'error'); if(d.success) loadInbound();
    }).catch(()=>showToast('删除失败','error'));
}
function inspectInbound(iid,status){
    fetch(apiBase+'/pm/inbounds/'+iid+'/inspect',{method:'POST',headers:authHeaders,body:JSON.stringify({quality_status:status,status:'POSTED'})}).then(r=>r.json()).then(d=>{
        showToast(d.message||(d.success?'质检完成':'失败'), d.success?'success':'error'); if(d.success) loadInbound();
    });
}

// ========== 采购报表 ==========
function renderReportsUI(){ return `<div id="pur-reports"><div style="color:#888;padding:20px;">加载中...</div></div>`; }
function loadPurchaseReports(){
    const el=document.getElementById('pur-reports'); if(!el) return;
    el.innerHTML=`<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px;margin-bottom:16px;">
        <div class="pur-stat-card" onclick="showReport('exec')" style="cursor:pointer;"><div class="num">—</div><div class="lbl">📊 订单执行情况表</div></div>
        <div class="pur-stat-card" onclick="showReport('supplier')" style="cursor:pointer;"><div class="num">—</div><div class="lbl">🏭 供应商绩效分析</div></div>
        <div class="pur-stat-card" onclick="showReport('price')" style="cursor:pointer;"><div class="num">—</div><div class="lbl">📈 价格波动分析</div></div>
    </div>
    <div id="pur-report-detail"></div>`;
}
function showReport(type){
    const el=document.getElementById('pur-report-detail');
    if(type==='exec'){
        fetch(apiBase+'/pm/reports/order-execution',{headers:authHeaders}).then(r=>r.json()).then(d=>{
            const items=d.data?.items||[];
            el.innerHTML=`<h4 style="border-bottom:2px solid #0ea5e9;padding-bottom:4px;">📊 采购订单执行情况表</h4>
                <div style="margin-bottom:8px;font-size:12px;color:#666;">共 ${d.data?.total_count||0} 张订单，总金额 ${(d.data?.total_amount||0).toFixed(2)} 元</div>
                <table style="width:100%;border-collapse:collapse;font-size:12px;"><thead><tr style="background:#f5f5f5;">
                <th style="border:1px solid #d1d5db;padding:6px 8px;">订单号</th><th style="border:1px solid #d1d5db;padding:6px 8px;">供应商</th>
                <th style="border:1px solid #d1d5db;padding:6px 8px;">金额</th><th style="border:1px solid #d1d5db;padding:6px 8px;">状态</th></tr></thead>
                <tbody>${items.slice(0,20).map(i=>`<tr><td style="border:1px solid #e5e7eb;padding:6px 8px;">${escapeHtml(i.po_no)}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;">${escapeHtml(i.supplier_name)}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:right;">${i.amount.toFixed(2)}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">${i.status}</td></tr>`).join('')}</tbody></table>`;
        });
    } else if(type==='supplier'){
        fetch(apiBase+'/pm/reports/supplier-performance',{headers:authHeaders}).then(r=>r.json()).then(d=>{
            const items=d.data?.items||[];
            el.innerHTML=`<h4 style="border-bottom:2px solid #0ea5e9;padding-bottom:4px;">🏭 供应商绩效分析</h4>
                <table style="width:100%;border-collapse:collapse;font-size:12px;"><thead><tr style="background:#f5f5f5;">
                <th style="border:1px solid #d1d5db;padding:6px 8px;">供应商</th><th style="border:1px solid #d1d5db;padding:6px 8px;">订单数</th>
                <th style="border:1px solid #d1d5db;padding:6px 8px;">总金额</th><th style="border:1px solid #d1d5db;padding:6px 8px;">准时率</th>
                <th style="border:1px solid #d1d5db;padding:6px 8px;">合格率</th><th style="border:1px solid #d1d5db;padding:6px 8px;">综合评分</th></tr></thead>
                <tbody>${items.map(i=>`<tr><td style="border:1px solid #e5e7eb;padding:6px 8px;">${escapeHtml(i.supplier_name)}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:right;">${i.order_count}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:right;">${i.total_amount.toFixed(2)}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;color:${i.on_time_rate>90?'#059669':'#dc2626'};">${i.on_time_rate.toFixed(1)}%</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;color:${i.quality_rate>90?'#059669':'#dc2626'};">${i.quality_rate.toFixed(1)}%</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;font-weight:bold;">${i.avg_score.toFixed(2)}</td></tr>`).join('')}</tbody></table>`;
        });
    } else if(type==='price'){
        fetch(apiBase+'/pm/reports/price-fluctuation',{headers:authHeaders}).then(r=>r.json()).then(d=>{
            const items=d.data?.items||[];
            el.innerHTML=`<h4 style="border-bottom:2px solid #0ea5e9;padding-bottom:4px;">📈 采购价格波动分析</h4>
                <table style="width:100%;border-collapse:collapse;font-size:12px;"><thead><tr style="background:#f5f5f5;">
                <th style="border:1px solid #d1d5db;padding:6px 8px;">物料</th><th style="border:1px solid #d1d5db;padding:6px 8px;">当前价</th>
                <th style="border:1px solid #d1d5db;padding:6px 8px;">平均价</th><th style="border:1px solid #d1d5db;padding:6px 8px;">最低/最高</th>
                <th style="border:1px solid #d1d5db;padding:6px 8px;">波动幅度</th></tr></thead>
                <tbody>${items.map(i=>`<tr>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;">${escapeHtml(i.material_code)} ${escapeHtml(i.material_name)}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:right;">${i.current_price.toFixed(2)}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:right;">${i.avg_price.toFixed(2)}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:right;">${i.min_price.toFixed(2)} / ${i.max_price.toFixed(2)}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;color:${i.change_pct>0?'#dc2626':'#059669'};">${i.change_pct>0?'▲':'▼'} ${Math.abs(i.change_pct)}%</td></tr>`).join('')||'<tr><td colspan="5" style="text-align:center;padding:20px;color:#999;">暂无价格数据，请先创建入库单</td></tr>'}</tbody></table>`;
        });
    }
}

// ========== 新建采购订单（可增加子项）==========
let _poItemCount = 0;
function showPurchaseOrderForm() {
    _poItemCount = 0;
    let modal = document.getElementById('po-form-modal');
    if (modal) modal.remove();
    modal = document.createElement('div');
    modal.id = 'po-form-modal';
    modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    modal.innerHTML = `
        <div style="background:#fff;border-radius:12px;padding:24px;width:720px;max-width:95%;max-height:90vh;overflow-y:auto;">
            <h3 style="margin:0 0 16px 0;font-size:16px;">➕ 新建采购订单</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;">
                <div>
                    <label style="font-size:12px;color:#666;">供应商名称 *</label>
                    <input id="po-supplier" class="form-control" style="width:100%;" placeholder="输入供应商名称" onblur="checkSupplierOverseas()">
                    <label style="display:flex;align-items:center;gap:4px;margin-top:4px;cursor:pointer;font-size:11px;color:#0369a1;">
                        <input type="checkbox" id="po-supplier-overseas" style="width:14px;height:14px;" onchange="checkSupplierOverseasManual()">
                        🌍 海外贸易供应商（勾选后需填贸易术语）
                    </label>
                </div>
                <div><label style="font-size:12px;color:#666;">预计交期</label><input id="po-delivery" type="date" class="form-control" style="width:100%;"></div>
            </div>
            <div id="po-trade-term-wrap" style="display:none;background:#fef3c7;border:1px solid #f59e0b;border-radius:8px;padding:10px 12px;margin-bottom:16px;">
                <label style="font-size:12px;color:#92400e;font-weight:bold;">🌍 贸易术语（海外贸易供应商必填）</label>
                <select id="po-trade-term" class="form-control" style="width:100%;margin-top:4px;">
                    <option value="FOB">FOB（船上交货）</option>
                    <option value="CIF">CIF（成本加保险费加运费）</option>
                    <option value="CFR">CFR（成本加运费）</option>
                    <option value="EXW">EXW（工厂交货）</option>
                    <option value="DDP">DDP（完税后交货）</option>
                </select>
                <div style="font-size:11px;color:#b45309;margin-top:4px;">⚠️ 已检测到该供应商为海外贸易，需填写贸易术语</div>
            </div>
            <div style="border:1px solid #e2e8f0;border-radius:8px;padding:12px;margin-bottom:16px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <h4 style="margin:0;font-size:14px;color:#475569;">📦 物料明细</h4>
                    <button class="btn btn-primary" style="padding:4px 10px;font-size:12px;" onclick="addPoItemRow()">➕ 增加一行</button>
                </div>
                <table style="width:100%;border-collapse:collapse;font-size:12px;">
                    <thead><tr style="background:#f8fafc;">
                        <th style="border:1px solid #e2e8f0;padding:6px 8px;width:30%;">物料名称</th>
                        <th style="border:1px solid #e2e8f0;padding:6px 8px;width:15%;">数量</th>
                        <th style="border:1px solid #e2e8f0;padding:6px 8px;width:15%;">单价</th>
                        <th style="border:1px solid #e2e8f0;padding:6px 8px;width:15%;">金额</th>
                        <th style="border:1px solid #e2e8f0;padding:6px 8px;width:25%;">操作</th>
                    </tr></thead>
                    <tbody id="po-items-body"></tbody>
                    <tfoot><tr style="font-weight:bold;background:#f8fafc;">
                        <td colspan="3" style="border:1px solid #e2e8f0;padding:6px 8px;text-align:right;">合计</td>
                        <td id="po-total" style="border:1px solid #e2e8f0;padding:6px 8px;text-align:right;color:#b45309;">0.00</td>
                        <td></td>
                    </tr></tfoot>
                </table>
            </div>
            <div style="display:flex;gap:8px;justify-content:flex-end;">
                <button class="btn btn-default" onclick="document.getElementById('po-form-modal').remove()">取消</button>
                <button class="btn btn-primary" onclick="savePurchaseOrder()">保存订单</button>
            </div>
        </div>`;
    document.body.appendChild(modal);
    addPoItemRow();
}

function addPoItemRow() {
    _poItemCount++;
    const idx = _poItemCount;
    const tbody = document.getElementById('po-items-body');
    if (!tbody) return;
    const tr = document.createElement('tr');
    tr.id = 'po-item-row-' + idx;
    tr.innerHTML = `
        <td style="border:1px solid #e2e8f0;padding:4px 6px;"><input id="po-mat-${idx}" class="form-control" style="width:100%;padding:4px;font-size:12px;" placeholder="物料名称"></td>
        <td style="border:1px solid #e2e8f0;padding:4px 6px;"><input id="po-qty-${idx}" type="number" value="1" class="form-control" style="width:100%;padding:4px;font-size:12px;" oninput="recalcPoTotal()"></td>
        <td style="border:1px solid #e2e8f0;padding:4px 6px;"><input id="po-price-${idx}" type="number" step="0.01" value="0" class="form-control" style="width:100%;padding:4px;font-size:12px;" oninput="recalcPoTotal()"></td>
        <td style="border:1px solid #e2e8f0;padding:4px 6px;text-align:right;" id="po-amt-${idx}">0.00</td>
        <td style="border:1px solid #e2e8f0;padding:4px 6px;text-align:center;"><button class="btn" style="padding:2px 8px;font-size:11px;background:#fee2e2;color:#991b1b;" onclick="removePoItemRow(${idx})">🗑 删除</button></td>`;
    tbody.appendChild(tr);
    recalcPoTotal();
}

function removePoItemRow(idx) {
    const row = document.getElementById('po-item-row-' + idx);
    if (row) row.remove();
    recalcPoTotal();
}

function recalcPoTotal() {
    const rows = document.querySelectorAll('[id^="po-item-row-"]');
    let total = 0;
    rows.forEach(row => {
        const id = row.id.replace('po-item-row-', '');
        const qty = parseFloat(document.getElementById('po-qty-' + id).value) || 0;
        const price = parseFloat(document.getElementById('po-price-' + id).value) || 0;
        const amt = qty * price;
        const amtEl = document.getElementById('po-amt-' + id);
        if (amtEl) amtEl.textContent = amt.toFixed(2);
        total += amt;
    });
    const totalEl = document.getElementById('po-total');
    if (totalEl) totalEl.textContent = total.toFixed(2);
}

// 检查供应商是否海外贸易，动态显示/隐藏贸易术语字段
function checkSupplierOverseas() {
    const name = document.getElementById('po-supplier').value.trim();
    const wrap = document.getElementById('po-trade-term-wrap');
    if (!name) { if(wrap) wrap.style.display='none'; return; }
    // 先默认隐藏，避免异步延迟导致旧状态残留
    if(wrap) wrap.style.display = 'none';
    // 手动勾选优先
    const manualOverseas = document.getElementById('po-supplier-overseas').checked;
    if (manualOverseas) { wrap.style.display = 'block'; return; }
    fetch('/api/v1/purchase/suppliers', {headers:{'Content-Type':'application/json'}}).then(r=>r.json()).then(d=>{
        const list = (d.data?.items || d.data || []);
        const found = list.find(s => s.name === name);
        if (found && found.is_overseas) {
            wrap.style.display = 'block';
        } else {
            wrap.style.display = 'none';
        }
    }).catch(() => { if(wrap) wrap.style.display='none'; });
}
// 手动勾选海外贸易时直接切换
function checkSupplierOverseasManual() {
    const wrap = document.getElementById('po-trade-term-wrap');
    const checked = document.getElementById('po-supplier-overseas').checked;
    if (wrap) wrap.style.display = checked ? 'block' : 'none';
}

function savePurchaseOrder() {
    const supplierName = document.getElementById('po-supplier').value.trim();
    if (!supplierName) { showToast('请输入供应商名称', 'warning'); return; }
    // 海外贸易必须填贸易术语
    const ttWrap = document.getElementById('po-trade-term-wrap');
    let tradeTerm = null;
    if (ttWrap && ttWrap.style.display !== 'none') {
        tradeTerm = document.getElementById('po-trade-term').value;
        if (!tradeTerm) { showToast('请选择贸易术语', 'warning'); return; }
    }
    const rows = document.querySelectorAll('[id^="po-item-row-"]');
    if (rows.length === 0) { showToast('请至少添加一行物料明细', 'warning'); return; }
    const items = [];
    rows.forEach(row => {
        const id = row.id.replace('po-item-row-', '');
        const mat = document.getElementById('po-mat-' + id).value.trim();
        const qty = parseInt(document.getElementById('po-qty-' + id).value) || 0;
        const price = parseFloat(document.getElementById('po-price-' + id).value) || 0;
        if (mat && qty > 0) {
            items.push({ material_name: mat, quantity: qty, unit_price: price, remark: mat });
        }
    });
    if (items.length === 0) { showToast('请填写有效的物料明细', 'warning'); return; }

    // 第一步：先创建/获取供应商（带上海外贸易标记）
    const isOverseas = document.getElementById('po-supplier-overseas') ? document.getElementById('po-supplier-overseas').checked : false;
    const supPayload = { account_set_id: 1, name: supplierName, is_overseas: isOverseas };
    fetch(apiBase + '/purchase/suppliers', { method: 'POST', headers: authHeaders, body: JSON.stringify(supPayload) })
        .then(r => r.json())
        .then(supRes => {
            if (!supRes.success) {
                // 供应商可能已存在，尝试查询
                return fetch(apiBase + '/purchase/suppliers?keyword=' + encodeURIComponent(supplierName), { headers: authHeaders })
                    .then(r => r.json())
                    .then(listRes => {
                        const list = listRes.data?.items || listRes.data || [];
                        const found = list.find(s => s.name === supplierName);
                        if (!found) throw new Error('供应商创建失败且未找到已有供应商');
                        return found;
                    });
            }
            return supRes.data;
        })
        .then(supplier => {
            const supplierId = supplier.id || supplier.supplier_id;
            if (!supplierId) throw new Error('无法获取供应商ID');
            // 第二步：创建采购订单
            const payload = {
                account_set_id: 1,
                supplier_id: supplierId,
                status: 'DRAFT',
                trade_term: tradeTerm,
                items: items
            };
            return fetch(apiBase + '/pm/orders', { method: 'POST', headers: authHeaders, body: JSON.stringify(payload) });
        })
        .then(r => r.json())
        .then(res => {
            if (res.success !== false) {
                showToast('✅ 采购订单创建成功！\n\n供应商：' + supplierName + '\n物料明细：\n' + items.map(i => `${i.material_name} × ${i.quantity} × ¥${i.unit_price}`).join('\n'), 'success', 5000);
                document.getElementById('po-form-modal').remove();
                loadOrders();
            } else {
                showToast('❌ ' + (res.message || '创建失败'), 'error');
            }
        })
        .catch(e => {
            console.error('采购订单创建失败:', e);
            showToast('❌ 创建失败：' + e.message + '\n\n请检查网络或联系管理员。', 'error', 5000);
        });
}

// ========== 最优采购批量 EOQ 7公式联动计算器 ==========
// 公式依赖链：H' → Q* → TC / CI / Turnover → ROI
function renderEoqCalculator() {
    return `
    <div style="margin-bottom:16px;">
        <div style="background:linear-gradient(135deg,#fef3c7,#fde68a);border:1px solid #f59e0b;border-radius:12px;padding:16px;">
            <h3 style="margin:0 0 8px 0;color:#92400e;font-size:15px;">🎯 最优采购批量联动计算器</h3>
            <p style="margin:0;font-size:12px;color:#78350f;">通过7个公式联动计算，平衡库存成本与采购成本，<b>ROI（投资回报率）</b>是采购优化的核心目标。调整任一输入参数，7个公式结果自动重算。</p>
        </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1.2fr;gap:20px;">
        <!-- 左侧：输入参数 -->
        <div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:16px;">
            <h4 style="margin:0 0 12px 0;color:#1e40af;font-size:14px;">📥 输入参数</h4>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                <label style="font-size:12px;color:#374151;">年需求量 D (件/年)<input type="number" id="eoq-in-D" value="5000" class="eoq-input"></label>
                <label style="font-size:12px;color:#374151;">单次订货成本 S (元/次)<input type="number" id="eoq-in-S" value="200" class="eoq-input"></label>
                <label style="font-size:12px;color:#374151;">采购单价 C (元/件)<input type="number" id="eoq-in-C" value="50" class="eoq-input"></label>
                <label style="font-size:12px;color:#374151;">资金成本率 i (%)<input type="number" id="eoq-in-i" value="8" class="eoq-input" step="0.1"></label>
                <label style="font-size:12px;color:#374151;">采购提前期 L (天)<input type="number" id="eoq-in-L" value="7" class="eoq-input"></label>
                <label style="font-size:12px;color:#374151;">基础持有成本 H (元/件·年)<input type="number" id="eoq-in-H" value="5" class="eoq-input"></label>
                <label style="font-size:12px;color:#374151;">销售单价 P (元/件)<input type="number" id="eoq-in-P" value="60" class="eoq-input"></label>
                <div style="display:flex;align-items:flex-end;">
                    <button onclick="eoqResetDefaults()" class="btn btn-secondary" style="width:100%;padding:8px;font-size:12px;">🔄 重置默认值</button>
                </div>
            </div>
            <div style="margin-top:12px;padding:10px;background:#f0f9ff;border-radius:6px;font-size:11px;color:#0369a1;line-height:1.6;">
                <b>参数说明：</b><br>
                D=年需求量 · S=每次订货固定成本 · C=采购单价 · i=资金年利率<br>
                L=供应商交期天数 · H=基础仓储持有成本 · P=对外销售单价
            </div>
        </div>
        <!-- 右侧：7公式结果链式展示 -->
        <div id="eoq-results"></div>
    </div>
    <style>
        .eoq-input{width:100%;padding:7px 8px;border:1px solid #d1d5db;border-radius:6px;margin-top:4px;font-size:13px;box-sizing:border-box;}
        .eoq-input:focus{outline:none;border-color:#0ea5e9;box-shadow:0 0 0 3px rgba(14,165,233,.1);}
        .eoq-formula-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px;margin-bottom:10px;position:relative;transition:all .3s;}
        .eoq-formula-card.core{background:linear-gradient(135deg,#fef3c7,#fde68a);border:2px solid #f59e0b;box-shadow:0 4px 16px rgba(245,158,11,.2);}
        .eoq-formula-card:hover{transform:translateY(-2px);box-shadow:0 4px 12px rgba(0,0,0,.08);}
        .eoq-step{display:inline-block;width:22px;height:22px;line-height:22px;text-align:center;border-radius:50%;background:#0ea5e9;color:#fff;font-size:11px;font-weight:bold;margin-right:8px;}
        .eoq-formula-card.core .eoq-step{background:#d97706;}
        .eoq-formula{font-size:11px;color:#64748b;font-family:monospace;background:#f8fafc;padding:4px 8px;border-radius:4px;margin:6px 0;}
        .eoq-value{font-size:22px;font-weight:700;color:#1e40af;}
        .eoq-formula-card.core .eoq-value{font-size:28px;color:#92400e;}
        .eoq-dep-arrow{text-align:center;color:#94a3b8;font-size:16px;margin:2px 0;}
    </style>`;
}

function initEoqCalculator() {
    // 实时联动：任何输入变化都触发重算
    ['D','S','C','i','L','H','P'].forEach(k => {
        const el = document.getElementById('eoq-in-' + k);
        if (el) el.addEventListener('input', calcEoqAll);
    });
    calcEoqAll();
}

function eoqResetDefaults() {
    const defaults = {D:5000,S:200,C:50,i:8,L:7,H:5,P:60};
    for (const k in defaults) {
        const el = document.getElementById('eoq-in-' + k);
        if (el) el.value = defaults[k];
    }
    calcEoqAll();
}

// 核心计算函数：7个公式链式联动
function calcEoqAll() {
    const D = parseFloat(document.getElementById('eoq-in-D').value) || 0;
    const S = parseFloat(document.getElementById('eoq-in-S').value) || 0;
    const C = parseFloat(document.getElementById('eoq-in-C').value) || 0;
    const i = (parseFloat(document.getElementById('eoq-in-i').value) || 0) / 100; // 转为小数
    const L = parseFloat(document.getElementById('eoq-in-L').value) || 0;
    const H = parseFloat(document.getElementById('eoq-in-H').value) || 0;
    const P = parseFloat(document.getElementById('eoq-in-P').value) || 0;

    // 公式1：修正持有成本 H' = H + C×i + C×i×(L/365)
    const H_prime = H + C * i + C * i * (L / 365);

    // 公式2：最优采购批量 Q* = √(2×D×S/H')
    const Q = H_prime > 0 ? Math.sqrt(2 * D * S / H_prime) : 0;

    // 公式3：总成本 TC = D×C + (D/Q)×S + (Q/2)×H'
    const TC = D * C + (Q > 0 ? (D / Q) * S + (Q / 2) * H_prime : 0);

    // 公式4：资金占用 CI = (Q/2)×C
    const CI = (Q / 2) * C;

    // 公式5：库存周转率 Turnover = D/Q
    const Turnover = Q > 0 ? D / Q : 0;

    // 公式6：利润率 Profit Rate = (P-C)/P
    const ProfitRate = P > 0 ? (P - C) / P : 0;

    // 公式7：ROI = 库存周转率 × 利润率（核心目标）
    const ROI = Turnover * ProfitRate;

    // 渲染结果（链式依赖可视化）
    const fmt = (n, d=2) => {
        if (!isFinite(n)) return '0.00';
        return n.toLocaleString('zh-CN', {minimumFractionDigits:d, maximumFractionDigits:d});
    };

    document.getElementById('eoq-results').innerHTML = `
        <div class="eoq-formula-card">
            <div><span class="eoq-step">1</span><b>修正持有成本 H'</b></div>
            <div class="eoq-formula">H' = H + C×i + C×i×(L/365)</div>
            <div class="eoq-value">¥${fmt(H_prime)} <span style="font-size:12px;color:#64748b;font-weight:normal;">/件·年</span></div>
        </div>
        <div class="eoq-dep-arrow">↓ 依赖 H'</div>
        <div class="eoq-formula-card">
            <div><span class="eoq-step">2</span><b>最优采购批量 Q*</b></div>
            <div class="eoq-formula">Q* = √(2×D×S / H')</div>
            <div class="eoq-value">${fmt(Q,0)} <span style="font-size:12px;color:#64748b;font-weight:normal;">件</span></div>
        </div>
        <div class="eoq-dep-arrow">↓ 依赖 Q* 和 H'</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
            <div class="eoq-formula-card">
                <div><span class="eoq-step">3</span><b>总成本 TC</b></div>
                <div class="eoq-formula">TC = D×C + (D/Q)×S + (Q/2)×H'</div>
                <div class="eoq-value" style="font-size:18px;">¥${fmt(TC)}</div>
            </div>
            <div class="eoq-formula-card">
                <div><span class="eoq-step">4</span><b>资金占用 CI</b></div>
                <div class="eoq-formula">CI = (Q/2)×C</div>
                <div class="eoq-value" style="font-size:18px;">¥${fmt(CI)}</div>
            </div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px;">
            <div class="eoq-formula-card">
                <div><span class="eoq-step">5</span><b>库存周转率</b></div>
                <div class="eoq-formula">Turnover = D / Q</div>
                <div class="eoq-value" style="font-size:18px;">${fmt(Turnover,1)} <span style="font-size:12px;color:#64748b;font-weight:normal;">次/年</span></div>
            </div>
            <div class="eoq-formula-card">
                <div><span class="eoq-step">6</span><b>利润率</b></div>
                <div class="eoq-formula">Profit Rate = (P-C) / P</div>
                <div class="eoq-value" style="font-size:18px;">${fmt(ProfitRate*100,1)}<span style="font-size:14px;">%</span></div>
            </div>
        </div>
        <div class="eoq-dep-arrow">↓ 依赖周转率和利润率</div>
        <div class="eoq-formula-card core">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div><span class="eoq-step">7</span><b>🎯 ROI 投资回报率 <span style="font-size:11px;background:#d97706;color:#fff;padding:2px 8px;border-radius:10px;">采购优化核心目标</span></b></div>
            </div>
            <div class="eoq-formula" style="background:#fef3c7;">ROI = 库存周转率 × 利润率</div>
            <div class="eoq-value">${fmt(ROI,2)}<span style="font-size:16px;color:#92400e;"> 次/年</span></div>
            <div style="margin-top:6px;font-size:11px;color:#92400e;">💡 ROI越高，资金使用效率越好。对比不同采购方案的ROI，选择最优批量。</div>
        </div>
    `;
}

// 将实现注册到全局，供 index.html 中的 delegate renderPurchase() 调用
window._renderPurchaseImpl = _renderPurchaseModule;

// ============================================================
// 📜 采购合同（填写式合同文书 + 法律声明）
// ============================================================

var DEFAULT_LEGAL = [
    '1. 本合同经双方授权代表签字并加盖公章（或合同专用章）后生效，具有法律约束力，双方应严格履行。',
    '2. 双方保证具备签署及履行本合同所需的合法经营资格与授权，签署本合同系双方真实意思表示，不存在欺诈、胁迫或重大误解情形。',
    '3. 任何一方提供虚假资质、虚假信息或以欺诈手段订立合同的，另一方有权解除合同、要求赔偿全部损失并依法追究其法律责任。',
    '4. 未经对方书面同意，任何一方不得将本合同项下权利义务全部或部分转让给第三方。',
    '5. 双方对履行本合同过程中知悉的对方商业秘密、技术资料及价格信息负有保密义务，未经书面许可不得向第三方披露。',
    '6. 因不可抗力致使合同不能履行的，根据不可抗力的影响程度，部分或全部免除违约责任，但应及时通知对方并提供证明。',
    '7. 本合同未尽事宜，双方可另行签订补充协议；补充协议与本合同具有同等法律效力。',
    '8. 本合同一式两份，甲乙双方各执一份，自双方签字盖章之日起生效。'
].join('\n');

var DEFAULT_QUALITY = '货物应符合国家标准、行业标准及乙方明示的质量要求，随货提供合格证/质检报告；质量保证期不少于约定期限。';
var DEFAULT_ACCEPT = '货到后甲方应在7个工作日内按订单及送货单验收数量、外观、规格；质量异议应在验收后15日内书面提出，乙方负责退换货并承担费用。';

function renderContractsUI() {
    return `
    <div id="contract-list-wrap">
        <div style="display:flex;gap:8px;margin-bottom:12px;align-items:center;flex-wrap:wrap;">
            <button class="btn btn-primary" onclick="showContractForm()">➕ 新建合同</button>
            <button class="btn btn-secondary" onclick="window.open(apiBase+'/pm/contracts/export')">📤 导出台账Excel</button>
            <select id="ct-status-filter" onchange="loadContracts()" style="padding:5px;border:1px solid #ccc;border-radius:4px;">
                <option value="">全部状态</option><option value="DRAFT">草稿</option>
                <option value="SIGNED">已签署</option><option value="CANCELLED">已作废</option>
            </select>
            <input id="ct-kw" type="text" placeholder="搜索合同编号/名称/供应商..." style="flex:1;min-width:160px;padding:5px;border:1px solid #ccc;border-radius:4px;" onkeydown="if(event.key==='Enter')loadContracts()">
            <button class="btn btn-secondary" onclick="loadContracts()">🔍</button>
        </div>
        <div id="contract-list"><div style="color:#888;padding:20px;">加载中...</div></div>
    </div>
    <div id="contract-form-wrap" style="display:none;"></div>`;
}

function loadContracts() {
    var kw = encodeURIComponent(document.getElementById('ct-kw')?.value || '');
    var st = document.getElementById('ct-status-filter')?.value || '';
    fetch(apiBase + '/pm/contracts?keyword=' + kw + '&status=' + st, { headers: authHeaders }).then(r => r.json()).then(d => {
        var el = document.getElementById('contract-list');
        if (!el) return;
        var items = (d && d.data && d.data.items) || [];
        if (!items.length) {
            el.innerHTML = '<div style="text-align:center;color:#94a3b8;padding:40px 0;">暂无合同，点击「➕ 新建合同」开始填写</div>';
            return;
        }
        var stMap = { DRAFT: ['草稿', '#b45309', '#fffbeb'], SIGNED: ['已签署', '#047857', '#ecfdf5'], CANCELLED: ['已作废', '#b91c1c', '#fef2f2'] };
        var html = '<table style="width:100%;border-collapse:collapse;font-size:12px;table-layout:fixed;">';
        html += '<thead><tr style="background:#f5f5f5;">';
        ['合同编号', '合同名称', '供应商', '金额(元)', '签订日期', '交付日期', '状态', '操作'].forEach(function (h) {
            html += '<th style="border:1px solid #d1d5db;padding:6px 8px;">' + h + '</th>';
        });
        html += '</tr></thead><tbody>';
        items.forEach(function (c) {
            var s = stMap[c.status] || [c.status, '#666', '#f3f4f6'];
            html += '<tr>'
                + '<td style="border:1px solid #e5e7eb;padding:6px 8px;">' + escapeHtml(c.contract_no) + '</td>'
                + '<td style="border:1px solid #e5e7eb;padding:6px 8px;font-weight:bold;">' + escapeHtml(c.title) + '</td>'
                + '<td style="border:1px solid #e5e7eb;padding:6px 8px;">' + escapeHtml(c.supplier_name || c.party_b_name) + '</td>'
                + '<td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:right;">' + (c.total_amount || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) + '</td>'
                + '<td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">' + (c.sign_date || '-') + '</td>'
                + '<td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">' + (c.delivery_date || '-') + '</td>'
                + '<td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;"><span style="color:' + s[1] + ';background:' + s[2] + ';border-radius:4px;padding:1px 8px;font-size:11px;">' + s[0] + '</span></td>'
                + '<td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;white-space:nowrap;">'
                + '<button class="btn btn-primary" style="padding:2px 8px;font-size:11px;" onclick="window.open(apiBase+\'/pm/contracts/' + c.id + '/print\')">🖨 文书</button>'
                + '<button class="btn btn-secondary" style="padding:2px 8px;font-size:11px;margin-left:4px;" onclick="showContractForm(' + c.id + ')">✏</button>'
                + (c.status !== 'SIGNED' ? '<button class="btn btn-secondary" style="padding:2px 8px;font-size:11px;margin-left:4px;" onclick="setContractStatus(' + c.id + ',\'SIGNED\')">✍签署</button>' : '')
                + '<button class="btn btn-danger" style="padding:2px 8px;font-size:11px;margin-left:4px;" onclick="deleteContract(' + c.id + ')">🗑</button>'
                + '</td></tr>';
        });
        html += '</tbody></table>';
        el.innerHTML = html;
    });
}

function _ctInput(id, label, val, type, ph) {
    return '<div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">' + label + '</label>'
        + '<input id="' + id + '" type="' + (type || 'text') + '" value="' + (val || '') + '" placeholder="' + (ph || '') + '"'
        + ' style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;box-sizing:border-box;"></div>';
}

function showContractForm(id) {
    var wrap = document.getElementById('contract-form-wrap');
    var listWrap = document.getElementById('contract-list-wrap');
    if (!wrap) return;
    listWrap.style.display = 'none';
    wrap.style.display = 'block';
    wrap.innerHTML = '<div style="color:#888;padding:20px;">加载中...</div>';
    var partyA = JSON.parse(localStorage.getItem('erp_party_a') || 'null') || {};
    var today = new Date().toISOString().slice(0, 10);
    var base = {
        title: '', supplier_id: '', purchase_order_id: '',
        party_a_name: partyA.name || '', party_a_address: partyA.address || '',
        party_a_contact: partyA.contact || '', party_a_phone: partyA.phone || '',
        party_b_name: '', party_b_address: '', party_b_contact: '', party_b_phone: '',
        total_amount: 0, sign_date: today, delivery_date: '', delivery_location: '',
        payment_terms: '', quality_terms: DEFAULT_QUALITY, acceptance_terms: DEFAULT_ACCEPT,
        warranty_months: 12, breach_rate: 5, special_terms: '', legal_declaration: DEFAULT_LEGAL,
        remark: '', items: [{ material_code: '', material_name: '', spec: '', quantity: 1, unit: '', unit_price: 0, delivery_date: '' }]
    };
    var editing = false;
    var loadDetail = id ? fetch(apiBase + '/pm/contracts/' + id, { headers: authHeaders }).then(r => r.json()).then(d => d.data) : Promise.resolve(null);
    var loadOrders = fetch(apiBase + '/pm/orders', { headers: authHeaders }).then(r => r.json()).then(d => (d.data && d.data.items) || []).catch(() => []);
    var loadSups = fetch(apiBase + '/pm/suppliers', { headers: authHeaders }).then(r => r.json()).then(d => (d.data && d.data.items) || []).catch(() => []);
    Promise.all([loadDetail, loadOrders, loadSups]).then(function (rs) {
        var c = rs[0];
        var orders = rs[1]; var sups = rs[2];
        if (c) { editing = true; Object.assign(base, c); }
        window._ctSups = sups;
        window._ctOrderCache = orders;
        var orderOpts = '<option value="">（不关联，手动填写）</option>' + orders.map(function (o) {
            return '<option value="' + o.id + '"' + (base.purchase_order_id === o.id ? ' selected' : '') + '>' + escapeHtml(o.order_no || o.po_no) + '｜' + escapeHtml(o.project_name || '') + '｜¥' + (o.total_amount || 0) + '</option>';
        }).join('');
        var supOpts = '<option value="">（手动填写乙方）</option>' + sups.map(function (s) {
            return '<option value="' + s.id + '"' + (base.supplier_id === s.id ? ' selected' : '') + '>' + escapeHtml(s.name) + '</option>';
        }).join('');
        var payOpts = ['货到付款', '预付30%，到货验收后付60%，质保金10%满一年支付', '预付50%，到货付50%', '月结30天', '月结60天', '全额预付'];
        var paySel = '<option value="">（自定义填写）</option>' + payOpts.map(function (p) {
            return '<option' + (base.payment_terms === p ? ' selected' : '') + '>' + p + '</option>';
        }).join('');

        wrap.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <h3 style="margin:0;font-size:15px;">${editing ? '✏ 编辑合同' : '➕ 新建采购合同'}</h3>
            <div style="display:flex;gap:8px;">
                <button class="btn btn-primary" onclick="saveContract(${editing ? c.id : 0})">💾 保存合同</button>
                <button class="btn btn-secondary" onclick="closeContractForm()">返回列表</button>
            </div>
        </div>
        <div style="background:#f8fafc;border-radius:8px;padding:14px;margin-bottom:12px;">
            <div style="font-size:13px;font-weight:600;color:#1e40af;margin-bottom:10px;">📝 基本信息</div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;">
                ${_ctInput('ct-title', '合同名称 *', base.title, 'text', '如：机器人标准件采购合同')}
                <div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">关联采购订单（带入供应商和明细）</label>
                    <select id="ct-order" onchange="fillContractFromOrder(this.value)" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;box-sizing:border-box;">${orderOpts}</select></div>
                <div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">乙方供应商</label>
                    <select id="ct-supplier" onchange="fillSupplierToPartyB(this.value)" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;box-sizing:border-box;">${supOpts}</select></div>
                ${_ctInput('ct-total', '合同总金额（元，含税）', base.total_amount, 'number')}
                ${_ctInput('ct-sign-date', '签订日期', base.sign_date, 'date')}
                ${_ctInput('ct-delivery-date', '交付日期', base.delivery_date, 'date')}
            </div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
            <div style="background:#eff6ff;border-radius:8px;padding:14px;">
                <div style="font-size:13px;font-weight:600;color:#1e40af;margin-bottom:10px;">🏢 甲方（采购方）</div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                    ${_ctInput('ct-a-name', '单位名称', base.party_a_name)}
                    ${_ctInput('ct-a-address', '地址', base.party_a_address)}
                    ${_ctInput('ct-a-contact', '联系人', base.party_a_contact)}
                    ${_ctInput('ct-a-phone', '电话', base.party_a_phone)}
                </div>
                <div style="font-size:11px;color:#64748b;margin-top:6px;">💡 甲方信息保存后自动记住，下次不用重复填</div>
            </div>
            <div style="background:#f0fdf4;border-radius:8px;padding:14px;">
                <div style="font-size:13px;font-weight:600;color:#047857;margin-bottom:10px;">🏭 乙方（供货方）</div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                    ${_ctInput('ct-b-name', '单位名称', base.party_b_name)}
                    ${_ctInput('ct-b-address', '地址', base.party_b_address)}
                    ${_ctInput('ct-b-contact', '联系人', base.party_b_contact)}
                    ${_ctInput('ct-b-phone', '电话', base.party_b_phone)}
                </div>
            </div>
        </div>
        <div style="margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <div style="font-size:13px;font-weight:600;color:#1e40af;">📦 合同标的明细</div>
                <button class="btn btn-secondary" style="padding:4px 12px;font-size:12px;" onclick="addContractItemRow()">➕ 加一行</button>
            </div>
            <div style="overflow-x:auto;"><table id="ct-items-table" style="width:100%;border-collapse:collapse;font-size:12px;table-layout:fixed;">
                <thead><tr style="background:#f5f5f5;">
                    <th style="border:1px solid #d1d5db;padding:5px;width:90px;">物料编码</th>
                    <th style="border:1px solid #d1d5db;padding:5px;">物料名称</th>
                    <th style="border:1px solid #d1d5db;padding:5px;width:110px;">规格型号</th>
                    <th style="border:1px solid #d1d5db;padding:5px;width:70px;">数量</th>
                    <th style="border:1px solid #d1d5db;padding:5px;width:55px;">单位</th>
                    <th style="border:1px solid #d1d5db;padding:5px;width:90px;">单价</th>
                    <th style="border:1px solid #d1d5db;padding:5px;width:100px;">金额</th>
                    <th style="border:1px solid #d1d5db;padding:5px;width:110px;">交付日期</th>
                    <th style="border:1px solid #d1d5db;padding:5px;width:40px;"></th>
                </tr></thead><tbody></tbody>
            </table></div>
        </div>
        <div style="background:#f8fafc;border-radius:8px;padding:14px;margin-bottom:12px;">
            <div style="font-size:13px;font-weight:600;color:#1e40af;margin-bottom:10px;">⚖️ 合同条款（可直接修改）</div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:10px;">
                <div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">付款方式</label>
                    <select id="ct-pay-sel" onchange="if(this.value)document.getElementById('ct-payment').value=this.value" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;box-sizing:border-box;">${paySel}</select></div>
                ${_ctInput('ct-delivery-loc', '交付地点', base.delivery_location, 'text', '如：甲方工厂仓库')}
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                    ${_ctInput('ct-warranty', '质保期(月)', base.warranty_months, 'number')}
                    ${_ctInput('ct-breach', '违约金比例%', base.breach_rate, 'number')}
                </div>
            </div>
            <div style="display:grid;gap:10px;">
                <div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">付款方式条款</label><textarea id="ct-payment" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;box-sizing:border-box;min-height:44px;">${base.payment_terms || ''}</textarea></div>
                <div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">质量标准</label><textarea id="ct-quality" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;box-sizing:border-box;min-height:44px;">${escapeHtml(base.quality_terms)}</textarea></div>
                <div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">验收标准</label><textarea id="ct-accept" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;box-sizing:border-box;min-height:44px;">${escapeHtml(base.acceptance_terms)}</textarea></div>
                <div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">特别约定（选填）</label><textarea id="ct-special" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;box-sizing:border-box;min-height:44px;">${escapeHtml(base.special_terms)}</textarea></div>
            </div>
        </div>
        <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:14px;margin-bottom:12px;">
            <details ${editing ? '' : 'open'}>
                <summary style="font-size:13px;font-weight:600;color:#92400e;cursor:pointer;">📜 法律声明（默认已附标准条款，可修改）</summary>
                <textarea id="ct-legal" style="width:100%;padding:8px 10px;border:1px solid #fde68a;border-radius:6px;box-sizing:border-box;min-height:150px;margin-top:8px;font-size:12px;line-height:1.8;">${escapeHtml(base.legal_declaration)}</textarea>
            </details>
        </div>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-bottom:20px;">
            <button class="btn btn-primary" onclick="saveContract(${editing ? c.id : 0})">💾 保存合同</button>
            <button class="btn btn-secondary" onclick="closeContractForm()">取消</button>
        </div>`;
        (base.items && base.items.length ? base.items : [{}]).forEach(function (it) { addContractItemRow(it); });
    });
}

function _ctItemRowHtml(it) {
    it = it || {};
    return '<tr>'
        + '<td style="border:1px solid #e5e7eb;padding:3px;"><input id="ci-code" value="' + (it.material_code || '') + '" style="width:100%;border:none;padding:4px;box-sizing:border-box;"></td>'
        + '<td style="border:1px solid #e5e7eb;padding:3px;"><input id="ci-name" value="' + (it.material_name || '') + '" placeholder="物料名称" style="width:100%;border:none;padding:4px;box-sizing:border-box;"></td>'
        + '<td style="border:1px solid #e5e7eb;padding:3px;"><input id="ci-spec" value="' + (it.spec || '') + '" style="width:100%;border:none;padding:4px;box-sizing:border-box;"></td>'
        + '<td style="border:1px solid #e5e7eb;padding:3px;"><input id="ci-qty" type="number" value="' + (it.quantity != null ? it.quantity : 1) + '" onchange="_ctRecalcRow(this)" style="width:100%;border:none;padding:4px;box-sizing:border-box;"></td>'
        + '<td style="border:1px solid #e5e7eb;padding:3px;"><input id="ci-unit" value="' + (it.unit || '') + '" style="width:100%;border:none;padding:4px;box-sizing:border-box;"></td>'
        + '<td style="border:1px solid #e5e7eb;padding:3px;"><input id="ci-price" type="number" value="' + (it.unit_price != null ? it.unit_price : 0) + '" onchange="_ctRecalcRow(this)" style="width:100%;border:none;padding:4px;box-sizing:border-box;"></td>'
        + '<td style="border:1px solid #e5e7eb;padding:3px;"><input id="ci-amount" type="number" value="' + (it.amount != null ? it.amount : 0) + '" onchange="_ctRecalcRow(this)" style="width:100%;border:none;padding:4px;box-sizing:border-box;background:#f9fafb;"></td>'
        + '<td style="border:1px solid #e5e7eb;padding:3px;"><input id="ci-dd" type="date" value="' + (it.delivery_date || '') + '" style="width:100%;border:none;padding:4px;box-sizing:border-box;"></td>'
        + '<td style="border:1px solid #e5e7eb;padding:3px;text-align:center;"><button class="btn btn-danger" style="padding:2px 6px;font-size:11px;" onclick="this.closest(\'tr\').remove();_ctSumTotal()">✕</button></td>'
        + '</tr>';
}

function addContractItemRow(it) {
    var tb = document.querySelector('#ct-items-table tbody');
    if (!tb) return;
    tb.insertAdjacentHTML('beforeend', _ctItemRowHtml(it));
}

function _ctRecalcRow(input) {
    var tr = input.closest('tr');
    var q = parseFloat(tr.querySelector('#ci-qty').value) || 0;
    var p = parseFloat(tr.querySelector('#ci-price').value) || 0;
    var a = tr.querySelector('#ci-amount');
    var changed = input.id;
    if (changed === 'ci-amount') {
        // 手动改金额不动单价
    } else {
        a.value = (q * p).toFixed(2);
    }
    _ctSumTotal();
}

function _ctSumTotal() {
    var sum = 0;
    document.querySelectorAll('#ct-items-table tbody #ci-amount').forEach(function (a) { sum += parseFloat(a.value) || 0; });
    var t = document.getElementById('ct-total');
    if (t && sum > 0) t.value = sum.toFixed(2);
}

function fillSupplierToPartyB(sid) {
    if (!sid) return;
    var s = (window._ctSups || []).find(function (x) { return x.id == sid; });
    if (!s) return;
    document.getElementById('ct-supplier').value = sid;
    document.getElementById('ct-b-name').value = s.name || '';
    document.getElementById('ct-b-address').value = s.address || '';
    document.getElementById('ct-b-contact').value = s.contact || '';
    document.getElementById('ct-b-phone').value = s.phone || '';
}

window._ctOrderCache = [];
function fillContractFromOrder(oid) {
    if (!oid) return;
    var order = (window._ctOrderCache || []).find(function (o) { return o.id == oid; });
    if (!order) {
        fetch(apiBase + '/pm/orders', { headers: authHeaders }).then(r => r.json()).then(d => {
            window._ctOrderCache = (d.data && d.data.items) || [];
            fillContractFromOrder(oid);
        });
        return;
    }
    // 带入乙方
    var supSel = document.getElementById('ct-supplier');
    var matched = (window._ctSups || []).find(function (s) { return order.supplier_id && s.id === order.supplier_id; });
    if (order.supplier_id && matched) {
        supSel.value = order.supplier_id;
        fillSupplierToPartyB(order.supplier_id);
    } else if (order.supplier_name) {
        document.getElementById('ct-b-name').value = order.supplier_name;
    }
    if (order.project_id) window._ctProjId = order.project_id;
    // 带入明细
    var tb = document.querySelector('#ct-items-table tbody');
    tb.innerHTML = '';
    (order.items || []).forEach(function (it) {
        addContractItemRow({
            material_code: it.material_code || '', material_name: it.material_name || '',
            spec: it.material_spec || '', quantity: it.quantity || 1, unit: it.unit || '',
            unit_price: it.unit_price || 0, delivery_date: it.delivery_date || ''
        });
    });
    _ctSumTotal();
}

function saveContract(id) {
    var items = [];
    document.querySelectorAll('#ct-items-table tbody tr').forEach(function (tr) {
        var name = tr.querySelector('#ci-name').value.trim();
        if (!name) return;
        items.push({
            material_code: tr.querySelector('#ci-code').value.trim(),
            material_name: name,
            spec: tr.querySelector('#ci-spec').value.trim(),
            quantity: parseFloat(tr.querySelector('#ci-qty').value) || 1,
            unit: tr.querySelector('#ci-unit').value.trim(),
            unit_price: parseFloat(tr.querySelector('#ci-price').value) || 0,
            amount: parseFloat(tr.querySelector('#ci-amount').value) || 0,
            delivery_date: tr.querySelector('#ci-dd').value
        });
    });
    var data = {
        title: document.getElementById('ct-title').value.trim(),
        purchase_order_id: parseInt(document.getElementById('ct-order').value) || null,
        supplier_id: parseInt(document.getElementById('ct-supplier').value) || null,
        project_id: window._ctProjId || null,
        total_amount: parseFloat(document.getElementById('ct-total').value) || 0,
        sign_date: document.getElementById('ct-sign-date').value,
        delivery_date: document.getElementById('ct-delivery-date').value,
        party_a_name: document.getElementById('ct-a-name').value.trim(),
        party_a_address: document.getElementById('ct-a-address').value.trim(),
        party_a_contact: document.getElementById('ct-a-contact').value.trim(),
        party_a_phone: document.getElementById('ct-a-phone').value.trim(),
        party_b_name: document.getElementById('ct-b-name').value.trim(),
        party_b_address: document.getElementById('ct-b-address').value.trim(),
        party_b_contact: document.getElementById('ct-b-contact').value.trim(),
        party_b_phone: document.getElementById('ct-b-phone').value.trim(),
        delivery_location: document.getElementById('ct-delivery-loc').value.trim(),
        payment_terms: document.getElementById('ct-payment').value.trim(),
        quality_terms: document.getElementById('ct-quality').value.trim(),
        acceptance_terms: document.getElementById('ct-accept').value.trim(),
        warranty_months: parseInt(document.getElementById('ct-warranty').value) || 12,
        breach_rate: parseFloat(document.getElementById('ct-breach').value) || 5,
        special_terms: document.getElementById('ct-special').value.trim(),
        legal_declaration: document.getElementById('ct-legal').value,
        items: items
    };
    if (!data.title) { showToast('请填写合同名称', 'warning'); return; }
    // 甲方信息记住，下次免填
    localStorage.setItem('erp_party_a', JSON.stringify({
        name: data.party_a_name, address: data.party_a_address,
        contact: data.party_a_contact, phone: data.party_a_phone
    }));
    var url = apiBase + '/pm/contracts' + (id ? '/' + id : '');
    fetch(url, { method: id ? 'PUT' : 'POST', headers: Object.assign({ 'Content-Type': 'application/json' }, authHeaders), body: JSON.stringify(data) })
        .then(r => r.json()).then(d => {
            if (d && (d.success || d.data)) {
                showToast('合同已保存', 'success');
                closeContractForm();
                loadContracts();
            } else {
                showToast((d && (d.detail || d.message)) || '保存失败', 'error');
            }
        }).catch(() => showToast('保存失败', 'error'));
}

function closeContractForm() {
    var wrap = document.getElementById('contract-form-wrap');
    var listWrap = document.getElementById('contract-list-wrap');
    if (wrap) wrap.style.display = 'none';
    if (listWrap) listWrap.style.display = 'block';
}

function setContractStatus(id, status) {
    fetch(apiBase + '/pm/contracts/' + id, {
        method: 'PUT',
        headers: Object.assign({ 'Content-Type': 'application/json' }, authHeaders),
        body: JSON.stringify({ status: status })
    }).then(r => r.json()).then(d => {
        showToast(status === 'SIGNED' ? '已标记为签署' : '状态已更新', 'success');
        loadContracts();
    }).catch(() => showToast('操作失败', 'error'));
}

function deleteContract(id) {
    if (!confirm('确定删除该合同？删除后不可恢复。')) return;
    fetch(apiBase + '/pm/contracts/' + id, { method: 'DELETE', headers: authHeaders }).then(r => r.json()).then(d => {
        showToast('合同已删除', 'success');
        loadContracts();
    }).catch(() => showToast('删除失败', 'error'));
}

