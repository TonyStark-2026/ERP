// ============================================================
// PMC模块：生产物料控制（主计划→排产→物料需求联动）
// ============================================================
const PMC_API = '/api/v1/eng-modules';

// ---------- 通用工具 ----------
function _pmcStatusBadge(status) {
    const map = {
        'PLANNED': '<span style="background:#dbeafe;color:#1e40af;padding:2px 8px;border-radius:10px;font-size:12px;">已排产</span>',
        'RUNNING': '<span style="background:#fef3c7;color:#92400e;padding:2px 8px;border-radius:10px;font-size:12px;">生产中</span>',
        'COMPLETED': '<span style="background:#d1fae5;color:#065f46;padding:2px 8px;border-radius:10px;font-size:12px;">已完成</span>',
        'PAUSED': '<span style="background:#fee2e2;color:#991b1b;padding:2px 8px;border-radius:10px;font-size:12px;">暂停</span>',
        'CANCELLED': '<span style="background:#f3f4f6;color:#6b7280;padding:2px 8px;border-radius:10px;font-size:12px;">已取消</span>',
    };
    return map[status] || status;
}

function _pmcReadyBadge(status) {
    const map = {
        'READY': '<span style="background:#d1fae5;color:#065f46;padding:2px 8px;border-radius:10px;font-size:12px;">齐套</span>',
        'PARTIAL': '<span style="background:#fef3c7;color:#92400e;padding:2px 8px;border-radius:10px;font-size:12px;">部分齐套</span>',
        'SHORTAGE': '<span style="background:#fee2e2;color:#991b1b;padding:2px 8px;border-radius:10px;font-size:12px;">缺料</span>',
        'UNKNOWN': '<span style="background:#f3f4f6;color:#6b7280;padding:2px 8px;border-radius:10px;font-size:12px;">未知</span>',
    };
    return map[status] || status;
}

function _pmcPriorityBadge(p) {
    const map = {
        'URGENT': '<span style="color:#dc2626;font-weight:bold;">紧急</span>',
        'HIGH': '<span style="color:#f59e0b;font-weight:bold;">高</span>',
        'NORMAL': '<span style="color:#6b7280;">正常</span>',
        'LOW': '<span style="color:#9ca3af;">低</span>',
    };
    return map[p] || p;
}

// ---------- PMC主入口 ----------
function renderPMC() {
    renderPmcDashboard();
}

// ============================================================
// 1. PMC看板
// ============================================================
async function renderPmcDashboard() {
    const content = document.getElementById('content');
    if (!content) return;
    content.innerHTML = `<div class="content-header"><h2>📊 PMC生产物料控制看板</h2></div><div id="pmc-dash-loading">加载中...</div>`;
    try {
        const r = await fetch(`${PMC_API}/pmc/dashboard`);
        const d = await r.json();
        const ss = d.schedule_stats || {};
        const ms = d.material_stats || {};
        let html = `
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">
                <div style="background:#fff;padding:16px;border-radius:8px;border:1px solid #e5e7eb;">
                    <div style="color:#6b7280;font-size:13px;">排产单总数</div>
                    <div style="font-size:28px;font-weight:bold;color:#1e40af;">${ss.total||0}</div>
                </div>
                <div style="background:#fff;padding:16px;border-radius:8px;border:1px solid #e5e7eb;">
                    <div style="color:#6b7280;font-size:13px;">物料齐套</div>
                    <div style="font-size:28px;font-weight:bold;color:#065f46;">${ms.ready||0}</div>
                </div>
                <div style="background:#fff;padding:16px;border-radius:8px;border:1px solid #e5e7eb;${ms.overdue_shortage>0?'border-color:#ef4444;':''}">
                    <div style="color:#6b7280;font-size:13px;">逾期缺料预警</div>
                    <div style="font-size:28px;font-weight:bold;color:#dc2626;">${ms.overdue_shortage||0}</div>
                </div>
                <div style="background:#fff;padding:16px;border-radius:8px;border:1px solid #e5e7eb;">
                    <div style="color:#6b7280;font-size:13px;">今日排产</div>
                    <div style="font-size:28px;font-weight:bold;color:#92400e;">${d.today_schedule_count||0}</div>
                </div>
            </div>
        `;
        // 产能瓶颈
        html += `<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">`;
        html += `<div style="background:#fff;padding:16px;border-radius:8px;border:1px solid #e5e7eb;">
            <h3 style="margin:0 0 12px;font-size:15px;">⚠️ 产能瓶颈</h3>`;
        if ((d.capacity_bottlenecks||[]).length === 0) {
            html += '<p style="color:#9ca3af;">无</p>';
        } else {
            html += '<table class="data-table" style="width:100%;font-size:13px;"><thead><tr><th>生产线</th><th>需求</th><th>标准产能</th><th>利用率</th></tr></thead><tbody>';
            (d.capacity_bottlenecks||[]).forEach(l => {
                html += `<tr style="background:#fee2e2;"><td>${l.line_name||'-'}</td><td>${l.demand_qty}</td><td>${l.standard_capacity}</td><td style="color:#dc2626;font-weight:bold;">${l.utilization}%</td></tr>`;
            });
            html += '</tbody></table>';
        }
        html += `</div>`;
        // 缺料TOP10
        html += `<div style="background:#fff;padding:16px;border-radius:8px;border:1px solid #e5e7eb;">
            <h3 style="margin:0 0 12px;font-size:15px;">🔴 缺料预警TOP10</h3>`;
        if ((d.shortage_list||[]).length === 0) {
            html += '<p style="color:#9ca3af;">无</p>';
        } else {
            html += '<table class="data-table" style="width:100%;font-size:13px;"><thead><tr><th>物料编码</th><th>物料名称</th><th>缺料量</th><th>需求日期</th></tr></thead><tbody>';
            (d.shortage_list||[]).forEach(m => {
                html += `<tr style="background:#fee2e2;"><td>${m.material_code||'-'}</td><td>${m.material_name||'-'}</td><td style="color:#dc2626;font-weight:bold;">${m.deficit_qty}</td><td>${m.required_date||'-'}</td></tr>`;
            });
            html += '</tbody></table>';
        }
        html += `</div></div>`;
        content.innerHTML = html;
    } catch(e) {
        content.innerHTML = '<div class="error">加载看板失败</div>';
    }
}

// ============================================================
// 2. 产能负荷分析
// ============================================================
async function renderPmcCapacity() {
    const content = document.getElementById('content');
    if (!content) return;
    const today = new Date().toISOString().slice(0,10);
    const end = new Date(Date.now()+30*86400000).toISOString().slice(0,10);
    content.innerHTML = `
        <div class="content-header"><h2>📈 产能负荷分析</h2></div>
        <div style="margin-bottom:16px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
            <label>开始：<input type="date" id="pmc-cap-start" value="${today}" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;"></label>
            <label>结束：<input type="date" id="pmc-cap-end" value="${end}" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;"></label>
            <button onclick="loadPmcCapacity()" style="padding:6px 14px;background:#3b82f6;color:#fff;border:none;border-radius:6px;">分析</button>
        </div>
        <div id="pmc-cap-list">加载中...</div>
    `;
    loadPmcCapacity();
}

async function loadPmcCapacity() {
    const start = document.getElementById('pmc-cap-start')?.value;
    const end = document.getElementById('pmc-cap-end')?.value;
    const el = document.getElementById('pmc-cap-list');
    try {
        const r = await fetch(`${PMC_API}/pmc/capacity-analysis?start=${start}&end=${end}`);
        const d = await r.json();
        if ((d.lines||[]).length === 0) { el.innerHTML = '<div class="empty">无数据</div>'; return; }
        let html = '';
        html += '<table class="data-table" style="width:100%;font-size:13px;"><thead><tr><th>生产线</th><th>车间</th><th>工序</th><th>标准产能</th><th>最大产能(含加班)</th><th>需求数量</th><th>利用率</th><th>状态</th></tr></thead><tbody>';
        (d.lines||[]).forEach(l => {
            const bg = l.bottleneck ? '#fee2e2' : (l.utilization >= 80 ? '#fef3c7' : '');
            html += `<tr style="background:${bg};">
                <td><b>${l.line_name}</b></td>
                <td>${l.workshop||'-'}</td>
                <td>${l.process_codes||'-'}</td>
                <td>${l.standard_capacity}</td>
                <td>${l.max_capacity}</td>
                <td>${l.demand_qty}</td>
                <td style="font-weight:bold;${l.utilization>=100?'color:#dc2626':l.utilization>=80?'color:#f59e0b':''}">${l.utilization}%</td>
                <td>${l.bottleneck?'🔴 瓶颈':l.utilization>=80?'🟡 负荷高':'🟢 正常'}</td>
            </tr>`;
        });
        html += '</tbody></table>';
        el.innerHTML = html;
    } catch(e) { el.innerHTML = '<div class="error">加载失败</div>'; }
}

// ============================================================
// 3. 生产排产计划
// ============================================================
async function renderPmcSchedules(targetId) {
    const content = document.getElementById(targetId || 'content');
    if (!content) return;
    content.innerHTML = `
        ${targetId ? '' : '<div class="content-header"><h2>📅 生产排产计划</h2></div>'}
        <div id="pmc-optimal" style="margin-bottom:16px;"><div style="color:#888;padding:14px;text-align:center;background:#f8fafc;border-radius:8px;">⚡ 产能分析计算中...</div></div>
        <div style="margin-bottom:16px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
            <button onclick="showPmcScheduleForm()" style="padding:6px 14px;background:#3b82f6;color:#fff;border:none;border-radius:6px;">➕ 新建排产</button>
            <select id="pmc-sched-filter" onchange="loadPmcSchedules()" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;">
                <option value="">全部状态</option>
                <option value="PLANNED">已排产</option>
                <option value="RUNNING">生产中</option>
                <option value="COMPLETED">已完成</option>
            </select>
            <button onclick="loadPmcSchedules()" style="padding:6px 14px;background:#9ca3af;color:#fff;border:none;border-radius:6px;">🔄 刷新</button>
        </div>
        <div id="pmc-sched-list">加载中...</div>
        <div id="pmc-sched-detail"></div>
    `;
    loadOptimalSchedule();
    loadPmcSchedules();
}

// ========== 产能最优排产分析（最快完成方案 + 甘特可视化） ==========
async function loadOptimalSchedule() {
    const el = document.getElementById('pmc-optimal');
    if (!el) return;
    try {
        const r = await fetch('/api/v1/pp/optimal-schedule', { headers: authHeaders });
        const d = await r.json();
        if (!d.success) throw new Error(d.message || '加载失败');
        el.innerHTML = _optimalScheduleHtml(d.data);
    } catch (e) {
        el.innerHTML = `<div style="color:#b91c1c;padding:10px;background:#fef2f2;border-radius:8px;font-size:12px;">产能分析加载失败：${escapeHtml(e.message || '')}</div>`;
    }
}

function _optimalScheduleHtml(d) {
    const color = v => v >= 100 ? '#dc2626' : v >= 80 ? '#ea580c' : '#16a34a';
    // 工序配色：下料/焊接/机加/钻孔/装配
    const GC = { cut: '#0ea5e9', weld: '#f97316', machine: '#3b82f6', drill: '#a855f7', assembly: '#22c55e' };
    if (!d.tasks || !d.tasks.length) {
        return `<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:10px;padding:16px;text-align:center;color:#0369a1;font-size:13px;">
            ⚡ 暂无可排产的自制件任务 — 项目BOM导入确认后（加工/装配零件）自动进入智能排产</div>`;
    }
    const _days = (a, b) => Math.round((new Date(b) - new Date(a)) / 86400000);
    const totalDays = Math.max(1, _days(d.today, d.fastest_finish || d.today) + 1);
    // 工序产能卡（瓶颈高亮红框）
    const poolCards = (d.pool_analysis || []).map(p => `
        <div style="background:#fff;border:1px solid ${p.is_bottleneck ? '#fca5a5' : '#e5e7eb'};${p.is_bottleneck ? 'box-shadow:0 0 0 2px #fee2e2;' : ''}border-radius:10px;padding:10px 12px;">
            <div style="font-size:12px;font-weight:bold;color:#374151;">${p.is_bottleneck ? '🔓 ' : '🏭 '}${escapeHtml(p.pool)}工序 ${p.is_bottleneck ? '<span style="color:#dc2626;font-size:10px;">瓶颈</span>' : ''} <span style="font-weight:normal;color:#9ca3af;font-size:10px;">${p.equip_count}台</span></div>
            <div style="font-size:11px;color:#6b7280;margin:2px 0;">${p.equipments && p.equipments.length ? escapeHtml(p.equipments.join('、')) : '无对应设备'}</div>
            <div style="font-size:15px;font-weight:bold;color:#0369a1;">${p.capacity}${escapeHtml(p.unit)}/天 <span style="font-size:10px;color:#9ca3af;font-weight:normal;">(应急线${p.eff_capacity})</span></div>
            <div style="font-size:10px;color:#6b7280;margin-top:2px;">工作量 ${p.workload} · 最快 ${p.min_days || '—'} 天${p.finish_date ? ' · 完工 ' + p.finish_date : ''}</div>
        </div>`).join('');
    // 甘特时间刻度
    const tickStep = totalDays <= 10 ? 1 : totalDays <= 30 ? 5 : 10;
    let ticks = '';
    for (let i = 0; i < totalDays; i += tickStep) {
        const ds = new Date(new Date(d.today).getTime() + i * 86400000).toISOString().slice(5, 10);
        ticks += `<div style="position:absolute;left:${(i / totalDays * 100).toFixed(2)}%;top:0;font-size:9px;color:#9ca3af;transform:translateX(2px);">${ds}</div>`;
    }
    const rows = d.tasks.map(t => {
        const gc = GC[t.group] || '#64748b';
        const star = t.critical ? '<span style="color:#f59e0b;" title="关键路径">⭐</span> ' : '';
        if (!t.start || !t.end) {
            return `<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                <div style="width:210px;font-size:11px;color:#374151;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${escapeHtml(t.project_name)} / ${escapeHtml(t.part_name)}">${star}${escapeHtml(t.part_name)} <span style="color:#2563eb;font-size:10px;">${escapeHtml(t.group_label)}</span></div>
                <div style="flex:1;position:relative;height:20px;background:#f8fafc;border-radius:4px;">
                    <span style="position:absolute;left:6px;top:2px;font-size:10px;color:#b91c1c;">⚠ ${escapeHtml(t.reason || '无法排产')}</span>
                </div></div>`;
        }
        const left = (_days(d.today, t.start) / totalDays * 100).toFixed(2);
        const width = Math.max(2, (t.days / totalDays * 100)).toFixed(2);
        const late = !t.on_time;
        const equip = (t.equipment || []).join('、');
        return `<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;" title="${escapeHtml(t.project_name)} / ${escapeHtml(t.part_name)} ${escapeHtml(t.spec || '')}\n工序：${escapeHtml(t.group_label)}（${escapeHtml(equip)}）| 前置：${escapeHtml(t.prereq || '无')}\n${t.start} ~ ${t.end} 共${t.days}天 | 交付 ${t.delivery_date || '—'}\n${late ? '⚠ ' + escapeHtml(t.reason || '无法按期') : '✓ 可按期'}${t.critical ? ' | ⭐关键路径' : ''}">
            <div style="width:210px;font-size:11px;color:#374151;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${star}${escapeHtml(t.part_name)} <span style="color:#9ca3af;">${t.qty}${escapeHtml(t.unit)}</span> <span style="color:${gc};font-size:10px;font-weight:bold;">${escapeHtml(t.group_label)}</span></div>
            <div style="flex:1;position:relative;height:20px;background:#f8fafc;border-radius:4px;">
                <div style="position:absolute;left:${left}%;width:${width}%;top:2px;height:16px;background:${gc};${late ? 'box-shadow:inset 0 0 0 2px #dc2626;' : ''}border-radius:4px;overflow:hidden;white-space:nowrap;">
                    <span style="font-size:9px;color:#fff;padding-left:4px;line-height:16px;">${t.start.slice(5)}~${t.end.slice(5)} ${t.days}天</span>
                </div>
            </div>
            ${late ? '<span style="font-size:10px;color:#dc2626;font-weight:bold;flex-shrink:0;">⚠</span>' : ''}
        </div>`;
    }).join('');
    // 项目汇总（含关键路径件）
    const projRows = (d.projects || []).map(p => `
        <tr>
            <td style="padding:5px 8px;border-bottom:1px solid #f1f5f9;"><b>${escapeHtml(p.project_name)}</b> <span style="font-size:10px;color:#9ca3af;">${escapeHtml(p.project_no)}</span></td>
            <td style="padding:5px 8px;border-bottom:1px solid #f1f5f9;text-align:center;">${p.parts} 项</td>
            <td style="padding:5px 8px;border-bottom:1px solid #f1f5f9;font-size:10px;color:#b45309;">${(p.critical || []).length ? '⭐' + escapeHtml(p.critical.slice(0, 3).join('、')) + (p.critical.length > 3 ? '…' : '') : ''}</td>
            <td style="padding:5px 8px;border-bottom:1px solid #f1f5f9;text-align:center;font-size:11px;">${p.start || '—'} ~ ${p.end || '—'}</td>
            <td style="padding:5px 8px;border-bottom:1px solid #f1f5f9;text-align:center;">交付 ${p.delivery_date || '—'}</td>
            <td style="padding:5px 8px;border-bottom:1px solid #f1f5f9;text-align:center;">
                ${p.all_on_time ? '<span style="padding:2px 8px;border-radius:10px;font-size:10px;background:#d1fae5;color:#047857;font-weight:bold;">✓ 可按期</span>' : '<span style="padding:2px 8px;border-radius:10px;font-size:10px;background:#fee2e2;color:#b91c1c;font-weight:bold;">⚠ 无法按期</span>'}</td>
        </tr>`).join('');
    // 每日负荷（前14天）
    const loadBars = (d.daily_load || []).slice(0, 14).map(x => `
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px;">
            <div style="width:52px;font-size:10px;color:#6b7280;">${x.date.slice(5)}</div>
            <div style="flex:1;background:#f1f5f9;border-radius:4px;height:12px;overflow:hidden;">
                <div style="height:100%;width:${Math.min(100, x.rate)}%;background:${color(x.rate)};border-radius:4px;"></div></div>
            <div style="width:88px;font-size:10px;color:${color(x.rate)};text-align:right;font-weight:bold;">${x.load}/${d.total_capacity} ${x.rate}%</div>
        </div>`).join('');
    return `<div style="background:linear-gradient(135deg,#eef2ff,#e0f2fe);border:1px solid #c7d2fe;border-radius:12px;padding:14px 16px;">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:6px;">
            <div style="font-size:14px;font-weight:bold;color:#1e3a8a;">⚡ 智能排产 · 五规则最快完成方案</div>
        </div>
        <div style="font-size:10px;color:#64748b;line-height:1.7;margin-bottom:10px;background:rgba(255,255,255,.6);border-radius:6px;padding:6px 10px;">
            排产规则（哪个等不起就先干）：<b>①关键路径</b>⭐焊接/装配优先 → <b>②瓶颈设备</b>满负荷先行 → <b>③物料齐套</b>下料→焊接→钻孔→装配逐级驱动 → <b>④负载均衡</b>连续排产 → <b>⑤应急预留</b>每日留 ${d.reserve_pct || 15}% 弹性产能给插单返工</div>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:8px;margin-bottom:12px;">
            <div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:10px 12px;">
                <div style="font-size:12px;color:#6b7280;">🚀 全部任务最快完工</div>
                <div style="font-size:20px;font-weight:bold;color:#0369a1;">${d.fastest_finish || '—'}</div></div>
            <div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:10px 12px;">
                <div style="font-size:12px;color:#6b7280;">📋 排产任务</div>
                <div style="font-size:20px;font-weight:bold;color:#374151;">${d.task_count} 项 <span style="font-size:12px;${d.late_count ? 'color:#dc2626;' : 'color:#16a34a;'}">${d.late_count ? d.late_count + ' 项无法按期' : '全部可按期'}</span></div></div>
            ${d.bottleneck ? `<div style="background:#fff;border:1px solid #fecaca;border-radius:10px;padding:10px 12px;">
                <div style="font-size:12px;color:#6b7280;">🔓 瓶颈工序（决定交期）</div>
                <div style="font-size:15px;font-weight:bold;color:#b91c1c;">${escapeHtml(d.bottleneck.pool || d.bottleneck.label || '')}工序 <span style="font-size:11px;font-weight:normal;color:#6b7280;">完工 ${d.bottleneck.finish_date || '—'}</span></div></div>` : ''}
            ${poolCards}
        </div>
        <div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:12px;margin-bottom:10px;">
            <div style="font-size:12px;font-weight:bold;color:#374151;margin-bottom:8px;">📊 排产甘特图 <span style="font-weight:normal;font-size:10px;color:#9ca3af;">（<span style="color:#0ea5e9;">■下料</span> <span style="color:#f97316;">■焊接</span> <span style="color:#3b82f6;">■机加</span> <span style="color:#a855f7;">■钻孔</span> <span style="color:#22c55e;">■装配</span> ⭐关键路径 红框=无法按期，悬停看前置条件）</span></div>
            <div style="position:relative;height:16px;margin:0 0 4px 218px;">${ticks}</div>
            ${rows}
        </div>
        ${projRows ? `<div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:12px;margin-bottom:10px;overflow-x:auto;">
            <div style="font-size:12px;font-weight:bold;color:#374151;margin-bottom:6px;">📁 项目最快完成方案（关键路径件）</div>
            <table style="width:100%;border-collapse:collapse;font-size:12px;">
                <thead><tr style="background:#f8fafc;color:#6b7280;font-size:11px;">
                    <th style="padding:5px 8px;text-align:left;">项目</th><th style="padding:5px 8px;">任务</th><th style="padding:5px 8px;text-align:left;">⭐关键路径</th>
                    <th style="padding:5px 8px;">最快开工 ~ 完工</th><th style="padding:5px 8px;">交付要求</th><th style="padding:5px 8px;">结论</th>
                </tr></thead><tbody>${projRows}</tbody></table></div>` : ''}
        ${loadBars ? `<div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:12px;">
            <div style="font-size:12px;font-weight:bold;color:#374151;margin-bottom:8px;">🔋 未来14天全厂负荷（已按85%应急线排产，超出即预警）</div>${loadBars}</div>` : ''}
    </div>`;
}

async function loadPmcSchedules() {
    const el = document.getElementById('pmc-sched-list');
    const filter = document.getElementById('pmc-sched-filter')?.value || '';
    try {
        const r = await fetch(`${PMC_API}/pmc/schedules${filter?('?status='+filter):''}`);
        const data = await r.json();
        if (!data.length) { el.innerHTML = '<div class="empty">暂无排产单，点击「新建排产」</div>'; return; }
        let html = '<table class="data-table" style="width:100%;font-size:13px;"><thead><tr><th>排产单号</th><th>产品</th><th>需求</th><th>计划时间</th><th>生产线</th><th>优先级</th><th>插单</th><th>齐套</th><th>状态</th><th>操作</th></tr></thead><tbody>';
        data.forEach(s => {
            html += `<tr>
                <td>${s.schedule_no}</td>
                <td>${s.product_name||'-'}</td>
                <td>${s.demand_qty}</td>
                <td>${s.plan_start_date||'-'} ~ ${s.plan_end_date||'-'}</td>
                <td>${s.line_name||'-'}</td>
                <td>${_pmcPriorityBadge(s.priority)}</td>
                <td>${s.is_insert?'⚡是':'否'}</td>
                <td>${_pmcReadyBadge(s.material_ready_status)}</td>
                <td>${_pmcStatusBadge(s.status)}</td>
                <td>
                    <button onclick="showPmcScheduleDetail(${s.id})" style="color:#3b82f6;border:none;background:none;cursor:pointer;">详情</button>
                    <button onclick="pmcToggleInsert(${s.id}, ${s.is_insert?0:1})" style="color:#f59e0b;border:none;background:none;cursor:pointer;">${s.is_insert?'取消插单':'插单'}</button>
                </td>
            </tr>`;
        });
        html += '</tbody></table>';
        el.innerHTML = html;
    } catch(e) { el.innerHTML = '<div class="error">加载失败</div>'; }
}

function showPmcScheduleForm() {
    const el = document.getElementById('pmc-sched-detail');
    const today = new Date().toISOString().slice(0,10);
    const end = new Date(Date.now()+7*86400000).toISOString().slice(0,10);
    el.innerHTML = `
        <div style="background:#f0f9ff;padding:16px;border-radius:8px;margin-top:16px;">
            <h4 style="margin:0 0 12px;">新建排产单</h4>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">
                <input id="ps-product" placeholder="产品名称" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;">
                <input id="ps-demand" type="number" placeholder="需求数量" value="100" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;">
                <select id="ps-line" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;"><option value="">加载中...</option></select>
                <input id="ps-start" type="date" value="${today}" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;">
                <input id="ps-end" type="date" value="${end}" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;">
                <select id="ps-priority" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;">
                    <option value="NORMAL">正常</option><option value="HIGH">高</option><option value="URGENT">紧急</option>
                </select>
                <input id="ps-bom-id" type="number" placeholder="BOM ID(可选)" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;">
                <select id="ps-insert" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;">
                    <option value="0">正常排产</option><option value="1">⚡插单</option>
                </select>
                <input id="ps-remark" placeholder="备注" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;">
            </div>
            <div style="margin-top:12px;">
                <button onclick="submitPmcSchedule()" style="padding:6px 14px;background:#10b981;color:#fff;border:none;border-radius:6px;">保存并生成排产+物料需求</button>
                <button onclick="document.getElementById('pmc-sched-detail').innerHTML=''" style="padding:6px 14px;background:#9ca3af;color:#fff;border:none;border-radius:6px;margin-left:8px;">取消</button>
            </div>
        </div>
    `;
    // 加载生产线下拉
    fetch(`${PMC_API}/pmc/lines`).then(r=>r.json()).then(lines => {
        const sel = document.getElementById('ps-line');
        if (!sel) return;
        sel.innerHTML = '<option value="">未指定</option>' + lines.map(l=>`<option value="${l.id}">${l.line_name}</option>`).join('');
    }).catch(()=>{});
}

async function submitPmcSchedule() {
    const body = {
        product_name: document.getElementById('ps-product').value.trim(),
        demand_qty: parseFloat(document.getElementById('ps-demand').value) || 0,
        line_id: parseInt(document.getElementById('ps-line').value) || null,
        plan_start_date: document.getElementById('ps-start').value,
        plan_end_date: document.getElementById('ps-end').value,
        priority: document.getElementById('ps-priority').value,
        bom_id: parseInt(document.getElementById('ps-bom-id').value) || null,
        is_insert: parseInt(document.getElementById('ps-insert').value) || 0,
        remark: document.getElementById('ps-remark').value.trim(),
    };
    try {
        const r = await fetch(`${PMC_API}/pmc/schedules`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
        const d = await r.json();
        if (d.success) {
            showToast(`排产单创建成功：${d.schedule_no}，已自动生成排产明细+物料需求`);
            document.getElementById('pmc-sched-detail').innerHTML = '';
            loadPmcSchedules();
        } else showToast(d.detail || '创建失败', 'error');
    } catch(e) { showToast('创建失败：'+e.message, 'error'); }
}

async function showPmcScheduleDetail(id) {
    const el = document.getElementById('pmc-sched-detail');
    try {
        const r = await fetch(`${PMC_API}/pmc/schedules/${id}`);
        const d = await r.json();
        const s = d.schedule;
        let html = `<div style="background:#fff;padding:16px;border-radius:8px;border:1px solid #e5e7eb;margin-top:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <h3 style="margin:0;">排产单 ${s.schedule_no}</h3>
                <div>
                    <button onclick="pmcChangeStatus(${id},'RUNNING')" style="padding:4px 10px;background:#f59e0b;color:#fff;border:none;border-radius:4px;">开始生产</button>
                    <button onclick="pmcChangeStatus(${id},'COMPLETED')" style="padding:4px 10px;background:#10b981;color:#fff;border:none;border-radius:4px;">完成</button>
                    <button onclick="pmcRecalcMaterial(${id})" style="padding:4px 10px;background:#6366f1;color:#fff;border:none;border-radius:4px;">重算物料</button>
                </div>
            </div>
            <div style="margin-bottom:12px;font-size:13px;color:#6b7280;">
                产品：${s.product_name||'-'} | 需求：${s.demand_qty} | 计划：${s.plan_start_date} ~ ${s.plan_end_date} | 状态：${_pmcStatusBadge(s.status)} | 齐套：${_pmcReadyBadge(s.material_ready_status)}
            </div>`;
        // 排产明细（加班调节）
        html += `<h4 style="margin:12px 0 8px;font-size:14px;">📅 排产明细</h4>`;
        if ((d.items||[]).length === 0) {
            html += '<p style="color:#9ca3af;">无排产明细</p>';
        } else {
            html += '<table class="data-table" style="width:100%;font-size:13px;"><thead><tr><th>日期</th><th>工序</th><th>计划数量</th><th>完成</th><th>基础工时</th><th>加班工时</th><th>操作</th></tr></thead><tbody>';
            d.items.forEach(it => {
                html += `<tr>
                    <td>${it.schedule_date}</td>
                    <td>${it.process_name||'-'}</td>
                    <td>${it.planned_qty}</td>
                    <td>${it.completed_qty}</td>
                    <td>${it.base_hours}</td>
                    <td><input type="number" id="ot-${it.id}" value="${it.overtime_hours}" style="width:60px;padding:2px;border:1px solid #d1d5db;border-radius:4px;"></td>
                    <td><button onclick="pmcAdjustOvertime(${it.id})" style="color:#3b82f6;border:none;background:none;cursor:pointer;">保存加班</button></td>
                </tr>`;
            });
            html += '</tbody></table>';
        }
        // 物料需求
        html += `<h4 style="margin:12px 0 8px;font-size:14px;">📦 物料需求（排产联动MRP）</h4>`;
        if ((d.demands||[]).length === 0) {
            html += '<p style="color:#9ca3af;">无物料需求（排产单未关联BOM）</p>';
        } else {
            html += '<table class="data-table" style="width:100%;font-size:13px;"><thead><tr><th>物料</th><th>总需求</th><th>库存</th><th>在途</th><th>缺料</th><th>提前期</th><th>需到位日期</th><th>齐套</th></tr></thead><tbody>';
            d.demands.forEach(m => {
                const bg = m.ready_status==='SHORTAGE' ? '#fee2e2' : (m.ready_status==='PARTIAL' ? '#fef3c7' : '');
                html += `<tr style="background:${bg};">
                    <td>${m.material_code||'-'} ${m.material_name||''}</td>
                    <td>${m.total_demand}</td>
                    <td>${m.stock_qty}</td>
                    <td>${m.intransit_qty}</td>
                    <td style="${m.deficit_qty>0?'color:#dc2626;font-weight:bold;':''}">${m.deficit_qty}</td>
                    <td>${m.lead_time_days}天</td>
                    <td>${m.schedule_date||'-'}</td>
                    <td>${_pmcReadyBadge(m.ready_status)}</td>
                </tr>`;
            });
            html += '</tbody></table>';
        }
        html += `</div>`;
        el.innerHTML = html;
    } catch(e) { el.innerHTML = '<div class="error">加载详情失败</div>'; }
}

async function pmcAdjustOvertime(itemId) {
    const ot = parseFloat(document.getElementById(`ot-${itemId}`).value) || 0;
    try {
        const r = await fetch(`${PMC_API}/pmc/schedule-items/${itemId}/overtime`, {
            method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({overtime_hours: ot})
        });
        const d = await r.json();
        if (d.success) showToast('加班工时已保存');
    } catch(e) { showToast('保存失败', 'error'); }
}

async function pmcChangeStatus(id, status) {
    try {
        const r = await fetch(`${PMC_API}/pmc/schedules/${id}/status`, {
            method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({status})
        });
        const d = await r.json();
        if (d.success) { showToast('状态已更新'); loadPmcSchedules(); }
    } catch(e) { showToast('更新失败', 'error'); }
}

async function pmcToggleInsert(id, isInsert) {
    try {
        const r = await fetch(`${PMC_API}/pmc/schedules/${id}/status`, {
            method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({is_insert: isInsert})
        });
        const d = await r.json();
        if (d.success) { showToast(isInsert?'已标记为插单':'已取消插单'); loadPmcSchedules(); }
    } catch(e) { showToast('操作失败', 'error'); }
}

async function pmcRecalcMaterial(id) {
    try {
        const r = await fetch(`${PMC_API}/pmc/schedules/${id}/recalc-material`, {method:'POST'});
        const d = await r.json();
        if (d.success) { showToast(`物料需求已重算，齐套状态：${d.material_ready_status}`); showPmcScheduleDetail(id); loadPmcSchedules(); }
    } catch(e) { showToast('重算失败', 'error'); }
}

// ============================================================
// 4. 物料需求齐套
// ============================================================
async function renderPmcMaterialDemands() {
    const content = document.getElementById('content');
    if (!content) return;
    content.innerHTML = `
        <div class="content-header"><h2>📦 PMC物料需求齐套</h2></div>
        <div style="margin-bottom:16px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
            <select id="pmc-md-filter" onchange="loadPmcMaterialDemands()" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;">
                <option value="">全部状态</option>
                <option value="READY">齐套</option>
                <option value="PARTIAL">部分齐套</option>
                <option value="SHORTAGE">缺料</option>
            </select>
            <button onclick="loadPmcMaterialDemands()" style="padding:6px 14px;background:#9ca3af;color:#fff;border:none;border-radius:6px;">🔄 刷新</button>
        </div>
        <div id="pmc-md-list">加载中...</div>
    `;
    loadPmcMaterialDemands();
}

async function loadPmcMaterialDemands() {
    const el = document.getElementById('pmc-md-list');
    const filter = document.getElementById('pmc-md-filter')?.value || '';
    try {
        const r = await fetch(`${PMC_API}/pmc/material-demands${filter?('?ready_status='+filter):''}`);
        const data = await r.json();
        if (!data.length) { el.innerHTML = '<div class="empty">暂无物料需求</div>'; return; }
        let html = '<table class="data-table" style="width:100%;font-size:13px;"><thead><tr><th>物料编码</th><th>物料名称</th><th>规格</th><th>总需求</th><th>库存</th><th>在途</th><th>缺料</th><th>提前期</th><th>需到位日期</th><th>需求下单日期</th><th>齐套</th></tr></thead><tbody>';
        data.forEach(m => {
            const bg = m.ready_status==='SHORTAGE' ? '#fee2e2' : (m.ready_status==='PARTIAL' ? '#fef3c7' : '');
            html += `<tr style="background:${bg};">
                <td>${m.material_code||'-'}</td>
                <td>${m.material_name||'-'}</td>
                <td>${m.spec||'-'}</td>
                <td>${m.total_demand}</td>
                <td>${m.stock_qty}</td>
                <td>${m.intransit_qty}</td>
                <td style="${m.deficit_qty>0?'color:#dc2626;font-weight:bold;':''}">${m.deficit_qty}</td>
                <td>${m.lead_time_days}天</td>
                <td>${m.schedule_date||'-'}</td>
                <td>${m.required_date||'-'}</td>
                <td>${_pmcReadyBadge(m.ready_status)}</td>
            </tr>`;
        });
        html += '</tbody></table>';
        el.innerHTML = html;
    } catch(e) { el.innerHTML = '<div class="error">加载失败</div>'; }
}

// ============================================================
// 5. 生产线管理
// ============================================================
async function renderPmcLines(targetId) {
    const content = document.getElementById(targetId || 'content');
    if (!content) return;
    content.innerHTML = `
        ${targetId ? '' : '<div class="content-header"><h2>🏭 生产线管理</h2></div>'}
        <div style="margin-bottom:16px;">
            <button onclick="showPmcLineForm()" style="padding:6px 14px;background:#3b82f6;color:#fff;border:none;border-radius:6px;">➕ 新建生产线</button>
        </div>
        <div id="pmc-line-list">加载中...</div>
        <div id="pmc-line-form"></div>
    `;
    loadPmcLines();
}

async function loadPmcLines() {
    const el = document.getElementById('pmc-line-list');
    try {
        const r = await fetch(`${PMC_API}/pmc/lines`);
        const data = await r.json();
        if (!data.length) { el.innerHTML = '<div class="empty">暂无生产线，点击「新建生产线」</div>'; return; }
        let html = '<table class="data-table" style="width:100%;font-size:13px;"><thead><tr><th>编号</th><th>名称</th><th>车间</th><th>每日产能</th><th>班次</th><th>最大加班/班</th><th>工序</th><th>状态</th><th>操作</th></tr></thead><tbody>';
        data.forEach(l => {
            html += `<tr>
                <td>${l.line_code}</td>
                <td><b>${l.line_name}</b></td>
                <td>${l.workshop||'-'}</td>
                <td>${l.daily_capacity}</td>
                <td>${l.shift_count}×${l.shift_hours}h</td>
                <td>${l.max_overtime_hours}h</td>
                <td>${l.process_codes||'-'}</td>
                <td>${l.status==='ACTIVE'?'<span style="color:#065f46;">启用</span>':'停用'}</td>
                <td><button onclick="deletePmcLine(${l.id})" style="color:#ef4444;border:none;background:none;cursor:pointer;">删除</button></td>
            </tr>`;
        });
        html += '</tbody></table>';
        el.innerHTML = html;
    } catch(e) { el.innerHTML = '<div class="error">加载失败</div>'; }
}

function showPmcLineForm() {
    const el = document.getElementById('pmc-line-form');
    el.innerHTML = `
        <div style="background:#f0f9ff;padding:16px;border-radius:8px;margin-top:12px;">
            <h4 style="margin:0 0 12px;">新建生产线</h4>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">
                <input id="pl-name" placeholder="生产线名称" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;">
                <input id="pl-workshop" placeholder="车间" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;">
                <input id="pl-capacity" type="number" placeholder="每日标准产能(件)" value="100" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;">
                <input id="pl-shift-count" type="number" placeholder="每日班次" value="1" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;">
                <input id="pl-shift-hours" type="number" placeholder="每班工时" value="8" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;">
                <input id="pl-overtime" type="number" placeholder="最大加班工时/班" value="3" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;">
                <input id="pl-process" placeholder="工序(逗号分隔,如 CNC,打磨,组装)" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;">
                <select id="pl-status" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;"><option value="ACTIVE">启用</option><option value="MAINTENANCE">维护中</option><option value="DISABLED">停用</option></select>
            </div>
            <div style="margin-top:12px;">
                <button onclick="submitPmcLine()" style="padding:6px 14px;background:#10b981;color:#fff;border:none;border-radius:6px;">保存</button>
                <button onclick="document.getElementById('pmc-line-form').innerHTML=''" style="padding:6px 14px;background:#9ca3af;color:#fff;border:none;border-radius:6px;margin-left:8px;">取消</button>
            </div>
        </div>
    `;
}

async function submitPmcLine() {
    const body = {
        line_name: document.getElementById('pl-name').value.trim(),
        workshop: document.getElementById('pl-workshop').value.trim(),
        daily_capacity: parseFloat(document.getElementById('pl-capacity').value) || 0,
        shift_count: parseInt(document.getElementById('pl-shift-count').value) || 1,
        shift_hours: parseFloat(document.getElementById('pl-shift-hours').value) || 8,
        max_overtime_hours: parseFloat(document.getElementById('pl-overtime').value) || 3,
        process_codes: document.getElementById('pl-process').value.trim(),
        status: document.getElementById('pl-status').value,
    };
    if (!body.line_name) { showToast('请输入生产线名称', 'warning'); return; }
    try {
        const r = await fetch(`${PMC_API}/pmc/lines`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
        const d = await r.json();
        if (d.success) { showToast('生产线已创建'); document.getElementById('pmc-line-form').innerHTML=''; loadPmcLines(); }
    } catch(e) { showToast('创建失败', 'error'); }
}

async function deletePmcLine(id) {
    try {
        const r = await fetch(`${PMC_API}/pmc/lines/${id}`, {method:'DELETE'});
        const d = await r.json();
        if (d.success) { showToast('已删除'); loadPmcLines(); }
    } catch(e) { showToast('删除失败', 'error'); }
}
