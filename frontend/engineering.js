// =============== 工程导向型ERP 7大核心模块前端 ===============
let engCurrentTab = 'project';

function renderEngineering() {
    return `
        <div class="content-header">
            <h2>🏗️ 工程管理</h2>
        </div>
        <div id="eng-content"></div>
    `;
}

function renderEngTab(tab, btnEl, subView) {
    engCurrentTab = tab;
    document.querySelectorAll('.finance-tab').forEach(b => b.classList.remove('active'));
    if (btnEl) btnEl.classList.add('active');
    const content = document.getElementById('eng-content') || document.getElementById('content');
    if (!content) return;
    switch(tab) {
        case 'project':
            content.innerHTML = renderProjectMgmt();
            if (subView === 'create') { setTimeout(() => showProjectForm(), 300); }
            else if (subView === 'wbs') { loadProjectBoard(); setTimeout(() => {
                // 默认展开第一个项目的WBS结构
                fetch(`${API}/projects/board`).then(r=>r.json()).then(d=>{
                    if (d.total > 0) showProjectDetail(d.groups[Object.keys(d.groups)[0]][0].id);
                });
            }, 300); }
            else { loadProjectBoard(); }
            break;
        case 'bom':
            content.innerHTML = renderBomMgmt();
            loadBomList();
            if (subView === 'compare') { setTimeout(() => showBomCompare(), 300); }
            else if (subView === 'cost') { setTimeout(() => { const id = prompt('请输入BOM ID进行成本卷积:','1'); if(id) bomCostRollup(parseInt(id)); }, 300); }
            break;
        case 'eco':
            content.innerHTML = renderEcoMgmt();
            loadEcoList();
            if (subView === 'apply') { setTimeout(() => showEcoForm(), 300); }
            break;
        case 'schedule':
            content.innerHTML = renderScheduleMgmt();
            loadScheduleAll();
            break;
        case 'cost':
            content.innerHTML = renderCostMgmt();
            loadCostMgmt();
            break;
        case 'revenue':
            content.innerHTML = renderRevenueMgmt();
            loadRevenueMgmt();
            break;
        case 'equipment':
            content.innerHTML = renderEquipmentQuality();
            loadEquipmentQuality();
            break;
        // 直接跳转现有模块的子菜单
        case 'purchase':
            loadModule('purchase'); break;
        case 'sales':
            loadModule('sales'); break;
        case 'inventory':
            loadModule('inventory_v2'); break;
        case 'finance':
            loadModule('finance'); break;
        case 'system':
            loadModule('dashboard'); break;
    }
}

const API = '/api/v1/eng-modules';
const ENG_API = '/api/v1/eng';

// 货币符号映射
function currencySymbol(code) {
    return {CNY:'¥', USD:'$', EUR:'€', HKD:'HK$'}[code] || '¥';
}

// ==================== 模块1：项目管理 ====================
// 获取当前业务模式 A/B
function getBizMode() {
    return localStorage.getItem('erp_business_mode') || 'B';
}

function renderProjectMgmt() {
    return `
        <div style="margin-bottom:16px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
            <button class="btn btn-primary" onclick="showProjectForm()">➕ 新建项目</button>
            <button class="btn btn-secondary" onclick="loadProjectBoard()">🔄 刷新</button>
            <label class="btn btn-secondary" style="cursor:pointer;margin:0;">📥 导入合同Excel<input type="file" accept=".xlsx,.xls" onchange="importProjectsExcel(this)" style="display:none;"></label>
            <button class="btn btn-secondary" onclick="window.open(ENG_API+'/wbs-projects/export','_blank')">📤 导出合同</button>
            <button class="btn btn-secondary" onclick="window.open(ENG_API+'/wbs-projects/import-template','_blank')">📄 合同模板</button>
            <button class="btn" style="background:#0ea5e9;color:#fff;" onclick="loadProjectCostReport()">📊 项目成本明细表</button>
        </div>
        <div id="project-cost-report"></div>
        <div id="project-board"></div>
        <div id="project-detail" style="margin-top:20px;"></div>
    `;
}

// ==================== 项目成本明细表（报表层：成本要素 + 预算vs实际 + 超支预警）====================
async function loadProjectCostReport() {
    const board = document.getElementById('project-board');
    const detail = document.getElementById('project-detail');
    const rep = document.getElementById('project-cost-report');
    if (!rep) return;
    if (board) board.style.display = 'none';
    if (detail) detail.innerHTML = '';
    rep.style.display = 'block';
    rep.innerHTML = '<div class="empty">报表加载中...</div>';
    try {
        const r = await fetch(`${ENG_API}/wbs-projects/cost-report`);
        const d = await r.json();
        if (!d.success) throw new Error(d.message || '加载失败');
        const data = d.data || {};
        const rows = data.rows || [];
        const t = data.total || {};
        const warnStyle = {
            OVER:   'background:#fee2e2;color:#dc2626;border:1px solid #fca5a5;',
            NEAR:   'background:#fef3c7;color:#d97706;border:1px solid #fcd34d;',
            OK:     'background:#dcfce7;color:#16a34a;border:1px solid #86efac;',
            NOBUDGET:'background:#f1f5f9;color:#64748b;border:1px solid #cbd5e1;',
        };
        const money = v => '¥' + (v||0).toLocaleString(undefined,{maximumFractionDigits:2});
        let html = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <h3 style="margin:0;font-size:17px;">📊 项目成本明细表（按成本要素 · 预算执行 · 超支预警）</h3>
            <button class="btn btn-secondary" onclick="closeProjectCostReport()">← 返回项目看板</button>
        </div>`;
        // 汇总预警条
        if (data.over_budget_count > 0) {
            html += `<div style="margin-bottom:12px;padding:10px 14px;background:#fee2e2;border:1px solid #fca5a5;border-radius:8px;color:#dc2626;font-weight:600;">🚨 有 ${data.over_budget_count} 个项目已超预算！${data.near_budget_count>0 ? '另有 '+data.near_budget_count+' 个项目接近预算（≥80%）。' : ''}请重点核查成本。</div>`;
        } else if (data.near_budget_count > 0) {
            html += `<div style="margin-bottom:12px;padding:10px 14px;background:#fef3c7;border:1px solid #fcd34d;border-radius:8px;color:#d97706;font-weight:600;">⚠️ 有 ${data.near_budget_count} 个项目成本已达预算80%以上，请注意控制。</div>`;
        }
        html += `<div style="overflow-x:auto;"><table class="data-table" style="font-size:13px;min-width:1100px;">
            <thead><tr style="background:#f1f5f9;">
                <th style="text-align:left;">项目</th>
                <th>合同收入</th><th>预算成本</th>
                <th>直接材料</th><th>直接人工</th><th>外协费用</th><th>制造费用</th>
                <th style="color:#dc2626;">实际成本</th>
                <th>预算执行率</th><th>剩余预算</th>
                <th>净利润</th><th>毛利率</th><th>预警</th>
            </tr></thead><tbody>`;
        rows.forEach(r => {
            const ws = warnStyle[r.warn] || warnStyle.NOBUDGET;
            html += `<tr style="cursor:pointer;" onclick="closeProjectCostReport();showProjectDetail(${r.project_id})">
                <td style="text-align:left;white-space:nowrap;"><b>${r.project_name}</b><br><span style="color:#94a3b8;font-size:11px;">${r.project_no}</span></td>
                <td>${money(r.contract_amount)}</td>
                <td>${money(r.budget_cost)}</td>
                <td>${money(r.material_cost)}</td>
                <td>${money(r.labor_cost)}</td>
                <td>${money(r.outsource_cost)}</td>
                <td>${money(r.overhead_cost)}</td>
                <td style="color:#dc2626;font-weight:700;">${money(r.actual_cost)}</td>
                <td style="font-weight:600;color:${r.usage_pct>=100?'#dc2626':r.usage_pct>=80?'#d97706':'#16a34a'};">${r.budget_cost>0?r.usage_pct+'%':'—'}</td>
                <td style="color:${r.budget_remain<0?'#dc2626':'#64748b'};">${r.budget_cost>0?money(r.budget_remain):'—'}</td>
                <td style="color:${r.net_profit>=0?'#16a34a':'#dc2626'};font-weight:600;">${money(r.net_profit)}</td>
                <td style="font-weight:600;color:${r.gross_margin>=30?'#16a34a':r.gross_margin>=10?'#d97706':'#dc2626'};">${r.gross_margin.toFixed(1)}%</td>
                <td><span style="padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600;white-space:nowrap;${ws}">${r.warn_cn}</span></td>
            </tr>`;
        });
        // 合计行
        html += `<tr style="background:#f8fafc;font-weight:700;border-top:2px solid #cbd5e1;">
            <td style="text-align:left;">合计（${data.project_count}个项目）</td>
            <td>${money(t.contract)}</td><td>${money(t.budget)}</td>
            <td>${money(t.material)}</td><td>${money(t.labor)}</td><td>${money(t.outsource)}</td><td>${money(t.overhead)}</td>
            <td style="color:#dc2626;">${money(t.actual)}</td>
            <td>—</td><td>—</td>
            <td style="color:${t.profit>=0?'#16a34a':'#dc2626'};">${money(t.profit)}</td>
            <td>${t.gross_margin.toFixed(1)}%</td><td>—</td>
        </tr>`;
        html += `</tbody></table></div>
        <div style="margin-top:8px;color:#94a3b8;font-size:12px;">说明：成本由财务凭证自动归集——直接材料=采购记账(1401)、制造费用=车间水电等(5101)按材料占比分摊；直接人工、外协费用随对应业务单据记账后自动计入（当前暂无则为0）。点击某行可查看项目详情。</div>`;
        rep.innerHTML = html;
    } catch (e) {
        rep.innerHTML = `<div class="empty">成本明细表加载失败：${e.message}</div>`;
    }
}

function closeProjectCostReport() {
    const rep = document.getElementById('project-cost-report');
    const board = document.getElementById('project-board');
    if (rep) rep.style.display = 'none';
    if (board) board.style.display = '';
}

async function loadProjectBoard() {
    const el = document.getElementById('project-board');
    if (!el) return;
    try {
        const r = await fetch(`${API}/projects/board`);
        const data = await r.json();
        if (!data.total) { el.innerHTML = '<div class="empty">暂无项目，点击「新建项目」开始</div>'; return; }
        let html = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px;">';
        const colorMap = {PLANNING:'#3498db', EXECUTING:'#f39c12', COMPLETED:'#27ae60', CLOSED:'#95a5a6'};
        for (const [status, projects] of Object.entries(data.groups)) {
            projects.forEach(p => {
                const color = colorMap[status] || '#95a5a6';
                const progressColor = p.progress_pct >= 80 ? '#27ae60' : p.progress_pct >= 50 ? '#f39c12' : '#e74c3c';
                const modeLabels = {MTS:'备货生产', MTO:'按单生产', ATO:'按单装配', ETO:'按单设计'};
                const _ic = p.incurred_cost||0, _bg = p.budget_cost||0;
                const _usage = _bg>0 ? _ic/_bg*100 : 0;
                const _budgetBadge = _bg>0 && _ic>_bg ? '<span style="background:#dc2626;color:#fff;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:700;">🚨超支</span>'
                    : (_bg>0 && _usage>=80 ? '<span style="background:#d97706;color:#fff;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:700;">⚠️近预算</span>' : '');
                html += `<div onclick="showProjectDetail(${p.id})" style="cursor:pointer;background:#fff;border-radius:12px;padding:16px;border-left:4px solid ${color};box-shadow:0 2px 8px rgba(0,0,0,0.08);transition:transform 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform=''">
                    <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:8px;">
                        <div>
                            <div style="font-size:12px;color:#95a5a6;">${p.project_no}</div>
                            <div style="font-size:16px;font-weight:600;color:#2c3e50;">${p.project_name}</div>
                        </div>
                        <div style="display:flex;gap:4px;align-items:center;flex-wrap:wrap;justify-content:flex-end;">
                            ${_budgetBadge}
                            <span style="background:#ede9fe;color:#6d28d9;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600;">${p.delivery_mode || 'MTO'}</span>
                            <span style="background:${color};color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;">${p.status_name}</span>
                        </div>
                    </div>
                    <div style="font-size:13px;color:#7f8c8d;margin-bottom:6px;">👤 ${p.customer_name} · 👨‍💼 ${p.manager || '-'}</div>
                    <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;">
                        <span>合同额: <b>${currencySymbol(p.currency)}${(p.contract_amount||0).toLocaleString()}</b></span>
                        <span>成本: <b style="color:#e74c3c;">¥${(p.incurred_cost||0).toLocaleString()}</b></span>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:8px;">
                        <span>净利润: <b style="color:${(p.net_profit||0)>=0?'#16a34a':'#dc2626'};">¥${(p.net_profit||0).toLocaleString()}</b></span>
                        <span>毛利率: <b style="color:${(p.gross_margin||0)>=30?'#16a34a':(p.gross_margin||0)>=10?'#d97706':'#dc2626'};">${(p.gross_margin||0).toFixed(1)}%</b></span>
                    </div>
                    <div style="background:#ecf0f1;border-radius:6px;height:8px;overflow:hidden;">
                        <div style="background:${progressColor};height:100%;width:${p.progress_pct}%;transition:width 0.3s;"></div>
                    </div>
                    <div style="text-align:right;font-size:12px;color:${progressColor};margin-top:4px;">${p.progress_pct}%</div>
                    ${status === 'PLANNING' ? `<div style="margin-top:10px;padding-top:10px;border-top:1px dashed #e5e7eb;text-align:right;">
                        <button onclick="event.stopPropagation();confirmProjectAndImportBom(${p.id},'${(p.project_no||'').replace(/'/g,"\\'")}','${(p.project_name||'').replace(/'/g,"\\'")}')" style="padding:5px 14px;background:linear-gradient(135deg,#10b981,#059669);color:#fff;border:none;border-radius:6px;font-size:12px;cursor:pointer;">✅ 确认项目</button>
                    </div>` : ''}
                </div>`;
            });
        }
        html += '</div>';
        el.innerHTML = html;
    } catch(e) { el.innerHTML = '<div class="error">加载项目看板失败</div>'; }
}

// ==================== 项目确认 → 导入零件分类BOM ====================
let _projBomProject = null;
let _projBomPreviewItems = [];
const _PROJ_TYPE_MAP = {MACHINABLE:'加工件', STANDARD:'标准件', PURCHASE:'外购件', OUTSOURCE:'外协件', ASSEMBLY:'装配件'};

async function confirmProjectAndImportBom(id, projectNo, projectName) {
    if (!confirm(`确认项目「${projectName}」？\n确认后将立即转入执行，并请您上传零件分类表导入BOM。`)) return;
    try {
        const r = await fetch(`${ENG_API}/wbs-projects/${id}`, {
            method: 'PUT', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({status: 'EXECUTING'})
        });
        if (!r.ok) { showToast('项目确认失败', 'error'); return; }
        showToast('项目已确认，请上传零件分类表');
        loadProjectBoard();
        showProjectBomImportDialog(id, projectNo, projectName);
    } catch(e) { showToast('项目确认失败', 'error'); }
}

function showProjectBomImportDialog(id, projectNo, projectName) {
    _projBomProject = {id, projectNo, projectName};
    _projBomPreviewItems = [];
    const old = document.getElementById('proj-bom-modal');
    if (old) old.remove();
    const modal = document.createElement('div');
    modal.id = 'proj-bom-modal';
    modal.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    modal.innerHTML = `
        <div style="background:#fff;border-radius:12px;width:820px;max-width:94vw;max-height:88vh;overflow-y:auto;padding:20px 22px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                <h3 style="margin:0;font-size:17px;color:#1f2937;">📤 导入项目零件分类表</h3>
                <button onclick="document.getElementById('proj-bom-modal').remove()" style="border:none;background:none;font-size:20px;color:#9ca3af;cursor:pointer;">×</button>
            </div>
            <div style="font-size:12px;color:#6b7280;margin-bottom:14px;">${projectNo} ${projectName} · 表头：物料归属 / 零件名称 / 代号 / 工件类型 / 数量 / 材质</div>
            <div id="proj-bom-upload-area" style="border:2px dashed #c7d2fe;background:#f5f7ff;border-radius:10px;padding:26px;text-align:center;">
                <div style="font-size:13px;color:#4b5563;margin-bottom:12px;">请上传本项目的零件分类 Excel 表格</div>
                <button onclick="window.open('${MRP_API}/bom/project-import-template','_blank')" style="padding:7px 16px;background:#6b7280;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;">📥 下载模板</button>
                <label style="padding:7px 16px;background:#10b981;color:#fff;border-radius:6px;cursor:pointer;font-size:13px;margin-left:8px;">📁 选择Excel
                    <input type="file" accept=".xlsx,.xls" onchange="handleProjectBomUpload(event)" style="display:none;">
                </label>
            </div>
            <div id="proj-bom-preview"></div>
        </div>`;
    document.body.appendChild(modal);
}

async function handleProjectBomUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    const fd = new FormData(); fd.append('file', file);
    try {
        const r = await fetch(`${MRP_API}/bom/import-preview`, {method: 'POST', body: fd});
        const d = await r.json();
        if (d.success) {
            _projBomPreviewItems = d.items;
            renderProjectBomPreview();
            showToast(`解析到 ${d.total} 项，请确认后导入BOM表`);
        } else showToast(d.detail || '解析失败', 'error');
    } catch(e) { showToast('解析失败', 'error'); }
    event.target.value = '';
}

function renderProjectBomPreview() {
    const el = document.getElementById('proj-bom-preview');
    if (!el) return;
    const stdItems = _projBomPreviewItems.filter(i => i.item_type === 'STANDARD' || i.item_type === 'PURCHASE');
    const madeItems = _projBomPreviewItems.filter(i => !['STANDARD', 'PURCHASE'].includes(i.item_type));
    const rowHtml = i => `<tr>
        <td style="padding:5px;border:1px solid #e5e7eb;">${i.parent_name || '-'}</td>
        <td style="padding:5px;border:1px solid #e5e7eb;">${i.material_name || '-'}</td>
        <td style="padding:5px;border:1px solid #e5e7eb;">${i.material_code || '-'}</td>
        <td style="padding:5px;border:1px solid #e5e7eb;text-align:center;">${_PROJ_TYPE_MAP[i.item_type] || i.item_type || '-'}</td>
        <td style="padding:5px;border:1px solid #e5e7eb;text-align:right;">${i.quantity}</td>
        <td style="padding:5px;border:1px solid #e5e7eb;">${i.material_grade || '-'}</td>
    </tr>`;
    const tableHtml = (title, list, color) => list.length ? `
        <div style="margin:12px 0 6px;font-weight:600;font-size:13px;color:${color};">${title} (${list.length}项)</div>
        <div style="overflow-x:auto;background:#fff;border-radius:8px;">
        <table style="width:100%;border-collapse:collapse;font-size:12px;">
            <thead><tr style="background:#f3f4f6;">
                <th style="padding:5px;border:1px solid #e5e7eb;">物料归属</th>
                <th style="padding:5px;border:1px solid #e5e7eb;">零件名称</th>
                <th style="padding:5px;border:1px solid #e5e7eb;">代号</th>
                <th style="padding:5px;border:1px solid #e5e7eb;">工件类型</th>
                <th style="padding:5px;border:1px solid #e5e7eb;text-align:right;">数量</th>
                <th style="padding:5px;border:1px solid #e5e7eb;">材质</th>
            </tr></thead>
            <tbody>${list.map(rowHtml).join('')}</tbody>
        </table></div>` : '';
    el.innerHTML = `
        <div style="margin-top:14px;">
            ${tableHtml('🛒 标准件', stdItems, '#2563eb')}
            ${tableHtml('🔧 自制件', madeItems, '#d97706')}
            <div style="margin-top:14px;text-align:right;">
                <button onclick="document.getElementById('proj-bom-modal').remove()" style="padding:7px 16px;background:#e5e7eb;color:#374151;border:none;border-radius:6px;cursor:pointer;margin-right:8px;">稍后再导</button>
                <button onclick="confirmProjectBomImport()" style="padding:8px 22px;background:linear-gradient(135deg,#f59e0b,#d97706);color:#fff;border:none;border-radius:6px;cursor:pointer;font-weight:600;">确认导入BOM表</button>
            </div>
        </div>`;
}

async function confirmProjectBomImport() {
    if (!_projBomProject || !_projBomPreviewItems.length) return;
    try {
        const r = await fetch(`${MRP_API}/bom/0/import-confirm`, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                bom_name: `${_projBomProject.projectNo} ${_projBomProject.projectName}`.trim(),
                project_id: _projBomProject.id,
                items: _projBomPreviewItems
            })
        });
        const d = await r.json();
        if (d.success) {
            document.getElementById('proj-bom-modal').remove();
            showToast(`已导入BOM表（${d.imported}项）`
                + (d.purchase_dispatched > 0 ? `，${d.purchase_dispatched}项标准件已下发采购` : '')
                + (d.production_dispatched > 0 ? `，${d.production_dispatched}项自制件已下发生产` : '')
                + (d.po_no ? `，已生成采购订单${d.po_no}` : ''));
            setTimeout(() => { openBomImportPage(); }, 600);
        } else showToast(d.detail || '导入失败', 'error');
    } catch(e) { showToast('导入失败', 'error'); }
}

function openBomImportPage() {
    const content = document.getElementById('content');
    if (!content) return;
    content.innerHTML = '';
    setTimeout(() => { if (typeof renderBomImport === 'function') renderBomImport(); }, 100);
}

function showProjectForm() {
    const title = '➕ 新建项目';

    // A模式表单（批次项目）
    const aFields = `
        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:12px;">
            <div style="font-size:12px;color:#1e40af;font-weight:600;margin-bottom:8px;">🏭 批次项目信息</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                <input id="pf-product-no" placeholder="产品编号 *（如 Motor2024）" style="padding:8px;border:1px solid #ddd;border-radius:6px;">
                <input id="pf-batch-no" placeholder="批次号 *（如 B005）" style="padding:8px;border:1px solid #ddd;border-radius:6px;">
            </div>
            <div id="pf-auto-no" style="margin-top:8px;font-size:12px;color:#64748b;">📌 项目编号将自动生成：<b id="pf-no-preview" style="color:#1e40af;">P-产品编号-B批次号</b></div>
            <div style="margin-top:8px;font-size:11px;color:#64748b;">✅ 创建后将自动建立WBS 2级结构（批次→工序）和固定里程碑</div>
        </div>`;

    const aExtraFields = `
        <div>
            <label style="font-size:12px;color:#666;font-weight:600;">批次金额</label>
            <input id="pf-amount" type="number" placeholder="批次金额" value="500000" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;">
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
                <label style="font-size:12px;color:#666;font-weight:600;">预算成本</label>
                <input id="pf-budget" type="number" placeholder="预算成本" value="350000" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;">
            </div>
            <div>
                <label style="font-size:12px;color:#666;font-weight:600;">预计总成本</label>
                <input id="pf-estcost" type="number" placeholder="预计总成本" value="375000" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;">
            </div>
        </div>
        <div>
            <label style="font-size:12px;color:#666;font-weight:600;">项目经理</label>
            <input id="pf-manager" placeholder="项目经理" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;">
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
                <label style="font-size:12px;color:#666;font-weight:600;">计划开始</label>
                <input id="pf-start" type="date" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;">
            </div>
            <div>
                <label style="font-size:12px;color:#666;font-weight:600;">计划结束</label>
                <input id="pf-end" type="date" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;">
            </div>
        </div>`;

    const aNameField = `
        <div>
            <label style="font-size:12px;color:#666;font-weight:600;">项目名称 *</label>
            <input id="pf-name" placeholder="项目名称" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;margin-top:4px;">
        </div>`;

    // B模式精简表单
    const bFields = `
        <div>
            <label style="font-size:12px;color:#666;font-weight:600;">项目名称 *</label>
            <input id="pf-name-b" placeholder="如：自动化产线改造项目" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;margin-top:4px;">
        </div>
        <div>
            <label style="font-size:12px;color:#666;font-weight:600;">项目编号 *</label>
            <input id="pf-project-no" placeholder="如 P2024-001" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;margin-top:4px;">
        </div>
        <div>
            <label style="font-size:12px;color:#666;font-weight:600;">客户名称</label>
            <input id="pf-customer-name" placeholder="如：某某科技有限公司" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;margin-top:4px;">
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
                <label style="font-size:12px;color:#666;font-weight:600;">合同签订日期</label>
                <input id="pf-start-b" type="date" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;margin-top:4px;">
            </div>
            <div>
                <label style="font-size:12px;color:#666;font-weight:600;">交付日期</label>
                <input id="pf-end-b" type="date" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;margin-top:4px;">
            </div>
        </div>
        <div>
            <label style="font-size:12px;color:#666;font-weight:600;">合同金额</label>
            <div style="display:flex;gap:8px;margin-top:4px;">
                <input id="pf-amount-b" type="number" placeholder="合同金额" value="100" style="flex:1;padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;">
                <select id="pf-amount-unit" style="padding:8px;border:1px solid #ddd;border-radius:6px;white-space:nowrap;">
                    <option value="1">元</option>
                    <option value="10000" selected>万</option>
                    <option value="1000000">百万</option>
                </select>
                <select id="pf-currency" style="padding:8px;border:1px solid #ddd;border-radius:6px;white-space:nowrap;">
                    <option value="CNY">人民币</option>
                    <option value="USD">美元</option>
                    <option value="EUR">欧元</option>
                    <option value="HKD">港币</option>
                </select>
            </div>
            <div id="pf-amount-preview" style="margin-top:4px;font-size:11px;color:#7c3aed;">📌 实际金额：100.00 万人民币 = ¥1,000,000.00</div>
        </div>
        <div>
            <label style="font-size:12px;color:#666;font-weight:600;">交付方式</label>
            <select id="pf-delivery-mode" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;margin-top:4px;">
                <option value="MTO" selected>MTO 按单生产（根据订单生产）</option>
                <option value="MTS">MTS 备货生产（根据预测生产）</option>
                <option value="ATO">ATO 按订单装配（通用件+定制装配）</option>
                <option value="ETO">ETO 按订单设计（定制设计+生产）</option>
            </select>
        </div>`;

    const html = `
        <div id="pf-modal" style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;">
            <div style="background:#fff;border-radius:12px;padding:24px;width:540px;max-height:90vh;overflow-y:auto;">
                <h3>${title}</h3>
                <div style="margin-top:12px;margin-bottom:16px;padding:10px;background:#f8fafc;border-radius:8px;">
                    <label style="font-size:12px;color:#666;font-weight:600;margin-right:16px;">业务模式 *</label>
                    <label style="font-size:13px;margin-right:16px;cursor:pointer;"><input type="radio" name="pf-biz-mode" value="B" checked onchange="switchProjectBizMode('B')"> 🔧 小批量多品种（合同项目）</label>
                    <label style="font-size:13px;cursor:pointer;"><input type="radio" name="pf-biz-mode" value="A" onchange="switchProjectBizMode('A')"> 🏭 大批量单品种（批次项目）</label>
                </div>
                <div style="display:grid;gap:12px;">
                    <div id="pf-a-fields" style="display:none;">
                        ${aFields}
                        ${aNameField}
                        ${aExtraFields}
                    </div>
                    <div id="pf-b-fields">
                        ${bFields}
                    </div>
                </div>
                <div style="display:flex;gap:8px;margin-top:16px;justify-content:flex-end;">
                    <button class="btn btn-secondary" onclick="document.getElementById('pf-modal').remove()">取消</button>
                    <button class="btn btn-primary" onclick="submitProjectForm()">创建</button>
                </div>
            </div>
        </div>`;
    const div = document.createElement('div');
    div.innerHTML = html;
    document.body.appendChild(div.firstElementChild);

    // A模式实时预览项目编号
    const updatePreview = () => {
        const pno = document.getElementById('pf-product-no').value.trim() || '产品编号';
        const bno = document.getElementById('pf-batch-no').value.trim() || '批次号';
        const preview = document.getElementById('pf-no-preview');
        if (preview) preview.textContent = `P-${pno}-${bno}`;
    };
    const pInput = document.getElementById('pf-product-no');
    const bInput = document.getElementById('pf-batch-no');
    if (pInput) pInput.addEventListener('input', updatePreview);
    if (bInput) bInput.addEventListener('input', updatePreview);

    // B模式：合同金额实时预览
    const updateAmountPreview = () => {
        const amt = parseFloat(document.getElementById('pf-amount-b').value) || 0;
        const unit = parseFloat(document.getElementById('pf-amount-unit').value) || 1;
        const currencyEl = document.getElementById('pf-currency');
        const currencyText = currencyEl.options[currencyEl.selectedIndex].text;
        const total = amt * unit;
        const preview = document.getElementById('pf-amount-preview');
        if (preview) {
            preview.textContent = `📌 实际金额：${amt} × ${unit>=10000?(unit/10000)+'万':unit}${currencyText} = ¥${total.toLocaleString('zh-CN', {minimumFractionDigits:2, maximumFractionDigits:2})}`;
        }
    };
    const amtInput = document.getElementById('pf-amount-b');
    const unitSelect = document.getElementById('pf-amount-unit');
    const curSelect = document.getElementById('pf-currency');
    if (amtInput) amtInput.addEventListener('input', updateAmountPreview);
    if (unitSelect) unitSelect.addEventListener('change', updateAmountPreview);
    if (curSelect) curSelect.addEventListener('change', updateAmountPreview);
}

// 切换项目业务模式（表单内）
function switchProjectBizMode(mode) {
    const aDiv = document.getElementById('pf-a-fields');
    const bDiv = document.getElementById('pf-b-fields');
    if (mode === 'A') {
        aDiv.style.display = 'block';
        bDiv.style.display = 'none';
    } else {
        aDiv.style.display = 'none';
        bDiv.style.display = 'block';
    }
}

async function submitProjectForm() {
    // 从表单radio读取业务模式
    const radio = document.querySelector('input[name="pf-biz-mode"]:checked');
    const bizMode = radio ? radio.value : 'B';
    const isA = bizMode === 'A';
    // A模式用pf-name，B模式用pf-name-b
    const nameElId = isA ? 'pf-name' : 'pf-name-b';
    const name = document.getElementById(nameElId).value.trim();
    if (!name) { showToast('请输入项目名称', 'warning'); return; }

    let projectNo = '';
    if (isA) {
        const pno = document.getElementById('pf-product-no').value.trim();
        const bno = document.getElementById('pf-batch-no').value.trim();
        if (!pno || !bno) { showToast('请填写产品编号和批次号', 'warning'); return; }
        projectNo = `P-${pno}-${bno}`;
    } else {
        projectNo = document.getElementById('pf-project-no').value.trim();
        if (!projectNo) { showToast('请输入项目编号', 'warning'); return; }
    }

    // 计算实际合同金额
    let contractAmount = parseFloat(document.getElementById(isA ? 'pf-amount' : 'pf-amount-b').value) || 0;
    let currency = 'CNY';
    let customerName = null;
    if (!isA) {
        const unit = parseFloat(document.getElementById('pf-amount-unit').value) || 1;
        contractAmount = contractAmount * unit;
        currency = document.getElementById('pf-currency').value;
        customerName = document.getElementById('pf-customer-name').value.trim() || null;
    }

    const body = {
        project_no: projectNo,
        project_name: name,
        customer_name: customerName,
        contract_amount: contractAmount,
        currency: currency,
        delivery_mode: !isA ? (document.getElementById('pf-delivery-mode')?.value || 'MTO') : 'MTS',
        budget_cost: isA ? (parseFloat(document.getElementById('pf-budget').value) || 0) : contractAmount,
        estimated_total_cost: isA ? (parseFloat(document.getElementById('pf-estcost').value) || 0) : contractAmount * 0.7,
        manager: isA ? (document.getElementById('pf-manager').value || null) : null,
        planned_start: document.getElementById(isA ? 'pf-start' : 'pf-start-b').value || null,
        planned_end: document.getElementById(isA ? 'pf-end' : 'pf-end-b').value || null,
        business_mode: bizMode,
    };
    try {
        const r = await fetch(`${ENG_API}/wbs-projects/`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
        const d = await r.json();
        if (d.id) {
            // A模式：自动创建固定里程碑
            if (isA) {
                try {
                    await autoCreateAMilestones(d.id);
                    await autoCreateAWbsNodes(d.id, name);
                } catch(e) { console.warn('WBS自动创建部分失败:', e); }
            }
            // 非阻塞Toast提示，3秒自动消失
            showToast(`${isA ? '批次项目' : '合同项目'}创建成功：${d.project_no}${isA ? '，已自动建立WBS结构和里程碑' : ''}`, 'success');
            // 关闭模态框并刷新看板
            const modal = document.getElementById('pf-modal');
            if (modal) modal.remove();
            loadProjectBoard();
            // 项目创立后立即自动弹出BOM零件分类表上传窗口
            setTimeout(() => { showProjectBomImportDialog(d.id, d.project_no || projectNo, name); }, 400);
        } else {
            showToast('创建失败：' + (d.detail || d.message || '未知错误'), 'error');
        }
    } catch(e) {
        showToast('创建失败：' + e.message, 'error');
    }
}

// ==================== 项目交付物料清单 ====================
let _deliverableExcelPreview = null; // 存储Excel预览数据

function downloadDelivTemplate(projectId) {
    showToast('正在下载模板...', 'info', 1500);
    window.open(`${ENG_API}/wbs-projects/${projectId}/deliverables/template`, '_blank');
}

let _delivConfirmMap = {}; // 存储待确认的删除ID

// A模式：自动创建固定里程碑（物料齐套→首件验证→批量投产→入库→发货）
async function autoCreateAMilestones(projectId) {
    const milestones = [
        { name: '原料清单物料齐套', target_progress: 20 },
        { name: '首件验证', target_progress: 40 },
        { name: '批量投产', target_progress: 60 },
        { name: '入库', target_progress: 80 },
        { name: '发货', target_progress: 100 },
    ];
    for (const m of milestones) {
        try {
            await fetch(`${API}/milestones`, {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({ project_id: projectId, name: m.name, target_progress: m.target_progress })
            });
        } catch(e) { console.warn('创建里程碑失败:', m.name, e); }
    }
}

// A模式：自动创建WBS 2级结构（批次→工序）
async function autoCreateAWbsNodes(projectId, projectName) {
    try {
        // 第1级：批次节点
        const r = await fetch(`${API}/projects/${projectId}/wbs-nodes`, {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({ node_code: 'BATCH-001', node_name: `${projectName}-批次`, node_type: 'TASK' })
        });
        const d = await r.json();
        if (d.id) {
            // 第2级：工序节点（固定5道工序）
            const processes = ['物料准备', '首件检验', '批量生产', '入库检验', '发货准备'];
            for (let i = 0; i < processes.length; i++) {
                await fetch(`${API}/projects/${projectId}/wbs-nodes`, {
                    method:'POST', headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({ parent_id: d.id, node_code: `OP-${String(i+1).padStart(2,'0')}`, node_name: processes[i], node_type: 'TASK', sort_order: i+1 })
                });
            }
        }
    } catch(e) { console.warn('创建WBS节点失败:', e); }
}

async function showProjectDetail(projectId) {
    _currentProjectId = projectId; // 记录当前项目ID供生产派工tab使用
    const el = document.getElementById('project-detail');
    const board = document.getElementById('project-board');
    if (!el) return;
    // 隐藏看板，只显示详情（单一滚动区）
    if (board) board.style.display = 'none';
    el.style.display = 'block';
    el.innerHTML = '<div class="empty">加载中...</div>';
    try {
        const r = await fetch(`${API}/projects/${projectId}/detail`);
        const d = await r.json();
        const p = d.project;
        const modeLabels = {MTS:'备货生产', MTO:'按单生产', ATO:'按单装配', ETO:'按单设计'};
        el.innerHTML = `
            <div style="background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                    <div style="display:flex;align-items:center;gap:10px;">
                        <button class="btn btn-sm btn-secondary" onclick="returnToBoard()">← 返回看板</button>
                        <h3 style="margin:0;">📋 ${p.project_name} <span style="font-size:14px;color:#95a5a6;">${p.project_no}</span></h3>
                        <span style="background:#ede9fe;color:#6d28d9;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">${p.delivery_mode || 'MTO'} ${modeLabels[p.delivery_mode]||''}</span>
                    </div>
                    <div>
                        <button id="delete-project-btn" class="btn btn-sm" style="background:#fee2e2;color:#dc2626;border:1px solid #fca5a5;" onclick="handleDeleteProject(${projectId}, '${p.project_name.replace(/'/g,"\\'")}')">🗑️ 删除项目</button>
                    </div>
                </div>
                <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:8px;">
                    <div style="background:#f8f9fa;padding:12px;border-radius:8px;text-align:center;">
                        <div style="font-size:12px;color:#7f8c8d;">合同金额(收入)</div>
                        <div style="font-size:18px;font-weight:600;color:#2c3e50;">${currencySymbol(p.currency)}${(p.contract_amount||0).toLocaleString()}</div>
                    </div>
                    <div style="background:#fef2f2;padding:12px;border-radius:8px;text-align:center;border:1px solid #fecaca;">
                        <div style="font-size:12px;color:#7f8c8d;">项目成本(材料+制费)</div>
                        <div style="font-size:18px;font-weight:600;color:#e74c3c;">¥${(p.incurred_cost||0).toLocaleString()}</div>
                        <div style="font-size:11px;color:#94a3b8;margin-top:2px;">材料¥${(p.material_cost||0).toLocaleString()} · 制费¥${(p.overhead_cost||0).toLocaleString()}</div>
                    </div>
                    <div style="background:${(p.net_profit||0)>=0?'#f0fdf4':'#fef2f2'};padding:12px;border-radius:8px;text-align:center;border:1px solid ${(p.net_profit||0)>=0?'#bbf7d0':'#fecaca'};">
                        <div style="font-size:12px;color:#7f8c8d;">净利润</div>
                        <div style="font-size:18px;font-weight:600;color:${(p.net_profit||0)>=0?'#16a34a':'#dc2626'};">¥${(p.net_profit||0).toLocaleString()}</div>
                        <div style="font-size:11px;color:#94a3b8;margin-top:2px;">合同额 − 项目成本</div>
                    </div>
                    <div style="background:${(p.gross_margin||0)>=30?'#f0fdf4':(p.gross_margin||0)>=10?'#fffbeb':'#fef2f2'};padding:12px;border-radius:8px;text-align:center;border:1px solid ${(p.gross_margin||0)>=30?'#bbf7d0':(p.gross_margin||0)>=10?'#fde68a':'#fecaca'};">
                        <div style="font-size:12px;color:#7f8c8d;">毛利率</div>
                        <div style="font-size:18px;font-weight:600;color:${(p.gross_margin||0)>=30?'#16a34a':(p.gross_margin||0)>=10?'#d97706':'#dc2626'};">${(p.gross_margin||0).toFixed(1)}%</div>
                        <div style="font-size:11px;color:#94a3b8;margin-top:2px;">净利润 / 合同额</div>
                    </div>
                </div>
                <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px;">
                    <div style="background:#f8f9fa;padding:10px 12px;border-radius:8px;text-align:center;">
                        <div style="font-size:12px;color:#7f8c8d;">预算成本</div>
                        <div style="font-size:15px;font-weight:600;color:#e67e22;">¥${(p.budget_cost||0).toLocaleString()}</div>
                    </div>
                    <div style="background:#f8f9fa;padding:10px 12px;border-radius:8px;text-align:center;">
                        <div style="font-size:12px;color:#7f8c8d;">直接材料</div>
                        <div style="font-size:15px;font-weight:600;color:#2563eb;">¥${(p.material_cost||0).toLocaleString()}</div>
                    </div>
                    <div style="background:#f8f9fa;padding:10px 12px;border-radius:8px;text-align:center;">
                        <div style="font-size:12px;color:#7f8c8d;">制造费用(分摊)</div>
                        <div style="font-size:15px;font-weight:600;color:#7c3aed;">¥${(p.overhead_cost||0).toLocaleString()}</div>
                    </div>
                    <div style="background:#f8f9fa;padding:10px 12px;border-radius:8px;text-align:center;">
                        <div style="font-size:12px;color:#7f8c8d;">完工%</div>
                        <div style="font-size:15px;font-weight:600;color:#27ae60;">${p.progress_pct}%</div>
                    </div>
                </div>
                <div class="finance-tabs" style="margin-bottom:12px;flex-wrap:wrap;">
                    <button class="finance-tab active" onclick="showProjTab(event,'deliverables',${projectId})">📦 交付物料</button>
                    <button class="finance-tab" onclick="showProjTab(event,'production',${projectId})">🏭 生产派工</button>
                    <button class="finance-tab" onclick="showProjTab(event,'wbs',${projectId})">🌲 WBS结构</button>
                    <button class="finance-tab" onclick="showProjTab(event,'cost',${projectId})">💰 成本归集</button>
                    <button class="finance-tab" onclick="showProjTab(event,'revenue',${projectId})">📈 收入确认</button>
                    <button class="finance-tab" onclick="showProjTab(event,'milestone',${projectId})">🏁 里程碑</button>
                </div>
                <div id="proj-tab-content"></div>
            </div>`;
        showProjTab(null, 'deliverables', projectId, d);
    } catch(e) { el.innerHTML = '<div class="error">加载失败</div>'; }
}

// 删除项目（二次确认机制，避免误删）
let _deleteConfirmTimer = null;
async function handleDeleteProject(projectId, projectName) {
    const btn = document.getElementById('delete-project-btn');
    if (!btn) return;
    if (btn.dataset.confirming === '1') {
        // 第二次点击：真正删除
        if (_deleteConfirmTimer) { clearTimeout(_deleteConfirmTimer); _deleteConfirmTimer = null; }
        btn.dataset.confirming = '0';
        btn.innerHTML = '🗑️ 删除中...';
        btn.disabled = true;
        try {
            const resp = await fetch(`/api/v1/eng/wbs-projects/${projectId}`, { method: 'DELETE' });
            const d = await resp.json();
            if (d.success) {
                showToast('项目已删除', 'success');
                returnToBoard();
                if (typeof loadProjectBoard === 'function') loadProjectBoard();
            } else {
                showToast(d.message || '删除失败', 'error');
                btn.innerHTML = '🗑️ 删除项目';
                btn.disabled = false;
            }
        } catch(e) {
            showToast('删除失败', 'error');
            btn.innerHTML = '🗑️ 删除项目';
            btn.disabled = false;
        }
    } else {
        // 第一次点击：进入确认状态
        btn.dataset.confirming = '1';
        btn.innerHTML = `⚠️ 确认删除「${projectName}」? (3秒内再点确认)`;
        btn.style.background = '#dc2626';
        btn.style.color = '#fff';
        if (_deleteConfirmTimer) clearTimeout(_deleteConfirmTimer);
        _deleteConfirmTimer = setTimeout(() => {
            btn.dataset.confirming = '0';
            btn.innerHTML = '🗑️ 删除项目';
            btn.style.background = '#fee2e2';
            btn.style.color = '#dc2626';
        }, 3000);
    }
}

function returnToBoard() {
    const board = document.getElementById('project-board');
    const el = document.getElementById('project-detail');
    if (board) board.style.display = '';
    if (el) { el.innerHTML = ''; el.style.display = 'none'; }
}

function showProjTab(ev, tab, projectId, preloaded) {
    if (ev) {
        ev.target.parentElement.querySelectorAll('.finance-tab').forEach(b=>b.classList.remove('active'));
        ev.target.classList.add('active');
    }
    const content = document.getElementById('proj-tab-content');
    if (tab === 'deliverables') {
        content.innerHTML = renderDelivInlineHTML(projectId);
        loadDelivListInline(projectId);
    } else if (tab === 'production') {
        renderProductionTab(projectId, content);
    } else if (tab === 'wbs') {
        content.innerHTML = renderWbsTree(preloaded ? preloaded.wbs_tree : []);
    } else if (tab === 'cost') {
        renderCostForProject(projectId, content);
    } else if (tab === 'revenue') {
        renderRevenueForProject(projectId, content);
    } else if (tab === 'milestone') {
        renderMilestonesForProject(projectId, content);
    }
}

// ==================== 生产派工跨部门协同流程 ====================
let _productionMaterialExcelPreview = null; // 生产原材料Excel预览数据
let _currentProjectId = null; // 当前查看的项目ID（供生产派工tab使用）
let _dispatchConfirmMap = {}; // 下发采购二次确认状态

async function renderProductionTab(projectId, content) {
    content.innerHTML = '<div class="empty">加载中...</div>';
    try {
        const r = await fetch(`${ENG_API}/wbs-projects/${projectId}/production-task`);
        const d = await r.json();
        if (!d.exists) {
            content.innerHTML = `<div style="text-align:center;padding:40px;color:#999;">
                <div style="font-size:48px;margin-bottom:12px;">🏭</div>
                <div style="font-size:15px;margin-bottom:8px;">该项目尚未进入生产阶段</div>
                <div style="font-size:13px;">合同签订后项目状态变为「执行中」，系统会自动创建生产派工任务并下发到生产部门</div>
            </div>`;
            return;
        }
        const task = d.task;
        const flow = d.flow;
        const currentIdx = flow.findIndex(f => f.key === (d.display_status || task.status));
        // 渲染时间线
        let timelineHtml = '<div style="display:flex;align-items:center;gap:0;margin-bottom:24px;overflow-x:auto;padding:8px 0;">';
        flow.forEach((step, idx) => {
            const isDone = idx < currentIdx;
            const isCurrent = idx === currentIdx;
            const color = isDone ? '#10b981' : isCurrent ? '#7c3aed' : '#d1d5db';
            timelineHtml += `<div style="display:flex;align-items:center;flex-shrink:0;">
                <div style="display:flex;flex-direction:column;align-items:center;min-width:80px;">
                    <div style="width:32px;height:32px;border-radius:50%;background:${color};color:#fff;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:600;${isCurrent?'box-shadow:0 0 0 4px #ede9fe;':''}">${isDone?'✓':idx+1}</div>
                    <div style="font-size:11px;color:${isCurrent?'#7c3aed':'#666'};font-weight:${isCurrent?'600':'400'};margin-top:4px;text-align:center;">${step.label}</div>
                </div>
                ${idx < flow.length - 1 ? `<div style="width:40px;height:2px;background:${isDone?'#10b981':'#e5e7eb'};margin:0 4px;"></div>` : ''}
            </div>`;
        });
        timelineHtml += '</div>';
        // 状态描述
        const currentStep = flow[currentIdx] || flow[0];
        let html = `<div style="background:#fff;border-radius:8px;padding:16px;margin-bottom:16px;border:1px solid #e5e7eb;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <div><span style="font-size:14px;font-weight:600;">派工单号：${task.task_no}</span>
                <span style="margin-left:8px;padding:2px 8px;border-radius:4px;font-size:11px;background:#ede9fe;color:#6d28d9;">${currentStep.label}</span></div>
                <div style="font-size:12px;color:#999;">${currentStep.desc}</div>
            </div>
            ${timelineHtml}`;
        // 操作区（根据状态显示）
        if (task.status === 'CONTRACT_SIGNED') {
            html += `<button onclick="receiveProductionTask(${task.id})" style="padding:10px 24px;background:#7c3aed;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:14px;font-weight:600;">📥 生产部门接收任务</button>`;
        } else if (task.status === 'PRODUCTION_RECEIVED') {
            html += `<button onclick="showProductionStepsForm(${task.id})" style="padding:10px 24px;background:#3b82f6;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:14px;font-weight:600;">📝 定义生产步骤</button>`;
        } else if (task.status === 'STEPS_DEFINED' || task.status === 'MATERIALS_UPLOADED') {
            html += `<button onclick="showProductionStepsForm(${task.id})" style="padding:10px 16px;background:#3b82f6;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;margin-right:8px;">📝 编辑工序</button>
                     <button onclick="document.getElementById('mat-excel-input-'+${task.id}).click()" style="padding:10px 16px;background:#10b981;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;">📊 上传原材料Excel</button>
                     <input type="file" id="mat-excel-input-${task.id}" accept=".xlsx,.xls" style="display:none;" onchange="handleMaterialExcelUpload(event, ${task.id})">`;
        } else if (task.status === 'PROCUREMENT_DISPATCHED' || task.status === 'PURCHASING' || task.status === 'COMPLETED') {
            html += `<div style="padding:8px 16px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;color:#16a34a;font-size:13px;">✅ 已下发采购部门，采购部门正在处理</div>`;
        }
        html += `</div>`;
        // 生产步骤展示
        if (task.production_steps && task.production_steps.length) {
            html += `<div style="background:#fff;border-radius:8px;padding:16px;margin-bottom:16px;border:1px solid #e5e7eb;">
                <div style="font-size:14px;font-weight:600;margin-bottom:12px;">📋 生产步骤</div>
                <table style="width:100%;border-collapse:collapse;font-size:13px;">
                    <thead><tr style="background:#f8fafc;"><th style="padding:8px;text-align:left;border-bottom:2px solid #e5e7eb;">序号</th><th style="padding:8px;text-align:left;border-bottom:2px solid #e5e7eb;">工序名称</th><th style="padding:8px;text-align:left;border-bottom:2px solid #e5e7eb;">说明</th><th style="padding:8px;text-align:left;border-bottom:2px solid #e5e7eb;">负责人</th></tr></thead><tbody>`;
            task.production_steps.forEach((s, i) => {
                html += `<tr style="border-bottom:1px solid #f3f4f6;"><td style="padding:8px;">${s.seq||i+1}</td><td style="padding:8px;font-weight:500;">${s.name||''}</td><td style="padding:8px;color:#666;">${s.desc||'-'}</td><td style="padding:8px;">${s.operator||'-'}</td></tr>`;
            });
            html += `</tbody></table></div>`;
        }
        // 工序表单（默认隐藏）
        html += `<div id="prod-steps-form-${task.id}" style="display:none;background:#fff;border-radius:8px;padding:16px;margin-bottom:16px;border:1px solid #e5e7eb;">
            <div style="font-size:14px;font-weight:600;margin-bottom:12px;">📝 定义生产步骤</div>
            <div id="prod-steps-list-${task.id}"></div>
            <button onclick="addProdStepRow(${task.id})" style="padding:6px 12px;background:#e5e7eb;color:#333;border:none;border-radius:4px;cursor:pointer;font-size:12px;margin-top:8px;">+ 添加工序</button>
            <div style="display:flex;gap:8px;margin-top:12px;">
                <button onclick="saveProductionSteps(${task.id})" style="padding:8px 16px;background:#10b981;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;">保存步骤</button>
                <button onclick="document.getElementById('prod-steps-form-${task.id}').style.display='none'" style="padding:8px 16px;background:#e5e7eb;color:#333;border:none;border-radius:6px;cursor:pointer;font-size:13px;">取消</button>
            </div>
        </div>`;
        // 原材料Excel预览区
        html += `<div id="mat-excel-preview-${task.id}" style="display:none;background:#fffbeb;padding:16px;border-radius:8px;margin-bottom:16px;border:1px solid #fde68a;">
            <div id="mat-excel-title-${task.id}" style="font-weight:600;margin-bottom:8px;">📊 原材料Excel预览</div>
            <div id="mat-excel-table-${task.id}" style="max-height:200px;overflow:auto;margin-bottom:12px;"></div>
            <div style="font-size:12px;color:#666;margin-bottom:8px;">请确认列映射：</div>
            <div id="mat-mapping-${task.id}" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;margin-bottom:12px;"></div>
            <div style="display:flex;gap:8px;">
                <button onclick="confirmMaterialExcelImport(${task.id})" style="padding:8px 16px;background:#10b981;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;">确认导入</button>
                <button onclick="document.getElementById('mat-excel-preview-${task.id}').style.display='none';_productionMaterialExcelPreview=null;" style="padding:8px 16px;background:#e5e7eb;color:#333;border:none;border-radius:6px;cursor:pointer;font-size:13px;">取消</button>
            </div>
        </div>`;
        // 原材料需求清单
        html += `<div style="background:#fff;border-radius:8px;padding:16px;border:1px solid #e5e7eb;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <div style="font-size:14px;font-weight:600;">📦 原材料需求清单（${d.materials.length}项）</div>
                ${(task.status==='STEPS_DEFINED'||task.status==='MATERIALS_UPLOADED') ? `<div style="display:flex;gap:6px;"><button onclick="showMaterialAddForm(${task.id})" style="padding:6px 12px;background:#3b82f6;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:12px;">➕ 手动添加</button><button onclick="showOcrCaptureModal(${task.id})" style="padding:6px 12px;background:#8b5cf6;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:12px;">📷 截图识别录入</button></div>` : ''}
            </div>
            <div id="mat-add-form-${task.id}" style="display:none;background:#f8fafc;padding:12px;border-radius:6px;margin-bottom:12px;">
                <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px;">
                    <input id="mat-code-${task.id}" placeholder="物料编码" style="padding:6px;border:1px solid #ddd;border-radius:4px;font-size:12px;">
                    <input id="mat-name-${task.id}" placeholder="物料名称 *" style="padding:6px;border:1px solid #ddd;border-radius:4px;font-size:12px;">
                    <input id="mat-spec-${task.id}" placeholder="规格型号" style="padding:6px;border:1px solid #ddd;border-radius:4px;font-size:12px;">
                    <input id="mat-qty-${task.id}" type="number" value="1" placeholder="数量" style="padding:6px;border:1px solid #ddd;border-radius:4px;font-size:12px;">
                    <input id="mat-unit-${task.id}" value="个" placeholder="单位" style="padding:6px;border:1px solid #ddd;border-radius:4px;font-size:12px;">
                    <input id="mat-price-${task.id}" type="number" placeholder="单价" style="padding:6px;border:1px solid #ddd;border-radius:4px;font-size:12px;">
                </div>
                <div style="margin-top:8px;"><button onclick="submitMaterialAdd(${task.id})" style="padding:6px 12px;background:#10b981;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:12px;">确认添加</button></div>
            </div>
            <div id="mat-list-${task.id}"></div>
            ${(task.status==='MATERIALS_UPLOADED') ? `<div style="margin-top:16px;text-align:center;"><button onclick="dispatchToProcurement(${task.id})" style="padding:12px 32px;background:linear-gradient(135deg,#f59e0b,#d97706);color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:14px;font-weight:600;">🚀 下发到采购部门</button></div>` : ''}
        </div>`;
        content.innerHTML = html;
        loadMaterialList(task.id, d.materials);
    } catch(e) {
        content.innerHTML = '<div class="error">加载失败：' + e.message + '</div>';
    }
}

async function receiveProductionTask(taskId) {
    try {
        const r = await fetch(`${ENG_API}/production-tasks/${taskId}/receive`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({})});
        const d = await r.json();
        if (d.success) { showToast(d.msg); renderProductionTab(getCurrentProjectId(), document.getElementById('proj-tab-content')); }
        else showToast('操作失败：' + (d.detail||''), 'error');
    } catch(e) { showToast('操作失败：' + e.message, 'error'); }
}

function getCurrentProjectId() {
    return _currentProjectId;
}

function showProductionStepsForm(taskId) {
    const form = document.getElementById('prod-steps-form-' + taskId);
    if (!form) return;
    form.style.display = 'block';
    // 加载已有步骤
    fetch(`${ENG_API}/wbs-projects/${getCurrentProjectId()}/production-task`).then(r=>r.json()).then(d=>{
        if (!d.exists) return;
        const listEl = document.getElementById('prod-steps-list-' + taskId);
        listEl.innerHTML = '';
        const steps = d.task.production_steps || [];
        if (!steps.length) steps.push({seq:1, name:'', desc:'', operator:''});
        steps.forEach((s, i) => {
            listEl.innerHTML += `<div style="display:grid;grid-template-columns:60px 1fr 2fr 1fr auto;gap:6px;margin-bottom:6px;align-items:center;">
                <input value="${s.seq||i+1}" placeholder="序号" style="padding:6px;border:1px solid #ddd;border-radius:4px;font-size:12px;text-align:center;">
                <input value="${s.name||''}" placeholder="工序名称" style="padding:6px;border:1px solid #ddd;border-radius:4px;font-size:12px;">
                <input value="${s.desc||''}" placeholder="工序说明" style="padding:6px;border:1px solid #ddd;border-radius:4px;font-size:12px;">
                <input value="${s.operator||''}" placeholder="负责人" style="padding:6px;border:1px solid #ddd;border-radius:4px;font-size:12px;">
                <button onclick="this.parentElement.remove()" style="padding:6px 8px;background:#fee2e2;color:#dc2626;border:none;border-radius:4px;cursor:pointer;font-size:11px;">删除</button>
            </div>`;
        });
    });
}

function addProdStepRow(taskId) {
    const listEl = document.getElementById('prod-steps-list-' + taskId);
    const idx = listEl.children.length + 1;
    const div = document.createElement('div');
    div.style.cssText = 'display:grid;grid-template-columns:60px 1fr 2fr 1fr auto;gap:6px;margin-bottom:6px;align-items:center;';
    div.innerHTML = `<input value="${idx}" placeholder="序号" style="padding:6px;border:1px solid #ddd;border-radius:4px;font-size:12px;text-align:center;"><input placeholder="工序名称" style="padding:6px;border:1px solid #ddd;border-radius:4px;font-size:12px;"><input placeholder="工序说明" style="padding:6px;border:1px solid #ddd;border-radius:4px;font-size:12px;"><input placeholder="负责人" style="padding:6px;border:1px solid #ddd;border-radius:4px;font-size:12px;"><button onclick="this.parentElement.remove()" style="padding:6px 8px;background:#fee2e2;color:#dc2626;border:none;border-radius:4px;cursor:pointer;font-size:11px;">删除</button>`;
    listEl.appendChild(div);
}

async function saveProductionSteps(taskId) {
    const rows = document.getElementById('prod-steps-list-' + taskId).children;
    const steps = [];
    for (let row of rows) {
        const inputs = row.querySelectorAll('input');
        if (inputs[1].value.trim()) {
            steps.push({seq:parseInt(inputs[0].value)||steps.length+1, name:inputs[1].value.trim(), desc:inputs[2].value.trim(), operator:inputs[3].value.trim()});
        }
    }
    if (!steps.length) { showToast('请至少添加一个工序步骤', 'warning'); return; }
    try {
        const r = await fetch(`${ENG_API}/production-tasks/${taskId}/steps`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({steps})});
        const d = await r.json();
        if (d.success) { showToast(d.msg); renderProductionTab(getCurrentProjectId(), document.getElementById('proj-tab-content')); }
        else showToast('保存失败：' + (d.detail||''), 'error');
    } catch(e) { showToast('保存失败：' + e.message, 'error'); }
}

function showMaterialAddForm(taskId) {
    const form = document.getElementById('mat-add-form-' + taskId);
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

async function submitMaterialAdd(taskId) {
    const name = document.getElementById('mat-name-' + taskId).value.trim();
    if (!name) { showToast('请输入物料名称', 'warning'); return; }
    const body = {
        material_code: document.getElementById('mat-code-' + taskId).value.trim() || null,
        material_name: name,
        specification: document.getElementById('mat-spec-' + taskId).value.trim() || null,
        quantity: parseFloat(document.getElementById('mat-qty-' + taskId).value) || 1,
        unit: document.getElementById('mat-unit-' + taskId).value.trim() || '个',
        unit_price: parseFloat(document.getElementById('mat-price-' + taskId).value) || null,
    };
    try {
        const r = await fetch(`${ENG_API}/production-tasks/${taskId}/materials`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
        const d = await r.json();
        if (d.success) {
            showToast('原材料需求已添加');
            document.getElementById('mat-add-form-' + taskId).style.display = 'none';
            renderProductionTab(getCurrentProjectId(), document.getElementById('proj-tab-content'));
        } else showToast('添加失败：' + (d.detail||''), 'error');
    } catch(e) { showToast('添加失败：' + e.message, 'error'); }
}

async function handleMaterialExcelUpload(event, taskId) {
    const file = event.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
        showToast('正在解析Excel...', 'info', 2000);
        const r = await fetch(`${ENG_API}/production-tasks/${taskId}/materials/preview-excel`, {method:'POST', body:formData});
        const d = await r.json();
        if (d.success) {
            _productionMaterialExcelPreview = d;
            renderMaterialExcelPreview(taskId);
            showToast(`Excel解析成功，共${d.total}行数据，请确认列映射`, 'success');
        } else showToast('Excel解析失败：' + (d.detail||''), 'error');
    } catch(e) { showToast('上传失败：' + e.message, 'error'); }
    event.target.value = '';
}

function renderMaterialExcelPreview(taskId) {
    const d = _productionMaterialExcelPreview;
    if (!d) return;
    const previewEl = document.getElementById('mat-excel-preview-' + taskId);
    const tableEl = document.getElementById('mat-excel-table-' + taskId);
    const mappingEl = document.getElementById('mat-mapping-' + taskId);
    previewEl.style.display = 'block';
    document.getElementById('mat-excel-title-' + taskId).textContent = `📊 原材料Excel预览（共${d.total}行）`;
    let tableHtml = '<table style="width:100%;border-collapse:collapse;font-size:12px;"><thead><tr style="background:#f3f4f6;">';
    d.headers.forEach(h => tableHtml += `<th style="padding:6px;border:1px solid #e5e7eb;">${h}</th>`);
    tableHtml += '</tr></thead><tbody>';
    d.rows.slice(0, 5).forEach(row => {
        tableHtml += '<tr>';
        d.headers.forEach(h => tableHtml += `<td style="padding:6px;border:1px solid #e5e7eb;">${row[h] || ''}</td>`);
        tableHtml += '</tr>';
    });
    tableHtml += '</tbody></table>';
    if (d.total > 5) tableHtml += `<div style="font-size:11px;color:#666;margin-top:4px;">仅显示前5行，共${d.total}行</div>`;
    tableEl.innerHTML = tableHtml;
    // 智能映射（复用交付物料的逻辑）
    const fieldAliases = {
        material_code: ['物料编码', '物料编号', '编码', '料号'],
        material_name: ['物料名称', '名称', '品名', '原材料名称'],
        specification: ['规格型号', '规格', '型号', '规格/型号'],
        quantity: ['数量', 'qty'],
        unit: ['单位', '计量单位'],
        unit_price: ['单价', '价格', '单价元', '含税单价'],
        remark: ['备注', '说明']
    };
    function normalizeHeader(h) { return String(h).trim().replace(/[（(].*?[)）]/g, '').replace(/\s+/g, '').toLowerCase(); }
    function smartMatchField(header) {
        const norm = normalizeHeader(header);
        for (const [field, aliases] of Object.entries(fieldAliases)) {
            for (const alias of aliases) {
                if (norm === normalizeHeader(alias)) return field;
            }
        }
        for (const [field, aliases] of Object.entries(fieldAliases)) {
            for (const alias of aliases) {
                const normAlias = normalizeHeader(alias);
                if (norm.includes(normAlias) && normAlias.length >= 2) return field;
            }
        }
        return null;
    }
    const systemFields = [
        {key:'material_code', label:'物料编码'}, {key:'material_name', label:'物料名称 *'},
        {key:'specification', label:'规格型号'}, {key:'quantity', label:'数量'},
        {key:'unit', label:'单位'}, {key:'unit_price', label:'单价'}, {key:'remark', label:'备注'}
    ];
    let mappingHtml = '';
    systemFields.forEach(f => {
        const matched = d.headers.find(h => smartMatchField(h) === f.key);
        mappingHtml += `<div><label style="font-size:11px;color:#666;">${f.label}</label><select id="mat-map-${f.key}-${taskId}" style="width:100%;padding:4px;border:1px solid #ddd;border-radius:4px;font-size:12px;margin-top:2px;"><option value="">-- 不导入 --</option>`;
        d.headers.forEach(h => {
            const selected = matched === h ? 'selected' : '';
            mappingHtml += `<option value="${h}" ${selected}>${h}${selected?' ✓':''}</option>`;
        });
        mappingHtml += '</select></div>';
    });
    mappingEl.innerHTML = mappingHtml;
}

async function confirmMaterialExcelImport(taskId) {
    const d = _productionMaterialExcelPreview;
    if (!d) return;
    const fieldMap = {};
    ['material_code','material_name','specification','quantity','unit','unit_price','remark'].forEach(key => {
        const sel = document.getElementById('mat-map-' + key + '-' + taskId);
        if (sel && sel.value) fieldMap[key] = sel.value;
    });
    if (!fieldMap.material_name) { showToast('必须映射"物料名称"字段', 'warning'); return; }
    const items = d.rows.map(row => {
        const item = {};
        Object.keys(fieldMap).forEach(sysKey => {
            let val = row[fieldMap[sysKey]] || '';
            if (sysKey === 'quantity' || sysKey === 'unit_price') val = parseFloat(val) || (sysKey === 'quantity' ? 1 : null);
            item[sysKey] = val;
        });
        return item;
    }).filter(item => item.material_name);
    try {
        const r = await fetch(`${ENG_API}/production-tasks/${taskId}/materials/batch`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({items})});
        const resp = await r.json();
        if (resp.success) {
            showToast(resp.msg);
            _productionMaterialExcelPreview = null;
            renderProductionTab(getCurrentProjectId(), document.getElementById('proj-tab-content'));
        } else showToast('导入失败：' + (resp.detail||''), 'error');
    } catch(e) { showToast('导入失败：' + e.message, 'error'); }
}

async function deleteMaterialReq(reqId, taskId) {
    try {
        const r = await fetch(`${ENG_API}/material-requirements/${reqId}`, {method:'DELETE'});
        const d = await r.json();
        if (d.success) { showToast('删除成功'); renderProductionTab(getCurrentProjectId(), document.getElementById('proj-tab-content')); }
    } catch(e) { showToast('删除失败：' + e.message, 'error'); }
}

async function dispatchToProcurement(taskId) {
    // 非阻塞二次点击确认：第一次点击显示"确认下发"红色按钮，2秒后自动取消
    if (!_dispatchConfirmMap[taskId]) {
        _dispatchConfirmMap[taskId] = true;
        showToast('再次点击「🚀 下发到采购部门」按钮确认下发', 'warning', 2000);
        const btn = event.target;
        const origText = btn.textContent;
        btn.textContent = '⚠️ 确认下发？';
        btn.style.background = '#dc2626';
        setTimeout(() => {
            _dispatchConfirmMap[taskId] = false;
            btn.textContent = origText;
            btn.style.background = 'linear-gradient(135deg,#f59e0b,#d97706)';
        }, 2000);
        return;
    }
    _dispatchConfirmMap[taskId] = false;
    try {
        const r = await fetch(`${ENG_API}/production-tasks/${taskId}/dispatch-procurement`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({})});
        const d = await r.json();
        if (d.success) { showToast('🚀 已下发到采购部门'); renderProductionTab(getCurrentProjectId(), document.getElementById('proj-tab-content')); }
        else showToast('下发失败：' + (d.detail||''), 'error');
    } catch(e) { showToast('下发失败：' + e.message, 'error'); }
}

function loadMaterialList(taskId, materials) {
    const el = document.getElementById('mat-list-' + taskId);
    if (!el) return;
    if (!materials.length) {
        el.innerHTML = '<div style="text-align:center;color:#999;padding:16px;">暂无原材料需求，请手动添加或上传Excel</div>';
        return;
    }
    let html = `<table style="width:100%;border-collapse:collapse;font-size:13px;"><thead><tr style="background:#f8fafc;">
        <th style="padding:8px;text-align:left;border-bottom:2px solid #e5e7eb;">物料编码</th>
        <th style="padding:8px;text-align:left;border-bottom:2px solid #e5e7eb;">物料名称</th>
        <th style="padding:8px;text-align:left;border-bottom:2px solid #e5e7eb;">规格</th>
        <th style="padding:8px;text-align:right;border-bottom:2px solid #e5e7eb;">数量</th>
        <th style="padding:8px;text-align:left;border-bottom:2px solid #e5e7eb;">单位</th>
        <th style="padding:8px;text-align:right;border-bottom:2px solid #e5e7eb;">单价</th>
        <th style="padding:8px;text-align:center;border-bottom:2px solid #e5e7eb;">来源</th>
        <th style="padding:8px;text-align:center;border-bottom:2px solid #e5e7eb;">操作</th>
    </tr></thead><tbody>`;
    let total = 0;
    materials.forEach(m => {
        const subtotal = (m.quantity||0) * (m.unit_price||0);
        total += subtotal;
        html += `<tr style="border-bottom:1px solid #f3f4f6;">
            <td style="padding:8px;">${m.material_code||'-'}</td>
            <td style="padding:8px;font-weight:500;">${m.material_name}</td>
            <td style="padding:8px;color:#666;">${m.specification||'-'}</td>
            <td style="padding:8px;text-align:right;">${m.quantity}</td>
            <td style="padding:8px;">${m.unit}</td>
            <td style="padding:8px;text-align:right;">${m.unit_price?'¥'+m.unit_price.toLocaleString():'-'}</td>
            <td style="padding:8px;text-align:center;"><span style="padding:2px 6px;border-radius:4px;font-size:11px;background:${m.source==='excel'?'#dbeafe':'#fef3c7'};color:${m.source==='excel'?'#1e40af':'#92400e'};">${m.source==='excel'?'Excel':'手动'}</span></td>
            <td style="padding:8px;text-align:center;"><button onclick="deleteMaterialReq(${m.id}, ${taskId})" style="background:#fee2e2;color:#dc2626;border:none;border-radius:4px;padding:4px 8px;cursor:pointer;font-size:11px;">删除</button></td>
        </tr>`;
    });
    html += `</tbody></table><div style="text-align:right;margin-top:12px;font-size:14px;font-weight:600;">合计金额：<span style="color:#d97706;">¥${total.toLocaleString()}</span></div>`;
    el.innerHTML = html;
}

// 交付物料内联渲染（项目详情tab）
function renderDelivInlineHTML(projectId) {
    return `
        <div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;">
            <button onclick="showDelivAddInline(${projectId})" style="padding:8px 16px;background:#3b82f6;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;">➕ 手动添加</button>
            <button onclick="document.getElementById('deliv-excel-input-inline-${projectId}').click()" style="padding:8px 16px;background:#10b981;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;">📊 Excel导入</button>
            <button onclick="downloadDelivTemplate(${projectId})" style="padding:8px 16px;background:#f59e0b;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;">📥 下载模板</button>
            <input type="file" id="deliv-excel-input-inline-${projectId}" accept=".xlsx,.xls" style="display:none;" onchange="handleDelivExcelUploadInline(event, ${projectId})">
            <button onclick="loadDelivListInline(${projectId})" style="padding:8px 16px;background:#6b7280;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;">🔄 刷新</button>
        </div>
        <div id="deliv-add-form-inline-${projectId}" style="display:none;background:#f8fafc;padding:16px;border-radius:8px;margin-bottom:16px;">
            <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;">
                <div><label style="font-size:12px;color:#666;font-weight:600;">物料编码</label><input id="deliv-code-inline-${projectId}" placeholder="可选" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;margin-top:4px;"></div>
                <div><label style="font-size:12px;color:#666;font-weight:600;">物料名称 *</label><input id="deliv-name-inline-${projectId}" placeholder="如：钢板" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;margin-top:4px;"></div>
                <div><label style="font-size:12px;color:#666;font-weight:600;">规格型号</label><input id="deliv-spec-inline-${projectId}" placeholder="可选" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;margin-top:4px;"></div>
                <div><label style="font-size:12px;color:#666;font-weight:600;">数量 *</label><input id="deliv-qty-inline-${projectId}" type="number" value="1" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;margin-top:4px;"></div>
                <div><label style="font-size:12px;color:#666;font-weight:600;">单位</label><input id="deliv-unit-inline-${projectId}" value="个" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;margin-top:4px;"></div>
                <div><label style="font-size:12px;color:#666;font-weight:600;">单价</label><input id="deliv-price-inline-${projectId}" type="number" placeholder="可选" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;margin-top:4px;"></div>
            </div>
            <div style="margin-top:12px;"><label style="font-size:12px;color:#666;font-weight:600;">备注</label><input id="deliv-remark-inline-${projectId}" placeholder="可选" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:6px;box-sizing:border-box;margin-top:4px;"></div>
            <div style="display:flex;gap:8px;margin-top:12px;">
                <button onclick="submitDelivAddInline(${projectId})" style="padding:8px 16px;background:#10b981;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;">确认添加</button>
                <button onclick="document.getElementById('deliv-add-form-inline-${projectId}').style.display='none'" style="padding:8px 16px;background:#e5e7eb;color:#333;border:none;border-radius:6px;cursor:pointer;font-size:13px;">取消</button>
            </div>
        </div>
        <div id="deliv-excel-preview-inline-${projectId}" style="display:none;background:#fffbeb;padding:16px;border-radius:8px;margin-bottom:16px;border:1px solid #fde68a;">
            <div id="deliv-excel-title-inline-${projectId}" style="font-weight:600;margin-bottom:8px;">📊 Excel数据预览</div>
            <div id="deliv-excel-table-inline-${projectId}" style="max-height:200px;overflow:auto;margin-bottom:12px;"></div>
            <div style="font-size:12px;color:#666;margin-bottom:8px;">请确认列映射：</div>
            <div id="deliv-mapping-inline-${projectId}" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;margin-bottom:12px;"></div>
            <div style="display:flex;gap:8px;">
                <button onclick="confirmDelivExcelImportInline(${projectId})" style="padding:8px 16px;background:#10b981;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;">确认导入</button>
                <button onclick="document.getElementById('deliv-excel-preview-inline-${projectId}').style.display='none';_deliverableExcelPreview=null;" style="padding:8px 16px;background:#e5e7eb;color:#333;border:none;border-radius:6px;cursor:pointer;font-size:13px;">取消</button>
            </div>
        </div>
        <div id="deliv-list-inline-${projectId}"></div>`;
}

function showDelivAddInline(projectId) {
    const form = document.getElementById('deliv-add-form-inline-' + projectId);
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

async function loadDelivListInline(projectId) {
    const el = document.getElementById('deliv-list-inline-' + projectId);
    if (!el) return;
    try {
        const r = await fetch(`${ENG_API}/wbs-projects/${projectId}/deliverables`);
        const data = await r.json();
        if (!data.length) {
            el.innerHTML = '<div style="text-align:center;color:#999;padding:20px;">暂无交付物料，请手动添加或Excel导入</div>';
            return;
        }
        let html = `<table style="width:100%;border-collapse:collapse;font-size:13px;">
            <thead><tr style="background:#f8fafc;">
                <th style="padding:8px;text-align:left;border-bottom:2px solid #e5e7eb;">物料编码</th>
                <th style="padding:8px;text-align:left;border-bottom:2px solid #e5e7eb;">物料名称</th>
                <th style="padding:8px;text-align:left;border-bottom:2px solid #e5e7eb;">规格</th>
                <th style="padding:8px;text-align:right;border-bottom:2px solid #e5e7eb;">数量</th>
                <th style="padding:8px;text-align:left;border-bottom:2px solid #e5e7eb;">单位</th>
                <th style="padding:8px;text-align:right;border-bottom:2px solid #e5e7eb;">单价</th>
                <th style="padding:8px;text-align:center;border-bottom:2px solid #e5e7eb;">来源</th>
                <th style="padding:8px;text-align:center;border-bottom:2px solid #e5e7eb;">操作</th>
            </tr></thead><tbody>`;
        let total = 0;
        data.forEach(d => {
            const subtotal = (d.quantity || 0) * (d.unit_price || 0);
            total += subtotal;
            html += `<tr style="border-bottom:1px solid #f3f4f6;">
                <td style="padding:8px;">${d.material_code || '-'}</td>
                <td style="padding:8px;font-weight:500;">${d.material_name}</td>
                <td style="padding:8px;color:#666;">${d.specification || '-'}</td>
                <td style="padding:8px;text-align:right;">${d.quantity}</td>
                <td style="padding:8px;">${d.unit}</td>
                <td style="padding:8px;text-align:right;">${d.unit_price ? '¥' + d.unit_price.toLocaleString() : '-'}</td>
                <td style="padding:8px;text-align:center;"><span style="padding:2px 6px;border-radius:4px;font-size:11px;background:${d.source==='excel'?'#dbeafe':'#fef3c7'};color:${d.source==='excel'?'#1e40af':'#92400e'};">${d.source==='excel'?'Excel':'手动'}</span></td>
                <td style="padding:8px;text-align:center;"><button onclick="deleteDelivInline(${d.id}, ${projectId})" style="background:${_delivConfirmMap[d.id]?'#dc2626':'#fee2e2'};color:${_delivConfirmMap[d.id]?'#fff':'#dc2626'};border:none;border-radius:4px;padding:4px 8px;cursor:pointer;font-size:11px;">${_delivConfirmMap[d.id]?'确认删除?':'删除'}</button></td>
            </tr>`;
        });
        html += `</tbody></table>
            <div style="text-align:right;margin-top:12px;font-size:14px;font-weight:600;">合计金额：<span style="color:#7c3aed;">¥${total.toLocaleString()}</span></div>`;
        el.innerHTML = html;
    } catch(e) {
        el.innerHTML = '<div style="text-align:center;color:#dc2626;padding:20px;">加载失败：' + e.message + '</div>';
    }
}

async function submitDelivAddInline(projectId) {
    const name = document.getElementById('deliv-name-inline-' + projectId).value.trim();
    if (!name) { showToast('请输入物料名称', 'warning'); return; }
    const body = {
        material_code: document.getElementById('deliv-code-inline-' + projectId).value.trim() || null,
        material_name: name,
        specification: document.getElementById('deliv-spec-inline-' + projectId).value.trim() || null,
        quantity: parseFloat(document.getElementById('deliv-qty-inline-' + projectId).value) || 1,
        unit: document.getElementById('deliv-unit-inline-' + projectId).value.trim() || '个',
        unit_price: parseFloat(document.getElementById('deliv-price-inline-' + projectId).value) || null,
        remark: document.getElementById('deliv-remark-inline-' + projectId).value.trim() || null,
    };
    try {
        const r = await fetch(`${ENG_API}/wbs-projects/${projectId}/deliverables`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
        const d = await r.json();
        if (d.id) {
            showToast('物料添加成功');
            document.getElementById('deliv-add-form-inline-' + projectId).style.display = 'none';
            loadDelivListInline(projectId);
            loadProjectBoard();
        } else { showToast('添加失败：' + (d.detail || ''), 'error'); }
    } catch(e) { showToast('添加失败：' + e.message, 'error'); }
}

async function deleteDelivInline(delivId, projectId) {
    if (!_delivConfirmMap[delivId]) {
        _delivConfirmMap[delivId] = true;
        showToast('再次点击删除按钮确认删除', 'warning', 2000);
        setTimeout(() => { delete _delivConfirmMap[delivId]; loadDelivListInline(projectId); }, 2000);
        return;
    }
    try {
        const r = await fetch(`${ENG_API}/deliverables/${delivId}`, {method:'DELETE'});
        const d = await r.json();
        if (d.success) {
            showToast('删除成功');
            delete _delivConfirmMap[delivId];
            loadDelivListInline(projectId);
            loadProjectBoard();
        }
    } catch(e) { showToast('删除失败：' + e.message, 'error'); }
}

async function handleDelivExcelUploadInline(event, projectId) {
    const file = event.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
        showToast('正在解析Excel...', 'info', 2000);
        const r = await fetch(`${ENG_API}/wbs-projects/${projectId}/deliverables/preview-excel`, {method:'POST', body:formData});
        const d = await r.json();
        if (d.success) {
            _deliverableExcelPreview = d;
            renderDelivExcelPreviewInline(projectId);
            showToast(`Excel解析成功，共${d.total}行数据，请确认列映射`, 'success');
        } else {
            showToast('Excel解析失败：' + (d.detail || ''), 'error');
        }
    } catch(e) {
        showToast('上传失败：' + e.message, 'error');
    }
    event.target.value = '';
}

function renderDelivExcelPreviewInline(projectId) {
    const d = _deliverableExcelPreview;
    if (!d) return;
    const previewEl = document.getElementById('deliv-excel-preview-inline-' + projectId);
    if (!previewEl) return;
    const tableEl = document.getElementById('deliv-excel-table-inline-' + projectId);
    const mappingEl = document.getElementById('deliv-mapping-inline-' + projectId);
    previewEl.style.display = 'block';
    document.getElementById('deliv-excel-title-inline-' + projectId).textContent = `📊 Excel数据预览（共${d.total}行）`;
    let tableHtml = '<table style="width:100%;border-collapse:collapse;font-size:12px;"><thead><tr style="background:#f3f4f6;">';
    d.headers.forEach(h => tableHtml += `<th style="padding:6px;border:1px solid #e5e7eb;">${h}</th>`);
    tableHtml += '</tr></thead><tbody>';
    d.rows.slice(0, 5).forEach(row => {
        tableHtml += '<tr>';
        d.headers.forEach(h => tableHtml += `<td style="padding:6px;border:1px solid #e5e7eb;">${row[h] || ''}</td>`);
        tableHtml += '</tr>';
    });
    tableHtml += '</tbody></table>';
    if (d.total > 5) tableHtml += `<div style="font-size:11px;color:#666;margin-top:4px;">仅显示前5行，共${d.total}行</div>`;
    tableEl.innerHTML = tableHtml;
    const systemFields = [
        {key:'material_code', label:'物料编码'}, {key:'material_name', label:'物料名称 *'},
        {key:'specification', label:'规格型号'}, {key:'quantity', label:'数量'},
        {key:'unit', label:'单位'}, {key:'unit_price', label:'单价'}, {key:'remark', label:'备注'}
    ];
    // 字段别名列表（支持各种表头变体）
    const fieldAliases = {
        material_code: ['物料编码', '物料编号', '物料代码', '编码', '料号', '料号编码', '图号'],
        material_name: ['物料名称', '物料/设备名称', '名称', '品名', '设备名称', '物料描述'],
        specification: ['规格型号', '规格', '型号', '型号规格', '规格/型号', '规格参数', '技术规格'],
        quantity: ['数量', 'qty', '数量pcs'],
        unit: ['单位', '计量单位'],
        unit_price: ['单价', '价格', '单价元', '含税单价', '未税单价', '单价含税', '单价未税', '税前单价', '税后单价'],
        remark: ['备注', '说明', '备注说明', '用途']
    };
    // 规范化表头：去除括号及内容、空格、转小写
    function normalizeHeader(h) {
        return String(h).trim().replace(/[（(].*?[)）]/g, '').replace(/\s+/g, '').toLowerCase();
    }
    // 智能匹配：先精确匹配，再包含匹配
    function smartMatchField(header) {
        const norm = normalizeHeader(header);
        // 第一轮：精确匹配
        for (const [field, aliases] of Object.entries(fieldAliases)) {
            for (const alias of aliases) {
                if (norm === normalizeHeader(alias)) return field;
            }
        }
        // 第二轮：包含匹配（表头包含别名，或别名包含表头）
        for (const [field, aliases] of Object.entries(fieldAliases)) {
            for (const alias of aliases) {
                const normAlias = normalizeHeader(alias);
                if (norm.includes(normAlias) && normAlias.length >= 2) return field;
            }
        }
        return null;
    }
    // 先计算每个表头匹配到的字段
    const headerFieldMap = {};
    d.headers.forEach(h => {
        headerFieldMap[h] = smartMatchField(h);
    });
    let mappingHtml = '';
    systemFields.forEach(f => {
        mappingHtml += `<div><label style="font-size:11px;color:#666;">${f.label}</label><select id="map-inline-${f.key}-${projectId}" style="width:100%;padding:4px;border:1px solid #ddd;border-radius:4px;font-size:12px;margin-top:2px;"><option value="">-- 不导入 --</option>`;
        d.headers.forEach(h => {
            const selected = headerFieldMap[h] === f.key ? 'selected' : '';
            const matched = selected ? ' ✓' : '';
            mappingHtml += `<option value="${h}" ${selected}>${h}${matched}</option>`;
        });
        mappingHtml += '</select></div>';
    });
    mappingEl.innerHTML = mappingHtml;
}

async function confirmDelivExcelImportInline(projectId) {
    const d = _deliverableExcelPreview;
    if (!d) return;
    const fieldMap = {};
    ['material_code','material_name','specification','quantity','unit','unit_price','remark'].forEach(key => {
        const sel = document.getElementById('map-inline-' + key + '-' + projectId);
        if (sel && sel.value) fieldMap[key] = sel.value;
    });
    if (!fieldMap.material_name) { showToast('必须映射"物料名称"字段', 'warning'); return; }
    const items = d.rows.map(row => {
        const item = {};
        Object.keys(fieldMap).forEach(sysKey => {
            let val = row[fieldMap[sysKey]] || '';
            if (sysKey === 'quantity' || sysKey === 'unit_price') val = parseFloat(val) || (sysKey === 'quantity' ? 1 : null);
            item[sysKey] = val;
        });
        return item;
    }).filter(item => item.material_name);
    try {
        const r = await fetch(`${ENG_API}/wbs-projects/${projectId}/deliverables/batch`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({items})});
        const resp = await r.json();
        if (resp.success) {
            showToast(resp.msg);
            document.getElementById('deliv-excel-preview-inline-' + projectId).style.display = 'none';
            _deliverableExcelPreview = null;
            loadDelivListInline(projectId);
            loadProjectBoard();
        } else { showToast('导入失败：' + (resp.detail || ''), 'error'); }
    } catch(e) { showToast('导入失败：' + e.message, 'error'); }
}

function renderWbsTree(tree) {
    // 通用WBS层级标签
    const levelLabels = {1: '项目', 2: '子系统/工序', 3: '组件', 4: '任务'};
    const levelGuide = `<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px;margin-bottom:12px;font-size:12px;color:#475569;">
        📋 WBS层级结构：<b>第1级=项目</b> / <b>第2级=子系统或工序</b> / <b>第3级=组件</b> / <b>第4级=任务</b> · 按WBS节点归集成本和进度
       </div>`;
    if (!tree.length) return levelGuide + '<div class="empty">暂无WBS节点，请先创建WBS结构</div>';
    let html = levelGuide + `<table class="data-table"><thead><tr><th>层级</th><th>节点编号</th><th>节点名称</th><th>类型</th><th>人工预算</th><th>材料预算</th><th>外协预算</th><th>其他预算</th><th>总预算</th><th>已发生</th><th>进度</th><th>状态</th></tr></thead><tbody>`;
    function renderNode(node, indent) {
        const typeMap = {TASK:'任务', MILESTONE:'里程碑', COST_POINT:'成本点'};
        const budgetColor = node.budget_cost > 0 && node.incurred_cost > node.budget_cost ? '#e74c3c' : '#2c3e50';
        const levelLabel = levelLabels[node.level] || `第${node.level}级`;
        html += `<tr>
            <td><span style="background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:11px;color:#475569;">L${node.level} ${levelLabel}</span></td>
            <td>${'&nbsp;'.repeat(indent*4)}📁 ${node.node_code}</td>
            <td>${node.node_name}</td>
            <td><span class="badge badge-default">${typeMap[node.node_type]||node.node_type}</span></td>
            <td>¥${node.budget_labor.toLocaleString()}</td>
            <td>¥${node.budget_material.toLocaleString()}</td>
            <td>¥${node.budget_outsource.toLocaleString()}</td>
            <td>¥${node.budget_other.toLocaleString()}</td>
            <td style="color:${budgetColor};font-weight:600;">¥${node.budget_cost.toLocaleString()}</td>
            <td>¥${node.incurred_cost.toLocaleString()}</td>
            <td><div style="display:flex;align-items:center;gap:4px;"><div style="background:#ecf0f1;border-radius:4px;height:6px;width:60px;"><div style="background:#3498db;height:100%;width:${node.progress}%;"></div></div>${node.progress}%</div></td>
            <td>${node.status}</td>
        </tr>`;
        if (node.children) node.children.forEach(c => renderNode(c, indent+1));
    }
    tree.forEach(n => renderNode(n, 0));
    html += '</tbody></table>';
    return html;
}

async function renderCostForProject(projectId, el) {
    el.innerHTML = '<div class="empty">加载中...</div>';
    try {
        const r = await fetch(`${API}/cost-collections/summary?project_id=${projectId}`);
        const d = await r.json();
        let html = `<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px;">
            <div style="background:#f8f9fa;padding:16px;border-radius:8px;text-align:center;"><div style="font-size:12px;color:#7f8c8d;">累计成本</div><div style="font-size:22px;font-weight:600;color:#e74c3c;">¥${d.total_cost.toLocaleString()}</div></div>`;
        const colors = ['#3498db','#e74c3c','#f39c12','#9b59b6'];
        d.by_type.forEach((t, i) => {
            html += `<div style="background:#f8f9fa;padding:16px;border-radius:8px;text-align:center;"><div style="font-size:12px;color:#7f8c8d;">${t.cost_type}</div><div style="font-size:18px;font-weight:600;color:${colors[i%4]};">¥${t.amount.toLocaleString()}</div></div>`;
        });
        html += '</div>';
        if (d.warnings.length) {
            html += '<div style="margin-bottom:16px;">';
            d.warnings.forEach(w => {
                const color = w.level === '严重' ? '#e74c3c' : '#f39c12';
                html += `<div style="background:${color}15;border-left:4px solid ${color};padding:8px 12px;margin-bottom:6px;border-radius:4px;color:${color};">⚠️ ${w.msg}</div>`;
            });
            html += '</div>';
        }
        el.innerHTML = html;
    } catch(e) { el.innerHTML = '<div class="error">加载失败</div>'; }
}

async function renderRevenueForProject(projectId, el) {
    el.innerHTML = '<div class="empty">加载中...</div>';
    try {
        const r = await fetch(`${API}/revenue-recognitions/ledger?project_id=${projectId}`);
        const d = await r.json();
        if (!d.items.length) { el.innerHTML = '<div class="empty">暂无收入确认记录</div>'; return; }
        let html = `<table class="data-table"><thead><tr><th>确认日期</th><th>完工进度</th><th>应确认收入</th><th>累计确认</th><th>本次确认</th><th>已发生成本</th><th>毛利</th><th>毛利率</th></tr></thead><tbody>`;
        d.items.forEach(r => {
            html += `<tr>
                <td>${r.confirm_date}</td>
                <td><b>${r.progress_percent}%</b></td>
                <td>¥${r.total_revenue.toLocaleString()}</td>
                <td>¥${r.cumulative_revenue.toLocaleString()}</td>
                <td style="color:#27ae60;font-weight:600;">¥${r.current_revenue.toLocaleString()}</td>
                <td>¥${r.incurred_cost.toLocaleString()}</td>
                <td style="color:${r.gross_profit>=0?'#27ae60':'#e74c3c'};">¥${r.gross_profit.toLocaleString()}</td>
                <td>${r.gross_margin}%</td>
            </tr>`;
        });
        html += '</tbody></table>';
        el.innerHTML = html;
    } catch(e) { el.innerHTML = '<div class="error">加载失败</div>'; }
}

async function renderMilestonesForProject(projectId, el) {
    el.innerHTML = '<div class="empty">加载中...</div>';
    const guide = `<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px;margin-bottom:12px;font-size:12px;color:#475569;">
        🏁 项目里程碑：按项目进度节点定义（如设计评审→到货验收→安装完成→最终交付），用于跟踪项目关键节点
       </div>`;
    try {
        const r = await fetch(`${API}/milestones?project_id=${projectId}`);
        const d = await r.json();
        if (!d.items.length) { el.innerHTML = guide + '<div class="empty">暂无里程碑</div>'; return; }
        let html = guide + '<div style="display:flex;gap:8px;flex-wrap:wrap;">';
        d.items.forEach(m => {
            const color = m.status === 'ACHIEVED' ? '#27ae60' : m.status === 'IN_PROGRESS' ? '#f39c12' : '#95a5a6';
            html += `<div style="background:#fff;border:2px solid ${color};border-radius:8px;padding:12px;min-width:180px;">
                <div style="font-weight:600;">${m.name}</div>
                <div style="font-size:12px;color:#7f8c8d;margin:4px 0;">目标: ${m.target_progress}% / 实际: ${m.actual_progress}%</div>
                <div style="background:#ecf0f1;border-radius:4px;height:6px;"><div style="background:${color};height:100%;width:${m.actual_progress}%;border-radius:4px;"></div></div>
                <div style="font-size:11px;color:${color};margin-top:4px;">${m.status === 'ACHIEVED' ? '✅ 已达成' : '⏳ 进行中'}</div>
            </div>`;
        });
        html += '</div>';
        el.innerHTML = html;
    } catch(e) { el.innerHTML = '<div class="error">加载失败</div>'; }
}


// ==================== 模块2：BOM管理 ====================
function renderBomMgmt() {
    return `
        <div style="margin-bottom:16px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
            <button class="btn btn-primary" onclick="showBomForm()">➕ 新建BOM</button>
            <button class="btn btn-secondary" onclick="loadBomList()">🔄 刷新</button>
        </div>
        <div id="bom-list"></div>
        <div id="bom-detail" style="margin-top:20px;"></div>
    `;
}

async function loadBomList() {
    const el = document.getElementById('bom-list');
    if (!el) return;
    try {
        const r = await fetch(`${ENG_API}/bom-versions/`);
        const data = await r.json();
        if (!data.length) { el.innerHTML = '<div class="empty">暂无BOM，点击「新建BOM」开始</div>'; return; }
        let html = '<table class="data-table"><thead><tr><th>BOM编号</th><th>名称</th><th>产品</th><th>版本</th><th>类型</th><th>状态</th><th>明细数</th><th>操作</th></tr></thead><tbody>';
        data.forEach(b => {
            const typeBadge = b.bom_type === 'MBOM' ? 'badge-info' : 'badge-default';
            const statusBadge = b.status === 'ACTIVE' ? 'badge-success' : b.status === 'DRAFT' ? 'badge-warning' : 'badge-default';
            html += `<tr>
                <td>${b.bom_code || '-'}</td>
                <td>${b.name || '-'}</td>
                <td>${b.product_name || '-'}</td>
                <td><b>${b.version}</b></td>
                <td><span class="badge ${typeBadge}">${b.bom_type || 'EBOM'}</span></td>
                <td><span class="badge ${statusBadge}">${b.status === 'ACTIVE' ? '生效' : b.status === 'DRAFT' ? '草稿' : '失效'}</span></td>
                <td>${b.item_count}项</td>
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="viewBomDetail(${b.id})">查看</button>
                    <button class="btn btn-sm btn-info" onclick="bomCostRollup(${b.id})">成本卷积</button>
                </td>
            </tr>`;
        });
        html += '</tbody></table>';
        el.innerHTML = html;
    } catch(e) { el.innerHTML = '<div class="error">加载失败</div>'; }
}

async function viewBomDetail(bomId) {
    const el = document.getElementById('bom-detail');
    if (!el) return;
    el.innerHTML = '<div class="empty">加载中...</div>';
    try {
        const r = await fetch(`${API}/boms/${bomId}/items`);
        const d = await r.json();
        let html = `<div style="background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <h3 style="margin:0;">📋 ${d.bom.name || d.bom.bom_code} <span style="font-size:14px;color:#95a5a6;">V${d.bom.version} · ${d.bom.bom_type}</span></h3>
                <button class="btn btn-sm btn-secondary" onclick="document.getElementById('bom-detail').innerHTML=''">✕</button>
            </div>
            <table class="data-table"><thead><tr><th>物料编号</th><th>物料名称</th><th>规格</th><th>用量</th><th>单位</th><th>损耗率</th><th>类型</th><th>工序</th></tr></thead><tbody>`;
        d.items.forEach(i => {
            html += `<tr>
                <td>${i.material_code || '-'}</td>
                <td>${i.material_name || '-'}</td>
                <td>${i.spec || '-'}</td>
                <td>${i.quantity}</td>
                <td>${i.unit}</td>
                <td>${i.loss_rate}%</td>
                <td>${i.item_type === 'SELF' ? '自制' : i.item_type === 'OUTSOURCE' ? '外协' : '采购'}</td>
                <td>${i.process_name || '-'}</td>
            </tr>`;
        });
        html += '</tbody></table></div>';
        el.innerHTML = html;
    } catch(e) { el.innerHTML = '<div class="error">加载失败</div>'; }
}

function showBomForm() {
    const pid = prompt('请输入产品ID（物料ID）:', '1');
    if (!pid) return;
    const name = prompt('BOM名称:', '产品BOM');
    const version = prompt('版本号:', 'V1.0');
    const bomType = confirm('点击确定=EBOM工程BOM，取消=MBOM制造BOM') ? 'EBOM' : 'MBOM';
    fetch(`${API}/boms`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({product_id:parseInt(pid), name, version, bom_type:bomType, status:'DRAFT', items:[]})
    }).then(r=>r.json()).then(d=>{showToast('BOM创建成功：'+d.bom_code); loadBomList();});
}

function showBomCompare() {
    const id1 = prompt('请输入第一个BOM ID:');
    const id2 = prompt('请输入第二个BOM ID:');
    if (!id1 || !id2) return;
    fetch(`${API}/boms/compare`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({bom1_id:parseInt(id1), bom2_id:parseInt(id2)})})
        .then(r=>r.json()).then(d=>{
            if (!d.diffs.length) { showToast('两个BOM完全一致', 'info'); return; }
            let msg = `差异数: ${d.diff_count}\n\n`;
            d.diffs.forEach(x => {
                const tag = x.type === 'added' ? '[新增]' : x.type === 'removed' ? '[删除]' : '[修改]';
                msg += `${tag} ${x.material_name || '物料'} ${x.type === 'modified' ? JSON.stringify(x.changes) : '数量:'+x.quantity}\n`;
            });
            showToast(msg, 'info', 5000);
        });
}

function convertEbomToMbom() {
    const ebomId = prompt('请输入EBOM ID:');
    if (!ebomId) return;
    fetch(`${API}/boms/ebom-to-mbom`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({ebom_id:parseInt(ebomId)})})
        .then(r=>r.json()).then(d=>{showToast(d.message + '，MBOM ID: ' + d.id); loadBomList();});
}

function bomCostRollup(bomId) {
    fetch(`${API}/boms/${bomId}/cost-rollup`).then(r=>r.json()).then(d=>{
        let msg = `BOM成本卷积 - ${d.bom_code}\n\n材料成本: ¥${d.total_material_cost}\n人工成本: ¥${d.total_labor_cost}\n外协成本: ¥${d.total_outsource_cost}\n总成本: ¥${d.total_cost}`;
        showToast(msg, 'info', 5000);
    });
}


// ==================== 模块3：ECO变更管理 ====================
function renderEcoMgmt() {
    return `
        <div style="margin-bottom:16px;display:flex;gap:8px;align-items:center;">
            <button class="btn btn-primary" onclick="showEcoForm()">➕ 新建ECO变更</button>
            <button class="btn btn-secondary" onclick="loadEcoList()">🔄 刷新</button>
        </div>
        <div id="eco-list"></div>
        <div id="eco-detail" style="margin-top:20px;"></div>
    `;
}

async function loadEcoList() {
    const el = document.getElementById('eco-list');
    if (!el) return;
    try {
        const r = await fetch(`${ENG_API}/eco-orders/`);
        const data = await r.json();
        if (!data.length) { el.innerHTML = '<div class="empty">暂无ECO变更单</div>'; return; }
        let html = '<table class="data-table"><thead><tr><th>ECO单号</th><th>产品</th><th>变更类型</th><th>变更原因</th><th>旧版本</th><th>新版本</th><th>状态</th><th>操作</th></tr></thead><tbody>';
        data.forEach(o => {
            const statusMap = {DRAFT:'badge-default', PENDING:'badge-warning', APPROVED:'badge-info', IMPLEMENTED:'badge-success', REJECTED:'badge-danger'};
            const statusText = {DRAFT:'草稿', PENDING:'待审批', APPROVED:'已审批', IMPLEMENTED:'已执行', REJECTED:'已驳回'}[o.status] || o.status;
            let actions = `<button class="btn btn-sm btn-secondary" onclick="viewEcoDetail(${o.id})">详情</button>`;
            if (o.status === 'DRAFT') actions += ` <button class="btn btn-sm btn-secondary" onclick="submitEco(${o.id})">提交</button>`;
            if (o.status === 'PENDING') actions += ` <button class="btn btn-sm btn-primary" onclick="approveEco(${o.id})">审批</button>`;
            if (o.status === 'APPROVED') actions += ` <button class="btn btn-sm btn-success" onclick="implementEco(${o.id})">执行</button>`;
            html += `<tr>
                <td><b>${o.eco_no}</b></td>
                <td>${o.product_name || '-'}</td>
                <td>${o.change_type}</td>
                <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${o.change_reason||''}">${o.change_reason || '-'}</td>
                <td>${o.old_version || '-'}</td>
                <td>${o.new_version || '-'}</td>
                <td><span class="badge ${statusMap[o.status]||'badge-default'}">${statusText}</span></td>
                <td>${actions}</td>
            </tr>`;
        });
        html += '</tbody></table>';
        el.innerHTML = html;
    } catch(e) { el.innerHTML = '<div class="error">加载失败</div>'; }
}

async function viewEcoDetail(ecoId) {
    const el = document.getElementById('eco-detail');
    if (!el) return;
    el.innerHTML = '<div class="empty">加载中...</div>';
    try {
        const [r1, r2] = await Promise.all([
            fetch(`${API}/eco-orders/${ecoId}/impact-analysis`, {method:'POST'}),
            fetch(`${API}/eco-orders/${ecoId}/trail`)
        ]);
        const impact = await r1.json();
        const trail = await r2.json();
        let html = `<div style="background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                <h3 style="margin:0;">🔧 ECO变更详情 - ${trail.eco.eco_no}</h3>
                <button class="btn btn-sm btn-secondary" onclick="document.getElementById('eco-detail').innerHTML=''">✕</button>
            </div>
            <div style="margin-bottom:16px;padding:12px;background:#f8f9fa;border-radius:8px;">
                <div style="font-weight:600;margin-bottom:8px;">📋 申请信息</div>
                <div style="font-size:13px;display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                    <div>变更类型: ${trail.eco.change_type}</div>
                    <div>申请人: ${trail.eco.requested_by || '-'}</div>
                    <div>变更原因: ${trail.eco.change_reason || '-'}</div>
                    <div>状态: ${trail.eco.status}</div>
                </div>
            </div>
            <div style="margin-bottom:16px;">
                <div style="font-weight:600;margin-bottom:8px;">⚡ 影响范围分析（${impact.impact_count}项）</div>
                <table class="data-table"><thead><tr><th>影响类型</th><th>影响对象</th></tr></thead><tbody>`;
        (impact.impacts || []).forEach(i => {
            html += `<tr><td><span class="badge badge-warning">${i.impact_type}</span></td><td>${i.target_desc}</td></tr>`;
        });
        html += '</tbody></table></div>';
        html += `<div><div style="font-weight:600;margin-bottom:8px;">🔄 审批流程</div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;">`;
        (trail.approval_flow || []).forEach((step, i) => {
            html += `<div style="padding:6px 12px;background:#ecf0f1;border-radius:6px;font-size:13px;">${i+1}. ${step}</div>`;
        });
        html += '</div></div></div>';
        el.innerHTML = html;
    } catch(e) { el.innerHTML = '<div class="error">加载失败</div>'; }
}

function showEcoForm() {
    const productId = prompt('产品ID:', '1');
    if (!productId) return;
    const productName = prompt('产品名称:', '机械A');
    const reason = prompt('变更原因:');
    if (!reason) return;
    fetch(`${ENG_API}/eco-orders/`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({product_id:parseInt(productId), product_name:productName, change_reason:reason, change_type:'normal', change_content:[]})
    }).then(r=>r.json()).then(d=>{showToast('ECO创建成功：'+d.eco_no); loadEcoList();});
}

function submitEco(id) { fetch(`${ENG_API}/eco-orders/${id}/submit`, {method:'POST'}).then(r=>r.json()).then(d=>{showToast(d.message); loadEcoList();}); }
function approveEco(id) { if (!confirm('确认审批通过？')) return; fetch(`${ENG_API}/eco-orders/${id}/approve`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({effective_date:new Date().toISOString().slice(0,10)})}).then(r=>r.json()).then(d=>{showToast(d.message); loadEcoList();}); }
function implementEco(id) { if (!confirm('执行ECO将创建新BOM版本，确认？')) return; fetch(`${ENG_API}/eco-orders/${id}/implement`, {method:'POST'}).then(r=>r.json()).then(d=>{showToast(d.message); loadEcoList();}); }


// ==================== 模块4：生产排程 ====================
function renderScheduleMgmt() {
    return `
        <div style="margin-bottom:16px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
            <button class="btn btn-primary" onclick="showWoProcessForm()">➕ 新建工单工序</button>
            <button class="btn btn-warning" onclick="autoSchedule()">🤖 自动排程</button>
            <button class="btn btn-secondary" onclick="loadScheduleAll()">🔄 刷新</button>
        </div>
        <div style="display:grid;grid-template-columns:1fr 300px;gap:16px;">
            <div>
                <div style="background:#fff;border-radius:12px;padding:16px;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                    <h4 style="margin:0 0 12px;">📊 产能负荷</h4>
                    <div id="capacity-load"></div>
                </div>
                <div style="background:#fff;border-radius:12px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                    <h4 style="margin:0 0 12px;">📅 工单工序列表</h4>
                    <div id="wo-process-list"></div>
                </div>
            </div>
            <div style="background:#fff;border-radius:12px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                <h4 style="margin:0 0 12px;">⚠️ 排程预警</h4>
                <div id="schedule-warnings"></div>
            </div>
        </div>
    `;
}

async function loadScheduleAll() {
    const [woR, capR, warnR] = await Promise.all([
        fetch(`${API}/work-order-processes`),
        fetch(`${API}/schedule/capacity-load`),
        fetch(`${API}/schedule/warnings`)
    ]);
    const wo = await woR.json();
    const cap = await capR.json();
    const warn = await warnR.json();
    // 产能负荷
    const capEl = document.getElementById('capacity-load');
    if (capEl) {
        if (!cap.items.length) { capEl.innerHTML = '<div class="empty">暂无产能数据</div>'; }
        else {
            capEl.innerHTML = cap.items.map(c => {
                const color = c.overload ? '#e74c3c' : c.load_rate > 80 ? '#f39c12' : '#27ae60';
                return `<div style="margin-bottom:8px;">
                    <div style="display:flex;justify-content:space-between;font-size:13px;"><span>${c.work_center}</span><span style="color:${color};font-weight:600;">${c.load_rate}%</span></div>
                    <div style="background:#ecf0f1;border-radius:4px;height:8px;"><div style="background:${color};height:100%;width:${Math.min(c.load_rate,100)}%;border-radius:4px;"></div></div>
                    <div style="font-size:11px;color:#95a5a6;margin-top:2px;">${c.planned_hours}h / ${c.capacity_hours}h</div>
                </div>`;
            }).join('');
        }
    }
    // 工单列表
    const woEl = document.getElementById('wo-process-list');
    if (woEl) {
        if (!wo.total) { woEl.innerHTML = '<div class="empty">暂无工单工序</div>'; }
        else {
            let html = '<table class="data-table"><thead><tr><th>工单号</th><th>工序</th><th>工作中心</th><th>计划开始</th><th>计划结束</th><th>数量</th><th>状态</th></tr></thead><tbody>';
            wo.items.forEach(p => {
                const statusBadge = {PENDING:'badge-default', SCHEDULED:'badge-info', RUNNING:'badge-warning', COMPLETED:'badge-success'}[p.status] || 'badge-default';
                html += `<tr>
                    <td>${p.work_order_no}</td><td>${p.process_name}</td><td>${p.work_center || '-'}</td>
                    <td>${p.plan_start || '-'}</td><td>${p.plan_end || '-'}</td><td>${p.quantity}</td>
                    <td><span class="badge ${statusBadge}">${p.status}</span></td>
                </tr>`;
            });
            html += '</tbody></table>';
            woEl.innerHTML = html;
        }
    }
    // 预警
    const warnEl = document.getElementById('schedule-warnings');
    if (warnEl) {
        let html = '';
        if (warn.overdue.length) {
            html += '<div style="margin-bottom:12px;"><div style="color:#e74c3c;font-weight:600;margin-bottom:4px;">🔴 即将逾期</div>';
            warn.overdue.forEach(w => html += `<div style="font-size:12px;padding:4px 0;">${w.work_order_no} - ${w.process_name}</div>`);
            html += '</div>';
        }
        if (warn.today_start.length) {
            html += '<div style="margin-bottom:12px;"><div style="color:#f39c12;font-weight:600;margin-bottom:4px;">🟡 今日开工</div>';
            warn.today_start.forEach(w => html += `<div style="font-size:12px;padding:4px 0;">${w.work_order_no} - ${w.process_name} (${w.work_center||'-'})</div>`);
            html += '</div>';
        }
        if (warn.bottleneck.length) {
            html += '<div><div style="color:#e67e22;font-weight:600;margin-bottom:4px;">🟠 产能瓶颈</div>';
            warn.bottleneck.forEach(w => html += `<div style="font-size:12px;padding:4px 0;">${w.work_center} 负荷${w.load_rate}%</div>`);
            html += '</div>';
        }
        if (!html) html = '<div class="empty">暂无预警</div>';
        warnEl.innerHTML = html;
    }
}

function showWoProcessForm() {
    const woNo = prompt('工单号:'); if (!woNo) return;
    const processName = prompt('工序名称:', '组装'); if (!processName) return;
    const wc = prompt('工作中心:', '装配车间');
    const start = prompt('计划开始 (YYYY-MM-DDTHH:MM):', new Date().toISOString().slice(0,16));
    const end = prompt('计划结束 (YYYY-MM-DDTHH:MM):', new Date(Date.now()+8*3600*1000).toISOString().slice(0,16));
    fetch(`${API}/work-order-processes`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({
        work_order_no: woNo, process_name: processName, work_center: wc,
        plan_start: start, plan_end: end, quantity: 100, status: 'PENDING'
    })}).then(r=>r.json()).then(()=>loadScheduleAll());
}

function autoSchedule() {
    fetch(`${API}/schedule/auto`, {method:'POST'}).then(r=>r.json()).then(d=>{
        let msg = `排程完成: ${d.scheduled}个工单已排程\n`;
        if (d.conflicts.length) {
            msg += `\n⚠️ 发现${d.conflicts.length}个冲突:\n`;
            d.conflicts.forEach(c => msg += `- ${c.work_order_no}: ${c.suggestion}\n`);
        }
        showToast(msg, 'info', 5000);
        loadScheduleAll();
    });
}


// ==================== 模块5：WBS成本归集 ====================
function renderCostMgmt() {
    const guide = `<div style="background:linear-gradient(135deg,#f8fafc,#f1f5f9);border:1px solid #e2e8f0;border-radius:10px;padding:14px;margin-bottom:16px;">
        <div style="font-size:13px;color:#475569;font-weight:600;">💰 项目成本归集</div>
        <div style="font-size:12px;color:#64748b;margin-top:4px;">按<b>WBS节点</b>归集成本，四路径自动归集：材料、人工、外协、其他。<br>
        <span style="color:#dc2626;font-weight:600;">⚠️ 成本预警机制：</span>节点超预算110%<span style="color:#d97706;">黄色预警</span>，超120%<span style="color:#dc2626;">红色预警</span>，项目总成本超合同80%全项目预警。</div>
       </div>`;
    return `
        ${guide}
        <div style="margin-bottom:16px;display:flex;gap:8px;align-items:center;">
            <select id="cost-project-select" style="padding:8px;border:1px solid #ddd;border-radius:6px;" onchange="loadCostSummary()">
                <option value="">选择${isA?'批次':'合同项目'}查看成本</option>
            </select>
            <button class="btn btn-primary" onclick="showCostCollectionForm()">➕ 成本归集</button>
            <button class="btn btn-secondary" onclick="loadCostSummary()">🔄 刷新</button>
        </div>
        <div id="cost-summary"></div>
    `;
}

async function loadCostMgmt() {
    // 加载项目列表
    try {
        const r = await fetch(`${ENG_API}/wbs-projects/`);
        const projects = await r.json();
        const sel = document.getElementById('cost-project-select');
        if (sel && projects.length) {
            projects.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.id; opt.textContent = `${p.project_no} - ${p.project_name}`;
                sel.appendChild(opt);
            });
        }
    } catch(e) {}
    loadCostSummary();
}

async function loadCostSummary() {
    const el = document.getElementById('cost-summary');
    if (!el) return;
    const pid = document.getElementById('cost-project-select').value;
    if (!pid) { el.innerHTML = '<div class="empty">请选择项目查看成本汇总</div>'; return; }
    el.innerHTML = '<div class="empty">加载中...</div>';
    try {
        const r = await fetch(`${API}/cost-collections/summary?project_id=${pid}`);
        const d = await r.json();
        let html = `<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:16px;">
            <div style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:20px;border-radius:12px;text-align:center;">
                <div style="font-size:13px;opacity:0.9;">累计成本</div>
                <div style="font-size:26px;font-weight:700;">¥${d.total_cost.toLocaleString()}</div>
            </div>`;
        const colors = ['#e74c3c','#f39c12','#3498db','#27ae60'];
        d.by_type.forEach((t, i) => {
            html += `<div style="background:#fff;padding:16px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.08);border-top:4px solid ${colors[i%4]};">
                <div style="font-size:13px;color:#7f8c8d;">${t.cost_type}</div>
                <div style="font-size:20px;font-weight:600;color:${colors[i%4]};">¥${t.amount.toLocaleString()}</div>
            </div>`;
        });
        html += '</div>';
        // 饼图（CSS实现）
        if (d.by_type.length) {
            html += `<div style="background:#fff;padding:20px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.08);margin-bottom:16px;">
                <h4 style="margin:0 0 12px;">🥧 成本类型占比</h4>
                <div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap;">`;
            let cumulative = 0;
            d.by_type.forEach((t, i) => {
                const pct = d.total_cost > 0 ? t.amount / d.total_cost * 100 : 0;
                html += `<div style="display:flex;align-items:center;gap:6px;font-size:13px;">
                    <div style="width:14px;height:14px;border-radius:3px;background:${colors[i%4]};"></div>
                    ${t.cost_type}: ${pct.toFixed(1)}%
                </div>`;
            });
            html += '</div></div>';
        }
        // 预警 - 后端预警
        if (d.warnings.length) {
            html += '<div style="margin-bottom:16px;">';
            d.warnings.forEach(w => {
                const color = w.level === '严重' ? '#e74c3c' : '#f39c12';
                html += `<div style="background:${color}15;border-left:4px solid ${color};padding:12px;margin-bottom:8px;border-radius:6px;color:${color};font-weight:500;">⚠️ ${w.msg}</div>`;
            });
            html += '</div>';
        }
        // V3成本预警机制：超预算110%黄色/120%红色/超合同80%全项目预警（所有项目通用）
        if (d.budget_cost > 0) {
            const budget = parseFloat(d.budget_cost) || 0;
            const contract = parseFloat(d.contract_amount) || 0;
            const totalCost = parseFloat(d.total_cost) || 0;
            const overBudgetPct = budget > 0 ? (totalCost / budget * 100) : 0;
            const contractUsePct = contract > 0 ? (totalCost / contract * 100) : 0;
            let alerts = [];
            if (overBudgetPct >= 120) alerts.push({color:'#dc2626', msg:`🔴 红色预警：成本已超预算 ${overBudgetPct.toFixed(1)}%（阈值120%），请立即核查！`});
            else if (overBudgetPct >= 110) alerts.push({color:'#d97706', msg:`🟡 黄色预警：成本已超预算 ${overBudgetPct.toFixed(1)}%（阈值110%），请关注成本控制。`});
            if (contractUsePct >= 80) alerts.push({color:'#dc2626', msg:`🔴 全项目预警：总成本已达合同额 ${contractUsePct.toFixed(1)}%（阈值80%），项目盈利告急！`});
            if (alerts.length) {
                html += '<div style="margin-bottom:16px;">';
                alerts.forEach(a => {
                    html += `<div style="background:${a.color}15;border-left:4px solid ${a.color};padding:12px;margin-bottom:8px;border-radius:6px;color:${a.color};font-weight:600;">${a.msg}</div>`;
                });
                html += '</div>';
            }
        }
        el.innerHTML = html;
    } catch(e) { el.innerHTML = '<div class="error">加载失败</div>'; }
}

function showCostCollectionForm() {
    const pid = document.getElementById('cost-project-select').value;
    if (!pid) { showToast('请先选择项目', 'warning'); return; }
    const type = prompt('成本类型 (材料/人工/外协/其他):', '材料');
    if (!type) return;
    const amount = prompt('金额:', '1000');
    if (!amount) return;
    const sourceType = prompt('来源 (采购/报工/外协/报销):', '采购');
    fetch(`${API}/cost-collections`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({
        project_id: parseInt(pid), cost_type: type, amount: parseFloat(amount), source_type: sourceType
    })}).then(r=>r.json()).then(d=>{showToast('成本归集成功：¥'+d.amount); loadCostSummary();});
}


// ==================== 模块6：收入确认 ====================
function renderRevenueMgmt() {
    const revMethod = localStorage.getItem('erp_revenue_method') || 'percentage_of_completion';
    const isPoc = revMethod === 'percentage_of_completion';
    const guide = isPoc
        ? `<div style="background:linear-gradient(135deg,#faf5ff,#ede9fe);border:1px solid #e9d5ff;border-radius:10px;padding:14px;margin-bottom:16px;">
            <div style="font-size:13px;color:#7c3aed;font-weight:600;">📊 完工百分比法（当前已启用）</div>
            <div style="font-size:12px;color:#64748b;margin-top:4px;">完工进度 = 累计实际成本 ÷ 预计总成本 × 100%。里程碑式触发收入确认，每次里程碑达成自动按进度确认收入。适合项目制合同、周期长、按进度收款。</div>
           </div>`
        : `<div style="background:linear-gradient(135deg,#eff6ff,#dbeafe);border:1px solid #bfdbfe;border-radius:10px;padding:14px;margin-bottom:16px;">
            <div style="font-size:13px;color:#1e40af;font-weight:600;">📦 按出库确认（当前已启用）</div>
            <div style="font-size:12px;color:#64748b;margin-top:4px;">成品入库 → 发货 → 确认收入（标准方式）。适合大批量生产、现货销售、短周期。里程碑仅作进度跟踪，不触发收入确认。</div>
           </div>`;
    return `
        ${guide}
        <div style="margin-bottom:16px;display:flex;gap:8px;align-items:center;">
            <select id="rev-project-select" style="padding:8px;border:1px solid #ddd;border-radius:6px;" onchange="loadRevenueSummary()">
                <option value="">选择项目</option>
            </select>
            <button class="btn btn-primary" onclick="showRevenueForm()">➕ 确认收入</button>
            <button class="btn btn-secondary" onclick="showMilestoneForm()">🏁 新建里程碑</button>
            <button class="btn btn-secondary" onclick="loadRevenueSummary()">🔄 刷新</button>
        </div>
        <div id="revenue-summary"></div>
    `;
}

async function loadRevenueMgmt() {
    try {
        const r = await fetch(`${ENG_API}/wbs-projects/`);
        const projects = await r.json();
        const sel = document.getElementById('rev-project-select');
        if (sel && projects.length) {
            projects.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.id; opt.textContent = `${p.project_no} - ${p.project_name}`;
                sel.appendChild(opt);
            });
        }
    } catch(e) {}
    loadRevenueSummary();
}

async function loadRevenueSummary() {
    const el = document.getElementById('revenue-summary');
    if (!el) return;
    const pid = document.getElementById('rev-project-select').value;
    if (!pid) { el.innerHTML = '<div class="empty">请选择项目查看收入确认</div>'; return; }
    el.innerHTML = '<div class="empty">加载中...</div>';
    try {
        const [revR, milR] = await Promise.all([
            fetch(`${API}/revenue-recognitions/ledger?project_id=${pid}`),
            fetch(`${API}/milestones?project_id=${pid}`)
        ]);
        const rev = await revR.json();
        const mil = await milR.json();
        let html = `<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:16px;">
            <div style="background:linear-gradient(135deg,#11998e,#38ef7d);color:#fff;padding:20px;border-radius:12px;text-align:center;">
                <div style="font-size:13px;opacity:0.9;">累计收入</div>
                <div style="font-size:26px;font-weight:700;">¥${rev.total_revenue.toLocaleString()}</div>
            </div>
            <div style="background:linear-gradient(135deg,#f093fb,#f5576c);color:#fff;padding:20px;border-radius:12px;text-align:center;">
                <div style="font-size:13px;opacity:0.9;">累计毛利</div>
                <div style="font-size:26px;font-weight:700;">¥${rev.total_gross_profit.toLocaleString()}</div>
            </div>
            <div style="background:linear-gradient(135deg,#4facfe,#00f2fe);color:#fff;padding:20px;border-radius:12px;text-align:center;">
                <div style="font-size:13px;opacity:0.9;">确认次数</div>
                <div style="font-size:26px;font-weight:700;">${rev.total_records}</div>
            </div>
        </div>`;
        // 里程碑进度条
        if (mil.items.length) {
            html += `<div style="background:#fff;padding:20px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.08);margin-bottom:16px;">
                <h4 style="margin:0 0 12px;">🏁 里程碑进度</h4>
                <div style="display:flex;gap:12px;flex-wrap:wrap;">`;
            mil.items.forEach(m => {
                const color = m.status === 'ACHIEVED' ? '#27ae60' : '#3498db';
                html += `<div style="flex:1;min-width:200px;padding:12px;border:2px solid ${color};border-radius:8px;">
                    <div style="font-weight:600;">${m.name}</div>
                    <div style="font-size:12px;color:#7f8c8d;margin:4px 0;">目标${m.target_progress}%</div>
                    <div style="background:#ecf0f1;border-radius:4px;height:8px;"><div style="background:${color};height:100%;width:${m.actual_progress}%;border-radius:4px;"></div></div>
                    <div style="text-align:right;font-size:11px;color:${color};margin-top:4px;">${m.actual_progress}%</div>
                    ${m.status !== 'ACHIEVED' ? `<button class="btn btn-sm btn-success" style="margin-top:8px;" onclick="achieveMilestone(${m.id})">达成</button>` : '<div style="color:#27ae60;font-size:12px;margin-top:8px;">✅ 已达成</div>'}
                </div>`;
            });
            html += '</div></div>';
        }
        // 收入台账
        if (rev.items.length) {
            html += `<div style="background:#fff;padding:20px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                <h4 style="margin:0 0 12px;">📊 收入确认台账</h4>
                <table class="data-table"><thead><tr><th>日期</th><th>进度</th><th>应确认收入</th><th>累计确认</th><th>本次确认</th><th>毛利</th><th>毛利率</th></tr></thead><tbody>`;
            rev.items.forEach(r => {
                html += `<tr>
                    <td>${r.confirm_date}</td><td><b>${r.progress_percent}%</b></td>
                    <td>¥${r.total_revenue.toLocaleString()}</td><td>¥${r.cumulative_revenue.toLocaleString()}</td>
                    <td style="color:#27ae60;font-weight:600;">¥${r.current_revenue.toLocaleString()}</td>
                    <td style="color:${r.gross_profit>=0?'#27ae60':'#e74c3c'};">¥${r.gross_profit.toLocaleString()}</td>
                    <td>${r.gross_margin}%</td>
                </tr>`;
            });
            html += '</tbody></table></div>';
        }
        el.innerHTML = html;
    } catch(e) { el.innerHTML = '<div class="error">加载失败</div>'; }
}

function showRevenueForm() {
    const pid = document.getElementById('rev-project-select').value;
    if (!pid) { showToast('请先选择项目', 'warning'); return; }
    const progress = prompt('完工进度 (%)', '50');
    if (!progress) return;
    fetch(`${API}/revenue-recognitions`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({
        project_id: parseInt(pid), progress_percent: parseFloat(progress)
    })}).then(r=>r.json()).then(d=>{showToast(`收入确认成功！进度: ${d.progress}%，本次确认: ¥${d.current_revenue}`); loadRevenueSummary();});
}

function showMilestoneForm() {
    const pid = document.getElementById('rev-project-select').value;
    if (!pid) { showToast('请先选择项目', 'warning'); return; }
    const name = prompt('里程碑名称:', '设计完成'); if (!name) return;
    const target = prompt('目标进度 (%)', '30'); if (!target) return;
    fetch(`${API}/milestones`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({
        project_id: parseInt(pid), name, target_progress: parseFloat(target)
    })}).then(r=>r.json()).then(()=>{showToast('里程碑创建成功'); loadRevenueSummary();});
}

function achieveMilestone(id) {
    fetch(`${API}/milestones/${id}/achieve`, {method:'PUT'}).then(r=>r.json()).then(d=>{showToast('里程碑已达成！触发收入确认'); loadRevenueSummary();});
}


// ==================== 模块7：设备质量 ====================
function renderEquipmentQuality() {
    return `
        <div class="finance-tabs" style="margin-bottom:16px;">
            <button class="finance-tab active" onclick="renderEqTab(event,'equipment')">⚙️ 设备看板</button>
            <button class="finance-tab" onclick="renderEqTab(event,'downtime')">⏸️ 停机管理</button>
            <button class="finance-tab" onclick="renderEqTab(event,'quality')">🔍 质量管理</button>
        </div>
        <div id="eqq-content"></div>
    `;
}

function renderEqTab(ev, tab) {
    if (ev) {
        ev.target.parentElement.querySelectorAll('.finance-tab').forEach(b=>b.classList.remove('active'));
        ev.target.classList.add('active');
    }
    const content = document.getElementById('eqq-content');
    if (tab === 'equipment') loadEquipmentDashboard(content);
    else if (tab === 'downtime') loadDowntimeStats(content);
    else if (tab === 'quality') loadQualityDashboard(content);
}

async function loadEquipmentDashboard(el) {
    el.innerHTML = '<div class="empty">加载中...</div>';
    try {
        const r = await fetch(`${API}/equipments/dashboard`);
        const d = await r.json();
        const statusColors = {RUNNING:'#27ae60', IDLE:'#e74c3c', MAINTENANCE:'#f39c12', SCRAPPED:'#95a5a6'};
        let html = `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px;">
            <div style="background:#fff;padding:16px;border-radius:12px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.08);"><div style="font-size:13px;color:#7f8c8d;">设备总数</div><div style="font-size:24px;font-weight:600;">${d.total}</div></div>
            <div style="background:#fff;padding:16px;border-radius:12px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.08);border-top:3px solid #27ae60;"><div style="font-size:13px;color:#7f8c8d;">运行中</div><div style="font-size:24px;font-weight:600;color:#27ae60;">${d.status_counts.RUNNING}</div></div>
            <div style="background:#fff;padding:16px;border-radius:12px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.08);border-top:3px solid #e74c3c;"><div style="font-size:13px;color:#7f8c8d;">停机</div><div style="font-size:24px;font-weight:600;color:#e74c3c;">${d.status_counts.IDLE}</div></div>
            <div style="background:#fff;padding:16px;border-radius:12px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.08);border-top:3px solid #f39c12;"><div style="font-size:13px;color:#7f8c8d;">维护中</div><div style="font-size:24px;font-weight:600;color:#f39c12;">${d.status_counts.MAINTENANCE}</div></div>
        </div>`;
        html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin-bottom:16px;">';
        d.equipments.forEach(e => {
            const color = statusColors[e.status] || '#95a5a6';
            html += `<div style="background:#fff;border-radius:12px;padding:16px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <div style="font-weight:600;">${e.name}</div>
                    <div style="width:12px;height:12px;border-radius:50%;background:${color};box-shadow:0 0 8px ${color};"></div>
                </div>
                <div style="font-size:12px;color:#7f8c8d;margin-bottom:8px;">${e.code} · ${e.work_center || '-'}</div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:12px;">
                    <div>OEE: <b>${e.oee}%</b></div><div>可用率: ${e.availability}%</div>
                    <div>性能率: ${e.performance}%</div><div>合格率: ${e.quality_rate}%</div>
                </div>
            </div>`;
        });
        html += '</div>';
        // 停机TOP5
        if (d.downtime_top5.length) {
            html += `<div style="background:#fff;padding:20px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                <h4 style="margin:0 0 12px;">🔴 停机原因TOP5</h4>`;
            d.downtime_top5.forEach((t, i) => {
                const pct = d.downtime_top5[0].duration > 0 ? t.duration / d.downtime_top5[0].duration * 100 : 0;
                html += `<div style="margin-bottom:8px;">
                    <div style="display:flex;justify-content:space-between;font-size:13px;"><span>${i+1}. ${t.reason}</span><span>${t.duration}分钟 (${t.count}次)</span></div>
                    <div style="background:#ecf0f1;border-radius:4px;height:6px;"><div style="background:#e74c3c;height:100%;width:${pct}%;border-radius:4px;"></div></div>
                </div>`;
            });
            html += '</div>';
        }
        el.innerHTML = html;
    } catch(e) { el.innerHTML = '<div class="error">加载失败</div>'; }
}

async function loadDowntimeStats(el) {
    el.innerHTML = '<div class="empty">加载中...</div>';
    try {
        const r = await fetch(`${API}/downtimes/stats`);
        const d = await r.json();
        let html = `<div style="background:#fff;padding:20px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.08);margin-bottom:16px;">
            <h4 style="margin:0 0 12px;">⏸️ 停机统计</h4>
            <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:16px;">
                <div style="background:#f8f9fa;padding:12px;border-radius:8px;text-align:center;"><div style="font-size:12px;color:#7f8c8d;">停机次数</div><div style="font-size:20px;font-weight:600;">${d.total_count}</div></div>
                <div style="background:#f8f9fa;padding:12px;border-radius:8px;text-align:center;"><div style="font-size:12px;color:#7f8c8d;">总停机时长(分钟)</div><div style="font-size:20px;font-weight:600;color:#e74c3c;">${d.total_duration}</div></div>
            </div>
            <h5 style="margin:0 0 8px;">按原因统计</h5>`;
        d.by_reason.forEach(t => {
            html += `<div style="margin-bottom:6px;">
                <div style="display:flex;justify-content:space-between;font-size:13px;"><span>${t.reason}</span><span>${t.count}次 / ${t.duration}分钟</span></div>
            </div>`;
        });
        html += '</div>';
        el.innerHTML = html;
    } catch(e) { el.innerHTML = '<div class="error">加载失败</div>'; }
}

async function loadQualityDashboard(el) {
    el.innerHTML = '<div class="empty">加载中...</div>';
    try {
        const r = await fetch(`${API}/quality/dashboard`);
        const d = await r.json();
        let html = `<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px;">
            <div style="background:#fff;padding:16px;border-radius:12px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.08);"><div style="font-size:13px;color:#7f8c8d;">总检验数</div><div style="font-size:24px;font-weight:600;">${d.total_inspections}</div></div>`;
        d.by_type.forEach(t => {
            const color = t.pass_rate >= 95 ? '#27ae60' : t.pass_rate >= 80 ? '#f39c12' : '#e74c3c';
            html += `<div style="background:#fff;padding:16px;border-radius:12px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.08);border-top:3px solid ${color};">
                <div style="font-size:13px;color:#7f8c8d;">${t.type}</div>
                <div style="font-size:20px;font-weight:600;color:${color};">${t.pass_rate}%</div>
                <div style="font-size:11px;color:#95a5a6;">${t.pass}/${t.total}</div>
            </div>`;
        });
        html += '</div>';
        if (d.fail_top5.length) {
            html += `<div style="background:#fff;padding:20px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                <h4 style="margin:0 0 12px;">🔴 不良原因TOP5</h4>
                <table class="data-table"><thead><tr><th>排名</th><th>不良原因</th><th>次数</th></tr></thead><tbody>`;
            d.fail_top5.forEach((t, i) => {
                html += `<tr><td>${i+1}</td><td>${t.reason}</td><td>${t.count}</td></tr>`;
            });
            html += '</tbody></table></div>';
        } else {
            html += '<div class="empty">暂无不良记录</div>';
        }
        el.innerHTML = html;
    } catch(e) { el.innerHTML = '<div class="error">加载失败</div>'; }
}

// ==================== 采购需求池（采购部门入口）====================
async function renderProcurementPool(el) {
    el.innerHTML = '<div class="empty">加载中...</div>';
    try {
        const r = await fetch(ENG_API + '/procurement/pool');
        const tasks = await r.json();
        if (!tasks || !tasks.length) {
            el.innerHTML = '<div style="text-align:center;padding:40px;color:#999;"><div style="font-size:48px;margin-bottom:12px;">🛒</div><div style="font-size:15px;">采购需求池为空</div><div style="font-size:13px;">生产部门下发原材料需求后，将在此处显示</div></div>';
            return;
        }
        let html = '<div style="margin-bottom:16px;"><h3 style="margin:0 0 12px 0;">🛒 采购需求池（' + tasks.length + '项）</h3></div>';
        tasks.forEach(t => {
            const statusColors = {
                'PROCUREMENT_DISPATCHED': 'background:#fef3c7;color:#92400e',
                'PURCHASING': 'background:#dbeafe;color:#1e40af',
                'COMPLETED': 'background:#dcfce7;color:#166534'
            };
            const statusLabels = {
                'PROCUREMENT_DISPATCHED': '待采购',
                'PURCHASING': '采购中',
                'COMPLETED': '已完成'
            };
            html += '<div style="background:#fff;border-radius:8px;padding:16px;margin-bottom:12px;border:1px solid #e5e7eb;">';
            html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">';
            html += '<div><span style="font-weight:600;font-size:14px;">' + t.project_name + '</span> <span style="font-size:12px;color:#999;margin-left:8px;">' + t.project_no + '</span></div>';
            html += '<span style="padding:2px 8px;border-radius:4px;font-size:11px;' + statusColors[t.status] + ';">' + statusLabels[t.status] + '</span>';
            html += '</div>';
            html += '<div style="font-size:12px;color:#666;margin-bottom:8px;">派工单号：' + t.task_no + ' | 下发时间：' + (t.dispatched_at || '-') + ' | 物料：' + t.material_count + '项 | 预估金额：¥' + t.total_amount.toLocaleString() + '</div>';
            html += '<table style="width:100%;border-collapse:collapse;font-size:12px;"><thead><tr style="background:#f8fafc;"><th style="padding:6px;text-align:left;border-bottom:1px solid #e5e7eb;">物料编码</th><th style="padding:6px;text-align:left;border-bottom:1px solid #e5e7eb;">物料名称</th><th style="padding:6px;text-align:left;border-bottom:1px solid #e5e7eb;">规格</th><th style="padding:6px;text-align:right;border-bottom:1px solid #e5e7eb;">数量</th><th style="padding:6px;text-align:left;border-bottom:1px solid #e5e7eb;">单位</th><th style="padding:6px;text-align:right;border-bottom:1px solid #e5e7eb;">单价</th><th style="padding:6px;text-align:center;border-bottom:1px solid #e5e7eb;">采购状态</th></tr></thead><tbody>';
            t.materials.forEach(m => {
                const pStatusColors = {'PENDING':'background:#fef3c7;color:#92400e','PURCHASING':'background:#dbeafe;color:#1e40af','ARRIVED':'background:#dcfce7;color:#166534','CANCELLED':'background:#f3f4f6;color:#6b7280'};
                html += '<tr style="border-bottom:1px solid #f3f4f6;">';
                html += '<td style="padding:6px;">' + (m.material_code || '-') + '</td>';
                html += '<td style="padding:6px;font-weight:500;">' + m.material_name + '</td>';
                html += '<td style="padding:6px;color:#666;">' + (m.specification || '-') + '</td>';
                html += '<td style="padding:6px;text-align:right;">' + m.quantity + '</td>';
                html += '<td style="padding:6px;">' + m.unit + '</td>';
                html += '<td style="padding:6px;text-align:right;">' + (m.unit_price ? '¥' + m.unit_price.toLocaleString() : '-') + '</td>';
                html += '<td style="padding:6px;text-align:center;"><select onchange="updatePurchaseStatus(' + m.id + ', this.value)" style="padding:2px 6px;border-radius:4px;border:1px solid #ddd;font-size:11px;cursor:pointer;' + pStatusColors[m.purchase_status] + '"><option value="PENDING"' + (m.purchase_status==='PENDING'?' selected':'') + '>待采购</option><option value="PURCHASING"' + (m.purchase_status==='PURCHASING'?' selected':'') + '>采购中</option><option value="ARRIVED"' + (m.purchase_status==='ARRIVED'?' selected':'') + '>已到货</option><option value="CANCELLED"' + (m.purchase_status==='CANCELLED'?' selected':'') + '>已取消</option></select></td>';
                html += '</tr>';
            });
            html += '</tbody></table></div>';
        });
        el.innerHTML = html;
    } catch(e) { el.innerHTML = '<div class="error">加载失败：' + e.message + '</div>'; }
}

async function updatePurchaseStatus(reqId, newStatus) {
    try {
        const r = await fetch(ENG_API + '/material-requirements/' + reqId + '/purchase-status', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({purchase_status: newStatus})
        });
        const d = await r.json();
        if (d.success) {
            showToast('采购状态已更新');
            renderProcurementPool(document.getElementById('content'));
        } else {
            showToast('更新失败：' + (d.detail || ''), 'error');
        }
    } catch(e) {
        showToast('更新失败：' + e.message, 'error');
    }
}

// ==================== 截图OCR识别录入（方案B）====================
let _ocrParsedItems = []; // OCR解析出的物料列表
let _ocrOriginalText = ''; // OCR原始文本

function showOcrCaptureModal(taskId) {
    _ocrParsedItems = [];
    _ocrOriginalText = '';
    let modal = document.getElementById('ocr-modal');
    if (modal) modal.remove();
    modal = document.createElement('div');
    modal.id = 'ocr-modal';
    modal.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    modal.innerHTML = `
        <div style="background:#fff;border-radius:12px;padding:24px;width:90%;max-width:800px;max-height:90vh;overflow:auto;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                <h3 style="margin:0;font-size:18px;">📷 截图识别录入</h3>
                <button onclick="closeOcrModal()" style="background:none;border:none;font-size:24px;cursor:pointer;color:#999;">×</button>
            </div>
            <div id="ocr-upload-area" style="border:2px dashed #d1d5db;border-radius:8px;padding:32px;text-align:center;cursor:pointer;margin-bottom:16px;" onclick="document.getElementById('ocr-file-input').click()" ondragover="event.preventDefault();this.style.background='#f0f9ff';this.style.borderColor='#3b82f6';" ondragleave="this.style.background='';this.style.borderColor='#d1d5db';" ondrop="event.preventDefault();this.style.background='';this.style.borderColor='#d1d5db';const f=event.dataTransfer.files[0];if(f){const e={target:{files:[f],value:''}};handleOcrImageUpload(e, ${taskId});}">
                <div style="font-size:48px;margin-bottom:8px;">🖼️</div>
                <div style="font-size:14px;color:#666;">点击选择截图文件，或拖拽图片到此处</div>
                <div style="font-size:12px;color:#999;margin-top:4px;">支持PNG、JPG、JPEG</div>
                <input type="file" id="ocr-file-input" accept="image/*" style="display:none;" onchange="handleOcrImageUpload(event, ${taskId})">
            </div>
            <div id="ocr-progress" style="display:none;margin-bottom:16px;">
                <div style="background:#e5e7eb;border-radius:8px;height:8px;overflow:hidden;">
                    <div id="ocr-progress-bar" style="background:linear-gradient(90deg,#8b5cf6,#6d28d9);height:100%;width:0%;transition:width .3s;"></div>
                </div>
                <div id="ocr-progress-text" style="text-align:center;font-size:12px;color:#666;margin-top:4px;">准备中...</div>
            </div>
            <div id="ocr-original-text-area" style="display:none;margin-bottom:16px;">
                <div style="font-size:13px;font-weight:600;margin-bottom:8px;color:#666;">📝 OCR识别原始文本（供参考）：</div>
                <div id="ocr-original-text" style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:6px;padding:8px;font-size:12px;font-family:monospace;max-height:120px;overflow:auto;white-space:pre-wrap;"></div>
            </div>
            <div id="ocr-result-area" style="display:none;margin-bottom:16px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <div style="font-size:13px;font-weight:600;color:#666;">📋 解析结果（请确认/编辑后导入）：</div>
                    <button onclick="addOcrRow()" style="padding:4px 10px;background:#e5e7eb;border:none;border-radius:4px;cursor:pointer;font-size:12px;">+ 添加行</button>
                </div>
                <div style="overflow:auto;">
                    <table style="width:100%;border-collapse:collapse;font-size:12px;">
                        <thead><tr style="background:#f8fafc;">
                            <th style="padding:6px;border:1px solid #e5e7eb;text-align:left;">物料名称 *</th>
                            <th style="padding:6px;border:1px solid #e5e7eb;text-align:left;">规格</th>
                            <th style="padding:6px;border:1px solid #e5e7eb;text-align:right;">数量</th>
                            <th style="padding:6px;border:1px solid #e5e7eb;text-align:left;">单位</th>
                            <th style="padding:6px;border:1px solid #e5e7eb;text-align:right;">单价</th>
                            <th style="padding:6px;border:1px solid #e5e7eb;text-align:center;">操作</th>
                        </tr></thead>
                        <tbody id="ocr-items-tbody"></tbody>
                    </table>
                </div>
            </div>
            <div style="display:flex;gap:8px;justify-content:flex-end;">
                <button onclick="closeOcrModal()" style="padding:8px 16px;background:#e5e7eb;color:#333;border:none;border-radius:6px;cursor:pointer;font-size:13px;">取消</button>
                <button id="ocr-confirm-btn" onclick="confirmOcrMaterials(${taskId})" style="padding:8px 16px;background:#10b981;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;display:none;">✅ 确认导入物料</button>
            </div>
        </div>`;
    document.body.appendChild(modal);
}

function closeOcrModal() {
    const modal = document.getElementById('ocr-modal');
    if (modal) modal.remove();
    _ocrParsedItems = [];
    _ocrOriginalText = '';
}

async function handleOcrImageUpload(event, taskId) {
    const file = event.target.files[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
        showToast('请上传图片文件', 'warning');
        return;
    }
    // 显示预览和进度
    const uploadArea = document.getElementById('ocr-upload-area');
    uploadArea.innerHTML = `<img src="${URL.createObjectURL(file)}" style="max-width:100%;max-height:300px;border-radius:6px;"><div style="font-size:12px;color:#999;margin-top:4px;">点击重新选择</div>`;
    uploadArea.onclick = () => document.getElementById('ocr-file-input').click();
    document.getElementById('ocr-progress').style.display = 'block';
    document.getElementById('ocr-progress-bar').style.width = '10%';
    document.getElementById('ocr-progress-text').textContent = '正在加载OCR引擎（首次约需几秒）...';
    try {
        const result = await Tesseract.recognize(file, 'chi_sim+eng', {
            // 明确指定CDN路径，避免语言包加载失败
            langPath: 'https://tessdata.projectnaptha.com/4.0.0',
            workerPath: 'https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/worker.min.js',
            logger: m => {
                if (m.status === 'recognizing text') {
                    const pct = Math.round(20 + m.progress * 70);
                    document.getElementById('ocr-progress-bar').style.width = pct + '%';
                    document.getElementById('ocr-progress-text').textContent = `正在识别文字... ${Math.round(m.progress * 100)}%`;
                } else if (m.status === 'loading tesseract core') {
                    document.getElementById('ocr-progress-text').textContent = '正在加载OCR核心...';
                } else if (m.status === 'initializing tesseract') {
                    document.getElementById('ocr-progress-text').textContent = '正在初始化...';
                } else if (m.status === 'loading language traineddata') {
                    document.getElementById('ocr-progress-text').textContent = '正在加载中文语言包（首次约需10-30秒）...';
                }
            }
        });
        _ocrOriginalText = result.data.text;
        document.getElementById('ocr-progress-bar').style.width = '100%';
        document.getElementById('ocr-progress-text').textContent = '识别完成！';
        document.getElementById('ocr-original-text-area').style.display = 'block';
        document.getElementById('ocr-original-text').textContent = _ocrOriginalText || '(未识别到文字)';
        // 解析字段
        _ocrParsedItems = parseOcrText(_ocrOriginalText);
        // 优雅降级：如果没解析到项，添加一个空行让用户手动录入
        if (_ocrParsedItems.length === 0) {
            _ocrParsedItems.push({material_name: '', specification: '', quantity: 1, unit: '个', unit_price: null});
            showToast('OCR未识别到物料，请手动录入或重新上传截图', 'warning');
        } else {
            showToast(`识别完成，解析出 ${_ocrParsedItems.length} 项物料，请确认编辑`, 'success');
        }
        document.getElementById('ocr-result-area').style.display = 'block';
        document.getElementById('ocr-confirm-btn').style.display = 'inline-block';
        renderOcrItems();
        setTimeout(() => {
            document.getElementById('ocr-progress').style.display = 'none';
        }, 1500);
    } catch(e) {
        document.getElementById('ocr-progress-text').textContent = '识别失败，已切换到手动录入';
        document.getElementById('ocr-progress-bar').style.background = '#ef4444';
        showToast('OCR识别失败，已切换到手动录入模式', 'warning');
        // 优雅降级：OCR失败时显示空表格让用户手动录入
        _ocrOriginalText = '';
        _ocrParsedItems = [{material_name: '', specification: '', quantity: 1, unit: '个', unit_price: null}];
        document.getElementById('ocr-original-text-area').style.display = 'none';
        document.getElementById('ocr-result-area').style.display = 'block';
        document.getElementById('ocr-confirm-btn').style.display = 'inline-block';
        renderOcrItems();
        setTimeout(() => {
            document.getElementById('ocr-progress').style.display = 'none';
        }, 2000);
    }
    event.target.value = '';
}

function parseOcrText(text) {
    const items = [];
    const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 0);
    // 价格正则：匹配 ¥123.45 / 123.45元 / 价格123.45 / 纯数字123.45
    const priceRe = /[¥￥]\s*([\d,]+(?:\.\d+)?)/;
    const priceRe2 = /([\d,]+(?:\.\d+)?)\s*元/;
    // 纯数字价格行（整行只有数字和小数点，2-8位）
    const purePriceRe = /^[\d,]+\.\d{2}$|^[\d,]{3,}$/;
    // 数量正则：匹配 x2 / ×2 / 2个 / 2件 / 数量:2
    const qtyRe = /[x×]\s*(\d+(?:\.\d+)?)/i;
    const qtyRe2 = /数量[:：]?\s*(\d+(?:\.\d+)?)/;
    const unitRe = /(\d+(?:\.\d+)?)\s*(个|件|套|台|箱|张|条|米|根|块|组|包|kg|克|千克|台|只|瓶|set|pcs|pcs)/i;
    // 判断是否为价格行（含¥/元符号，或整行纯数字，或行尾是价格+数量模式）
    function isPriceLine(line) {
        if (priceRe.test(line) || priceRe2.test(line) || purePriceRe.test(line)) return true;
        // 行尾是 数字.数字 + x数字 模式（如 "商品名 850.00 x5"）
        if (/[\d,]+\.\d{2}\s*[x×]\s*\d/i.test(line)) return true;
        return false;
    }
    // 提取价格数值
    function extractPrice(line) {
        let pm = line.match(priceRe) || line.match(priceRe2);
        if (pm) return parseFloat(pm[1].replace(/,/g, ''));
        if (purePriceRe.test(line)) return parseFloat(line.replace(/,/g, ''));
        // 尝试提取行内最后一个数字（可能是价格）
        const nums = line.match(/[\d,]+\.\d{2}|[\d,]+/g);
        if (nums) return parseFloat(nums[nums.length - 1].replace(/,/g, ''));
        return null;
    }
    // 判断是否为商品名行（包含中文或较长英文，不含纯价格）
    function isNameLine(line) {
        if (isPriceLine(line)) return false;
        if (/^[\d,.\s]+$/.test(line)) return false;
        if (/^[x×\d\s]+$/.test(line)) return false;
        return /[\u4e00-\u9fa5a-zA-Z]/.test(line) && line.length >= 2;
    }

    // 策略0：处理内联格式（名称+价格+数量在同一行，如 "Product A 850.00 x5"）
    const inlineItems = [];
    const remainingLines = [];
    for (const line of lines) {
        // 检测行内是否同时有文字和价格模式
        const hasPriceInline = priceRe.test(line) || priceRe2.test(line) || /[\d,]+\.\d{2}/.test(line);
        const hasText = /[\u4e00-\u9fa5a-zA-Z]{2,}/.test(line);
        // 内联行必须有足够文字（避免纯价格行被误处理）
        if (hasPriceInline && hasText && line.replace(/[\d,.\s¥$x×元]/gi, '').length >= 2) {
            // 提取价格（优先¥/元符号，其次行内第一个带小数点的数字）
            let price = null;
            const pm = line.match(priceRe) || line.match(priceRe2);
            if (pm) price = parseFloat(pm[1].replace(/,/g, ''));
            else {
                // 优先匹配带小数点的价格（两位或更多小数）
                const priceMatch = line.match(/[\d,]+\.\d{2,}/);
                if (priceMatch) price = parseFloat(priceMatch[0].replace(/,/g, ''));
                else {
                    // 没有小数点时，取第一个较大的数字（>=10通常是价格而非数量）
                    const nums = line.match(/\d+/g);
                    if (nums) {
                        const candidates = nums.map(n => parseInt(n)).filter(n => n >= 10);
                        if (candidates.length > 0) price = candidates[0];
                    }
                }
            }
            // 提取数量
            let qty = null, unit = null;
            const qm = line.match(qtyRe) || line.match(qtyRe2);
            if (qm) qty = parseFloat(qm[1]);
            const um = line.match(unitRe);
            if (um) { qty = parseFloat(um[1]); unit = um[2]; }
            // 提取名称（去掉价格和数量部分后的剩余文字）
            let name = line
                .replace(priceRe, '').replace(priceRe2, '')
                .replace(/[\d,]+\.\d{2}/g, '')
                .replace(qtyRe, '').replace(qtyRe2, '')
                .replace(unitRe, '')
                .replace(/[x×]/gi, ' ')
                .replace(/\s+/g, ' ').trim();
            if (name && name.length >= 2 && price !== null) {
                inlineItems.push({material_name: name, specification: '', quantity: qty||1, unit: unit||'个', unit_price: price});
                continue; // 跳过后续处理
            }
        }
        remainingLines.push(line);
    }
    // 如果内联解析到项，直接返回
    if (inlineItems.length > 0) return inlineItems;

    // 策略1：价格行上方找商品名
    let i = 0;
    while (i < remainingLines.length) {
        const line = remainingLines[i];
        if (isPriceLine(line)) {
            const price = extractPrice(line);
            let name = null, spec = null, qty = null, unit = null;
            // 找上方3行内的商品名
            for (let j = Math.max(0, i - 3); j < i; j++) {
                if (isNameLine(remainingLines[j])) {
                    if (!name) name = remainingLines[j];
                    else if (!spec && remainingLines[j].length < 30) spec = remainingLines[j];
                }
                // 提取数量
                const qm = remainingLines[j].match(qtyRe) || remainingLines[j].match(qtyRe2);
                if (qm && !qty) qty = parseFloat(qm[1]);
                const um = remainingLines[j].match(unitRe);
                if (um && !unit) { qty = parseFloat(um[1]); unit = um[2]; }
            }
            // 同一行提取数量
            const qm2 = line.match(qtyRe) || line.match(qtyRe2);
            if (qm2 && !qty) qty = parseFloat(qm2[1]);
            if (name) {
                items.push({material_name: name, specification: spec||'', quantity: qty||1, unit: unit||'个', unit_price: price});
            }
        } else if (isNameLine(line) && i + 1 < remainingLines.length && isPriceLine(remainingLines[i+1])) {
            // 名称行后面紧跟价格行，已在上面处理
        }
        i++;
    }

    // 策略2：如果没解析到项，用宽松模式（名称行+价格行配对）
    if (items.length === 0) {
        let currentName = null;
        let currentSpec = null;
        for (const line of remainingLines) {
            if (isPriceLine(line)) {
                const price = extractPrice(line);
                if (currentName && price) {
                    items.push({material_name: currentName, specification: currentSpec||'', quantity: 1, unit: '个', unit_price: price});
                    currentName = null; currentSpec = null;
                }
            } else if (isNameLine(line)) {
                if (!currentName) currentName = line;
                else if (!currentSpec && line.length < 30) currentSpec = line;
                else { currentName = line; currentSpec = null; }
            }
        }
    }

    // 策略3：如果还是没有，把所有名称行都列为候选
    if (items.length === 0) {
        for (const line of remainingLines) {
            if (isNameLine(line) && line.length >= 3) {
                items.push({material_name: line, specification: '', quantity: 1, unit: '个', unit_price: null});
            }
        }
    }

    return items;
}

function renderOcrItems() {
    const tbody = document.getElementById('ocr-items-tbody');
    if (!tbody) return;
    if (!_ocrParsedItems.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="padding:16px;text-align:center;color:#999;">未识别到物料，请手动添加或重新上传截图</td></tr>';
        return;
    }
    tbody.innerHTML = '';
    _ocrParsedItems.forEach((item, idx) => {
        const tr = document.createElement('tr');
        tr.style.borderBottom = '1px solid #f3f4f6';
        tr.innerHTML = `
            <td style="padding:4px;border:1px solid #e5e7eb;"><input value="${(item.material_name||'').replace(/"/g,'&quot;')}" onchange="updateOcrItem(${idx},'material_name',this.value)" style="width:100%;padding:4px;border:1px solid #ddd;border-radius:3px;font-size:12px;"></td>
            <td style="padding:4px;border:1px solid #e5e7eb;"><input value="${(item.specification||'').replace(/"/g,'&quot;')}" onchange="updateOcrItem(${idx},'specification',this.value)" style="width:100%;padding:4px;border:1px solid #ddd;border-radius:3px;font-size:12px;"></td>
            <td style="padding:4px;border:1px solid #e5e7eb;"><input type="number" value="${item.quantity||1}" onchange="updateOcrItem(${idx},'quantity',parseFloat(this.value)||1)" style="width:60px;padding:4px;border:1px solid #ddd;border-radius:3px;font-size:12px;text-align:right;"></td>
            <td style="padding:4px;border:1px solid #e5e7eb;"><input value="${item.unit||'个'}" onchange="updateOcrItem(${idx},'unit',this.value)" style="width:50px;padding:4px;border:1px solid #ddd;border-radius:3px;font-size:12px;text-align:center;"></td>
            <td style="padding:4px;border:1px solid #e5e7eb;"><input type="number" value="${item.unit_price||''}" onchange="updateOcrItem(${idx},'unit_price',this.value?parseFloat(this.value):null)" style="width:80px;padding:4px;border:1px solid #ddd;border-radius:3px;font-size:12px;text-align:right;"></td>
            <td style="padding:4px;border:1px solid #e5e7eb;text-align:center;"><button onclick="removeOcrItem(${idx})" style="background:#fee2e2;color:#dc2626;border:none;border-radius:3px;padding:4px 8px;cursor:pointer;font-size:11px;">删除</button></td>
        `;
        tbody.appendChild(tr);
    });
}

function updateOcrItem(idx, field, value) {
    if (_ocrParsedItems[idx]) _ocrParsedItems[idx][field] = value;
}

function removeOcrItem(idx) {
    _ocrParsedItems.splice(idx, 1);
    renderOcrItems();
}

function addOcrRow() {
    _ocrParsedItems.push({material_name: '', specification: '', quantity: 1, unit: '个', unit_price: null});
    renderOcrItems();
}

async function confirmOcrMaterials(taskId) {
    // 过滤有效项
    const validItems = _ocrParsedItems.filter(item => item.material_name && item.material_name.trim());
    if (!validItems.length) { showToast('没有有效的物料项，请至少填写物料名称', 'warning'); return; }
    try {
        const r = await fetch(`${ENG_API}/production-tasks/${taskId}/materials/batch`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({items: validItems})
        });
        const d = await r.json();
        if (d.success) {
            showToast(`✅ 成功导入 ${d.imported} 项原材料`);
            closeOcrModal();
            renderProductionTab(getCurrentProjectId(), document.getElementById('proj-tab-content'));
        } else {
            showToast('导入失败：' + (d.detail||''), 'error');
        }
    } catch(e) {
        showToast('导入失败：' + e.message, 'error');
    }
}

// =============== 委派加工 ===============
const TECH_API = '/api/v1/eng-modules';

async function renderOutsourcingOrders() {
    const content = document.getElementById('content') || document.getElementById('eng-content');
    if (!content) return;
    content.innerHTML = `<div class="content-header"><h2>🏭 委派加工</h2></div><div id="outsource-list">加载中...</div>`;
    try {
        const r = await fetch(`${TECH_API}/technical/outsourcing-orders`);
        const orders = await r.json();
        const statusMap = {PENDING:'⏳待加工', PROCESSING:'🔄加工中', COMPLETED:'✅已完成', CANCELLED:'❌已取消'};
        const el = document.getElementById('outsource-list');
        if (!orders.length) { el.innerHTML = '<p style="color:#9ca3af;">暂无委派加工单</p>'; return; }
        el.innerHTML = `
            <table class="data-table" style="width:100%;border-collapse:collapse;font-size:13px;">
                <thead><tr style="background:#f3f4f6;">
                    <th style="padding:8px;border:1px solid #e5e7eb;">单号</th><th style="padding:8px;border:1px solid #e5e7eb;">零件名称</th>
                    <th style="padding:8px;border:1px solid #e5e7eb;">规格</th><th style="padding:8px;border:1px solid #e5e7eb;">数量</th>
                    <th style="padding:8px;border:1px solid #e5e7eb;">状态</th><th style="padding:8px;border:1px solid #e5e7eb;">操作</th>
                </tr></thead>
                <tbody>${orders.map(o=>`<tr>
                    <td style="padding:8px;border:1px solid #e5e7eb;">${o.order_no}</td>
                    <td style="padding:8px;border:1px solid #e5e7eb;">${o.part_name}</td>
                    <td style="padding:8px;border:1px solid #e5e7eb;">${o.specification||'-'}</td>
                    <td style="padding:8px;border:1px solid #e5e7eb;">${o.quantity}${o.unit}</td>
                    <td style="padding:8px;border:1px solid #e5e7eb;">${statusMap[o.status]}</td>
                    <td style="padding:8px;border:1px solid #e5e7eb;">
                        ${o.status==='PENDING'?`<button onclick="updateOutsourceStatus(${o.id},'PROCESSING')" style="color:#3b82f6;border:none;background:none;cursor:pointer;">开始</button>`:''}
                        ${o.status==='PROCESSING'?`<button onclick="updateOutsourceStatus(${o.id},'COMPLETED')" style="color:#10b981;border:none;background:none;cursor:pointer;">完成</button>`:''}
                        ${o.status!=='COMPLETED'&&o.status!=='CANCELLED'?`<button onclick="updateOutsourceStatus(${o.id},'CANCELLED')" style="color:#ef4444;border:none;background:none;cursor:pointer;margin-left:6px;">取消</button>`:''}
                    </td>
                </tr>`).join('')}</tbody>
            </table>
        `;
    } catch(e) { showToast('加载失败', 'error'); }
}

async function updateOutsourceStatus(id, status) {
    try {
        const r = await fetch(`${TECH_API}/technical/outsourcing-orders/${id}/status`, {
            method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({status})
        });
        const d = await r.json();
        if (d.success) { showToast('状态已更新'); renderOutsourcingOrders(); }
    } catch(e) { showToast('更新失败', 'error'); }
}

// =============== 技术管理：技术拆解 + 三分类一键分发 ===============
let _techProjects = [];
let _techCurrentProject = null;
let _techItems = [];
let _techImportItems = [];
let _techEditId = null;
const TECH_CAT_MAP = {PURCHASABLE:'🛒 可采购', MANUFACTURABLE:'🔧 可加工', ASSEMBLABLE:'🧩 可装配'};
const TECH_SOURCE_MAP = {excel:'Excel导入', manual:'手动添加', deliverable:'交付物料'};
const TECH_BTN = 'padding:7px 16px;border:none;border-radius:6px;color:#fff;cursor:pointer;font-size:13px;';

async function renderTechManagement() {
    const content = document.getElementById('content') || document.getElementById('eng-content');
    if (!content) return;
    content.innerHTML = `
        <div class="content-header"><h2>🔧 技术管理</h2>
        <div style="font-size:12px;color:#9ca3af;margin-top:4px;">合同交付物料 → 技术拆解（可采购 / 可加工 / 可装配）→ 一键分发到采购、委外、生产</div>
        </div>
        <div style="background:#fff;border-radius:10px;padding:14px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
            <div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;">
                <label style="font-size:13px;font-weight:600;color:#374151;">选择项目：</label>
                <select id="tech-project-select" onchange="onTechProjectChange(this.value)" style="padding:7px 12px;border:1px solid #d1d5db;border-radius:6px;min-width:320px;font-size:13px;">
                    <option value="">-- 请选择项目 --</option>
                </select>
                <span id="tech-project-stats" style="font-size:12px;color:#6b7280;"></span>
            </div>
            <div id="tech-toolbar" style="display:none;margin-top:12px;flex-wrap:wrap;gap:10px;align-items:center;">
                <button onclick="showTechItemForm()" style="${TECH_BTN}background:#10b981;">➕ 手动添加</button>
                <button onclick="document.getElementById('tech-excel-input').click()" style="${TECH_BTN}background:#6366f1;">📤 Excel导入</button>
                <input type="file" id="tech-excel-input" accept=".xlsx,.xls" onchange="handleTechExcelUpload(event)" style="display:none;">
                <button onclick="downloadTechTemplate()" style="${TECH_BTN}background:#6b7280;">📥 模板下载</button>
                <button onclick="loadTechFromDeliverables()" style="${TECH_BTN}background:#0ea5e9;">📋 从交付物料加载</button>
                <button onclick="dispatchTechItems()" style="${TECH_BTN}background:linear-gradient(135deg,#f59e0b,#d97706);margin-left:auto;padding:9px 22px;font-weight:600;">🚀 一键下发选中项</button>
            </div>
        </div>
        <div id="tech-item-form" style="display:none;background:#fff;border-radius:10px;padding:14px 16px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);border-left:4px solid #10b981;"></div>
        <div id="tech-import-preview" style="display:none;background:#fff;border-radius:10px;padding:14px 16px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);border-left:4px solid #6366f1;"></div>
        <div id="tech-items-wrap"></div>
    `;
    try {
        const r = await fetch('/api/v1/eng-modules/technical/projects');
        _techProjects = await r.json();
        const sel = document.getElementById('tech-project-select');
        sel.innerHTML = '<option value="">-- 请选择项目 --</option>' + _techProjects.map(p =>
            `<option value="${p.id}">${p.project_no || ''} ${p.project_name || ''}（交付${p.deliverable_count}项 / 拆解${p.decomposition_count}项）</option>`).join('');
    } catch (e) { showToast('项目列表加载失败', 'error'); }
}

async function onTechProjectChange(pid) {
    _techCurrentProject = pid ? parseInt(pid) : null;
    _techEditId = null;
    document.getElementById('tech-toolbar').style.display = pid ? 'flex' : 'none';
    document.getElementById('tech-item-form').style.display = 'none';
    document.getElementById('tech-import-preview').style.display = 'none';
    document.getElementById('tech-project-stats').textContent = '';
    if (!pid) { document.getElementById('tech-items-wrap').innerHTML = ''; return; }
    await loadTechDecompositions();
}

async function loadTechDecompositions() {
    const wrap = document.getElementById('tech-items-wrap');
    if (!wrap) return;
    wrap.innerHTML = '<div style="padding:24px;text-align:center;color:#9ca3af;background:#fff;border-radius:10px;">加载中...</div>';
    try {
        const r = await fetch(`/api/v1/eng-modules/technical/${_techCurrentProject}/decompositions`);
        _techItems = await r.json();
        const pending = _techItems.filter(i => i.dispatch_status !== 'DISPATCHED').length;
        const p = _techProjects.find(x => x.id === _techCurrentProject);
        document.getElementById('tech-project-stats').textContent =
            p ? `合同交付物料 ${p.deliverable_count} 项 · 已拆解 ${_techItems.length} 项 · 待下发 ${pending} 项` : '';
        renderTechItemsTable();
    } catch (e) {
        wrap.innerHTML = '<div style="padding:24px;text-align:center;color:#dc2626;background:#fff;border-radius:10px;">加载失败，请重试</div>';
    }
}

function _techCatOptions(selected) {
    return Object.keys(TECH_CAT_MAP).map(k =>
        `<option value="${k}" ${k === selected ? 'selected' : ''}>${TECH_CAT_MAP[k]}</option>`).join('');
}

function renderTechItemsTable() {
    const wrap = document.getElementById('tech-items-wrap');
    if (!_techItems.length) {
        wrap.innerHTML = '<div style="padding:28px;text-align:center;color:#9ca3af;background:#fff;border-radius:10px;">暂无拆解项，请点击「手动添加」「Excel导入」或「从交付物料加载」</div>';
        return;
    }
    wrap.innerHTML = `
        <div style="background:#fff;border-radius:10px;padding:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
        <div style="overflow-x:auto;">
        <table style="width:100%;border-collapse:collapse;font-size:13px;min-width:1000px;">
            <thead><tr style="background:#f3f4f6;">
                <th style="padding:8px;border:1px solid #e5e7eb;width:36px;"><input type="checkbox" id="tech-check-all" onchange="toggleTechAll(this.checked)"></th>
                <th style="padding:8px;border:1px solid #e5e7eb;width:44px;">序号</th>
                <th style="padding:8px;border:1px solid #e5e7eb;">零件编码</th>
                <th style="padding:8px;border:1px solid #e5e7eb;">零件名称</th>
                <th style="padding:8px;border:1px solid #e5e7eb;">规格型号</th>
                <th style="padding:8px;border:1px solid #e5e7eb;text-align:right;width:70px;">数量</th>
                <th style="padding:8px;border:1px solid #e5e7eb;width:56px;">单位</th>
                <th style="padding:8px;border:1px solid #e5e7eb;width:120px;">分类</th>
                <th style="padding:8px;border:1px solid #e5e7eb;width:90px;">来源</th>
                <th style="padding:8px;border:1px solid #e5e7eb;width:80px;">状态</th>
                <th style="padding:8px;border:1px solid #e5e7eb;width:110px;">操作</th>
            </tr></thead>
            <tbody>${_techItems.map((i, idx) => {
                const dispatched = i.dispatch_status === 'DISPATCHED';
                return `<tr style="${dispatched ? 'background:#f9fafb;color:#9ca3af;' : ''}">
                    <td style="padding:8px;border:1px solid #e5e7eb;text-align:center;">
                        ${dispatched ? '' : `<input type="checkbox" class="tech-check" value="${i.id}">`}
                    </td>
                    <td style="padding:8px;border:1px solid #e5e7eb;text-align:center;">${idx + 1}</td>
                    <td style="padding:8px;border:1px solid #e5e7eb;">${i.part_code || '-'}</td>
                    <td style="padding:8px;border:1px solid #e5e7eb;font-weight:500;">${i.part_name || '-'}</td>
                    <td style="padding:8px;border:1px solid #e5e7eb;">${i.specification || '-'}</td>
                    <td style="padding:8px;border:1px solid #e5e7eb;text-align:right;">${i.quantity}</td>
                    <td style="padding:8px;border:1px solid #e5e7eb;">${i.unit || '个'}</td>
                    <td style="padding:8px;border:1px solid #e5e7eb;">
                        <select onchange="changeTechCategory(${i.id}, this.value)" ${dispatched ? 'disabled' : ''} style="padding:4px 6px;border:1px solid #d1d5db;border-radius:4px;font-size:12px;${dispatched ? 'background:#f3f4f6;' : ''}">
                            ${_techCatOptions(i.category)}
                        </select>
                    </td>
                    <td style="padding:8px;border:1px solid #e5e7eb;font-size:12px;">${TECH_SOURCE_MAP[i.source] || i.source || '-'}</td>
                    <td style="padding:8px;border:1px solid #e5e7eb;">${dispatched ? '<span style="color:#16a34a;">✅ 已下发</span>' : '<span style="color:#d97706;">⏳ 待下发</span>'}</td>
                    <td style="padding:8px;border:1px solid #e5e7eb;white-space:nowrap;">
                        ${dispatched ? '-' : `
                            <button onclick="editTechItem(${i.id})" style="color:#3b82f6;border:none;background:none;cursor:pointer;font-size:12px;">编辑</button>
                            <button id="tech-del-${i.id}" onclick="deleteTechItem(${i.id}, this)" style="color:#ef4444;border:none;background:none;cursor:pointer;font-size:12px;margin-left:8px;">删除</button>`}
                    </td>
                </tr>`;
            }).join('')}</tbody>
        </table></div></div>
    `;
}

function toggleTechAll(checked) {
    document.querySelectorAll('.tech-check').forEach(cb => { cb.checked = checked; });
}

function showTechItemForm() {
    _techEditId = null;
    const el = document.getElementById('tech-item-form');
    el.style.display = 'block';
    el.innerHTML = _techItemFormHTML({});
    el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function editTechItem(id) {
    const item = _techItems.find(x => x.id === id);
    if (!item) return;
    _techEditId = id;
    const el = document.getElementById('tech-item-form');
    el.style.display = 'block';
    el.innerHTML = _techItemFormHTML(item);
    el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function cancelTechItemForm() {
    _techEditId = null;
    document.getElementById('tech-item-form').style.display = 'none';
}

function _techItemFormHTML(item) {
    const lbl = 'display:block;font-size:12px;color:#6b7280;margin-bottom:3px;';
    const inp = 'width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:13px;box-sizing:border-box;';
    return `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
            <b style="font-size:14px;color:#374151;">${_techEditId ? '✏️ 编辑拆解项' : '➕ 新增拆解项'}</b>
            <button onclick="cancelTechItemForm()" style="border:none;background:none;color:#9ca3af;cursor:pointer;font-size:16px;">✕</button>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;">
            <div><label style="${lbl}">零件编码</label><input id="tf-code" value="${item.part_code || ''}" placeholder="如 P-01" style="${inp}"></div>
            <div><label style="${lbl}">零件名称 *</label><input id="tf-name" value="${item.part_name || ''}" placeholder="如 304不锈钢板" style="${inp}"></div>
            <div><label style="${lbl}">规格型号</label><input id="tf-spec" value="${item.specification || ''}" style="${inp}"></div>
            <div><label style="${lbl}">数量</label><input id="tf-qty" type="number" min="0.01" step="any" value="${item.quantity != null ? item.quantity : 1}" style="${inp}"></div>
            <div><label style="${lbl}">单位</label><input id="tf-unit" value="${item.unit || '个'}" style="${inp}"></div>
            <div><label style="${lbl}">分类</label><select id="tf-cat" style="${inp}">${_techCatOptions(item.category || 'PURCHASABLE')}</select></div>
            <div style="grid-column:1/-1;"><label style="${lbl}">备注</label><input id="tf-remark" value="${item.remark || ''}" style="${inp}"></div>
        </div>
        <div style="margin-top:12px;">
            <button onclick="saveTechItem()" style="${TECH_BTN}background:#10b981;">💾 保存</button>
            <button onclick="cancelTechItemForm()" style="${TECH_BTN}background:#9ca3af;margin-left:10px;">取消</button>
        </div>
    `;
}

async function saveTechItem() {
    const name = (document.getElementById('tf-name').value || '').trim();
    if (!name) { showToast('零件名称不能为空', 'warning'); return; }
    const body = {
        part_code: (document.getElementById('tf-code').value || '').trim(),
        part_name: name,
        specification: (document.getElementById('tf-spec').value || '').trim(),
        quantity: parseFloat(document.getElementById('tf-qty').value) || 1,
        unit: (document.getElementById('tf-unit').value || '个').trim(),
        category: document.getElementById('tf-cat').value,
        remark: (document.getElementById('tf-remark').value || '').trim(),
    };
    try {
        let r;
        if (_techEditId) {
            r = await fetch(`/api/v1/eng-modules/technical/items/${_techEditId}`, {
                method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
            });
        } else {
            r = await fetch(`/api/v1/eng-modules/technical/${_techCurrentProject}/items`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
            });
        }
        const d = await r.json();
        if (d.success) {
            showToast(_techEditId ? '已更新' : '已添加');
            cancelTechItemForm();
            await loadTechDecompositions();
        } else {
            showToast(d.detail || '保存失败', 'error');
        }
    } catch (e) { showToast('保存失败', 'error'); }
}

async function changeTechCategory(id, cat) {
    try {
        const r = await fetch(`/api/v1/eng-modules/technical/items/${id}`, {
            method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ category: cat })
        });
        const d = await r.json();
        if (d.success) {
            const it = _techItems.find(x => x.id === id);
            if (it) it.category = cat;
            showToast('分类已更新');
        } else { showToast(d.detail || '更新失败', 'error'); }
    } catch (e) { showToast('更新失败', 'error'); }
}

async function deleteTechItem(id, btn) {
    // 两步确认：第一次点击变红提示，第二次真正删除（无弹窗）
    if (!btn.dataset.confirm) {
        btn.dataset.confirm = '1';
        btn.textContent = '确认删除？';
        setTimeout(() => { btn.dataset.confirm = ''; btn.textContent = '删除'; }, 3000);
        return;
    }
    try {
        const r = await fetch(`/api/v1/eng-modules/technical/items/${id}`, { method: 'DELETE' });
        const d = await r.json();
        if (d.success) { showToast('已删除'); await loadTechDecompositions(); }
        else { showToast(d.detail || '删除失败', 'error'); }
    } catch (e) { showToast('删除失败', 'error'); }
}

function downloadTechTemplate() {
    window.open('/api/v1/eng-modules/technical/decomposition-template', '_blank');
}

async function loadTechFromDeliverables() {
    try {
        const r = await fetch(`/api/v1/eng-modules/technical/${_techCurrentProject}/load-deliverables`, { method: 'POST' });
        const d = await r.json();
        if (d.success) {
            showToast(`已从交付物料加载 ${d.loaded} 项，默认可采购，可调整分类`);
            await loadTechDecompositions();
        } else {
            showToast(d.detail || '加载失败', 'warning');
        }
    } catch (e) { showToast('加载失败', 'error'); }
}

async function handleTechExcelUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    try {
        const r = await fetch(`/api/v1/eng-modules/technical/${_techCurrentProject}/import-preview`, {
            method: 'POST', body: fd
        });
        const d = await r.json();
        if (d.success) {
            _techImportItems = d.items || [];
            renderTechImportPreview();
            showToast(`解析到 ${d.total} 项，请确认分类后导入`);
        } else {
            showToast(d.detail || '解析失败', 'error');
        }
    } catch (e) { showToast('解析失败', 'error'); }
    event.target.value = '';
}

function renderTechImportPreview() {
    const el = document.getElementById('tech-import-preview');
    el.style.display = 'block';
    el.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <b style="font-size:14px;color:#374151;">📋 导入预览（${_techImportItems.length} 项，可调整分类）</b>
            <button onclick="cancelTechImport()" style="border:none;background:none;color:#9ca3af;cursor:pointer;font-size:16px;">✕</button>
        </div>
        <div style="overflow-x:auto;max-height:360px;overflow-y:auto;">
        <table style="width:100%;border-collapse:collapse;font-size:12px;min-width:800px;">
            <thead><tr style="background:#eef2ff;position:sticky;top:0;">
                <th style="padding:6px;border:1px solid #e0e7ff;">零件编码</th>
                <th style="padding:6px;border:1px solid #e0e7ff;">零件名称</th>
                <th style="padding:6px;border:1px solid #e0e7ff;">规格型号</th>
                <th style="padding:6px;border:1px solid #e0e7ff;text-align:right;">数量</th>
                <th style="padding:6px;border:1px solid #e0e7ff;">单位</th>
                <th style="padding:6px;border:1px solid #e0e7ff;">分类</th>
                <th style="padding:6px;border:1px solid #e0e7ff;">备注</th>
            </tr></thead>
            <tbody>${_techImportItems.map((i, idx) => `<tr>
                <td style="padding:6px;border:1px solid #e5e7eb;">${i.part_code || '-'}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;font-weight:500;">${i.part_name}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;">${i.specification || '-'}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;text-align:right;">${i.quantity}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;">${i.unit || '个'}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;">
                    <select onchange="_techImportItems[${idx}].category=this.value" style="padding:3px 6px;border:1px solid #d1d5db;border-radius:4px;font-size:12px;">
                        ${_techCatOptions(i.category)}
                    </select>
                </td>
                <td style="padding:6px;border:1px solid #e5e7eb;color:#9ca3af;">${i.remark || ''}</td>
            </tr>`).join('')}</tbody>
        </table></div>
        <div style="margin-top:10px;">
            <button onclick="confirmTechImport()" style="${TECH_BTN}background:#10b981;">✅ 确认导入 ${_techImportItems.length} 项</button>
            <button onclick="cancelTechImport()" style="${TECH_BTN}background:#9ca3af;margin-left:10px;">取消</button>
        </div>
    `;
    el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function cancelTechImport() {
    _techImportItems = [];
    document.getElementById('tech-import-preview').style.display = 'none';
}

async function confirmTechImport() {
    if (!_techImportItems.length) { showToast('没有可导入的数据', 'warning'); return; }
    try {
        const r = await fetch(`/api/v1/eng-modules/technical/${_techCurrentProject}/import-confirm`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items: _techImportItems })
        });
        const d = await r.json();
        if (d.success) {
            showToast(`✅ 成功导入 ${d.imported} 项`);
            cancelTechImport();
            await loadTechDecompositions();
        } else {
            showToast(d.detail || '导入失败', 'error');
        }
    } catch (e) { showToast('导入失败', 'error'); }
}

async function dispatchTechItems() {
    const ids = Array.from(document.querySelectorAll('.tech-check:checked')).map(cb => parseInt(cb.value));
    if (!ids.length) { showToast('请先勾选要下发的零件（仅待下发项可选）', 'warning'); return; }
    const btn = document.querySelector('#tech-toolbar button[onclick="dispatchTechItems()"]');
    if (btn) { btn.disabled = true; btn.textContent = '下发中...'; }
    try {
        const r = await fetch(`/api/v1/eng-modules/technical/${_techCurrentProject}/dispatch`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_ids: ids })
        });
        const d = await r.json();
        if (d.success) {
            showToast(`🚚 下发完成：采购 ${d.purchase} 项 · 委外加工 ${d.outsource} 项 · 装配 ${d.assembly} 项`);
            await loadTechDecompositions();
        } else {
            showToast(d.detail || '下发失败', 'error');
        }
    } catch (e) { showToast('下发失败', 'error'); }
    if (btn) { btn.disabled = false; btn.textContent = '🚀 一键下发选中项'; }
}

// =============== BOM增强：Excel导入 + MRP + 在途物料 ===============
let _bomImportPreviewItems = [];
const MRP_API = '/api/v1/eng-modules';

let _bomImportName = '';

async function renderBomImport() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="content-header"><h2>📤 BOM表</h2></div>
        <div style="margin-bottom:12px;">
            <button onclick="downloadBomTemplate()" style="padding:6px 14px;background:#6366f1;color:#fff;border:none;border-radius:6px;">📥 模板下载</button>
            <label style="padding:6px 14px;background:#10b981;color:#fff;border-radius:6px;margin-left:8px;cursor:pointer;">📤 选择Excel<input type="file" accept=".xlsx,.xls" onchange="handleBomExcelUpload(event)" style="display:none;"></label>
            <span style="font-size:12px;color:#9ca3af;margin-left:8px;">导入后自动新建BOM（名称取文件名）</span>
        </div>
        <div id="bom-import-preview" style="display:none;margin-top:16px;"></div>
        <div id="proj-bom-section"></div>
        <div id="bom-list-bar"></div>
        <div id="bom-items-table" style="margin-top:16px;"></div>
    `;
    loadProjectMaterialsSection();
    loadBomListBar();
}

// 项目立项后：自动整理项目物料，请求上传BOM分类表
async function loadProjectMaterialsSection() {
    const el = document.getElementById('proj-bom-section');
    if (!el) return;
    try {
        const [pr, br] = await Promise.all([fetch(`${ENG_API}/wbs-projects/`), fetch(`${MRP_API}/boms`)]);
        const projects = await pr.json();
        const boms = await br.json();
        const pending = projects.filter(p => p.deliverable_count > 0 && !boms.some(b => (b.name || '').startsWith(p.project_no || '###')));
        if (!pending.length) { el.innerHTML = ''; return; }
        const statusMap = { PLANNING: '立项中', EXECUTING: '执行中' };
        const cards = await Promise.all(pending.map(async p => {
            let rows = '';
            try {
                const dr = await fetch(`${ENG_API}/wbs-projects/${p.id}/deliverables`);
                const items = await dr.json();
                rows = items.map(d => `<tr>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;">${d.material_code || '-'}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;">${d.material_name || '-'}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;color:#6b7280;">${d.specification || '-'}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;text-align:right;">${d.quantity}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;">${d.unit || '个'}</td>
                    <td style="padding:5px 8px;border:1px solid #e5e7eb;text-align:right;">${d.unit_price != null ? '¥' + d.unit_price.toLocaleString() : '-'}</td>
                </tr>`).join('');
            } catch (e) {}
            const no = (p.project_no || '').replace(/'/g, "\\'");
            const nm = (p.project_name || '').replace(/'/g, "\\'");
            return `<div style="margin:14px 0;background:#fff;border:1px solid #e5e7eb;border-left:4px solid #6366f1;border-radius:10px;padding:14px 16px;">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                    <div style="font-weight:600;color:#1f2937;font-size:14px;">📋 ${p.project_no || ''} ${p.project_name || ''}</div>
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span style="font-size:12px;color:#6b7280;">${statusMap[p.status] || p.status || ''} · 已自动整理 ${p.deliverable_count} 项物料</span>
                        <label style="padding:7px 16px;background:linear-gradient(135deg,#f59e0b,#d97706);color:#fff;border-radius:6px;cursor:pointer;font-size:13px;font-weight:600;">📁 上传该项目的BOM表<input type="file" accept=".xlsx,.xls" onchange="uploadProjBomFromBomPage(event,${p.id},'${no}','${nm}')" style="display:none;"></label>
                    </div>
                </div>
                <div style="font-size:12px;color:#9ca3af;margin:6px 0 10px;">请上传BOM分类表（表头：物料归属 / 零件名称 / 代号 / 工件类型 / 数量 / 材质，<a href="#" onclick="event.preventDefault();window.open('${MRP_API}/bom/project-import-template','_blank');">下载模板</a>）</div>
                <div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:12px;">
                    <thead><tr style="background:#f9fafb;">
                        <th style="padding:5px 8px;border:1px solid #e5e7eb;text-align:left;">物料编码</th>
                        <th style="padding:5px 8px;border:1px solid #e5e7eb;text-align:left;">物料名称</th>
                        <th style="padding:5px 8px;border:1px solid #e5e7eb;text-align:left;">规格型号</th>
                        <th style="padding:5px 8px;border:1px solid #e5e7eb;text-align:right;">数量</th>
                        <th style="padding:5px 8px;border:1px solid #e5e7eb;text-align:left;">单位</th>
                        <th style="padding:5px 8px;border:1px solid #e5e7eb;text-align:right;">单价</th>
                    </tr></thead>
                    <tbody>${rows || '<tr><td colspan="6" style="padding:8px;text-align:center;color:#9ca3af;">物料加载失败</td></tr>'}</tbody>
                </table></div>
            </div>`;
        }));
        el.innerHTML = cards.join('');
    } catch (e) { el.innerHTML = ''; }
}

function uploadProjBomFromBomPage(event, id, no, name) {
    showProjectBomImportDialog(id, no, name);
    handleProjectBomUpload(event);
}

// 已建BOM列表：竖排项目卡片（从上到下），点击项目卡片才展开明细 —— 与项目立项看板交互一致
let _bomOpenId = null;
async function loadBomListBar() {
    const bar = document.getElementById('bom-list-bar');
    const tbl = document.getElementById('bom-items-table');
    if (!bar) return;
    try {
        const r = await fetch(`${MRP_API}/boms`);
        let boms = await r.json();
        if (!boms.length) {
            bar.innerHTML = `<div style="margin-top:16px;padding:26px;text-align:center;background:#fff;border:1px dashed #d1d5db;border-radius:10px;color:#6b7280;font-size:13px;">暂无BOM。上方立项项目的物料已自动整理，上传分类表即可生成BOM。</div>`;
            if (tbl) tbl.innerHTML = '';
            return;
        }
        boms = boms.slice().sort((a, b) => b.id - a.id);
        bar.innerHTML = `<div style="margin:18px 0 8px;font-weight:600;color:#374151;">📚 已建BOM（点击项目卡片展开明细）</div>
        <div style="display:flex;flex-direction:column;gap:10px;">${boms.map(b => `
            <div style="background:#fff;border:1px solid #e5e7eb;border-left:4px solid ${_bomOpenId === b.id ? '#4338ca' : '#c7d2fe'};border-radius:10px;overflow:hidden;">
                <div onclick="toggleBomCard(${b.id})" style="display:flex;align-items:center;gap:12px;padding:12px 16px;cursor:pointer;flex-wrap:wrap;">
                    <div style="font-size:20px;">📁</div>
                    <div style="flex:1;min-width:200px;">
                        <div style="font-size:14px;font-weight:600;color:#1f2937;">${b.name || ('BOM#' + b.id)}</div>
                        ${b.version ? `<div style="font-size:11px;color:#9ca3af;margin-top:2px;">版本 ${b.version}</div>` : ''}
                    </div>
                    <span style="font-size:11px;color:${_bomOpenId === b.id ? '#4338ca' : '#9ca3af'};">${_bomOpenId === b.id ? '收起 ▲' : '展开明细 ▼'}</span>
                    <button title="导出该BOM明细Excel" onclick="event.stopPropagation();window.open('${MRP_API}/bom/${b.id}/export','_blank')" style="padding:4px 10px;border:1px solid #c7d2fe;border-radius:6px;background:#eef2ff;color:#4338ca;cursor:pointer;font-size:12px;">📤</button>
                </div>
                <div id="bom-card-detail-${b.id}" style="display:${_bomOpenId === b.id ? 'block' : 'none'};padding:0 16px 14px;"></div>
            </div>`).join('')}
        </div>`;
        if (tbl) tbl.innerHTML = '';
        if (_bomOpenId) renderBomCardDetail(_bomOpenId);
    } catch (e) { bar.innerHTML = ''; }
}

function toggleBomCard(bomId) {
    _bomOpenId = (_bomOpenId === bomId) ? null : bomId;
    loadBomListBar();
}

async function renderBomCardDetail(bomId) {
    const el = document.getElementById('bom-card-detail-' + bomId);
    if (!el) return;
    el.innerHTML = '<div style="color:#9ca3af;font-size:12px;padding:10px 0;">明细加载中...</div>';
    try {
        const r = await fetch(`${MRP_API}/boms/${bomId}/items`);
        const d = await r.json();
        const items = d.items || [];
        const typeMap = {MACHINABLE:'可加工', STANDARD:'标准件', PURCHASE:'外购', OUTSOURCE:'外协', ASSEMBLY:'装配'};
        if (!items.length) {
            el.innerHTML = '<div style="padding:12px;color:#9ca3af;text-align:center;background:#f8fafc;border-radius:8px;">该BOM暂无物料，请通过Excel导入</div>';
            return;
        }
        // 标准件=即买即用；自制件=需图纸定制（机加/钣焊/外协/装配）
        const stdItems = items.filter(i=>i.item_type==='STANDARD'||i.item_type==='PURCHASE');
        const madeItems = items.filter(i=>!['STANDARD','PURCHASE'].includes(i.item_type));
        const rowHtml = i=>`<tr>
            <td style="padding:6px;border:1px solid #e5e7eb;text-align:center;">${i.level||1}</td>
            <td style="padding:6px;border:1px solid #e5e7eb;">${i.material_code||'-'}</td>
            <td style="padding:6px;border:1px solid #e5e7eb;">${i.material_name||'-'}</td>
            <td style="padding:6px;border:1px solid #e5e7eb;">${i.spec||'-'}</td>
            <td style="padding:6px;border:1px solid #e5e7eb;">${typeMap[i.item_type]||i.item_type||'-'}</td>
            <td style="padding:6px;border:1px solid #e5e7eb;">${i.material_grade||'-'}</td>
            <td style="padding:6px;border:1px solid #e5e7eb;">${i.process_name||'-'}</td>
            <td style="padding:6px;border:1px solid #e5e7eb;text-align:right;">${i.quantity}</td>
            <td style="padding:6px;border:1px solid #e5e7eb;">${i.unit||'个'}</td>
        </tr>`;
        const tableHtml = (title, list, color)=>list.length ? `
            <div style="margin:14px 0 8px;font-weight:600;color:${color};">${title} (${list.length}项)</div>
            <div style="overflow-x:auto;background:#fff;border-radius:8px;">
            <table style="width:100%;border-collapse:collapse;font-size:12px;">
                <thead><tr style="background:#f3f4f6;position:sticky;top:0;">
                    <th style="padding:6px;border:1px solid #e5e7eb;">层级</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;">物料编码</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;">物料名称</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;">规格型号</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;">类型</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;">材质</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;">工艺</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;text-align:right;">数量</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;">单位</th>
                </tr></thead>
                <tbody>${list.map(rowHtml).join('')}</tbody>
            </table></div>` : '';
        el.innerHTML = tableHtml('🛒 标准件BOM', stdItems, '#2563eb') + tableHtml('🔧 自制件BOM', madeItems, '#d97706');
    } catch(e) { el.innerHTML = '<div style="color:#dc2626;font-size:12px;padding:8px 0;">加载BOM明细失败</div>'; }
}

function importProjectsExcel(input) {
    const f = input.files[0];
    if (!f) return;
    const fd = new FormData();
    fd.append('file', f);
    fetch(`${ENG_API}/wbs-projects/import`, { method: 'POST', headers: authHeaders || {}, body: fd })
        .then(r => r.json()).then(d => {
            let msg = d.message || (d.success ? '导入成功' : '导入失败');
            if (d.fail_rows && d.fail_rows.length) msg += '；' + d.fail_rows.join('；');
            showToast(msg, d.success ? (d.fail ? 'warning' : 'success') : 'error');
            input.value = '';
            if (d.success) loadProjectBoard();
        }).catch(() => showToast('导入失败', 'error'));
}

// 兼容旧调用（导入成功后刷新）：改为展开该BOM的项目卡片
async function loadBomItems(bomId) {
    _bomOpenId = bomId;
    loadBomListBar();
}

function downloadBomTemplate() { window.open(`${MRP_API}/bom/import-template`, '_blank'); }

async function handleBomExcelUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    _bomImportName = file.name.replace(/\.[^.]+$/, '');
    const fd = new FormData(); fd.append('file', file);
    try {
        const r = await fetch(`${MRP_API}/bom/import-preview`, {method:'POST', body:fd});
        const d = await r.json();
        if (d.success) {
            _bomImportPreviewItems = d.items;
            renderBomImportPreview();
            showToast(`解析到 ${d.total} 项，请确认后导入`);
        } else showToast(d.detail||'解析失败', 'error');
    } catch(e) { showToast('解析失败', 'error'); }
    event.target.value='';
}

function renderBomImportPreview() {
    const typeMap = {MACHINABLE:'可加工', STANDARD:'标准件', PURCHASE:'外购', OUTSOURCE:'外协', ASSEMBLY:'装配'};
    document.getElementById('bom-import-preview').style.display='block';
    document.getElementById('bom-import-preview').innerHTML = `
        <h4 style="margin:0 0 8px;">预览 (${_bomImportPreviewItems.length}项)</h4>
        <div style="overflow-x:auto;">
        <table class="data-table" style="width:100%;border-collapse:collapse;font-size:12px;background:#fff;">
            <thead><tr style="background:#e5e7eb;">
                <th style="padding:6px;border:1px solid #d1d5db;">层级</th><th style="padding:6px;border:1px solid #d1d5db;">编码</th>
                <th style="padding:6px;border:1px solid #d1d5db;">工件类型</th><th style="padding:6px;border:1px solid #d1d5db;">规格</th>
                <th style="padding:6px;border:1px solid #d1d5db;">品名</th><th style="padding:6px;border:1px solid #d1d5db;">材质</th>
                <th style="padding:6px;border:1px solid #d1d5db;">表面处理</th><th style="padding:6px;border:1px solid #d1d5db;">工艺</th>
                <th style="padding:6px;border:1px solid #d1d5db;">数量</th><th style="padding:6px;border:1px solid #d1d5db;">单位</th>
            </tr></thead>
            <tbody>${_bomImportPreviewItems.map(i=>`<tr>
                <td style="padding:6px;border:1px solid #d1d5db;">${i.bom_level}</td>
                <td style="padding:6px;border:1px solid #d1d5db;">${i.material_code||'-'}</td>
                <td style="padding:6px;border:1px solid #d1d5db;">${typeMap[i.item_type]||i.item_type}</td>
                <td style="padding:6px;border:1px solid #d1d5db;">${i.spec||'-'}</td>
                <td style="padding:6px;border:1px solid #d1d5db;">${i.material_name}</td>
                <td style="padding:6px;border:1px solid #d1d5db;">${i.material_grade||'-'}</td>
                <td style="padding:6px;border:1px solid #d1d5db;">${i.surface_treatment||'-'}</td>
                <td style="padding:6px;border:1px solid #d1d5db;">${i.process_name||'-'}</td>
                <td style="padding:6px;border:1px solid #d1d5db;">${i.quantity}</td>
                <td style="padding:6px;border:1px solid #d1d5db;">${i.unit}</td>
            </tr>`).join('')}</tbody>
        </table></div>
        <div style="margin-top:8px;">
            <button onclick="confirmBomImport()" style="padding:6px 14px;background:#10b981;color:#fff;border:none;border-radius:6px;">确认导入</button>
            <button onclick="document.getElementById('bom-import-preview').style.display='none'" style="padding:6px 14px;background:#9ca3af;color:#fff;border:none;border-radius:6px;margin-left:8px;">取消</button>
        </div>
    `;
}

async function confirmBomImport() {
    try {
        const r = await fetch(`${MRP_API}/bom/0/import-confirm`, {
            method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({items:_bomImportPreviewItems, bom_name:_bomImportName})
        });
        const d = await r.json();
        if (d.success) {
            showToast(`成功导入 ${d.imported} 项`);
            _bomImportPreviewItems = [];
            document.getElementById('bom-import-preview').style.display = 'none';
            // 刷新显示BOM明细表格
            loadBomItems(d.bom_id);
        }
        else showToast('导入失败', 'error');
    } catch(e) { showToast('导入失败', 'error'); }
}

async function renderMrpCommonMaterials() {
    const content = document.getElementById('content');
    content.innerHTML = `<div class="content-header"><h2>📦 共用物料计算</h2></div><div id="common-mat-list">加载中...</div>`;
    try {
        const r = await fetch(`${MRP_API}/mrp/common-materials`);
        const list = await r.json();
        const typeMap = {MACHINABLE:'可加工', STANDARD:'标准件', PURCHASE:'外购', OUTSOURCE:'外协', ASSEMBLY:'装配'};
        const el = document.getElementById('common-mat-list');
        if (!list.length) { el.innerHTML = '<p style="color:#9ca3af;">暂无BOM物料</p>'; return; }
        el.innerHTML = `<table class="data-table" style="width:100%;border-collapse:collapse;font-size:13px;">
            <thead><tr style="background:#f3f4f6;">
                <th style="padding:8px;border:1px solid #e5e7eb;">编码</th><th style="padding:8px;border:1px solid #e5e7eb;">品名</th>
                <th style="padding:8px;border:1px solid #e5e7eb;">规格</th><th style="padding:8px;border:1px solid #e5e7eb;">类型</th>
                <th style="padding:8px;border:1px solid #e5e7eb;">总需求</th><th style="padding:8px;border:1px solid #e5e7eb;">库存</th>
                <th style="padding:8px;border:1px solid #e5e7eb;">欠料</th><th style="padding:8px;border:1px solid #e5e7eb;">状态</th>
            </tr></thead>
            <tbody>${list.map(m=>`<tr style="${m.deficit_qty>0?'background:#fee2e2;':''}">
                <td style="padding:8px;border:1px solid #e5e7eb;">${m.material_code||'-'}</td>
                <td style="padding:8px;border:1px solid #e5e7eb;">${m.material_name}</td>
                <td style="padding:8px;border:1px solid #e5e7eb;">${m.spec||'-'}</td>
                <td style="padding:8px;border:1px solid #e5e7eb;">${typeMap[m.item_type]||m.item_type}</td>
                <td style="padding:8px;border:1px solid #e5e7eb;">${m.total_qty}${m.unit}</td>
                <td style="padding:8px;border:1px solid #e5e7eb;">${m.stock_qty}</td>
                <td style="padding:8px;border:1px solid #e5e7eb;color:${m.deficit_qty>0?'#dc2626':'#16a34a'};font-weight:bold;">${m.deficit_qty}</td>
                <td style="padding:8px;border:1px solid #e5e7eb;">${m.deficit_qty>0?'🔴缺料':'🟢充足'}</td>
            </tr>`).join('')}</tbody></table>`;
    } catch(e) { showToast('加载失败', 'error'); }
}

async function renderMrpForward() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="content-header"><h2>📊 MRP正推欠料</h2></div>
        <div style="margin-bottom:12px;">
            <select id="mrp-bom-select" style="padding:6px 12px;border:1px solid #d1d5db;border-radius:6px;min-width:280px;"><option value="">-- 选择BOM --</option></select>
            <input id="mrp-order-qty" type="number" value="1" min="1" style="padding:6px;border:1px solid #d1d5db;border-radius:6px;width:80px;margin-left:8px;">
            <button onclick="loadMrpForward()" style="padding:6px 14px;background:#3b82f6;color:#fff;border:none;border-radius:6px;margin-left:8px;">计算欠料</button>
        </div>
        <div id="mrp-forward-result"></div>
    `;
    try {
        const r = await fetch('/api/v1/eng-modules/boms');
        const boms = await r.json();
        document.getElementById('mrp-bom-select').innerHTML = '<option value="">-- 选择BOM --</option>' + boms.map(b=>`<option value="${b.id}">${b.bom_code||''} ${b.name||''}</option>`).join('');
    } catch(e) {}
}

async function loadMrpForward() {
    const bomId = document.getElementById('mrp-bom-select').value;
    const qty = document.getElementById('mrp-order-qty').value || 1;
    if (!bomId) { showToast('请选择BOM', 'warning'); return; }
    try {
        const r = await fetch(`${MRP_API}/mrp/forward?bom_id=${bomId}&order_qty=${qty}`);
        const d = await r.json();
        const typeMap = {MACHINABLE:'可加工', STANDARD:'标准件', PURCHASE:'外购', OUTSOURCE:'外协', ASSEMBLY:'装配'};
        const catMap = {self_made:'自制欠料', purchase:'外购欠料', outsource:'外协欠料'};
        let html = `<div style="margin-bottom:12px;padding:8px;background:#fef3c7;border-radius:6px;">
            <strong>摘要：</strong>自制缺料${d.summary.self_made_shortage}项 | 外购缺料${d.summary.purchase_shortage}项 | 外协缺料${d.summary.outsource_shortage}项
        </div>`;
        for (const cat of ['self_made','purchase','outsource']) {
            const rows = d[cat];
            html += `<h4 style="margin:12px 0 6px;">${catMap[cat]} (${rows.length}项)</h4>`;
            if (!rows.length) { html += '<p style="color:#9ca3af;">无</p>'; continue; }
            html += `<table class="data-table" style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:12px;">
                <thead><tr style="background:#f3f4f6;">
                    <th style="padding:6px;border:1px solid #e5e7eb;">编码</th><th style="padding:6px;border:1px solid #e5e7eb;">品名</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;">类型</th><th style="padding:6px;border:1px solid #e5e7eb;">总需求</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;">库存</th><th style="padding:6px;border:1px solid #e5e7eb;">在途</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;">欠料</th>
                </tr></thead>
                <tbody>${rows.map(r=>`<tr style="${r.shortage?'background:#fee2e2;':''}">
                    <td style="padding:6px;border:1px solid #e5e7eb;">${r.material_code||'-'}</td>
                    <td style="padding:6px;border:1px solid #e5e7eb;">${r.material_name}</td>
                    <td style="padding:6px;border:1px solid #e5e7eb;">${typeMap[r.item_type]||r.item_type}</td>
                    <td style="padding:6px;border:1px solid #e5e7eb;">${r.total_req}${r.unit}</td>
                    <td style="padding:6px;border:1px solid #e5e7eb;">${r.stock_qty}</td>
                    <td style="padding:6px;border:1px solid #e5e7eb;">${r.intransit_qty}</td>
                    <td style="padding:6px;border:1px solid #e5e7eb;color:${r.shortage?'#dc2626':'#16a34a'};font-weight:bold;">${r.deficit_qty}</td>
                </tr>`).join('')}</tbody></table>`;
        }
        document.getElementById('mrp-forward-result').innerHTML = html;
    } catch(e) { showToast('计算失败', 'error'); }
}

async function renderMrpBackward() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="content-header"><h2>🔄 逆推可生产量</h2></div>
        <div style="margin-bottom:12px;">
            <select id="back-bom-select" style="padding:6px 12px;border:1px solid #d1d5db;border-radius:6px;min-width:280px;"><option value="">-- 选择BOM --</option></select>
            <button onclick="loadMrpBackward()" style="padding:6px 14px;background:#3b82f6;color:#fff;border:none;border-radius:6px;margin-left:8px;">计算</button>
        </div>
        <div id="mrp-backward-result"></div>
    `;
    try {
        const r = await fetch('/api/v1/eng-modules/boms');
        const boms = await r.json();
        document.getElementById('back-bom-select').innerHTML = '<option value="">-- 选择BOM --</option>' + boms.map(b=>`<option value="${b.id}">${b.bom_code||''} ${b.name||''}</option>`).join('');
    } catch(e) {}
}

async function loadMrpBackward() {
    const bomId = document.getElementById('back-bom-select').value;
    if (!bomId) { showToast('请选择BOM', 'warning'); return; }
    try {
        const r = await fetch(`${MRP_API}/mrp/backward?bom_id=${bomId}`);
        const d = await r.json();
        const typeMap = {MACHINABLE:'可加工', STANDARD:'标准件', PURCHASE:'外购', OUTSOURCE:'外协', ASSEMBLY:'装配'};
        let html = `<div style="margin-bottom:12px;padding:12px;background:#dbeafe;border-radius:6px;font-size:18px;">
            🎯 基于当前库存，最多可生产：<strong style="color:#1d4ed8;font-size:24px;">${d.max_production}</strong> 套成品
        </div>`;
        html += `<table class="data-table" style="width:100%;border-collapse:collapse;font-size:12px;">
            <thead><tr style="background:#f3f4f6;">
                <th style="padding:6px;border:1px solid #e5e7eb;">编码</th><th style="padding:6px;border:1px solid #e5e7eb;">品名</th>
                <th style="padding:6px;border:1px solid #e5e7eb;">类型</th><th style="padding:6px;border:1px solid #e5e7eb;">单耗</th>
                <th style="padding:6px;border:1px solid #e5e7eb;">库存</th><th style="padding:6px;border:1px solid #e5e7eb;">可生产</th>
            </tr></thead>
            <tbody>${d.capacities.map(c=>`<tr style="${c.capacity<=d.max_production?'background:#fef3c7;':''}">
                <td style="padding:6px;border:1px solid #e5e7eb;">${c.material_code||'-'}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;">${c.material_name}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;">${typeMap[c.item_type]||c.item_type}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;">${c.unit_qty}${c.unit}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;">${c.stock_qty}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;font-weight:bold;">${c.capacity}</td>
            </tr>`).join('')}</tbody></table>`;
        document.getElementById('mrp-backward-result').innerHTML = html;
    } catch(e) { showToast('计算失败', 'error'); }
}

async function renderInTransitMaterials() {
    const content = document.getElementById('content');
    content.innerHTML = `
        <div class="content-header"><h2>🚚 在途物料管理</h2></div>
        <div style="margin-bottom:12px;">
            <button onclick="showInTransitAddForm()" style="padding:6px 14px;background:#3b82f6;color:#fff;border:none;border-radius:6px;">➕ 添加在途物料</button>
        </div>
        <div id="intransit-list">加载中...</div>
    `;
    loadInTransitList();
}

function showInTransitAddForm() {
    const el = document.getElementById('intransit-list');
    el.innerHTML = `
        <div style="background:#f0f9ff;padding:12px;border-radius:8px;margin-bottom:12px;">
            <h4 style="margin:0 0 8px;">添加在途物料</h4>
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
                <input id="it-code" placeholder="存货编码" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;width:120px;">
                <input id="it-name" placeholder="品名" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;width:150px;">
                <input id="it-spec" placeholder="规格" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;width:120px;">
                <input id="it-qty" type="number" placeholder="数量" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;width:80px;">
                <select id="it-type" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;">
                    <option value="PURCHASE">采购在途</option><option value="OUTSOURCE">外协在途</option>
                </select>
                <input id="it-supplier" placeholder="供应商" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;width:120px;">
                <input id="it-order" placeholder="订单号" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;width:120px;">
                <button onclick="submitInTransit()" style="padding:6px 14px;background:#3b82f6;color:#fff;border:none;border-radius:4px;">保存</button>
                <button onclick="loadInTransitList()" style="padding:6px 14px;background:#9ca3af;color:#fff;border:none;border-radius:4px;">取消</button>
            </div>
        </div>
        <div id="intransit-list-content"></div>
    `;
    // 列表放下面
    setTimeout(()=>loadInTransitList('intransit-list-content'), 100);
}

async function submitInTransit() {
    const name = document.getElementById('it-name').value.trim();
    if (!name) { showToast('请输入品名', 'warning'); return; }
    try {
        const r = await fetch(`${MRP_API}/in-transit-materials`, {
            method:'POST', headers:{'Content-Type':'application/json'},
            body:JSON.stringify({
                material_code:document.getElementById('it-code').value.trim(),
                material_name:name, spec:document.getElementById('it-spec').value.trim(),
                quantity:parseFloat(document.getElementById('it-qty').value)||0,
                transit_type:document.getElementById('it-type').value,
                supplier:document.getElementById('it-supplier').value.trim(),
                order_no:document.getElementById('it-order').value.trim(),
            })
        });
        const d = await r.json();
        if (d.success) { showToast('添加成功'); renderInTransitMaterials(); }
        else showToast('添加失败', 'error');
    } catch(e) { showToast('添加失败', 'error'); }
}

async function loadInTransitList(targetId) {
    try {
        const r = await fetch(`${MRP_API}/in-transit-materials`);
        const list = await r.json();
        const typeMap = {PURCHASE:'采购', OUTSOURCE:'外协'};
        const statusMap = {ORDERED:'已下单', SHIPPED:'已发货', ARRIVED:'已到货'};
        const elId = targetId || 'intransit-list';
        const el = document.getElementById(elId);
        if (!el) return;
        if (!list.length) { el.innerHTML = '<p style="color:#9ca3af;">暂无在途物料</p>'; return; }
        el.innerHTML = `<table class="data-table" style="width:100%;border-collapse:collapse;font-size:12px;">
            <thead><tr style="background:#f3f4f6;">
                <th style="padding:6px;border:1px solid #e5e7eb;">编码</th><th style="padding:6px;border:1px solid #e5e7eb;">品名</th>
                <th style="padding:6px;border:1px solid #e5e7eb;">规格</th><th style="padding:6px;border:1px solid #e5e7eb;">数量</th>
                <th style="padding:6px;border:1px solid #e5e7eb;">类型</th><th style="padding:6px;border:1px solid #e5e7eb;">供应商</th>
                <th style="padding:6px;border:1px solid #e5e7eb;">订单号</th><th style="padding:6px;border:1px solid #e5e7eb;">状态</th>
                <th style="padding:6px;border:1px solid #e5e7eb;">操作</th>
            </tr></thead>
            <tbody>${list.map(i=>`<tr>
                <td style="padding:6px;border:1px solid #e5e7eb;">${i.material_code||'-'}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;">${i.material_name}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;">${i.specification||'-'}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;">${i.quantity}${i.unit}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;">${typeMap[i.transit_type]||i.transit_type}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;">${i.supplier||'-'}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;">${i.order_no||'-'}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;">${statusMap[i.status]||i.status}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;">
                    ${i.status!=='ARRIVED'?`<button onclick="updateInTransitStatus(${i.id},'SHIPPED')" style="color:#3b82f6;border:none;background:none;cursor:pointer;">发货</button>`:''}
                    ${i.status!=='ARRIVED'?`<button onclick="updateInTransitStatus(${i.id},'ARRIVED')" style="color:#10b981;border:none;background:none;cursor:pointer;margin-left:4px;">到货</button>`:''}
                    <button onclick="deleteInTransit(${i.id})" style="color:#ef4444;border:none;background:none;cursor:pointer;margin-left:4px;">删</button>
                </td>
            </tr>`).join('')}</tbody></table>`;
    } catch(e) { showToast('加载失败', 'error'); }
}

async function updateInTransitStatus(id, status) {
    try {
        const r = await fetch(`${MRP_API}/in-transit-materials/${id}/status`, {
            method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({status})
        });
        const d = await r.json();
        if (d.success) { showToast('状态已更新'); renderInTransitMaterials(); }
    } catch(e) { showToast('更新失败', 'error'); }
}

async function deleteInTransit(id) {
    try {
        const r = await fetch(`${MRP_API}/in-transit-materials/${id}`, {method:'DELETE'});
        const d = await r.json();
        if (d.success) { showToast('已删除'); renderInTransitMaterials(); }
    } catch(e) { showToast('删除失败', 'error'); }
}

async function renderOrderMaterialAnalysis() {
    const content = document.getElementById('content') || document.getElementById('eng-content');
    if (!content) return;
    content.innerHTML = `
        <div class="content-header"><h2>📋 订单物料分析</h2></div>
        <div style="margin-bottom:12px;">
            <select id="analysis-so-select" style="padding:6px 12px;border:1px solid #d1d5db;border-radius:6px;min-width:320px;"><option value="">-- 选择销售订单 --</option></select>
            <button onclick="loadOrderMaterialAnalysis()" style="padding:6px 14px;background:#3b82f6;color:#fff;border:none;border-radius:6px;margin-left:8px;">分析</button>
        </div>
        <div id="analysis-result"></div>
    `;
    try {
        const r = await fetch(`${MRP_API}/sales-orders`);
        const orders = await r.json();
        document.getElementById('analysis-so-select').innerHTML = '<option value="">-- 选择销售订单 --</option>' + orders.map(o=>`<option value="${o.id}">${o.so_no} | ${o.customer_name} | 数量${o.total_qty}</option>`).join('');
    } catch(e) {}
}

async function loadOrderMaterialAnalysis() {
    const soId = document.getElementById('analysis-so-select').value;
    if (!soId) { showToast('请选择销售订单', 'warning'); return; }
    try {
        const r = await fetch(`${MRP_API}/sales-orders/${soId}/material-analysis`);
        const d = await r.json();
        if (d.detail) { showToast(d.detail, 'error'); return; }
        let html = `<div style="margin-bottom:12px;padding:8px;background:${d.shortage_count>0?'#fee2e2':'#d1fae5'};border-radius:6px;">
            订单：<strong>${d.so_no}</strong> | 物料总数：${d.total} | <span style="color:#dc2626;font-weight:bold;">缺料：${d.shortage_count}项</span>
        </div>`;
        if (!d.materials || d.materials.length === 0) {
            html += '<div class="empty">该订单产品未关联BOM或BOM无物料数据</div>';
        } else {
            html += `<table class="data-table" style="width:100%;border-collapse:collapse;font-size:12px;">
                <thead><tr style="background:#f3f4f6;">
                    <th style="padding:6px;border:1px solid #e5e7eb;">物料代码</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;">物料名称</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;">规格型号</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;">需求数量</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;">可分配库存</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;">缺料量</th>
                </tr></thead>
                <tbody>${d.materials.map(m=>`<tr style="${m.shortage?'background:#fee2e2;':''}">
                    <td style="padding:6px;border:1px solid #e5e7eb;">${m.material_code||'-'}</td>
                    <td style="padding:6px;border:1px solid #e5e7eb;">${m.material_name||'-'}</td>
                    <td style="padding:6px;border:1px solid #e5e7eb;">${m.spec||'-'}</td>
                    <td style="padding:6px;border:1px solid #e5e7eb;">${m.demand_qty}${m.unit||''}</td>
                    <td style="padding:6px;border:1px solid #e5e7eb;">${m.allocatable_qty}</td>
                    <td style="padding:6px;border:1px solid #e5e7eb;color:${m.shortage?'#dc2626':'#16a34a'};font-weight:bold;">${m.deficit_qty}</td>
                </tr>`).join('')}</tbody></table>`;
        }
        document.getElementById('analysis-result').innerHTML = html;
    } catch(e) { showToast('分析失败', 'error'); }
}

async function renderShortageSchedule() {
    const content = document.getElementById('content') || document.getElementById('eng-content');
    if (!content) return;
    const today = new Date().toISOString().split('T')[0];
    const future = new Date(Date.now() + 30*86400000).toISOString().split('T')[0];
    content.innerHTML = `
        <div class="content-header"><h2>📊 物料欠料表</h2></div>
        <div style="margin-bottom:12px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
            <input type="date" id="sch-start" value="${today}" style="padding:6px;border:1px solid #d1d5db;border-radius:6px;">
            <span>至</span>
            <input type="date" id="sch-end" value="${future}" style="padding:6px;border:1px solid #d1d5db;border-radius:6px;">
            <button onclick="loadShortageSchedule()" style="padding:6px 14px;background:#3b82f6;color:#fff;border:none;border-radius:6px;">查询</button>
        </div>
        <div id="sch-result"></div>
    `;
    loadShortageSchedule();
}

async function loadShortageSchedule() {
    const sd = document.getElementById('sch-start').value;
    const ed = document.getElementById('sch-end').value;
    if (!sd || !ed) { showToast('请选择日期范围', 'warning'); return; }
    try {
        const r = await fetch(`${MRP_API}/mrp/shortage-schedule?start_date=${sd}&end_date=${ed}`);
        const d = await r.json();
        if (d.detail) { showToast(d.detail, 'error'); return; }
        const result = document.getElementById('sch-result');
        if (!d.materials || d.materials.length === 0) {
            result.innerHTML = '<div class="empty">无物料需求数据</div>';
            return;
        }
        // 日期列头
        const dateHeaders = d.dates.map(dt => {
            const date = new Date(dt);
            const month = date.getMonth()+1;
            const day = date.getDate();
            const weekDay = ['日','一','二','三','四','五','六'][date.getDay()];
            return `<th style="padding:6px 4px;border:1px solid #e5e7eb;min-width:70px;writing-mode:vertical-lr;">${month}-${day}<br>${weekDay}</th>`;
        }).join('');
        // 行
        let rowHtml = '';
        d.materials.forEach((m, idx) => {
            const rowBg = m.shortage ? 'background:#fee2e2;' : '';
            const dailyCells = d.dates.map(dt => {
                const qty = m.daily[dt] || 0;
                return `<td style="padding:6px 4px;border:1px solid #e5e7eb;text-align:center;${qty>0?'background:#fef08a;':''}">${qty>0?qty:''}</td>`;
            }).join('');
            rowHtml += `<tr style="${rowBg}">
                <td style="padding:6px;border:1px solid #e5e7eb;text-align:center;">${idx+1}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;white-space:nowrap;">${m.material_code||'-'}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;white-space:nowrap;">${m.material_name||'-'}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;white-space:nowrap;">${m.spec||'-'}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;text-align:right;">${m.allocatable_qty}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;text-align:right;">${m.total_demand}</td>
                <td style="padding:6px;border:1px solid #e5e7eb;text-align:right;color:${m.shortage?'#dc2626':'#16a34a'};font-weight:bold;">${m.deficit_qty}</td>
                ${dailyCells}
            </tr>`;
        });
        result.innerHTML = `
            <div style="margin-bottom:12px;padding:8px;background:${d.shortage_count>0?'#fee2e2':'#d1fae5'};border-radius:6px;">
                物料总数：${d.total} | <span style="color:#dc2626;font-weight:bold;">缺料：${d.shortage_count}项</span> | 日期范围：${d.start_date} ~ ${d.end_date}
            </div>
            <div style="overflow-x:auto;max-height:calc(100vh - 200px);overflow-y:auto;">
            <table style="border-collapse:collapse;font-size:12px;min-width:100%;">
                <thead><tr style="background:#f3f4f6;position:sticky;top:0;z-index:2;">
                    <th style="padding:6px;border:1px solid #e5e7eb;position:sticky;left:0;z-index:3;background:#f3f4f6;min-width:40px;">序</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;position:sticky;left:40px;z-index:3;background:#f3f4f6;min-width:100px;">物料代码</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;position:sticky;left:140px;z-index:3;background:#f3f4f6;min-width:120px;">物料名称</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;position:sticky;left:260px;z-index:3;background:#f3f4f6;min-width:120px;">规格型号</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;min-width:80px;">可分配库存</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;min-width:70px;">总需求</th>
                    <th style="padding:6px;border:1px solid #e5e7eb;min-width:70px;">缺料量</th>
                    ${dateHeaders}
                </tr></thead>
                <tbody>${rowHtml}</tbody>
            </table>
            </div>
        `;
    } catch(e) { showToast('加载失败', 'error'); }
}

// =============== 我的工厂模块 ===============
const FACTORY_API = '/api/v1/factory';
let _factoryChart1 = null;
let _factoryChart2 = null;

function renderMyFactory() {
    const content = document.getElementById('content');
    if (!content) return;
    content.innerHTML = `
        <div class="content-header"><h2>🏭 我的工厂</h2></div>
        <div class="finance-tabs" id="factory-tabs">
            <button class="finance-tab active" onclick="switchFactoryTab('equipment', this)">🔧 设备台账</button>
            <button class="finance-tab" onclick="switchFactoryTab('capacity', this)">📊 产能上报</button>
            <button class="finance-tab" onclick="switchFactoryTab('projcap', this)">🏭 项目产能</button>
            <button class="finance-tab" onclick="switchFactoryTab('progress', this)">📈 进度线</button>
            <button class="finance-tab" onclick="switchFactoryTab('util', this)">💧 水电费</button>
        </div>
        <div id="factory-content"></div>
    `;
    loadFactoryEquipments();
}

function switchFactoryTab(tab, btnEl) {
    document.querySelectorAll('#factory-tabs .finance-tab').forEach(b => b.classList.remove('active'));
    if (btnEl) btnEl.classList.add('active');
    if (tab === 'equipment') loadFactoryEquipments();
    else if (tab === 'capacity') loadCapacityRecords();
    else if (tab === 'projcap') loadFactoryProjectCapacity();
    else if (tab === 'progress') loadCapacityProgress();
    else if (tab === 'util') loadFactoryUtilityFee();
}

// ---------- 设备每日水电费（自动计提→财务制造费用）----------
async function loadFactoryUtilityFee() {
    const el = document.getElementById('factory-content');
    if (!el) return;
    el.innerHTML = '<div class="empty">加载中...</div>';
    try {
        const r = await fetch('/api/v1/factory/utility-fee', { headers: authHeaders });
        const d = await r.json();
        if (!d.success) throw new Error(d.message || '加载失败');
        const data = d.data || {};
        const byEq = data.by_equipment || [];
        const byDate = data.by_date || [];
        const maxDay = Math.max(1, ...byDate.map(x => x.amount));
        el.innerHTML = `
        <div style="margin-bottom:14px;padding:12px 16px;background:linear-gradient(90deg,#e0f2fe,#f0f9ff);border-radius:10px;border:1px solid #bae6fd;">
            <span style="font-size:15px;font-weight:700;color:#0369a1;">💧 本月车间设备水电费合计：<span style="font-size:20px;color:#0284c7;">¥${(data.total||0).toFixed(2)}</span></span>
            <span style="margin-left:10px;color:#64748b;font-size:12px;">系统每日自动计提，凭证已记入财务（制造费用）</span>
        </div>
        <h3 style="margin:14px 0 8px;font-size:14px;">各设备月度水电费（元）</h3>
        <table class="data-table"><thead><tr>
            <th>设备</th><th>计提天数</th><th>电费</th><th>水费</th><th>合计</th>
        </tr></thead><tbody>
        ${byEq.map(e => `<tr>
            <td>${e.name} <span style="color:#94a3b8;font-size:11px;">${e.code||''}</span></td>
            <td>${e.days} 天</td>
            <td>¥${e.electric.toFixed(2)}</td>
            <td>¥${e.water.toFixed(2)}</td>
            <td style="font-weight:700;color:#0284c7;">¥${e.total.toFixed(2)}</td>
        </tr>`).join('')}
        </tbody></table>
        <h3 style="margin:18px 0 8px;font-size:14px;">每日水电费（元）</h3>
        <div style="margin-bottom:16px;">
        ${byDate.map(x => `
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                <div style="width:86px;color:#475569;font-size:12px;">${x.date.slice(5)}</div>
                <div style="flex:1;background:#e2e8f0;border-radius:6px;overflow:hidden;">
                    <div style="width:${(x.amount/maxDay*100).toFixed(1)}%;background:linear-gradient(90deg,#38bdf8,#0284c7);height:18px;border-radius:6px;"></div>
                </div>
                <div style="width:70px;text-align:right;font-weight:700;color:#0284c7;font-size:12px;">¥${x.amount.toFixed(2)}</div>
            </div>`).join('')}
        </div>`;
    } catch (e) {
        el.innerHTML = `<div class="empty">水电费数据加载失败：${e.message}</div>`;
    }
}

// ---------- 项目产能（按项目看产能占用）----------
let _fcOpenProject = null;
async function loadFactoryProjectCapacity() {
    const el = document.getElementById('factory-content');
    if (!el) return;
    el.innerHTML = '<div class="empty">加载中...</div>';
    try {
        const r = await fetch('/api/v1/pp/production-plan', { headers: authHeaders });
        const d = await r.json();
        if (!d.success) throw new Error(d.message || '加载失败');
        const pp = d.data;
        const tasks = pp.tasks || [];
        const totalCap = pp.total_capacity || 0;
        // 按项目聚合排产任务
        const projects = {};
        tasks.forEach(t => {
            const key = t.project_no || t.project_name || '未知项目';
            if (!projects[key]) projects[key] = { name: t.project_name || key, no: t.project_no || '', parts: 0, qty: 0, days: 0, dailyNeed: 0, risk: 0, starts: [], ends: [], deliveries: [], items: [] };
            const p = projects[key];
            p.parts += 1;
            p.qty += (t.qty || 0);
            p.days += (t.needed_days || 0);
            p.dailyNeed += (t.qty || 0) / Math.max(1, t.needed_days || 1);
            if (t.risk === 'OVERDUE' || t.risk === 'TIGHT') p.risk += 1;
            if (t.suggested_start) p.starts.push(t.suggested_start);
            if (t.suggested_end) p.ends.push(t.suggested_end);
            if (t.delivery_date) p.deliveries.push(t.delivery_date);
            p.items.push(t);
        });
        const list = Object.values(projects).sort((a, b) => b.dailyNeed - a.dailyNeed);
        const usedCap = list.reduce((s, p) => s + p.dailyNeed, 0);
        const usage = totalCap > 0 ? Math.min(100, Math.round(usedCap / totalCap * 100)) : 0;
        const capColor = usage >= 100 ? '#dc2626' : usage >= 80 ? '#ea580c' : '#16a34a';
        const barColor = v => v >= 100 ? '#dc2626' : v >= 80 ? '#ea580c' : '#16a34a';
        if (!list.length) {
            el.innerHTML = `<div style="padding:40px;text-align:center;color:#9ca3af;">
                <div style="font-size:36px;margin-bottom:10px;">🏭</div>
                <div>暂无项目排产任务 — 项目完成技术拆解（可加工/可装配件）后自动进入产能核算</div>
                <div style="margin-top:12px;"><button class="btn btn-primary" onclick="switchFactoryTab('capacity', document.querySelectorAll('#factory-tabs .finance-tab')[1])">📊 去上报产能</button></div>
            </div>`;
            return;
        }
        const itemRow = t => `<tr>
            <td style="border:1px solid #e5e7eb;padding:6px 8px;"><b>${escapeHtml(t.part_name)}</b> <span style="color:#6b7280;font-size:11px;">${escapeHtml(t.spec || '')}</span><br><span style="font-size:10px;color:#9ca3af;font-family:monospace;">${escapeHtml(t.part_code || '')}</span></td>
            <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">${escapeHtml(t.category || '-')}</td>
            <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:right;font-weight:bold;color:#b45309;">${t.qty} ${escapeHtml(t.unit || '')}</td>
            <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">${t.needed_days ? t.needed_days + ' 天' : '—'}</td>
            <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;font-size:11px;">${t.suggested_start ? t.suggested_start + ' ~ ' + t.suggested_end : '—'}</td>
            <td style="border:1px solid #e5e7eb;padding:6px 8px;text-align:center;">${_ppRiskChip(t)}</td>
        </tr>`;
        el.innerHTML = `
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px;">
            <div style="background:linear-gradient(135deg,#f0fdf4,#dcfce7);border:1px solid #bbf7d0;border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:22px;font-weight:bold;color:#15803d;">${totalCap}${escapeHtml(pp.capacity_unit || '')}</div><div style="font-size:11px;color:#666;margin-top:3px;">全厂日产能（运行设备合计）</div></div>
            <div style="background:linear-gradient(135deg,#f0f9ff,#e0f2fe);border:1px solid #bae6fd;border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:22px;font-weight:bold;color:#0369a1;">${list.length}</div><div style="font-size:11px;color:#666;margin-top:3px;">排产项目（个）</div></div>
            <div style="background:linear-gradient(135deg,#fffbeb,#fef3c7);border:1px solid #fde68a;border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:22px;font-weight:bold;color:#b45309;">${Math.round(usedCap * 10) / 10}${escapeHtml(pp.capacity_unit || '')}/天</div><div style="font-size:11px;color:#666;margin-top:3px;">项目日产能占用合计</div></div>
            <div style="background:linear-gradient(135deg,#fef2f2,#fee2e2);border:1px solid #fecaca;border-radius:10px;padding:12px;text-align:center;">
                <div style="font-size:22px;font-weight:bold;color:${capColor};">${usage}%</div><div style="font-size:11px;color:#666;margin-top:3px;">全厂产能占用率</div></div>
        </div>
        <div style="margin-bottom:12px;font-size:12px;color:#6b7280;">💡 按项目看产能占用：占用率 = 项目日需求产量 ÷ 全厂日产能。${totalCap > 0 && usage > 100 ? '<span style="color:#dc2626;font-weight:bold;">⚠ 当前已超负荷，建议增加设备产能或调整交付日期！</span>' : ''}</div>
        <div style="display:flex;flex-direction:column;gap:10px;">
        ${list.map(p => {
            const pUsage = totalCap > 0 ? Math.min(100, Math.round(p.dailyNeed / totalCap * 100)) : 0;
            const open = _fcOpenProject === p.no;
            const start = p.starts.length ? p.starts.slice().sort()[0] : null;
            const end = p.ends.length ? p.ends.slice().sort()[p.ends.length - 1] : null;
            return `<div style="background:#fff;border:1px solid #e5e7eb;border-left:4px solid ${open ? '#16a34a' : '#bbf7d0'};border-radius:10px;overflow:hidden;">
                <div onclick="toggleFcProject('${escapeHtml(p.no)}')" style="display:flex;align-items:center;gap:12px;padding:12px 16px;cursor:pointer;flex-wrap:wrap;">
                    <div style="font-size:20px;">📁</div>
                    <div style="flex:1;min-width:200px;">
                        <div style="font-size:14px;font-weight:600;color:#1f2937;">${escapeHtml(p.name)}</div>
                        <div style="font-size:11px;color:#9ca3af;margin-top:2px;">${escapeHtml(p.no)} · 零件 ${p.parts} 项 / 共 ${p.qty} 件 · 所需 ${p.days} 天</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:13px;font-weight:bold;color:#b45309;">${Math.round(p.dailyNeed * 10) / 10}${escapeHtml(pp.capacity_unit || '')}/天</div>
                        <div style="font-size:10px;color:#9ca3af;">建议 ${start || '—'} ~ ${end || '—'}</div>
                    </div>
                    <div style="width:140px;">
                        <div style="background:#f1f5f9;border-radius:6px;height:14px;overflow:hidden;position:relative;">
                            <div style="height:100%;width:${pUsage}%;background:${barColor(pUsage)};border-radius:6px;"></div>
                        </div>
                        <div style="font-size:10px;color:${barColor(pUsage)};margin-top:2px;font-weight:bold;">占用 ${pUsage}%</div>
                    </div>
                    ${p.risk > 0 ? `<span style="padding:3px 10px;border-radius:12px;font-size:11px;background:#fee2e2;color:#b91c1c;font-weight:bold;">${p.risk} 项风险</span>` : ''}
                    <span style="font-size:11px;color:#9ca3af;">${open ? '收起 ▲' : '明细 ▼'}</span>
                </div>
                ${open ? `<div style="padding:0 16px 14px;">
                    <div style="overflow-x:auto;background:#fff;border-radius:8px;">
                    <table style="width:100%;border-collapse:collapse;font-size:12px;">
                        <thead><tr style="background:#f8fafc;">
                            <th style="border:1px solid #e5e7eb;padding:6px 8px;">零件</th>
                            <th style="border:1px solid #e5e7eb;padding:6px 8px;">类别</th>
                            <th style="border:1px solid #e5e7eb;padding:6px 8px;text-align:right;">数量</th>
                            <th style="border:1px solid #e5e7eb;padding:6px 8px;">所需天数</th>
                            <th style="border:1px solid #e5e7eb;padding:6px 8px;">建议开工 ~ 完工</th>
                            <th style="border:1px solid #e5e7eb;padding:6px 8px;">状态</th>
                        </tr></thead>
                        <tbody>${p.items.map(itemRow).join('')}</tbody>
                    </table></div>
                </div>` : ''}
            </div>`;
        }).join('')}
        </div>`;
    } catch (e) {
        el.innerHTML = '<div class="empty">加载失败：' + escapeHtml(e.message || '') + '</div>';
    }
}

function toggleFcProject(no) {
    _fcOpenProject = (_fcOpenProject === no) ? null : no;
    loadFactoryProjectCapacity();
}

// ---------- 设备台账 ----------
async function loadFactoryEquipments() {
    const el = document.getElementById('factory-content');
    if (!el) return;
    el.innerHTML = '<div class="empty">加载中...</div>';
    try {
        const r = await fetch(`${FACTORY_API}/equipments`);
        const data = await r.json();
        if (!data.success) throw new Error(data.detail || '加载失败');
        let html = `
            <div style="margin-bottom:12px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
                <button class="btn btn-primary" onclick="showEquipmentForm()">➕ 新增设备</button>
                <button class="btn btn-secondary" onclick="document.getElementById('eq-import-file').click()">📥 Excel导入</button>
                <button class="btn btn-secondary" onclick="window.open(FACTORY_API+'/equipments/export')">📤 Excel导出</button>
                <button class="btn btn-secondary" onclick="window.open(FACTORY_API+'/equipments/template')">📋 下载模板</button>
                <input type="file" id="eq-import-file" accept=".xlsx,.xls" style="display:none;" onchange="importEquipmentsExcel(event)">
                <span style="font-size:12px;color:#7f8c8d;">共 ${data.total} 台设备</span>
            </div>
            <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:13px;">
                <thead><tr style="background:#f8fafc;">
                    <th style="padding:8px;border:1px solid #e2e8f0;">编码</th>
                    <th style="padding:8px;border:1px solid #e2e8f0;">名称</th>
                    <th style="padding:8px;border:1px solid #e2e8f0;">类别</th>
                    <th style="padding:8px;border:1px solid #e2e8f0;">规格</th>
                    <th style="padding:8px;border:1px solid #e2e8f0;">位置</th>
                    <th style="padding:8px;border:1px solid #e2e8f0;">状态</th>
                    <th style="padding:8px;border:1px solid #e2e8f0;">日产能目标</th>
                    <th style="padding:8px;border:1px solid #e2e8f0;">操作</th>
                </tr></thead><tbody>
        `;
        const statusMap = {running:'运行', idle:'闲置', maintenance:'维修', scrapped:'报废'};
        const statusColor = {running:'#16a34a', idle:'#94a3b8', maintenance:'#d97706', scrapped:'#dc2626'};
        for (const e of data.data) {
            html += `<tr>
                <td style="padding:8px;border:1px solid #e2e8f0;">${e.equipment_code}</td>
                <td style="padding:8px;border:1px solid #e2e8f0;font-weight:600;">${e.equipment_name}</td>
                <td style="padding:8px;border:1px solid #e2e8f0;">${e.category}</td>
                <td style="padding:8px;border:1px solid #e2e8f0;">${e.specification||'-'}</td>
                <td style="padding:8px;border:1px solid #e2e8f0;">${e.location||'-'}</td>
                <td style="padding:8px;border:1px solid #e2e8f0;color:${statusColor[e.status]||'#666'};">${statusMap[e.status]||e.status}</td>
                <td style="padding:8px;border:1px solid #e2e8f0;">${e.daily_capacity_target} ${e.unit}</td>
                <td style="padding:8px;border:1px solid #e2e8f0;white-space:nowrap;">
                    <button class="btn btn-secondary" style="padding:4px 10px;font-size:12px;" onclick="showEquipmentForm(${e.id})">编辑</button>
                    <button class="btn btn-danger" style="padding:4px 10px;font-size:12px;margin-left:4px;" onclick="deleteEquipment(${e.id})">删除</button>
                </td>
            </tr>`;
        }
        if (!data.total) html += '<tr><td colspan="8" style="padding:20px;text-align:center;color:#94a3b8;">暂无设备，点击「新增设备」开始</td></tr>';
        html += '</tbody></table></div>';
        el.innerHTML = html;
    } catch(e) { showToast('加载设备列表失败', 'error'); el.innerHTML = '<div class="empty">加载失败</div>'; }
}

// 设备Excel导入
async function importEquipmentsExcel(event) {
    const file = event.target.files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    try {
        showToast('正在导入...', 'info');
        const r = await fetch(`${FACTORY_API}/equipments/import`, { method: 'POST', body: fd });
        const data = await r.json();
        if (data.success) {
            let msg = data.message;
            if (data.error_rows && data.error_rows.length) {
                msg += '<br>' + data.error_rows.slice(0, 5).join('<br>');
                if (data.error_rows.length > 5) msg += `<br>...还有${data.error_rows.length - 5}条错误`;
            }
            showToast(msg, data.success_count > 0 ? 'success' : 'warning');
            loadFactoryEquipments();
        } else {
            showToast(data.detail || '导入失败', 'error');
        }
    } catch(e) { showToast('导入失败：' + e.message, 'error'); }
    event.target.value = '';
}

function showEquipmentForm(id) {
    const editing = !!id;
    const content = document.getElementById('factory-content');
    // 先获取设备数据（如果编辑）
    const fetchData = editing ? fetch(`${FACTORY_API}/equipments`).then(r=>r.json()).then(d=>d.data.find(x=>x.id===id)) : Promise.resolve(null);
    fetchData.then(eqData => {
        const eq = eqData || {};
        content.innerHTML = `
            <div style="max-width:600px;">
                <h3 style="margin:0 0 16px 0;font-size:16px;">${editing?'编辑设备':'新增设备'}</h3>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                    <div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">设备编码 *</label><input id="eq-code" value="${eq.equipment_code||''}" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;"></div>
                    <div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">设备名称 *</label><input id="eq-name" value="${eq.equipment_name||''}" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;"></div>
                    <div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">类别</label><select id="eq-category" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;"><option ${eq.category==='加工设备'?'selected':''}>加工设备</option><option ${eq.category==='装配设备'?'selected':''}>装配设备</option><option ${eq.category==='检测与调试设备'?'selected':''}>检测与调试设备</option><option ${eq.category==='辅助设备'?'selected':''}>辅助设备</option></select></div>
                    <div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">规格型号</label><input id="eq-spec" value="${eq.specification||''}" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;"></div>
                    <div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">位置</label><input id="eq-loc" value="${eq.location||''}" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;"></div>
                    <div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">状态</label><select id="eq-status" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;"><option value="running" ${eq.status==='running'?'selected':''}>运行</option><option value="idle" ${eq.status==='idle'?'selected':''}>闲置</option><option value="maintenance" ${eq.status==='maintenance'?'selected':''}>维修</option><option value="scrapped" ${eq.status==='scrapped'?'selected':''}>报废</option></select></div>
                    <div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">日产能目标</label><input id="eq-target" type="number" value="${eq.daily_capacity_target||0}" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;"></div>
                    <div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">单位</label><input id="eq-unit" value="${eq.unit||'件'}" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;"></div>
                </div>
                <div style="margin-top:12px;"><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">备注</label><textarea id="eq-remark" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;min-height:60px;">${eq.remark||''}</textarea></div>
                <div style="margin-top:16px;display:flex;gap:8px;">
                    <button class="btn btn-primary" onclick="saveEquipment(${id||0})">${editing?'保存':'新增'}</button>
                    <button class="btn btn-secondary" onclick="loadFactoryEquipments()">取消</button>
                </div>
            </div>
        `;
    });
}

async function saveEquipment(id) {
    const data = {
        equipment_code: document.getElementById('eq-code').value.trim(),
        equipment_name: document.getElementById('eq-name').value.trim(),
        category: document.getElementById('eq-category').value,
        specification: document.getElementById('eq-spec').value,
        location: document.getElementById('eq-loc').value,
        status: document.getElementById('eq-status').value,
        daily_capacity_target: parseFloat(document.getElementById('eq-target').value)||0,
        unit: document.getElementById('eq-unit').value,
        remark: document.getElementById('eq-remark').value,
    };
    if (!data.equipment_code || !data.equipment_name) { showToast('编码和名称不能为空', 'warning'); return; }
    try {
        const url = id ? `${FACTORY_API}/equipments/${id}` : `${FACTORY_API}/equipments`;
        const method = id ? 'PUT' : 'POST';
        const r = await fetch(url, {method, headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
        const result = await r.json();
        if (!r.ok) throw new Error(result.detail || '保存失败');
        showToast(result.message || '保存成功', 'success');
        loadFactoryEquipments();
    } catch(e) { showToast(e.message, 'error'); }
}

async function deleteEquipment(id) {
    try {
        const r = await fetch(`${FACTORY_API}/equipments/${id}`, {method:'DELETE'});
        const result = await r.json();
        if (!r.ok) throw new Error(result.detail || '删除失败');
        showToast('设备已删除', 'success');
        loadFactoryEquipments();
    } catch(e) { showToast(e.message, 'error'); }
}

// ---------- 产能上报 ----------
async function loadCapacityRecords() {
    const el = document.getElementById('factory-content');
    if (!el) return;
    el.innerHTML = '<div class="empty">加载中...</div>';
    try {
        const r = await fetch(`${FACTORY_API}/capacity-daily`);
        const data = await r.json();
        if (!data.success) throw new Error(data.detail || '加载失败');
        // 同时加载设备列表供下拉选择
        const er = await fetch(`${FACTORY_API}/equipments`);
        const edata = await er.json();
        const eqOptions = edata.data.map(e=>`<option value="${e.id}">${e.equipment_code} - ${e.equipment_name}</option>`).join('');
        const today = new Date().toISOString().slice(0,10);
        let html = `
            <div style="margin-bottom:16px;background:#f8fafc;border-radius:8px;padding:14px;">
                <div style="font-size:14px;font-weight:600;color:#1e40af;margin-bottom:10px;">📝 手动录入产能</div>
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;align-items:end;">
                    <div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">设备 *</label><select id="cap-eq" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;">${eqOptions}</select></div>
                    <div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">日期 *</label><input id="cap-date" type="date" value="${today}" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;"></div>
                    <div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">班次</label><select id="cap-shift" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;"><option value="day">白班</option><option value="night">夜班</option><option value="full">全天</option></select></div>
                    <div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">实际产量 *</label><input id="cap-actual" type="number" value="0" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;"></div>
                    <div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">目标产量</label><input id="cap-target" type="number" value="0" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;"></div>
                    <div><label style="display:block;font-size:12px;color:#64748b;margin-bottom:4px;">操作人</label><input id="cap-operator" style="width:100%;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;"></div>
                </div>
                <div style="margin-top:10px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
                    <button class="btn btn-primary" onclick="saveCapacity()">💾 提交</button>
                    <button class="btn btn-secondary" onclick="window.open('${FACTORY_API}/capacity-daily/template')">📋 下载模板</button>
                    <label class="btn btn-secondary" style="cursor:pointer;">📥 Excel导入<input type="file" accept=".xlsx,.xls" onchange="importCapacityExcel(event)" style="display:none;"></label>
                    <button class="btn btn-secondary" onclick="exportCapacityExcel()">📤 Excel导出</button>
                    <input id="cap-export-start" type="date" style="padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:12px;" title="导出开始日期">
                    <span style="font-size:12px;color:#94a3b8;">至</span>
                    <input id="cap-export-end" type="date" style="padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:12px;" title="导出结束日期">
                    <span style="font-size:12px;color:#94a3b8;">Excel需含「设备编码」列；有「日期」列时按Excel日期导入（支持8月15日、2026/8/15等），无日期列则用上方所选日期</span>
                </div>
            </div>
            <div id="cap-import-errors"></div>
            <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:13px;">
                <thead><tr style="background:#f8fafc;">
                    <th style="padding:8px;border:1px solid #e2e8f0;">日期</th>
                    <th style="padding:8px;border:1px solid #e2e8f0;">设备</th>
                    <th style="padding:8px;border:1px solid #e2e8f0;">班次</th>
                    <th style="padding:8px;border:1px solid #e2e8f0;">实际产量</th>
                    <th style="padding:8px;border:1px solid #e2e8f0;">目标产量</th>
                    <th style="padding:8px;border:1px solid #e2e8f0;">达成率</th>
                    <th style="padding:8px;border:1px solid #e2e8f0;">操作人</th>
                    <th style="padding:8px;border:1px solid #e2e8f0;">操作</th>
                </tr></thead><tbody>
        `;
        const shiftMap = {day:'白班', night:'夜班', full:'全天'};
        for (const r of data.data) {
            const rate = r.target_output > 0 ? Math.round(r.actual_output/r.target_output*100) : 0;
            const rateColor = rate >= 100 ? '#16a34a' : rate >= 80 ? '#d97706' : '#dc2626';
            html += `<tr>
                <td style="padding:8px;border:1px solid #e2e8f0;">${r.report_date}</td>
                <td style="padding:8px;border:1px solid #e2e8f0;">${r.equipment_code} ${r.equipment_name}</td>
                <td style="padding:8px;border:1px solid #e2e8f0;">${shiftMap[r.shift]||r.shift}</td>
                <td style="padding:8px;border:1px solid #e2e8f0;font-weight:600;">${r.actual_output}</td>
                <td style="padding:8px;border:1px solid #e2e8f0;">${r.target_output}</td>
                <td style="padding:8px;border:1px solid #e2e8f0;">
                    <div style="display:flex;align-items:center;gap:8px;min-width:110px;">
                        <div style="flex:1;height:8px;background:#e2e8f0;border-radius:4px;overflow:hidden;">
                            <div style="width:${Math.min(rate,100)}%;height:100%;background:${rateColor};border-radius:4px;transition:width .3s;"></div>
                        </div>
                        <span style="font-size:12px;color:${rateColor};font-weight:600;white-space:nowrap;">${rate}%</span>
                    </div>
                </td>
                <td style="padding:8px;border:1px solid #e2e8f0;">${r.operator||'-'}</td>
                <td style="padding:8px;border:1px solid #e2e8f0;"><button class="btn btn-danger" style="padding:4px 10px;font-size:12px;" onclick="deleteCapacity(${r.id})">删除</button></td>
            </tr>`;
        }
        if (!data.total) html += '<tr><td colspan="8" style="padding:20px;text-align:center;color:#94a3b8;">暂无产能记录</td></tr>';
        html += '</tbody></table></div>';
        el.innerHTML = html;
    } catch(e) { showToast('加载产能记录失败', 'error'); el.innerHTML = '<div class="empty">加载失败</div>'; }
}

async function saveCapacity() {
    const equipment_id = parseInt(document.getElementById('cap-eq').value);
    const report_date = document.getElementById('cap-date').value;
    const actual = parseFloat(document.getElementById('cap-actual').value)||0;
    const target = parseFloat(document.getElementById('cap-target').value)||0;
    if (!equipment_id || !report_date) { showToast('设备和日期不能为空', 'warning'); return; }
    try {
        const r = await fetch(`${FACTORY_API}/capacity-daily`, {
            method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify({
                equipment_id, report_date,
                shift: document.getElementById('cap-shift').value,
                actual_output: actual, target_output: target,
                operator: document.getElementById('cap-operator').value,
            })
        });
        const result = await r.json();
        if (!r.ok) throw new Error(result.detail || '提交失败');
        showToast('产能已录入', 'success');
        loadCapacityRecords();
    } catch(e) { showToast(e.message, 'error'); }
}

async function deleteCapacity(id) {
    try {
        const r = await fetch(`${FACTORY_API}/capacity-daily/${id}`, {method:'DELETE'});
        const result = await r.json();
        if (!r.ok) throw new Error(result.detail || '删除失败');
        showToast('已删除', 'success');
        loadCapacityRecords();
    } catch(e) { showToast(e.message, 'error'); }
}

async function importCapacityExcel(event) {
    const file = event.target.files[0];
    if (!file) return;
    const reportDate = document.getElementById('cap-date')?.value || '';
    if (!reportDate) { showToast('请先选择录入日期', 'warning'); event.target.value = ''; return; }
    const fd = new FormData();
    fd.append('file', file);
    fd.append('report_date', reportDate);
    try {
        const r = await fetch(`${FACTORY_API}/capacity-daily/import`, {method:'POST', body:fd});
        const result = await r.json();
        if (!r.ok) throw new Error(result.detail || '导入失败');
        showToast(result.message, result.success_count > 0 ? 'success' : 'warning');
        await loadCapacityRecords();
        const errEl = document.getElementById('cap-import-errors');
        if (errEl) {
            errEl.innerHTML = (result.error_rows && result.error_rows.length)
                ? `<div style="margin:0 0 12px;padding:10px 14px;background:#fef2f2;border:1px solid #fecaca;border-radius:8px;color:#b91c1c;font-size:12px;"><b>❌ 失败明细（${result.error_rows.length}条）：</b><div style="margin-top:4px;line-height:1.8;">${result.error_rows.slice(0, 25).join('<br>')}</div></div>`
                : '';
        }
    } catch(e) { showToast(e.message, 'error'); }
    event.target.value = '';
}

// 产能Excel导出（支持日期范围筛选）
function exportCapacityExcel() {
    const params = new URLSearchParams();
    const sd = document.getElementById('cap-export-start')?.value;
    const ed = document.getElementById('cap-export-end')?.value;
    if (sd) params.append('start_date', sd);
    if (ed) params.append('end_date', ed);
    const qs = params.toString();
    window.open(`${FACTORY_API}/capacity-daily/export${qs ? '?' + qs : ''}`);
}

// ---------- 进度线 ----------
async function loadCapacityProgress() {
    const el = document.getElementById('factory-content');
    if (!el) return;
    el.innerHTML = '<div class="empty">加载中...</div>';
    try {
        const r = await fetch(`${FACTORY_API}/capacity-daily/progress?days=30`);
        const data = await r.json();
        if (!data.success) throw new Error(data.detail || '加载失败');
        const d = data.data;
        el.innerHTML = `
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px;">
                <div class="card" style="margin:0;">
                    <div class="card-title">📊 总产能汇总</div>
                    <div style="display:flex;gap:24px;">
                        <div><div style="font-size:12px;color:#64748b;">累计实际</div><div style="font-size:24px;font-weight:700;color:#1e40af;">${d.total_actual}</div></div>
                        <div><div style="font-size:12px;color:#64748b;">累计目标</div><div style="font-size:24px;font-weight:700;color:#94a3b8;">${d.total_target}</div></div>
                        <div><div style="font-size:12px;color:#64748b;">总达成率</div><div style="font-size:24px;font-weight:700;color:${d.total_target>0&&d.total_actual/d.total_target>=1?'#16a34a':'#d97706'};">${d.total_target>0?Math.round(d.total_actual/d.total_target*100):0}%</div></div>
                    </div>
                </div>
                <div></div>
            </div>
            <div class="card">
                <div class="card-title">📈 每日进度线（实际 vs 目标）</div>
                <canvas id="factory-chart-daily" height="100"></canvas>
            </div>
            <div class="card" style="margin-top:16px;">
                <div class="card-title">📈 总项目进度线（累计实际 vs 累计目标）</div>
                <canvas id="factory-chart-cumulative" height="100"></canvas>
            </div>
        `;
        // 渲染图表
        setTimeout(() => {
            const labels = d.dates.map(x => x.slice(5)); // MM-DD
            // 销毁旧图表
            if (_factoryChart1) _factoryChart1.destroy();
            if (_factoryChart2) _factoryChart2.destroy();
            // 每日进度线
            const ctx1 = document.getElementById('factory-chart-daily');
            if (ctx1) {
                _factoryChart1 = new Chart(ctx1, {
                    type: 'line',
                    data: {
                        labels,
                        datasets: [
                            {label:'实际产量', data:d.daily_actual, borderColor:'#2563eb', backgroundColor:'rgba(37,99,235,0.1)', fill:true, tension:0.3},
                            {label:'目标产量', data:d.daily_target, borderColor:'#94a3b8', backgroundColor:'rgba(148,163,184,0.05)', fill:false, borderDash:[5,5], tension:0.3},
                        ]
                    },
                    options: {responsive:true, plugins:{legend:{position:'top'}}, scales:{y:{beginAtZero:true}}}
                });
            }
            // 累计进度线
            const ctx2 = document.getElementById('factory-chart-cumulative');
            if (ctx2) {
                _factoryChart2 = new Chart(ctx2, {
                    type: 'line',
                    data: {
                        labels,
                        datasets: [
                            {label:'累计实际', data:d.cumulative_actual, borderColor:'#16a34a', backgroundColor:'rgba(22,163,74,0.15)', fill:true, tension:0.3},
                            {label:'累计目标', data:d.cumulative_target, borderColor:'#ea580c', backgroundColor:'rgba(234,88,12,0.05)', fill:false, borderDash:[5,5], tension:0.3},
                        ]
                    },
                    options: {responsive:true, plugins:{legend:{position:'top'}}, scales:{y:{beginAtZero:true}}}
                });
            }
        }, 100);
    } catch(e) { showToast('加载进度线数据失败', 'error'); el.innerHTML = '<div class="empty">加载失败</div>'; }
}
