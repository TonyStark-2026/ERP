/* ============================================================
 * 财务期末 前端模块
 * 期末调汇 / 结转损益 / 结账
 * ============================================================ */
if (typeof escapeHtml === 'undefined') {
    window.escapeHtml = function(s) {
        if (s === null || s === undefined) return '';
        var d = document.createElement('div');
        d.textContent = String(s);
        return d.innerHTML;
    };
}

var _fn2Tab = 'forex';

function _renderFinanceV2Impl() {
    setTimeout(() => switchFn2Tab('forex'), 80);
    return `
    <div style="padding:16px;">
        <div class="card">
            <div class="card-title" style="display:flex;justify-content:space-between;align-items:center;background:linear-gradient(135deg,#6366f1,#4338ca);color:#fff;border-radius:8px 8px 0 0;padding:12px 16px;margin:-16px -16px 12px -16px;">
                <span style="font-size:16px;font-weight:bold;">📅 财务期末</span>
                <span style="font-size:12px;" id="fn2-period">当前期间：-</span>
            </div>
            <div style="padding:12px 16px;">
                <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px;margin-bottom:16px;">
                    <div class="fn2-stat-card" id="fn2-card-forex"><div class="lbl">期末调汇</div><div class="num" id="fn2-stat-forex">-</div></div>
                    <div class="fn2-stat-card" id="fn2-card-pnl"><div class="lbl">结转损益</div><div class="num" id="fn2-stat-pnl">-</div></div>
                    <div class="fn2-stat-card" id="fn2-card-close"><div class="lbl">结账</div><div class="num" id="fn2-stat-close">-</div></div>
                </div>
                <div style="display:flex;gap:4px;border-bottom:2px solid #4338ca;margin-bottom:16px;flex-wrap:wrap;">
                    <button class="btn fn2-tab-btn active" data-f2-tab="forex" onclick="switchFn2Tab('forex')">💱 期末调汇</button>
                    <button class="btn fn2-tab-btn" data-f2-tab="pnl" onclick="switchFn2Tab('pnl')">📊 结转损益</button>
                    <button class="btn fn2-tab-btn" data-f2-tab="close" onclick="switchFn2Tab('close')">🔒 结账</button>
                    <button class="btn fn2-tab-btn" data-f2-tab="history" onclick="switchFn2Tab('history')">📋 历史记录</button>
                </div>
                <div id="fn2-tab-forex" class="fn2-tab-panel"></div>
                <div id="fn2-tab-pnl" class="fn2-tab-panel" style="display:none;"></div>
                <div id="fn2-tab-close" class="fn2-tab-panel" style="display:none;"></div>
                <div id="fn2-tab-history" class="fn2-tab-panel" style="display:none;"></div>
            </div>
        </div>
    </div>
    <style>
        .fn2-tab-btn{padding:4px 12px;font-size:12px;border:1px solid #e5e7eb;background:#fff;color:#666;border-radius:6px;cursor:pointer;transition:all .2s;}
        .fn2-tab-btn:hover{background:#eef2ff;border-color:#4338ca;}
        .fn2-tab-btn.active{background:linear-gradient(135deg,#6366f1,#4338ca);color:#fff;border-color:transparent;}
        .fn2-stat-card{background:linear-gradient(135deg,#eef2ff,#e0e7ff);border:1px solid #c7d2fe;border-radius:10px;padding:12px;text-align:center;}
        .fn2-stat-card .num{font-size:16px;font-weight:bold;color:#4338ca;margin-top:4px;}
        .fn2-stat-card .lbl{font-size:11px;color:#666;}
        .fn2-table{width:100%;border-collapse:collapse;font-size:12px;}
        .fn2-table th{background:#f1f5f9;padding:8px 10px;text-align:left;border-bottom:2px solid #cbd5e1;color:#475569;font-weight:600;}
        .fn2-table td{padding:8px 10px;border-bottom:1px solid #e2e8f0;color:#334155;}
        .fn2-table tr:hover td{background:#f8fafc;}
        .fn2-op-box{background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:20px;max-width:560px;}
    </style>`;
}

function switchFn2Tab(tab) {
    _fn2Tab = tab;
    document.querySelectorAll('.fn2-tab-btn').forEach(b => b.classList.toggle('active', b.getAttribute('data-f2-tab') === tab));
    document.querySelectorAll('.fn2-tab-panel').forEach(p => p.style.display = 'none');
    const el = document.getElementById('fn2-tab-' + tab);
    if (!el) return;
    el.style.display = 'block';
    if (tab === 'forex') el.innerHTML = renderForexUI();
    if (tab === 'pnl') el.innerHTML = renderPnlUI();
    if (tab === 'close') el.innerHTML = renderCloseUI();
    if (tab === 'history') setTimeout(loadFn2History, 30);
    loadFn2Overview();
}

function loadFn2Overview() {
    fetch(apiBase + '/fn2/overview', { headers: authHeaders })
        .then(r => r.json()).then(res => {
            if (!res.success) return;
            const d = res.data || {};
            const pe = document.getElementById('fn2-period');
            if (pe) pe.textContent = '当前期间：' + (d.current_period || '-');
            const setStat = (id, done) => {
                const el = document.getElementById(id);
                if (el) { el.textContent = done ? '✅ 已完成' : '⏳ 待处理'; el.style.color = done ? '#16a34a' : '#ca8a04'; }
            };
            setStat('fn2-stat-forex', d.forex_done);
            setStat('fn2-stat-pnl', d.pnl_settled);
            setStat('fn2-stat-close', d.closed);
        }).catch(e => console.error('fn2 overview err', e));
}

function renderForexUI() {
    return `<div class="fn2-op-box">
        <h3 style="margin:0 0 12px;font-size:14px;">💱 期末调汇</h3>
        <p style="font-size:12px;color:#666;margin:0 0 16px;">对外币货币性项目按期末汇率进行调整，生成调汇凭证。系统将自动计算汇兑损益并推送到凭证管理。</p>
        <div style="display:flex;gap:10px;align-items:center;margin-bottom:12px;">
            <label style="font-size:12px;">期间：</label>
            <input id="fn2-forex-period" type="month" style="padding:6px 8px;border:1px solid #cbd5e1;border-radius:6px;font-size:12px;">
        </div>
        <textarea id="fn2-forex-remark" placeholder="备注（可选）" style="width:100%;padding:8px;border:1px solid #cbd5e1;border-radius:6px;font-size:12px;min-height:60px;margin-bottom:12px;"></textarea>
        <button class="btn" style="padding:8px 20px;font-size:12px;background:#4338ca;color:#fff;border:none;border-radius:6px;cursor:pointer;" onclick="execForex()">执行期末调汇</button>
    </div>`;
}

function execForex() {
    const period = (document.getElementById('fn2-forex-period') || {}).value || '';
    const remark = (document.getElementById('fn2-forex-remark') || {}).value || '';
    if (!confirm('确认执行期末调汇？将生成调汇凭证。')) return;
    fetch(apiBase + '/fn2/forex', { method: 'POST', headers: Object.assign({}, authHeaders, { 'Content-Type': 'application/json' }), body: JSON.stringify({ period_code: period.replace('-', '-'), remark }) })
        .then(r => r.json()).then(res => {
            if (res.success) { showToast('调汇完成！凭证号：' + (res.data || {}).voucher_no, 'success'); loadFn2Overview(); }
            else showToast(res.message || '操作失败', 'error');
        }).catch(e => showToast('网络错误', 'error'));
}

function renderPnlUI() {
    return `<div class="fn2-op-box">
        <h3 style="margin:0 0 12px;font-size:14px;">📊 结转损益</h3>
        <p style="font-size:12px;color:#666;margin:0 0 16px;">将所有收入、费用类科目余额结转至"本年利润"科目，生成结转损益凭证。结转后收入、费用科目余额清零。</p>
        <div style="display:flex;gap:10px;align-items:center;margin-bottom:12px;">
            <label style="font-size:12px;">期间：</label>
            <input id="fn2-pnl-period" type="month" style="padding:6px 8px;border:1px solid #cbd5e1;border-radius:6px;font-size:12px;">
        </div>
        <button class="btn" style="padding:8px 20px;font-size:12px;background:#4338ca;color:#fff;border:none;border-radius:6px;cursor:pointer;" onclick="execPnl()">执行结转损益</button>
    </div>`;
}

function execPnl() {
    const period = (document.getElementById('fn2-pnl-period') || {}).value || '';
    if (!confirm('确认执行结转损益？收入、费用科目余额将清零。')) return;
    fetch(apiBase + '/fn2/pnl-settle', { method: 'POST', headers: Object.assign({}, authHeaders, { 'Content-Type': 'application/json' }), body: JSON.stringify({ period_code: period.replace('-', '-') }) })
        .then(r => r.json()).then(res => {
            if (res.success) {
                const d = res.data || {};
                showToast(`结转完成！\n凭证号：${d.voucher_no}\n本期收入：¥${(d.total_revenue || 0).toLocaleString()}\n本期费用：¥${(d.total_expense || 0).toLocaleString()}\n净利润：¥${(d.net_profit || 0).toLocaleString()}`, 'success', 5000);
                loadFn2Overview();
            } else showToast(res.message || '操作失败', 'error');
        }).catch(e => showToast('网络错误', 'error'));
}

function renderCloseUI() {
    return `<div class="fn2-op-box">
        <h3 style="margin:0 0 12px;font-size:14px;">🔒 结账</h3>
        <p style="font-size:12px;color:#666;margin:0 0 16px;">结账前系统将自动检查：<br>① 试算平衡校验 ② 损益是否已结转<br>全部通过后方可结账，结账后该期间数据将被锁定。</p>
        <div style="display:flex;gap:10px;align-items:center;margin-bottom:12px;">
            <label style="font-size:12px;">期间：</label>
            <input id="fn2-close-period" type="month" style="padding:6px 8px;border:1px solid #cbd5e1;border-radius:6px;font-size:12px;">
        </div>
        <button class="btn" style="padding:8px 20px;font-size:12px;background:#dc2626;color:#fff;border:none;border-radius:6px;cursor:pointer;" onclick="execClose()">执行结账</button>
    </div>`;
}

function execClose() {
    const period = (document.getElementById('fn2-close-period') || {}).value || '';
    if (!confirm('确认结账？结账后该期间数据将被锁定，不可修改。')) return;
    fetch(apiBase + '/fn2/close', { method: 'POST', headers: Object.assign({}, authHeaders, { 'Content-Type': 'application/json' }), body: JSON.stringify({ period_code: period.replace('-', '-') }) })
        .then(r => r.json()).then(res => {
            if (res.success) {
                const d = res.data || {};
                showToast(`✅ ${d.period_code} 期间结账成功！\n借方合计：¥${(d.total_debit || 0).toLocaleString()}\n贷方合计：¥${(d.total_credit || 0).toLocaleString()}`, 'success', 5000);
                loadFn2Overview();
            } else {
                const d = res.data || {};
                showToast((res.message || '结账失败') + (d.failed ? '\n未通过项：' + d.failed.join('、') : ''), 'error', 5000);
            }
        }).catch(e => showToast('网络错误', 'error'));
}

function loadFn2History() {
    const el = document.getElementById('fn2-tab-history');
    if (el) el.innerHTML = '<div style="color:#999;">加载中...</div>';
    fetch(apiBase + '/fn2/period-closings', { headers: authHeaders })
        .then(r => r.json()).then(res => {
            if (!res.success) return;
            const items = (res.data || {}).items || [];
            if (!items.length) { el.innerHTML = '<div style="text-align:center;padding:30px;color:#999;">暂无期末处理记录</div>'; return; }
            el.innerHTML = `<table class="fn2-table"><thead><tr>
                <th>期间</th><th>类型</th><th>状态</th><th>凭证号</th><th>操作人</th><th>操作时间</th><th>备注</th>
            </tr></thead><tbody>${items.map(p => `<tr>
                <td>${escapeHtml(p.period_code)}</td><td>${escapeHtml(p.closing_type_label)}</td>
                <td><span style="color:${p.status === 'COMPLETED' ? '#16a34a' : '#ca8a04'};">${p.status_label}</span></td>
                <td>${escapeHtml(p.voucher_no)}</td><td>${escapeHtml(p.operated_by)}</td>
                <td>${escapeHtml(p.operated_at)}</td><td>${escapeHtml(p.remark)}</td>
            </tr>`).join('')}</tbody></table>`;
        }).catch(e => { if (el) el.innerHTML = '<div style="color:#dc2626;">加载失败</div>'; });
}

window._renderFinanceV2Impl = _renderFinanceV2Impl;
