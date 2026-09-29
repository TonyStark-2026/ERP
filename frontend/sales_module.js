/* ============================================================
 * 销售管理 V2 前端模块（报价/退货/应收/收款）
 * 独立文件，通过 <script src> 引入 index.html
 * ============================================================ */
if (typeof escapeHtml === 'undefined') {
    window.escapeHtml = function(s){ if(s===null||s===undefined)return ''; var d=document.createElement('div'); d.textContent=String(s); return d.innerHTML; };
}
var _smTab = 'quotations';

function _renderSalesV2Impl() {
    setTimeout(()=>switchSMTab('quotations'),80);
    return `<div style="padding:16px;"><div class="card">
        <div class="card-title" style="display:flex;justify-content:space-between;align-items:center;background:linear-gradient(135deg,#0891b2,#7c3aed);color:#fff;border-radius:8px 8px 0 0;padding:12px 16px;margin:-16px -16px 12px -16px;">
            <span style="font-size:16px;font-weight:bold;">💼 销售财务中心</span>
            <span style="font-size:12px;">报价 · 退货 · 应收 · 收款核销</span>
        </div>
        <div style="padding:12px 16px;">
            <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-bottom:16px;">
                <div class="sm-stat"><div class="num" id="sm-stat-qt">-</div><div class="lbl">报价单</div></div>
                <div class="sm-stat"><div class="num" id="sm-stat-ar">-</div><div class="lbl">应收余额</div></div>
                <div class="sm-stat"><div class="num" id="sm-stat-rcv">-</div><div class="lbl">已收款</div></div>
                <div class="sm-stat"><div class="num" id="sm-stat-over">-</div><div class="lbl">逾期</div></div>
            </div>
            <div style="display:flex;gap:4px;border-bottom:2px solid #0891b2;margin-bottom:16px;flex-wrap:wrap;">
                <button class="btn sm-tab-btn active" data-s-tab="quotations" onclick="switchSMTab('quotations')">💬 报价管理</button>
                <button class="btn sm-tab-btn" data-s-tab="returns" onclick="switchSMTab('returns')">↩️ 退货管理</button>
                <button class="btn sm-tab-btn" data-s-tab="receivables" onclick="switchSMTab('receivables')">📋 应收管理</button>
                <button class="btn sm-tab-btn" data-s-tab="receipts" onclick="switchSMTab('receipts')">💰 收款核销</button>
            </div>
            <div id="sm-tab-quotations" class="sm-tab-panel"></div>
            <div id="sm-tab-returns" class="sm-tab-panel" style="display:none;"></div>
            <div id="sm-tab-receivables" class="sm-tab-panel" style="display:none;"></div>
            <div id="sm-tab-receipts" class="sm-tab-panel" style="display:none;"></div>
        </div>
    </div></div>
    <style>
        .sm-tab-btn{padding:4px 12px;font-size:12px;border:1px solid #e5e7eb;background:#fff;color:#666;border-radius:6px;cursor:pointer;transition:all .2s;}
        .sm-tab-btn:hover{background:#ecfeff;border-color:#0891b2;}
        .sm-tab-btn.active{background:linear-gradient(135deg,#0891b2,#7c3aed);color:#fff;border-color:transparent;}
        .sm-stat{background:linear-gradient(135deg,#ecfeff,#f3e8ff);border:1px solid #a5f3fc;border-radius:10px;padding:12px;text-align:center;}
        .sm-stat .num{font-size:22px;font-weight:bold;color:#0891b2;}
        .sm-stat .lbl{font-size:11px;color:#666;margin-top:4px;}
        table.sm-table{width:100%;border-collapse:collapse;font-size:12px;}
        .sm-table th{background:#f1f5f9;padding:8px;text-align:left;border-bottom:2px solid #cbd5e1;color:#475569;}
        .sm-table td{padding:8px;border-bottom:1px solid #e2e8f0;}
        .sm-table tr:hover td{background:#f8fafc;}
    </style>`;
}

function switchSMTab(tab){
    _smTab=tab;
    document.querySelectorAll('.sm-tab-btn').forEach(b=>b.classList.toggle('active',b.getAttribute('data-s-tab')===tab));
    document.querySelectorAll('.sm-tab-panel').forEach(p=>p.style.display='none');
    const map={quotations:'sm-tab-quotations',returns:'sm-tab-returns',receivables:'sm-tab-receivables',receipts:'sm-tab-receipts'};
    const el=document.getElementById(map[tab]); if(!el)return; el.style.display='block';
    if(tab==='quotations') el.innerHTML=smQuotationsUI(),setTimeout(loadSMQuotations,30);
    if(tab==='returns') el.innerHTML=smReturnsUI(),setTimeout(loadSMReturns,30);
    if(tab==='receivables') el.innerHTML=smReceivablesUI(),setTimeout(loadSMReceivables,30);
    if(tab==='receipts') el.innerHTML=smReceiptsUI(),setTimeout(loadSMReceipts,30);
}

function loadSMOverview(){
    fetch(apiBase+'/sm/overview',{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success)return; const d=res.data||{};
        document.getElementById('sm-stat-qt').textContent=d.quotation_count||0;
        document.getElementById('sm-stat-ar').textContent='¥'+(d.total_balance||0).toFixed(0);
        document.getElementById('sm-stat-rcv').textContent='¥'+(d.total_received||0).toFixed(0);
        document.getElementById('sm-stat-over').textContent=d.overdue_count||0;
    }).catch(e=>console.error(e));
}

// ===== 报价 =====
function smQuotationsUI(){
    return `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <input id="sm-qt-kw" placeholder="报价单号" style="width:160px;padding:5px 8px;font-size:12px;border:1px solid #cbd5e1;border-radius:6px;" onkeyup="if(event.key==='Enter')loadSMQuotations()">
        <button class="btn btn-primary" style="padding:5px 12px;font-size:12px;" onclick="smQuotationForm()">➕ 新增报价单</button>
    </div><div id="sm-qt-list" style="overflow-x:auto;"><div style="color:#888;padding:20px;text-align:center;">加载中...</div></div>`;
}
function loadSMQuotations(){
    const kw=(document.getElementById('sm-qt-kw')||{}).value||'';
    let url=apiBase+'/sm/quotations?'; if(kw)url+='keyword='+encodeURIComponent(kw)+'&';
    fetch(url,{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){document.getElementById('sm-qt-list').innerHTML='<div style="color:#c0392b;padding:16px;">'+escapeHtml(res.message)+'</div>';return;}
        const items=(res.data&&res.data.items)||[];
        if(!items.length){document.getElementById('sm-qt-list').innerHTML='<div style="color:#888;padding:20px;text-align:center;">暂无报价单</div>';return;}
        let h='<table class="sm-table"><thead><tr><th>报价单号</th><th>客户</th><th>报价日期</th><th>有效期至</th><th>币种</th><th>金额</th><th>状态</th><th>操作</th></tr></thead><tbody>';
        items.forEach(q=>{
            h+=`<tr><td style="font-weight:600;color:#0891b2;">${escapeHtml(q.quotation_no)}</td><td>${escapeHtml(q.customer_name||'-')}</td><td>${escapeHtml(q.quotation_date)}</td><td>${escapeHtml(q.valid_until||'-')}</td><td>${escapeHtml(q.currency)}</td><td style="text-align:right;font-weight:600;">¥${q.total_amount.toFixed(2)}</td><td>${escapeHtml(q.status_label)}</td><td><button class="btn" style="padding:2px 8px;font-size:11px;color:#dc2626;" onclick="deleteSMQuotation(${q.id})">删除</button></td></tr>`;
        });
        h+='</tbody></table>'; document.getElementById('sm-qt-list').innerHTML=h;
    });
}
function smQuotationForm(){
    const m=document.createElement('div'); m.className='fixed'; m.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    m.innerHTML=`<div style="background:#fff;border-radius:10px;padding:20px;width:400px;max-width:92vw;">
        <h3 style="margin:0 0 16px;color:#0891b2;">新增报价单</h3>
        <div style="display:grid;gap:10px;font-size:12px;">
            <div><label>客户ID</label><input id="qt-cid" type="number" placeholder="客户ID" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div><label>有效期至</label><input id="qt-vu" type="date" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div><label>币种</label><select id="qt-cur" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"><option value="CNY">人民币</option><option value="USD">美元</option><option value="EUR">欧元</option></select></div>
            <div><label>备注</label><input id="qt-rmk" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div style="color:#94a3b8;font-size:11px;">提示：报价单创建后可在明细中添加物料行</div>
        </div>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
            <button class="btn" style="padding:6px 14px;font-size:12px;" onclick="this.closest('.fixed').remove()">取消</button>
            <button class="btn btn-primary" style="padding:6px 14px;font-size:12px;" onclick="saveSMQuotation(this)">保存</button>
        </div></div>`;
    document.body.appendChild(m);
}
function saveSMQuotation(btn){
    const payload={customer_id:parseInt(document.getElementById('qt-cid').value)||null,valid_until:document.getElementById('qt-vu').value||null,currency:document.getElementById('qt-cur').value,remark:document.getElementById('qt-rmk').value,items:[]};
    fetch(apiBase+'/sm/quotations',{method:'POST',headers:{...authHeaders,'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json()).then(res=>{
        if(!res.success){showToast(res.message, 'error');return;} btn.closest('.fixed').remove(); loadSMQuotations(); loadSMOverview();
    });
}
function deleteSMQuotation(id){ if(!confirm('确认删除？'))return; fetch(apiBase+'/sm/quotations/'+id,{method:'DELETE',headers:authHeaders}).then(r=>r.json()).then(res=>{ if(!res.success){showToast(res.message, 'error');return;} loadSMQuotations(); loadSMOverview(); }); }

// ===== 退货 =====
function smReturnsUI(){
    return `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <span style="font-size:13px;color:#475569;font-weight:600;">销售退货单</span>
        <button class="btn btn-primary" style="padding:5px 12px;font-size:12px;" onclick="smReturnForm()">➕ 新增退货单</button>
    </div><div id="sm-ret-list" style="overflow-x:auto;"><div style="color:#888;padding:20px;text-align:center;">加载中...</div></div>`;
}
function loadSMReturns(){
    fetch(apiBase+'/sm/returns',{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){document.getElementById('sm-ret-list').innerHTML='<div style="color:#c0392b;padding:16px;">'+escapeHtml(res.message)+'</div>';return;}
        const items=(res.data&&res.data.items)||[];
        if(!items.length){document.getElementById('sm-ret-list').innerHTML='<div style="color:#888;padding:20px;text-align:center;">暂无退货单</div>';return;}
        let h='<table class="sm-table"><thead><tr><th>退货单号</th><th>客户</th><th>退货日期</th><th>原因</th><th>金额</th><th>状态</th><th>操作</th></tr></thead><tbody>';
        items.forEach(r=>{
            const ops=`<select onchange="updateSMReturnStatus(${r.id},this.value)" style="padding:2px;font-size:11px;border:1px solid #cbd5e1;border-radius:4px;"><option value="">--</option><option value="INSPECTING">质检中</option><option value="ACCEPTED">已接受</option><option value="REJECTED">已拒绝</option></select>`;
            h+=`<tr><td style="font-weight:600;color:#0891b2;">${escapeHtml(r.return_no)}</td><td>${escapeHtml(r.customer_name||'-')}</td><td>${escapeHtml(r.return_date)}</td><td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(r.reason||'-')}</td><td style="text-align:right;">¥${r.total_amount.toFixed(2)}</td><td>${escapeHtml(r.status_label)}</td><td>${ops}</td></tr>`;
        });
        h+='</tbody></table>'; document.getElementById('sm-ret-list').innerHTML=h;
    });
}
function smReturnForm(){
    const m=document.createElement('div'); m.className='fixed'; m.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    m.innerHTML=`<div style="background:#fff;border-radius:10px;padding:20px;width:400px;max-width:92vw;">
        <h3 style="margin:0 0 16px;color:#0891b2;">新增退货单</h3>
        <div style="display:grid;gap:10px;font-size:12px;">
            <div><label>客户ID</label><input id="ret-cid" type="number" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div><label>退货原因</label><textarea id="ret-reason" rows="3" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></textarea></div>
        </div>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
            <button class="btn" style="padding:6px 14px;font-size:12px;" onclick="this.closest('.fixed').remove()">取消</button>
            <button class="btn btn-primary" style="padding:6px 14px;font-size:12px;" onclick="saveSMReturn(this)">保存</button>
        </div></div>`;
    document.body.appendChild(m);
}
function saveSMReturn(btn){
    const payload={customer_id:parseInt(document.getElementById('ret-cid').value)||null,reason:document.getElementById('ret-reason').value,items:[]};
    fetch(apiBase+'/sm/returns',{method:'POST',headers:{...authHeaders,'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json()).then(res=>{ if(!res.success){showToast(res.message, 'error');return;} btn.closest('.fixed').remove(); loadSMReturns(); loadSMOverview(); });
}
function updateSMReturnStatus(id,status){ if(!status)return; fetch(apiBase+'/sm/returns/'+id+'/status',{method:'PUT',headers:{...authHeaders,'Content-Type':'application/json'},body:JSON.stringify({status})}).then(r=>r.json()).then(res=>{ if(!res.success){showToast(res.message, 'error');return;} loadSMReturns(); }); }

// ===== 应收 =====
function smReceivablesUI(){
    return `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <select id="sm-ar-status" style="padding:5px 8px;font-size:12px;border:1px solid #cbd5e1;border-radius:6px;" onchange="loadSMReceivables()"><option value="">全部状态</option><option value="PENDING">待收</option><option value="PARTIAL">部分收款</option><option value="SETTLED">已结清</option><option value="OVERDUE">逾期</option></select>
        <button class="btn btn-primary" style="padding:5px 12px;font-size:12px;" onclick="smReceivableForm()">➕ 新增应收单</button>
    </div><div id="sm-ar-list" style="overflow-x:auto;"><div style="color:#888;padding:20px;text-align:center;">加载中...</div></div>`;
}
function loadSMReceivables(){
    const st=(document.getElementById('sm-ar-status')||{}).value||'';
    let url=apiBase+'/sm/receivables?'; if(st)url+='status='+st+'&';
    fetch(url,{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){document.getElementById('sm-ar-list').innerHTML='<div style="color:#c0392b;padding:16px;">'+escapeHtml(res.message)+'</div>';return;}
        const items=(res.data&&res.data.items)||[];
        if(!items.length){document.getElementById('sm-ar-list').innerHTML='<div style="color:#888;padding:20px;text-align:center;">暂无应收单</div>';return;}
        let h='<table class="sm-table"><thead><tr><th>应收单号</th><th>客户</th><th>来源</th><th>应收金额</th><th>已收</th><th>余额</th><th>到期日</th><th>状态</th></tr></thead><tbody>';
        items.forEach(r=>{
            const balColor=r.status==='OVERDUE'?'#dc2626':'#16a34a';
            h+=`<tr><td style="font-weight:600;color:#0891b2;">${escapeHtml(r.receivable_no)}</td><td>${escapeHtml(r.customer_name||'-')}</td><td>${escapeHtml(r.source_label)}<br><span style="color:#94a3b8;font-size:10px;">${escapeHtml(r.source_no||'')}</span></td><td style="text-align:right;">¥${r.amount.toFixed(2)}</td><td style="text-align:right;color:#16a34a;">¥${r.received_amount.toFixed(2)}</td><td style="text-align:right;font-weight:600;color:${balColor};">¥${r.balance.toFixed(2)}</td><td>${escapeHtml(r.due_date||'-')}</td><td>${escapeHtml(r.status_label)}</td></tr>`;
        });
        h+='</tbody></table>'; document.getElementById('sm-ar-list').innerHTML=h;
    });
}
function smReceivableForm(){
    const m=document.createElement('div'); m.className='fixed'; m.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    m.innerHTML=`<div style="background:#fff;border-radius:10px;padding:20px;width:400px;max-width:92vw;">
        <h3 style="margin:0 0 16px;color:#0891b2;">新增应收单</h3>
        <div style="display:grid;gap:10px;font-size:12px;">
            <div><label>客户ID</label><input id="ar-cid" type="number" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div><label>应收金额</label><input id="ar-amt" type="number" step="0.01" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div><label>到期日</label><input id="ar-due" type="date" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div><label>来源单号</label><input id="ar-src" placeholder="如销售订单号" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
        </div>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
            <button class="btn" style="padding:6px 14px;font-size:12px;" onclick="this.closest('.fixed').remove()">取消</button>
            <button class="btn btn-primary" style="padding:6px 14px;font-size:12px;" onclick="saveSMReceivable(this)">保存</button>
        </div></div>`;
    document.body.appendChild(m);
}
function saveSMReceivable(btn){
    const payload={customer_id:parseInt(document.getElementById('ar-cid').value)||null,amount:parseFloat(document.getElementById('ar-amt').value)||0,due_date:document.getElementById('ar-due').value,source_no:document.getElementById('ar-src').value,source_type:'SALES_ORDER'};
    fetch(apiBase+'/sm/receivables',{method:'POST',headers:{...authHeaders,'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json()).then(res=>{ if(!res.success){showToast(res.message, 'error');return;} btn.closest('.fixed').remove(); loadSMReceivables(); loadSMOverview(); });
}

// ===== 收款 =====
function smReceiptsUI(){
    return `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <span style="font-size:13px;color:#475569;font-weight:600;">收款单（自动核销应收）</span>
        <button class="btn btn-primary" style="padding:5px 12px;font-size:12px;" onclick="smReceiptForm()">➕ 新增收款单</button>
    </div><div id="sm-rc-list" style="overflow-x:auto;"><div style="color:#888;padding:20px;text-align:center;">加载中...</div></div>`;
}
function loadSMReceipts(){
    fetch(apiBase+'/sm/receipts',{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){document.getElementById('sm-rc-list').innerHTML='<div style="color:#c0392b;padding:16px;">'+escapeHtml(res.message)+'</div>';return;}
        const items=(res.data&&res.data.items)||[];
        if(!items.length){document.getElementById('sm-rc-list').innerHTML='<div style="color:#888;padding:20px;text-align:center;">暂无收款单</div>';return;}
        let h='<table class="sm-table"><thead><tr><th>收款单号</th><th>客户</th><th>收款日期</th><th>金额</th><th>收款方式</th><th>核销应收</th><th>状态</th></tr></thead><tbody>';
        items.forEach(r=>{
            h+=`<tr><td style="font-weight:600;color:#0891b2;">${escapeHtml(r.receipt_no)}</td><td>${escapeHtml(r.customer_name||'-')}</td><td>${escapeHtml(r.receipt_date)}</td><td style="text-align:right;font-weight:600;color:#16a34a;">¥${r.amount.toFixed(2)}</td><td>${escapeHtml(r.method_label||'-')}</td><td>${r.receivable_id?'#'+r.receivable_id:'-'}</td><td>${escapeHtml(r.status)}</td></tr>`;
        });
        h+='</tbody></table>'; document.getElementById('sm-rc-list').innerHTML=h;
    });
}
function smReceiptForm(){
    const m=document.createElement('div'); m.className='fixed'; m.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    m.innerHTML=`<div style="background:#fff;border-radius:10px;padding:20px;width:400px;max-width:92vw;">
        <h3 style="margin:0 0 16px;color:#0891b2;">新增收款单</h3>
        <div style="display:grid;gap:10px;font-size:12px;">
            <div><label>客户ID</label><input id="rc-cid" type="number" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div><label>收款金额</label><input id="rc-amt" type="number" step="0.01" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div><label>核销应收单ID</label><input id="rc-rid" type="number" placeholder="应收单ID（可留空）" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div><label>收款方式</label><select id="rc-pm" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"><option value="BANK">银行转账</option><option value="CASH">现金</option><option value="ALIPAY">支付宝</option><option value="WECHAT">微信</option></select></div>
        </div>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
            <button class="btn" style="padding:6px 14px;font-size:12px;" onclick="this.closest('.fixed').remove()">取消</button>
            <button class="btn btn-primary" style="padding:6px 14px;font-size:12px;" onclick="saveSMReceipt(this)">保存</button>
        </div></div>`;
    document.body.appendChild(m);
}
function saveSMReceipt(btn){
    const payload={customer_id:parseInt(document.getElementById('rc-cid').value)||null,amount:parseFloat(document.getElementById('rc-amt').value)||0,receivable_id:parseInt(document.getElementById('rc-rid').value)||null,payment_method:document.getElementById('rc-pm').value};
    fetch(apiBase+'/sm/receipts',{method:'POST',headers:{...authHeaders,'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json()).then(res=>{ if(!res.success){showToast(res.message, 'error');return;} btn.closest('.fixed').remove(); loadSMReceipts(); loadSMReceivables(); loadSMOverview(); });
}

window._renderSalesV2Impl=function(){ const html=_renderSalesV2Impl(); setTimeout(loadSMOverview,100); return html; };
