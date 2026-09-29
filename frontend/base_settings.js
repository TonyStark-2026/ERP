/* ============================================================
 * 基础设置 前端模块
 * 独立文件，通过 <script src> 引入 index.html
 * 包含：会计科目表 / 编码规则 / 会计期间 / 角色权限 / 操作日志
 * ============================================================ */

// 安全兜底：确保escapeHtml存在（apiBase和authHeaders由index.html的const声明提供）
if (typeof escapeHtml === 'undefined') {
    window.escapeHtml = function(s) {
        if (s === null || s === undefined) return '';
        var d = document.createElement('div');
        d.textContent = String(s);
        return d.innerHTML;
    };
}

var _baseTab = 'subjects';

function _renderBaseSettingsImpl() {
    setTimeout(() => switchBaseTab('subjects'), 80);
    return `
    <div style="padding:16px;">
        <div class="card">
            <div class="card-title" style="display:flex;justify-content:space-between;align-items:center;background:linear-gradient(135deg,#0f766e,#1e40af);color:#fff;border-radius:8px 8px 0 0;padding:12px 16px;margin:-16px -16px 12px -16px;">
                <span style="font-size:16px;font-weight:bold;">⚙️ 基础设置</span>
                <span style="font-size:12px;">ERP系统地基：科目表 / 编码规则 / 会计期间 / 权限 / 日志</span>
            </div>
            <div style="padding:12px 16px;">
                <!-- 统计卡片 -->
                <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;margin-bottom:16px;">
                    <div class="base-stat-card"><div class="num" id="base-stat-subj">-</div><div class="lbl">会计科目</div></div>
                    <div class="base-stat-card"><div class="num" id="base-stat-rule">-</div><div class="lbl">编码规则</div></div>
                    <div class="base-stat-card"><div class="num" id="base-stat-period">-</div><div class="lbl">在用期间</div></div>
                    <div class="base-stat-card"><div class="num" id="base-stat-role">-</div><div class="lbl">启用角色</div></div>
                    <div class="base-stat-card"><div class="num" id="base-stat-bal">-</div><div class="lbl">试算平衡</div></div>
                </div>
                <!-- Tab 导航 -->
                <div style="display:flex;gap:4px;border-bottom:2px solid #0f766e;margin-bottom:16px;flex-wrap:wrap;">
                    <button class="btn base-tab-btn active" data-b-tab="subjects" onclick="switchBaseTab('subjects')">📒 会计科目表</button>
                    <button class="btn base-tab-btn" data-b-tab="rules" onclick="switchBaseTab('rules')">🔢 编码规则</button>
                    <button class="btn base-tab-btn" data-b-tab="periods" onclick="switchBaseTab('periods')">📅 会计期间</button>
                    <button class="btn base-tab-btn" data-b-tab="roles" onclick="switchBaseTab('roles')">👥 角色权限</button>
                    <button class="btn base-tab-btn" data-b-tab="logs" onclick="switchBaseTab('logs')">📝 操作日志</button>
                    <button class="btn base-tab-btn" data-b-tab="enterprise" onclick="switchBaseTab('enterprise')">🏢 企业配置</button>
                </div>

                <div id="base-tab-subjects" class="base-tab-panel"></div>
                <div id="base-tab-rules" class="base-tab-panel" style="display:none;"></div>
                <div id="base-tab-periods" class="base-tab-panel" style="display:none;"></div>
                <div id="base-tab-roles" class="base-tab-panel" style="display:none;"></div>
                <div id="base-tab-logs" class="base-tab-panel" style="display:none;"></div>
                <div id="base-tab-enterprise" class="base-tab-panel" style="display:none;"></div>
            </div>
        </div>
    </div>
    <style>
        .base-tab-btn{padding:4px 12px;font-size:12px;border:1px solid #e5e7eb;background:#fff;color:#666;border-radius:6px;cursor:pointer;transition:all .2s;}
        .base-tab-btn:hover{background:#eff6ff;border-color:#0f766e;}
        .base-tab-btn.active{background:linear-gradient(135deg,#0f766e,#1e40af);color:#fff;border-color:transparent;}
        .base-stat-card{background:linear-gradient(135deg,#f0fdfa,#e0f2fe);border:1px solid #99f6e4;border-radius:10px;padding:12px;text-align:center;}
        .base-stat-card .num{font-size:22px;font-weight:bold;color:#0f766e;}
        .base-stat-card .lbl{font-size:11px;color:#666;margin-top:4px;}
        .base-table{width:100%;border-collapse:collapse;font-size:12px;}
        .base-table th{background:#f1f5f9;padding:8px 10px;text-align:left;border-bottom:2px solid #cbd5e1;color:#475569;font-weight:600;}
        .base-table td{padding:8px 10px;border-bottom:1px solid #e2e8f0;color:#334155;}
        .base-table tr:hover td{background:#f8fafc;}
        .base-cat-tag{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;font-weight:600;}
        .base-cat-ASSET{background:#dcfce7;color:#166534;}
        .base-cat-LIABILITY{background:#fee2e2;color:#991b1b;}
        .base-cat-EQUITY{background:#e0e7ff;color:#3730a3;}
        .base-cat-REVENUE{background:#fef9c3;color:#854d0e;}
        .base-cat-EXPENSE{background:#ffedd5;color:#9a3412;}
        .base-cat-COST{background:#f3e8ff;color:#6b21a8;}
        .base-status-open{background:#dcfce7;color:#166534;padding:1px 8px;border-radius:10px;font-size:11px;}
        .base-status-closed{background:#f1f5f9;color:#64748b;padding:1px 8px;border-radius:10px;font-size:11px;}
    </style>`;
}

function switchBaseTab(tab) {
    _baseTab = tab;
    document.querySelectorAll('.base-tab-btn').forEach(b => b.classList.toggle('active', b.getAttribute('data-b-tab') === tab));
    document.querySelectorAll('.base-tab-panel').forEach(p => p.style.display = 'none');
    const map = { subjects:'base-tab-subjects', rules:'base-tab-rules', periods:'base-tab-periods',
                  roles:'base-tab-roles', logs:'base-tab-logs', enterprise:'base-tab-enterprise' };
    const el = document.getElementById(map[tab]);
    if (!el) return;
    el.style.display = 'block';
    if (tab === 'subjects') el.innerHTML = renderSubjectsUI(), setTimeout(loadSubjects, 30);
    if (tab === 'rules') el.innerHTML = renderRulesUI(), setTimeout(loadRules, 30);
    if (tab === 'periods') el.innerHTML = renderPeriodsUI(), setTimeout(loadPeriods, 30);
    if (tab === 'roles') el.innerHTML = renderRolesUI(), setTimeout(loadRoles, 30);
    if (tab === 'logs') el.innerHTML = renderLogsUI(), setTimeout(loadLogs, 30);
    if (tab === 'enterprise') el.innerHTML = renderEnterpriseUI(), setTimeout(loadEnterpriseConfig, 30);
}

// ========== 企业级配置 ==========
function renderEnterpriseConfigUI() {
    return `
    <div style="max-width:720px;">
        <div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;border-radius:10px;padding:16px;margin-bottom:16px;">
            <h3 style="margin:0 0 6px 0;font-size:15px;">🏢 企业级配置</h3>
            <div style="font-size:12px;opacity:0.9;">全局唯一配置，影响模块展示、收入确认方式、领料策略、EOQ计算等核心业务逻辑</div>
        </div>
        <div id="enterprise-config-form">
            <div style="text-align:center;padding:20px;color:#94a3b8;">加载中...</div>
        </div>
    </div>`;
}

function loadEnterpriseConfig() {
    fetch(apiBase + '/config/enterprise', { headers: authHeaders })
        .then(r => r.json())
        .then(res => {
            if (!res.success || !res.data) { document.getElementById('enterprise-config-form').innerHTML = '<div style="color:#ef4444;">加载失败</div>'; return; }
            const c = res.data;
            const pickingModes = c.picking_modes || ['by_order'];
            const industryOptions = [
                {v:'engineering', label:'🏗️ 工程导向型'},
                {v:'agility', label:'⚡ 敏捷导向型'},
                {v:'compliance', label:'🛡️ 合规导向型'},
                {v:'subscription', label:'🔄 订阅导向型'}
            ];
            const modeOptions = [
                {v:'A', label:'A - 大批量单品种'},
                {v:'B', label:'B - 小批量多品种'}
            ];
            const revenueOptions = [
                {v:'percentage_of_completion', label:'完工百分比法'},
                {v:'on_delivery', label:'发货确认法'}
            ];
            const pickingOptions = [
                {v:'by_order', label:'按单领料'},
                {v:'batch_prep', label:'批量备料'},
                {v:'central', label:'中央领料'},
                {v:'backflush', label:'倒冲领料'}
            ];
            const sel = (opts, val) => opts.map(o => `<option value="${o.v}" ${o.v===val?'selected':''}>${o.label}</option>`).join('');
            const chk = (opts, vals) => opts.map(o => `<label style="display:inline-flex;align-items:center;gap:4px;margin-right:12px;font-size:13px;"><input type="checkbox" value="${o.v}" ${vals.includes(o.v)?'checked':''}>${o.label}</label>`).join('');

            document.getElementById('enterprise-config-form').innerHTML = `
            <div style="display:flex;flex-direction:column;gap:12px;">
                <div class="form-group">
                    <label>行业类型</label>
                    <select id="ec-industry" class="form-control" style="width:100%;">${sel(industryOptions, c.industry_type)}</select>
                </div>
                <div class="form-group">
                    <label>业务模式</label>
                    <select id="ec-business-mode" class="form-control" style="width:100%;">${sel(modeOptions, c.business_mode)}</select>
                </div>
                <div class="form-group">
                    <label>收入确认方式</label>
                    <select id="ec-revenue-method" class="form-control" style="width:100%;">${sel(revenueOptions, c.revenue_method)}</select>
                </div>
                <div class="form-group">
                    <label>领料方式（可多选）</label>
                    <div id="ec-picking-modes" style="padding:8px 0;">${chk(pickingOptions, pickingModes)}</div>
                </div>
                <div class="form-group">
                    <label>细分行业（用于自动判断A/B模式）</label>
                    <input id="ec-sub-industry" class="form-control" style="width:100%;" value="${escapeHtml(c.sub_industry||'')}" placeholder="如：专用设备制造、纺织服装等">
                </div>
                <div class="form-group">
                    <label>资金成本率（年化，用于EOQ计算，0~1）</label>
                    <input id="ec-capital-rate" type="number" step="0.01" min="0" max="1" class="form-control" style="width:100%;" value="${c.capital_cost_rate ?? 0.08}">
                </div>
                <div style="display:flex;gap:8px;margin-top:8px;">
                    <button class="btn btn-primary" onclick="saveEnterpriseConfigForm()">💾 保存配置</button>
                    <button class="btn btn-default" onclick="loadEnterpriseConfig()">🔄 重置</button>
                    <span id="ec-save-status" style="font-size:12px;color:#0f766e;align-self:center;"></span>
                </div>
                <div style="font-size:12px;color:#94a3b8;padding:8px;background:#f8fafc;border-radius:6px;">
                    📌 提示：修改行业类型后，侧边栏菜单将自动切换为对应导向型的模块组合
                </div>
            </div>`;
        })
        .catch(e => { document.getElementById('enterprise-config-form').innerHTML = '<div style="color:#ef4444;">加载失败: ' + e.message + '</div>'; });
}

function saveEnterpriseConfigForm() {
    const industry = document.getElementById('ec-industry').value;
    const businessMode = document.getElementById('ec-business-mode').value;
    const revenueMethod = document.getElementById('ec-revenue-method').value;
    const pickingModes = Array.from(document.querySelectorAll('#ec-picking-modes input[type=checkbox]:checked')).map(c => c.value);
    const subIndustry = document.getElementById('ec-sub-industry').value;
    const capitalRate = parseFloat(document.getElementById('ec-capital-rate').value) || 0.08;

    const status = document.getElementById('ec-save-status');
    if (status) { status.textContent = '保存中...'; status.style.color = '#64748b'; }

    const params = new URLSearchParams();
    params.append('industry_type', industry);
    params.append('business_mode', businessMode);
    params.append('revenue_method', revenueMethod);
    pickingModes.forEach(m => params.append('picking_modes', m));
    params.append('sub_industry', subIndustry);
    params.append('capital_cost_rate', capitalRate);

    fetch(apiBase + '/config/enterprise?' + params.toString(), { method: 'PUT', headers: authHeaders })
        .then(r => r.json())
        .then(res => {
            if (res.success) {
                if (status) { status.textContent = '✅ 保存成功！'; status.style.color = '#16a34a'; }
                // 同步 localStorage 并刷新侧边栏
                localStorage.setItem('erp_industry_type', industry);
                localStorage.setItem('erp_business_mode', businessMode);
                localStorage.setItem('erp_revenue_method', revenueMethod);
                localStorage.setItem('erp_picking_modes', JSON.stringify(pickingModes));
                localStorage.setItem('erp_capital_cost_rate', String(capitalRate));
                if (typeof filterSidebarByIndustry === 'function') filterSidebarByIndustry(industry);
                if (typeof updateDashboardIndustryTag === 'function') updateDashboardIndustryTag(industry);
            } else {
                if (status) { status.textContent = '❌ ' + (res.detail || '保存失败'); status.style.color = '#dc2626'; }
            }
        })
        .catch(e => { if (status) { status.textContent = '❌ ' + e.message; status.style.color = '#dc2626'; } });
}

// ========== 统计卡片 ==========
function loadBaseOverview() {
    fetch(apiBase+'/base/overview',{headers:authHeaders})
        .then(r=>r.json()).then(res=>{
            if(!res.success) return;
            const d=res.data||{};
            document.getElementById('base-stat-subj').textContent = d.subject_count||0;
            document.getElementById('base-stat-rule').textContent = d.rule_count||0;
            document.getElementById('base-stat-period').textContent = d.period_open||0;
            document.getElementById('base-stat-role').textContent = d.role_count||0;
            const balEl = document.getElementById('base-stat-bal');
            if (balEl) balEl.textContent = d.balanced ? '平衡' : '不平衡';
            if (balEl && !d.balanced) balEl.style.color = '#dc2626';
        }).catch(e=>console.error('base overview err',e));
}

// ========== 1. 会计科目表 ==========
function renderSubjectsUI() {
    return `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px;">
        <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">
            <input id="base-subj-kw" placeholder="科目编码/名称" class="form-input" style="width:160px;padding:5px 8px;font-size:12px;border:1px solid #cbd5e1;border-radius:6px;" onkeyup="if(event.key==='Enter')loadSubjects()">
            <select id="base-subj-cat" class="form-input" style="padding:5px 8px;font-size:12px;border:1px solid #cbd5e1;border-radius:6px;" onchange="loadSubjects()">
                <option value="">全部类别</option>
                <option value="ASSET">资产</option><option value="LIABILITY">负债</option>
                <option value="EQUITY">所有者权益</option><option value="REVENUE">收入</option>
                <option value="EXPENSE">费用</option><option value="COST">成本</option>
            </select>
            <button class="btn" style="padding:5px 12px;font-size:12px;" onclick="loadSubjects()">🔍查询</button>
        </div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
            <button class="btn btn-primary" style="padding:5px 12px;font-size:12px;" onclick="baseSubjForm()">➕ 新增科目</button>
            <button class="btn" style="padding:5px 12px;font-size:12px;background:#6366f1;color:#fff;border:none;" onclick="initSubjectTemplate()">📋 初始化标准科目</button>
            <button class="btn" style="padding:5px 12px;font-size:12px;" onclick="showTrialBalance()">⚖️ 试算平衡</button>
        </div>
    </div>
    <div id="base-subj-list" style="overflow-x:auto;"><div style="color:#888;padding:20px;text-align:center;">加载中...</div></div>`;
}

function loadSubjects() {
    const kw = (document.getElementById('base-subj-kw')||{}).value||'';
    const cat = (document.getElementById('base-subj-cat')||{}).value||'';
    let url = apiBase+'/base/subjects?';
    if(kw) url += 'keyword='+encodeURIComponent(kw)+'&';
    if(cat) url += 'category='+cat+'&';
    fetch(url,{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){ document.getElementById('base-subj-list').innerHTML='<div style="color:#c0392b;padding:16px;">'+escapeHtml(res.message)+'</div>'; return; }
        const items = (res.data&&res.data.items)||[];
        if(!items.length){ document.getElementById('base-subj-list').innerHTML='<div style="color:#888;padding:20px;text-align:center;">暂无科目，点击「初始化标准科目」快速开始</div>'; return; }
        let html = '<table class="base-table"><thead><tr><th>编码</th><th>科目名称</th><th>类别</th><th>方向</th><th>期初余额</th><th>当前余额</th><th>状态</th><th>操作</th></tr></thead><tbody>';
        items.forEach(s=>{
            html += `<tr>
                <td style="font-weight:600;color:#0f766e;">${escapeHtml(s.code)}</td>
                <td>${escapeHtml(s.name)}</td>
                <td><span class="base-cat-tag base-cat-${s.category}">${escapeHtml(s.category_label)}</span></td>
                <td>${escapeHtml(s.direction_label)}</td>
                <td style="text-align:right;">${s.opening_balance.toFixed(2)}</td>
                <td style="text-align:right;font-weight:600;">${s.current_balance.toFixed(2)}</td>
                <td>${s.is_active?'<span style="color:#16a34a;">启用</span>':'<span style="color:#94a3b8;">停用</span>'}</td>
                <td>
                    <button class="btn" style="padding:2px 8px;font-size:11px;" onclick="baseSubjForm(${s.id})">编辑</button>
                    <button class="btn" style="padding:2px 8px;font-size:11px;color:#dc2626;" onclick="deleteSubject(${s.id})">删除</button>
                </td>
            </tr>`;
        });
        html += '</tbody></table>';
        document.getElementById('base-subj-list').innerHTML = html;
    }).catch(e=>{ document.getElementById('base-subj-list').innerHTML='<div style="color:#c0392b;padding:16px;">加载失败: '+escapeHtml(e.message)+'</div>'; });
}

function baseSubjForm(id) {
    const isEdit = !!id;
    let data = { code:'',name:'',category:'ASSET',balance_direction:'DEBIT',opening_balance:0,is_leaf:true,level:1 };
    const afterLoad = (s)=>{ if(s) Object.assign(data,s); renderModal(); };
    if(isEdit){
        fetch(apiBase+'/base/subjects',{headers:authHeaders}).then(r=>r.json()).then(res=>{
            const s=(res.data&&res.data.items||[]).find(x=>x.id===id); afterLoad(s);
        });
    } else renderModal();

    function renderModal(){
        const cats=[['ASSET','资产'],['LIABILITY','负债'],['EQUITY','所有者权益'],['REVENUE','收入'],['EXPENSE','费用'],['COST','成本']];
        const dirs=[['DEBIT','借方'],['CREDIT','贷方']];
        const m=document.createElement('div');
        m.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
        m.innerHTML=`<div style="background:#fff;border-radius:10px;padding:20px;width:420px;max-width:92vw;max-height:88vh;overflow:auto;box-shadow:0 20px 50px rgba(0,0,0,.3);">
            <h3 style="margin:0 0 16px;color:#0f766e;">${isEdit?'编辑':'新增'}会计科目</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:12px;">
                <div><label>科目编码 *</label><input id="f-code" value="${escapeHtml(data.code)}" ${isEdit?'disabled':''} style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
                <div><label>科目名称 *</label><input id="f-name" value="${escapeHtml(data.name)}" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
                <div><label>类别</label><select id="f-cat" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;">${cats.map(c=>`<option value="${c[0]}" ${data.category===c[0]?'selected':''}>${c[1]}</option>`).join('')}</select></div>
                <div><label>余额方向</label><select id="f-dir" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;">${dirs.map(d=>`<option value="${d[0]}" ${data.balance_direction===d[0]?'selected':''}>${d[1]}</option>`).join('')}</select></div>
                <div><label>期初余额</label><input id="f-ob" type="number" step="0.01" value="${data.opening_balance}" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
                <div><label>层级</label><input id="f-lvl" type="number" value="${data.level}" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            </div>
            <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
                <button class="btn" style="padding:6px 14px;font-size:12px;" onclick="this.closest('.fixed').remove()">取消</button>
                <button class="btn btn-primary" style="padding:6px 14px;font-size:12px;" onclick="saveSubject(${id||0},this)">保存</button>
            </div>
        </div>`;
        m.className='fixed';
        document.body.appendChild(m);
    }
}

function saveSubject(id, btn) {
    const payload = {
        code: document.getElementById('f-code').value.trim(),
        name: document.getElementById('f-name').value.trim(),
        category: document.getElementById('f-cat').value,
        balance_direction: document.getElementById('f-dir').value,
        opening_balance: parseFloat(document.getElementById('f-ob').value)||0,
        level: parseInt(document.getElementById('f-lvl').value)||1,
        is_leaf: true,
    };
    const url = id ? apiBase+'/base/subjects/'+id : apiBase+'/base/subjects';
    const method = id ? 'PUT' : 'POST';
    fetch(url,{method,headers:{...authHeaders,'Content-Type':'application/json'},body:JSON.stringify(payload)})
        .then(r=>r.json()).then(res=>{
            if(!res.success){ showToast(res.message||'保存失败', 'error'); return; }
            btn.closest('.fixed').remove();
            loadSubjects();
            loadBaseOverview();
        }).catch(e=>showToast('保存失败: '+e.message, 'error'));
}

function deleteSubject(id) {
    if(!confirm('确认删除该科目？')) return;
    fetch(apiBase+'/base/subjects/'+id,{method:'DELETE',headers:authHeaders})
        .then(r=>r.json()).then(res=>{
            if(!res.success){ showToast(res.message||'删除失败', 'error'); return; }
            loadSubjects(); loadBaseOverview();
        });
}

function initSubjectTemplate() {
    if(!confirm('将初始化24条企业会计准则标准科目，确认继续？')) return;
    fetch(apiBase+'/base/subjects/init-template',{method:'POST',headers:authHeaders})
        .then(r=>r.json()).then(res=>{
            showToast(res.message||'初始化完成', 'success');
            if(res.success){ loadSubjects(); loadBaseOverview(); }
        });
}

function showTrialBalance() {
    fetch(apiBase+'/base/subjects/trial-balance',{headers:authHeaders})
        .then(r=>r.json()).then(res=>{
            if(!res.success){ showToast(res.message, 'error'); return; }
            const d=res.data;
            const m=document.createElement('div');
            m.className='fixed';
            m.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
            let rowsHtml='';
            (d.rows||[]).forEach(r=>{
                rowsHtml+=`<tr><td style="font-weight:600;color:#0f766e;">${escapeHtml(r.code)}</td><td>${escapeHtml(r.name)}</td><td>${escapeHtml(r.direction)}</td><td style="text-align:right;">${r.balance.toFixed(2)}</td></tr>`;
            });
            m.innerHTML=`<div style="background:#fff;border-radius:10px;padding:20px;width:520px;max-width:92vw;max-height:85vh;overflow:auto;">
                <h3 style="margin:0 0 12px;color:#0f766e;">⚖️ 试算平衡表</h3>
                <div style="display:flex;gap:12px;margin-bottom:12px;font-size:13px;">
                    <span>借方合计：<b style="color:#0f766e;">${d.total_debit.toFixed(2)}</b></span>
                    <span>贷方合计：<b style="color:#1e40af;">${d.total_credit.toFixed(2)}</b></span>
                    <span>差额：<b style="color:${d.balanced?'#16a34a':'#dc2626'};">${d.difference.toFixed(2)}</b></span>
                    <span style="padding:2px 10px;border-radius:10px;background:${d.balanced?'#dcfce7':'#fee2e2'};color:${d.balanced?'#166534':'#991b1b'};font-weight:600;">${d.balanced_label}</span>
                </div>
                <table class="base-table"><thead><tr><th>编码</th><th>科目</th><th>方向</th><th>余额</th></tr></thead><tbody>${rowsHtml}</tbody></table>
                <div style="text-align:right;margin-top:12px;"><button class="btn" style="padding:6px 14px;font-size:12px;" onclick="this.closest('.fixed').remove()">关闭</button></div>
            </div>`;
            document.body.appendChild(m);
        });
}

// ========== 2. 编码规则 ==========
function renderRulesUI() {
    return `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <span style="font-size:13px;color:#475569;font-weight:600;">编号自动生成规则配置</span>
        <button class="btn btn-primary" style="padding:5px 12px;font-size:12px;" onclick="baseRuleForm()">➕ 新增规则</button>
    </div>
    <div id="base-rule-list" style="overflow-x:auto;"><div style="color:#888;padding:20px;text-align:center;">加载中...</div></div>`;
}

function loadRules() {
    fetch(apiBase+'/base/coding-rules',{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){ document.getElementById('base-rule-list').innerHTML='<div style="color:#c0392b;padding:16px;">'+escapeHtml(res.message)+'</div>'; return; }
        const items=(res.data&&res.data.items)||[];
        if(!items.length){ document.getElementById('base-rule-list').innerHTML='<div style="color:#888;padding:20px;text-align:center;">暂无编码规则</div>'; return; }
        let html='<table class="base-table"><thead><tr><th>实体类型</th><th>前缀</th><th>日期格式</th><th>流水号位数</th><th>重置周期</th><th>分隔符</th><th>状态</th><th>操作</th></tr></thead><tbody>';
        items.forEach(r=>{
            html+=`<tr><td><span style="font-weight:600;color:#0f766e;">${escapeHtml(r.entity_label)}</span></td><td>${escapeHtml(r.prefix||'-')}</td><td>${escapeHtml(r.date_format||'-')}</td><td>${r.seq_length}位</td><td>${escapeHtml(r.reset_cycle)}</td><td>${escapeHtml(r.separator||'无')}</td><td>${r.is_active?'<span style="color:#16a34a;">启用</span>':'<span style="color:#94a3b8;">停用</span>'}</td><td><button class="btn" style="padding:2px 8px;font-size:11px;" onclick="baseRuleForm(${r.id})">编辑</button> <button class="btn" style="padding:2px 8px;font-size:11px;color:#dc2626;" onclick="deleteRule(${r.id})">删除</button></td></tr>`;
        });
        html+='</tbody></table>';
        document.getElementById('base-rule-list').innerHTML=html;
    });
}

function baseRuleForm(id) {
    const entities=[['MATERIAL','物料'],['SUPPLIER','供应商'],['CUSTOMER','客户'],['PO','采购订单'],['SO','销售订单'],['WO','生产工单'],['VOUCHER','凭证']];
    const cycles=[['YEARLY','按年'],['MONTHLY','按月'],['DAILY','按日'],['NEVER','不重置']];
    const dfs=[['','无格式'],['YYYYMMDD','年月日'],['YYYYMM','年月']];
    let data={entity_type:'',prefix:'',date_format:'',seq_length:4,reset_cycle:'YEARLY',separator:'-',is_active:true};
    const renderModal=()=>{
        const m=document.createElement('div'); m.className='fixed';
        m.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
        m.innerHTML=`<div style="background:#fff;border-radius:10px;padding:20px;width:400px;max-width:92vw;">
            <h3 style="margin:0 0 16px;color:#0f766e;">${id?'编辑':'新增'}编码规则</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:12px;">
                <div style="grid-column:1/3;"><label>实体类型 *</label><select id="r-et" ${id?'disabled':''} style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;">${entities.map(e=>`<option value="${e[0]}" ${data.entity_type===e[0]?'selected':''}>${e[1]}</option>`).join('')}</select></div>
                <div><label>前缀</label><input id="r-prefix" value="${escapeHtml(data.prefix)}" placeholder="如 PO/SO" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
                <div><label>日期格式</label><select id="r-df" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;">${dfs.map(d=>`<option value="${d[0]}" ${data.date_format===d[0]?'selected':''}>${d[1]}</option>`).join('')}</select></div>
                <div><label>流水号位数</label><input id="r-seq" type="number" min="2" max="8" value="${data.seq_length}" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
                <div><label>重置周期</label><select id="r-cyc" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;">${cycles.map(c=>`<option value="${c[0]}" ${data.reset_cycle===c[0]?'selected':''}>${c[1]}</option>`).join('')}</select></div>
                <div><label>分隔符</label><input id="r-sep" value="${escapeHtml(data.separator)}" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            </div>
            <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
                <button class="btn" style="padding:6px 14px;font-size:12px;" onclick="this.closest('.fixed').remove()">取消</button>
                <button class="btn btn-primary" style="padding:6px 14px;font-size:12px;" onclick="saveRule(${id||0},this)">保存</button>
            </div></div>`;
        document.body.appendChild(m);
    };
    if(id){ fetch(apiBase+'/base/coding-rules',{headers:authHeaders}).then(r=>r.json()).then(res=>{ const r=(res.data&&res.data.items||[]).find(x=>x.id===id); if(r)Object.assign(data,r); renderModal(); }); }
    else renderModal();
}

function saveRule(id,btn){
    const payload={entity_type:document.getElementById('r-et').value,prefix:document.getElementById('r-prefix').value,date_format:document.getElementById('r-df').value,seq_length:parseInt(document.getElementById('r-seq').value)||4,reset_cycle:document.getElementById('r-cyc').value,separator:document.getElementById('r-sep').value,is_active:true};
    const url=id?apiBase+'/base/coding-rules/'+id:apiBase+'/base/coding-rules';
    const method=id?'PUT':'POST';
    fetch(url,{method,headers:{...authHeaders,'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json()).then(res=>{ if(!res.success){showToast(res.message, 'error');return;} btn.closest('.fixed').remove(); loadRules(); loadBaseOverview(); });
}

function deleteRule(id){ if(!confirm('确认删除？'))return; fetch(apiBase+'/base/coding-rules/'+id,{method:'DELETE',headers:authHeaders}).then(r=>r.json()).then(res=>{ if(!res.success){showToast(res.message, 'error');return;} loadRules(); loadBaseOverview(); }); }

// ========== 3. 会计期间 ==========
function renderPeriodsUI() {
    return `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <span style="font-size:13px;color:#475569;font-weight:600;">会计期间管理（结账/反结账）</span>
        <button class="btn btn-primary" style="padding:5px 12px;font-size:12px;" onclick="initYearPeriods()">📅 初始化年度期间</button>
    </div>
    <div id="base-period-list" style="overflow-x:auto;"><div style="color:#888;padding:20px;text-align:center;">加载中...</div></div>`;
}

function loadPeriods() {
    fetch(apiBase+'/base/periods',{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){ document.getElementById('base-period-list').innerHTML='<div style="color:#c0392b;padding:16px;">'+escapeHtml(res.message)+'</div>'; return; }
        const items=(res.data&&res.data.items)||[];
        if(!items.length){ document.getElementById('base-period-list').innerHTML='<div style="color:#888;padding:20px;text-align:center;">暂无会计期间，点击「初始化年度期间」</div>'; return; }
        let html='<table class="base-table"><thead><tr><th>期间</th><th>年度</th><th>月份</th><th>起始</th><th>结束</th><th>状态</th><th>结账时间</th><th>操作</th></tr></thead><tbody>';
        items.forEach(p=>{
            const statusTag=p.status==='OPEN'?'<span class="base-status-open">已开</span>':'<span class="base-status-closed">已关</span>';
            const btn=p.status==='OPEN'?`<button class="btn" style="padding:2px 8px;font-size:11px;color:#dc2626;" onclick="closePeriod(${p.id})">结账</button>`:`<button class="btn" style="padding:2px 8px;font-size:11px;color:#2563eb;" onclick="reopenPeriod(${p.id})">反结账</button>`;
            html+=`<tr><td style="font-weight:600;color:#0f766e;">${escapeHtml(p.period_code)}</td><td>${p.year}</td><td>${p.month}</td><td>${escapeHtml(p.start_date)}</td><td>${escapeHtml(p.end_date)}</td><td>${statusTag}</td><td>${escapeHtml(p.closed_at)}</td><td>${btn}</td></tr>`;
        });
        html+='</tbody></table>';
        document.getElementById('base-period-list').innerHTML=html;
    });
}

function initYearPeriods() {
    const year=new Date().getFullYear();
    if(!confirm('将初始化'+year+'年12个会计期间，确认继续？'))return;
    fetch(apiBase+'/base/periods/init-year',{method:'POST',headers:{...authHeaders,'Content-Type':'application/json'},body:JSON.stringify({year})}).then(r=>r.json()).then(res=>{ showToast(res.message, 'success'); if(res.success){loadPeriods();loadBaseOverview();} });
}

function closePeriod(id){ if(!confirm('确认结账？结账后该期间将不能录入凭证。'))return; fetch(apiBase+'/base/periods/'+id+'/close',{method:'POST',headers:{...authHeaders,'Content-Type':'application/json'},body:JSON.stringify({})}).then(r=>r.json()).then(res=>{ showToast(res.message, 'success'); if(res.success){loadPeriods();loadBaseOverview();} }); }
function reopenPeriod(id){ if(!confirm('确认反结账？'))return; fetch(apiBase+'/base/periods/'+id+'/reopen',{method:'POST',headers:authHeaders}).then(r=>r.json()).then(res=>{ showToast(res.message, 'success'); if(res.success){loadPeriods();} }); }

// ========== 4. 角色权限 ==========
function renderRolesUI() {
    return `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <span style="font-size:13px;color:#475569;font-weight:600;">角色与权限管理</span>
        <button class="btn btn-primary" style="padding:5px 12px;font-size:12px;" onclick="baseRoleForm()">➕ 新增角色</button>
    </div>
    <div id="base-role-list" style="overflow-x:auto;"><div style="color:#888;padding:20px;text-align:center;">加载中...</div></div>`;
}

function loadRoles() {
    fetch(apiBase+'/base/roles',{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){ document.getElementById('base-role-list').innerHTML='<div style="color:#c0392b;padding:16px;">'+escapeHtml(res.message)+'</div>'; return; }
        const items=(res.data&&res.data.items)||[];
        if(!items.length){ document.getElementById('base-role-list').innerHTML='<div style="color:#888;padding:20px;text-align:center;">暂无角色</div>'; return; }
        let html='<table class="base-table"><thead><tr><th>角色名称</th><th>描述</th><th>权限配置</th><th>状态</th><th>创建时间</th><th>操作</th></tr></thead><tbody>';
        items.forEach(r=>{
            let permText=r.permissions||'';
            try{ const p=JSON.parse(permText); permText=Array.isArray(p)?p.join(', '):JSON.stringify(p); }catch(e){}
            html+=`<tr><td style="font-weight:600;color:#0f766e;">${escapeHtml(r.name)}</td><td>${escapeHtml(r.description||'-')}</td><td style="max-width:220px;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(permText||'-')}</td><td>${r.is_active?'<span style="color:#16a34a;">启用</span>':'<span style="color:#94a3b8;">停用</span>'}</td><td>${escapeHtml(r.created_at)}</td><td><button class="btn" style="padding:2px 8px;font-size:11px;" onclick="baseRoleForm(${r.id})">编辑</button> <button class="btn" style="padding:2px 8px;font-size:11px;color:#dc2626;" onclick="deleteRole(${r.id})">删除</button></td></tr>`;
        });
        html+='</tbody></table>';
        document.getElementById('base-role-list').innerHTML=html;
    });
}

function baseRoleForm(id) {
    let data={name:'',description:'',permissions:'',is_active:true};
    const renderModal=()=>{
        const m=document.createElement('div'); m.className='fixed';
        m.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
        m.innerHTML=`<div style="background:#fff;border-radius:10px;padding:20px;width:420px;max-width:92vw;">
            <h3 style="margin:0 0 16px;color:#0f766e;">${id?'编辑':'新增'}角色</h3>
            <div style="display:grid;gap:10px;font-size:12px;">
                <div><label>角色名称 *</label><input id="ro-name" value="${escapeHtml(data.name)}" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
                <div><label>描述</label><input id="ro-desc" value="${escapeHtml(data.description)}" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
                <div><label>权限（JSON或逗号分隔模块名）</label><textarea id="ro-perm" rows="4" placeholder='如：materials,sales,finance 或 {"materials":["read"]}' style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;font-size:11px;">${escapeHtml(data.permissions)}</textarea></div>
            </div>
            <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
                <button class="btn" style="padding:6px 14px;font-size:12px;" onclick="this.closest('.fixed').remove()">取消</button>
                <button class="btn btn-primary" style="padding:6px 14px;font-size:12px;" onclick="saveRole(${id||0},this)">保存</button>
            </div></div>`;
        document.body.appendChild(m);
    };
    if(id){ fetch(apiBase+'/base/roles',{headers:authHeaders}).then(r=>r.json()).then(res=>{ const r=(res.data&&res.data.items||[]).find(x=>x.id===id); if(r)Object.assign(data,r); renderModal(); }); }
    else renderModal();
}

function saveRole(id,btn){
    const perm=document.getElementById('ro-perm').value.trim();
    let permVal=perm;
    // 支持逗号分隔自动转JSON数组
    if(perm && !perm.startsWith('[') && !perm.startsWith('{') && perm.includes(',')){
        permVal=JSON.stringify(perm.split(',').map(s=>s.trim()).filter(Boolean));
    } else if(perm && !perm.startsWith('[') && !perm.startsWith('{')){
        permVal=JSON.stringify([perm]);
    }
    const payload={name:document.getElementById('ro-name').value.trim(),description:document.getElementById('ro-desc').value,permissions:permVal,is_active:true};
    const url=id?apiBase+'/base/roles/'+id:apiBase+'/base/roles';
    const method=id?'PUT':'POST';
    fetch(url,{method,headers:{...authHeaders,'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json()).then(res=>{ if(!res.success){showToast(res.message, 'error');return;} btn.closest('.fixed').remove(); loadRoles(); loadBaseOverview(); });
}

function deleteRole(id){ if(!confirm('确认删除该角色？'))return; fetch(apiBase+'/base/roles/'+id,{method:'DELETE',headers:authHeaders}).then(r=>r.json()).then(res=>{ if(!res.success){showToast(res.message, 'error');return;} loadRoles(); loadBaseOverview(); }); }

// ========== 5. 操作日志 ==========
function renderLogsUI() {
    return `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px;">
        <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">
            <input id="base-log-mod" placeholder="模块" class="form-input" style="width:120px;padding:5px 8px;font-size:12px;border:1px solid #cbd5e1;border-radius:6px;">
            <input id="base-log-user" placeholder="用户名" class="form-input" style="width:120px;padding:5px 8px;font-size:12px;border:1px solid #cbd5e1;border-radius:6px;">
            <button class="btn" style="padding:5px 12px;font-size:12px;" onclick="loadLogs()">🔍查询</button>
        </div>
        <span style="font-size:11px;color:#94a3b8;">最近100条操作记录</span>
    </div>
    <div id="base-log-list" style="overflow-x:auto;"><div style="color:#888;padding:20px;text-align:center;">加载中...</div></div>`;
}

function loadLogs() {
    const mod=(document.getElementById('base-log-mod')||{}).value||'';
    const user=(document.getElementById('base-log-user')||{}).value||'';
    let url=apiBase+'/base/logs?limit=100';
    if(mod) url+='&module='+encodeURIComponent(mod);
    if(user) url+='&username='+encodeURIComponent(user);
    fetch(url,{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){ document.getElementById('base-log-list').innerHTML='<div style="color:#c0392b;padding:16px;">'+escapeHtml(res.message)+'</div>'; return; }
        const items=(res.data&&res.data.items)||[];
        if(!items.length){ document.getElementById('base-log-list').innerHTML='<div style="color:#888;padding:20px;text-align:center;">暂无操作日志</div>'; return; }
        let html='<table class="base-table"><thead><tr><th>时间</th><th>用户</th><th>模块</th><th>操作</th><th>对象类型</th><th>对象ID</th><th>详情</th><th>IP</th></tr></thead><tbody>';
        items.forEach(l=>{
            html+=`<tr><td>${escapeHtml(l.created_at)}</td><td>${escapeHtml(l.username||'-')}</td><td><span style="font-weight:600;color:#0f766e;">${escapeHtml(l.module)}</span></td><td>${escapeHtml(l.action)}</td><td>${escapeHtml(l.target_type||'-')}</td><td>${escapeHtml(l.target_id||'-')}</td><td style="max-width:260px;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(l.detail||'-')}</td><td>${escapeHtml(l.ip_address||'-')}</td></tr>`;
        });
        html+='</tbody></table>';
        document.getElementById('base-log-list').innerHTML=html;
    });
}

// 注册渲染入口
window._renderBaseSettingsImpl = _renderBaseSettingsImpl;
// 渲染后加载统计
const _origBaseRender = _renderBaseSettingsImpl;
window._renderBaseSettingsImpl = function() {
    const html = _origBaseRender();
    setTimeout(loadBaseOverview, 100);
    return html;
};

// ========== API对接中心 ==========
function renderApiCenterUI() {
    return `
    <div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:8px;">
            <div>
                <h3 style="margin:0;font-size:15px;">🔌 API对接中心</h3>
                <p style="margin:4px 0 0 0;font-size:12px;color:#64748b;">管理第三方平台API连接（淘宝/1688/京东/Shopify/飞书等）</p>
            </div>
            <div style="display:flex;gap:8px;">
                <button class="btn btn-default" onclick="loadApiPresets()">📋 查看预设</button>
                <button class="btn btn-primary" onclick="showApiIntegrationForm()">➕ 新建对接</button>
            </div>
        </div>
        <div id="api-presets-area" style="display:none;margin-bottom:16px;"></div>
        <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:12px;">
                <thead><tr style="background:#f1f5f9;">
                    <th style="border:1px solid #e2e8f0;padding:8px;">名称</th><th style="border:1px solid #e2e8f0;padding:8px;">类型</th>
                    <th style="border:1px solid #e2e8f0;padding:8px;">API地址</th><th style="border:1px solid #e2e8f0;padding:8px;">认证方式</th>
                    <th style="border:1px solid #e2e8f0;padding:8px;">状态</th><th style="border:1px solid #e2e8f0;padding:8px;">测试结果</th>
                    <th style="border:1px solid #e2e8f0;padding:8px;">操作</th>
                </tr></thead>
                <tbody id="api-list-body"><tr><td colspan="7" style="text-align:center;padding:20px;color:#94a3b8;">加载中...</td></tr></tbody>
            </table>
        </div>
    </div>`;
}

function loadApiIntegrations() {
    fetch(apiBase + '/api-center/integrations', { headers: authHeaders })
        .then(r => r.json())
        .then(res => {
            const body = document.getElementById('api-list-body');
            if (!body) return;
            const list = res.data || [];
            if (list.length === 0) {
                body.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:30px;color:#94a3b8;">暂无API对接配置，点击"新建对接"添加</td></tr>';
                return;
            }
            const typeColors = { taobao:'#ff6b35', '1688':'#ff4400', jd:'#e1251b', shopify:'#96bf48', wechat:'#07c160', feishu:'#00d6b9', dingtalk:'#1677ff', custom:'#64748b' };
            body.innerHTML = list.map(i => `
                <tr>
                    <td style="border:1px solid #e2e8f0;padding:8px;"><b>${escapeHtml(i.name)}</b></td>
                    <td style="border:1px solid #e2e8f0;padding:8px;"><span style="background:${typeColors[i.api_type]||'#64748b'};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;">${escapeHtml(i.api_type)}</span></td>
                    <td style="border:1px solid #e2e8f0;padding:8px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${escapeHtml(i.base_url)}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px;">${escapeHtml(i.auth_type)}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px;"><span style="color:${i.status==='active'?'#16a34a':'#dc2626'};">${i.status==='active'?'🟢 启用':'🔴 停用'}</span></td>
                    <td style="border:1px solid #e2e8f0;padding:8px;font-size:11px;color:#64748b;">${escapeHtml(i.last_test_result||'未测试')}</td>
                    <td style="border:1px solid #e2e8f0;padding:8px;">
                        <button class="btn" style="padding:2px 8px;font-size:11px;" onclick="testApiIntegration(${i.id})">🔍 测试</button>
                        <button class="btn" style="padding:2px 8px;font-size:11px;" onclick="showApiIntegrationForm(${i.id})">✏️ 编辑</button>
                        <button class="btn" style="padding:2px 8px;font-size:11px;background:#fee2e2;color:#991b1b;" onclick="deleteApiIntegration(${i.id})">🗑️ 删除</button>
                    </td>
                </tr>`).join('');
        })
        .catch(() => {
            const body = document.getElementById('api-list-body');
            if (body) body.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:20px;color:#ef4444;">加载失败</td></tr>';
        });
}

function loadApiPresets() {
    fetch(apiBase + '/api-center/integrations/presets', { headers: authHeaders })
        .then(r => r.json())
        .then(res => {
            const area = document.getElementById('api-presets-area');
            if (!area) return;
            const presets = res.data || [];
            area.style.display = 'block';
            area.innerHTML = `<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px;">
                <h4 style="margin:0 0 8px 0;font-size:13px;color:#475569;">📋 快速对接预设（点击使用）</h4>
                <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;">
                    ${presets.map(p => `<div onclick='useApiPreset(${JSON.stringify(p)})' style="background:#fff;border:1px solid #e2e8f0;border-radius:6px;padding:10px;cursor:pointer;transition:all .2s;" onmouseover="this.style.borderColor='#3b82f6';this.style.boxShadow='0 2px 8px rgba(59,130,246,.15)'" onmouseout="this.style.borderColor='#e2e8f0';this.style.boxShadow='none'">
                        <div style="font-weight:600;font-size:13px;color:#1e40af;">${escapeHtml(p.name)}</div>
                        <div style="font-size:11px;color:#64748b;margin-top:4px;">${escapeHtml(p.desc)}</div>
                    </div>`).join('')}
                </div></div>`;
        });
}

function useApiPreset(preset) {
    showApiIntegrationForm();
    setTimeout(() => {
        const typeEl = document.getElementById('api-type');
        const nameEl = document.getElementById('api-name');
        const urlEl = document.getElementById('api-url');
        if (typeEl) typeEl.value = preset.type;
        if (nameEl) nameEl.value = preset.name;
        if (urlEl) urlEl.value = preset.url;
    }, 100);
}

function showApiIntegrationForm(id) {
    const isEdit = !!id;
    let modal = document.getElementById('api-form-modal');
    if (modal) modal.remove();
    modal = document.createElement('div');
    modal.id = 'api-form-modal';
    modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    modal.innerHTML = `
        <div style="background:#fff;border-radius:12px;padding:24px;width:600px;max-width:90%;max-height:90vh;overflow-y:auto;">
            <h3 style="margin:0 0 16px 0;font-size:16px;">${isEdit?'编辑API对接':'➕ 新建API对接'}</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                <div><label style="font-size:12px;color:#666;">对接名称 *</label><input id="api-name" class="form-control" style="width:100%;" placeholder="如：淘宝店铺订单同步"></div>
                <div><label style="font-size:12px;color:#666;">对接类型</label>
                    <select id="api-type" class="form-control" style="width:100%;">
                        <option value="custom">自定义</option>
                        <option value="taobao">淘宝开放平台</option>
                        <option value="1688">1688开放平台</option>
                        <option value="jd">京东开放平台</option>
                        <option value="shopify">Shopify</option>
                        <option value="wechat">微信小程序</option>
                        <option value="feishu">飞书开放平台</option>
                        <option value="dingtalk">钉钉开放平台</option>
                    </select>
                </div>
                <div style="grid-column:1/-1;"><label style="font-size:12px;color:#666;">API基础地址 *</label><input id="api-url" class="form-control" style="width:100%;" placeholder="https://api.example.com/"></div>
                <div><label style="font-size:12px;color:#666;">认证方式</label>
                    <select id="api-auth" class="form-control" style="width:100%;">
                        <option value="bearer">Bearer Token</option>
                        <option value="apikey">API Key</option>
                        <option value="basic">Basic Auth</option>
                    </select>
                </div>
                <div><label style="font-size:12px;color:#666;">App ID</label><input id="api-appid" class="form-control" style="width:100%;" placeholder="可选"></div>
                <div><label style="font-size:12px;color:#666;">API Key / Token</label><input id="api-key" class="form-control" style="width:100%;" type="password" placeholder="可选"></div>
                <div><label style="font-size:12px;color:#666;">API Secret</label><input id="api-secret" class="form-control" style="width:100%;" type="password" placeholder="可选"></div>
            </div>
            <div style="margin-top:12px;font-size:12px;color:#64748b;background:#f8fafc;padding:8px;border-radius:6px;">
                💡 提示：创建后可点击"测试"按钮验证API连接是否可达
            </div>
            <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
                <button class="btn btn-default" onclick="document.getElementById('api-form-modal').remove()">取消</button>
                <button class="btn btn-primary" onclick="saveApiIntegration(${id||0})">保存</button>
            </div>
        </div>`;
    document.body.appendChild(modal);
}

function saveApiIntegration(id) {
    const name = document.getElementById('api-name').value.trim();
    const url = document.getElementById('api-url').value.trim();
    if (!name || !url) { showToast('请填写对接名称和API地址', 'warning'); return; }
    const params = new URLSearchParams();
    params.append('name', name);
    params.append('base_url', url);
    params.append('api_type', document.getElementById('api-type').value);
    params.append('auth_type', document.getElementById('api-auth').value);
    const appid = document.getElementById('api-appid').value.trim();
    const key = document.getElementById('api-key').value.trim();
    const secret = document.getElementById('api-secret').value.trim();
    if (appid) params.append('app_id', appid);
    if (key) params.append('api_key', key);
    if (secret) params.append('api_secret', secret);

    const isEdit = !!id;
    const method = isEdit ? 'PUT' : 'POST';
    const apiUrl = isEdit ? apiBase + '/api-center/integrations/' + id + '?' + params.toString() : apiBase + '/api-center/integrations?' + params.toString();
    fetch(apiUrl, { method: method, headers: authHeaders })
        .then(r => r.json())
        .then(res => {
            if (res.success) {
                showToast(isEdit ? '更新成功！' : '创建成功！', 'success');
                document.getElementById('api-form-modal').remove();
                loadApiIntegrations();
            } else {
                showToast(res.detail || res.message || '保存失败', 'error');
            }
        })
        .catch(e => showToast('保存失败: ' + e.message, 'error'));
}

function testApiIntegration(id) {
    const btn = event.target;
    const origText = btn.textContent;
    btn.textContent = '测试中...';
    btn.disabled = true;
    fetch(apiBase + '/api-center/integrations/' + id + '/test', { method: 'POST', headers: authHeaders })
        .then(r => r.json())
        .then(res => {
            showToast(res.message || (res.success ? '测试通过' : '测试失败'), 'success');
            btn.textContent = origText;
            btn.disabled = false;
            loadApiIntegrations();
        })
        .catch(e => {
            showToast('测试失败: ' + e.message, 'error');
            btn.textContent = origText;
            btn.disabled = false;
        });
}

function deleteApiIntegration(id) {
    if (!confirm('确定删除该API对接配置？')) return;
    fetch(apiBase + '/api-center/integrations/' + id, { method: 'DELETE', headers: authHeaders })
        .then(r => r.json())
        .then(res => { if (res.success) loadApiIntegrations(); else showToast(res.detail || '删除失败', 'error'); })
        .catch(e => showToast('删除失败: ' + e.message, 'error'));
}
