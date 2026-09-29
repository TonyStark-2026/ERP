/* ============================================================
 * 生产管理 V2 前端模块
 * 生产计划 · MRP分析 · 工艺路线 · 生产工单 · 派工 · 领料 · 报工 · 质检 · 委外 · 设备
 * ============================================================ */
if (typeof escapeHtml === 'undefined') {
    window.escapeHtml = function(s){ if(s===null||s===undefined)return ''; var d=document.createElement('div'); d.textContent=String(s); return d.innerHTML; };
}
var _pmTab = 'plans';

function _renderProductionV2Impl() {
    setTimeout(()=>switchPMTab('plans'),80);
    return `<div style="padding:16px;"><div class="card">
        <div class="card-title" style="display:flex;justify-content:space-between;align-items:center;background:linear-gradient(135deg,#ca8a04,#b45309);color:#fff;border-radius:8px 8px 0 0;padding:12px 16px;margin:-16px -16px 12px -16px;">
            <span style="font-size:16px;font-weight:bold;">🏭 生产管理中心</span>
            <span style="font-size:12px;">计划 → MRP → 工单 → 派工 → 报工 → 质检 → 委外</span>
        </div>
        <div style="padding:12px 16px;">
            <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:8px;margin-bottom:16px;">
                <div class="pm-stat"><div class="num" id="pm-stat-wo">-</div><div class="lbl">活跃工单</div></div>
                <div class="pm-stat"><div class="num" id="pm-stat-plan">-</div><div class="lbl">生产计划</div></div>
                <div class="pm-stat"><div class="num" id="pm-stat-mrp">-</div><div class="lbl">MRP运算</div></div>
                <div class="pm-stat"><div class="num" id="pm-stat-disp">-</div><div class="lbl">派工单</div></div>
                <div class="pm-stat"><div class="num" id="pm-stat-rt">-</div><div class="lbl">工艺路线</div></div>
                <div class="pm-stat"><div class="num" id="pm-stat-rp">-</div><div class="lbl">待审批领料</div></div>
                <div class="pm-stat"><div class="num" id="pm-stat-wr">-</div><div class="lbl">报工单</div></div>
                <div class="pm-stat"><div class="num" id="pm-stat-outs">-</div><div class="lbl">委外订单</div></div>
                <div class="pm-stat"><div class="num" id="pm-stat-eq">-</div><div class="lbl">设备</div></div>
            </div>
            <div style="display:flex;gap:3px;border-bottom:2px solid #ca8a04;margin-bottom:16px;flex-wrap:wrap;">
                <button class="btn pm-tab-btn active" data-pm-tab="plans" onclick="switchPMTab('plans')">📋 生产计划</button>
                <button class="btn pm-tab-btn" data-pm-tab="mrp" onclick="switchPMTab('mrp')">📊 MRP分析</button>
                <button class="btn pm-tab-btn" data-pm-tab="routings" onclick="switchPMTab('routings')">🛠️ 工艺路线</button>
                <button class="btn pm-tab-btn" data-pm-tab="workorders" onclick="switchPMTab('workorders')">🏭 生产工单</button>
                <button class="btn pm-tab-btn" data-pm-tab="dispatches" onclick="switchPMTab('dispatches')">⚡ 派工管理</button>
                <button class="btn pm-tab-btn" data-pm-tab="requisitions" onclick="switchPMTab('requisitions')">📦 生产领料</button>
                <button class="btn pm-tab-btn" data-pm-tab="reports" onclick="switchPMTab('reports')">✅ 工序报工</button>
                <button class="btn pm-tab-btn" data-pm-tab="inspections" onclick="switchPMTab('inspections')">🔍 质量检验</button>
                <button class="btn pm-tab-btn" data-pm-tab="outsourcing" onclick="switchPMTab('outsourcing')">🔄 委外加工</button>
                <button class="btn pm-tab-btn" data-pm-tab="equipments" onclick="switchPMTab('equipments')">⚙️ 设备工作中心</button>
            </div>
            <div id="pm-tab-plans" class="pm-tab-panel"></div>
            <div id="pm-tab-mrp" class="pm-tab-panel" style="display:none;"></div>
            <div id="pm-tab-routings" class="pm-tab-panel" style="display:none;"></div>
            <div id="pm-tab-workorders" class="pm-tab-panel" style="display:none;"></div>
            <div id="pm-tab-dispatches" class="pm-tab-panel" style="display:none;"></div>
            <div id="pm-tab-requisitions" class="pm-tab-panel" style="display:none;"></div>
            <div id="pm-tab-reports" class="pm-tab-panel" style="display:none;"></div>
            <div id="pm-tab-inspections" class="pm-tab-panel" style="display:none;"></div>
            <div id="pm-tab-outsourcing" class="pm-tab-panel" style="display:none;"></div>
            <div id="pm-tab-equipments" class="pm-tab-panel" style="display:none;"></div>
        </div>
    </div></div>
    <style>
        .pm-tab-btn{padding:4px 10px;font-size:11px;border:1px solid #e5e7eb;background:#fff;color:#666;border-radius:6px;cursor:pointer;transition:all .2s;}
        .pm-tab-btn:hover{background:#fefce8;border-color:#ca8a04;}
        .pm-tab-btn.active{background:linear-gradient(135deg,#ca8a04,#b45309);color:#fff;border-color:transparent;}
        .pm-stat{background:linear-gradient(135deg,#fefce8,#fef3c7);border:1px solid #fde68a;border-radius:10px;padding:10px 8px;text-align:center;}
        .pm-stat .num{font-size:20px;font-weight:bold;color:#b45309;}
        .pm-stat .lbl{font-size:10px;color:#666;margin-top:3px;}
        table.pm-table{width:100%;border-collapse:collapse;font-size:12px;}
        .pm-table th{background:#f1f5f9;padding:8px;text-align:left;border-bottom:2px solid #cbd5e1;color:#475569;white-space:nowrap;}
        .pm-table td{padding:6px 8px;border-bottom:1px solid #e2e8f0;}
        .pm-table tr:hover td{background:#f8fafc;}
        .pm-badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;}
        .pm-progress{display:inline-block;width:60px;height:8px;background:#e2e8f0;border-radius:4px;overflow:hidden;vertical-align:middle;}
        .pm-progress-fill{height:100%;border-radius:4px;}
    </style>`;
}

function switchPMTab(tab){
    _pmTab=tab;
    document.querySelectorAll('.pm-tab-btn').forEach(b=>b.classList.toggle('active',b.getAttribute('data-pm-tab')===tab));
    document.querySelectorAll('.pm-tab-panel').forEach(p=>p.style.display='none');
    const map={plans:'pm-tab-plans',mrp:'pm-tab-mrp',routings:'pm-tab-routings',workorders:'pm-tab-workorders',
        dispatches:'pm-tab-dispatches',requisitions:'pm-tab-requisitions',reports:'pm-tab-reports',
        inspections:'pm-tab-inspections',outsourcing:'pm-tab-outsourcing',equipments:'pm-tab-equipments'};
    const el=document.getElementById(map[tab]); if(!el)return; el.style.display='block';
    if(tab==='plans') el.innerHTML=pmPlansUI(),setTimeout(loadPMPlans,30);
    if(tab==='mrp') el.innerHTML=pmMrpUI(),setTimeout(loadPMMrp,30);
    if(tab==='routings') el.innerHTML=pmRoutingsUI(),setTimeout(loadPMRoutings,30);
    if(tab==='workorders') el.innerHTML=pmWorkOrdersUI(),setTimeout(loadPMWorkOrders,30);
    if(tab==='dispatches') el.innerHTML=pmDispatchesUI(),setTimeout(loadPMDispatches,30);
    if(tab==='requisitions') el.innerHTML=pmReqUI(),setTimeout(loadPMReqs,30);
    if(tab==='reports') el.innerHTML=pmReportsUI(),setTimeout(loadPMReports,30);
    if(tab==='inspections') el.innerHTML=pmInspectionsUI(),setTimeout(loadPMInspections,30);
    if(tab==='outsourcing') el.innerHTML=pmOutsourcingUI(),setTimeout(loadPMOutsourcing,30);
    if(tab==='equipments') el.innerHTML=pmEquipmentsUI(),setTimeout(loadPMEquipments,30);
}

// ============================================================
// 生产计划
// ============================================================
function pmPlansUI(){
    return `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <h3 style="margin:0;color:#b45309;font-size:14px;">生产计划列表</h3>
        <select id="pm-plan-filter" onchange="loadPMPlans()" style="padding:4px 8px;border:1px solid #cbd5e1;border-radius:6px;font-size:12px;">
            <option value="ALL">全部状态</option>
            <option value="CONFIRMED">已确认</option>
            <option value="RELEASED">已下达</option>
            <option value="COMPLETED">已完成</option>
        </select>
    </div>
    <div id="pm-plan-list" style="overflow-x:auto;color:#888;padding:20px;text-align:center;">加载中...</div>`;
}
function loadPMPlans(){
    const filter=document.getElementById('pm-plan-filter')?.value||'ALL';
    fetch(apiBase+'/pm2/production-plans?status='+filter,{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){document.getElementById('pm-plan-list').innerHTML='<div style="color:#dc2626;">加载失败</div>';return;}
        const items=res.data||[];
        if(!items.length){document.getElementById('pm-plan-list').innerHTML='<div style="color:#888;padding:20px;text-align:center;">暂无生产计划</div>';return;}
        let h='<table class="pm-table"><thead><tr><th>计划号</th><th>类型</th><th>计划日期</th><th>状态</th><th>项目</th><th>总数量</th><th>计划员</th><th>明细</th></tr></thead><tbody>';
        items.forEach(p=>{
            const stColor={'DRAFT':'#94a3b8','CONFIRMED':'#2563eb','RELEASED':'#ca8a04','COMPLETED':'#16a34a','CLOSED':'#64748b'}[p.status]||'#666';
            h+=`<tr>
                <td style="font-weight:600;color:#b45309;">${escapeHtml(p.plan_no)}</td>
                <td>${escapeHtml(p.plan_type_label)}</td>
                <td>${p.plan_date||'-'}</td>
                <td><span class="pm-badge" style="background:${stColor}1a;color:${stColor};">${escapeHtml(p.status_label)}</span></td>
                <td>${escapeHtml(p.project_name||'-')}</td>
                <td style="text-align:center;">${p.total_qty}</td>
                <td>${escapeHtml(p.planner)}</td>
                <td><button class="btn" style="padding:2px 8px;font-size:11px;border:1px solid #cbd5e1;border-radius:4px;cursor:pointer;" onclick="viewPlanItems(${p.id})">查看</button></td>
            </tr>`;
        });
        h+='</tbody></table>';
        document.getElementById('pm-plan-list').innerHTML=h;
    }).catch(()=>{document.getElementById('pm-plan-list').innerHTML='<div style="color:#dc2626;">加载失败</div>';});
}
function viewPlanItems(planId){
    fetch(apiBase+'/pm2/production-plans',{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success)return;
        const plan=(res.data||[]).find(p=>p.id===planId);
        if(!plan)return;
        const items=plan.items||[];
        let h='<div style="position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:9999;display:flex;align-items:center;justify-content:center;" onclick="if(event.target===this)this.remove()">';
        h+='<div style="background:#fff;border-radius:10px;padding:20px;max-width:600px;width:90%;max-height:80vh;overflow:auto;">';
        h+='<h3 style="margin:0 0 12px;color:#b45309;">'+escapeHtml(plan.plan_no)+' - 计划明细</h3>';
        if(!items.length){h+='<div style="color:#888;text-align:center;padding:20px;">暂无明细</div>';}
        else{
            h+='<table class="pm-table"><thead><tr><th>物料编码</th><th>物料名称</th><th>数量</th><th>开始日期</th><th>结束日期</th></tr></thead><tbody>';
            items.forEach(it=>{
                h+=`<tr><td>${escapeHtml(it.product_code)}</td><td>${escapeHtml(it.product_name)}</td><td style="text-align:center;">${it.quantity}</td><td>${it.start_date||'-'}</td><td>${it.end_date||'-'}</td></tr>`;
            });
            h+='</tbody></table>';
        }
        h+='<div style="text-align:right;margin-top:12px;"><button class="btn" style="padding:6px 16px;" onclick="this.closest(\'[style*=fixed]\').remove()">关闭</button></div>';
        h+='</div></div>';
        document.body.insertAdjacentHTML('beforeend',h);
    });
}

// ============================================================
// MRP分析
// ============================================================
function pmMrpUI(){
    return `<div style="margin-bottom:12px;">
        <h3 style="margin:0 0 8px;color:#b45309;font-size:14px;">MRP物料需求分析</h3>
        <div style="font-size:11px;color:#888;">毛需求 / 库存 / 在途 / 安全库存 / 净需求 / 计划订单</div>
    </div>
    <div id="pm-mrp-list" style="overflow-x:auto;color:#888;padding:20px;text-align:center;">加载中...</div>`;
}
function loadPMMrp(){
    fetch(apiBase+'/pm2/mrp-results',{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){document.getElementById('pm-mrp-list').innerHTML='<div style="color:#dc2626;">加载失败</div>';return;}
        const data=res.data||{}; const items=data.items||[];
        if(!items.length){document.getElementById('pm-mrp-list').innerHTML='<div style="color:#888;padding:20px;text-align:center;">暂无MRP数据</div>';return;}
        let h='<table class="pm-table"><thead><tr><th>层级</th><th>物料编码</th><th>物料名称</th><th>规格</th><th>毛需求</th><th>库存</th><th>在途</th><th>安全库存</th><th>净需求</th><th>计划订单</th><th>计划类型</th><th>计划交期</th><th>下达日期</th></tr></thead><tbody>';
        items.forEach(m=>{
            const typeColor={'PRODUCTION':'#ca8a04','PURCHASE':'#2563eb'}[m.planned_type]||'#666';
            const netColor=m.net_requirement>0?'#dc2626':'#16a34a';
            h+=`<tr>
                <td style="text-align:center;font-weight:600;">L${m.bom_level}</td>
                <td style="font-weight:600;color:#b45309;">${escapeHtml(m.material_code)}</td>
                <td>${escapeHtml(m.material_name)}</td>
                <td>${escapeHtml(m.specification||'-')}</td>
                <td style="text-align:center;">${m.gross_requirement}</td>
                <td style="text-align:center;color:#16a34a;">${m.on_hand_qty}</td>
                <td style="text-align:center;color:#2563eb;">${m.on_order_qty}</td>
                <td style="text-align:center;">${m.safety_stock}</td>
                <td style="text-align:center;font-weight:600;color:${netColor};">${m.net_requirement}</td>
                <td style="text-align:center;font-weight:600;">${m.planned_order_qty}</td>
                <td><span class="pm-badge" style="background:${typeColor}1a;color:${typeColor};">${escapeHtml(m.planned_type_label)}</span></td>
                <td>${m.planned_date||'-'}</td>
                <td>${m.planned_release_date||'-'}</td>
            </tr>`;
        });
        h+='</tbody></table>';
        document.getElementById('pm-mrp-list').innerHTML=h;
    }).catch(()=>{document.getElementById('pm-mrp-list').innerHTML='<div style="color:#dc2626;">加载失败</div>';});
}

// ============================================================
// 生产工单管理
// ============================================================
function pmWorkOrdersUI(){
    return `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <h3 style="margin:0;color:#b45309;font-size:14px;">生产工单列表</h3>
        <div style="display:flex;gap:8px;align-items:center;">
            <select id="pm-wo-filter" onchange="loadPMWorkOrders()" style="padding:4px 8px;border:1px solid #cbd5e1;border-radius:6px;font-size:12px;">
                <option value="ALL">全部状态</option>
                <option value="RELEASED">已下达</option>
                <option value="IN_PROGRESS">进行中</option>
                <option value="COMPLETED">已完工</option>
            </select>
            <button class="btn btn-primary" style="padding:4px 12px;font-size:12px;" onclick="pmWOForm()">➕ 新建工单</button>
        </div>
    </div>
    <div id="pm-wo-list" style="overflow-x:auto;color:#888;padding:20px;text-align:center;">加载中...</div>`;
}
function loadPMWorkOrders(){
    const filter=document.getElementById('pm-wo-filter')?.value||'ALL';
    fetch(apiBase+'/pm2/work-orders?status='+filter,{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){document.getElementById('pm-wo-list').innerHTML='<div style="color:#dc2626;">加载失败</div>';return;}
        const items=res.data||[];
        if(!items.length){document.getElementById('pm-wo-list').innerHTML='<div style="color:#888;padding:20px;text-align:center;">暂无工单</div>';return;}
        let h='<table class="pm-table"><thead><tr><th>工单号</th><th>产品</th><th>计划量</th><th>完工量</th><th>完工率</th><th>状态</th><th>优先级</th><th>开始</th><th>结束</th><th>实际成本</th><th>操作</th></tr></thead><tbody>';
        items.forEach(w=>{
            const ratio=Math.round(w.completion_ratio||0);
            const ratioColor=ratio>=100?'#16a34a':ratio>0?'#ca8a04':'#94a3b8';
            const stColor={'PLANNED':'#94a3b8','RELEASED':'#2563eb','IN_PROGRESS':'#ca8a04','COMPLETED':'#16a34a','CLOSED':'#64748b'}[w.status]||'#666';
            let ops='';
            if(w.status==='RELEASED') ops+=`<button class="btn" style="padding:2px 8px;font-size:11px;color:#ca8a04;border:1px solid #ca8a04;border-radius:4px;cursor:pointer;" onclick="startWO(${w.id})">开工</button> `;
            if(w.status==='IN_PROGRESS') ops+=`<button class="btn" style="padding:2px 8px;font-size:11px;color:#2563eb;border:1px solid #2563eb;border-radius:4px;cursor:pointer;" onclick="progressWO(${w.id},${w.planned_qty})">报工</button> `;
            if(w.status!=='COMPLETED') ops+=`<button class="btn" style="padding:2px 8px;font-size:11px;color:#16a34a;border:1px solid #16a34a;border-radius:4px;cursor:pointer;" onclick="completeWO(${w.id})">完工</button> `;
            ops+=`<button class="btn" style="padding:2px 8px;font-size:11px;border:1px solid #cbd5e1;border-radius:4px;cursor:pointer;" onclick="viewWOProcesses(${w.id})">工序</button>`;
            h+=`<tr>
                <td style="font-weight:600;color:#b45309;">${escapeHtml(w.work_order_no)}</td>
                <td>${escapeHtml(w.product_code)} ${escapeHtml(w.product_name)}</td>
                <td style="text-align:center;">${w.planned_qty}</td>
                <td style="text-align:center;">${w.completed_qty}</td>
                <td style="text-align:center;"><div class="pm-progress" style="display:inline-block;width:50px;height:8px;background:#e2e8f0;border-radius:4px;overflow:hidden;vertical-align:middle;margin-right:4px;"><div class="pm-progress-fill" style="width:${ratio}%;height:100%;background:${ratioColor};"></div></div><span style="color:${ratioColor};font-weight:600;font-size:11px;">${ratio}%</span></td>
                <td><span class="pm-badge" style="background:${stColor}1a;color:${stColor};">${escapeHtml(w.status_label)}</span></td>
                <td style="text-align:center;">${w.priority==='HIGH'?'<span style="color:#dc2626;font-weight:600;">高</span>':'<span style="color:#666;">正常</span>'}</td>
                <td>${w.start_date||'-'}</td>
                <td>${w.end_date||'-'}</td>
                <td style="text-align:right;">¥${(w.actual_total||0).toLocaleString()}</td>
                <td style="white-space:nowrap;">${ops}</td>
            </tr>`;
        });
        h+='</tbody></table>';
        document.getElementById('pm-wo-list').innerHTML=h;
    }).catch(()=>{document.getElementById('pm-wo-list').innerHTML='<div style="color:#dc2626;">加载失败</div>';});
}
function startWO(id){
    if(!confirm('确认开始生产？'))return;
    fetch(apiBase+'/pm2/work-orders/'+id+'/start',{method:'PUT',headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){showToast(res.message,'error');return;}
        showToast('工单已开工','success'); loadPMWorkOrders();
    });
}
function progressWO(id,plannedQty){
    const completed=prompt('请输入完工数量：',plannedQty);
    if(completed===null)return;
    fetch(apiBase+'/pm2/work-orders/'+id+'/progress',{method:'PUT',headers:{...authHeaders,'Content-Type':'application/json'},body:JSON.stringify({completed_qty:parseInt(completed)||0})}).then(r=>r.json()).then(res=>{
        if(!res.success){showToast(res.message,'error');return;}
        showToast('进度已更新','success'); loadPMWorkOrders();
    });
}
function completeWO(id){
    if(!confirm('确认完工？将自动设置完工量=计划量'))return;
    fetch(apiBase+'/pm2/work-orders/'+id+'/complete',{method:'PUT',headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){showToast(res.message,'error');return;}
        showToast('工单已完工','success'); loadPMWorkOrders();
    });
}
function pmWOForm(){
    const m=document.createElement('div'); m.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    m.innerHTML=`<div style="background:#fff;border-radius:10px;padding:20px;width:400px;max-width:92vw;">
        <h3 style="margin:0 0 16px;color:#b45309;">新建生产工单</h3>
        <div style="display:grid;gap:10px;font-size:12px;">
            <div><label>产品ID *</label><input id="wo-pid" type="number" placeholder="物料ID" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div><label>计划数量 *</label><input id="wo-qty" type="number" placeholder="如 100" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                <div><label>优先级</label><select id="wo-pri" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"><option value="NORMAL">正常</option><option value="HIGH">高</option></select></div>
                <div><label>BOM ID</label><input id="wo-bom" type="number" placeholder="可选" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                <div><label>开始日期</label><input id="wo-sd" type="date" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
                <div><label>结束日期</label><input id="wo-ed" type="date" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            </div>
        </div>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
            <button class="btn" style="padding:6px 14px;font-size:12px;" onclick="this.closest('[style*=fixed]').remove()">取消</button>
            <button class="btn btn-primary" style="padding:6px 14px;font-size:12px;" onclick="savePMWO(this)">创建</button>
        </div></div>`;
    document.body.appendChild(m);
}
function savePMWO(btn){
    const payload={product_id:parseInt(document.getElementById('wo-pid').value)||null,planned_qty:parseInt(document.getElementById('wo-qty').value)||0,priority:document.getElementById('wo-pri').value,bom_id:parseInt(document.getElementById('wo-bom').value)||null,start_date:document.getElementById('wo-sd').value||null,end_date:document.getElementById('wo-ed').value||null};
    if(!payload.product_id||!payload.planned_qty){showToast('产品ID和计划数量必填','warning');return;}
    fetch(apiBase+'/pm2/work-orders',{method:'POST',headers:{...authHeaders,'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json()).then(res=>{
        if(!res.success){showToast(res.message,'error');return;}
        btn.closest('[style*=fixed]').remove(); loadPMWorkOrders(); loadPMOverview();
    });
}
function viewWOProcesses(woId){
    fetch(apiBase+'/pm2/work-orders/'+woId+'/processes',{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){showToast('加载工序失败','error');return;}
        const items=res.data||[];
        let h='<div style="position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:9999;display:flex;align-items:center;justify-content:center;" onclick="if(event.target===this)this.remove()">';
        h+='<div style="background:#fff;border-radius:10px;padding:20px;max-width:750px;width:90%;max-height:80vh;overflow:auto;">';
        h+='<h3 style="margin:0 0 12px;color:#b45309;">工单工序明细</h3>';
        if(!items.length){h+='<div style="color:#888;text-align:center;padding:20px;">暂无工序数据</div>';}
        else{
            h+='<table class="pm-table"><thead><tr><th>序号</th><th>工序名称</th><th>工作中心</th><th>数量</th><th>状态</th><th>计划开始</th><th>计划结束</th><th>操作</th></tr></thead><tbody>';
            items.forEach(p=>{
                const stColor={'PENDING':'#94a3b8','IN_PROGRESS':'#ca8a04','COMPLETED':'#16a34a'}[p.status]||'#666';
                let ops='';
                if(p.status==='PENDING') ops+=`<button class="btn" style="padding:2px 6px;font-size:10px;color:#ca8a04;border:1px solid #ca8a04;border-radius:4px;cursor:pointer;" onclick="startProc(${p.id})">开工</button> `;
                if(p.status==='IN_PROGRESS') ops+=`<button class="btn" style="padding:2px 6px;font-size:10px;color:#16a34a;border:1px solid #16a34a;border-radius:4px;cursor:pointer;" onclick="completeProc(${p.id})">完工</button>`;
                h+=`<tr><td style="text-align:center;font-weight:600;">${p.process_seq}</td><td>${escapeHtml(p.process_name)}</td><td>${escapeHtml(p.work_center)}</td><td style="text-align:center;">${p.quantity}</td><td><span class="pm-badge" style="background:${stColor}1a;color:${stColor};">${escapeHtml(p.status_label)}</span></td><td>${p.plan_start||'-'}</td><td>${p.plan_end||'-'}</td><td style="white-space:nowrap;">${ops||'-'}</td></tr>`;
            });
            h+='</tbody></table>';
        }
        h+='<div style="text-align:right;margin-top:12px;"><button class="btn" style="padding:6px 16px;" onclick="this.closest(\'[style*=fixed]\').remove()">关闭</button></div>';
        h+='</div></div>';
        document.body.insertAdjacentHTML('beforeend',h);
    });
}
function startProc(id){
    fetch(apiBase+'/pm2/work-order-processes/'+id+'/start',{method:'PUT',headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){showToast(res.message,'error');return;}
        showToast('工序已开工','success');
    });
}
function completeProc(id){
    fetch(apiBase+'/pm2/work-order-processes/'+id+'/complete',{method:'PUT',headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){showToast(res.message,'error');return;}
        showToast('工序已完工','success');
    });
}

// ============================================================
// 派工管理
// ============================================================
function pmDispatchesUI(){
    return `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <h3 style="margin:0;color:#b45309;font-size:14px;">派工单列表</h3>
        <div style="display:flex;gap:8px;">
            <select id="pm-disp-filter" onchange="loadPMDispatches()" style="padding:4px 8px;border:1px solid #cbd5e1;border-radius:6px;font-size:12px;">
                <option value="ALL">全部</option>
                <option value="DISPATCHED">已派工</option>
                <option value="IN_PROGRESS">加工中</option>
                <option value="COMPLETED">已完成</option>
            </select>
            <button class="btn btn-primary" style="padding:4px 12px;font-size:12px;" onclick="pmDispForm()">➕ 新增派工</button>
        </div>
    </div>
    <div id="pm-disp-list" style="overflow-x:auto;color:#888;padding:20px;text-align:center;">加载中...</div>`;
}
function loadPMDispatches(){
    const filter=document.getElementById('pm-disp-filter')?.value||'ALL';
    fetch(apiBase+'/pm2/dispatches?status='+filter,{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){document.getElementById('pm-disp-list').innerHTML='<div style="color:#dc2626;">加载失败</div>';return;}
        const items=res.data||[];
        if(!items.length){document.getElementById('pm-disp-list').innerHTML='<div style="color:#888;padding:20px;text-align:center;">暂无派工单</div>';return;}
        let h='<table class="pm-table"><thead><tr><th>派工单号</th><th>工单号</th><th>产品</th><th>工序</th><th>数量</th><th>状态</th><th>调度员</th><th>操作工</th><th>日期</th><th>操作</th></tr></thead><tbody>';
        items.forEach(d=>{
            const stColor={'PENDING':'#94a3b8','DISPATCHED':'#2563eb','IN_PROGRESS':'#ca8a04','COMPLETED':'#16a34a','CANCELLED':'#dc2626'}[d.status]||'#666';
            let ops=d.status!=='COMPLETED'?`<button class="btn" style="padding:2px 8px;font-size:11px;color:#16a34a;border:1px solid #16a34a;border-radius:4px;cursor:pointer;" onclick="completeDisp(${d.id})">完工</button>`:'-';
            h+=`<tr>
                <td style="font-weight:600;color:#b45309;">${escapeHtml(d.dispatch_no)}</td>
                <td>${escapeHtml(d.work_order_no||'-')}</td>
                <td>${escapeHtml(d.product_code||'')} ${escapeHtml(d.product_name||'')}</td>
                <td>${escapeHtml(d.process_name||'-')}</td>
                <td style="text-align:center;">${d.dispatch_qty}</td>
                <td><span class="pm-badge" style="background:${stColor}1a;color:${stColor};">${escapeHtml(d.status_label)}</span></td>
                <td>${escapeHtml(d.dispatcher||'-')}</td>
                <td>${escapeHtml(d.operator||'-')}</td>
                <td>${d.dispatch_date||'-'}</td>
                <td>${ops}</td>
            </tr>`;
        });
        h+='</tbody></table>';
        document.getElementById('pm-disp-list').innerHTML=h;
    }).catch(()=>{document.getElementById('pm-disp-list').innerHTML='<div style="color:#dc2626;">加载失败</div>';});
}
function pmDispForm(){
    const m=document.createElement('div'); m.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    m.innerHTML=`<div style="background:#fff;border-radius:10px;padding:20px;width:400px;max-width:92vw;">
        <h3 style="margin:0 0 16px;color:#b45309;">新增派工单</h3>
        <div style="display:grid;gap:10px;font-size:12px;">
            <div><label>工单ID *</label><input id="disp-woid" type="number" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div><label>工序ID</label><input id="disp-pid" type="number" placeholder="routing_operations ID" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                <div><label>派工数量</label><input id="disp-qty" type="number" value="1" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
                <div><label>工作中心ID</label><input id="disp-wcid" type="number" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                <div><label>调度员</label><input id="disp-disp" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
                <div><label>操作工</label><input id="disp-opr" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            </div>
        </div>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
            <button class="btn" style="padding:6px 14px;font-size:12px;" onclick="this.closest('[style*=fixed]').remove()">取消</button>
            <button class="btn btn-primary" style="padding:6px 14px;font-size:12px;" onclick="savePMDisp(this)">创建</button>
        </div></div>`;
    document.body.appendChild(m);
}
function savePMDisp(btn){
    const payload={work_order_id:parseInt(document.getElementById('disp-woid').value)||null,process_id:parseInt(document.getElementById('disp-pid').value)||null,work_center_id:parseInt(document.getElementById('disp-wcid').value)||null,dispatch_qty:parseInt(document.getElementById('disp-qty').value)||1,dispatcher:document.getElementById('disp-disp').value,operator:document.getElementById('disp-opr').value};
    if(!payload.work_order_id){showToast('工单ID必填','warning');return;}
    fetch(apiBase+'/pm2/dispatches',{method:'POST',headers:{...authHeaders,'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json()).then(res=>{
        if(!res.success){showToast(res.message,'error');return;}
        btn.closest('[style*=fixed]').remove(); loadPMDispatches(); loadPMOverview();
    });
}
function completeDisp(id){
    if(!confirm('确认派工完工？'))return;
    fetch(apiBase+'/pm2/dispatches/'+id+'/complete',{method:'PUT',headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){showToast(res.message,'error');return;}
        showToast('派工已完工','success'); loadPMDispatches();
    });
}

// ============================================================
// 委外加工管理
// ============================================================
function pmOutsourcingUI(){
    return `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <h3 style="margin:0;color:#b45309;font-size:14px;">委外加工订单</h3>
        <div style="display:flex;gap:8px;">
            <select id="pm-outs-filter" onchange="loadPMOutsourcing()" style="padding:4px 8px;border:1px solid #cbd5e1;border-radius:6px;font-size:12px;">
                <option value="ALL">全部</option>
                <option value="PENDING">待发料</option>
                <option value="ISSUED">已发料</option>
                <option value="RECEIVED">已收货</option>
            </select>
            <button class="btn btn-primary" style="padding:4px 12px;font-size:12px;" onclick="pmOutsForm()">➕ 新增委外</button>
        </div>
    </div>
    <div id="pm-outs-list" style="overflow-x:auto;color:#888;padding:20px;text-align:center;">加载中...</div>`;
}
function loadPMOutsourcing(){
    const filter=document.getElementById('pm-outs-filter')?.value||'ALL';
    fetch(apiBase+'/pm2/outsourcing-orders?status='+filter,{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){document.getElementById('pm-outs-list').innerHTML='<div style="color:#dc2626;">加载失败</div>';return;}
        const items=res.data||[];
        if(!items.length){document.getElementById('pm-outs-list').innerHTML='<div style="color:#888;padding:20px;text-align:center;">暂无委外订单</div>';return;}
        let h='<table class="pm-table"><thead><tr><th>订单号</th><th>供应商</th><th>物料</th><th>工序</th><th>数量</th><th>单价</th><th>总价</th><th>状态</th><th>计划日期</th><th>发料</th><th>收货</th><th>操作</th></tr></thead><tbody>';
        items.forEach(o=>{
            const stColor={'PENDING':'#94a3b8','ISSUED':'#2563eb','IN_PROGRESS':'#ca8a04','RECEIVED':'#16a34a','COMPLETED':'#64748b'}[o.status]||'#666';
            let ops='';
            if(o.status==='PENDING') ops+=`<button class="btn" style="padding:2px 8px;font-size:11px;color:#ca8a04;border:1px solid #ca8a04;border-radius:4px;cursor:pointer;" onclick="issueOuts(${o.id})">发料</button> `;
            if(o.status==='ISSUED'||o.status==='IN_PROGRESS') ops+=`<button class="btn" style="padding:2px 8px;font-size:11px;color:#16a34a;border:1px solid #16a34a;border-radius:4px;cursor:pointer;" onclick="receiveOuts(${o.id})">收货</button>`;
            if(!ops) ops='-';
            h+=`<tr>
                <td style="font-weight:600;color:#b45309;">${escapeHtml(o.order_no)}</td>
                <td>${escapeHtml(o.supplier_name||'-')}</td>
                <td>${escapeHtml(o.material_code||'')} ${escapeHtml(o.material_name||'')}</td>
                <td>${escapeHtml(o.process_name||'-')}</td>
                <td style="text-align:center;">${o.ordered_qty}</td>
                <td style="text-align:right;">¥${(o.unit_price||0).toLocaleString()}</td>
                <td style="text-align:right;font-weight:600;">¥${(o.total_fee||0).toLocaleString()}</td>
                <td><span class="pm-badge" style="background:${stColor}1a;color:${stColor};">${escapeHtml(o.status_label)}</span></td>
                <td>${o.planned_date||'-'}</td>
                <td style="font-size:10px;">${o.issue_no||'-'}</td>
                <td style="font-size:10px;">${o.receive_no||'-'}</td>
                <td style="white-space:nowrap;">${ops}</td>
            </tr>`;
        });
        h+='</tbody></table>';
        document.getElementById('pm-outs-list').innerHTML=h;
    }).catch(()=>{document.getElementById('pm-outs-list').innerHTML='<div style="color:#dc2626;">加载失败</div>';});
}
function pmOutsForm(){
    const m=document.createElement('div'); m.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    m.innerHTML=`<div style="background:#fff;border-radius:10px;padding:20px;width:420px;max-width:92vw;">
        <h3 style="margin:0 0 16px;color:#b45309;">新增委外加工订单</h3>
        <div style="display:grid;gap:10px;font-size:12px;">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                <div><label>供应商ID *</label><input id="outs-sid" type="number" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
                <div><label>物料ID *</label><input id="outs-mid" type="number" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                <div><label>加工数量 *</label><input id="outs-qty" type="number" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
                <div><label>单价</label><input id="outs-price" type="number" step="0.01" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                <div><label>工序名称</label><input id="outs-pn" placeholder="如 表面处理" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
                <div><label>计划日期</label><input id="outs-pd" type="date" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            </div>
        </div>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
            <button class="btn" style="padding:6px 14px;font-size:12px;" onclick="this.closest('[style*=fixed]').remove()">取消</button>
            <button class="btn btn-primary" style="padding:6px 14px;font-size:12px;" onclick="savePMOuts(this)">创建</button>
        </div></div>`;
    document.body.appendChild(m);
}
function savePMOuts(btn){
    const payload={supplier_id:parseInt(document.getElementById('outs-sid').value)||null,material_id:parseInt(document.getElementById('outs-mid').value)||null,ordered_qty:parseInt(document.getElementById('outs-qty').value)||0,unit_price:parseFloat(document.getElementById('outs-price').value)||0,process_name:document.getElementById('outs-pn').value,planned_date:document.getElementById('outs-pd').value};
    if(!payload.supplier_id||!payload.material_id||!payload.ordered_qty){showToast('供应商、物料、数量必填','warning');return;}
    fetch(apiBase+'/pm2/outsourcing-orders',{method:'POST',headers:{...authHeaders,'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json()).then(res=>{
        if(!res.success){showToast(res.message,'error');return;}
        btn.closest('[style*=fixed]').remove(); loadPMOutsourcing(); loadPMOverview();
    });
}
function issueOuts(id){
    if(!confirm('确认发料给委外供应商？'))return;
    fetch(apiBase+'/pm2/outsourcing-orders/'+id+'/issue',{method:'PUT',headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){showToast(res.message,'error');return;}
        showToast('委外已发料','success'); loadPMOutsourcing();
    });
}
function receiveOuts(id){
    if(!confirm('确认委外收货入库？'))return;
    fetch(apiBase+'/pm2/outsourcing-orders/'+id+'/receive',{method:'PUT',headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){showToast(res.message,'error');return;}
        showToast('委外已收货入库','success'); loadPMOutsourcing();
    });
}

// ============================================================
// 设备与工作中心
// ============================================================
function pmEquipmentsUI(){
    return `<div style="display:flex;gap:6px;border-bottom:1px solid #e2e8f0;margin-bottom:12px;padding-bottom:8px;">
        <button class="btn pm-eq-subtab active" onclick="pmEqSubTab('equipments',this)" style="padding:3px 10px;font-size:11px;background:#ca8a04;color:#fff;border:none;border-radius:4px;cursor:pointer;">设备台账</button>
        <button class="btn pm-eq-subtab" onclick="pmEqSubTab('workcenters',this)" style="padding:3px 10px;font-size:11px;border:1px solid #cbd5e1;border-radius:4px;cursor:pointer;">工作中心</button>
        <button class="btn pm-eq-subtab" onclick="pmEqSubTab('workshops',this)" style="padding:3px 10px;font-size:11px;border:1px solid #cbd5e1;border-radius:4px;cursor:pointer;">车间管理</button>
    </div>
    <div id="pm-eq-content" style="overflow-x:auto;color:#888;padding:20px;text-align:center;">加载中...</div>`;
}
function pmEqSubTab(sub,btn){
    document.querySelectorAll('.pm-eq-subtab').forEach(b=>{b.style.background='';b.style.color='';b.style.border='1px solid #cbd5e1';});
    btn.style.background='#ca8a04'; btn.style.color='#fff'; btn.style.border='none';
    const el=document.getElementById('pm-eq-content'); if(!el)return;
    el.innerHTML='<div style="color:#888;padding:20px;text-align:center;">加载中...</div>';
    if(sub==='equipments') loadPMEquipments();
    if(sub==='workcenters') loadPMWorkCenters();
    if(sub==='workshops') loadPMWorkshops();
}
function loadPMEquipments(){
    fetch(apiBase+'/pm2/equipments',{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){document.getElementById('pm-eq-content').innerHTML='<div style="color:#dc2626;">加载失败</div>';return;}
        const items=res.data||[];
        if(!items.length){document.getElementById('pm-eq-content').innerHTML='<div style="color:#888;padding:20px;text-align:center;">暂无设备</div>';return;}
        let h='<table class="pm-table"><thead><tr><th>编码</th><th>名称</th><th>型号</th><th>制造商</th><th>车间</th><th>状态</th><th>OEE</th><th>可用率</th><th>性能</th><th>质量率</th><th>上次保养</th><th>下次保养</th></tr></thead><tbody>';
        items.forEach(e=>{
            const stColor={'RUNNING':'#16a34a','IDLE':'#ca8a04','MAINTENANCE':'#dc2626','SCRAPPED':'#64748b'}[e.status]||'#666';
            h+=`<tr>
                <td style="font-weight:600;color:#b45309;">${escapeHtml(e.equipment_code)}</td>
                <td>${escapeHtml(e.equipment_name)}</td>
                <td>${escapeHtml(e.model||'-')}</td>
                <td>${escapeHtml(e.manufacturer||'-')}</td>
                <td>${escapeHtml(e.workshop||'-')}</td>
                <td><span class="pm-badge" style="background:${stColor}1a;color:${stColor};">${escapeHtml(e.status_label)}</span></td>
                <td style="text-align:center;font-weight:600;color:${e.oee>=85?'#16a34a':e.oee>=60?'#ca8a04':'#dc2626'};">${e.oee}%</td>
                <td style="text-align:center;">${e.availability}%</td>
                <td style="text-align:center;">${e.performance}%</td>
                <td style="text-align:center;">${e.quality_rate}%</td>
                <td>${e.last_maintenance||'-'}</td>
                <td>${e.next_maintenance||'-'}</td>
            </tr>`;
        });
        h+='</tbody></table>';
        document.getElementById('pm-eq-content').innerHTML=h;
    }).catch(()=>{document.getElementById('pm-eq-content').innerHTML='<div style="color:#dc2626;">加载失败</div>';});
}
function loadPMWorkCenters(){
    fetch(apiBase+'/pm2/work-centers',{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){document.getElementById('pm-eq-content').innerHTML='<div style="color:#dc2626;">加载失败</div>';return;}
        const items=res.data||[];
        if(!items.length){document.getElementById('pm-eq-content').innerHTML='<div style="color:#888;padding:20px;text-align:center;">暂无工作中心</div>';return;}
        let h='<table class="pm-table"><thead><tr><th>编码</th><th>名称</th><th>类型</th><th>车间</th><th>产能/时</th><th>效率</th><th>人工费率</th><th>机器费率</th><th>状态</th></tr></thead><tbody>';
        items.forEach(w=>{
            const stColor={'ACTIVE':'#16a34a','INACTIVE':'#94a3b8'}[w.status]||'#666';
            h+=`<tr>
                <td style="font-weight:600;color:#b45309;">${escapeHtml(w.code)}</td>
                <td>${escapeHtml(w.name)}</td>
                <td>${escapeHtml(w.type||'-')}</td>
                <td>${escapeHtml(w.workshop_name||'-')}</td>
                <td style="text-align:center;">${w.capacity_per_hour}</td>
                <td style="text-align:center;color:${w.efficiency>=90?'#16a34a':'#ca8a04'};">${w.efficiency}%</td>
                <td style="text-align:right;">¥${w.labor_cost_rate}/时</td>
                <td style="text-align:right;">¥${w.machine_cost_rate}/时</td>
                <td><span class="pm-badge" style="background:${stColor}1a;color:${stColor};">${escapeHtml(w.status_label)}</span></td>
            </tr>`;
        });
        h+='</tbody></table>';
        document.getElementById('pm-eq-content').innerHTML=h;
    }).catch(()=>{document.getElementById('pm-eq-content').innerHTML='<div style="color:#dc2626;">加载失败</div>';});
}
function loadPMWorkshops(){
    fetch(apiBase+'/pm2/workshops',{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){document.getElementById('pm-eq-content').innerHTML='<div style="color:#dc2626;">加载失败</div>';return;}
        const items=res.data||[];
        if(!items.length){document.getElementById('pm-eq-content').innerHTML='<div style="color:#888;padding:20px;text-align:center;">暂无车间</div>';return;}
        let h='<table class="pm-table"><thead><tr><th>编码</th><th>名称</th><th>负责人</th><th>位置</th><th>状态</th></tr></thead><tbody>';
        items.forEach(w=>{
            const stColor={'ACTIVE':'#16a34a','INACTIVE':'#94a3b8'}[w.status]||'#666';
            h+=`<tr><td style="font-weight:600;color:#b45309;">${escapeHtml(w.code)}</td><td>${escapeHtml(w.name)}</td><td>${escapeHtml(w.manager||'-')}</td><td>${escapeHtml(w.location||'-')}</td><td><span class="pm-badge" style="background:${stColor}1a;color:${stColor};">${escapeHtml(w.status_label)}</span></td></tr>`;
        });
        h+='</tbody></table>';
        document.getElementById('pm-eq-content').innerHTML=h;
    }).catch(()=>{document.getElementById('pm-eq-content').innerHTML='<div style="color:#dc2626;">加载失败</div>';});
}

// ============================================================
// 质量检验管理
// ============================================================
function pmInspectionsUI(){
    return `<div style="margin-bottom:12px;">
        <h3 style="margin:0 0 8px;color:#b45309;font-size:14px;">质量检验记录</h3>
    </div>
    <div id="pm-qi-list" style="overflow-x:auto;color:#888;padding:20px;text-align:center;">加载中...</div>`;
}
function loadPMInspections(){
    fetch(apiBase+'/pm2/inspections',{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){document.getElementById('pm-qi-list').innerHTML='<div style="color:#dc2626;">加载失败</div>';return;}
        const items=res.data||[];
        if(!items.length){document.getElementById('pm-qi-list').innerHTML='<div style="color:#888;padding:20px;text-align:center;">暂无质检记录</div>';return;}
        let h='<table class="pm-table"><thead><tr><th>检验单号</th><th>来源类型</th><th>来源ID</th><th>检验日期</th><th>检验员</th><th>结果</th><th>备注</th></tr></thead><tbody>';
        items.forEach(q=>{
            const stColor={'PASSED':'#16a34a','FAILED':'#dc2626','PENDING':'#ca8a04','IN_PROGRESS':'#2563eb'}[q.status]||'#666';
            h+=`<tr>
                <td style="font-weight:600;color:#b45309;">${escapeHtml(q.inspection_no)}</td>
                <td>${escapeHtml(q.source_type)}</td>
                <td style="text-align:center;">${q.source_id||'-'}</td>
                <td>${q.inspection_date||'-'}</td>
                <td>${escapeHtml(q.inspector)}</td>
                <td><span class="pm-badge" style="background:${stColor}1a;color:${stColor};">${escapeHtml(q.status_label)}</span></td>
                <td>${escapeHtml(q.remarks||'')}</td>
            </tr>`;
        });
        h+='</tbody></table>';
        document.getElementById('pm-qi-list').innerHTML=h;
    }).catch(()=>{document.getElementById('pm-qi-list').innerHTML='<div style="color:#dc2626;">加载失败</div>';});
}

// ============================================================
// 概览统计
// ============================================================
function loadPMOverview(){
    fetch(apiBase+'/pm2/overview',{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success)return; const d=res.data||{};
        document.getElementById('pm-stat-wo').textContent=d.active_work_orders||0;
        document.getElementById('pm-stat-plan').textContent=d.plan_count||0;
        document.getElementById('pm-stat-mrp').textContent=d.mrp_count||0;
        document.getElementById('pm-stat-disp').textContent=d.dispatch_count||0;
        document.getElementById('pm-stat-rt').textContent=d.routing_count||0;
        document.getElementById('pm-stat-rp').textContent=d.req_pending||0;
        document.getElementById('pm-stat-wr').textContent=d.work_report_count||0;
        document.getElementById('pm-stat-outs').textContent=d.outsourcing_count||0;
        document.getElementById('pm-stat-eq').textContent=d.equipment_count||0;
    }).catch(e=>console.error(e));
}

// ===== 工艺路线 =====
function pmRoutingsUI(){
    return `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <span style="font-size:13px;color:#475569;font-weight:600;">工艺路线管理（产品加工工序）</span>
        <button class="btn btn-primary" style="padding:5px 12px;font-size:12px;" onclick="pmRoutingForm()">➕ 新增工艺路线</button>
    </div><div id="pm-rt-list" style="overflow-x:auto;"><div style="color:#888;padding:20px;text-align:center;">加载中...</div></div>`;
}
function loadPMRoutings(){
    fetch(apiBase+'/pm2/routings',{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){document.getElementById('pm-rt-list').innerHTML='<div style="color:#c0392b;padding:16px;">'+escapeHtml(res.message)+'</div>';return;}
        const items=(res.data&&res.data.items)||[];
        if(!items.length){document.getElementById('pm-rt-list').innerHTML='<div style="color:#888;padding:20px;text-align:center;">暂无工艺路线</div>';return;}
        let h='<table class="pm-table"><thead><tr><th>路线名称</th><th>版本</th><th>产品编码</th><th>产品名称</th><th>工序数</th><th>状态</th><th>操作</th></tr></thead><tbody>';
        items.forEach(r=>{
            h+=`<tr><td style="font-weight:600;color:#b45309;">${escapeHtml(r.name)}</td><td>${escapeHtml(r.version)}</td><td>${escapeHtml(r.product_code||'-')}</td><td>${escapeHtml(r.product_name||'-')}</td><td style="text-align:center;">${r.operation_count}道</td><td>${escapeHtml(r.status_label)}</td><td><button class="btn" style="padding:2px 8px;font-size:11px;border:1px solid #cbd5e1;border-radius:4px;cursor:pointer;" onclick="viewPMRoutingOps(${r.id},'${escapeHtml(r.name)}')">查看工序</button> <button class="btn" style="padding:2px 8px;font-size:11px;color:#dc2626;border:1px solid #dc2626;border-radius:4px;cursor:pointer;" onclick="deletePMRouting(${r.id})">删除</button></td></tr>`;
        });
        h+='</tbody></table>'; document.getElementById('pm-rt-list').innerHTML=h;
    });
}
function pmRoutingForm(){
    const m=document.createElement('div'); m.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    m.innerHTML=`<div style="background:#fff;border-radius:10px;padding:20px;width:420px;max-width:92vw;max-height:85vh;overflow:auto;">
        <h3 style="margin:0 0 16px;color:#b45309;">新增工艺路线</h3>
        <div style="display:grid;gap:10px;font-size:12px;">
            <div><label>路线名称 *</label><input id="rt-name" placeholder="如 电路板组装工艺" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                <div><label>产品ID</label><input id="rt-pid" type="number" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
                <div><label>版本</label><input id="rt-ver" value="V1" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            </div>
            <div style="border-top:1px solid #e2e8f0;padding-top:10px;margin-top:6px;">
                <label style="font-weight:600;">工序列表（至少1道）</label>
                <div id="rt-ops" style="margin-top:6px;"></div>
                <button class="btn" style="padding:4px 10px;font-size:11px;margin-top:6px;border:1px solid #cbd5e1;border-radius:4px;cursor:pointer;" onclick="addPMOp()">➕ 添加工序</button>
            </div>
        </div>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
            <button class="btn" style="padding:6px 14px;font-size:12px;border:1px solid #cbd5e1;border-radius:6px;cursor:pointer;" onclick="this.closest('[style*=fixed]').remove()">取消</button>
            <button class="btn btn-primary" style="padding:6px 14px;font-size:12px;" onclick="savePMRouting(this)">保存</button>
        </div></div>`;
    document.body.appendChild(m); addPMOp();
}
function addPMOp(){
    const c=document.getElementById('rt-ops');
    const idx=c.children.length+1;
    const d=document.createElement('div'); d.style.cssText='border:1px solid #e2e8f0;border-radius:6px;padding:8px;margin-top:6px;font-size:11px;';
    d.innerHTML=`<div style="display:flex;justify-content:space-between;"><b>工序 ${idx}</b><button style="color:#dc2626;cursor:pointer;background:none;border:none;" onclick="this.parentElement.parentElement.remove()">✕</button></div>
        <div style="display:grid;grid-template-columns:60px 1fr 80px 80px;gap:4px;margin-top:4px;">
            <input class="op-seq" type="number" value="${idx}" placeholder="序号" style="padding:4px;border:1px solid #cbd5e1;border-radius:4px;">
            <input class="op-name" placeholder="工序名称" style="padding:4px;border:1px solid #cbd5e1;border-radius:4px;">
            <input class="op-time" type="number" placeholder="工时(分)" style="padding:4px;border:1px solid #cbd5e1;border-radius:4px;">
            <input class="op-eq" placeholder="设备" style="padding:4px;border:1px solid #cbd5e1;border-radius:4px;">
        </div>`;
    c.appendChild(d);
}
function savePMRouting(btn){
    const ops=[]; document.querySelectorAll('#rt-ops > div').forEach(d=>{
        const seq=d.querySelector('.op-seq').value, name=d.querySelector('.op-name').value, time=d.querySelector('.op-time').value, eq=d.querySelector('.op-eq').value;
        if(name) ops.push({sequence:parseInt(seq)||1,name,standard_time:parseFloat(time)||0,equipment:eq});
    });
    if(!ops.length){showToast('请至少添加一道工序','warning');return;}
    const payload={name:document.getElementById('rt-name').value.trim(),product_id:parseInt(document.getElementById('rt-pid').value)||null,version:document.getElementById('rt-ver').value||'V1',operations:ops};
    if(!payload.name){showToast('请输入路线名称','warning');return;}
    fetch(apiBase+'/pm2/routings',{method:'POST',headers:{...authHeaders,'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json()).then(res=>{ if(!res.success){showToast(res.message,'error');return;} btn.closest('[style*=fixed]').remove(); loadPMRoutings(); loadPMOverview(); });
}
function deletePMRouting(id){ if(!confirm('确认删除该工艺路线及其工序？'))return; fetch(apiBase+'/pm2/routings/'+id,{method:'DELETE',headers:authHeaders}).then(r=>r.json()).then(res=>{ if(!res.success){showToast(res.message,'error');return;} loadPMRoutings(); loadPMOverview(); }); }
function viewPMRoutingOps(id,name){
    fetch(apiBase+'/pm2/routings/'+id+'/operations',{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){showToast(res.message,'error');return;}
        const items=(res.data&&res.data.items)||[];
        const m=document.createElement('div'); m.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
        let rows=''; items.forEach(o=>{ rows+=`<tr><td style="text-align:center;font-weight:600;">${o.sequence}</td><td style="font-weight:600;color:#b45309;">${escapeHtml(o.name)}</td><td>${escapeHtml(o.description||'-')}</td><td style="text-align:right;">${o.standard_time}分</td><td>${escapeHtml(o.equipment||'-')}</td><td>${escapeHtml(o.work_center||'-')}</td></tr>`; });
        m.innerHTML=`<div style="background:#fff;border-radius:10px;padding:20px;width:560px;max-width:92vw;max-height:85vh;overflow:auto;">
            <h3 style="margin:0 0 12px;color:#b45309;">🛠️ ${escapeHtml(name)} - 工序列表</h3>
            <table class="pm-table"><thead><tr><th>序号</th><th>工序名称</th><th>描述</th><th>标准工时</th><th>设备</th><th>工作中心</th></tr></thead><tbody>${rows}</tbody></table>
            <div style="text-align:right;margin-top:12px;"><button class="btn" style="padding:6px 14px;font-size:12px;border:1px solid #cbd5e1;border-radius:6px;cursor:pointer;" onclick="this.closest('[style*=fixed]').remove()">关闭</button></div></div>`;
        document.body.appendChild(m);
    });
}

// ===== 领料 =====
function pmReqUI(){
    return `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <span style="font-size:13px;color:#475569;font-weight:600;">生产领料单（审批→发料→扣减库存）</span>
        <button class="btn btn-primary" style="padding:5px 12px;font-size:12px;" onclick="pmReqForm()">➕ 新增领料单</button>
    </div><div id="pm-req-list" style="overflow-x:auto;"><div style="color:#888;padding:20px;text-align:center;">加载中...</div></div>`;
}
function loadPMReqs(){
    fetch(apiBase+'/pm2/requisitions',{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){document.getElementById('pm-req-list').innerHTML='<div style="color:#c0392b;padding:16px;">'+escapeHtml(res.message)+'</div>';return;}
        const items=(res.data&&res.data.items)||[];
        if(!items.length){document.getElementById('pm-req-list').innerHTML='<div style="color:#888;padding:20px;text-align:center;">暂无领料单</div>';return;}
        let h='<table class="pm-table"><thead><tr><th>领料单号</th><th>工单号</th><th>领料日期</th><th>状态</th><th>操作</th></tr></thead><tbody>';
        items.forEach(r=>{
            let ops='-';
            if(r.status==='PENDING') ops=`<button class="btn" style="padding:2px 8px;font-size:11px;color:#16a34a;border:1px solid #16a34a;border-radius:4px;cursor:pointer;" onclick="approvePMReq(${r.id})">审批</button>`;
            else if(r.status==='APPROVED') ops=`<button class="btn" style="padding:2px 8px;font-size:11px;color:#dc2626;border:1px solid #dc2626;border-radius:4px;cursor:pointer;" onclick="issuePMReq(${r.id})">发料</button>`;
            h+=`<tr><td style="font-weight:600;color:#b45309;">${escapeHtml(r.requisition_no)}</td><td>${escapeHtml(r.work_order_no||r.work_order_id||'-')}</td><td>${escapeHtml(r.requisition_date)}</td><td>${escapeHtml(r.status_label)}</td><td>${ops}</td></tr>`;
        });
        h+='</tbody></table>'; document.getElementById('pm-req-list').innerHTML=h;
    });
}
function pmReqForm(){
    const m=document.createElement('div'); m.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    m.innerHTML=`<div style="background:#fff;border-radius:10px;padding:20px;width:400px;max-width:92vw;">
        <h3 style="margin:0 0 16px;color:#b45309;">新增领料单</h3>
        <div style="display:grid;gap:10px;font-size:12px;">
            <div><label>工单ID *</label><input id="req-woid" type="number" placeholder="生产工单ID" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div><label>备注</label><input id="req-rmk" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div style="color:#94a3b8;font-size:11px;">提示：领料单创建后可在审批通过后发料扣减库存</div>
        </div>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
            <button class="btn" style="padding:6px 14px;font-size:12px;border:1px solid #cbd5e1;border-radius:6px;cursor:pointer;" onclick="this.closest('[style*=fixed]').remove()">取消</button>
            <button class="btn btn-primary" style="padding:6px 14px;font-size:12px;" onclick="savePMReq(this)">保存</button>
        </div></div>`;
    document.body.appendChild(m);
}
function savePMReq(btn){
    const payload={work_order_id:parseInt(document.getElementById('req-woid').value)||null,remark:document.getElementById('req-rmk').value,items:[]};
    if(!payload.work_order_id){showToast('请输入工单ID','warning');return;}
    fetch(apiBase+'/pm2/requisitions',{method:'POST',headers:{...authHeaders,'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json()).then(res=>{ if(!res.success){showToast(res.message,'error');return;} btn.closest('[style*=fixed]').remove(); loadPMReqs(); loadPMOverview(); });
}
function approvePMReq(id){ if(!confirm('确认审批通过？'))return; fetch(apiBase+'/pm2/requisitions/'+id+'/approve',{method:'PUT',headers:authHeaders}).then(r=>r.json()).then(res=>{ if(!res.success){showToast(res.message,'error');return;} loadPMReqs(); loadPMOverview(); }); }
function issuePMReq(id){ if(!confirm('确认发料？将扣减对应物料库存。'))return; fetch(apiBase+'/pm2/requisitions/'+id+'/issue',{method:'PUT',headers:authHeaders}).then(r=>r.json()).then(res=>{ if(!res.success){showToast(res.message,'error');return;} loadPMReqs(); loadPMOverview(); }); }

// ===== 报工 =====
function pmReportsUI(){
    return `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <span style="font-size:13px;color:#475569;font-weight:600;">工序报工单（完工/合格/废品/工时）</span>
        <button class="btn btn-primary" style="padding:5px 12px;font-size:12px;" onclick="pmReportForm()">➕ 新增报工单</button>
    </div><div id="pm-wr-list" style="overflow-x:auto;"><div style="color:#888;padding:20px;text-align:center;">加载中...</div></div>`;
}
function loadPMReports(){
    fetch(apiBase+'/pm2/work-reports',{headers:authHeaders}).then(r=>r.json()).then(res=>{
        if(!res.success){document.getElementById('pm-wr-list').innerHTML='<div style="color:#c0392b;padding:16px;">'+escapeHtml(res.message)+'</div>';return;}
        const items=(res.data&&res.data.items)||[];
        if(!items.length){document.getElementById('pm-wr-list').innerHTML='<div style="color:#888;padding:20px;text-align:center;">暂无报工单</div>';return;}
        let h='<table class="pm-table"><thead><tr><th>报工单号</th><th>工单号</th><th>工人</th><th>报工日期</th><th>完工</th><th>合格</th><th>废品</th><th>合格率</th><th>实际工时</th></tr></thead><tbody>';
        items.forEach(w=>{
            const rate=w.completed_qty?((w.qualified_qty/w.completed_qty)*100).toFixed(1):'0.0';
            h+=`<tr><td style="font-weight:600;color:#b45309;">${escapeHtml(w.report_no)}</td><td>${escapeHtml(w.work_order_no||w.work_order_id||'-')}</td><td>${escapeHtml(w.worker)}</td><td>${escapeHtml(w.report_date)}</td><td style="text-align:center;">${w.completed_qty}</td><td style="text-align:center;color:#16a34a;">${w.qualified_qty}</td><td style="text-align:center;color:#dc2626;">${w.defective_qty}</td><td style="text-align:center;font-weight:600;color:${parseFloat(rate)>=95?'#16a34a':'#ca8a04'};">${rate}%</td><td style="text-align:right;">${w.actual_time}分</td></tr>`;
        });
        h+='</tbody></table>'; document.getElementById('pm-wr-list').innerHTML=h;
    });
}
function pmReportForm(){
    const m=document.createElement('div'); m.style.cssText='position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    m.innerHTML=`<div style="background:#fff;border-radius:10px;padding:20px;width:420px;max-width:92vw;">
        <h3 style="margin:0 0 16px;color:#b45309;">新增报工单</h3>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:12px;">
            <div style="grid-column:1/3;"><label>工单ID *</label><input id="wr-woid" type="number" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div><label>工人 *</label><input id="wr-worker" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div><label>报工日期</label><input id="wr-date" type="date" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div><label>完工数量</label><input id="wr-cq" type="number" value="0" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div><label>合格数量</label><input id="wr-qq" type="number" value="0" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div><label>废品数量</label><input id="wr-dq" type="number" value="0" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
            <div><label>实际工时(分)</label><input id="wr-at" type="number" value="0" style="width:100%;padding:6px;border:1px solid #cbd5e1;border-radius:6px;margin-top:3px;"></div>
        </div>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px;">
            <button class="btn" style="padding:6px 14px;font-size:12px;border:1px solid #cbd5e1;border-radius:6px;cursor:pointer;" onclick="this.closest('[style*=fixed]').remove()">取消</button>
            <button class="btn btn-primary" style="padding:6px 14px;font-size:12px;" onclick="savePMReport(this)">保存</button>
        </div></div>`;
    document.body.appendChild(m);
}
function savePMReport(btn){
    const payload={work_order_id:parseInt(document.getElementById('wr-woid').value)||null,worker:document.getElementById('wr-worker').value,report_date:document.getElementById('wr-date').value,completed_qty:parseInt(document.getElementById('wr-cq').value)||0,qualified_qty:parseInt(document.getElementById('wr-qq').value)||0,defective_qty:parseInt(document.getElementById('wr-dq').value)||0,actual_time:parseFloat(document.getElementById('wr-at').value)||0};
    if(!payload.work_order_id||!payload.worker){showToast('工单ID和工人必填','warning');return;}
    fetch(apiBase+'/pm2/work-reports',{method:'POST',headers:{...authHeaders,'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json()).then(res=>{ if(!res.success){showToast(res.message,'error');return;} btn.closest('[style*=fixed]').remove(); loadPMReports(); loadPMOverview(); });
}

window._renderProductionV2Impl=function(){ const html=_renderProductionV2Impl(); setTimeout(loadPMOverview,100); return html; };
