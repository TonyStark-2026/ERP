/* ============================================================
 * 成本会计 前端模块
 * 标准成本 / 差异分析 / 约当产量法
 * ============================================================ */
if (typeof escapeHtml === 'undefined') {
    window.escapeHtml = function(s) {
        if (s === null || s === undefined) return '';
        var d = document.createElement('div');
        d.textContent = String(s);
        return d.innerHTML;
    };
}

var _costTab = 'standards';

function _renderCostAccountingImpl() {
    setTimeout(() => switchCostTab('standards'), 80);
    return `
    <div style="padding:16px;">
        <div class="card">
            <div class="card-title" style="display:flex;justify-content:space-between;align-items:center;background:linear-gradient(135deg,#0891b2,#0e7490);color:#fff;border-radius:8px 8px 0 0;padding:12px 16px;margin:-16px -16px 12px -16px;">
                <span style="font-size:16px;font-weight:bold;">📐 成本会计</span>
                <span style="font-size:12px;">标准成本 / 差异分析 / 约当产量法</span>
            </div>
            <div style="padding:12px 16px;">
                <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;margin-bottom:16px;">
                    <div class="cost-stat-card"><div class="num" id="cost-stat-std">-</div><div class="lbl">标准成本</div></div>
                    <div class="cost-stat-card"><div class="num" id="cost-stat-var">-</div><div class="lbl">差异记录</div></div>
                    <div class="cost-stat-card"><div class="num" id="cost-stat-diff">-</div><div class="lbl">总差异</div></div>
                </div>
                <div style="display:flex;gap:4px;border-bottom:2px solid #0e7490;margin-bottom:16px;flex-wrap:wrap;">
                    <button class="btn cost-tab-btn active" data-c-tab="standards" onclick="switchCostTab('standards')">📋 标准成本</button>
                    <button class="btn cost-tab-btn" data-c-tab="variances" onclick="switchCostTab('variances')">📉 差异分析</button>
                    <button class="btn cost-tab-btn" data-c-tab="equivalent" onclick="switchCostTab('equivalent')">⚖️ 约当产量法</button>
                </div>
                <div id="cost-tab-standards" class="cost-tab-panel"></div>
                <div id="cost-tab-variances" class="cost-tab-panel" style="display:none;"></div>
                <div id="cost-tab-equivalent" class="cost-tab-panel" style="display:none;"></div>
            </div>
        </div>
    </div>
    <style>
        .cost-tab-btn{padding:4px 12px;font-size:12px;border:1px solid #e5e7eb;background:#fff;color:#666;border-radius:6px;cursor:pointer;transition:all .2s;}
        .cost-tab-btn:hover{background:#ecfeff;border-color:#0e7490;}
        .cost-tab-btn.active{background:linear-gradient(135deg,#0891b2,#0e7490);color:#fff;border-color:transparent;}
        .cost-stat-card{background:linear-gradient(135deg,#ecfeff,#cffafe);border:1px solid #67e8f9;border-radius:10px;padding:12px;text-align:center;}
        .cost-stat-card .num{font-size:22px;font-weight:bold;color:#0e7490;}
        .cost-stat-card .lbl{font-size:11px;color:#666;margin-top:4px;}
        .cost-table{width:100%;border-collapse:collapse;font-size:12px;}
        .cost-table th{background:#f1f5f9;padding:8px 10px;text-align:left;border-bottom:2px solid #cbd5e1;color:#475569;font-weight:600;}
        .cost-table td{padding:8px 10px;border-bottom:1px solid #e2e8f0;color:#334155;}
        .cost-table tr:hover td{background:#f8fafc;}
        .cost-op-box{background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:20px;max-width:680px;}
        .cost-input{padding:6px 8px;border:1px solid #cbd5e1;border-radius:6px;font-size:12px;width:100%;}
    </style>`;
}

function switchCostTab(tab) {
    _costTab = tab;
    document.querySelectorAll('.cost-tab-btn').forEach(b => b.classList.toggle('active', b.getAttribute('data-c-tab') === tab));
    document.querySelectorAll('.cost-tab-panel').forEach(p => p.style.display = 'none');
    const el = document.getElementById('cost-tab-' + tab);
    if (!el) return;
    el.style.display = 'block';
    if (tab === 'standards') el.innerHTML = renderStandardsUI(), setTimeout(loadStandards, 30);
    if (tab === 'variances') el.innerHTML = renderVariancesUI(), setTimeout(loadVariances, 30);
    if (tab === 'equivalent') el.innerHTML = renderEquivalentUI();
    loadCostOverview();
}

function loadCostOverview() {
    fetch(apiBase + '/cost/overview', { headers: authHeaders })
        .then(r => r.json()).then(res => {
            if (!res.success) return;
            const d = res.data || {};
            document.getElementById('cost-stat-std').textContent = d.standard_count || 0;
            document.getElementById('cost-stat-var').textContent = d.variance_count || 0;
            const diffEl = document.getElementById('cost-stat-diff');
            const tv = d.total_variance || 0;
            diffEl.textContent = '¥' + Math.abs(tv).toLocaleString();
            diffEl.style.color = tv < 0 ? '#16a34a' : (tv > 0 ? '#dc2626' : '#0e7490');
        }).catch(e => console.error('cost overview err', e));
}

// ========== 标准成本 ==========
function renderStandardsUI() {
    return `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <span style="font-size:12px;color:#666;">物料标准成本清单（材料/人工/制造费用）</span>
        <button class="btn" style="padding:5px 14px;font-size:12px;background:#0e7490;color:#fff;border:none;border-radius:6px;cursor:pointer;" onclick="openStdModal()">+ 新增标准成本</button>
    </div>
    <div id="cost-std-list" style="font-size:12px;color:#999;">加载中...</div>`;
}

function loadStandards() {
    fetch(apiBase + '/cost/standards', { headers: authHeaders })
        .then(r => r.json()).then(res => {
            if (!res.success) return;
            const items = (res.data || {}).items || [];
            const el = document.getElementById('cost-std-list');
            if (!items.length) { el.innerHTML = '<div style="text-align:center;padding:30px;color:#999;">暂无标准成本数据</div>'; return; }
            el.innerHTML = `<table class="cost-table"><thead><tr>
                <th>物料</th><th>材料成本</th><th>人工成本</th><th>制造费用</th><th>标准总成本</th><th>生效日期</th><th>状态</th><th>操作</th>
            </tr></thead><tbody>${items.map(s => `<tr>
                <td>${escapeHtml((s.material || {}).code || '')} ${escapeHtml((s.material || {}).name || '')}</td>
                <td>¥${s.standard_material_cost.toLocaleString()}</td>
                <td>¥${s.standard_labor_cost.toLocaleString()}</td>
                <td>¥${s.standard_overhead_cost.toLocaleString()}</td>
                <td><b style="color:#0e7490;">¥${s.standard_total_cost.toLocaleString()}</b></td>
                <td>${escapeHtml(s.effective_date)}</td>
                <td><span style="color:${s.status === 'ACTIVE' ? '#16a34a' : '#999'};">${s.status}</span></td>
                <td><button class="btn" style="padding:2px 8px;font-size:11px;border:1px solid #cbd5e1;border-radius:4px;cursor:pointer;background:#fff;" onclick="openStdModal(${s.id})">编辑</button></td>
            </tr>`).join('')}</tbody></table>`;
        }).catch(e => { document.getElementById('cost-std-list').innerHTML = '<div style="color:#dc2626;">加载失败</div>'; });
}

function openStdModal(id) {
    const isEdit = !!id;
    const old = document.getElementById('cost-std-modal');
    if (old) old.remove();
    const m = document.createElement('div');
    m.id = 'cost-std-modal';
    m.className = 'fixed';
    m.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    m.innerHTML = `<div style="background:#fff;border-radius:10px;padding:20px;width:440px;max-width:92vw;">
        <h3 style="margin:0 0 16px;font-size:15px;">${isEdit ? '编辑标准成本' : '新增标准成本'}</h3>
        <div style="display:grid;gap:10px;">
            <input id="cs-material" class="cost-input" placeholder="物料ID（数字） *" type="number">
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;">
                <input id="cs-mat" class="cost-input" placeholder="材料成本" type="number" step="0.01">
                <input id="cs-lab" class="cost-input" placeholder="人工成本" type="number" step="0.01">
                <input id="cs-oh" class="cost-input" placeholder="制造费用" type="number" step="0.01">
            </div>
            <input id="cs-date" class="cost-input" type="date">
        </div>
        <div style="display:flex;gap:10px;margin-top:16px;justify-content:flex-end;">
            <button class="btn" style="padding:6px 16px;font-size:12px;border:1px solid #cbd5e1;border-radius:6px;cursor:pointer;background:#fff;" onclick="document.getElementById('cost-std-modal').remove()">取消</button>
            <button class="btn" style="padding:6px 16px;font-size:12px;background:#0e7490;color:#fff;border:none;border-radius:6px;cursor:pointer;" onclick="saveStd(${id || 0})">保存</button>
        </div>
    </div>`;
    document.body.appendChild(m);
}

function saveStd(id) {
    const payload = {
        material_id: parseInt(document.getElementById('cs-material').value) || 0,
        standard_material_cost: parseFloat(document.getElementById('cs-mat').value) || 0,
        standard_labor_cost: parseFloat(document.getElementById('cs-lab').value) || 0,
        standard_overhead_cost: parseFloat(document.getElementById('cs-oh').value) || 0,
        effective_date: document.getElementById('cs-date').value || undefined,
    };
    if (!payload.material_id) { showToast('物料ID必填', 'warning'); return; }
    const url = id ? apiBase + '/cost/standards/' + id : apiBase + '/cost/standards';
    const method = id ? 'PUT' : 'POST';
    fetch(url, { method, headers: Object.assign({}, authHeaders, { 'Content-Type': 'application/json' }), body: JSON.stringify(payload) })
        .then(r => r.json()).then(res => {
            if (res.success) { document.getElementById('cost-std-modal').remove(); loadStandards(); }
            else showToast(res.message || '保存失败', 'error');
        }).catch(e => showToast('网络错误', 'error'));
}

// ========== 差异分析 ==========
function renderVariancesUI() {
    return `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <span style="font-size:12px;color:#666;">成本差异分析（标准 vs 实际）</span>
        <button class="btn" style="padding:5px 14px;font-size:12px;background:#dc2626;color:#fff;border:none;border-radius:6px;cursor:pointer;" onclick="openVarModal()">+ 录入差异</button>
    </div>
    <div id="cost-var-list" style="font-size:12px;color:#999;">加载中...</div>`;
}

function loadVariances() {
    fetch(apiBase + '/cost/variances', { headers: authHeaders })
        .then(r => r.json()).then(res => {
            if (!res.success) return;
            const items = (res.data || {}).items || [];
            const el = document.getElementById('cost-var-list');
            if (!items.length) { el.innerHTML = '<div style="text-align:center;padding:30px;color:#999;">暂无差异分析记录</div>'; return; }
            el.innerHTML = `<table class="cost-table"><thead><tr>
                <th>工单</th><th>差异类型</th><th>标准成本</th><th>实际成本</th><th>差异金额</th><th>差异率</th><th>分析</th>
            </tr></thead><tbody>${items.map(v => `<tr>
                <td>${escapeHtml((v.work_order || {}).wo_no || v.work_order_id)}</td>
                <td>${escapeHtml(v.variance_type_label)}</td>
                <td>¥${v.standard_cost.toLocaleString()}</td>
                <td>¥${v.actual_cost.toLocaleString()}</td>
                <td><b style="color:${v.variance_amount < 0 ? '#16a34a' : '#dc2626'};">${v.variance_amount >= 0 ? '+' : ''}¥${v.variance_amount.toLocaleString()}</b></td>
                <td>${v.variance_rate.toFixed(1)}%</td>
                <td style="max-width:200px;font-size:11px;color:#666;">${escapeHtml(v.analysis || '')}</td>
            </tr>`).join('')}</tbody></table>`;
        }).catch(e => { document.getElementById('cost-var-list').innerHTML = '<div style="color:#dc2626;">加载失败</div>'; });
}

function openVarModal() {
    const old = document.getElementById('cost-var-modal');
    if (old) old.remove();
    const m = document.createElement('div');
    m.id = 'cost-var-modal';
    m.className = 'fixed';
    m.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    m.innerHTML = `<div style="background:#fff;border-radius:10px;padding:20px;width:440px;max-width:92vw;">
        <h3 style="margin:0 0 16px;font-size:15px;">录入成本差异</h3>
        <div style="display:grid;gap:10px;">
            <input id="cv-wo" class="cost-input" placeholder="工单ID *" type="number">
            <select id="cv-type" class="cost-input">
                <option value="MATERIAL">材料成本差异</option>
                <option value="LABOR">人工成本差异</option>
                <option value="OVERHEAD">制造费用差异</option>
            </select>
            <input id="cv-std" class="cost-input" placeholder="标准成本 *" type="number" step="0.01">
            <input id="cv-act" class="cost-input" placeholder="实际成本 *" type="number" step="0.01">
            <textarea id="cv-analysis" class="cost-input" placeholder="差异原因分析" style="min-height:50px;"></textarea>
        </div>
        <div style="display:flex;gap:10px;margin-top:16px;justify-content:flex-end;">
            <button class="btn" style="padding:6px 16px;font-size:12px;border:1px solid #cbd5e1;border-radius:6px;cursor:pointer;background:#fff;" onclick="document.getElementById('cost-var-modal').remove()">取消</button>
            <button class="btn" style="padding:6px 16px;font-size:12px;background:#dc2626;color:#fff;border:none;border-radius:6px;cursor:pointer;" onclick="saveVar()">保存</button>
        </div>
    </div>`;
    document.body.appendChild(m);
}

function saveVar() {
    const payload = {
        work_order_id: parseInt(document.getElementById('cv-wo').value) || 0,
        variance_type: document.getElementById('cv-type').value,
        standard_cost: parseFloat(document.getElementById('cv-std').value) || 0,
        actual_cost: parseFloat(document.getElementById('cv-act').value) || 0,
        analysis: document.getElementById('cv-analysis').value,
    };
    if (!payload.work_order_id) { showToast('工单ID必填', 'warning'); return; }
    fetch(apiBase + '/cost/variances', { method: 'POST', headers: Object.assign({}, authHeaders, { 'Content-Type': 'application/json' }), body: JSON.stringify(payload) })
        .then(r => r.json()).then(res => {
            if (res.success) { document.getElementById('cost-var-modal').remove(); loadVariances(); }
            else showToast(res.message || '保存失败', 'error');
        }).catch(e => showToast('网络错误', 'error'));
}

// ========== 约当产量法 ==========
function renderEquivalentUI() {
    return `<div class="cost-op-box">
        <h3 style="margin:0 0 12px;font-size:14px;">⚖️ 约当产量法成本分摊</h3>
        <p style="font-size:12px;color:#666;margin:0 0 16px;">将期初在产品成本 + 本期投入成本，按约当产量（完工数量 + 期末在产品×完工程度）分摊至完工产品和期末在产品。</p>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px;">
            <div><label style="font-size:11px;color:#666;">期初在产品成本</label><input id="eq-begin" class="cost-input" type="number" step="0.01" value="0"></div>
            <div><label style="font-size:11px;color:#666;">本期投入成本</label><input id="eq-current" class="cost-input" type="number" step="0.01" value="0"></div>
            <div><label style="font-size:11px;color:#666;">完工数量</label><input id="eq-completed" class="cost-input" type="number" step="0.01" value="0"></div>
            <div><label style="font-size:11px;color:#666;">期末在产品数量</label><input id="eq-endwip" class="cost-input" type="number" step="0.01" value="0"></div>
            <div><label style="font-size:11px;color:#666;">完工程度(%)</label><input id="eq-pct" class="cost-input" type="number" step="1" value="50"></div>
        </div>
        <button class="btn" style="padding:8px 20px;font-size:12px;background:#0e7490;color:#fff;border:none;border-radius:6px;cursor:pointer;" onclick="calcEquivalent()">计算</button>
        <div id="eq-result" style="margin-top:16px;"></div>
    </div>`;
}

function calcEquivalent() {
    const payload = {
        begin_wip_cost: parseFloat(document.getElementById('eq-begin').value) || 0,
        current_cost: parseFloat(document.getElementById('eq-current').value) || 0,
        completed_qty: parseFloat(document.getElementById('eq-completed').value) || 0,
        end_wip_qty: parseFloat(document.getElementById('eq-endwip').value) || 0,
        completion_pct: parseFloat(document.getElementById('eq-pct').value) || 0,
    };
    fetch(apiBase + '/cost/equivalent-units', { method: 'POST', headers: Object.assign({}, authHeaders, { 'Content-Type': 'application/json' }), body: JSON.stringify(payload) })
        .then(r => r.json()).then(res => {
            const el = document.getElementById('eq-result');
            if (res.success) {
                const d = res.data || {};
                el.innerHTML = `<div style="background:#ecfeff;border:1px solid #67e8f9;border-radius:8px;padding:14px;font-size:12px;">
                    <div style="margin-bottom:8px;"><b>总成本：</b>¥${(d.total_cost || 0).toLocaleString()}</div>
                    <div style="margin-bottom:8px;"><b>约当产量：</b>${d.equivalent_units} <b>单位成本：</b>¥${d.unit_cost}</div>
                    <hr style="border:none;border-top:1px dashed #cbd5e1;margin:10px 0;">
                    <div style="margin-bottom:6px;color:#16a34a;">✅ 完工产品成本（${d.completed_qty}件）：¥${(d.completed_cost || 0).toLocaleString()}</div>
                    <div style="color:#ca8a04;">📦 期末在产品成本（${d.end_wip_qty}件×${d.completion_pct}%）：¥${(d.end_wip_cost || 0).toLocaleString()}</div>
                </div>`;
            } else { el.innerHTML = `<div style="color:#dc2626;">${res.message || '计算失败'}</div>`; }
        }).catch(e => { document.getElementById('eq-result').innerHTML = '<div style="color:#dc2626;">网络错误</div>'; });
}

window._renderCostAccountingImpl = _renderCostAccountingImpl;
