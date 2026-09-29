/* ============================================================
 * 生产计划表（计划管理）
 * 根据机器日产能目标 + 项目交付日期自动排产
 * 独立文件，通过 <script src> 引入 index.html
 * ============================================================ */

if (typeof escapeHtml === 'undefined') {
    window.escapeHtml = function(s) {
        if (!s) return '';
        var d = document.createElement('div');
        d.textContent = String(s);
        return d.innerHTML;
    };
}

var _ppView = 'table';
var _ppData = null;
var _ppFuncTab = 'plan'; // plan=计划表 lines=生产线管理 sched=排产管理

function renderProductionPlan() {
    document.getElementById('content').innerHTML = `
    <div style="padding:16px;">
        <div class="card">
            <div class="card-title" style="display:flex;justify-content:space-between;align-items:center;background:linear-gradient(135deg,#0ea5e9,#6366f1);color:#fff;border-radius:8px 8px 0 0;padding:12px 16px;margin:-16px -16px 12px -16px;">
                <span style="font-size:16px;font-weight:bold;">📅 生产计划</span>
                <span style="font-size:12px;">计划排产 · 生产线 · 排产管理一体化</span>
            </div>
            <div style="padding:12px 16px;">
                <div style="display:flex;gap:6px;margin-bottom:14px;flex-wrap:wrap;border-bottom:1px solid #e5e7eb;padding-bottom:10px;">
                    <button class="btn pp-ftab active" data-f="plan" onclick="_ppSwitchFunc('plan')">📋 计划表</button>
                    <button class="btn pp-ftab" data-f="lines" onclick="_ppSwitchFunc('lines')">🏭 生产线管理</button>
                    <button class="btn pp-ftab" data-f="sched" onclick="_ppSwitchFunc('sched')">📅 排产管理</button>
                </div>
                <div id="pp-func-body"></div>
            </div>
        </div>
    </div>
    <style>
        .pp-ftab{padding:6px 16px;font-size:13px;border:1px solid #e5e7eb;background:#fff;color:#666;border-radius:6px;cursor:pointer;}
        .pp-ftab.active{background:linear-gradient(135deg,#0ea5e9,#6366f1);color:#fff;border-color:transparent;font-weight:bold;}
        .pp-vtab{padding:5px 14px;font-size:12px;border:1px solid #e5e7eb;background:#fff;color:#666;border-radius:6px;cursor:pointer;}
        .pp-vtab.active{background:linear-gradient(135deg,#0ea5e9,#6366f1);color:#fff;border-color:transparent;}
        .pp-stat{background:linear-gradient(135deg,#f0f9ff,#e0f2fe);border:1px solid #bae6fd;border-radius:10px;padding:12px;text-align:center;}
        .pp-stat .num{font-size:22px;font-weight:bold;color:#0369a1;}
        .pp-stat .lbl{font-size:11px;color:#666;margin-top:3px;}
    </style>`;
    _ppRenderFunc();
}

function _ppSwitchFunc(f) {
    _ppFuncTab = f;
    document.querySelectorAll('.pp-ftab').forEach(b => b.classList.toggle('active', b.getAttribute('data-f') === f));
    _ppRenderFunc();
}

function _ppRenderFunc() {
    const el = document.getElementById('pp-func-body');
    if (!el) return;
    if (_ppFuncTab === 'lines') { renderPmcLines('pp-func-body'); return; }
    if (_ppFuncTab === 'sched') { renderPmcSchedules('pp-func-body'); return; }
    // 默认：计划表（自动排产 表格+甘特）
    el.innerHTML = `
        <div id="pp-summary" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;margin-bottom:16px;"></div>
        <div style="display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap;">
            <button class="btn pp-vtab active" data-v="table" onclick="_ppSwitchView('table')">📋 生产计划表</button>
            <button class="btn pp-vtab" data-v="gantt" onclick="_ppSwitchView('gantt')">🗓️ 生产日程</button>
            <button class="btn btn-secondary" style="margin-left:auto;" onclick="loadProductionPlan()">🔄 重新排产</button>
        </div>
        <div id="pp-content"><div style="color:#888;padding:30px;text-align:center;">排产计算中...</div></div>`;
    loadProductionPlan();
}

function _ppSwitchView(v) {
    _ppView = v;
    document.querySelectorAll('.pp-vtab').forEach(b => b.classList.toggle('active', b.getAttribute('data-v') === v));
    _ppRenderView();
}

function loadProductionPlan() {
    fetch('/api/v1/pp/production-plan', { headers: authHeaders }).then(r => r.json()).then(d => {
        if (!d.success) {
            const el = document.getElementById('pp-content');
            if (el) el.innerHTML = '<div style="color:#dc2626;padding:20px;text-align:center;">' + escapeHtml(d.message || '加载失败') + '</div>';
            return;
        }
        _ppData = d.data;
        _ppRenderSummary();
        _ppRenderView();
    }).catch(() => {
        const el = document.getElementById('pp-content');
        if (el) el.innerHTML = '<div style="color:#dc2626;padding:20px;text-align:center;">网络错误</div>';
    });
}

function _ppRenderSummary() {
    const el = document.getElementById('pp-summary');
    if (!el || !_ppData) return;
    const d = _ppData;
    el.innerHTML = `
        <div class="pp-stat"><div class="num">${d.machine_count}</div><div class="lbl">可用机器（台）</div></div>
        <div class="pp-stat"><div class="num">${d.total_capacity}</div><div class="lbl">日产能合计（${escapeHtml(d.capacity_unit)}/天）</div></div>
        <div class="pp-stat"><div class="num">${d.task_count}</div><div class="lbl">排产任务（项）</div></div>
        <div class="pp-stat"><div class="num" style="${d.risk_count > 0 ? 'color:#dc2626;' : ''}">${d.risk_count}</div><div class="lbl">风险任务（项）</div></div>`;
}

function _ppRenderView() {
    const el = document.getElementById('pp-content');
    if (!el || !_ppData) return;
    if (_ppView === 'table') el.innerHTML = _ppTableHtml();
    else el.innerHTML = _ppGanttHtml();
}

function _ppRiskChip(t) {
    const map = {
        OVERDUE: ['已逾期' + (t.late_days || 0) + '天', '#b91c1c', '#fee2e2'],
        TIGHT: ['须立即开工', '#b45309', '#fef3c7'],
        OK: ['可按期', '#047857', '#d1fae5'],
        NO_CAP: ['无可用产能', '#6b7280', '#f3f4f6'],
        NO_DATE: ['缺交付日期', '#6b7280', '#f3f4f6']
    };
    const s = map[t.risk] || [t.risk, '#6b7280', '#f3f4f6'];
    return `<span style="padding:3px 10px;border-radius:12px;font-size:11px;background:${s[2]};color:${s[1]};font-weight:bold;">${s[0]}</span>`;
}

// ========== 视图1：生产计划表（按项目时间排序的项目卡片，点开项目看零件明细） ==========
let _ppOpenProject = null;
function _ppTableHtml() {
    const tasks = _ppData.tasks || [];
    if (!tasks.length) {
        let hint = '<div style="color:#999;padding:30px;text-align:center;">暂无生产任务</div>';
        const nd = _ppData.no_decomposition_projects || [];
        if (nd.length) hint += `<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:10px 14px;margin:0 auto 20px;max-width:640px;font-size:12px;color:#92400e;">📦 项目【${nd.map(p => escapeHtml(p.project_name)).join('、')}】已立项但未做技术拆解，先到「工程管理 → 技术管理」拆解出可加工/可装配件后自动进入排产</div>`;
        return hint;
    }
    // 按项目聚合
    const projects = {};
    tasks.forEach(t => {
        const key = t.project_no || t.project_name || '未知项目';
        if (!projects[key]) projects[key] = { name: t.project_name || key, no: t.project_no || '', items: [], minDelivery: null, hasOverdue: false, hasTight: false };
        const p = projects[key];
        p.items.push(t);
        if (t.delivery_date) {
            if (!p.minDelivery || t.delivery_date < p.minDelivery) p.minDelivery = t.delivery_date;
        }
        if (t.risk === 'OVERDUE') p.hasOverdue = true;
        if (t.risk === 'TIGHT') p.hasTight = true;
    });
    // 按项目时间（最早交付日期）升序，无交付日期排最后
    const list = Object.values(projects).sort((a, b) => {
        if (a.minDelivery && b.minDelivery) return a.minDelivery < b.minDelivery ? -1 : 1;
        if (a.minDelivery) return -1;
        if (b.minDelivery) return 1;
        return 0;
    });
    let ndHint = '';
    const nd = _ppData.no_decomposition_projects || [];
    if (nd.length) ndHint = `<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:8px 12px;margin-bottom:10px;font-size:12px;color:#92400e;">📦 ${nd.length} 个项目未做技术拆解，暂未纳入排产（工程管理 → 技术管理）</div>`;
    const cardHtml = p => {
        const open = _ppOpenProject === p.no;
        const chip = p.hasOverdue ? ['已逾期', '#b91c1c', '#fee2e2'] : p.hasTight ? ['须立即开工', '#b45309', '#fef3c7'] : ['可按期', '#047857', '#d1fae5'];
        const totalQty = p.items.reduce((s, t) => s + (t.qty || 0), 0);
        const totalDays = p.items.reduce((s, t) => s + (t.needed_days || 0), 0);
        // 项目内零件按交付日期升序
        const sorted = p.items.slice().sort((a, b) => {
            if (a.delivery_date && b.delivery_date) return a.delivery_date < b.delivery_date ? -1 : 1;
            if (a.delivery_date) return -1;
            if (b.delivery_date) return 1;
            return 0;
        });
        const rows = sorted.map(t => {
            const range = t.suggested_start ? `${t.suggested_start} ~ ${t.suggested_end}` : '—';
            return `<tr>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;"><b>${escapeHtml(t.part_name)}</b>${t.spec ? ` <span style="color:#6b7280;font-size:11px;">${escapeHtml(t.spec)}</span>` : ''}<br><span style="font-size:10px;color:#9ca3af;font-family:monospace;">${escapeHtml(t.part_code)}</span></td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">${t.category}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:right;font-weight:bold;color:#b45309;">${t.qty} ${escapeHtml(t.unit)}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">${t.delivery_date || '—'}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">${t.needed_days ? t.needed_days + ' 天' : '—'}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">${t.latest_start || '—'}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;font-size:11px;">${range}</td>
                <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">${_ppRiskChip(t)}</td>
            </tr>`;
        }).join('');
        return `<div style="background:#fff;border:1px solid #e5e7eb;border-left:4px solid ${p.hasOverdue ? '#dc2626' : p.hasTight ? '#f59e0b' : '#22c55e'};border-radius:10px;overflow:hidden;margin-bottom:10px;">
            <div onclick="togglePpProject('${escapeHtml(p.no)}')" style="display:flex;align-items:center;gap:12px;padding:12px 16px;cursor:pointer;flex-wrap:wrap;">
                <div style="font-size:20px;">📁</div>
                <div style="flex:1;min-width:200px;">
                    <div style="font-size:14px;font-weight:600;color:#1f2937;">${escapeHtml(p.name)}</div>
                    <div style="font-size:11px;color:#9ca3af;margin-top:2px;">${escapeHtml(p.no)} · 零件 ${p.items.length} 项 / 共 ${totalQty} 件 · 所需 ${totalDays} 天</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:12px;font-weight:bold;color:#0369a1;">最早交付 ${p.minDelivery || '—'}</div>
                    <div style="font-size:10px;color:#9ca3af;">${open ? '点击收起 ▲' : '点击查看生产明细 ▼'}</div>
                </div>
                <span style="padding:3px 10px;border-radius:12px;font-size:11px;background:${chip[2]};color:${chip[1]};font-weight:bold;">${chip[0]}</span>
            </div>
            ${open ? `<div style="padding:0 16px 14px;">
                <div style="overflow-x:auto;">
                <table style="width:100%;border-collapse:collapse;font-size:12px;table-layout:fixed;">
                    <thead><tr style="background:#f5f5f5;">
                        <th style="border:1px solid #d1d5db;padding:6px 8px;width:180px;">零件</th>
                        <th style="border:1px solid #d1d5db;padding:6px 8px;width:55px;">类别</th>
                        <th style="border:1px solid #d1d5db;padding:6px 8px;width:90px;">数量</th>
                        <th style="border:1px solid #d1d5db;padding:6px 8px;width:95px;">交付日期</th>
                        <th style="border:1px solid #d1d5db;padding:6px 8px;width:70px;">所需天数</th>
                        <th style="border:1px solid #d1d5db;padding:6px 8px;width:95px;">最晚开工日</th>
                        <th style="border:1px solid #d1d5db;padding:6px 8px;width:170px;">建议开工 ~ 完工</th>
                        <th style="border:1px solid #d1d5db;padding:6px 8px;width:95px;">状态</th>
                    </tr></thead>
                    <tbody>${rows}</tbody>
                </table></div>
            </div>` : ''}
        </div>`;
    };
    return `<div style="font-size:11px;color:#9ca3af;margin-bottom:8px;">📁 按项目交付时间从早到晚排序，点击项目卡片查看生产明细。排产规则：所需天数 = 数量 ÷ 日产能合计（向上取整），从交付日期倒排最晚开工日</div>
    ${ndHint}
    <div>${list.map(cardHtml).join('')}</div>`;
}

function togglePpProject(no) {
    _ppOpenProject = (_ppOpenProject === no) ? null : no;
    _ppRenderView();
}

// ========== 视图2：生产日程（甘特） ==========
function _ppGanttHtml() {
    const tasks = (_ppData.tasks || []).filter(t => t.alloc && Object.keys(t.alloc).length);
    const loads = _ppData.date_loads || [];
    if (!tasks.length || !loads.length) return '<div style="color:#999;padding:30px;text-align:center;">暂无可排产任务（需有可用机器产能与带交付日期的生产任务）</div>';
    const riskColor = { OVERDUE: '#dc2626', TIGHT: '#f59e0b', OK: '#0ea5e9', NO_CAP: '#9ca3af', NO_DATE: '#9ca3af' };
    const headDates = loads.map(l => {
        const md = l.date.slice(5);
        const wk = ['日', '一', '二', '三', '四', '五', '六'][new Date(l.date + 'T00:00:00').getDay()];
        return `<th style="border:1px solid #e5e7eb;padding:4px 2px;min-width:56px;font-size:10px;">${md}<br><span style="color:#9ca3af;">周${wk}</span></th>`;
    }).join('');
    const loadRow = loads.map(l => {
        const col = l.rate >= 100 ? '#dc2626' : (l.rate >= 80 ? '#f59e0b' : '#16a34a');
        return `<td style="border:1px solid #e5e7eb;padding:3px 2px;text-align:center;font-size:10px;color:#fff;background:${col};">${l.rate}%</td>`;
    }).join('');
    const rows = tasks.map(t => {
        const color = riskColor[t.risk] || '#9ca3af';
        const cells = loads.map(l => {
            const q = t.alloc[l.date];
            return `<td style="border:1px solid #f1f5f9;padding:3px 2px;text-align:center;font-size:10px;${q ? `background:${color};color:#fff;font-weight:bold;border-radius:2px;` : 'color:#cbd5e1;'}">${q || ''}</td>`;
        }).join('');
        return `<tr>
            <td style="border:1px solid #e5e7eb;padding:5px 8px;position:sticky;left:0;background:#fff;min-width:170px;z-index:2;">
                <div style="font-size:12px;font-weight:bold;color:#1f2937;">${escapeHtml(t.part_name)} <span style="font-weight:normal;font-size:10px;color:${color};">[${t.category}]</span></div>
                <div style="font-size:10px;color:#9ca3af;">${escapeHtml(t.project_name)} · ${t.qty}${escapeHtml(t.unit)} · 交${t.delivery_date || '—'}</div>
            </td>
            ${cells}
        </tr>`;
    }).join('');
    return `<div style="font-size:11px;color:#9ca3af;margin-bottom:8px;">📊 首行=每日产能负荷率（<span style="color:#16a34a;">■&lt;80%正常</span> <span style="color:#f59e0b;">■80-99%偏满</span> <span style="color:#dc2626;">■≥100%超载</span>）；色块=当日计划产量</div>
    <div style="overflow-x:auto;max-height:70vh;overflow-y:auto;">
    <table style="border-collapse:collapse;font-size:12px;">
        <thead><tr style="background:#f5f5f5;"><th style="border:1px solid #d1d5db;padding:4px 8px;position:sticky;left:0;z-index:3;background:#f5f5f5;min-width:170px;">零件 / 日期</th>${headDates}</tr>
        <tr><th style="border:1px solid #d1d5db;padding:3px 8px;position:sticky;left:0;z-index:3;background:#f5f5f5;font-size:10px;color:#666;">日产能负荷率</th>${loadRow}</tr></thead>
        <tbody>${rows}</tbody>
    </table></div>`;
}
