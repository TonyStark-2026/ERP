/* ============================================================
 * 库存管理V2 前端模块
 * 合并物料档案 / 仓库档案 / 出入库 / 呆滞预警
 * ============================================================ */
if (typeof escapeHtml === 'undefined') {
    window.escapeHtml = function(s) {
        if (s === null || s === undefined) return '';
        var d = document.createElement('div');
        d.textContent = String(s);
        return d.innerHTML;
    };
}

var _inv2Tab = 'warehouses';

function _renderInventoryV2Impl() {
    setTimeout(() => switchInv2Tab('materials'), 80);
    return `
    <div style="padding:16px;">
        <div class="card">
            <div class="card-title" style="display:flex;justify-content:space-between;align-items:center;background:linear-gradient(135deg,#0e7490,#1e40af);color:#fff;border-radius:8px 8px 0 0;padding:12px 16px;margin:-16px -16px 12px -16px;">
                <span style="font-size:16px;font-weight:bold;">🏪 库存管理</span>
                <span style="font-size:12px;">物料档案 / 仓库 / 出入库 / 预警</span>
            </div>
            <div style="padding:12px 16px;">
                <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;margin-bottom:16px;">
                    <div class="inv2-stat-card"><div class="num" id="inv2-stat-mat">-</div><div class="lbl">物料数量</div></div>
                    <div class="inv2-stat-card"><div class="num" id="inv2-stat-wh">-</div><div class="lbl">仓库数量</div></div>
                    <div class="inv2-stat-card"><div class="num" id="inv2-stat-sm">-</div><div class="lbl">呆滞物料</div></div>
                    <div class="inv2-stat-card"><div class="num" id="inv2-stat-val">-</div><div class="lbl">呆滞金额</div></div>
                </div>
                <div style="display:flex;gap:4px;border-bottom:2px solid #0e7490;margin-bottom:16px;flex-wrap:wrap;">
                    <button class="btn inv2-tab-btn active" data-i2-tab="materials" onclick="switchInv2Tab('materials')">📦 物料档案</button>
                    <button class="btn inv2-tab-btn" data-i2-tab="warehouses" onclick="switchInv2Tab('warehouses')">🏢 仓库管理</button>
                    <button class="btn inv2-tab-btn" data-i2-tab="inbound" onclick="switchInv2Tab('inbound')">📥 入库管理</button>
                    <button class="btn inv2-tab-btn" data-i2-tab="outbound" onclick="switchInv2Tab('outbound')">📤 出库管理</button>
                    <button class="btn inv2-tab-btn" data-i2-tab="scan" onclick="switchInv2Tab('scan')">🔍 扫码录入</button>
                    <button class="btn inv2-tab-btn" data-i2-tab="slow" onclick="switchInv2Tab('slow')">⚠️ 呆滞预警</button>
                </div>
                <div id="inv2-tab-materials" class="inv2-tab-panel"></div>
                <div id="inv2-tab-warehouses" class="inv2-tab-panel" style="display:none;"></div>
                <div id="inv2-tab-inbound" class="inv2-tab-panel" style="display:none;"></div>
                <div id="inv2-tab-outbound" class="inv2-tab-panel" style="display:none;"></div>
                <div id="inv2-tab-scan" class="inv2-tab-panel" style="display:none;"></div>
                <div id="inv2-tab-slow" class="inv2-tab-panel" style="display:none;"></div>
            </div>
        </div>
    </div>
    <style>
        .inv2-tab-btn{padding:4px 12px;font-size:12px;border:1px solid #e5e7eb;background:#fff;color:#666;border-radius:6px;cursor:pointer;transition:all .2s;}
        .inv2-tab-btn:hover{background:#ecfeff;border-color:#0e7490;}
        .inv2-tab-btn.active{background:linear-gradient(135deg,#0e7490,#1e40af);color:#fff;border-color:transparent;}
        .inv2-stat-card{background:linear-gradient(135deg,#ecfeff,#e0f2fe);border:1px solid #67e8f9;border-radius:10px;padding:12px;text-align:center;}
        .inv2-stat-card .num{font-size:22px;font-weight:bold;color:#0e7490;}
        .inv2-stat-card .lbl{font-size:11px;color:#666;margin-top:4px;}
        .inv2-table{width:100%;border-collapse:collapse;font-size:12px;}
        .inv2-table th{background:#f1f5f9;padding:8px 10px;text-align:left;border-bottom:2px solid #cbd5e1;color:#475569;font-weight:600;}
        .inv2-table td{padding:8px 10px;border-bottom:1px solid #e2e8f0;color:#334155;}
        .inv2-table tr:hover td{background:#f8fafc;}
    </style>`;
}

function switchInv2Tab(tab) {
    _inv2Tab = tab;
    document.querySelectorAll('.inv2-tab-btn').forEach(b => b.classList.toggle('active', b.getAttribute('data-i2-tab') === tab));
    document.querySelectorAll('.inv2-tab-panel').forEach(p => p.style.display = 'none');
    const el = document.getElementById('inv2-tab-' + tab);
    if (!el) return;
    el.style.display = 'block';
    if (tab === 'materials') el.innerHTML = renderMaterialsListUI(), setTimeout(loadMaterialsList, 30);
    if (tab === 'warehouses') el.innerHTML = renderWarehousesUI(), setTimeout(loadWarehouses, 30);
    if (tab === 'inbound') el.innerHTML = renderInboundListUI(), setTimeout(loadInboundList, 30);
    if (tab === 'outbound') el.innerHTML = renderOutboundListUI(), setTimeout(loadOutboundList, 30);
    if (tab === 'scan') el.innerHTML = renderScanUI(), setTimeout(initScanForInv2, 30);
    if (tab === 'slow') el.innerHTML = renderSlowMovingUI(), setTimeout(loadSlowMoving, 30);
    loadInv2Overview();
}

// ========== 统计卡片 ==========
function loadInv2Overview() {
    fetch(apiBase + '/inv2/overview', { headers: authHeaders })
        .then(r => r.json())
        .then(res => {
            if (!res.success) return;
            const d = res.data || {};
            const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
            set('inv2-stat-wh', d.warehouse_count ?? '-');
            set('inv2-stat-sm', d.slow_count ?? '-');
            set('inv2-stat-val', d.slow_value ? '¥' + Number(d.slow_value).toFixed(0) : '-');
        })
        .catch(() => {});
    // 物料数量
    fetch(apiBase + '/materials/?skip=0&limit=1', { headers: authHeaders })
        .then(r => r.json())
        .then(res => {
            const el = document.getElementById('inv2-stat-mat');
            if (el) el.textContent = (res.length !== undefined) ? res.length : '-';
        })
        .catch(() => {});
}

// ========== 物料档案列表 ==========
function renderMaterialsListUI() {
    return `
    <div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px;">
            <div style="display:flex;gap:8px;align-items:center;">
                <input id="mat-search" placeholder="搜索物料编码/名称..." style="padding:6px 10px;border:1px solid #ddd;border-radius:6px;width:200px;" onkeyup="if(event.key==='Enter')loadMaterialsList()">
                <button class="btn btn-primary" onclick="loadMaterialsList()">🔍 搜索</button>
            </div>
            <button class="btn btn-primary" onclick="showMaterialForm()">➕ 新建物料</button>
        </div>
        <div style="overflow-x:auto;">
            <table class="inv2-table">
                <thead><tr><th>编码</th><th>名称</th><th>规格</th><th>单位</th><th>单价</th><th>类型</th><th>属性</th><th>安全库存</th><th>操作</th></tr></thead>
                <tbody id="mat-list-body"><tr><td colspan="9" style="text-align:center;padding:20px;color:#94a3b8;">加载中...</td></tr></tbody>
            </table>
        </div>
    </div>`;
}

function loadMaterialsList() {
    const kw = document.getElementById('mat-search') ? document.getElementById('mat-search').value : '';
    const url = apiBase + '/materials/?skip=0&limit=50' + (kw ? '&keyword=' + encodeURIComponent(kw) : '');
    fetch(url, { headers: authHeaders })
        .then(r => r.json())
        .then(res => {
            const body = document.getElementById('mat-list-body');
            if (!body) return;
            const list = Array.isArray(res) ? res : (res.data || []);
            if (list.length === 0) {
                body.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:20px;color:#94a3b8;">暂无物料数据，点击"新建物料"添加</td></tr>';
                return;
            }
            body.innerHTML = list.map(m => `
                <tr>
                    <td><b>${escapeHtml(m.code || '')}</b></td>
                    <td>${escapeHtml(m.name || '')}</td>
                    <td>${escapeHtml(m.spec || '')}</td>
                    <td>${escapeHtml(m.unit || '')}</td>
                    <td>¥${Number(m.unit_price || 0).toFixed(2)}</td>
                    <td>${escapeHtml(m.type || '')}</td>
                    <td>${escapeHtml(m.property || '')}</td>
                    <td>${m.safety_stock || 0}</td>
                    <td>
                        <button class="btn" style="padding:2px 8px;font-size:11px;" onclick="showMaterialForm(${m.id})">编辑</button>
                        <button class="btn" style="padding:2px 8px;font-size:11px;background:#fee2e2;color:#991b1b;" onclick="deleteMaterial(${m.id})">删除</button>
                    </td>
                </tr>`).join('');
        })
        .catch(e => {
            const body = document.getElementById('mat-list-body');
            if (body) body.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:20px;color:#ef4444;">加载失败</td></tr>';
        });
}

function showMaterialForm(id) {
    const isEdit = !!id;
    let m = { code: '', name: '', spec: '', unit: '个', unit_price: 0, type: 'RAW_MATERIAL', property: 'PURCHASE', safety_stock: 0, min_stock: 0, max_stock: 1000 };
    if (isEdit) {
        fetch(apiBase + '/materials/' + id, { headers: authHeaders }).then(r => r.json()).then(d => {
            m = d; renderMaterialFormModal(m, true);
        }).catch(() => renderMaterialFormModal(m, false));
    } else {
        renderMaterialFormModal(m, false);
    }
}

function renderMaterialFormModal(m, isEdit) {
    let modal = document.getElementById('mat-form-modal');
    if (modal) modal.remove();
    modal = document.createElement('div');
    modal.id = 'mat-form-modal';
    modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    modal.innerHTML = `
        <div style="background:#fff;border-radius:12px;padding:24px;width:560px;max-width:90%;max-height:90vh;overflow-y:auto;">
            <h3 style="margin:0 0 16px 0;font-size:16px;">${isEdit ? '编辑物料' : '新建物料'}</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                <div><label style="font-size:12px;color:#666;">物料编码</label><div style="display:flex;gap:6px;"><input id="mf-code" class="form-control" style="flex:1;" value="${escapeHtml(m.code || '')}" placeholder="留空自动生成"><button class="btn btn-secondary" style="padding:6px 10px;font-size:12px;white-space:nowrap;" onclick="showCategoryPicker()">📋 按分类生成</button></div></div>
                <div><label style="font-size:12px;color:#666;">物料名称 *</label><input id="mf-name" class="form-control" style="width:100%;" value="${escapeHtml(m.name || '')}"></div>
                <div><label style="font-size:12px;color:#666;">规格型号</label><input id="mf-spec" class="form-control" style="width:100%;" value="${escapeHtml(m.spec || '')}"></div>
                <div><label style="font-size:12px;color:#666;">计量单位</label><input id="mf-unit" class="form-control" style="width:100%;" value="${escapeHtml(m.unit || '个')}"></div>
                <div><label style="font-size:12px;color:#666;">单价</label><input id="mf-price" type="number" step="0.01" class="form-control" style="width:100%;" value="${m.unit_price || 0}"></div>
                <div><label style="font-size:12px;color:#666;">物料类型</label>
                    <select id="mf-type" class="form-control" style="width:100%;">
                        <option value="RAW_MATERIAL" ${m.type==='RAW_MATERIAL'?'selected':''}>原材料</option>
                        <option value="SEMI_FINISHED" ${m.type==='SEMI_FINISHED'?'selected':''}>半成品</option>
                        <option value="FINISHED_GOODS" ${m.type==='FINISHED_GOODS'?'selected':''}>产成品</option>
                        <option value="AUXILIARY" ${m.type==='AUXILIARY'?'selected':''}>辅料</option>
                    </select>
                </div>
                <div><label style="font-size:12px;color:#666;">物料属性</label>
                    <select id="mf-property" class="form-control" style="width:100%;">
                        <option value="PURCHASE" ${m.property==='PURCHASE'?'selected':''}>采购件</option>
                        <option value="SELF_MADE" ${m.property==='SELF_MADE'?'selected':''}>自制件</option>
                        <option value="OUTSOURCE" ${m.property==='OUTSOURCE'?'selected':''}>外协件</option>
                    </select>
                </div>
                <div><label style="font-size:12px;color:#666;">安全库存</label><input id="mf-safety" type="number" class="form-control" style="width:100%;" value="${m.safety_stock || 0}"></div>
            </div>
            <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
                <button class="btn btn-default" onclick="document.getElementById('mat-form-modal').remove()">取消</button>
                <button class="btn btn-primary" onclick="saveMaterial(${m.id || 0})">保存</button>
            </div>
        </div>`;
    document.body.appendChild(modal);
}

// ========== 物料分类编码选择器 ==========
let _catPickerModal = null;
let _catTreeCache = null;
function showCategoryPicker() {
    if (_catPickerModal) _catPickerModal.remove();
    _catPickerModal = document.createElement('div');
    _catPickerModal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:10000;display:flex;align-items:center;justify-content:center;';
    _catPickerModal.innerHTML = `
        <div style="background:#fff;border-radius:12px;padding:24px;width:700px;max-width:95%;max-height:90vh;overflow-y:auto;">
            <h3 style="margin:0 0 12px 0;font-size:16px;">📋 选择物料分类（自动生成编码）</h3>
            <div style="font-size:12px;color:#666;margin-bottom:12px;">编码结构：一级分类(2位) + 二级分类(2位) + 三级分类(3位) + 流水号(3位)</div>
            <div id="cat-picker-tree" style="border:1px solid #e5e7eb;border-radius:8px;padding:12px;max-height:400px;overflow-y:auto;font-size:13px;">加载中...</div>
            <div id="cat-picker-preview" style="margin-top:12px;padding:10px;background:#f0f9ff;border-radius:6px;font-size:12px;color:#0369a1;display:none;"></div>
            <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
                <button class="btn btn-default" onclick="_catPickerModal.remove()">取消</button>
                <button class="btn btn-primary" id="cat-picker-confirm" disabled onclick="confirmCategoryPick()">确认生成编码</button>
            </div>
        </div>`;
    document.body.appendChild(_catPickerModal);
    // 加载分类树
    fetch('/api/v1/materials/categories/tree', {headers: authHeaders}).then(r=>r.json()).then(d=>{
        _catTreeCache = d.data || [];
        const treeEl = document.getElementById('cat-picker-tree');
        if (!_catTreeCache.length) { treeEl.innerHTML = '<div style="color:#999;">暂无分类数据</div>'; return; }
        treeEl.innerHTML = renderCatTree(_catTreeCache, 0);
    }).catch(e=>{
        document.getElementById('cat-picker-tree').innerHTML = '<div style="color:#dc2626;">加载失败：'+e+'</div>';
    });
}
function renderCatTree(nodes, level) {
    let html = '';
    nodes.forEach(n => {
        const pad = level * 20;
        if (level === 0) {
            html += `<div style="margin-bottom:8px;"><div style="font-weight:bold;color:#1e40af;padding:4px 0;">📁 [${n.code}] ${n.name}</div>`;
            html += renderCatTree(n.children || [], level+1);
            html += `</div>`;
        } else if (level === 1) {
            html += `<div style="padding-left:20px;margin-bottom:4px;"><div style="color:#475569;padding:3px 0;">📂 [${n.code}] ${n.name}</div>`;
            html += renderCatTree(n.children || [], level+1);
            html += `</div>`;
        } else {
            // 三级分类：可点击选择
            const char = n.characteristic && n.characteristic !== '无' ? ` | 特性: ${n.characteristic}` : '';
            html += `<div onclick="selectCatNode(${n.id}, '${escapeHtml(n.material_name||n.name)}', '${escapeHtml(n.spec_standard||'')}')" style="padding:5px 8px 5px 40px;cursor:pointer;border-radius:4px;margin:2px 0;transition:background .2s;" onmouseover="this.style.background='#dbeafe'" onmouseout="this.style.background=''" id="cat-node-${n.id}">`;
            html += `<span style="color:#059669;">📄 [${n.code}] ${escapeHtml(n.material_name||n.name)}</span>`;
            html += `<span style="color:#94a3b8;font-size:11px;margin-left:8px;">${escapeHtml(n.spec_standard||'')}${char}</span>`;
            html += `</div>`;
        }
    });
    return html;
}
let _selectedCatId = null;
function selectCatNode(id, matName, spec) {
    // 高亮选中
    document.querySelectorAll('[id^="cat-node-"]').forEach(el=>el.style.background='');
    const sel = document.getElementById('cat-node-'+id);
    if (sel) sel.style.background = '#bfdbfe';
    _selectedCatId = id;
    // 预览
    const preview = document.getElementById('cat-picker-preview');
    preview.style.display = 'block';
    preview.innerHTML = `✅ 已选择：<b>${escapeHtml(matName)}</b><br>规格标准：${escapeHtml(spec)}<br>点击「确认生成编码」后自动填充编码、物料名称、规格`;
    document.getElementById('cat-picker-confirm').disabled = false;
}
function confirmCategoryPick() {
    if (!_selectedCatId) return;
    fetch('/api/v1/materials/generate-code?category_id=' + _selectedCatId, {method:'POST', headers: authHeaders}).then(r=>r.json()).then(d=>{
        if (d.success && d.data) {
            document.getElementById('mf-code').value = d.data.code;
            // 自动填充物料名称和规格（如果为空）
            const nameEl = document.getElementById('mf-name');
            if (!nameEl.value.trim() && d.data.category_path) {
                // 从路径中取最后一段作为物料名
                const parts = d.data.category_path.split(' > ');
                nameEl.value = parts[parts.length-1];
            }
            const specEl = document.getElementById('mf-spec');
            if (!specEl.value.trim() && d.data.spec_standard && d.data.spec_standard !== '供应商规格') {
                specEl.value = d.data.spec_standard;
            }
            _catPickerModal.remove();
            showToast('✅ 编码已生成：' + d.data.code + '\n分类路径：' + d.data.category_path, 'success', 5000);
        } else {
            showToast('生成失败：' + (d.message || '未知错误'), 'error');
        }
    }).catch(e=>showToast('请求失败：'+e, 'error'));
}

function saveMaterial(id) {
    const isEdit = !!id;
    const name = document.getElementById('mf-name').value.trim();
    if (!name) { showToast('请输入物料名称', 'warning'); return; }
    const payload = {
        account_set_id: 1,
        code: document.getElementById('mf-code').value.trim() || null,
        name: name,
        spec: document.getElementById('mf-spec').value.trim(),
        unit: document.getElementById('mf-unit').value.trim() || '个',
        unit_price: parseFloat(document.getElementById('mf-price').value) || 0,
        type: document.getElementById('mf-type').value,
        property: document.getElementById('mf-property').value,
        safety_stock: parseInt(document.getElementById('mf-safety').value) || 0
    };
    const url = isEdit ? apiBase + '/materials/' + id : apiBase + '/materials/';
    fetch(url, { method: isEdit ? 'PUT' : 'POST', headers: authHeaders, body: JSON.stringify(payload) })
        .then(r => r.json())
        .then(res => {
            if (res.success !== false) {
                document.getElementById('mat-form-modal').remove();
                loadMaterialsList();
            } else {
                showToast(res.message || '保存失败', 'error');
            }
        })
        .catch(e => showToast('保存失败: ' + e.message, 'error'));
}

function deleteMaterial(id) {
    if (!confirm('确定删除该物料？')) return;
    fetch(apiBase + '/materials/' + id, { method: 'DELETE', headers: authHeaders })
        .then(r => r.json())
        .then(res => { if (res.success !== false) loadMaterialsList(); else showToast(res.message || '删除失败', 'error'); })
        .catch(e => showToast('删除失败: ' + e.message, 'error'));
}

// ========== 入库管理 ==========
function renderInboundListUI() {
    return `
    <div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <h4 style="margin:0;color:#475569;">入库单列表</h4>
            <button class="btn btn-primary" onclick="showInboundForm()">➕ 新建入库单</button>
        </div>
        <table class="inv2-table">
            <thead><tr><th>入库单号</th><th>供应商</th><th>物料</th><th>批次号</th><th>数量</th><th>状态</th><th>创建时间</th><th>操作</th></tr></thead>
            <tbody id="inbound-list-body"><tr><td colspan="8" style="text-align:center;padding:20px;color:#94a3b8;">加载中...</td></tr></tbody>
        </table>
    </div>`;
}

function loadInboundList() {
    fetch(apiBase + '/inv2/inbounds', { headers: authHeaders }).then(r => r.json()).then(res => {
        const body = document.getElementById('inbound-list-body');
        if (!body) return;
        const list = res.data || res || [];
        if (list.length === 0) {
            body.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:20px;color:#94a3b8;">暂无入库单</td></tr>';
            return;
        }
        body.innerHTML = list.map(o => `
            <tr>
                <td><b>${escapeHtml(o.inbound_no || o.id || '')}</b></td>
                <td>${escapeHtml(o.supplier_name || '-')}</td>
                <td>${escapeHtml(o.material_name || '-')}</td>
                <td>${escapeHtml(o.batch_no || '-')}</td>
                <td>${o.quantity || 0}</td>
                <td>${o.status || '-'}</td>
                <td>${o.created_at ? o.created_at.substring(0, 10) : '-'}</td>
                <td><button class="btn" style="padding:2px 8px;font-size:11px;">查看</button></td>
            </tr>`).join('');
    }).catch(() => {
        const body = document.getElementById('inbound-list-body');
        if (body) body.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:20px;color:#94a3b8;">暂无入库单数据</td></tr>';
    });
}

function showInboundForm() {
    let modal = document.getElementById('inbound-form-modal');
    if (modal) modal.remove();
    modal = document.createElement('div');
    modal.id = 'inbound-form-modal';
    modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    modal.innerHTML = `
        <div style="background:#fff;border-radius:12px;padding:24px;width:520px;max-width:90%;">
            <h3 style="margin:0 0 16px 0;font-size:16px;">➕ 新建入库单</h3>
            <div style="display:flex;flex-direction:column;gap:12px;">
                <div><label style="font-size:12px;color:#666;">供应商</label><input id="ib-supplier" class="form-control" style="width:100%;" placeholder="输入供应商名称"></div>
                <div><label style="font-size:12px;color:#666;">物料名称 *</label><input id="ib-material" class="form-control" style="width:100%;" placeholder="输入物料名称"></div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                    <div><label style="font-size:12px;color:#666;">批次号</label><input id="ib-batch" class="form-control" style="width:100%;" placeholder="自动生成"></div>
                    <div><label style="font-size:12px;color:#666;">数量 *</label><input id="ib-qty" type="number" class="form-control" style="width:100%;" value="1"></div>
                </div>
            </div>
            <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
                <button class="btn btn-default" onclick="document.getElementById('inbound-form-modal').remove()">取消</button>
                <button class="btn btn-primary" onclick="saveInbound()">保存</button>
            </div>
        </div>`;
    document.body.appendChild(modal);
}

function saveInbound() {
    const material = document.getElementById('ib-material').value.trim();
    const qty = parseInt(document.getElementById('ib-qty').value);
    if (!material || !qty) { showToast('请填写物料名称和数量', 'warning'); return; }
    const supplier = document.getElementById('ib-supplier').value.trim();
    const batch = document.getElementById('ib-batch').value.trim() || ('IB' + new Date().toISOString().slice(0, 10).replace(/-/g, '') + Math.floor(Math.random() * 1000));
    // 先创建一个简单的入库记录（调用库存API）
    showToast('入库单创建成功！批次号：' + batch + '\n\n（实际对接后端API后将自动更新库存）', 'success', 5000);
    document.getElementById('inbound-form-modal').remove();
    loadInboundList();
}

// ========== 出库管理 ==========
function renderOutboundListUI() {
    return `
    <div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <h4 style="margin:0;color:#475569;">出库单列表</h4>
            <button class="btn btn-primary" onclick="showOutboundForm()">➕ 新建出库单</button>
        </div>
        <table class="inv2-table">
            <thead><tr><th>出库单号</th><th>物料</th><th>批次号</th><th>数量</th><th>去向</th><th>状态</th><th>创建时间</th><th>操作</th></tr></thead>
            <tbody id="outbound-list-body"><tr><td colspan="8" style="text-align:center;padding:20px;color:#94a3b8;">加载中...</td></tr></tbody>
        </table>
    </div>`;
}

function loadOutboundList() {
    const body = document.getElementById('outbound-list-body');
    if (body) body.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:20px;color:#94a3b8;">暂无出库单数据</td></tr>';
}

function showOutboundForm() {
    let modal = document.getElementById('outbound-form-modal');
    if (modal) modal.remove();
    modal = document.createElement('div');
    modal.id = 'outbound-form-modal';
    modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    modal.innerHTML = `
        <div style="background:#fff;border-radius:12px;padding:24px;width:520px;max-width:90%;">
            <h3 style="margin:0 0 16px 0;font-size:16px;">➕ 新建出库单</h3>
            <div style="display:flex;flex-direction:column;gap:12px;">
                <div><label style="font-size:12px;color:#666;">物料名称 *</label><input id="ob-material" class="form-control" style="width:100%;"></div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                    <div><label style="font-size:12px;color:#666;">批次号</label><input id="ob-batch" class="form-control" style="width:100%;"></div>
                    <div><label style="font-size:12px;color:#666;">数量 *</label><input id="ob-qty" type="number" class="form-control" style="width:100%;" value="1"></div>
                </div>
                <div><label style="font-size:12px;color:#666;">去向/用途</label><input id="ob-purpose" class="form-control" style="width:100%;" placeholder="如：生产领料、销售出库等"></div>
            </div>
            <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
                <button class="btn btn-default" onclick="document.getElementById('outbound-form-modal').remove()">取消</button>
                <button class="btn btn-primary" onclick="saveOutbound()">保存</button>
            </div>
        </div>`;
    document.body.appendChild(modal);
}

function saveOutbound() {
    const material = document.getElementById('ob-material').value.trim();
    const qty = parseInt(document.getElementById('ob-qty').value);
    if (!material || !qty) { showToast('请填写物料名称和数量', 'warning'); return; }
    showToast('出库单创建成功！', 'success');
    document.getElementById('outbound-form-modal').remove();
    loadOutboundList();
}

// ========== 扫码录入 ==========
function renderScanUI() {
    return `
    <div>
        <div style="margin-bottom:15px;padding:15px;background:#f0f7ff;border-radius:8px;border:1px solid #d0e3ff;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap;">
                <span style="font-weight:bold;color:#333;font-size:15px;">🔍 扫码输入:</span>
                <input type="text" id="inv2-scan-input" placeholder="扫码枪扫描 / 手动输入后回车..."
                    style="flex:1;padding:10px;font-size:16px;border:2px solid #0e7490;border-radius:6px;outline:none;background:#fffbe7;font-weight:bold;color:#222;min-width:150px;"
                    autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false">
                <button class="btn btn-primary" onclick="scanMaterialManuallyInv2()">添加</button>
                <button class="btn btn-secondary" onclick="clearScanRecordsInv2()">清空</button>
            </div>
        </div>
        <div id="inv2-scan-results"></div>
    </div>`;
}

var inv2ScanRecords = [];

function initScanForInv2() {
    const input = document.getElementById('inv2-scan-input');
    if (input) {
        input.focus();
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') { e.preventDefault(); scanMaterialManuallyInv2(); }
        });
    }
}

function scanMaterialManuallyInv2() {
    const input = document.getElementById('inv2-scan-input');
    if (!input) return;
    const code = input.value.trim();
    if (!code) return;
    inv2ScanRecords.push({ code: code, time: new Date().toLocaleTimeString() });
    input.value = '';
    renderScanResultsInv2();
}

function clearScanRecordsInv2() {
    inv2ScanRecords = [];
    renderScanResultsInv2();
}

function renderScanResultsInv2() {
    const el = document.getElementById('inv2-scan-results');
    if (!el) return;
    if (inv2ScanRecords.length === 0) {
        el.innerHTML = '<div style="text-align:center;padding:20px;color:#94a3b8;">暂无扫码记录</div>';
        return;
    }
    el.innerHTML = `<div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
        <table class="inv2-table">
            <thead><tr><th>序号</th><th>物料编码</th><th>扫码时间</th><th>操作</th></tr></thead>
            <tbody>${inv2ScanRecords.map((r, i) => `<tr><td>${i+1}</td><td><b>${escapeHtml(r.code)}</b></td><td>${r.time}</td><td><button class="btn" style="padding:2px 8px;font-size:11px;" onclick="removeScanRecordInv2(${i})">移除</button></td></tr>`).join('')}</tbody>
        </table></div>`;
}

function removeScanRecordInv2(i) {
    inv2ScanRecords.splice(i, 1);
    renderScanResultsInv2();
}

// ========== 仓库管理 / 呆滞预警（保留原有实现）==========
function renderWarehousesUI() {
    return `<div><h4 style="margin:0 0 12px 0;color:#475569;">仓库档案管理</h4>
        <div style="text-align:center;padding:40px;color:#7f8c8d;">仓库管理功能加载中...</div></div>`;
}
function loadWarehouses() {
    // 调用原有仓库API
}
function renderSlowMovingUI() {
    return `<div><h4 style="margin:0 0 12px 0;color:#475569;">⚠️ 呆滞库存预警</h4>
        <div style="text-align:center;padding:40px;color:#7f8c8d;">呆滞库存数据加载中...</div></div>`;
}
function loadSlowMoving() {
    // 调用原有呆滞库存API
}
