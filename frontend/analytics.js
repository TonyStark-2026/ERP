/* ============================================================
 * 报表与分析 前端模块
 * 自定义报表 / 管理驾驶舱 / 发票合规记录
 * ============================================================ */
if (typeof escapeHtml === 'undefined') {
    window.escapeHtml = function(s) {
        if (s === null || s === undefined) return '';
        var d = document.createElement('div');
        d.textContent = String(s);
        return d.innerHTML;
    };
}

var _anTab = 'cockpit';

function _renderAnalyticsImpl() {
    setTimeout(() => switchAnTab('cockpit'), 80);
    return `
    <div style="padding:16px;">
        <div class="card">
            <div class="card-title" style="display:flex;justify-content:space-between;align-items:center;background:linear-gradient(135deg,#7c3aed,#4338ca);color:#fff;border-radius:8px 8px 0 0;padding:12px 16px;margin:-16px -16px 12px -16px;">
                <span style="font-size:16px;font-weight:bold;">📈 报表分析</span>
                <span style="font-size:12px;">管理驾驶舱 / 自定义报表 / 发票合规</span>
            </div>
            <div style="padding:12px 16px;">
                <div style="display:flex;gap:4px;border-bottom:2px solid #4338ca;margin-bottom:16px;flex-wrap:wrap;">
                    <button class="btn an-tab-btn active" data-a-tab="cockpit" onclick="switchAnTab('cockpit')">📊 管理驾驶舱</button>
                    <button class="btn an-tab-btn" data-a-tab="reports" onclick="switchAnTab('reports')">📋 自定义报表</button>
                    <button class="btn an-tab-btn" data-a-tab="invoices" onclick="switchAnTab('invoices')">🧾 发票合规</button>
                </div>
                <div id="an-tab-cockpit" class="an-tab-panel"></div>
                <div id="an-tab-reports" class="an-tab-panel" style="display:none;"></div>
                <div id="an-tab-invoices" class="an-tab-panel" style="display:none;"></div>
            </div>
        </div>
    </div>
    <style>
        .an-tab-btn{padding:4px 12px;font-size:12px;border:1px solid #e5e7eb;background:#fff;color:#666;border-radius:6px;cursor:pointer;transition:all .2s;}
        .an-tab-btn:hover{background:#f5f3ff;border-color:#4338ca;}
        .an-tab-btn.active{background:linear-gradient(135deg,#7c3aed,#4338ca);color:#fff;border-color:transparent;}
        .an-table{width:100%;border-collapse:collapse;font-size:12px;}
        .an-table th{background:#f1f5f9;padding:8px 10px;text-align:left;border-bottom:2px solid #cbd5e1;color:#475569;font-weight:600;}
        .an-table td{padding:8px 10px;border-bottom:1px solid #e2e8f0;color:#334155;}
        .an-table tr:hover td{background:#f8fafc;}
        .an-metric-card{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;box-shadow:0 1px 3px rgba(0,0,0,.06);}
        .an-metric-card .lbl{font-size:11px;color:#666;margin-bottom:4px;}
        .an-metric-card .val{font-size:20px;font-weight:bold;}
        .an-metric-card .sub{font-size:11px;color:#999;margin-top:2px;}
        .an-input{padding:6px 8px;border:1px solid #cbd5e1;border-radius:6px;font-size:12px;width:100%;}
    </style>`;
}

function switchAnTab(tab) {
    _anTab = tab;
    document.querySelectorAll('.an-tab-btn').forEach(b => b.classList.toggle('active', b.getAttribute('data-a-tab') === tab));
    document.querySelectorAll('.an-tab-panel').forEach(p => p.style.display = 'none');
    const el = document.getElementById('an-tab-' + tab);
    if (!el) return;
    el.style.display = 'block';
    if (tab === 'cockpit') setTimeout(loadCockpit, 30);
    if (tab === 'reports') el.innerHTML = renderReportsUI(), setTimeout(loadReports, 30);
    if (tab === 'invoices') el.innerHTML = renderInvoiceChecksUI(), setTimeout(loadInvoiceChecks, 30);
}

// ========== 管理驾驶舱 ==========
function loadCockpit() {
    const el = document.getElementById('an-tab-cockpit');
    if (el) el.innerHTML = '<div style="text-align:center;padding:40px;color:#999;">加载中...</div>';
    fetch(apiBase + '/an/cockpit', { headers: authHeaders })
        .then(r => r.json()).then(res => {
            if (!res.success) return;
            const d = (res.data || {}).metrics || {};
            const p = res.data || {};
            const fin = d.finance || {};
            const cost = d.cost_variance || {};
            const inv = d.invoice_compliance || {};
            el.innerHTML = `
            <div style="font-size:12px;color:#666;margin-bottom:12px;">数据截止：${escapeHtml(p.as_of)}</div>
            <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin-bottom:16px;">
                <div class="an-metric-card"><div class="lbl">📦 采购总额</div><div class="val" style="color:#0891b2;">¥${((d.purchase||{}).amount||0).toLocaleString()}</div><div class="sub">${(d.purchase||{}).orders||0} 笔订单</div></div>
                <div class="an-metric-card"><div class="lbl">💼 销售总额</div><div class="val" style="color:#16a34a;">¥${((d.sales||{}).amount||0).toLocaleString()}</div><div class="sub">${(d.sales||{}).orders||0} 笔订单</div></div>
                <div class="an-metric-card"><div class="lbl">🏪 库存SKU</div><div class="val" style="color:#7c3aed;">${(d.inventory||{}).skus||0}</div><div class="sub">总量 ${(d.inventory||{}).quantity||0}</div></div>
                <div class="an-metric-card"><div class="lbl">⚠️ 呆滞库存</div><div class="val" style="color:#dc2626;">¥${((d.slow_moving||{}).value||0).toLocaleString()}</div><div class="sub">${(d.slow_moving||{}).count||0} 种物料</div></div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin-bottom:16px;">
                <div class="an-metric-card"><div class="lbl">💰 本期收入</div><div class="val" style="color:#16a34a;">¥${(fin.revenue||0).toLocaleString()}</div></div>
                <div class="an-metric-card"><div class="lbl">💸 本期费用</div><div class="val" style="color:#dc2626;">¥${(fin.expense||0).toLocaleString()}</div></div>
                <div class="an-metric-card"><div class="lbl">📈 净利润</div><div class="val" style="color:${(fin.net_profit||0) >= 0 ? '#16a34a' : '#dc2626'};">¥${(fin.net_profit||0).toLocaleString()}</div><div class="sub">试算${fin.balanced ? '平衡' : '不平衡'}</div></div>
                <div class="an-metric-card"><div class="lbl">📉 成本差异</div><div class="val" style="color:${(cost.total||0) <= 0 ? '#16a34a' : '#dc2626'};">¥${Math.abs(cost.total||0).toLocaleString()}</div><div class="sub">${cost.count||0} 条记录</div></div>
            </div>
            <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:14px;font-size:12px;">
                <b style="color:#92400e;">🧾 发票合规预警</b>
                <span style="color:#666;margin-left:10px;">不得抵扣发票 <b style="color:#dc2626;">${inv.non_deductible_alerts||0}</b> 张</span>
            </div>`;
        }).catch(e => { if (el) el.innerHTML = '<div style="color:#dc2626;">加载失败</div>'; });
}

// ========== 自定义报表 ==========
function renderReportsUI() {
    return `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <span style="font-size:12px;color:#666;">自定义报表（数据源：采购/销售/库存/生产/财务）</span>
        <button class="btn" style="padding:5px 14px;font-size:12px;background:#4338ca;color:#fff;border:none;border-radius:6px;cursor:pointer;" onclick="openReportModal()">+ 新建报表</button>
    </div>
    <div id="an-rpt-list" style="font-size:12px;color:#999;">加载中...</div>`;
}

function loadReports() {
    fetch(apiBase + '/an/reports', { headers: authHeaders })
        .then(r => r.json()).then(res => {
            if (!res.success) return;
            const items = (res.data || {}).items || [];
            const el = document.getElementById('an-rpt-list');
            if (!items.length) { el.innerHTML = '<div style="text-align:center;padding:30px;color:#999;">暂无自定义报表</div>'; return; }
            el.innerHTML = `<table class="an-table"><thead><tr>
                <th>名称</th><th>数据源</th><th>创建人</th><th>共享</th><th>创建时间</th><th>操作</th>
            </tr></thead><tbody>${items.map(r => `<tr>
                <td>${escapeHtml(r.name)}</td>
                <td><span style="padding:1px 8px;border-radius:10px;font-size:11px;background:#ede9fe;color:#5b21b6;">${escapeHtml(r.data_source_label)}</span></td>
                <td>${escapeHtml(r.creator)}</td>
                <td>${r.is_shared ? '✅' : '❌'}</td>
                <td>${escapeHtml(r.created_at)}</td>
                <td><button class="btn" style="padding:2px 8px;font-size:11px;background:#4338ca;color:#fff;border:none;border-radius:4px;cursor:pointer;" onclick="execReport(${r.id})">执行</button>
                <button class="btn" style="padding:2px 8px;font-size:11px;border:1px solid #cbd5e1;border-radius:4px;cursor:pointer;background:#fff;" onclick="deleteReport(${r.id})">删除</button></td>
            </tr>`).join('')}</tbody></table>`;
        }).catch(e => { document.getElementById('an-rpt-list').innerHTML = '<div style="color:#dc2626;">加载失败</div>'; });
}

function openReportModal() {
    const old = document.getElementById('an-rpt-modal');
    if (old) old.remove();
    const m = document.createElement('div');
    m.id = 'an-rpt-modal';
    m.className = 'fixed';
    m.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    m.innerHTML = `<div style="background:#fff;border-radius:10px;padding:20px;width:440px;max-width:92vw;">
        <h3 style="margin:0 0 16px;font-size:15px;">新建自定义报表</h3>
        <div style="display:grid;gap:10px;">
            <input id="ar-name" class="an-input" placeholder="报表名称 *">
            <select id="ar-source" class="an-input">
                <option value="PURCHASE">采购</option>
                <option value="SALES">销售</option>
                <option value="INVENTORY">库存</option>
                <option value="PRODUCTION">生产</option>
                <option value="FINANCE">财务</option>
            </select>
            <textarea id="ar-desc" class="an-input" placeholder="报表描述" style="min-height:50px;"></textarea>
            <label style="font-size:11px;display:flex;align-items:center;gap:6px;"><input type="checkbox" id="ar-share"> 共享给所有用户</label>
        </div>
        <div style="display:flex;gap:10px;margin-top:16px;justify-content:flex-end;">
            <button class="btn" style="padding:6px 16px;font-size:12px;border:1px solid #cbd5e1;border-radius:6px;cursor:pointer;background:#fff;" onclick="document.getElementById('an-rpt-modal').remove()">取消</button>
            <button class="btn" style="padding:6px 16px;font-size:12px;background:#4338ca;color:#fff;border:none;border-radius:6px;cursor:pointer;" onclick="saveReport()">保存</button>
        </div>
    </div>`;
    document.body.appendChild(m);
}

function saveReport() {
    const payload = {
        name: document.getElementById('ar-name').value.trim(),
        data_source: document.getElementById('ar-source').value,
        description: document.getElementById('ar-desc').value,
        is_shared: document.getElementById('ar-share').checked,
    };
    if (!payload.name) { showToast('报表名称必填', 'warning'); return; }
    fetch(apiBase + '/an/reports', { method: 'POST', headers: Object.assign({}, authHeaders, { 'Content-Type': 'application/json' }), body: JSON.stringify(payload) })
        .then(r => r.json()).then(res => {
            if (res.success) { document.getElementById('an-rpt-modal').remove(); loadReports(); }
            else showToast(res.message || '保存失败', 'error');
        }).catch(e => showToast('网络错误', 'error'));
}

function execReport(rid) {
    fetch(apiBase + '/an/reports/' + rid + '/execute', { method: 'POST', headers: authHeaders })
        .then(r => r.json()).then(res => {
            if (res.success) {
                const d = res.data || {};
                showToast('报表【' + d.report_name + '】执行完成\n\n' + JSON.stringify(d.summary, null, 2), 'success', 5000);
            } else showToast(res.message || '执行失败', 'error');
        }).catch(e => showToast('网络错误', 'error'));
}

function deleteReport(rid) {
    if (!confirm('确认删除该报表？')) return;
    fetch(apiBase + '/an/reports/' + rid, { method: 'DELETE', headers: authHeaders })
        .then(r => r.json()).then(res => { if (res.success) loadReports(); else showToast(res.message, 'error'); }).catch(e => showToast('网络错误', 'error'));
}

// ========== 发票合规 ==========
function renderInvoiceChecksUI() {
    return `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px;">
        <div style="display:flex;gap:8px;align-items:center;">
            <select id="an-ic-type" class="an-input" style="width:120px;" onchange="loadInvoiceChecks()">
                <option value="">全部类型</option>
                <option value="PURCHASE">进项发票</option>
                <option value="SALES">销项发票</option>
            </select>
            <select id="an-ic-deduct" class="an-input" style="width:120px;" onchange="loadInvoiceChecks()">
                <option value="">全部</option>
                <option value="false">不得抵扣</option>
                <option value="true">可抵扣</option>
            </select>
        </div>
        <button class="btn" style="padding:5px 14px;font-size:12px;background:#dc2626;color:#fff;border:none;border-radius:6px;cursor:pointer;" onclick="openInvoiceCheckModal()">+ 发票校验</button>
    </div>
    <div id="an-ic-list" style="font-size:12px;color:#999;">加载中...</div>`;
}

function loadInvoiceChecks() {
    const type = (document.getElementById('an-ic-type') || {}).value || '';
    const deduct = (document.getElementById('an-ic-deduct') || {}).value;
    let url = apiBase + '/an/invoice-checks?';
    if (type) url += 'invoice_type=' + type + '&';
    if (deduct === 'false') url += 'is_deductible=false';
    else if (deduct === 'true') url += 'is_deductible=true';
    fetch(url, { headers: authHeaders })
        .then(r => r.json()).then(res => {
            if (!res.success) return;
            const items = (res.data || {}).items || [];
            const el = document.getElementById('an-ic-list');
            if (!items.length) { el.innerHTML = '<div style="text-align:center;padding:30px;color:#999;">暂无发票校验记录</div>'; return; }
            el.innerHTML = `<table class="an-table"><thead><tr>
                <th>发票号</th><th>类型</th><th>日期</th><th>金额</th><th>税额</th><th>可抵扣</th><th>校验结果</th><th>预警</th>
            </tr></thead><tbody>${items.map(c => `<tr>
                <td>${escapeHtml(c.invoice_no)}</td>
                <td>${escapeHtml(c.invoice_type_label)}</td>
                <td>${escapeHtml(c.invoice_date)}</td>
                <td>¥${c.amount.toLocaleString()}</td>
                <td>¥${c.tax_amount.toLocaleString()}</td>
                <td>${c.is_deductible ? '<span style="color:#16a34a;">✅ 是</span>' : '<span style="color:#dc2626;">❌ 否</span>'}</td>
                <td><span style="padding:1px 8px;border-radius:10px;font-size:11px;background:${c.check_result === 'PASS' ? '#dcfce7;color:#166534' : c.check_result === 'WARNING' ? '#fef9c3;color:#854d0e' : '#fee2e2;color:#991b1b'};">${c.check_result}</span></td>
                <td style="max-width:200px;font-size:11px;color:#dc2626;">${escapeHtml(c.warning_msg || '')}</td>
            </tr>`).join('')}</tbody></table>`;
        }).catch(e => { document.getElementById('an-ic-list').innerHTML = '<div style="color:#dc2626;">加载失败</div>'; });
}

function openInvoiceCheckModal() {
    const old = document.getElementById('an-ic-modal');
    if (old) old.remove();
    const m = document.createElement('div');
    m.id = 'an-ic-modal';
    m.className = 'fixed';
    m.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    m.innerHTML = `<div style="background:#fff;border-radius:10px;padding:20px;width:480px;max-width:92vw;">
        <h3 style="margin:0 0 16px;font-size:15px;">发票合规校验</h3>
        <div style="display:grid;gap:10px;">
            <input id="ic-no" class="an-input" placeholder="发票号 *">
            <select id="ic-type" class="an-input">
                <option value="PURCHASE">进项发票（采购）</option>
                <option value="SALES">销项发票（销售）</option>
            </select>
            <input id="ic-date" class="an-input" type="date">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                <input id="ic-amt" class="an-input" placeholder="金额(含税)" type="number" step="0.01">
                <input id="ic-tax" class="an-input" placeholder="税额" type="number" step="0.01">
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                <input id="ic-inrate" class="an-input" placeholder="进项税率%" type="number" step="0.01">
                <input id="ic-outrate" class="an-input" placeholder="销项税率%" type="number" step="0.01">
            </div>
            <input id="ic-item" class="an-input" placeholder="项目名称（用于识别个人消费/集体福利）">
        </div>
        <div style="display:flex;gap:10px;margin-top:16px;justify-content:flex-end;">
            <button class="btn" style="padding:6px 16px;font-size:12px;border:1px solid #cbd5e1;border-radius:6px;cursor:pointer;background:#fff;" onclick="document.getElementById('an-ic-modal').remove()">取消</button>
            <button class="btn" style="padding:6px 16px;font-size:12px;background:#dc2626;color:#fff;border:none;border-radius:6px;cursor:pointer;" onclick="saveInvoiceCheck()">校验</button>
        </div>
    </div>`;
    document.body.appendChild(m);
}

function saveInvoiceCheck() {
    const payload = {
        invoice_no: document.getElementById('ic-no').value.trim(),
        invoice_type: document.getElementById('ic-type').value,
        invoice_date: document.getElementById('ic-date').value || undefined,
        amount: parseFloat(document.getElementById('ic-amt').value) || 0,
        tax_amount: parseFloat(document.getElementById('ic-tax').value) || 0,
        tax_rate: parseFloat(document.getElementById('ic-inrate').value) || 0,
        input_tax_rate: parseFloat(document.getElementById('ic-inrate').value) || 0,
        output_tax_rate: parseFloat(document.getElementById('ic-outrate').value) || 0,
        item_name: document.getElementById('ic-item').value,
    };
    if (!payload.invoice_no) { showToast('发票号必填', 'warning'); return; }
    fetch(apiBase + '/an/invoice-checks', { method: 'POST', headers: Object.assign({}, authHeaders, { 'Content-Type': 'application/json' }), body: JSON.stringify(payload) })
        .then(r => r.json()).then(res => {
            if (res.success) {
                const d = res.data || {};
                let msg = '校验结果：' + d.check_result + '\n可抵扣：' + (d.is_deductible ? '是' : '否');
                if (d.warnings && d.warnings.length) msg += '\n\n⚠️ 预警：\n' + d.warnings.join('\n');
                showToast(msg, 'success', 5000);
                document.getElementById('an-ic-modal').remove();
                loadInvoiceChecks();
            } else showToast(res.message || '校验失败', 'error');
        }).catch(e => showToast('网络错误', 'error'));
}

window._renderAnalyticsImpl = _renderAnalyticsImpl;
