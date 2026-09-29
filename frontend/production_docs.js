/**
 * 生产单据体系 - 前端模块
 * 8种单据 + 下推 + 双向追溯 + SVG关系图
 */

// ========== 全局状态 ==========
window._pdTab = 'work_orders';
window._pdCurrentDocId = null;
window._pdCurrentDocType = null;

// ========== 工具函数 ==========
function pdStatusBadge(status) {
    const map = {
        '草稿': '#94a3b8', '已确认': '#3b82f6', '已下达': '#8b5cf6',
        '生产中': '#f59e0b', '已完工': '#10b981', '已关闭': '#64748b', '已取消': '#ef4444'
    };
    const color = map[status] || '#94a3b8';
    return `<span style="display:inline-block;padding:2px 8px;border-radius:10px;font-size:12px;color:#fff;background:${color}">${status}</span>`;
}

function pdDocTypeLabel(type) {
    const map = {
        'work_order': '生产工单', 'component_list': '组件清单', 'process_plan': '工序计划',
        'pick': '领料单', 'material_return': '退料单', 'replenish': '补料单',
        'inbound': '完工入库单', 'return_inbound': '完工退库单'
    };
    return map[type] || type;
}

async function pdApi(url, method = 'GET', body = null) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const r = await fetch('/api/v1/pd' + url, opts);
    return await r.json();
}

// ========== 渲染主入口 ==========
function renderProductionDocs() {
    return `
    <div style="padding:16px;max-width:1400px;margin:0 auto;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
            <h2 style="margin:0;">📦 生产单据体系 <small style="font-size:14px;color:#64748b;">单据流转 · 下推追溯 · 关系图</small></h2>
            <div>
                <button class="btn btn-secondary" onclick="pdRefresh()">🔄 刷新</button>
            </div>
        </div>

        <!-- Tab栏 -->
        <div style="display:flex;gap:4px;border-bottom:2px solid #e2e8f0;margin-bottom:16px;flex-wrap:wrap;">
            ${['work_orders','picks','inbounds','material_returns','replenishes','return_inbounds'].map(t => {
                const labels = { work_orders:'生产工单', picks:'领料单', inbounds:'完工入库', material_returns:'退料单', replenishes:'补料单', return_inbounds:'退库单' };
                const active = window._pdTab === t;
                return `<button onclick="pdSwitchTab('${t}')" style="padding:8px 16px;border:none;background:${active?'#3b82f6':'transparent'};color:${active?'#fff':'#64748b'};cursor:pointer;border-radius:6px 6px 0 0;font-size:14px;font-weight:${active?'bold':'normal'};">${labels[t]}</button>`;
            }).join('')}
        </div>

        <div id="pd-content">${pdLoading()}</div>
    </div>
    `;
}

function pdLoading() {
    return '<div style="padding:40px;text-align:center;color:#64748b;">⏳ 加载中...</div>';
}

function pdSwitchTab(tab) {
    window._pdTab = tab;
    document.getElementById('content').innerHTML = renderProductionDocs();
    pdLoadCurrentTab();
}

function pdRefresh() {
    pdLoadCurrentTab();
}

async function pdLoadCurrentTab() {
    const el = document.getElementById('pd-content');
    if (!el) return;
    el.innerHTML = pdLoading();
    try {
        if (window._pdTab === 'work_orders') {
            await pdRenderWorkOrders();
        } else if (window._pdTab === 'picks') {
            await pdRenderPicks();
        } else if (window._pdTab === 'inbounds') {
            await pdRenderInbounds();
        } else if (window._pdTab === 'material_returns') {
            await pdRenderSimpleList('/material-returns', '退料单', 'pick_no');
        } else if (window._pdTab === 'replenishes') {
            await pdRenderSimpleList('/replenishes', '补料单', 'work_order_no');
        } else if (window._pdTab === 'return_inbounds') {
            await pdRenderSimpleList('/return-inbounds', '退库单', 'inbound_no');
        }
    } catch(e) {
        el.innerHTML = `<div style="padding:20px;color:#ef4444;">加载失败：${e.message}</div>`;
    }
}

// ========== 工单列表 ==========
async function pdRenderWorkOrders() {
    const el = document.getElementById('pd-content');
    const res = await pdApi('/work-orders');
    const list = res.data || [];
    el.innerHTML = `
        <div style="margin-bottom:12px;">
            <button class="btn btn-primary" onclick="pdShowWOForm()">➕ 新建工单</button>
        </div>
        <div style="background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.1);">
            <table style="width:100%;border-collapse:collapse;">
                <thead>
                    <tr style="background:#f1f5f9;">
                        <th style="padding:10px;text-align:left;font-size:13px;">工单号</th>
                        <th style="padding:10px;text-align:left;font-size:13px;">产品</th>
                        <th style="padding:10px;text-align:right;font-size:13px;">计划产量</th>
                        <th style="padding:10px;text-align:right;font-size:13px;">已完工</th>
                        <th style="padding:10px;text-align:right;font-size:13px;">已领料</th>
                        <th style="padding:10px;text-align:center;font-size:13px;">状态</th>
                        <th style="padding:10px;text-align:center;font-size:13px;">操作</th>
                    </tr>
                </thead>
                <tbody>
                    ${list.length === 0 ? '<tr><td colspan="7" style="padding:30px;text-align:center;color:#64748b;">暂无工单，点击"新建工单"开始</td></tr>' :
                    list.map(wo => `
                        <tr style="border-top:1px solid #e2e8f0;">
                            <td style="padding:10px;font-size:13px;"><a href="#" onclick="pdShowWODetail(${wo.id});return false;" style="color:#3b82f6;">${wo.doc_no}</a></td>
                            <td style="padding:10px;font-size:13px;">${wo.product_name || '-'}</td>
                            <td style="padding:10px;text-align:right;font-size:13px;">${wo.planned_qty}</td>
                            <td style="padding:10px;text-align:right;font-size:13px;color:${wo.completed_qty >= wo.planned_qty ? '#10b981' : '#f59e0b'}">${wo.completed_qty}</td>
                            <td style="padding:10px;text-align:right;font-size:13px;">${wo.issued_qty}</td>
                            <td style="padding:10px;text-align:center;">${pdStatusBadge(wo.status)}</td>
                            <td style="padding:10px;text-align:center;font-size:12px;">
                                <button class="btn btn-secondary" style="padding:3px 8px;font-size:11px;" onclick="pdShowWODetail(${wo.id})">详情</button>
                                ${(wo.status === '草稿' || wo.status === '已确认') ? `<button class="btn btn-primary" style="padding:3px 8px;font-size:11px;" onclick="pdReleaseWO(${wo.id})">下达</button>` : ''}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

// ========== 新建工单表单 ==========
function pdShowWOForm() {
    const el = document.getElementById('pd-content');
    el.innerHTML = `
        <div style="background:#fff;border-radius:8px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.1);">
            <h3 style="margin-top:0;">➕ 新建生产工单</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
                <div>
                    <label style="font-size:13px;color:#475569;">产品名称</label>
                    <input id="wo-product-name" type="text" style="width:100%;padding:8px;border:1px solid #cbd5e1;border-radius:4px;margin-top:4px;" placeholder="如：智能装配机A1">
                </div>
                <div>
                    <label style="font-size:13px;color:#475569;">产品编码</label>
                    <input id="wo-product-code" type="text" style="width:100%;padding:8px;border:1px solid #cbd5e1;border-radius:4px;margin-top:4px;" placeholder="如：P-A1">
                </div>
                <div>
                    <label style="font-size:13px;color:#475569;">计划产量</label>
                    <input id="wo-planned-qty" type="number" value="100" style="width:100%;padding:8px;border:1px solid #cbd5e1;border-radius:4px;margin-top:4px;">
                </div>
                <div>
                    <label style="font-size:13px;color:#475569;">车间</label>
                    <input id="wo-workshop" type="text" style="width:100%;padding:8px;border:1px solid #cbd5e1;border-radius:4px;margin-top:4px;" placeholder="如：一号车间">
                </div>
                <div>
                    <label style="font-size:13px;color:#475569;">计划开始</label>
                    <input id="wo-start" type="date" style="width:100%;padding:8px;border:1px solid #cbd5e1;border-radius:4px;margin-top:4px;">
                </div>
                <div>
                    <label style="font-size:13px;color:#475569;">计划结束</label>
                    <input id="wo-end" type="date" style="width:100%;padding:8px;border:1px solid #cbd5e1;border-radius:4px;margin-top:4px;">
                </div>
                <div>
                    <label style="font-size:13px;color:#475569;">优先级</label>
                    <select id="wo-priority" style="width:100%;padding:8px;border:1px solid #cbd5e1;border-radius:4px;margin-top:4px;">
                        <option value="normal">普通</option>
                        <option value="high">高</option>
                        <option value="urgent">紧急</option>
                    </select>
                </div>
                <div style="grid-column:1/3;">
                    <label style="font-size:13px;color:#475569;">备注</label>
                    <textarea id="wo-remark" style="width:100%;padding:8px;border:1px solid #cbd5e1;border-radius:4px;margin-top:4px;rows="2"></textarea>
                </div>
            </div>
            <div style="margin-top:20px;display:flex;gap:8px;">
                <button class="btn btn-primary" onclick="pdSubmitWO()">✅ 创建工单</button>
                <button class="btn btn-secondary" onclick="pdRenderWorkOrders()">取消</button>
            </div>
        </div>
    `;
    // 设置默认日期
    const today = new Date().toISOString().slice(0,10);
    const nextWeek = new Date(Date.now() + 7*86400000).toISOString().slice(0,10);
    document.getElementById('wo-start').value = today;
    document.getElementById('wo-end').value = nextWeek;
}

async function pdSubmitWO() {
    const data = {
        product_name: document.getElementById('wo-product-name').value,
        product_code: document.getElementById('wo-product-code').value,
        planned_qty: parseFloat(document.getElementById('wo-planned-qty').value) || 0,
        workshop: document.getElementById('wo-workshop').value,
        planned_start: document.getElementById('wo-start').value,
        planned_end: document.getElementById('wo-end').value,
        priority: document.getElementById('wo-priority').value,
        remark: document.getElementById('wo-remark').value,
        created_by: 'admin'
    };
    const res = await pdApi('/work-orders', 'POST', data);
    if (res.code === '000000' || res.success) {
        showToast(res.message || '创建成功', 'success');
        pdRenderWorkOrders();
    } else {
        showToast('创建失败：' + (res.message || '未知错误'), 'error');
    }
}

// ========== 工单详情 ==========
async function pdShowWODetail(id) {
    const el = document.getElementById('pd-content');
    el.innerHTML = pdLoading();
    const res = await pdApi('/work-orders/' + id);
    const wo = res.data;
    if (!wo) { el.innerHTML = '<div>工单不存在</div>'; return; }

    // 加载追溯数据
    const traceRes = await pdApi('/trace/work_order/' + id);
    const trace = traceRes.data;

    el.innerHTML = `
        <div style="background:#fff;border-radius:8px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.1);margin-bottom:16px;">
            <div style="display:flex;justify-content:space-between;align-items:start;">
                <div>
                    <h3 style="margin:0 0 8px 0;">${wo.doc_no} ${pdStatusBadge(wo.status)}</h3>
                    <p style="margin:4px 0;color:#64748b;font-size:14px;">${wo.product_name || '-'} | 车间：${wo.workshop || '-'} | 优先级：${wo.priority}</p>
                </div>
                <div style="display:flex;gap:6px;flex-wrap:wrap;">
                    <button class="btn btn-secondary" onclick="pdShowWOGraph('work_order',${wo.id})">🔗 关系图</button>
                    ${(wo.status === '草稿' || wo.status === '已确认') ? `<button class="btn btn-primary" onclick="pdReleaseWO(${wo.id})">📢 下达工单</button>` : ''}
                    ${(wo.status === '已下达' || wo.status === '生产中') ? `<button class="btn btn-primary" onclick="pdPushPick(${wo.id})">📦 下推领料</button><button class="btn btn-primary" onclick="pdPushInbound(${wo.id})">📥 下推入库</button>` : ''}
                    <button class="btn btn-secondary" onclick="pdRenderWorkOrders()">← 返回列表</button>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:16px;padding:16px;background:#f8fafc;border-radius:6px;">
                <div><div style="font-size:12px;color:#64748b;">计划产量</div><div style="font-size:20px;font-weight:bold;">${wo.planned_qty}</div></div>
                <div><div style="font-size:12px;color:#64748b;">已完工</div><div style="font-size:20px;font-weight:bold;color:#10b981;">${wo.completed_qty}</div></div>
                <div><div style="font-size:12px;color:#64748b;">已领料</div><div style="font-size:20px;font-weight:bold;color:#f59e0b;">${wo.issued_qty}</div></div>
                <div><div style="font-size:12px;color:#64748b;">完工进度</div><div style="font-size:20px;font-weight:bold;color:#3b82f6;">${wo.planned_qty > 0 ? Math.round(wo.completed_qty / wo.planned_qty * 100) : 0}%</div></div>
            </div>
        </div>

        <!-- 关联单据 -->
        <div style="background:#fff;border-radius:8px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.1);margin-bottom:16px;">
            <h4 style="margin-top:0;">🔗 关联单据</h4>
            <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;">
                ${wo.component_list ? `<div style="padding:12px;background:#ede9fe;border-radius:6px;border-left:3px solid #8b5cf6;"><div style="font-size:12px;color:#64748b;">组件清单</div><div style="font-weight:bold;">${wo.component_list.doc_no}</div><div style="font-size:12px;">${pdStatusBadge(wo.component_list.status)}</div></div>` : ''}
                ${wo.process_plan ? `<div style="padding:12px;background:#fef3c7;border-radius:6px;border-left:3px solid #f59e0b;"><div style="font-size:12px;color:#64748b;">工序计划</div><div style="font-weight:bold;">${wo.process_plan.doc_no}</div><div style="font-size:12px;">${pdStatusBadge(wo.process_plan.status)}</div></div>` : ''}
                ${(wo.picks || []).map(p => `<div style="padding:12px;background:#dbeafe;border-radius:6px;border-left:3px solid #3b82f6;cursor:pointer;" onclick="pdShowPickDetail(${p.id})"><div style="font-size:12px;color:#64748b;">领料单</div><div style="font-weight:bold;">${p.doc_no}</div><div style="font-size:12px;">${pdStatusBadge(p.status)}</div></div>`).join('')}
                ${(wo.inbounds || []).map(i => `<div style="padding:12px;background:#dcfce7;border-radius:6px;border-left:3px solid #10b981;cursor:pointer;" onclick="pdShowInboundDetail(${i.id})"><div style="font-size:12px;color:#64748b;">完工入库</div><div style="font-weight:bold;">${i.doc_no}</div><div style="font-size:12px;">${pdStatusBadge(i.status)}</div></div>`).join('')}
                ${(!wo.component_list && !wo.process_plan && (!wo.picks || wo.picks.length === 0) && (!wo.inbounds || wo.inbounds.length === 0)) ? '<div style="color:#94a3b8;padding:12px;">暂无关联单据</div>' : ''}
            </div>
        </div>

        <!-- 追溯结果 -->
        <div style="background:#fff;border-radius:8px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.1);">
            <h4 style="margin-top:0;">🔍 单据追溯</h4>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
                <div>
                    <h5 style="margin:0 0 8px 0;color:#475569;">⬆️ 上游来源</h5>
                    ${trace.upstream.length === 0 ? '<div style="color:#94a3b8;font-size:13px;">无上游单据（源头单据）</div>' :
                    trace.upstream.map(u => `<div style="padding:8px;background:#f8fafc;border-radius:4px;margin-bottom:4px;font-size:13px;">${pdDocTypeLabel(u.doc_type)}：<strong>${u.doc_no}</strong> <span style="color:#64748b;font-size:11px;">(${u.link_type === 'auto' ? '自动生成' : '下推'})</span></div>`).join('')}
                </div>
                <div>
                    <h5 style="margin:0 0 8px 0;color:#475569;">⬇️ 下游衍生</h5>
                    ${trace.downstream.length === 0 ? '<div style="color:#94a3b8;font-size:13px;">无下游单据</div>' :
                    trace.downstream.map(d => `<div style="padding:8px;background:#f8fafc;border-radius:4px;margin-bottom:4px;font-size:13px;">${pdDocTypeLabel(d.doc_type)}：<strong>${d.doc_no}</strong> <span style="color:#64748b;font-size:11px;">(${d.link_type === 'auto' ? '自动生成' : '下推'})</span></div>`).join('')}
                </div>
            </div>
        </div>
    `;
}

// ========== 工单下达 ==========
async function pdReleaseWO(id) {
    if (!confirm('下达工单将自动生成组件清单和工序计划，确认？')) return;
    const res = await pdApi('/work-orders/' + id + '/release', 'POST');
    if (res.code === '000000' || res.success) {
        showToast(res.message, 'success');
        pdShowWODetail(id);
    } else {
        showToast('下达失败：' + (res.message || '未知错误'), 'error');
    }
}

// ========== 下推领料 ==========
async function pdPushPick(woId) {
    const res = await pdApi('/work-orders/' + woId + '/push-pick', 'POST', { warehouse: '原材料仓' });
    if (res.code === '000000' || res.success) {
        showToast(res.message, 'success');
        pdShowPickDetail(res.data.id);
    } else {
        showToast('下推失败：' + (res.message || '未知错误'), 'error');
    }
}

// ========== 下推入库 ==========
async function pdPushInbound(woId) {
    const res = await pdApi('/work-orders/' + woId + '/push-inbound', 'POST', { warehouse: '成品仓' });
    if (res.code === '000000' || res.success) {
        showToast(res.message, 'success');
        pdShowInboundDetail(res.data.id);
    } else {
        showToast('下推失败：' + (res.message || '未知错误'), 'error');
    }
}

// ========== 领料单 ==========
async function pdRenderPicks() {
    const el = document.getElementById('pd-content');
    const res = await pdApi('/picks');
    const list = res.data || [];
    el.innerHTML = `
        <div style="background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.1);">
            <table style="width:100%;border-collapse:collapse;">
                <thead><tr style="background:#f1f5f9;">
                    <th style="padding:10px;text-align:left;font-size:13px;">领料单号</th>
                    <th style="padding:10px;text-align:left;font-size:13px;">来源工单</th>
                    <th style="padding:10px;text-align:left;font-size:13px;">领料日期</th>
                    <th style="padding:10px;text-align:center;font-size:13px;">状态</th>
                    <th style="padding:10px;text-align:center;font-size:13px;">操作</th>
                </tr></thead>
                <tbody>
                    ${list.length === 0 ? '<tr><td colspan="5" style="padding:30px;text-align:center;color:#64748b;">暂无领料单</td></tr>' :
                    list.map(p => `
                        <tr style="border-top:1px solid #e2e8f0;">
                            <td style="padding:10px;font-size:13px;"><a href="#" onclick="pdShowPickDetail(${p.id});return false;" style="color:#3b82f6;">${p.doc_no}</a></td>
                            <td style="padding:10px;font-size:13px;">${p.work_order_no || '-'}</td>
                            <td style="padding:10px;font-size:13px;">${p.pick_date || '-'}</td>
                            <td style="padding:10px;text-align:center;">${pdStatusBadge(p.status)}</td>
                            <td style="padding:10px;text-align:center;font-size:12px;">
                                <button class="btn btn-secondary" style="padding:3px 8px;font-size:11px;" onclick="pdShowPickDetail(${p.id})">详情</button>
                                ${p.status === '草稿' ? `<button class="btn btn-primary" style="padding:3px 8px;font-size:11px;" onclick="pdConfirmPick(${p.id})">确认</button>` : ''}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

async function pdShowPickDetail(id) {
    const el = document.getElementById('pd-content');
    el.innerHTML = pdLoading();
    const res = await pdApi('/picks/' + id);
    const p = res.data;
    el.innerHTML = `
        <div style="background:#fff;border-radius:8px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.1);">
            <div style="display:flex;justify-content:space-between;align-items:start;">
                <div>
                    <h3 style="margin:0 0 8px 0;">${p.doc_no} ${pdStatusBadge(p.status)}</h3>
                    <p style="margin:4px 0;color:#64748b;font-size:14px;">来源工单：${p.work_order_no || '-'} | 仓库：${p.warehouse || '-'}</p>
                </div>
                <div style="display:flex;gap:6px;">
                    <button class="btn btn-secondary" onclick="pdShowWOGraph('pick',${p.id})">🔗 关系图</button>
                    ${p.status === '草稿' ? `<button class="btn btn-primary" onclick="pdConfirmPick(${p.id})">✅ 确认领料</button>` : ''}
                    ${p.status === '已确认' ? `<button class="btn btn-primary" onclick="pdPushReturn(${p.id})">↩️ 下推退料</button>` : ''}
                    <button class="btn btn-secondary" onclick="pdRenderPicks()">← 返回列表</button>
                </div>
            </div>
            <h4 style="margin-top:20px;">📋 领料明细</h4>
            <table style="width:100%;border-collapse:collapse;margin-top:8px;">
                <thead><tr style="background:#f1f5f9;">
                    <th style="padding:8px;text-align:left;font-size:13px;">物料编码</th>
                    <th style="padding:8px;text-align:left;font-size:13px;">物料名称</th>
                    <th style="padding:8px;text-align:right;font-size:13px;">计划数量</th>
                    <th style="padding:8px;text-align:right;font-size:13px;">实领数量</th>
                    <th style="padding:8px;text-align:left;font-size:13px;">单位</th>
                </tr></thead>
                <tbody>
                    ${(p.items_json || []).map(it => `
                        <tr style="border-top:1px solid #e2e8f0;">
                            <td style="padding:8px;font-size:13px;">${it.material_code || '-'}</td>
                            <td style="padding:8px;font-size:13px;">${it.material_name || '-'}</td>
                            <td style="padding:8px;text-align:right;font-size:13px;">${it.planned_qty || 0}</td>
                            <td style="padding:8px;text-align:right;font-size:13px;font-weight:bold;color:#f59e0b;">${it.picked_qty || 0}</td>
                            <td style="padding:8px;font-size:13px;">${it.unit || '-'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

async function pdConfirmPick(id) {
    if (!confirm('确认领料后将回写数量到工单，确认？')) return;
    const res = await pdApi('/picks/' + id + '/confirm', 'POST');
    if (res.code === '000000' || res.success) {
        showToast(res.message, 'success');
        pdShowPickDetail(id);
    } else {
        showToast('确认失败：' + (res.message || '未知错误'), 'error');
    }
}

async function pdPushReturn(pickId) {
    const res = await pdApi('/picks/' + pickId + '/push-return', 'POST');
    if (res.code === '000000' || res.success) {
        showToast(res.message, 'success');
        pdSwitchTab('material_returns');
    } else {
        showToast('下推失败：' + (res.message || '未知错误'), 'error');
    }
}

// ========== 完工入库 ==========
async function pdRenderInbounds() {
    const el = document.getElementById('pd-content');
    const res = await pdApi('/inbounds');
    const list = res.data || [];
    el.innerHTML = `
        <div style="background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.1);">
            <table style="width:100%;border-collapse:collapse;">
                <thead><tr style="background:#f1f5f9;">
                    <th style="padding:10px;text-align:left;font-size:13px;">入库单号</th>
                    <th style="padding:10px;text-align:left;font-size:13px;">来源工单</th>
                    <th style="padding:10px;text-align:left;font-size:13px;">产品</th>
                    <th style="padding:10px;text-align:right;font-size:13px;">入库数量</th>
                    <th style="padding:10px;text-align:right;font-size:13px;">合格/不良</th>
                    <th style="padding:10px;text-align:center;font-size:13px;">状态</th>
                    <th style="padding:10px;text-align:center;font-size:13px;">操作</th>
                </tr></thead>
                <tbody>
                    ${list.length === 0 ? '<tr><td colspan="7" style="padding:30px;text-align:center;color:#64748b;">暂无入库单</td></tr>' :
                    list.map(i => `
                        <tr style="border-top:1px solid #e2e8f0;">
                            <td style="padding:10px;font-size:13px;"><a href="#" onclick="pdShowInboundDetail(${i.id});return false;" style="color:#3b82f6;">${i.doc_no}</a></td>
                            <td style="padding:10px;font-size:13px;">${i.work_order_no || '-'}</td>
                            <td style="padding:10px;font-size:13px;">${i.product_name || '-'}</td>
                            <td style="padding:10px;text-align:right;font-size:13px;font-weight:bold;">${i.qty}</td>
                            <td style="padding:10px;text-align:right;font-size:13px;"><span style="color:#10b981;">${i.qualified_qty}</span> / <span style="color:#ef4444;">${i.defective_qty}</span></td>
                            <td style="padding:10px;text-align:center;">${pdStatusBadge(i.status)}</td>
                            <td style="padding:10px;text-align:center;font-size:12px;">
                                <button class="btn btn-secondary" style="padding:3px 8px;font-size:11px;" onclick="pdShowInboundDetail(${i.id})">详情</button>
                                ${i.status === '草稿' ? `<button class="btn btn-primary" style="padding:3px 8px;font-size:11px;" onclick="pdConfirmInbound(${i.id})">确认</button>` : ''}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

async function pdShowInboundDetail(id) {
    const el = document.getElementById('pd-content');
    el.innerHTML = pdLoading();
    const res = await pdApi('/inbounds/' + id);
    const i = res.data;
    el.innerHTML = `
        <div style="background:#fff;border-radius:8px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.1);">
            <div style="display:flex;justify-content:space-between;align-items:start;">
                <div>
                    <h3 style="margin:0 0 8px 0;">${i.doc_no} ${pdStatusBadge(i.status)}</h3>
                    <p style="margin:4px 0;color:#64748b;font-size:14px;">来源工单：${i.work_order_no || '-'} | 产品：${i.product_name || '-'} | 仓库：${i.warehouse || '-'}</p>
                </div>
                <div style="display:flex;gap:6px;">
                    <button class="btn btn-secondary" onclick="pdShowWOGraph('inbound',${i.id})">🔗 关系图</button>
                    ${i.status === '草稿' ? `<button class="btn btn-primary" onclick="pdConfirmInbound(${i.id})">✅ 确认入库</button>` : ''}
                    ${i.status === '已确认' ? `<button class="btn btn-primary" onclick="pdPushReturnInbound(${i.id})">↩️ 下推退库</button>` : ''}
                    <button class="btn btn-secondary" onclick="pdRenderInbounds()">← 返回列表</button>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:16px;padding:16px;background:#f8fafc;border-radius:6px;">
                <div><div style="font-size:12px;color:#64748b;">入库数量</div><div style="font-size:24px;font-weight:bold;">${i.qty}</div></div>
                <div><div style="font-size:12px;color:#64748b;">合格数量</div><div style="font-size:24px;font-weight:bold;color:#10b981;">${i.qualified_qty}</div></div>
                <div><div style="font-size:12px;color:#64748b;">不良数量</div><div style="font-size:24px;font-weight:bold;color:#ef4444;">${i.defective_qty}</div></div>
            </div>
        </div>
    `;
}

async function pdConfirmInbound(id) {
    if (!confirm('确认入库后将回写完工数量到工单，确认？')) return;
    const res = await pdApi('/inbounds/' + id + '/confirm', 'POST');
    if (res.code === '000000' || res.success) {
        showToast(res.message, 'success');
        pdShowInboundDetail(id);
    } else {
        showToast('确认失败：' + (res.message || '未知错误'), 'error');
    }
}

async function pdPushReturnInbound(inboundId) {
    const res = await pdApi('/inbounds/' + inboundId + '/push-return-inbound', 'POST');
    if (res.code === '000000' || res.success) {
        showToast(res.message, 'success');
        pdSwitchTab('return_inbounds');
    } else {
        showToast('下推失败：' + (res.message || '未知错误'), 'error');
    }
}

// ========== 简单列表（退料/补料/退库） ==========
async function pdRenderSimpleList(url, title, sourceField) {
    const el = document.getElementById('pd-content');
    const res = await pdApi(url);
    const list = res.data || [];
    el.innerHTML = `
        <div style="background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.1);">
            <table style="width:100%;border-collapse:collapse;">
                <thead><tr style="background:#f1f5f9;">
                    <th style="padding:10px;text-align:left;font-size:13px;">单号</th>
                    <th style="padding:10px;text-align:left;font-size:13px;">来源</th>
                    <th style="padding:10px;text-align:center;font-size:13px;">状态</th>
                </tr></thead>
                <tbody>
                    ${list.length === 0 ? `<tr><td colspan="3" style="padding:30px;text-align:center;color:#64748b;">暂无${title}</td></tr>` :
                    list.map(d => `
                        <tr style="border-top:1px solid #e2e8f0;">
                            <td style="padding:10px;font-size:13px;"><strong>${d.doc_no}</strong></td>
                            <td style="padding:10px;font-size:13px;">${d[sourceField] || d.work_order_no || '-'}</td>
                            <td style="padding:10px;text-align:center;">${pdStatusBadge(d.status)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

// ========== SVG关系图 ==========
async function pdShowWOGraph(docType, docId) {
    const el = document.getElementById('pd-content');
    el.innerHTML = pdLoading();
    const res = await pdApi('/graph/' + docType + '/' + docId);
    const { nodes, edges } = res.data;

    // 布局：上游在左，中心在中，下游在右
    const centerNode = nodes.find(n => n.direction === 'center');
    const upstreamNodes = nodes.filter(n => n.direction === 'up');
    const downstreamNodes = nodes.filter(n => n.direction === 'down');

    const allNodes = [...upstreamNodes, centerNode, ...downstreamNodes].filter(Boolean);
    const nodeW = 160, nodeH = 60, gapX = 80, gapY = 20;
    const svgW = 1600;
    const svgH = Math.max(400, allNodes.length * (nodeH + gapY) + 100);

    // 计算位置
    let yOffset = 50;
    const positions = {};
    upstreamNodes.forEach(n => { positions[n.id] = { x: 50, y: yOffset }; yOffset += nodeH + gapY; });
    const centerY = Math.max(50, (svgH - nodeH) / 2);
    if (centerNode) positions[centerNode.id] = { x: 50 + nodeW + gapX, y: centerY };
    yOffset = 50;
    downstreamNodes.forEach(n => { positions[n.id] = { x: 50 + (nodeW + gapX) * 2, y: yOffset }; yOffset += nodeH + gapY; });

    // 颜色
    const typeColors = {
        work_order: '#3b82f6', component_list: '#8b5cf6', process_plan: '#f59e0b',
        pick: '#06b6d4', material_return: '#ef4444', replenish: '#f97316',
        inbound: '#10b981', return_inbound: '#ec4899'
    };

    let svg = `<svg width="100%" height="${svgH}" style="background:#f8fafc;border-radius:8px;">`;

    // 连线（贝塞尔曲线）
    edges.forEach(e => {
        const s = positions[e.source], t = positions[e.target];
        if (!s || !t) return;
        const x1 = s.x + nodeW, y1 = s.y + nodeH / 2;
        const x2 = t.x, y2 = t.y + nodeH / 2;
        const mx = (x1 + x2) / 2;
        const color = e.link_type === 'auto' ? '#8b5cf6' : '#3b82f6';
        const dash = e.link_type === 'auto' ? '5,5' : '';
        svg += `<path d="M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}" stroke="${color}" stroke-width="2" fill="none" stroke-dasharray="${dash}"/>`;
        // 箭头
        svg += `<polygon points="${x2},${y2} ${x2-10},${y2-5} ${x2-10},${y2+5}" fill="${color}"/>`;
    });

    // 节点
    allNodes.forEach(n => {
        const p = positions[n.id];
        const color = typeColors[n.type] || '#64748b';
        const isCenter = n.direction === 'center';
        svg += `<g>
            <rect x="${p.x}" y="${p.y}" width="${nodeW}" height="${nodeH}" rx="8" fill="#fff" stroke="${color}" stroke-width="${isCenter ? 3 : 2}"/>
            <text x="${p.x + nodeW/2}" y="${p.y + 22}" text-anchor="middle" font-size="12" font-weight="bold" fill="${color}">${pdDocTypeLabel(n.type)}</text>
            <text x="${p.x + nodeW/2}" y="${p.y + 42}" text-anchor="middle" font-size="11" fill="#475569">${n.doc_no}</text>
        </g>`;
    });

    svg += `</svg>`;

    // 返回按钮根据doc_type动态调用
    const backFn = docType === 'work_order' ? `pdShowWODetail(${docId})`
                 : docType === 'pick' ? `pdShowPickDetail(${docId})`
                 : docType === 'inbound' ? `pdShowInboundDetail(${docId})`
                 : `pdLoadCurrentTab()`;
    el.innerHTML = `
        <div style="background:#fff;border-radius:8px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.1);">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                <h3 style="margin:0;">🔗 单据关系图</h3>
                <button class="btn btn-secondary" onclick="${backFn}">← 返回详情</button>
            </div>
            <div style="display:flex;gap:16px;margin-bottom:12px;font-size:13px;color:#64748b;">
                <span><span style="display:inline-block;width:20px;height:2px;background:#3b82f6;vertical-align:middle;"></span> 下推生成</span>
                <span><span style="display:inline-block;width:20px;height:2px;background:#8b5cf6;vertical-align:middle;border-top:2px dashed #8b5cf6;"></span> 自动生成</span>
            </div>
            ${nodes.length === 1 ? '<div style="padding:40px;text-align:center;color:#94a3b8;">该单据暂无上下游关联</div>' : svg}
        </div>
    `;
}

// ========== 注册到全局 ==========
window.renderProductionDocs = renderProductionDocs;
window.pdSwitchTab = pdSwitchTab;
window.pdRefresh = pdRefresh;
window.pdShowWOForm = pdShowWOForm;
window.pdSubmitWO = pdSubmitWO;
window.pdShowWODetail = pdShowWODetail;
window.pdReleaseWO = pdReleaseWO;
window.pdPushPick = pdPushPick;
window.pdPushInbound = pdPushInbound;
window.pdRenderWorkOrders = pdRenderWorkOrders;
window.pdRenderPicks = pdRenderPicks;
window.pdRenderInbounds = pdRenderInbounds;
window.pdShowPickDetail = pdShowPickDetail;
window.pdConfirmPick = pdConfirmPick;
window.pdPushReturn = pdPushReturn;
window.pdShowInboundDetail = pdShowInboundDetail;
window.pdConfirmInbound = pdConfirmInbound;
window.pdPushReturnInbound = pdPushReturnInbound;
window.pdShowWOGraph = pdShowWOGraph;
