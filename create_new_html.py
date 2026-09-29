# -*- coding: utf-8 -*-
"""
创建一个全新的ERP前端页面，修复所有编码问题
"""

html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ERP系统 - VIBE CODING</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f7fa; min-height: 100vh; }
        .header { background-color: #2c3e50; color: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 20px; font-weight: 600; }
        .lang-btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
        .lang-btn.active { background-color: #3498db; color: white; }
        .lang-btn:not(.active) { background-color: #34495e; color: #bdc3c7; }
        .main-container { display: flex; height: calc(100vh - 60px); }
        .sidebar { width: 25%; background-color: white; border-right: 1px solid #e0e0e0; }
        .sidebar-menu { list-style: none; padding: 10px 0; }
        .sidebar-menu button { width: 100%; padding: 14px 16px; text-align: left; border: none; background: none; border-radius: 6px; cursor: pointer; font-size: 15px; color: #555; display: flex; align-items: center; gap: 10px; }
        .sidebar-menu button:hover { background-color: #f5f7fa; }
        .sidebar-menu button.active { background-color: #3498db; color: white; }
        .sidebar-footer { margin-top: auto; padding: 15px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #999; text-align: center; }
        .content-area { flex: 1; overflow-y: auto; padding: 20px; }
        .content-header { margin-bottom: 20px; }
        .content-header h2 { font-size: 24px; color: #2c3e50; }
        .card { background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); padding: 20px; margin-bottom: 20px; }
        .card-title { font-size: 18px; font-weight: 600; margin-bottom: 15px; color: #2c3e50; }
        .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; transition: background-color 0.2s; }
        .btn-primary { background-color: #3498db; color: white; }
        .btn-primary:hover { background-color: #2980b9; }
        .btn-secondary { background-color: #bdc3c7; color: #2c3e50; }
        .btn-secondary:hover { background-color: #95a5a6; }
        .btn-danger { background-color: #e74c3c; color: white; }
        .btn-danger:hover { background-color: #c0392b; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .stat-card { background-color: white; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .stat-icon { font-size: 36px; margin-bottom: 10px; }
        .stat-value { font-size: 28px; font-weight: 600; color: #2c3e50; }
        .stat-label { font-size: 14px; color: #7f8c8d; margin-top: 5px; }
        .data-table { width: 100%; border-collapse: collapse; }
        .data-table th, .data-table td { padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }
        .data-table th { background-color: #f5f7fa; font-weight: 600; color: #2c3e50; }
        .data-table tr:hover { background-color: #fafafa; }
        .status { padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; }
        .status.active { background-color: #d5f4e6; color: #27ae60; }
        .status.pending { background-color: #fef5e7; color: #f39c12; }
        .status.completed { background-color: #e8f4f8; color: #3498db; }
        .status.in_progress { background-color: #f5eef8; color: #9b59b6; }
        .status.in_use { background-color: #d5f4e6; color: #27ae60; }
        .status.disposed { background-color: #f5f5f5; color: #7f8c8d; }
        .status.scrapped { background-color: #ffebee; color: #e74c3c; }
        .modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0,0,0,0.5); display: none; justify-content: center; align-items: center; z-index: 1000; }
        .modal-overlay.show { display: flex; }
        .modal { background-color: white; border-radius: 8px; padding: 20px; width: 90%; max-width: 500px; }
        .modal h3 { margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: 500; }
        .form-group input, .form-group select { width: 100%; padding: 10px; border: 1px solid #e0e0e0; border-radius: 4px; font-size: 14px; }
        .form-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }
        .search-box { padding: 8px 12px; border: 1px solid #e0e0e0; border-radius: 4px; margin-bottom: 15px; width: 300px; }
        .add-btn { margin-bottom: 15px; }
        .finance-tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .finance-tab { padding: 8px 20px; border: none; border-radius: 4px; cursor: pointer; background-color: #e0e0e0; color: #555; }
        .finance-tab.active { background-color: #3498db; color: white; }
        .voucher-container { background-color: #fff; border: 2px solid #3498db; border-radius: 8px; padding: 20px; margin-top: 20px; }
        .voucher-title { text-align: center; font-size: 20px; font-weight: 600; margin-bottom: 20px; }
        .voucher-table { width: 100%; border-collapse: collapse; }
        .voucher-table th, .voucher-table td { padding: 10px; border: 1px solid #ddd; text-align: center; }
        .voucher-table th { background-color: #f5f7fa; }
        .voucher-total-row { font-weight: bold; background-color: #f5f7fa; }
        .voucher-signature-area { display: flex; justify-content: space-around; margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; }
        .amount-cell { display: flex; }
        .amount-digit { width: 24px; height: 30px; border-bottom: 1px solid #333; text-align: center; line-height: 30px; font-size: 16px; }
        .blue-line { border-bottom-color: #3498db; }
        .red-line { border-bottom-color: #e74c3c; }
        .upload-area { border: 2px dashed #3498db; border-radius: 8px; padding: 40px; text-align: center; cursor: pointer; margin-bottom: 20px; }
        .upload-area:hover { background-color: #f5f7fa; }
        .upload-area.dragover { border-color: #2980b9; background-color: #ebf5fb; }
        .upload-icon { font-size: 48px; margin-bottom: 15px; }
        .report-section { margin-bottom: 30px; }
        .report-section h3 { margin-bottom: 15px; color: #2c3e50; }
        .report-table { width: 100%; border-collapse: collapse; }
        .report-table th, .report-table td { padding: 10px; border: 1px solid #ddd; }
        .report-table th { background-color: #f5f7fa; text-align: left; }
        .report-total { font-weight: bold; background-color: #f5f7fa; }
        .add-data-form { background-color: #f5f7fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .add-data-form h4 { margin-bottom: 10px; }
        .add-data-form select, .add-data-form input { margin-right: 10px; padding: 8px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>ERP系统</h1>
        <div>
            <button class="lang-btn active" onclick="changeLang('zh')">中文</button>
            <button class="lang-btn" onclick="changeLang('en')">English</button>
        </div>
    </div>
    
    <div class="main-container">
        <div class="sidebar">
            <ul class="sidebar-menu">
                <li><button class="active" onclick="loadModule('dashboard')">📊 仪表盘</button></li>
                <li><button onclick="loadModule('materials')">📦 物料管理</button></li>
                <li><button onclick="loadModule('purchase')">🛒 采购管理</button></li>
                <li><button onclick="loadModule('production')">🏭 生产管理</button></li>
                <li><button onclick="loadModule('finance')">💰 财务管理</button></li>
                <li><button onclick="loadModule('crossborder')">🌍 跨境合规</button></li>
                <li><button onclick="loadModule('scanning')">📱 扫码录入</button></li>
                <li><button onclick="loadModule('invoice')">🧾 发票识别</button></li>
            </ul>
            <div class="sidebar-footer">ERP智能系统 v1.0</div>
        </div>
        
        <div class="content-area" id="content"></div>
    </div>

    <script>
        let currentLang = 'zh';
        let currentModule = 'dashboard';
        
        const translations = {
            'zh': {
                'dashboard-title': '仪表盘', 'dashboard-desc': '欢迎使用ERP系统',
                'materials-title': '物料管理', 'materials-desc': '管理企业物料库存',
                'purchase-title': '采购管理', 'purchase-desc': '采购订单管理',
                'production-title': '生产管理', 'production-desc': '生产订单管理',
                'finance-title': '财务管理', 'finance-desc': '总账、应收应付、出纳、固定资产、工资、报表',
                'finance-general': '总账管理', 'finance-arap': '应收应付', 'finance-cash': '出纳管理',
                'finance-asset': '固定资产', 'finance-payroll': '工资管理', 'finance-reports': '财务报表',
                'crossborder-title': '跨境合规', 'crossborder-desc': '跨境贸易合规',
                'scanning-title': '扫码录入', 'scanning-desc': '扫描条码生成凭证',
                'invoice-title': '发票识别', 'invoice-desc': '上传PDF发票识别',
                'total-materials': '物料总数', 'purchase-orders': '采购订单',
                'production-orders': '生产订单', 'compliance-alerts': '合规预警',
                'name': '名称', 'code': '编码', 'unit': '单位', 'price': '单价',
                'status': '状态', 'action': '操作', 'view': '查看', 'edit': '编辑',
                'delete': '删除', 'PO-no': '采购单号', 'supplier': '供应商',
                'material': '物料', 'quantity': '数量', 'work-order-no': '工单号',
                'product': '产品', 'hs-code': 'HS编码', 'description': '商品描述',
                'country': '目的地', 'declared-value': '申报价值', 'tax-estimate': '预估税费',
                'scan-input-placeholder': '请扫描条码...', 'batch-mode': '批量模式',
                'single-mode': '单条模式', 'generate-vouchers': '生成凭证',
                'clear-all': '清空全部', 'total': '合计', 'documents': '单据',
                'debit': '借方', 'credit': '贷方', 'click-or-drag': '点击或拖拽上传PDF发票',
                'supported-pdf': '支持格式：PDF', 'load-sample': '加载示例发票',
                'generate-voucher': '生成凭证', 'clear-data': '清空数据',
                'recognition-result': '识别结果', 'invoice-info': '发票信息',
                'invoice-no': '发票号码', 'invoice-code': '发票代码', 'issue-date': '开票日期',
                'buyer-info': '购买方信息', 'seller-info': '销售方信息', 'tax-id': '税号',
                'amount-info': '金额信息', 'subtotal': '不含税金额', 'tax': '税额',
                'total-cn': '合计', 'prepared-by': '制单人：', 'accounting-voucher': '记账凭证',
                'voucher-type': '凭证字', 'voucher-no': '凭证号', 'voucher-date': '日期',
                'attachments': '附单据', 'sheets': '张', 'summary': '摘要', 'account': '会计科目',
                'debit-amount': '借方金额', 'credit-amount': '贷方金额', 'hide-voucher': '隐藏凭证',
                'items': '商品明细', 'unit-price': '单价', 'tax-rate': '税率',
                'save-voucher': '保存凭证',
                'active': '激活', 'pending': '待处理', 'completed': '已完成', 'in_progress': '进行中',
                'in_use': '使用中', 'disposed': '已处置', 'scrapped': '已报废',
                'add-data': '添加数据', 'category': '类别', 'item': '项目', 'amount': '金额',
                'balance-sheet': '资产负债表', 'profit-statement': '利润表', 'cash-flow': '现金流量表',
                'assets': '资产', 'liabilities': '负债', 'equity': '所有者权益',
                'current-assets': '流动资产', 'non-current-assets': '非流动资产',
                'current-liabilities': '流动负债', 'non-current-liabilities': '非流动负债',
                'operating-revenue': '营业收入', 'operating-cost': '营业成本',
                'gross-profit': '营业利润', 'net-profit': '净利润',
                'currency-funds': '货币资金', 'short-term-investment': '短期投资',
                'accounts-receivable': '应收账款', 'inventory': '存货',
                'long-term-investment': '长期投资', 'fixed-assets': '固定资产',
                'accumulated-depreciation': '累计折旧', 'intangible-assets': '无形资产',
                'short-term-loan': '短期借款', 'accounts-payable': '应付账款',
                'tax-payable': '应交税费', 'long-term-loan': '长期借款',
                'paid-in-capital': '实收资本', 'retained-earnings': '留存收益',
                'add': '添加', 'update-success': '更新成功', 'update-failed': '更新失败'
            },
            'en': {
                'dashboard-title': 'Dashboard', 'dashboard-desc': 'Welcome to ERP',
                'materials-title': 'Materials', 'materials-desc': 'Manage inventory',
                'purchase-title': 'Purchase', 'purchase-desc': 'Purchase orders',
                'production-title': 'Production', 'production-desc': 'Work orders',
                'finance-title': 'Finance', 'finance-desc': 'GL, AR/AP, Cash, Assets, Payroll, Reports',
                'finance-general': 'General Ledger', 'finance-arap': 'AR/AP', 'finance-cash': 'Cash Management',
                'finance-asset': 'Fixed Assets', 'finance-payroll': 'Payroll', 'finance-reports': 'Financial Reports',
                'crossborder-title': 'Cross-border', 'crossborder-desc': 'Trade compliance',
                'scanning-title': 'Scan Entry', 'scanning-desc': 'Scan to generate vouchers',
                'invoice-title': 'Invoice Recognition', 'invoice-desc': 'Upload PDF invoice',
                'total-materials': 'Total Materials', 'purchase-orders': 'Purchase Orders',
                'production-orders': 'Production Orders', 'compliance-alerts': 'Compliance Alerts',
                'name': 'Name', 'code': 'Code', 'unit': 'Unit', 'price': 'Price',
                'status': 'Status', 'action': 'Action', 'view': 'View', 'edit': 'Edit',
                'delete': 'Delete', 'PO-no': 'PO No.', 'supplier': 'Supplier',
                'material': 'Material', 'quantity': 'Quantity', 'work-order-no': 'WO No.',
                'product': 'Product', 'hs-code': 'HS Code', 'description': 'Description',
                'country': 'Country', 'declared-value': 'Declared Value', 'tax-estimate': 'Tax Estimate',
                'scan-input-placeholder': 'Scan barcode...', 'batch-mode': 'Batch Mode',
                'single-mode': 'Single Mode', 'generate-vouchers': 'Generate Vouchers',
                'clear-all': 'Clear All', 'total': 'Total', 'documents': 'Documents',
                'debit': 'Debit', 'credit': 'Credit', 'click-or-drag': 'Click or drag to upload PDF',
                'supported-pdf': 'Supported: PDF', 'load-sample': 'Load Sample',
                'generate-voucher': 'Generate Voucher', 'clear-data': 'Clear Data',
                'recognition-result': 'Recognition Result', 'invoice-info': 'Invoice Info',
                'invoice-no': 'Invoice No.', 'invoice-code': 'Invoice Code', 'issue-date': 'Issue Date',
                'buyer-info': 'Buyer Info', 'seller-info': 'Seller Info', 'tax-id': 'Tax ID',
                'amount-info': 'Amount Info', 'subtotal': 'Subtotal', 'tax': 'Tax',
                'total-cn': 'Total', 'prepared-by': 'Prepared by:', 'accounting-voucher': 'Accounting Voucher',
                'voucher-type': 'Voucher Type', 'voucher-no': 'Voucher No.', 'voucher-date': 'Date',
                'attachments': 'Attachments', 'sheets': 'sheets', 'summary': 'Summary', 'account': 'Account',
                'debit-amount': 'Debit Amount', 'credit-amount': 'Credit Amount', 'hide-voucher': 'Hide Voucher',
                'items': 'Items', 'unit-price': 'Unit Price', 'tax-rate': 'Tax Rate',
                'save-voucher': 'Save Voucher',
                'active': 'Active', 'pending': 'Pending', 'completed': 'Completed', 'in_progress': 'In Progress',
                'in_use': 'In Use', 'disposed': 'Disposed', 'scrapped': 'Scrapped',
                'add-data': 'Add Data', 'category': 'Category', 'item': 'Item', 'amount': 'Amount',
                'balance-sheet': 'Balance Sheet', 'profit-statement': 'Profit Statement', 'cash-flow': 'Cash Flow',
                'assets': 'Assets', 'liabilities': 'Liabilities', 'equity': 'Equity',
                'current-assets': 'Current Assets', 'non-current-assets': 'Non-Current Assets',
                'current-liabilities': 'Current Liabilities', 'non-current-liabilities': 'Non-Current Liabilities',
                'operating-revenue': 'Operating Revenue', 'operating-cost': 'Operating Cost',
                'gross-profit': 'Gross Profit', 'net-profit': 'Net Profit',
                'currency-funds': 'Currency Funds', 'short-term-investment': 'Short-term Investment',
                'accounts-receivable': 'Accounts Receivable', 'inventory': 'Inventory',
                'long-term-investment': 'Long-term Investment', 'fixed-assets': 'Fixed Assets',
                'accumulated-depreciation': 'Accumulated Depreciation', 'intangible-assets': 'Intangible Assets',
                'short-term-loan': 'Short-term Loan', 'accounts-payable': 'Accounts Payable',
                'tax-payable': 'Tax Payable', 'long-term-loan': 'Long-term Loan',
                'paid-in-capital': 'Paid-in Capital', 'retained-earnings': 'Retained Earnings',
                'add': 'Add', 'update-success': 'Update Success', 'update-failed': 'Update Failed'
            }
        };
        
        const mockData = {
            stats: { total_materials: 156, purchase_orders: 23, production_orders: 15, compliance_alerts: 3 },
            materials: [
                { name: '原材料A', code: 'RM001', unit: 'kg', unit_price: 12.50, status: 'active' },
                { name: '原材料B', code: 'RM002', unit: 'm', unit_price: 8.00, status: 'active' },
                { name: '半成品C', code: 'SM001', unit: '件', unit_price: 56.00, status: 'active' },
                { name: '成品D', code: 'FG001', unit: '箱', unit_price: 280.00, status: 'completed' }
            ],
            purchaseOrders: [
                { po_no: 'PO2024001', supplier: '供应商A', material: '原材料A', quantity: 500, status: 'completed' },
                { po_no: 'PO2024002', supplier: '供应商B', material: '原材料B', quantity: 300, status: 'in_progress' },
                { po_no: 'PO2024003', supplier: '供应商C', material: '半成品C', quantity: 100, status: 'pending' }
            ],
            productionOrders: [
                { wo_no: 'WO2024001', product: '成品D', quantity: 50, status: 'completed' },
                { wo_no: 'WO2024002', product: '成品D', quantity: 30, status: 'in_progress' }
            ]
        };
        
        function changeLang(lang) {
            currentLang = lang;
            document.querySelectorAll('.lang-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            loadModule(currentModule);
        }
        
        function loadModule(module) {
            currentModule = module;
            document.querySelectorAll('.sidebar-menu button').forEach(btn => btn.classList.remove('active'));
            document.querySelector(`.sidebar-menu button[onclick="loadModule('${module}')"]`).classList.add('active');
            
            const content = document.getElementById('content');
            switch(module) {
                case 'dashboard': content.innerHTML = renderDashboard(); break;
                case 'materials': content.innerHTML = renderMaterials(); break;
                case 'purchase': content.innerHTML = renderPurchase(); break;
                case 'production': content.innerHTML = renderProduction(); break;
                case 'finance': content.innerHTML = renderFinance(); break;
                case 'crossborder': content.innerHTML = renderCrossborder(); break;
                case 'scanning': content.innerHTML = renderScanning(); break;
                case 'invoice': content.innerHTML = renderInvoice(); break;
            }
        }
        
        function getStatusText(status) {
            const texts = { 
                'active': translations[currentLang]['active'], 
                'pending': translations[currentLang]['pending'], 
                'completed': translations[currentLang]['completed'], 
                'in_progress': translations[currentLang]['in_progress'],
                'in_use': translations[currentLang]['in_use'],
                'disposed': translations[currentLang]['disposed'],
                'scrapped': translations[currentLang]['scrapped']
            };
            return texts[status] || status;
        }
        
        function renderDashboard() {
            const t = translations[currentLang];
            return `
                <div class="content-header"><h2>${t['dashboard-title']}</h2><p>${t['dashboard-desc']}</p></div>
                <div class="stats-grid">
                    <div class="stat-card"><div class="stat-icon">📦</div><div class="stat-value">${mockData.stats.total_materials}</div><div class="stat-label">${t['total-materials']}</div></div>
                    <div class="stat-card"><div class="stat-icon">🛒</div><div class="stat-value">${mockData.stats.purchase_orders}</div><div class="stat-label">${t['purchase-orders']}</div></div>
                    <div class="stat-card"><div class="stat-icon">🏭</div><div class="stat-value">${mockData.stats.production_orders}</div><div class="stat-label">${t['production-orders']}</div></div>
                    <div class="stat-card"><div class="stat-icon">⚠️</div><div class="stat-value">${mockData.stats.compliance_alerts}</div><div class="stat-label">${t['compliance-alerts']}</div></div>
                </div>
                <div class="card"><div class="card-title">${t['purchase-orders']}</div>
                    <table class="data-table"><thead><tr><th>${t['PO-no']}</th><th>${t['supplier']}</th><th>${t['material']}</th><th>${t['quantity']}</th><th>${t['status']}</th></tr></thead>
                    <tbody>${mockData.purchaseOrders.map(o => `<tr><td>${o.po_no}</td><td>${o.supplier}</td><td>${o.material}</td><td>${o.quantity}</td><td><span class="status ${o.status}">${getStatusText(o.status)}</span></td></tr>`).join('')}</tbody></table>
                </div>
            `;
        }
        
        function renderMaterials() {
            const t = translations[currentLang];
            return `<div class="content-header"><h2>${t['materials-title']}</h2><p>${t['materials-desc']}</p></div>
                <div class="card"><div class="card-title">${t['materials-title']}</div>
                    <table class="data-table"><thead><tr><th>${t['name']}</th><th>${t['code']}</th><th>${t['unit']}</th><th>${t['price']}</th><th>${t['status']}</th></tr></thead>
                    <tbody>${mockData.materials.map(m => `<tr><td>${m.name}</td><td>${m.code}</td><td>${m.unit}</td><td>¥${m.unit_price.toFixed(2)}</td><td><span class="status ${m.status}">${getStatusText(m.status)}</span></td></tr>`).join('')}</tbody></table>
                </div>`;
        }
        
        function renderPurchase() {
            const t = translations[currentLang];
            return `<div class="content-header"><h2>${t['purchase-title']}</h2><p>${t['purchase-desc']}</p></div>
                <div class="card"><div class="card-title">${t['purchase-orders']}</div>
                    <table class="data-table"><thead><tr><th>${t['PO-no']}</th><th>${t['supplier']}</th><th>${t['material']}</th><th>${t['quantity']}</th><th>${t['status']}</th></tr></thead>
                    <tbody>${mockData.purchaseOrders.map(o => `<tr><td>${o.po_no}</td><td>${o.supplier}</td><td>${o.material}</td><td>${o.quantity}</td><td><span class="status ${o.status}">${getStatusText(o.status)}</span></td></tr>`).join('')}</tbody></table>
                </div>`;
        }
        
        function renderProduction() {
            const t = translations[currentLang];
            return `<div class="content-header"><h2>${t['production-title']}</h2><p>${t['production-desc']}</p></div>
                <div class="card"><div class="card-title">${t['production-orders']}</div>
                    <table class="data-table"><thead><tr><th>${t['work-order-no']}</th><th>${t['product']}</th><th>${t['quantity']}</th><th>${t['status']}</th></tr></thead>
                    <tbody>${mockData.productionOrders.map(o => `<tr><td>${o.wo_no}</td><td>${o.product}</td><td>${o.quantity}</td><td><span class="status ${o.status}">${getStatusText(o.status)}</span></td></tr>`).join('')}</tbody></table>
                </div>`;
        }
        
        function renderFinance() {
            const t = translations[currentLang];
            return `<div class="content-header"><h2>${t['finance-title']}</h2><p>${t['finance-desc']}</p></div>
                <div class="finance-tabs">
                    <button class="finance-tab active" onclick="renderFinanceTab('reports')">${t['finance-reports']}</button>
                    <button class="finance-tab" onclick="renderFinanceTab('general')">${t['finance-general']}</button>
                    <button class="finance-tab" onclick="renderFinanceTab('arap')">${t['finance-arap']}</button>
                    <button class="finance-tab" onclick="renderFinanceTab('cash')">${t['finance-cash']}</button>
                    <button class="finance-tab" onclick="renderFinanceTab('asset')">${t['finance-asset']}</button>
                    <button class="finance-tab" onclick="renderFinanceTab('payroll')">${t['finance-payroll']}</button>
                </div>
                <div id="finance-content">${renderFinanceReports()}</div>`;
        }
        
        function renderFinanceTab(tab) {
            document.querySelectorAll('.finance-tab').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            const content = document.getElementById('finance-content');
            const t = translations[currentLang];
            
            switch(tab) {
                case 'reports': content.innerHTML = renderFinanceReports(); break;
                case 'general': content.innerHTML = renderGeneralLedger(); break;
                case 'arap': content.innerHTML = renderARAP(); break;
                case 'cash': content.innerHTML = renderCashManagement(); break;
                case 'asset': content.innerHTML = renderFixedAssets(); break;
                case 'payroll': content.innerHTML = renderPayroll(); break;
            }
        }
        
        function renderFinanceReports() {
            const t = translations[currentLang];
            return `
                <div class="card">
                    <h3>${t['balance-sheet']}</h3>
                    <div class="add-data-form">
                        <h4>${t['add-data']}</h4>
                        <select id="bs-category" onchange="loadBSItems()">
                            <option value="">${t['category']}</option>
                            <option value="current_assets">${t['current-assets']}</option>
                            <option value="non_current_assets">${t['non-current-assets']}</option>
                            <option value="current_liabilities">${t['current-liabilities']}</option>
                            <option value="non_current_liabilities">${t['non-current-liabilities']}</option>
                            <option value="equity">${t['equity']}</option>
                        </select>
                        <select id="bs-item" style="width: 200px;">
                            <option value="">${t['item']}</option>
                        </select>
                        <input type="number" id="bs-amount" placeholder="${t['amount']}" style="width: 120px;">
                        <button class="btn btn-primary" onclick="addReportData('balance_sheet')">${t['add']}</button>
                    </div>
                    <div id="balance-sheet-content">Loading...</div>
                </div>
                <div class="card">
                    <h3>${t['profit-statement']}</h3>
                    <div class="add-data-form">
                        <h4>${t['add-data']}</h4>
                        <select id="ps-item" style="width: 200px;">
                            <option value="">${t['item']}</option>
                            <option value="operating_revenue">${t['operating-revenue']}</option>
                            <option value="operating_cost">${t['operating-cost']}</option>
                            <option value="gross_profit">${t['gross-profit']}</option>
                            <option value="net_profit">${t['net-profit']}</option>
                        </select>
                        <input type="number" id="ps-amount" placeholder="${t['amount']}" style="width: 120px;">
                        <button class="btn btn-primary" onclick="addReportData('profit_statement')">${t['add']}</button>
                    </div>
                    <div id="profit-statement-content">Loading...</div>
                </div>
                <div class="card">
                    <h3>${t['cash-flow']}</h3>
                    <div id="cash-flow-content">Loading...</div>
                </div>
            `;
        }
        
        function renderGeneralLedger() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">${t['finance-general']}</div>
                <button class="btn btn-primary add-btn" onclick="showVoucherForm()">+ ${t['generate-voucher']}</button>
                <div id="voucher-list">Loading vouchers...</div>
            </div>`;
        }
        
        function renderARAP() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">${t['finance-arap']}</div>
                <div id="arap-content">Loading AR/AP data...</div>
            </div>`;
        }
        
        function renderCashManagement() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">${t['finance-cash']}</div>
                <div id="cash-content">Loading cash data...</div>
            </div>`;
        }
        
        function renderFixedAssets() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">${t['finance-asset']}</div>
                <button class="btn btn-primary add-btn" onclick="showAssetForm()">+ ${t['add-data']}</button>
                <table class="data-table" id="asset-table">
                    <thead><tr><th>${t['code']}</th><th>${t['name']}</th><th>${t['category']}</th><th>${t['price']}</th><th>${t['status']}</th><th>${t['action']}</th></tr></thead>
                    <tbody id="asset-tbody"><tr><td colspan="6" style="text-align:center;">Loading...</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderPayroll() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">${t['finance-payroll']}</div>
                <div id="payroll-content">Loading payroll data...</div>
            </div>`;
        }
        
        function renderCrossborder() {
            const t = translations[currentLang];
            return `<div class="content-header"><h2>${t['crossborder-title']}</h2><p>${t['crossborder-desc']}</p></div>
                <div class="card">
                    <div class="card-title">${t['product']}</div>
                    <table class="data-table"><thead><tr><th>${t['name']}</th><th>${t['hs-code']}</th><th>${t['description']}</th><th>${t['country']}</th><th>${t['declared-value']}</th><th>${t['tax-estimate']}</th></tr></thead>
                    <tbody>
                        <tr><td>电子产品A</td><td>85176200</td><td>智能手机配件</td><td>美国</td><td>$15,000</td><td>$1,200</td></tr>
                        <tr><td>服装B</td><td>62052000</td><td>棉质T恤</td><td>欧盟</td><td>$8,500</td><td>$850</td></tr>
                    </tbody>
                </table>
                </div>`;
        }
        
        function renderScanning() {
            const t = translations[currentLang];
            return `<div class="content-header"><h2>${t['scanning-title']}</h2><p>${t['scanning-desc']}</p></div>
                <div class="card">
                    <button class="btn btn-secondary" onclick="toggleScanMode()">${t['batch-mode']}</button>
                    <button class="btn btn-primary" onclick="clearScanData()">${t['clear-all']}</button>
                    <input type="text" class="search-box" id="scan-input" placeholder="${t['scan-input-placeholder']}" onkeydown="handleScanInput(event)">
                    <div id="scan-results"></div>
                </div>`;
        }
        
        let showVoucher = false;
        let currentInvoiceInfo = null;
        let currentVoucherDraft = null;
        let uploadedFileName = null;
        let uploadedFileSize = null;
        
        function renderInvoice() {
            const t = translations[currentLang];
            return `
                <div class="content-header"><h2>${t['invoice-title']}</h2><p>${t['invoice-desc']}</p></div>
                <div class="card">
                    <div class="upload-area" id="upload-area" onclick="document.getElementById('file-input').click()" ondragover="event.preventDefault()" ondrop="handleDrop(event)">
                        <div class="upload-icon">📄</div>
                        <div>${t['click-or-drag']}</div>
                        <div style="color: #999; font-size: 14px; margin-top: 10px;">${t['supported-pdf']}</div>
                    </div>
                    <input type="file" id="file-input" accept=".pdf" onchange="handleFile(this.files[0])" style="display:none;">
                    <div style="display:flex;gap:10px;">
                        <button class="btn btn-primary" onclick="loadSampleInvoice()">${t['load-sample']}</button>
                        <button class="btn btn-secondary" onclick="clearInvoice()">${t['clear-data']}</button>
                    </div>
                    
                    ${uploadedFileName ? `<div style="margin-top:20px;padding:15px;background-color:#f5f7fa;border-radius:4px;">
                        <div>📄 ${uploadedFileName} (${uploadedFileSize})</div>
                    </div>` : ''}
                    
                    ${currentInvoiceInfo ? `
                    <div style="margin-top:20px;">
                        <h4>${t['recognition-result']}</h4>
                        <div class="card">
                            <h5>${t['invoice-info']}</h5>
                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;">
                                <div><strong>${t['invoice-no']}:</strong> ${currentInvoiceInfo.invoice_number}</div>
                                <div><strong>${t['issue-date']}:</strong> ${currentInvoiceInfo.invoice_date}</div>
                                <div><strong>${t['subtotal']}:</strong> ¥${currentInvoiceInfo.total_amount.toFixed(2)}</div>
                                <div><strong>${t['tax']}:</strong> ¥${currentInvoiceInfo.tax_amount.toFixed(2)}</div>
                                <div><strong>${t['total-cn']}:</strong> ¥${currentInvoiceInfo.total_with_tax.toFixed(2)}</div>
                            </div>
                        </div>
                        
                        <div style="margin-top:20px;">
                            <button class="btn btn-primary" onclick="generateInvoiceVoucher()">${t['generate-voucher']}</button>
                        </div>
                    </div>
                    ` : ''}
                    
                    ${showVoucher ? `
                    <div style="margin-top:20px;">
                        <div style="display:flex;gap:10px;">
                            <button class="btn btn-primary" style="padding:4px 12px;font-size:12px;" onclick="saveInvoiceVoucher()">${t['save-voucher']}</button>
                            <button class="btn btn-secondary" style="padding:4px 12px;font-size:12px;" onclick="showVoucher=false;loadModule('invoice')">${t['hide-voucher']}</button>
                        </div>
                        <div class="voucher-container">
                            <div class="voucher-title">${t['accounting-voucher']}</div>
                            <div style="display:flex;justify-content:space-between;margin-bottom:10px;">
                                <div style="padding-left:20%;">${t['voucher-date']}：${currentInvoiceInfo?.invoice_date || new Date().toISOString().split('T')[0]}</div>
                                <div>${t['voucher-type']}：记 ${t['voucher-no']}：001</div>
                            </div>
                            <table class="voucher-table">
                                <thead>
                                    <tr>
                                        <th>${t['summary']}</th>
                                        <th>${t['account']}</th>
                                        <th>${t['debit-amount']}</th>
                                        <th>${t['credit-amount']}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr><td>${t['purchase']}原材料</td><td>原材料</td><td>${currentVoucherDraft.debit?.金额?.toFixed(2)||''}</td><td></td></tr>
                                    <tr><td>${t['tax']}进项税额</td><td>应交税费-应交增值税-进项税额</td><td>${currentVoucherDraft.debit_tax?.金额?.toFixed(2)||''}</td><td></td></tr>
                                    <tr><td>${t['payable']}货款</td><td>应付账款</td><td></td><td>${currentVoucherDraft.credit?.金额?.toFixed(2)||''}</td></tr>
                                    <tr class="voucher-total-row"><td colspan="2">${t['total-cn']}：${convertToChinese(currentVoucherDraft.credit?.金额||0)}</td><td>${currentVoucherDraft.credit?.金额?.toFixed(2)||''}</td><td>${currentVoucherDraft.credit?.金额?.toFixed(2)||''}</td></tr>
                                </tbody>
                            </table>
                            <div class="voucher-signature-area">
                                <div>${t['prepared-by']}系统自动生成</div>
                                <div>审核：________________________</div>
                                <div>记账：________________________</div>
                            </div>
                        </div>
                    </div>
                    ` : ''}
                </div>
            `;
        }
        
        const bsItemsMap = {
            'current_assets': ['货币资金', '短期投资', '应收账款', '存货', '其他流动资产'],
            'non_current_assets': ['长期投资', '固定资产', '累计折旧', '无形资产', '其他非流动资产'],
            'current_liabilities': ['短期借款', '应付账款', '应交税费', '应付职工薪酬', '其他流动负债'],
            'non_current_liabilities': ['长期借款', '应付债券', '其他非流动负债'],
            'equity': ['实收资本', '资本公积', '盈余公积', '未分配利润']
        };
        
        function loadBSItems() {
            const category = document.getElementById('bs-category').value;
            const itemSelect = document.getElementById('bs-item');
            itemSelect.innerHTML = '<option value="">选择项目</option>';
            if (category && bsItemsMap[category]) {
                bsItemsMap[category].forEach(item => {
                    const option = document.createElement('option');
                    option.value = item;
                    option.textContent = item;
                    itemSelect.appendChild(option);
                });
            }
        }
        
        async function loadBalanceSheet() {
            try {
                const response = await fetch('http://localhost:8080/api/v1/finance/reports/balance-sheet');
                const result = await response.json();
                if (result.success) {
                    renderBalanceSheetTable(result.data);
                }
            } catch (error) {
                document.getElementById('balance-sheet-content').innerHTML = '<div style="text-align:center;color:#999;">加载失败</div>';
            }
        }
        
        function renderBalanceSheetTable(data) {
            const t = translations[currentLang];
            let html = '<table class="report-table">';
            html += `<tr><th>${t['assets']}</th><th></th><th>${t['liabilities']} + ${t['equity']}</th><th></th></tr>`;
            
            let totalAssets = 0;
            let totalLiabilities = 0;
            let totalEquity = 0;
            
            html += `<tr><td colspan="2"><strong>${t['current-assets']}</strong></td><td colspan="2"><strong>${t['current-liabilities']}</strong></td></tr>`;
            Object.entries(data.assets.current_assets || {}).forEach(([name, value]) => {
                const numValue = parseFloat(value.replace(/,/g, '')) || 0;
                totalAssets += numValue;
                html += `<tr><td>${name}</td><td style="text-align:right;">¥${value}</td>`;
                if (Object.keys(data.liabilities.current_liabilities || {}).includes(name)) {
                    const liabValue = parseFloat((data.liabilities.current_liabilities[name] || '0').replace(/,/g, '')) || 0;
                    totalLiabilities += liabValue;
                    html += `<td>${name}</td><td style="text-align:right;">¥${data.liabilities.current_liabilities[name]}</td>`;
                } else {
                    html += '<td></td><td></td>';
                }
                html += '</tr>';
            });
            
            html += `<tr><td colspan="2"><strong>${t['non-current-assets']}</strong></td><td colspan="2"><strong>${t['non-current-liabilities']}</strong></td></tr>`;
            Object.entries(data.assets.non_current_assets || {}).forEach(([name, value]) => {
                const numValue = parseFloat(value.replace(/,/g, '')) || 0;
                totalAssets += numValue;
                html += `<tr><td>${name}</td><td style="text-align:right;">¥${value}</td>`;
                if (Object.keys(data.liabilities.non_current_liabilities || {}).includes(name)) {
                    const liabValue = parseFloat((data.liabilities.non_current_liabilities[name] || '0').replace(/,/g, '')) || 0;
                    totalLiabilities += liabValue;
                    html += `<td>${name}</td><td style="text-align:right;">¥${data.liabilities.non_current_liabilities[name]}</td>`;
                } else {
                    html += '<td></td><td></td>';
                }
                html += '</tr>';
            });
            
            html += `<tr><td colspan="2"><strong>${t['total']} ${t['assets']}</strong></td><td style="text-align:right;font-weight:bold;">¥${totalAssets.toLocaleString()}</td>`;
            html += `<td colspan="2"><strong>${t['equity']}</strong></td></tr>`;
            
            Object.entries(data.equity || {}).forEach(([name, value]) => {
                const numValue = parseFloat(value.replace(/,/g, '')) || 0;
                totalEquity += numValue;
                html += `<tr><td></td><td></td><td>${name}</td><td style="text-align:right;">¥${value}</td></tr>`;
            });
            
            html += `<tr class="report-total"><td></td><td></td><td><strong>${t['total']} ${t['liabilities']} + ${t['equity']}</strong></td><td style="text-align:right;font-weight:bold;">¥${(totalLiabilities + totalEquity).toLocaleString()}</td></tr>`;
            html += '</table>';
            
            document.getElementById('balance-sheet-content').innerHTML = html;
        }
        
        async function addReportData(reportType) {
            const t = translations[currentLang];
            let itemName, amount;
            
            if (reportType === 'balance_sheet') {
                itemName = document.getElementById('bs-item').value;
                amount = document.getElementById('bs-amount').value;
            } else {
                itemName = document.getElementById('ps-item').value;
                amount = document.getElementById('ps-amount').value;
            }
            
            if (!itemName || !amount) {
                alert(t['please-fill'] || '请填写完整信息');
                return;
            }
            
            try {
                const response = await fetch('http://localhost:8080/api/v1/finance/reports/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ report_type: reportType, item_name: itemName, amount: parseFloat(amount) })
                });
                const result = await response.json();
                if (result.success) {
                    alert(t['update-success']);
                    if (reportType === 'balance_sheet') {
                        loadBalanceSheet();
                    } else {
                        loadProfitStatement();
                    }
                } else {
                    alert(t['update-failed']);
                }
            } catch (error) {
                alert('网络错误');
            }
        }
        
        async function loadProfitStatement() {
            try {
                const response = await fetch('http://localhost:8080/api/v1/finance/reports/profit-statement');
                const result = await response.json();
                if (result.success) {
                    renderProfitStatementTable(result.data);
                }
            } catch (error) {
                document.getElementById('profit-statement-content').innerHTML = '<div style="text-align:center;color:#999;">加载失败</div>';
            }
        }
        
        function renderProfitStatementTable(data) {
            const t = translations[currentLang];
            let html = '<table class="report-table">';
            let total = 0;
            
            html += `<tr><th>${t['profit-statement']}</th><th style="text-align:right;">${t['amount']}</th></tr>`;
            
            Object.entries(data).forEach(([name, value]) => {
                const numValue = parseFloat(value.replace(/,/g, '')) || 0;
                total = name.includes('利润') ? numValue : total;
                html += `<tr><td>${name}</td><td style="text-align:right;">¥${value}</td></tr>`;
            });
            
            html += `<tr class="report-total"><td><strong>${t['net-profit']}</strong></td><td style="text-align:right;font-weight:bold;">¥${total.toLocaleString()}</td></tr>`;
            html += '</table>';
            
            document.getElementById('profit-statement-content').innerHTML = html;
        }
        
        async function loadCashFlow() {
            try {
                const response = await fetch('http://localhost:8080/api/v1/finance/reports/cash-flow');
                const result = await response.json();
                if (result.success) {
                    renderCashFlowTable(result.data);
                }
            } catch (error) {
                document.getElementById('cash-flow-content').innerHTML = '<div style="text-align:center;color:#999;">加载失败</div>';
            }
        }
        
        function renderCashFlowTable(data) {
            const t = translations[currentLang];
            let html = '<table class="report-table">';
            
            html += `<tr><th>${t['cash-flow']}</th><th style="text-align:right;">${t['amount']}</th></tr>`;
            
            Object.entries(data).forEach(([name, value]) => {
                html += `<tr><td>${name}</td><td style="text-align:right;">¥${value}</td></tr>`;
            });
            
            html += '</table>';
            
            document.getElementById('cash-flow-content').innerHTML = html;
        }
        
        function toggleScanMode() {
            // 切换扫描模式
        }
        
        function clearScanData() {
            document.getElementById('scan-input').value = '';
            document.getElementById('scan-results').innerHTML = '';
        }
        
        function handleScanInput(event) {
            if (event.key === 'Enter') {
                const code = event.target.value.trim();
                if (code) {
                    // 处理扫描码
                    const results = document.getElementById('scan-results');
                    results.innerHTML += `<div style="padding:10px;border-bottom:1px solid #e0e0e0;">${code}</div>`;
                    event.target.value = '';
                }
            }
        }
        
        function handleDrop(event) {
            event.preventDefault();
            const file = event.dataTransfer.files[0];
            handleFile(file);
        }
        
        function handleFile(file) {
            if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
                alert(translations[currentLang]['supported-pdf'] || '请上传PDF文件');
                return;
            }
            uploadedFileName = file.name;
            uploadedFileSize = formatFileSize(file.size);
            simulateInvoiceRecognition();
        }
        
        function formatFileSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
        }
        
        function simulateInvoiceRecognition() {
            currentInvoiceInfo = {
                invoice_number: 'FP20240518001',
                invoice_date: new Date().toISOString().split('T')[0],
                total_amount: 10000.00,
                tax_amount: 1300.00,
                total_with_tax: 11300.00
            };
            loadModule('invoice');
        }
        
        function clearInvoice() {
            uploadedFileName = null;
            uploadedFileSize = null;
            currentInvoiceInfo = null;
            currentVoucherDraft = null;
            showVoucher = false;
            loadModule('invoice');
        }
        
        function loadSampleInvoice() {
            uploadedFileName = 'sample_invoice.pdf';
            uploadedFileSize = '256.5 KB';
            simulateInvoiceRecognition();
        }
        
        function generateInvoiceVoucher() {
            if (!currentInvoiceInfo) return;
            currentVoucherDraft = {
                debit: { '科目': '原材料', '金额': currentInvoiceInfo.total_amount },
                debit_tax: { '科目': '应交税费-进项税额', '金额': currentInvoiceInfo.tax_amount },
                credit: { '科目': '应付账款', '金额': currentInvoiceInfo.total_with_tax }
            };
            showVoucher = true;
            loadModule('invoice');
        }
        
        async function saveInvoiceVoucher() {
            if (!currentVoucherDraft || !currentInvoiceInfo) return;
            
            const voucherData = {
                voucher_type: '记',
                voucher_date: currentInvoiceInfo.invoice_date || new Date().toISOString().split('T')[0],
                attachments: 1,
                preparer: '系统自动生成',
                entries: [
                    { account_code: '1403', account_name: '原材料', debit: currentVoucherDraft.debit.金额, credit: null, summary: '购买原材料', auxiliary_info: null },
                    { account_code: '22210101', account_name: '应交税费-应交增值税-进项税额', debit: currentVoucherDraft.debit_tax.金额, credit: null, summary: '进项税额', auxiliary_info: null },
                    { account_code: '2202', account_name: '应付账款', debit: null, credit: currentVoucherDraft.credit.金额, summary: '应付货款', auxiliary_info: null }
                ]
            };
            
            try {
                const response = await fetch('http://localhost:8080/api/v1/finance/vouchers', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(voucherData)
                });
                const result = await response.json();
                if (result.success) {
                    alert('凭证保存成功！已同步到财务管理模块');
                    loadBalanceSheet();
                    loadProfitStatement();
                } else {
                    alert('保存失败：' + (result.message || '未知错误'));
                }
            } catch (error) {
                alert('保存失败，请检查API服务是否正常运行');
            }
        }
        
        function convertToChinese(amount) {
            const digits = ['零','壹','贰','叁','肆','伍','陆','柒','捌','玖'];
            const units = ['','拾','佰','仟','万','拾','佰','仟','亿'];
            const [integerPart, decimalPart] = amount.toFixed(2).split('.');
            let result = '';
            for (let i = 0; i < integerPart.length; i++) {
                const digit = parseInt(integerPart[i]);
                const unit = units[integerPart.length - 1 - i];
                if (digit === 0) {
                    if (result && result[result.length - 1] !== '零') result += '零';
                } else result += digits[digit] + unit;
            }
            if (result === '') result = '零';
            if (decimalPart === '00') result += '元整';
            else {
                result += '元';
                if (decimalPart[0] !== '0') result += digits[parseInt(decimalPart[0])] + '角';
                if (decimalPart[1] !== '0') result += digits[parseInt(decimalPart[1])] + '分';
            }
            return result;
        }
        
        function showVoucherForm() {
            // 显示凭证表单
        }
        
        function showAssetForm() {
            // 显示资产表单
        }
        
        async function loadAssets() {
            try {
                const response = await fetch('http://localhost:8080/api/v1/finance/fixed-assets');
                const result = await response.json();
                if (result.success) {
                    document.getElementById('asset-tbody').innerHTML = result.data.length ? 
                        result.data.map(a => `<tr><td>${a.asset_code}</td><td>${a.asset_name}</td><td>${a.category}</td><td>¥${a.original_value}</td><td>${getStatusText(a.status)}</td><td><button class="btn btn-secondary btn-sm">编辑</button></td></tr>`).join('') : 
                        '<tr><td colspan="6" style="text-align:center;color:#999;">暂无数据</td></tr>';
                }
            } catch (error) {
                document.getElementById('asset-tbody').innerHTML = '<tr><td colspan="6" style="text-align:center;color:#999;">加载失败</td></tr>';
            }
        }
        
        document.addEventListener('DOMContentLoaded', () => {
            loadModule('dashboard');
            // 延迟加载财务报表
            setTimeout(() => {
                if (currentModule === 'finance') {
                    loadBalanceSheet();
                    loadProfitStatement();
                    loadCashFlow();
                    loadAssets();
                }
            }, 500);
        });
    </script>
</body>
</html>"""

# 写入文件
output_path = r'c:\Users\ruancanling\Desktop\ERP VIBE CODING\frontend\index.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("新的index.html文件已创建！")