// =============== 采购优化与选型门 前端 ===============
const OPT_API = '/api/v1/opt';

// ===== 主渲染函数 =====
function renderOptimization() {
    const html = `
    <div class="eng-container">
        <div class="eng-tabs">
            <button class="eng-tab active" onclick="showOptTab(event,'eoq')">🧮 EOQ平衡引擎</button>
            <button class="eng-tab" onclick="showOptTab(event,'roi')">📊 ROI看板</button>
            <button class="eng-tab" onclick="showOptTab(event,'tracking')">📍 到料跟踪</button>
            <button class="eng-tab" onclick="showOptTab(event,'picking')">📤 建档发料</button>
            <button class="eng-tab" onclick="showOptTab(event,'governance')">🔧 物料治理</button>
            <button class="eng-tab" onclick="showOptTab(event,'checkpoints')">🚦 流程卡点</button>
            <button class="eng-tab" onclick="showOptTab(event,'gate')">🏢 选型门</button>
        </div>
        <div id="optContent" style="padding:20px;"></div>
    </div>`;
    document.getElementById('mainContent').innerHTML = html;
    loadOptTab('eoq');
}

function showOptTab(ev, tab) {
    document.querySelectorAll('.eng-tab').forEach(b => b.classList.remove('active'));
    if (ev) ev.target.classList.add('active');
    loadOptTab(tab);
}

function loadOptTab(tab) {
    const el = document.getElementById('optContent');
    switch(tab) {
        case 'eoq': renderEOQ(el); break;
        case 'roi': renderROI(el); break;
        case 'tracking': renderTracking(el); break;
        case 'picking': renderPicking(el); break;
        case 'governance': renderGovernance(el); break;
        case 'checkpoints': renderCheckpoints(el); break;
        case 'gate': renderGate(el); break;
    }
}

// ===== 1. EOQ平衡引擎 =====
function renderEOQ(el) {
    el.innerHTML = `
    <h3 style="color:#1a237e;margin-bottom:16px;">🧮 EOQ采购-库存平衡优化引擎</h3>
    <div style="background:#fff8e1;border:2px dashed #f9a825;border-radius:10px;padding:16px;margin-bottom:16px;">
        <p style="font-size:13px;color:#e65100;font-weight:600;">🎯 核心公式：ROI = 库存周转率 × 利润率</p>
        <p style="font-size:12px;color:#666;margin-top:4px;">采购大批量→单价低→利润率↑，但交期长→资金占用多→周转率↓。系统帮你找ROI最大化的平衡点。</p>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
        <div>
            <h4 style="margin-bottom:12px;color:#1565c0;">输入参数</h4>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                <label>年需求量 D (件/年)<input type="number" id="eoq_D" value="5000" class="opt-input"></label>
                <label>单次订货成本 S (元/次)<input type="number" id="eoq_S" value="200" class="opt-input"></label>
                <label>采购单价 C (元/件)<input type="number" id="eoq_C" value="50" class="opt-input"></label>
                <label>资金成本率 i (%)<input type="number" id="eoq_i" value="8" class="opt-input"></label>
                <label>供应商交期 L (天)<input type="number" id="eoq_L" value="7" class="opt-input"></label>
                <label>仓储费 H (元/件·年)<input type="number" id="eoq_H" value="5" class="opt-input"></label>
                <label>销售单价 (元/件)<input type="number" id="eoq_price" value="60" class="opt-input"></label>
                <label>MOQ最小起订量<input type="number" id="eoq_moq" value="0" class="opt-input"></label>
            </div>
            <button onclick="calcEOQ()" style="margin-top:12px;background:#1565c0;color:#fff;border:none;padding:10px 24px;border-radius:8px;cursor:pointer;font-size:14px;">🧮 计算最优采购批量</button>
        </div>
        <div id="eoqResult" style="background:#f5f7fa;border-radius:10px;padding:16px;">
            <p style="color:#999;text-align:center;padding:40px 0;">点击计算按钮查看结果</p>
        </div>
    </div>
    <style>.opt-input{width:100%;padding:6px 8px;border:1px solid #ddd;border-radius:6px;margin-top:4px;font-size:13px;}label{font-size:12px;color:#555;}</style>
    `;
}

async function calcEOQ() {
    const data = {
        annual_demand: parseFloat(document.getElementById('eoq_D').value),
        order_cost: parseFloat(document.getElementById('eoq_S').value),
        unit_cost: parseFloat(document.getElementById('eoq_C').value),
        holding_rate: parseFloat(document.getElementById('eoq_i').value) / 100,
        lead_time_days: parseFloat(document.getElementById('eoq_L').value),
        warehouse_fee: parseFloat(document.getElementById('eoq_H').value),
        sell_price: parseFloat(document.getElementById('eoq_price').value),
        moq: parseFloat(document.getElementById('eoq_moq').value),
        service_level: 0.95,
    };
    try {
        const res = await fetch(`${OPT_API}/eoq/calculate`, {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify(data)
        });
        const r = await res.json();
        if (r.success) {
            const d = r.data.results;
            const f = r.data.formulas;
            document.getElementById('eoqResult').innerHTML = `
            <h4 style="color:#2e7d32;margin-bottom:12px;">✅ 计算结果</h4>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                <div class="opt-rcard"><span class="opt-rl">最优批量 Q*</span><span class="opt-rv">${d.eoq} 件</span></div>
                <div class="opt-rcard"><span class="opt-rl">修正持有成本 H'</span><span class="opt-rv">${d.H_prime} 元</span></div>
                <div class="opt-rcard"><span class="opt-rl">总成本 TC</span><span class="opt-rv">${d.total_cost} 元</span></div>
                <div class="opt-rcard"><span class="opt-rl">年订货次数</span><span class="opt-rv">${d.num_orders} 次</span></div>
                <div class="opt-rcard"><span class="opt-rl">安全库存 SS</span><span class="opt-rv">${d.safety_stock} 件</span></div>
                <div class="opt-rcard"><span class="opt-rl">再订货点 ROP</span><span class="opt-rv">${d.rop} 件</span></div>
                <div class="opt-rcard"><span class="opt-rl">资金占用</span><span class="opt-rv">${d.capital_occupation} 元</span></div>
                <div class="opt-rcard"><span class="opt-rl">库存周转率</span><span class="opt-rv">${d.turnover} 次/年</span></div>
                <div class="opt-rcard"><span class="opt-rl">利润率</span><span class="opt-rv">${d.profit_rate}%</span></div>
                <div class="opt-rcard" style="background:#e8f5e9;border-color:#2e7d32;"><span class="opt-rl" style="color:#1b5e20;">🎯 ROI</span><span class="opt-rv" style="color:#2e7d32;">${d.roi}</span></div>
            </div>
            <div style="margin-top:12px;font-size:11px;color:#888;line-height:1.8;">
                <p>${f.H_prime}</p><p>${f.eoq}</p><p>${f.tc}</p><p style="font-weight:700;color:#2e7d32;">${f.roi}</p>
            </div>
            ${d.moq_adjusted ? '<p style="color:#e65100;font-size:12px;margin-top:8px;">⚠ 批量已被MOQ调整</p>' : ''}
            ${d.capacity_adjusted ? '<p style="color:#c62828;font-size:12px;margin-top:8px;">⚠ 批量已被仓库容量约束调整</p>' : ''}
            `;
            // Add styles
            if (!document.getElementById('opt-rstyle')) {
                const s = document.createElement('style');
                s.id = 'opt-rstyle';
                s.textContent = `.opt-rcard{background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:10px;text-align:center;}.opt-rl{display:block;font-size:11px;color:#666;margin-bottom:4px;}.opt-rv{display:block;font-size:18px;font-weight:700;color:#1a237e;}`;
                document.head.appendChild(s);
            }
        }
    } catch(e) {
        document.getElementById('eoqResult').innerHTML = `<p style="color:#c62828;">计算失败: ${e.message}</p>`;
    }
}

// ===== 2. ROI看板 =====
async function renderROI(el) {
    el.innerHTML = `<h3 style="color:#1a237e;margin-bottom:16px;">📊 投资回报率（ROI）看板</h3><div id="roiContent"><p style="color:#999;">加载中...</p></div>`;
    try {
        const res = await fetch(`${OPT_API}/roi/dashboard`);
        const r = await res.json();
        if (r.success) {
            const s = r.data.summary;
            const items = r.data.items;
            let html = `
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:20px;">
                <div style="background:linear-gradient(135deg,#1565c0,#1976d2);color:#fff;border-radius:12px;padding:20px;text-align:center;">
                    <div style="font-size:12px;opacity:0.8;">库存周转率</div>
                    <div style="font-size:32px;font-weight:700;">${s.overall_turnover}</div>
                    <div style="font-size:11px;opacity:0.6;">次/年</div>
                </div>
                <div style="background:linear-gradient(135deg,#e65100,#f57c00);color:#fff;border-radius:12px;padding:20px;text-align:center;">
                    <div style="font-size:12px;opacity:0.8;">平均利润率</div>
                    <div style="font-size:32px;font-weight:700;">${s.overall_profit_rate}%</div>
                    <div style="font-size:11px;opacity:0.6;">毛利率</div>
                </div>
                <div style="background:linear-gradient(135deg,#2e7d32,#43a047);color:#fff;border-radius:12px;padding:20px;text-align:center;border:2px solid #ffc107;">
                    <div style="font-size:12px;opacity:0.8;">🎯 投资回报率 ROI</div>
                    <div style="font-size:32px;font-weight:700;color:#ffc107;">${s.overall_roi}</div>
                    <div style="font-size:11px;opacity:0.6;">每元库存投资赚回</div>
                </div>
            </div>
            <table style="width:100%;border-collapse:collapse;font-size:12px;">
                <thead><tr style="background:#1a237e;color:#fff;">
                    <th style="padding:8px;text-align:left;">物料编码</th>
                    <th style="padding:8px;text-align:left;">物料名称</th>
                    <th style="padding:8px;text-align:right;">出库金额</th>
                    <th style="padding:8px;text-align:right;">平均库存</th>
                    <th style="padding:8px;text-align:right;">周转率</th>
                    <th style="padding:8px;text-align:right;">利润率</th>
                    <th style="padding:8px;text-align:right;">ROI</th>
                    <th style="padding:8px;text-align:center;">等级</th>
                </tr></thead>
                <tbody>`;
            items.forEach((item, i) => {
                const bg = i % 2 ? '#f8fafc' : '#fff';
                const roiColor = item.roi >= 3 ? '#2e7d32' : (item.roi >= 1 ? '#e65100' : '#c62828');
                html += `<tr style="background:${bg};border-bottom:1px solid #e0e0e0;">
                    <td style="padding:6px 8px;">${item.material_code}</td>
                    <td style="padding:6px 8px;">${item.material_name}</td>
                    <td style="padding:6px 8px;text-align:right;">${item.outbound_value.toLocaleString()}</td>
                    <td style="padding:6px 8px;text-align:right;">${item.avg_inventory_value.toLocaleString()}</td>
                    <td style="padding:6px 8px;text-align:right;">${item.turnover}</td>
                    <td style="padding:6px 8px;text-align:right;">${item.profit_rate}%</td>
                    <td style="padding:6px 8px;text-align:right;font-weight:700;color:${roiColor};">${item.roi}</td>
                    <td style="padding:6px 8px;text-align:center;">${item.roi_level}</td>
                </tr>`;
            });
            html += '</tbody></table>';
            document.getElementById('roiContent').innerHTML = html;
        }
    } catch(e) {
        document.getElementById('roiContent').innerHTML = `<p style="color:#c62828;">加载失败: ${e.message}</p>`;
    }
}

// ===== 3. 到料跟踪看板 =====
async function renderTracking(el) {
    el.innerHTML = `<h3 style="color:#1a237e;margin-bottom:16px;">📍 项目物料到料跟踪看板</h3><div id="trackContent"><p style="color:#999;">加载中...</p></div>`;
    try {
        const res = await fetch(`${OPT_API}/arrival-tracking`);
        const r = await res.json();
        if (r.success) {
            const s = r.data;
            let html = `
            <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:16px;">
                <div style="background:#e3f2fd;border-radius:8px;padding:12px;text-align:center;"><div style="font-size:11px;color:#666;">总物料</div><div style="font-size:20px;font-weight:700;color:#1565c0;">${s.total}</div></div>
                <div style="background:#e8f5e9;border-radius:8px;padding:12px;text-align:center;"><div style="font-size:11px;color:#666;">已到齐</div><div style="font-size:20px;font-weight:700;color:#2e7d32;">${s.arrived}</div></div>
                <div style="background:#fff3e0;border-radius:8px;padding:12px;text-align:center;"><div style="font-size:11px;color:#666;">部分到料</div><div style="font-size:20px;font-weight:700;color:#e65100;">${s.partial}</div></div>
                <div style="background:#ffebee;border-radius:8px;padding:12px;text-align:center;"><div style="font-size:11px;color:#666;">未到料</div><div style="font-size:20px;font-weight:700;color:#c62828;">${s.not_arrived}</div></div>
                <div style="background:#fce4ec;border-radius:8px;padding:12px;text-align:center;"><div style="font-size:11px;color:#666;">关键件短缺</div><div style="font-size:20px;font-weight:700;color:#c62828;">${s.critical_short}</div></div>
            </div>
            <table style="width:100%;border-collapse:collapse;font-size:12px;">
                <thead><tr style="background:#1a237e;color:#fff;">
                    <th style="padding:8px;text-align:left;">采购单</th>
                    <th style="padding:8px;text-align:left;">物料编码</th>
                    <th style="padding:8px;text-align:left;">物料名称</th>
                    <th style="padding:8px;text-align:right;">订单量</th>
                    <th style="padding:8px;text-align:right;">已到料</th>
                    <th style="padding:8px;text-align:right;">到料率</th>
                    <th style="padding:8px;text-align:center;">关键件</th>
                    <th style="padding:8px;text-align:center;">状态</th>
                </tr></thead><tbody>`;
            s.forEach((item, i) => {
                const statusColor = item.status === '已到齐' ? '#2e7d32' : (item.status === '部分到料' ? '#e65100' : '#c62828');
                html += `<tr style="background:${i%2?'#f8fafc':'#fff'};border-bottom:1px solid #e0e0e0;">
                    <td style="padding:6px 8px;">${item.po_no}</td>
                    <td style="padding:6px 8px;">${item.material_code}</td>
                    <td style="padding:6px 8px;">${item.material_name}</td>
                    <td style="padding:6px 8px;text-align:right;">${item.ordered_qty}</td>
                    <td style="padding:6px 8px;text-align:right;">${item.received_qty}</td>
                    <td style="padding:6px 8px;text-align:right;font-weight:600;">${item.arrival_rate}%</td>
                    <td style="padding:6px 8px;text-align:center;">${item.is_critical ? '⭐是' : '-'}</td>
                    <td style="padding:6px 8px;text-align:center;color:${statusColor};font-weight:600;">${item.status}</td>
                </tr>`;
            });
            html += '</tbody></table>';
            document.getElementById('trackContent').innerHTML = html;
        }
    } catch(e) {
        document.getElementById('trackContent').innerHTML = `<p style="color:#c62828;">加载失败: ${e.message}</p>`;
    }
}

// ===== 4. 建档发料 =====
async function renderPicking(el) {
    el.innerHTML = `<h3 style="color:#1a237e;margin-bottom:16px;">📤 建档发料 —— 4种领料模式配置</h3><div id="pickContent"><p style="color:#999;">加载中...</p></div>`;
    try {
        const [modesRes, matsRes] = await Promise.all([
            fetch(`${OPT_API}/picking-modes`),
            fetch(`${OPT_API}/materials/picking-modes`)
        ]);
        const modes = await modesRes.json();
        const mats = await matsRes.json();
        if (modes.success && mats.success) {
            let modeHtml = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">';
            modes.data.forEach(m => {
                modeHtml += `<div style="background:#fff;border:2px solid #e0e0e0;border-radius:10px;padding:14px;text-align:center;${m.default?'border-color:#2e7d32;':''}">
                    <div style="font-size:24px;">${m.icon}</div>
                    <div style="font-size:14px;font-weight:700;margin:4px 0;">${m.name}</div>
                    <div style="font-size:11px;color:#666;">${m.desc}</div>
                    ${m.default?'<span style="font-size:10px;background:#2e7d32;color:#fff;padding:2px 8px;border-radius:8px;">默认</span>':''}
                </div>`;
            });
            modeHtml += '</div>';

            let tableHtml = `<table style="width:100%;border-collapse:collapse;font-size:12px;">
                <thead><tr style="background:#1a237e;color:#fff;">
                    <th style="padding:8px;text-align:left;">物料编码</th>
                    <th style="padding:8px;text-align:left;">物料名称</th>
                    <th style="padding:8px;text-align:left;">物料类型</th>
                    <th style="padding:8px;text-align:center;">领料模式</th>
                    <th style="padding:8px;text-align:center;">操作</th>
                </tr></thead><tbody>`;
            mats.data.forEach((m, i) => {
                tableHtml += `<tr style="background:${i%2?'#f8fafc':'#fff'};border-bottom:1px solid #e0e0e0;">
                    <td style="padding:6px 8px;">${m.material_code}</td>
                    <td style="padding:6px 8px;">${m.material_name}</td>
                    <td style="padding:6px 8px;">${m.material_type}</td>
                    <td style="padding:6px 8px;text-align:center;">${m.picking_mode_icon} ${m.picking_mode_name}</td>
                    <td style="padding:6px 8px;text-align:center;">
                        <select onchange="setPickingMode(${m.material_id}, this.value)" style="padding:4px;border-radius:6px;border:1px solid #ddd;font-size:11px;">
                            <option value="1" ${m.picking_mode==1?'selected':''}>📋 按单领料</option>
                            <option value="2" ${m.picking_mode==2?'selected':''}>🔧 配料制</option>
                            <option value="3" ${m.picking_mode==3?'selected':''}>🏭 集中领料</option>
                            <option value="4" ${m.picking_mode==4?'selected':''}>⬇️ 倒冲领料</option>
                        </select>
                    </td>
                </tr>`;
            });
            tableHtml += '</tbody></table>';
            document.getElementById('pickContent').innerHTML = modeHtml + tableHtml;
        }
    } catch(e) {
        document.getElementById('pickContent').innerHTML = `<p style="color:#c62828;">加载失败: ${e.message}</p>`;
    }
}

async function setPickingMode(materialId, mode) {
    try {
        const res = await fetch(`${OPT_API}/materials/${materialId}/picking-mode`, {
            method: 'PUT', headers: {'Content-Type':'application/json'},
            body: JSON.stringify({picking_mode: parseInt(mode)})
        });
        const r = await res.json();
        if (r.success) showToast(r.message, 'success');
    } catch(e) { showToast('设置失败: ' + e.message, 'error'); }
}

// ===== 5. 物料治理 =====
async function renderGovernance(el) {
    el.innerHTML = `<h3 style="color:#1a237e;margin-bottom:16px;">🔧 物料底层治理 —— 双编码规则 + 去重</h3><div id="govContent"><p style="color:#999;">加载中...</p></div>`;
    try {
        const [rulesRes, dupRes] = await Promise.all([
            fetch(`${OPT_API}/material-governance/coding-rules`),
            fetch(`${OPT_API}/material-governance/check-duplicates`)
        ]);
        const rules = await rulesRes.json();
        const dups = await dupRes.json();
        if (rules.success && dups.success) {
            const d = dups.data;
            const r = rules.data;
            let html = `
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;">
                <div style="background:#e3f2fd;border:2px solid #1565c0;border-radius:10px;padding:16px;">
                    <h4 style="color:#0d47a1;margin-bottom:8px;">标准件编码规则</h4>
                    <p style="font-size:13px;font-weight:600;color:#1565c0;">${r.standard.rule}</p>
                    <p style="font-size:11px;color:#666;margin:4px 0;">适用：${r.standard.applies_to}</p>
                    <p style="font-size:11px;color:#666;">原则：${r.standard.principle}</p>
                    <div style="margin-top:6px;">${r.standard.examples.map(e=>`<span style="font-size:10px;background:#fff;padding:2px 6px;border-radius:4px;margin:2px;display:inline-block;">${e}</span>`).join('')}</div>
                </div>
                <div style="background:#fff3e0;border:2px solid #e65100;border-radius:10px;padding:16px;">
                    <h4 style="color:#bf360c;margin-bottom:8px;">非标件编码规则</h4>
                    <p style="font-size:13px;font-weight:600;color:#e65100;">${r.non_standard.rule}</p>
                    <p style="font-size:11px;color:#666;margin:4px 0;">适用：${r.non_standard.applies_to}</p>
                    <p style="font-size:11px;color:#666;">原则：${r.non_standard.principle}</p>
                    <div style="margin-top:6px;">${r.non_standard.examples.map(e=>`<span style="font-size:10px;background:#fff;padding:2px 6px;border-radius:4px;margin:2px;display:inline-block;">${e}</span>`).join('')}</div>
                </div>
            </div>
            <div style="background:#fffde7;border:1px solid #f9a825;border-radius:8px;padding:10px 16px;margin-bottom:16px;font-size:12px;color:#827717;">
                💡 新物料创建须经「技术+PMC」双确认
            </div>
            <h4 style="margin-bottom:10px;">重复物料检查结果</h4>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:16px;">
                <div style="background:#e3f2fd;border-radius:8px;padding:12px;text-align:center;"><div style="font-size:11px;color:#666;">总物料数</div><div style="font-size:20px;font-weight:700;color:#1565c0;">${d.total_materials}</div></div>
                <div style="background:#ffebee;border-radius:8px;padding:12px;text-align:center;"><div style="font-size:11px;color:#666;">重复物料数</div><div style="font-size:20px;font-weight:700;color:#c62828;">${d.duplicate_count}</div></div>
                <div style="background:#fff3e0;border-radius:8px;padding:12px;text-align:center;"><div style="font-size:11px;color:#666;">重复组数</div><div style="font-size:20px;font-weight:700;color:#e65100;">${d.duplicates.length}</div></div>
            </div>`;
            if (d.duplicates.length > 0) {
                html += `<table style="width:100%;border-collapse:collapse;font-size:12px;">
                    <thead><tr style="background:#c62828;color:#fff;"><th style="padding:8px;text-align:left;">物料编码</th><th style="padding:8px;text-align:left;">物料名称</th><th style="padding:8px;text-align:left;">规格</th></tr></thead><tbody>`;
                d.duplicates.forEach(group => {
                    group.forEach(m => {
                        html += `<tr style="border-bottom:1px solid #e0e0e0;"><td style="padding:6px 8px;">${m.code}</td><td style="padding:6px 8px;">${m.name}</td><td style="padding:6px 8px;">${m.spec||'-'}</td></tr>`;
                    });
                    html += `<tr style="background:#ffebee;"><td colspan="3" style="padding:4px 8px;font-size:10px;color:#c62828;">↑ 以上物料疑似重复，建议合并</td></tr>`;
                });
                html += '</tbody></table>';
            } else {
                html += '<p style="color:#2e7d32;font-size:13px;">✅ 未发现重复物料</p>';
            }
            document.getElementById('govContent').innerHTML = html;
        }
    } catch(e) {
        document.getElementById('govContent').innerHTML = `<p style="color:#c62828;">加载失败: ${e.message}</p>`;
    }
}

// ===== 6. 流程卡点 =====
async function renderCheckpoints(el) {
    el.innerHTML = `<h3 style="color:#1a237e;margin-bottom:16px;">🚦 流程卡点 —— 6个关键审批门</h3><div id="cpContent"><p style="color:#999;">加载中...</p></div>`;
    try {
        const res = await fetch(`${OPT_API}/checkpoints/list`);
        const r = await res.json();
        if (r.success) {
            let html = `<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-bottom:20px;">`;
            r.data.forEach(cp => {
                const colors = ['#1565c0','#00838f','#6a1b9a','#e65100','#2e7d32','#c62828'];
                const c = colors[cp.id-1];
                html += `<div style="background:#fff;border:2px solid ${c};border-radius:10px;padding:14px;text-align:center;">
                    <div style="width:28px;height:28px;background:${c};color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;margin:0 auto 6px;">${cp.id}</div>
                    <div style="font-size:12px;font-weight:700;color:${c};">${cp.name}</div>
                    <div style="font-size:10px;color:#666;margin-top:4px;">${cp.rule}</div>
                    <div style="font-size:9px;color:#c62828;margin-top:4px;">不通过：${cp.fail_action}</div>
                </div>`;
            });
            html += '</div>';
            html += `<div style="background:#fff8e1;border:2px dashed #f9a825;border-radius:10px;padding:16px;">
                <h4 style="color:#e65100;margin-bottom:8px;">卡点校验测试</h4>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                    <label>选择卡点<select id="cp_select" class="opt-input"><option value="1">① 项目预算校验</option><option value="2">② 库存是否够用</option><option value="3">③ ≥3家比价</option><option value="4">④ 额度权限</option><option value="5">⑤ 检验合格率</option><option value="6">⑥ 项目号绑定</option></select></label>
                    <label>项目ID<input type="number" id="cp_project" value="1" class="opt-input"></label>
                    <label>金额<input type="number" id="cp_amount" value="10000" class="opt-input"></label>
                    <label>物料ID<input type="number" id="cp_material" value="1" class="opt-input"></label>
                </div>
                <button onclick="testCheckpoint()" style="margin-top:10px;background:#e65100;color:#fff;border:none;padding:8px 20px;border-radius:8px;cursor:pointer;">🔍 校验</button>
                <div id="cpResult" style="margin-top:12px;"></div>
            </div>`;
            document.getElementById('cpContent').innerHTML = html;
        }
    } catch(e) {
        document.getElementById('cpContent').innerHTML = `<p style="color:#c62828;">加载失败: ${e.message}</p>`;
    }
}

async function testCheckpoint() {
    const cp = parseInt(document.getElementById('cp_select').value);
    const data = {
        checkpoint: cp,
        project_id: parseInt(document.getElementById('cp_project').value) || null,
        amount: parseFloat(document.getElementById('cp_amount').value) || 0,
        material_id: parseInt(document.getElementById('cp_material').value) || null,
    };
    try {
        const res = await fetch(`${OPT_API}/checkpoints/validate`, {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify(data)
        });
        const r = await res.json();
        const color = r.passed ? '#2e7d32' : '#c62828';
        const icon = r.passed ? '✅' : '❌';
        document.getElementById('cpResult').innerHTML = `<div style="background:${r.passed?'#e8f5e9':'#ffebee'};border-radius:8px;padding:12px;">
            <p style="font-size:14px;color:${color};font-weight:700;">${icon} ${r.message}</p>
            ${r.details ? `<pre style="font-size:11px;color:#666;margin-top:8px;">${JSON.stringify(r.details, null, 2)}</pre>` : ''}
        </div>`;
    } catch(e) {
        document.getElementById('cpResult').innerHTML = `<p style="color:#c62828;">校验失败: ${e.message}</p>`;
    }
}

// ===== 7. 选型门 =====
async function renderGate(el) {
    el.innerHTML = `<h3 style="color:#1a237e;margin-bottom:16px;">🏢 登录选型门配置</h3><div id="gateContent"><p style="color:#999;">加载中...</p></div>`;
    try {
        const [optRes, curRes] = await Promise.all([
            fetch(`${OPT_API}/selection-gate/options`),
            fetch(`${OPT_API}/selection-gate/current`)
        ]);
        const opts = await optRes.json();
        const cur = await curRes.json();
        if (opts.success && cur.success) {
            const o = opts.data;
            const c = cur.data;
            let html = `
            <div style="background:#e0f7fa;border:2px dashed #006064;border-radius:12px;padding:20px;margin-bottom:20px;">
                <h4 style="color:#006064;margin-bottom:12px;">当前配置</h4>
                <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
                    <div style="background:#fff;border-radius:8px;padding:12px;text-align:center;">
                        <div style="font-size:11px;color:#666;">行业类型</div>
                        <div style="font-size:16px;font-weight:700;color:#006064;">${o.industry_types[c.industry_type]?.icon || ''} ${o.industry_types[c.industry_type]?.name || c.industry_type}</div>
                    </div>
                    <div style="background:#fff;border-radius:8px;padding:12px;text-align:center;">
                        <div style="font-size:11px;color:#666;">业务模式</div>
                        <div style="font-size:16px;font-weight:700;color:#006064;">${o.business_modes[c.business_mode]?.name || c.business_mode}</div>
                    </div>
                    <div style="background:#fff;border-radius:8px;padding:12px;text-align:center;">
                        <div style="font-size:11px;color:#666;">收入确认</div>
                        <div style="font-size:16px;font-weight:700;color:#006064;">${o.revenue_modes[c.revenue_mode]?.name || c.revenue_mode}</div>
                    </div>
                    <div style="background:#fff;border-radius:8px;padding:12px;text-align:center;">
                        <div style="font-size:11px;color:#666;">领料方式</div>
                        <div style="font-size:16px;font-weight:700;color:#006064;">${o.picking_modes[c.picking_mode]?.icon || ''} ${o.picking_modes[c.picking_mode]?.name || c.picking_mode}</div>
                    </div>
                </div>
            </div>

            <h4 style="margin-bottom:10px;">修改配置</h4>
            <div style="background:#fff;border:2px solid #e0e0e0;border-radius:10px;padding:20px;">
                <div style="margin-bottom:16px;">
                    <label style="font-size:13px;font-weight:600;color:#1565c0;">第一步：行业类型</label>
                    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:8px;">
                        ${Object.entries(o.industry_types).map(([k,v])=>`
                            <div onclick="selectGate('industry','${k}')" id="gate_industry_${k}" style="cursor:pointer;border:2px solid ${c.industry_type==k?v.icon==='🔧'?'#1565c0':'#e0e0e0':'#e0e0e0'};border-radius:10px;padding:12px;text-align:center;background:${c.industry_type==k?'#e3f2fd':'#fff'};">
                                <div style="font-size:24px;">${v.icon}</div>
                                <div style="font-size:13px;font-weight:700;">${v.name}</div>
                                <div style="font-size:10px;color:#666;">${v.desc}</div>
                            </div>`).join('')}
                    </div>
                </div>
                <div style="margin-bottom:16px;">
                    <label style="font-size:13px;font-weight:600;color:#e65100;">第二步：业务模式（默认小批量多品种）</label>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:8px;">
                        ${Object.entries(o.business_modes).map(([k,v])=>`
                            <div onclick="selectGate('mode','${k}')" id="gate_mode_${k}" style="cursor:pointer;border:2px solid ${c.business_mode==k?'#e65100':'#e0e0e0'};border-radius:10px;padding:14px;background:${c.business_mode==k?'#fff3e0':'#fff'};">
                                <div style="font-size:14px;font-weight:700;color:${k=='A'?'#1565c0':'#e65100'};">${k=='A'?'🏭':'🔧'} ${v.name}</div>
                                <div style="font-size:11px;color:#666;margin-top:4px;">${v.desc}</div>
                                ${v.default?'<span style="font-size:9px;background:#e65100;color:#fff;padding:2px 6px;border-radius:6px;">系统默认</span>':''}
                            </div>`).join('')}
                    </div>
                </div>
                <div style="margin-bottom:16px;">
                    <label style="font-size:13px;font-weight:600;color:#2e7d32;">第三步：收入确认方式（默认完工百分比法）</label>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:8px;">
                        ${Object.entries(o.revenue_modes).map(([k,v])=>`
                            <div onclick="selectGate('revenue','${k}')" id="gate_revenue_${k}" style="cursor:pointer;border:2px solid ${c.revenue_mode==k?'#2e7d32':'#e0e0e0'};border-radius:10px;padding:14px;background:${c.revenue_mode==k?'#e8f5e9':'#fff'};">
                                <div style="font-size:14px;font-weight:700;color:#2e7d32;">${k=='percentage'?'📐':'📦'} ${v.name}</div>
                                <div style="font-size:11px;color:#666;margin-top:4px;">${v.desc}</div>
                                ${v.default?'<span style="font-size:9px;background:#2e7d32;color:#fff;padding:2px 6px;border-radius:6px;">系统默认</span>':''}
                            </div>`).join('')}
                    </div>
                </div>
                <div style="margin-bottom:16px;">
                    <label style="font-size:13px;font-weight:600;color:#6a1b9a;">第四步：领料方式（默认按单领料）</label>
                    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:8px;">
                        ${Object.values(o.picking_modes).map(v=>`
                            <div onclick="selectGate('picking','${v.id}')" id="gate_picking_${v.id}" style="cursor:pointer;border:2px solid ${c.picking_mode==v.id?'#6a1b9a':'#e0e0e0'};border-radius:10px;padding:10px;text-align:center;background:${c.picking_mode==v.id?'#f3e5f5':'#fff'};">
                                <div style="font-size:20px;">${v.icon}</div>
                                <div style="font-size:12px;font-weight:700;">${v.name}</div>
                                <div style="font-size:9px;color:#666;">${v.desc}</div>
                                ${v.default?'<span style="font-size:8px;background:#6a1b9a;color:#fff;padding:1px 4px;border-radius:4px;">默认</span>':''}
                            </div>`).join('')}
                    </div>
                </div>
                <div style="margin-bottom:16px;">
                    <label style="font-size:13px;font-weight:600;color:#555;">细分行业（系统自动判断A/B模式）</label>
                    <input type="text" id="gate_subindustry" placeholder="如：非标自动化设备" value="${c.sub_industry||''}" class="opt-input" style="margin-top:6px;">
                    <p style="font-size:11px;color:#888;margin-top:4px;">${o.auto_detect.rule}</p>
                </div>
                <button onclick="saveGate()" style="background:#006064;color:#fff;border:none;padding:10px 28px;border-radius:8px;cursor:pointer;font-size:14px;">💾 保存选型配置</button>
                <div id="gateSaveResult" style="margin-top:12px;"></div>
            </div>`;
            document.getElementById('gateContent').innerHTML = html;
        }
    } catch(e) {
        document.getElementById('gateContent').innerHTML = `<p style="color:#c62828;">加载失败: ${e.message}</p>`;
    }
}

let gateSelections = {};
function selectGate(type, value) {
    gateSelections[type] = value;
    // Visual feedback - update borders
    if (type === 'industry') {
        document.querySelectorAll('[id^="gate_industry_"]').forEach(el => { el.style.borderColor = '#e0e0e0'; el.style.background = '#fff'; });
        const el = document.getElementById(`gate_industry_${value}`);
        if (el) { el.style.borderColor = '#1565c0'; el.style.background = '#e3f2fd'; }
    } else if (type === 'mode') {
        document.querySelectorAll('[id^="gate_mode_"]').forEach(el => { el.style.borderColor = '#e0e0e0'; el.style.background = '#fff'; });
        const el = document.getElementById(`gate_mode_${value}`);
        if (el) { el.style.borderColor = '#e65100'; el.style.background = '#fff3e0'; }
    } else if (type === 'revenue') {
        document.querySelectorAll('[id^="gate_revenue_"]').forEach(el => { el.style.borderColor = '#e0e0e0'; el.style.background = '#fff'; });
        const el = document.getElementById(`gate_revenue_${value}`);
        if (el) { el.style.borderColor = '#2e7d32'; el.style.background = '#e8f5e9'; }
    } else if (type === 'picking') {
        document.querySelectorAll('[id^="gate_picking_"]').forEach(el => { el.style.borderColor = '#e0e0e0'; el.style.background = '#fff'; });
        const el = document.getElementById(`gate_picking_${value}`);
        if (el) { el.style.borderColor = '#6a1b9a'; el.style.background = '#f3e5f5'; }
    }
}

async function saveGate() {
    const data = {
        industry_type: gateSelections.industry || 'engineering',
        business_mode: gateSelections.mode || 'B',
        revenue_mode: gateSelections.revenue || 'percentage',
        picking_mode: parseInt(gateSelections.picking || 1),
        sub_industry: document.getElementById('gate_subindustry').value,
        manual_override: true,
    };
    try {
        const res = await fetch(`${OPT_API}/selection-gate/save`, {
            method: 'POST', headers: {'Content-Type':'application/json'},
            body: JSON.stringify(data)
        });
        const r = await res.json();
        if (r.success) {
            document.getElementById('gateSaveResult').innerHTML = `<div style="background:#e8f5e9;border-radius:8px;padding:12px;color:#2e7d32;font-weight:600;">✅ ${r.message} | 行业：${r.data.industry_name} | 模式：${r.data.business_mode}</div>`;
        }
    } catch(e) {
        document.getElementById('gateSaveResult').innerHTML = `<p style="color:#c62828;">保存失败: ${e.message}</p>`;
    }
}
