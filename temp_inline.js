(function(){
// ==============================
        // 🧭 全局配置（必须放在最前面，避免 ReferenceError）
        // ==============================
        const API_BASE = '/api/v1';
        // apiBase 兼容：代码中 69+ 处直接用了 apiBase 变量
        const apiBase = API_BASE;
        // authHeaders 兼容：代码中直接用 authHeaders 作为请求头部对象
        // （若后续启用 JWT 鉴权，在此读取 localStorage token 并注入 Authorization）
        const authHeaders = {
            'Accept': 'application/json',
        };

        let currentLang = 'zh';
        let currentModule = 'dashboard';
        let currentUser = null;
        
        let scanInputTimeout = null;
        const SCAN_TIMEOUT = 300;

        // 安全的Tab切换辅助函数（兼容移动端）
        function setActiveTab() {
            document.querySelectorAll('.finance-tab').forEach(btn => btn.classList.remove('active'));
            try {
                if (event && event.target) event.target.classList.add('active');
            } catch(e) {}
        }
        
        function initScanInput() {
            const scanInput = document.getElementById('scan-input');
            if (!scanInput) return;
            
            scanInput.removeEventListener('input', handleScanInput);
            scanInput.removeEventListener('keydown', handleScanKeydown);
            
            scanInput.addEventListener('input', handleScanInput);
            scanInput.addEventListener('keydown', handleScanKeydown);
        }
        
        function handleScanInput(e) {
            const scanInput = document.getElementById('scan-input');
            if (!scanInput) return;
            
            const code = scanInput.value.trim();
            if (!code) return;
            
            if (scanInputTimeout) {
                clearTimeout(scanInputTimeout);
            }
            
            scanInputTimeout = setTimeout(() => {
                processScanCode(code);
            }, SCAN_TIMEOUT);
        }
        
        function handleScanKeydown(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const scanInput = document.getElementById('scan-input');
                if (scanInput && scanInput.value.trim()) {
                    processScanCode(scanInput.value.trim());
                }
            }
        }
        
        function clearScanInput() {
            const scanInput = document.getElementById('scan-input');
            if (scanInput) {
                scanInput.value = '';
                scanInput.focus();
            }
        }
        
        async function processScanCode(code) {
            const scanInput = document.getElementById('scan-input');
            if (scanInput) {
                scanInput.style.borderColor = '#27ae60';
                scanInput.placeholder = '正在查询...';
            }
            
            try {
                const response = await fetch(`/api/v1/materials/search?q=${encodeURIComponent(code)}`);
                const result = await response.json();
                
                if (result.success && result.data) {
                    loadModule('materials');
                    setTimeout(() => {
                        showMaterialDetail(result.data);
                    }, 300);
                    
                    if (scanInput) {
                        scanInput.value = '';
                        scanInput.style.borderColor = '#ccc';
                        scanInput.placeholder = '扫描二维码...';
                        scanInput.focus();
                    }
                } else {
                    if (scanInput) {
                        scanInput.style.borderColor = '#e74c3c';
                        scanInput.placeholder = '未找到物料，重新扫描';
                    }
                    setTimeout(() => {
                        if (scanInput) {
                            scanInput.value = '';
                            scanInput.style.borderColor = '#ccc';
                            scanInput.placeholder = '扫描二维码...';
                            scanInput.focus();
                        }
                    }, 2000);
                }
            } catch (error) {
                if (scanInput) {
                    scanInput.style.borderColor = '#e74c3c';
                    scanInput.placeholder = '查询失败: ' + error.message;
                }
                setTimeout(() => {
                    if (scanInput) {
                        scanInput.value = '';
                        scanInput.style.borderColor = '#ccc';
                        scanInput.placeholder = '扫描二维码...';
                        scanInput.focus();
                    }
                }, 2000);
            }
        }
        
        function showMaterialDetail(material) {
            const content = document.getElementById('materials-content');
            const t = translations[currentLang];
            
            const detailHtml = `
                <div class="card">
                    <div class="card-title">📦 物料详情 - ${material.name}</div>
                    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:20px;">
                        <div><strong>物料编码:</strong> ${material.code}</div>
                        <div><strong>物料名称:</strong> ${material.name}</div>
                        <div><strong>二维码:</strong> ${material.barcode || '-'}</div>
                        <div><strong>规格型号:</strong> ${material.spec || '-'}</div>
                        <div><strong>计量单位:</strong> ${material.unit}</div>
                        <div><strong>物料类型:</strong> ${material.type === 'RAW_MATERIAL' ? '原材料' : material.type === 'SEMI_FINISHED' ? '半成品' : '成品'}</div>
                        <div><strong>物料属性:</strong> ${material.property === 'PURCHASE' ? '采购' : material.property === 'OUTSOURCING' ? '委外' : '自制'}</div>
                        <div><strong>单价:</strong> ${material.unit_price}</div>
                        <div><strong>提前期:</strong> ${material.lead_time || 0} 天</div>
                        <div><strong>安全库存:</strong> ${material.safety_stock || 0}</div>
                        <div><strong>批量规则:</strong> ${material.batch_rule || 'FIXED'}</div>
                        <div><strong>批量大小:</strong> ${material.batch_size || 1}</div>
                        <div><strong>损耗率:</strong> ${material.loss_rate || 0}%</div>
                        <div><strong>HS编码:</strong> ${material.hs_code || '-'}</div>
                        <div><strong>描述:</strong> ${material.description || '-'}</div>
                    </div>
                    <button class="btn btn-secondary" onclick="renderMaterialsTab('inventory')" style="margin-top:20px;">返回库存管理</button>
                </div>
            `;
            
            content.innerHTML = detailHtml;
        }
        
        const translations = {
            'zh': {
                'dashboard-title': '系统', 'dashboard-desc': '欢迎使用ERP系统',
                'materials-title': '物料管理', 'materials-desc': '管理企业物料库存',
                'sales-title': '销售管理', 'sales-desc': '销售订单、发货通知、销售出库',
                'plan-title': '计划管理', 'plan-desc': '预测单、MRP运算、计划订单',
                'purchase-title': '采购管理', 'purchase-desc': '采购订单管理',
                'production-title': '生产管理', 'production-desc': '生产订单管理',
                'finance-title': '财务管理', 'finance-desc': '总账、应收应付、出纳、固定资产、工资、报表',
                'finance-general': '总账管理', 'finance-arap': '应收应付', 'finance-cash': '出纳管理',
                'finance-asset': '固定资产', 'finance-payroll': '工资管理', 'finance-reports': '财务报表',
                'crossborder-title': '跨境合规', 'crossborder-desc': '跨境贸易合规',
                'scanning-title': '扫码录入', 'scanning-desc': '扫描二维码生成凭证',
                'invoice-title': '发票识别', 'invoice-desc': '上传PDF发票识别',
                'total-materials': '物料总数', 'purchase-orders': '采购订单',
                'production-orders': '生产订单', 'compliance-alerts': '合规预警',
                'name': '名称', 'code': '编码', 'unit': '单位', 'price': '单价',
                'status': '状态', 'action': '操作', 'view': '查看', 'edit': '编辑',
                'delete': '删除', 'PO-no': '采购单号', 'supplier': '供应商',
                'material': '物料', 'quantity': '数量', 'work-order-no': '工单号',
                'product': '产品', 'hs-code': 'HS编码', 'description': '商品描述',
                'country': '目的地', 'declared-value': '申报价值', 'tax-estimate': '预估税费',
                'scan-input-placeholder': '请扫描二维码...', 'batch-mode': '批量模式',
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
                'add': '添加', 'update-success': '更新成功', 'update-failed': '更新失败',
                'username': '用户名', 'password': '密码', 'confirm-password': '确认密码',
                'email': '邮箱', 'phone': '手机号', 'login': '登录', 'register': '注册',
                'login-success': '登录成功', 'login-failed': '登录失败',
                'register-success': '注册成功', 'register-failed': '注册失败',
                'logout-success': '退出成功', 'no-account': '还没有账号？', 'has-account': '已有账号？',
                'register-now': '立即注册', 'login-now': '立即登录', 'welcome': '欢迎使用',
                'system-title': '系统', 'system-desc': '欢迎使用ERP系统',
                'no-data': '暂无数据', 'loading': '加载中...', 'logout': '退出'
            },
            'en': {
                'dashboard-title': 'System', 'dashboard-desc': 'Welcome to ERP',
                'materials-title': 'Materials', 'materials-desc': 'Manage inventory',
                'sales-title': 'Sales', 'sales-desc': 'Sales orders, delivery, shipping',
                'plan-title': 'Planning', 'plan-desc': 'Forecast, MRP, Planned orders',
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
                'scan-input-placeholder': 'Scan QR code...', 'batch-mode': 'Batch Mode',
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
                'add': 'Add', 'update-success': 'Update Success', 'update-failed': 'Update Failed',
                'username': 'Username', 'password': 'Password', 'confirm-password': 'Confirm Password',
                'email': 'Email', 'phone': 'Phone', 'login': 'Login', 'register': 'Register',
                'login-success': 'Login Success', 'login-failed': 'Login Failed',
                'register-success': 'Register Success', 'register-failed': 'Register Failed',
                'logout-success': 'Logout Success', 'no-account': 'No account?', 'has-account': 'Already have an account?',
                'register-now': 'Register Now', 'login-now': 'Login Now', 'welcome': 'Welcome',
                'system-title': 'System', 'system-desc': 'Welcome to ERP',
                'no-data': 'No Data', 'loading': 'Loading...', 'logout': 'Logout'
            }
        };
        
        function changeLang(lang) {
            currentLang = lang;
            document.querySelectorAll('.lang-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            updateLoginUI();
            if (currentUser) {
                loadModule(currentModule);
            }
        }
        
        function updateLoginUI() {
            const t = translations[currentLang];
            document.getElementById('login-subtitle').textContent = t['welcome'] + ' ' + t['system-desc'];
            document.getElementById('username-label').textContent = t['username'];
            document.getElementById('password-label').textContent = t['password'];
            document.getElementById('login-btn').textContent = t['login'];
            document.getElementById('no-account').textContent = t['no-account'];
            document.getElementById('register-link').textContent = t['register-now'];
        }
        
        function showRegisterForm() {
            const t = translations[currentLang];
            const loginBox = document.querySelector('.login-box');
            loginBox.innerHTML = `
                <h2 class="login-title">ERP系统</h2>
                <p class="login-subtitle">${t['register']}</p>
                <form class="login-form" id="register-form">
                    <div class="form-group">
                        <label>${t['username']}</label>
                        <input type="text" id="reg-username" required>
                    </div>
                    <div class="form-group">
                        <label>${t['password']}</label>
                        <input type="password" id="reg-password" required>
                    </div>
                    <div class="form-group">
                        <label>${t['confirm-password']}</label>
                        <input type="password" id="reg-confirm-password" required>
                    </div>
                    <div class="form-group">
                        <label>${t['email']}</label>
                        <input type="email" id="reg-email">
                    </div>
                    <div class="form-group">
                        <label>${t['phone']}</label>
                        <input type="tel" id="reg-phone">
                    </div>
                    <button type="submit" class="login-btn">${t['register']}</button>
                    <div id="register-message"></div>
                </form>
                <div class="login-footer">
                    <span>${t['has-account']}</span>
                    <a href="#" onclick="showLoginForm()">${t['login-now']}</a>
                </div>
            `;
            
            document.getElementById('register-form').addEventListener('submit', handleRegister);
        }
        
        function showLoginForm() {
            const t = translations[currentLang];
            const loginBox = document.querySelector('.login-box');
            loginBox.innerHTML = `
                <h2 class="login-title">ERP系统</h2>
                <p class="login-subtitle" id="login-subtitle">${t['welcome']} ${t['system-desc']}</p>
                <form class="login-form" id="login-form">
                    <div class="form-group">
                        <label id="username-label">${t['username']}</label>
                        <input type="text" id="login-username" required>
                    </div>
                    <div class="form-group">
                        <label id="password-label">${t['password']}</label>
                        <input type="password" id="login-password" required>
                    </div>
                    <button type="submit" class="login-btn" id="login-btn">${t['login']}</button>
                    <div id="login-message"></div>
                </form>
                <div class="login-footer">
                    <span id="no-account">${t['no-account']}</span>
                    <a href="#" id="register-link" onclick="showRegisterForm()">${t['register-now']}</a>
                </div>
            `;
            
            document.getElementById('login-form').addEventListener('submit', handleLogin);
        }
        
        async function handleLogin(event) {
            event.preventDefault();
            const t = translations[currentLang];
            const username = document.getElementById('login-username').value;
            const password = document.getElementById('login-password').value;
            const messageDiv = document.getElementById('login-message');
            
            try {
                const response = await fetch('/api/v1/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    currentUser = result.data;
                    localStorage.setItem('currentUser', JSON.stringify(currentUser));
                    messageDiv.innerHTML = `<div class="success-message">${t['login-success']}</div>`;
                    setTimeout(() => {
                        showMainApp();
                    }, 1000);
                } else {
                    messageDiv.innerHTML = `<div class="error-message">${t['login-failed']}: ${result.message}</div>`;
                }
            } catch (error) {
                messageDiv.innerHTML = `<div class="error-message">${t['login-failed']}: ${error.message}</div>`;
            }
        }
        
        async function handleRegister(event) {
            event.preventDefault();
            const t = translations[currentLang];
            const username = document.getElementById('reg-username').value;
            const password = document.getElementById('reg-password').value;
            const confirmPassword = document.getElementById('reg-confirm-password').value;
            const email = document.getElementById('reg-email').value;
            const phone = document.getElementById('reg-phone').value;
            const messageDiv = document.getElementById('register-message');
            
            if (password !== confirmPassword) {
                messageDiv.innerHTML = `<div class="error-message">密码不一致</div>`;
                return;
            }
            
            try {
                const response = await fetch('/api/v1/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password, email, phone })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    messageDiv.innerHTML = `<div class="success-message">${t['register-success']}</div>`;
                    setTimeout(() => {
                        showLoginForm();
                    }, 2000);
                } else {
                    messageDiv.innerHTML = `<div class="error-message">${t['register-failed']}: ${result.message}</div>`;
                }
            } catch (error) {
                messageDiv.innerHTML = `<div class="error-message">${t['register-failed']}: ${error.message}</div>`;
            }
        }
        
        // 全局 click 监听器（只绑定一次！避免重复登录导致监听器越积越多）
        let _globalClickListenerInstalled = false;
        function installGlobalClickFocusScanInput() {
            if (_globalClickListenerInstalled) return;
            _globalClickListenerInstalled = true;
            document.addEventListener('click', () => {
                try {
                    const scanInput = document.getElementById('scan-input');
                    if (!scanInput) return;
                    const tag = (document.activeElement && document.activeElement.tagName || '').toUpperCase();
                    if (tag !== 'INPUT' && tag !== 'TEXTAREA' && tag !== 'SELECT' && !scanInput.disabled) {
                        scanInput.focus({ preventScroll: true });
                    }
                } catch (e) { /* ignore */ }
            });
        }

        function showMainApp() {
            try {
                const loginPage = document.getElementById('login-page');
                const mainApp   = document.getElementById('main-app');
                const userNameEl= document.getElementById('current-user-name');
                if (loginPage) loginPage.style.display = 'none';
                if (mainApp)   mainApp.style.display   = 'block';
                if (userNameEl && currentUser) userNameEl.textContent = currentUser.username || '';
                // 先加载 dashboard（成功/失败都确保不崩）
                try {
                    loadModule('dashboard');
                } catch (e) {
                    console.error('[showMainApp] loadModule(dashboard) failed:', e);
                    const content = document.getElementById('content');
                    if (content) content.innerHTML =
                        '<div class="card"><div class="card-title">欢迎使用 ERP智能系统</div>' +
                        '<p style="padding:16px;">已成功登录，可从左侧菜单选择功能模块。</p></div>';
                }
                setTimeout(() => {
                    try { initScanInput(); } catch (e) {}
                    try {
                        const scanInput = document.getElementById('scan-input');
                        if (scanInput) scanInput.focus();
                    } catch (e) {}
                }, 500);
                // 全局 click 聚焦扫码输入（一次性绑定）
                installGlobalClickFocusScanInput();
            } catch (err) {
                console.error('[showMainApp] FATAL:', err);
                // 兜底：至少显示"已成功登录"，不让用户白屏
                try {
                    const loginPage = document.getElementById('login-page');
                    const mainApp   = document.getElementById('main-app');
                    if (loginPage) loginPage.style.display = 'none';
                    if (mainApp)   mainApp.style.display   = 'block';
                    const content = document.getElementById('content');
                    if (content) content.innerHTML =
                        '<div class="card"><div class="card-title">✅ 登录成功</div>' +
                        '<p style="padding:16px;">欢迎 <b>' + (currentUser && currentUser.username ? currentUser.username : '') + '</b>，请从左侧菜单选择功能模块。</p></div>';
                } catch (_) {}
            }
        }
        
        function logout() {
            const t = translations[currentLang];
            currentUser = null;
            localStorage.removeItem('currentUser');
            document.getElementById('main-app').style.display = 'none';
            document.getElementById('login-page').style.display = 'flex';
            showLoginForm();
        }
        
        function loadModule(module) {
            currentModule = module;
            // 稳健的 active 高亮切换：不用 onclick 属性选择器（移动端/Safari 可能序列化差异）
            const sidebarBtns = document.querySelectorAll('.sidebar-menu button');
            sidebarBtns.forEach(btn => {
                btn.classList.remove('active');
                // 按钮 textContent 末尾或 onclick 字符串中匹配模块名即可
                const attrs = (btn.getAttribute('onclick') || '') + '|' + (btn.textContent || '');
                if (attrs.indexOf("'" + module + "'") !== -1 || attrs.indexOf('"' + module + '"') !== -1) {
                    btn.classList.add('active');
                }
            });

            const content = document.getElementById('content');
            if (!content) return;
            try {
                switch(module) {
                    case 'dashboard':  content.innerHTML = renderDashboard();  break;
                    case 'materials':  content.innerHTML = renderMaterials();  break;
                    case 'sales':      content.innerHTML = renderSales();      break;
                    case 'plan':       content.innerHTML = renderPlan();       break;
                    case 'purchase':   content.innerHTML = renderPurchase();   break;
                    case 'production': content.innerHTML = renderProduction(); break;
                    case 'finance':    content.innerHTML = renderFinance();    break;
                    case 'crossborder':content.innerHTML = renderCrossborder();break;
                    case 'scanning':   content.innerHTML = renderScanning();   break;
                    case 'invoice':    content.innerHTML = renderInvoice();    break;
                    default:
                        content.innerHTML = '<div class="card"><div class="card-title">提示</div>' +
                                            '<p style="padding:16px;">未知模块：' + module + '</p></div>';
                }
            } catch (err) {
                console.error('[loadModule] error:', module, err);
                content.innerHTML =
                    '<div class="card"><div class="card-title">加载失败</div>' +
                    '<p style="padding:16px;color:#c0392b;">模块 "' + module + '" 加载出错，请刷新页面重试。</p>' +
                    '<pre style="background:#f8f9fa;padding:12px;font-size:12px;color:#666;">' +
                    (err && err.message ? err.message : err) + '</pre></div>';
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
                'scrapped': translations[currentLang]['scrapped'],
                'approved': '已审批',
                'delivery_created': '已创建发货通知',
                'pending_production': '待生产',
                'confirmed': '已确认',
                'available': '可用',
                'frozen': '冻结'
            };
            return texts[status.toLowerCase()] || status;
        }
        
        function renderDashboard() {
            const t = translations[currentLang];
            return `
                <div class="content-header"><h2>${t['system-title']}</h2><p>${t['system-desc']}</p></div>
                <div class="card">
                    <div class="card-title">${t['system-title']}</div>
                    <div style="text-align:center;padding:40px;color:#7f8c8d;">
                        <p>${t['no-data']}</p>
                        <p style="margin-top:10px;">${t['welcome']}</p>
                    </div>
                </div>
            `;
        }
        
        function renderMaterials() {
            const t = translations[currentLang];
            return `<div class="content-header"><h2>${t['materials-title']}</h2><p>${t['materials-desc']}</p></div>
                <div class="finance-tabs">
                    <button class="finance-tab active" onclick="renderMaterialsTab('inventory', this)">库存管理</button>
                    <button class="finance-tab" onclick="renderMaterialsTab('scanning', this)">扫码录入</button>
                    <button class="finance-tab" onclick="renderMaterialsTab('quality', this)">质检管理</button>
                    <button class="finance-tab" onclick="renderMaterialsTab('inbound', this)">入库管理</button>
                    <button class="finance-tab" onclick="renderMaterialsTab('outbound', this)">出库管理</button>
                </div>
                <div id="materials-content">${renderMaterialsInventory()}</div>`;
        }
        
        function renderMaterialsTab(tab, btnEl) {
            document.querySelectorAll('.finance-tab').forEach(btn => btn.classList.remove('active'));
            if (btnEl) btnEl.classList.add('active');
            else if (event && event.target) event.target.classList.add('active');
            
            const content = document.getElementById('materials-content');
            switch(tab) {
                case 'inventory': content.innerHTML = renderMaterialsInventory(); break;
                case 'scanning': content.innerHTML = renderMaterialsScanning(); setTimeout(initScanInputForMaterials, 100); break;
                case 'quality': content.innerHTML = renderMaterialsQuality(); break;
                case 'inbound': content.innerHTML = renderMaterialsInbound(); break;
                case 'outbound': content.innerHTML = renderMaterialsOutbound(); break;
            }
        }
        
        let scanRecords = [];
        let materialScanTimeout = null;
        let globalScanBuffer = '';
        let globalScanTimer = null;
        let globalScanListenerInstalled = false;

        function renderMaterialsScanning() {
            const matchedCount = scanRecords.filter(r => r.id).length;
            const unmatchedCount = scanRecords.filter(r => !r.id).length;
            return `<div class="card">
                <div class="card-title">扫码录入 - 采购入库</div>
                <div style="margin-bottom:15px;padding:15px;background:#f0f7ff;border-radius:8px;border:1px solid #d0e3ff;">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap;">
                        <span style="font-weight:bold;color:#333;font-size:15px;">🔍 扫码输入:</span>
                        <input type="text" id="material-scan-input" placeholder="扫码枪自动扫描 / 手动输入后回车..."
                            style="flex:1;padding:10px;font-size:16px;border:2px solid #3498db;border-radius:6px;outline:none;background:#fffbe7;font-weight:bold;color:#222;min-width:150px;"
                            autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false">
                        <button class="btn btn-primary" onclick="scanMaterialManually()">添加</button>
                        <button class="btn btn-secondary" onclick="clearScanRecords()">清空</button>
                        <button class="btn" onclick="openMobileScanner()" style="background:#27ae60;color:white;border-color:#27ae60;">📷 手机扫码</button>
                    </div>
                    <div id="scan-debug-info" style="font-size:13px;color:#2c3e50;padding:6px 8px;background:#ecf0f1;border-radius:4px;"></div>
                    <div style="font-size:12px;color:#555;margin-top:8px;">
                        💡 扫码枪配置：本页已开启<b>全局键盘监听</b>，无论焦点在何处，扫码枪扫描后自动录入。<br>
                        📌 扫到的内容<b>无论是否匹配到现有物料都会加入列表</b>，未匹配的物料可点击"新建物料"按钮创建。
                    </div>
                </div>
                <div style="display:flex;gap:10px;margin-bottom:15px;align-items:center;flex-wrap:wrap;">
                    <button class="btn btn-success" onclick="submitScanRecords()" style="font-size:15px;padding:10px 25px;">✅ 确认入库 (仅匹配项)</button>
                    <button class="btn btn-primary" onclick="showBarcodePrintModal()" style="font-size:15px;padding:10px 25px;">🖨️ 打印二维码标签</button>
                    <button class="btn btn-secondary" onclick="showNewMaterialModal()" style="font-size:15px;padding:10px 25px;">➕ 新增物料</button>
                    <span style="font-size:14px;color:#27ae60;">✅ 已匹配: ${matchedCount}</span>
                    <span style="font-size:14px;color:#e67e22;">⚠️ 未匹配: ${unmatchedCount}</span>
                    <span style="font-size:14px;color:#333;">📊 总计: ${scanRecords.length}</span>
                </div>
                <table class="data-table">
                    <thead><tr><th>序号</th><th>状态</th><th>二维码</th><th>物料编码</th><th>物料名称</th><th>规格</th><th>单位</th><th>数量</th><th>单价</th><th>操作</th></tr></thead>
                    <tbody id="scan-records-tbody">${scanRecords.length > 0 ? renderScanRecords() : `<tr><td colspan="10" style="text-align:center;padding:30px;color:#7f8c8d;">等待扫码枪输入，请扫描二维码...</td></tr>`}</tbody>
                </table>
            </div>`;
        }

        function renderScanRecords() {
            return scanRecords.map((r, i) => {
                const isMatched = !!r.id;
                const statusBadge = isMatched
                    ? `<span style="background:#e8f8f0;color:#27ae60;padding:3px 8px;border-radius:10px;font-size:12px;font-weight:bold;">✅ 已匹配</span>`
                    : `<span style="background:#fff4e5;color:#e67e22;padding:3px 8px;border-radius:10px;font-size:12px;font-weight:bold;">⚠️ 未建档</span>`;
                const actions = isMatched
                    ? `<button class="btn btn-danger btn-sm" onclick="removeScanRecord(${i})">删除</button>`
                    : `<button class="btn btn-primary btn-sm" onclick="createFromUnmatched(${i})" style="background:#e67e22;border-color:#e67e22;">新建物料</button>
                       <button class="btn btn-danger btn-sm" onclick="removeScanRecord(${i})">删除</button>`;
                const rowBg = isMatched ? '' : 'background:#fff8f0;';
                return `
                <tr style="${rowBg}">
                    <td>${i + 1}</td>
                    <td>${statusBadge}</td>
                    <td style="font-family:monospace;font-weight:bold;">${r.barcode || '-'}</td>
                    <td>${r.code || '-'}</td>
                    <td>${r.name || '<span style="color:#999;">(未命名)</span>'}</td>
                    <td>${r.spec || '-'}</td>
                    <td>${r.unit || '-'}</td>
                    <td><input type="number" value="${r.qty || 1}" min="1" onchange="updateScanQty(${i}, this.value)" style="width:60px;padding:4px;text-align:center;border:1px solid #ddd;border-radius:4px;"></td>
                    <td>${r.unit_price || 0}</td>
                    <td>${actions}</td>
                </tr>
            `}).join('');
        }

        function initScanInputForMaterials() {
            // 1. 输入框监听（扫码专用输入框）
            const si = document.getElementById('material-scan-input');
            if (si) {
                si.removeEventListener('input', handleMaterialScanInput);
                si.removeEventListener('keydown', handleMaterialScanKeydown);
                si.addEventListener('input', handleMaterialScanInput);
                si.addEventListener('keydown', handleMaterialScanKeydown);
                si.focus();
            }
            // 2. 全局扫码监听：已由 installGlobalScannerListener() 在页面加载时自动安装
            //    （不再需要此处重复安装）
            // 3. 点击页面任意空白处自动聚焦输入框
            document.onclick = function(e) {
                if (!e.target.closest('button') && !e.target.closest('input') && !e.target.closest('select') && !e.target.closest('a')) {
                    const si2 = document.getElementById('material-scan-input');
                    if (si2) si2.focus();
                }
            };
            showScanDebug('✅ 扫码枪已就绪！<span style="color:#27ae60;">无论在ERP哪个页面扫码，都会自动跳转到此处记录数据。</span> 任意内容（哪怕1个数字）都会被录入。');
        }

        function handleGlobalKeydown(e) {
            // 旧版全局监听已停用，改用 installGlobalScannerListener()（页面加载即生效）
            // 此处保留以兼容旧代码引用，但不做任何操作
            return;
        }

        function handleMaterialScanInput(e) {
            const si = document.getElementById('material-scan-input');
            if (!si) return;
            const code = si.value.trim();
            if (!code) return;
            if (materialScanTimeout) clearTimeout(materialScanTimeout);
            materialScanTimeout = setTimeout(() => processMaterialScan(code), 200);
        }

        function handleMaterialScanKeydown(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const si = document.getElementById('material-scan-input');
                if (si && si.value.trim()) processMaterialScan(si.value.trim());
            }
        }

        function showScanDebug(msg) {
            const d = document.getElementById('scan-debug-info');
            if (d) d.innerHTML = msg;
        }

        async function processMaterialScan(code) {
            const cleanCode = String(code || '').trim();
            if (!cleanCode) return;
            const si = document.getElementById('material-scan-input');
            if (si) { si.value = ''; si.focus(); si.style.borderColor = '#27ae60'; }
            showScanDebug(`<b>📡 已接收扫码数据:</b> <span style="font-family:monospace;color:#2980b9;">${cleanCode}</span> <span style="color:#7f8c8d;">（长度: ${cleanCode.length}）</span> — 正在查询ERP...`);
            try {
                const res = await fetch(`/api/v1/materials/search?q=${encodeURIComponent(cleanCode)}`);
                const result = await res.json();
                if (result.success && result.data) {
                    addMatchedRecord(result.data);
                    showScanDebug(`<b>✅ 匹配成功!</b> 物料: ${result.data.name}（编码: ${result.data.code}），已加入入库清单。`);
                } else {
                    addUnmatchedRecord(cleanCode);
                    showScanDebug(`<b>⚠️ 未在ERP中建档:</b> <span style="font-family:monospace;">${cleanCode}</span>，已加入清单（<span style="color:#e67e22;">点击"新建物料"可创建档案</span>）`);
                    if (si) si.style.borderColor = '#e67e22';
                }
            } catch (err) {
                addUnmatchedRecord(cleanCode);
                showScanDebug(`<b>⚠️ 查询异常:</b> ${err.message}，已记录扫码内容 "${cleanCode}" 到清单。`);
            }
        }

        function addMatchedRecord(m) {
            const idx = scanRecords.findIndex(r => r.id === m.id);
            if (idx >= 0) {
                scanRecords[idx].qty = (scanRecords[idx].qty || 1) + 1;
            } else {
                scanRecords.push({
                    id: m.id,
                    barcode: m.barcode || m.code,
                    code: m.code,
                    name: m.name,
                    spec: m.spec,
                    unit: m.unit,
                    unit_price: m.unit_price || 0,
                    qty: 1,
                    matched: true
                });
            }
            updateScanRecordsTable();
        }

        function addUnmatchedRecord(barcode) {
            const idx = scanRecords.findIndex(r => !r.id && r.barcode === barcode);
            if (idx >= 0) {
                scanRecords[idx].qty = (scanRecords[idx].qty || 1) + 1;
            } else {
                scanRecords.push({
                    id: null,
                    barcode: barcode,
                    code: '',
                    name: '',
                    spec: '',
                    unit: '个',
                    unit_price: 0,
                    qty: 1,
                    matched: false
                });
            }
            updateScanRecordsTable();
        }

        // ========== 手机摄像头扫码功能 ==========
        let mobileScannerActive = false;
        let mobileScannerStream = null;
        let mobileScannerAnimationId = null;

        function hasQRCapability() {
            return (typeof jsQR !== 'undefined') || ('BarcodeDetector' in window);
        }

        function decodeQRFromImageData(imageData, width, height) {
            // 优先用 jsQR 库
            if (typeof jsQR !== 'undefined') {
                return jsQR(imageData.data, width, height, { inversionAttempts: 'attemptBoth' });
            }
            // 备用：用 BarcodeDetector（异步）
            return null; // 由调用方处理异步
        }

        async function detectQRWithBarcodeDetector(imageData, width, height) {
            if (!('BarcodeDetector' in window)) return null;
            try {
                const canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');
                ctx.putImageData(imageData, 0, 0);
                const detector = new BarcodeDetector({ formats: ['qr_code'] });
                const codes = await detector.detect(canvas);
                if (codes && codes.length > 0) return codes[0].rawValue;
                return null;
            } catch(e) { return null; }
        }

        function openMobileScanner() {
            if (!hasQRCapability()) {
                alert('二维码识别功能不可用。请使用Chrome/Edge浏览器，或检查网络连接后刷新页面。');
                return;
            }
            const modal = document.createElement('div');
            modal.id = 'mobile-scanner-modal';
            modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.92);z-index:99999;display:flex;flex-direction:column;justify-content:center;align-items:center;';
            modal.innerHTML = `
                <div style="width:100%;max-width:500px;padding:20px;color:white;text-align:center;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;">
                        <h3 style="margin:0;color:white;font-size:18px;">📷 手机扫码录入</h3>
                        <button onclick="closeMobileScanner()" style="border:none;background:rgba(255,255,255,0.2);color:white;font-size:24px;cursor:pointer;width:36px;height:36px;border-radius:50%;">&times;</button>
                    </div>
                    <div style="position:relative;width:100%;aspect-ratio:1;max-width:350px;margin:0 auto;background:#000;border-radius:12px;overflow:hidden;border:2px solid #3498db;">
                        <video id="scanner-video" autoplay playsinline muted style="width:100%;height:100%;object-fit:cover;"></video>
                        <canvas id="scanner-canvas" style="display:none;"></canvas>
                        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:70%;height:60%;border:3px solid #27ae60;border-radius:8px;pointer-events:none;"></div>
                        <div id="scanner-status" style="position:absolute;bottom:10px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,0.7);color:white;padding:6px 14px;border-radius:20px;font-size:13px;white-space:nowrap;">准备扫描二维码...</div>
                    </div>
                    <div style="margin-top:20px;">
                        <label style="display:inline-block;background:#3498db;color:white;padding:12px 24px;border-radius:8px;cursor:pointer;font-size:15px;font-weight:bold;">
                            📸 拍照/选图片识别
                            <input type="file" accept="image/*" capture="environment" style="display:none;" onchange="handlePhotoScan(event)">
                        </label>
                    </div>
                    <div style="margin-top:12px;font-size:12px;color:rgba(255,255,255,0.6);">
                        💡 支持摄像头实时扫描，也可拍照或从相册选择图片识别<br>
                        ⚠️ 若摄像头无法打开（非HTTPS环境），请使用拍照识别
                    </div>
                    <div id="scanner-history" style="margin-top:15px;text-align:left;"></div>
                </div>
            `;
            document.body.appendChild(modal);
            startCameraScan();
        }

        function closeMobileScanner() {
            mobileScannerActive = false;
            if (mobileScannerStream) {
                mobileScannerStream.getTracks().forEach(t => t.stop());
                mobileScannerStream = null;
            }
            if (mobileScannerAnimationId) {
                cancelAnimationFrame(mobileScannerAnimationId);
                mobileScannerAnimationId = null;
            }
            const modal = document.getElementById('mobile-scanner-modal');
            if (modal) modal.remove();
        }

        async function startCameraScan() {
            const video = document.getElementById('scanner-video');
            const status = document.getElementById('scanner-status');
            if (!video) return;

            // 检测是否HTTPS或localhost（getUserMedia需要）
            const isSecure = location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1';
            
            if (!isSecure) {
                status.innerHTML = '📷 非安全连接，摄像头可能无法使用<br>请使用下方【拍照识别】按钮';
                return;
            }

            try {
                mobileScannerStream = await navigator.mediaDevices.getUserMedia({
                    video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
                    audio: false
                });
                video.srcObject = mobileScannerStream;
                mobileScannerActive = true;
                status.textContent = '对准二维码进行扫描...';
                requestAnimationFrame(tickCameraScan);
            } catch (err) {
                status.innerHTML = '📷 摄像头访问被拒绝或不可用<br>请使用下方【拍照识别】按钮<br><span style="font-size:11px;">' + err.message + '</span>';
            }
        }

        function tickCameraScan() {
            if (!mobileScannerActive) return;
            const video = document.getElementById('scanner-video');
            const canvas = document.getElementById('scanner-canvas');
            if (!video || !canvas || video.readyState !== video.HAVE_ENOUGH_DATA) {
                mobileScannerAnimationId = requestAnimationFrame(tickCameraScan);
                return;
            }
            const ctx = canvas.getContext('2d', { willReadFrequently: true });
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            
            // 尝试 jsQR
            let code = decodeQRFromImageData(imageData, canvas.width, canvas.height);
            if (code && code.data) {
                handleScannedCode(code.data);
                mobileScannerAnimationId = requestAnimationFrame(tickCameraScan);
                return;
            }
            
            // 备用：BarcodeDetector（异步）
            if ('BarcodeDetector' in window && typeof jsQR === 'undefined') {
                detectQRWithBarcodeDetector(imageData, canvas.width, canvas.height).then(text => {
                    if (text) handleScannedCode(text);
                });
            }
            
            mobileScannerAnimationId = requestAnimationFrame(tickCameraScan);
        }

        async function handlePhotoScan(event) {
            const file = event.target.files[0];
            if (!file) return;
            event.target.value = '';
            const status = document.getElementById('scanner-status');
            status.textContent = '正在识别图片中的二维码...';
            try {
                const result = await decodeQRFromFile(file);
                if (result) {
                    handleScannedCode(result);
                } else {
                    status.innerHTML = '<span style="color:#e74c3c;">❌ 未在图片中检测到二维码，请调整角度后重试</span>';
                }
            } catch (err) {
                status.innerHTML = '<span style="color:#e74c3c;">❌ 识别失败: ' + err.message + '</span>';
            }
        }

        function decodeQRFromFile(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const img = new Image();
                    img.onload = function() {
                        const canvas = document.createElement('canvas');
                        // 缩小图片提高识别速度
                        const maxDim = 800;
                        let w = img.width, h = img.height;
                        if (w > maxDim || h > maxDim) {
                            if (w > h) { h = h * maxDim / w; w = maxDim; }
                            else { w = w * maxDim / h; h = maxDim; }
                        }
                        canvas.width = w;
                        canvas.height = h;
                        const ctx = canvas.getContext('2d');
                        ctx.drawImage(img, 0, 0, w, h);
                        const imageData = ctx.getImageData(0, 0, w, h);
                        // 尝试 jsQR
                        const code = decodeQRFromImageData(imageData, w, h);
                        if (code && code.data) {
                            resolve(code.data);
                        } else {
                            // 备用：BarcodeDetector
                            detectQRWithBarcodeDetector(imageData, w, h).then(text => {
                                resolve(text);
                            });
                        }
                    };
                    img.onerror = () => reject(new Error('图片加载失败'));
                    img.src = e.target.result;
                };
                reader.onerror = () => reject(new Error('文件读取失败'));
                reader.readAsDataURL(file);
            });
        }

        function handleScannedCode(code) {
            const status = document.getElementById('scanner-status');
            status.innerHTML = '<span style="color:#27ae60;">✅ 扫描成功!</span> 正在添加到清单...';
            // 震动反馈（支持的设备）
            if (navigator.vibrate) navigator.vibrate(100);
            // 调用已有的处理函数
            processMaterialScan(code);
            // 显示历史记录
            const history = document.getElementById('scanner-history');
            if (history) {
                const time = new Date().toLocaleTimeString();
                history.innerHTML += `<div style="background:rgba(255,255,255,0.1);padding:8px;margin-top:5px;border-radius:6px;font-size:13px;"><span style="color:#95a5a6;">${time}</span> <span style="font-family:monospace;color:#2ecc71;">${code}</span> ✅ 已添加</div>`;
                history.scrollTop = history.scrollHeight;
            }
            // 2秒后恢复扫描
            setTimeout(() => {
                const s = document.getElementById('scanner-status');
                if (s) s.textContent = '对准二维码进行扫描...';
            }, 1500);
        }
        // ========== 手机扫码功能结束 ==========

        function createFromUnmatched(idx) {
            const rec = scanRecords[idx];
            if (!rec) return;
            const modal = document.createElement('div');
            modal.id = 'temp-mat-modal';
            modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:99999;display:flex;justify-content:center;align-items:center;';
            modal.innerHTML = `
                <div style="background:white;border-radius:10px;padding:25px;width:520px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;">
                        <h3 style="margin:0;">根据扫码内容创建物料档案</h3>
                        <button onclick="document.getElementById('temp-mat-modal').remove()" style="border:none;background:none;font-size:24px;cursor:pointer;">&times;</button>
                    </div>
                    <div style="margin-bottom:10px;">
                        <label>扫码内容 (二维码)</label>
                        <input type="text" id="tmp-barcode" value="${rec.barcode}" readonly style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;font-family:monospace;background:#f0f0f0;">
                    </div>
                    <div style="display:flex;gap:10px;margin-bottom:10px;">
                        <div style="flex:1;">
                            <label>产品编号映射</label>
                            <select id="tmp-product" onchange="onTmpProduct()" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;">
                                <option value="">-- 可选 --</option>
                                ${productCatalog.map(p => `<option value="${p.product_code}" data-name="${p.name}" data-abc="${p.abc_class}" data-unit="${p.unit}" data-price="${p.default_price}">${p.product_code} - ${p.name}</option>`).join('')}
                            </select>
                        </div>
                    </div>
                    <div style="display:flex;gap:10px;margin-bottom:10px;">
                        <div style="flex:1;">
                            <label>物料编码</label>
                            <div style="display:flex;gap:6px;">
                                <input type="text" id="tmp-code" style="flex:1;padding:8px;border:1px solid #ddd;border-radius:4px;background:#f9f9f9;" readonly>
                                <button class="btn btn-secondary" onclick="genTmpCode()">生成</button>
                            </div>
                        </div>
                    </div>
                    <div style="margin-bottom:10px;">
                        <label>物料名称 *</label>
                        <input type="text" id="tmp-name" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;" placeholder="必填 - 请输入物料名称">
                    </div>
                    <div style="display:flex;gap:10px;margin-bottom:10px;">
                        <div style="flex:1;">
                            <label>规格 *</label>
                            <input type="text" id="tmp-spec" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;" placeholder="必填">
                        </div>
                        <div style="flex:1;">
                            <label>单位 *</label>
                            <input type="text" id="tmp-unit" value="个" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;" placeholder="必填">
                        </div>
                    </div>
                    <div style="display:flex;gap:10px;margin-bottom:10px;">
                        <div style="flex:1;">
                            <label>单价 *</label>
                            <input type="number" id="tmp-price" placeholder="0.00" step="0.01" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;">
                        </div>
                        <div style="flex:1;">
                            <label>ABC分类</label>
                            <select id="tmp-abc" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;">
                                <option value="A">A</option><option value="B">B</option><option value="C">C</option>
                            </select>
                        </div>
                    </div>
                    <div style="background:#fff3cd;border:1px solid #ffc107;border-radius:6px;padding:8px 12px;margin-bottom:12px;font-size:12px;color:#856404;">
                        ⚠️ 请填完所有必填项（带 * 号的）后点击"创建"按钮
                    </div>
                    <div style="text-align:right;margin-top:15px;">
                        <button class="btn btn-secondary" onclick="document.getElementById('temp-mat-modal').remove()" style="padding:8px 20px;margin-right:10px;">取消</button>
                        <button class="btn btn-primary" onclick="createTmpMat(${idx})" style="padding:8px 20px;">创建并加入清单</button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
            // 阻止弹窗内的Enter键误触发全局扫码
            setTimeout(() => {
                const inputs = modal.querySelectorAll('input, select, textarea');
                inputs.forEach(inp => {
                    inp.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            e.stopPropagation();
                            // 只有在所有必填项都填完时才提交
                            const name = document.getElementById('tmp-name').value.trim();
                            const code = document.getElementById('tmp-code').value.trim();
                            const spec = document.getElementById('tmp-spec').value.trim();
                            const unit = document.getElementById('tmp-unit').value.trim();
                            const price = document.getElementById('tmp-price').value.trim();
                            if (name && code && spec && unit && price !== '') {
                                createTmpMat(idx);
                            } else {
                                alert('请先填完所有必填项！');
                            }
                        }
                    });
                });
            }, 100);
            if (productCatalog.length === 0) loadProductCatalog();
        }

        function onTmpProduct() {
            const s = document.getElementById('tmp-product');
            if (s && s.value) {
                const o = s.options[s.selectedIndex];
                document.getElementById('tmp-name').value = o.dataset.name || '';
                document.getElementById('tmp-unit').value = o.dataset.unit || '个';
                document.getElementById('tmp-price').value = o.dataset.price || 0;
                document.getElementById('tmp-abc').value = o.dataset.abc || 'C';
                genTmpCode();
            }
        }

        async function genTmpCode() {
            const product = document.getElementById('tmp-product').value || '0000';
            const abc = document.getElementById('tmp-abc').value || 'C';
            try {
                const res = await fetch(`/api/v1/materials/generate-code?abc_class=${abc}&product_code=${product}`);
                const result = await res.json();
                if (result.success) {
                    document.getElementById('tmp-code').value = result.data.code;
                }
            } catch (e) { alert('生成编码失败: ' + e.message); }
        }

        async function createTmpMat(idx) {
            const name = document.getElementById('tmp-name').value.trim();
            const code = document.getElementById('tmp-code').value.trim();
            const barcode = document.getElementById('tmp-barcode').value.trim();
            const spec = document.getElementById('tmp-spec').value.trim();
            const unit = document.getElementById('tmp-unit').value.trim();
            const price = document.getElementById('tmp-price').value.trim();
            const abc = document.getElementById('tmp-abc').value;
            const productSel = document.getElementById('tmp-product');
            const productCode = productSel ? productSel.value : '';

            // ====== 完整验证 ======
            const errors = [];
            if (!name) errors.push('物料名称');
            if (!code) errors.push('物料编码');
            if (!barcode) errors.push('二维码/条码');
            if (!unit) errors.push('单位');
            if (price === '' || isNaN(parseFloat(price))) errors.push('单价（必须填写数字）');
            if (errors.length > 0) {
                alert('请填写以下必填项：\\n• ' + errors.join('\\n• '));
                return;
            }

            try {
                const res = await fetch('/api/v1/materials/', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        account_set_id: 1, name: name, code: code, barcode: barcode,
                        spec: spec, unit: unit, unit_price: parseFloat(price), type: 'RAW_MATERIAL',
                        property: 'PURCHASE', abc_class: abc, cva_class: 'M',
                        safety_stock: 0, min_stock: 0, max_stock: 9999, reorder_point: 0,
                        batch_rule: 'FIXED', batch_size: 1, loss_rate: 0, lead_time: 0,
                        description: JSON.stringify({product_code: productCode})
                    })
                });
                const result = await res.json();
                if (result.success) {
                    const m = result.data;
                    const oldQty = scanRecords[idx].qty || 1;
                    scanRecords[idx] = {
                        id: m.id, barcode: m.barcode || m.code, code: m.code, name: m.name,
                        spec: m.spec, unit: m.unit, unit_price: m.unit_price || price, qty: oldQty, matched: true
                    };
                    document.getElementById('temp-mat-modal').remove();
                    updateScanRecordsTable();
                    alert('物料已创建并加入清单：' + m.name + ' (' + m.code + ')');
                } else { alert('创建失败: ' + result.message); }
            } catch (e) { alert('创建失败: ' + e.message); }
        }

        function updateScanRecordsTable() {
            const tb = document.getElementById('scan-records-tbody');
            if (tb) tb.innerHTML = scanRecords.length > 0 ? renderScanRecords() : `<tr><td colspan="10" style="text-align:center;padding:30px;color:#7f8c8d;">等待扫码枪输入，请扫描二维码...</td></tr>`;
            // 更新计数
            const mCnt = scanRecords.filter(r => r.id).length;
            const uCnt = scanRecords.filter(r => !r.id).length;
            const cntSpan = document.querySelectorAll('#materials-content span');
            if (cntSpan && cntSpan.length > 0) {
                // 尝试找按钮下方的span并更新内容不可靠，简单重新渲染扫码区域顶部按钮条即可
            }
            const mc = document.getElementById('materials-content');
            if (mc) {
                // 刷新计数显示：在按钮区的span
                const statSpans = mc.querySelectorAll('span');
                // 最后三个span是统计：匹配/未匹配/总计（若存在则更新）
                if (statSpans.length >= 3) {
                    const n = statSpans.length;
                    statSpans[n-3].textContent = `✅ 已匹配: ${mCnt}`;
                    statSpans[n-2].textContent = `⚠️ 未匹配: ${uCnt}`;
                    statSpans[n-1].textContent = `📊 总计: ${scanRecords.length}`;
                }
            }
        }

        function updateScanQty(i, q) { scanRecords[i].qty = parseInt(q) || 1; }
        function removeScanRecord(i) { scanRecords.splice(i, 1); updateScanRecordsTable(); }
        function clearScanRecords() { scanRecords = []; updateScanRecordsTable(); showScanDebug('✅ 清单已清空，等待扫码...'); }
        function scanMaterialManually() {
            const si = document.getElementById('material-scan-input');
            if (!si) return;
            const val = si.value.trim();
            if (!val) { alert('请先输入或扫描二维码内容！'); si.focus(); return; }
            processMaterialScan(val);
        }

        async function submitScanRecords() {
            const matched = scanRecords.filter(r => r.id);
            if (matched.length === 0) { alert('清单中没有已匹配的物料！请先为未建档的二维码点击"新建物料"创建档案。'); return; }
            if (!confirm('确认入库 ' + matched.length + ' 种物料？（未建档的物料将被忽略）')) return;
            const totalQty = matched.reduce((s, r) => s + (r.qty || 1), 0);
            try {
                const res = await fetch('/api/v1/inventory/quick-inbound', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ account_set_id: 1, items: matched.map(r => ({ material_id: r.id, quantity: r.qty || 1, unit_price: r.unit_price || 0 })) })
                });
                const result = await res.json();
                if (result.success) {
                    alert('入库成功！\\n入库单号: ' + result.data.inbound_no + '\\n总数量: ' + result.data.total_qty + ' 件\\n总金额: ' + result.data.total_amount.toFixed(2));
                    scanRecords = scanRecords.filter(r => !r.id);
                    updateScanRecordsTable();
                    // === 自动跳转到库存管理 ===
                    setTimeout(() => {
                        loadModule('materials');
                        setTimeout(() => {
                            renderMaterialsTab('inventory', document.querySelectorAll('.finance-tab')[0]);
                            setTimeout(() => {
                                alert('📦 已自动切换到【库存管理】查看入库记录。\\n\\n如需销售出库，请点击【销售管理】。');
                            }, 500);
                        }, 300);
                    }, 300);
                } else { alert('入库失败: ' + result.message); }
            } catch (err) { alert('入库失败: ' + err.message); }
        }

        function showBarcodePrintModal() {
            if (scanRecords.length === 0) { alert('请先扫描物料后再打印标签'); return; }
            const modal = document.createElement('div');
            modal.id = 'barcode-print-modal';
            modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:9999;display:flex;justify-content:center;align-items:center;';
            modal.innerHTML = `
                <div style="background:white;border-radius:10px;padding:25px;width:600px;max-height:80vh;overflow-y:auto;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                        <h3 style="margin:0;">打印二维码标签</h3>
                        <button onclick="document.getElementById('barcode-print-modal').remove()" style="border:none;background:none;font-size:24px;cursor:pointer;">&times;</button>
                    </div>
                    <div id="barcode-labels" style="display:flex;flex-wrap:wrap;gap:15px;">
                        ${scanRecords.map((r, i) => `
                            <div style="border:1px solid #ddd;padding:10px;width:200px;text-align:center;border-radius:6px;">
                                <div style="font-size:13px;font-weight:bold;margin-bottom:5px;">${r.name || ''}</div>
                                <div style="font-size:11px;color:#666;margin-bottom:5px;">规格: ${r.spec || '-'} | 单位: ${r.unit || '-'}</div>
                                <div style="font-size:11px;color:#666;margin-bottom:8px;">批次: ${r.code || '-'}</div>
                                <img src="/api/v1/materials/qr-image?text=${encodeURIComponent(r.barcode || r.code || '')}" style="width:150px;height:150px;" alt="QR码">
                                <div style="font-size:12px;font-family:monospace;margin-top:5px;">${r.barcode || r.code || ''}</div>
                                <div style="font-size:11px;color:#666;margin-top:3px;">数量: ${r.qty || 1} ${r.unit || ''}</div>
                            </div>
                        `).join('')}
                    </div>
                    <div style="text-align:center;margin-top:20px;">
                        <button class="btn btn-primary" onclick="printBarcodeLabels()" style="padding:10px 40px;font-size:15px;">打印标签</button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }

        function generateBarcodeSVG(elementId, text) {
            const el = document.getElementById(elementId);
            if (!el || !text) return;
            const chars = text.split('');
            const widths = chars.map(c => {
                const code = c.charCodeAt(0);
                return 2 + (code % 5);
            });
            const totalWidth = widths.reduce((a, b) => a + b * 2, 0) + 20;
            let x = 10;
            let bars = '';
            chars.forEach((c, i) => {
                const w = widths[i];
                bars += `<rect x="${x}" y="0" width="${w}" height="50" fill="black"/>`;
                x += w;
                bars += `<rect x="${x}" y="0" width="${w}" height="50" fill="white"/>`;
                x += w;
            });
            el.innerHTML = `<svg viewBox="0 0 ${totalWidth} 50" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" style="width:100%;height:50px;">${bars}</svg>`;
        }

        function printBarcodeLabels() {
            const content = document.getElementById('barcode-labels').innerHTML;
            const win = window.open('', '_blank');
            win.document.write(`
                <html><head><title>打印二维码标签</title>
                <style>
                    @media print { body { margin:0; } .label { display:inline-block; border:1px solid #000; padding:8px; width:200px; text-align:center; margin:5px; page-break-inside:avoid; } }
                    .label { display:inline-block; border:1px solid #000; padding:8px; width:200px; text-align:center; margin:5px; }
                    .label-name { font-size:14px; font-weight:bold; margin-bottom:3px; }
                    .label-info { font-size:10px; color:#333; margin-bottom:3px; }
                    .label-qty { font-size:11px; color:#333; }
                    img { width:150px; height:150px; }
                </style></head>
                <body>${content}</body></html>
            `);
            win.document.close();
            win.focus();
            // 等待图片加载后再打印
            setTimeout(() => {
                const imgs = win.document.querySelectorAll('img');
                let loaded = 0;
                const total = imgs.length;
                if (total === 0) { win.print(); return; }
                imgs.forEach(img => {
                    if (img.complete) { loaded++; if (loaded >= total) win.print(); }
                    else { img.onload = () => { loaded++; if (loaded >= total) win.print(); }; }
                });
                // Fallback: print after 2s regardless
                setTimeout(() => { try { win.print(); } catch(e) {} }, 2000);
            }, 500);
        }

        let productCatalog = [];

        async function loadProductCatalog() {
            try {
                const res = await fetch('/api/v1/materials/product-catalog');
                const result = await res.json();
                if (result.success) productCatalog = result.data;
            } catch (e) { console.error('加载产品目录失败', e); }
        }

        function showNewMaterialModal() {
            const modal = document.createElement('div');
            modal.id = 'new-material-modal';
            modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:9999;display:flex;justify-content:center;align-items:center;';
            modal.innerHTML = `
                <div style="background:white;border-radius:10px;padding:25px;width:550px;max-height:85vh;overflow-y:auto;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                        <h3 style="margin:0;">新增原材料</h3>
                        <button onclick="document.getElementById('new-material-modal').remove()" style="border:none;background:none;font-size:24px;cursor:pointer;">&times;</button>
                    </div>
                    <div style="margin-bottom:12px;padding:10px;background:#f0f7ff;border-radius:6px;border:1px solid #d0e3ff;">
                        <label style="display:block;margin-bottom:5px;font-size:13px;font-weight:bold;">选择产品（产品编号映射表）</label>
                        <select id="new-mat-product" onchange="onProductSelect()" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;">
                            <option value="">-- 请选择产品 --</option>
                            ${productCatalog.map(p => `<option value="${p.product_code}" data-name="${p.name}" data-abc="${p.abc_class}" data-unit="${p.unit}" data-price="${p.default_price}">${p.product_code} - ${p.name} (${p.abc_class}类)</option>`).join('')}
                        </select>
                    </div>
                    <div style="margin-bottom:10px;">
                        <label style="display:block;margin-bottom:5px;font-size:13px;">物料编码（自动生成: PO+日期+ABC+产品号+流水号）</label>
                        <div style="display:flex;gap:10px;">
                            <input type="text" id="new-mat-code" placeholder="选择产品后自动生成" readonly style="flex:1;padding:8px;border:1px solid #ddd;border-radius:4px;background:#f9f9f9;">
                            <button class="btn btn-secondary" onclick="generateNewCode()" style="padding:8px 15px;">生成编码</button>
                        </div>
                    </div>
                    <div style="margin-bottom:10px;">
                        <label style="display:block;margin-bottom:5px;font-size:13px;">物料名称 *</label>
                        <input type="text" id="new-mat-name" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;">
                    </div>
                    <div style="display:flex;gap:10px;margin-bottom:10px;">
                        <div style="flex:1;">
                            <label style="display:block;margin-bottom:5px;font-size:13px;">规格型号</label>
                            <input type="text" id="new-mat-spec" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;">
                        </div>
                        <div style="flex:1;">
                            <label style="display:block;margin-bottom:5px;font-size:13px;">计量单位</label>
                            <input type="text" id="new-mat-unit" value="个" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;">
                        </div>
                    </div>
                    <div style="display:flex;gap:10px;margin-bottom:10px;">
                        <div style="flex:1;">
                            <label style="display:block;margin-bottom:5px;font-size:13px;">单价</label>
                            <input type="number" id="new-mat-price" value="0" step="0.01" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;">
                        </div>
                        <div style="flex:1;">
                            <label style="display:block;margin-bottom:5px;font-size:13px;">ABC分类</label>
                            <select id="new-mat-abc" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;">
                                <option value="A">A类（高价值）</option>
                                <option value="B">B类（中等价值）</option>
                                <option value="C">C类（低价值）</option>
                            </select>
                        </div>
                    </div>
                    <div style="margin-bottom:10px;">
                        <label style="display:block;margin-bottom:5px;font-size:13px;">物料类型</label>
                        <select id="new-mat-type" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;">
                            <option value="RAW_MATERIAL">原材料</option>
                            <option value="SEMI_FINISHED">半成品</option>
                            <option value="FINISHED_GOOD">成品</option>
                        </select>
                    </div>
                    <div style="text-align:right;margin-top:15px;">
                        <button class="btn btn-secondary" onclick="document.getElementById('new-material-modal').remove()" style="padding:8px 20px;margin-right:10px;">取消</button>
                        <button class="btn btn-primary" onclick="createNewMaterial()" style="padding:8px 20px;">创建物料</button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
            if (productCatalog.length === 0) loadProductCatalog().then(() => { if (productCatalog.length > 0) showNewMaterialModal(); });
        }

        function onProductSelect() {
            const sel = document.getElementById('new-mat-product');
            if (!sel || !sel.value) return;
            const opt = sel.options[sel.selectedIndex];
            document.getElementById('new-mat-name').value = opt.dataset.name || '';
            document.getElementById('new-mat-unit').value = opt.dataset.unit || '个';
            document.getElementById('new-mat-price').value = opt.dataset.price || 0;
            document.getElementById('new-mat-abc').value = opt.dataset.abc || 'C';
            generateNewCode();
        }

        async function generateNewCode() {
            const productSel = document.getElementById('new-mat-product');
            const abcSel = document.getElementById('new-mat-abc');
            const productCode = productSel ? productSel.value : '0000';
            const abcClass = abcSel ? abcSel.value : 'C';
            if (!productCode) { alert('请先选择产品'); return; }
            try {
                const res = await fetch(`/api/v1/materials/generate-code?abc_class=${abcClass}&product_code=${productCode}`);
                const result = await res.json();
                if (result.success) {
                    document.getElementById('new-mat-code').value = result.data.code;
                }
            } catch (e) { alert('生成编码失败: ' + e.message); }
        }

        async function createNewMaterial() {
            const name = document.getElementById('new-mat-name').value.trim();
            if (!name) { alert('请填写物料名称'); return; }
            const code = document.getElementById('new-mat-code').value.trim();
            if (!code) { alert('请先生成编码'); return; }
            const spec = document.getElementById('new-mat-spec').value.trim();
            const unit = document.getElementById('new-mat-unit').value.trim() || '个';
            const price = parseFloat(document.getElementById('new-mat-price').value) || 0;
            const type = document.getElementById('new-mat-type').value;
            const abc = document.getElementById('new-mat-abc').value;
            const productSel = document.getElementById('new-mat-product');
            const productCode = productSel ? productSel.value : '';

            try {
                const res = await fetch('/api/v1/materials/', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        account_set_id: 1, name: name, code: code, barcode: code,
                        spec: spec, unit: unit, unit_price: price, type: type,
                        property: 'PURCHASE', abc_class: abc, cva_class: 'M',
                        safety_stock: 0, min_stock: 0, max_stock: 9999, reorder_point: 0,
                        batch_rule: 'FIXED', batch_size: 1, loss_rate: 0, lead_time: 0,
                        description: JSON.stringify({product_code: productCode})
                    })
                });
                const result = await res.json();
                if (result.success) {
                    alert('物料创建成功！\\n编码: ' + result.data.code + '\\n二维码: ' + result.data.barcode);
                    document.getElementById('new-material-modal').remove();
                } else { alert('创建失败: ' + result.message); }
            } catch (e) { alert('创建失败: ' + e.message); }
        }
        
        function renderMaterialsInventory() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">库存台账</div>
                <div style="text-align:center;padding:40px;color:#7f8c8d;">${t['no-data']}</div>
            </div>`;
        }
        
        function renderMaterialsQuality() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">质检管理</div>
                <button class="btn btn-primary add-btn">+ 创建质检单</button>
                <table class="data-table">
                    <thead><tr><th>质检单号</th><th>物料编码</th><th>物料名称</th><th>批次号</th><th>质检数量</th><th>合格数量</th><th>不合格数量</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="9" style="text-align:center;">${t['no-data']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderMaterialsInbound() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">入库管理</div>
                <button class="btn btn-primary add-btn">+ 创建入库单</button>
                <table class="data-table">
                    <thead><tr><th>入库单号</th><th>供应商</th><th>物料编码</th><th>批次号</th><th>数量</th><th>质检状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="7" style="text-align:center;">${t['no-data']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderMaterialsOutbound() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">出库管理</div>
                <button class="btn btn-primary add-btn">+ 创建出库单</button>
                <table class="data-table">
                    <thead><tr><th>出库单号</th><th>物料编码</th><th>批次号</th><th>数量</th><th>去向</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="7" style="text-align:center;">${t['no-data']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderSales() {
            const t = translations[currentLang];
            setTimeout(loadSalesOrders, 200);
            return `<div class="content-header"><h2>${t['sales-title']}</h2><p>${t['sales-desc']}</p></div>
                <div class="finance-tabs">
                    <button class="finance-tab active" onclick="renderSalesTab('orders', this)">销售订单</button>
                    <button class="finance-tab" onclick="renderSalesTab('delivery', this)">发货通知单</button>
                    <button class="finance-tab" onclick="renderSalesTab('outbound', this)">销售出库</button>
                    <button class="finance-tab" onclick="renderSalesTab('customers', this)">客户管理</button>
                </div>
                <div id="sales-content">${renderSalesOrders()}</div>`;
        }
        
        function renderSalesTab(tab, btnEl) {
            document.querySelectorAll('.finance-tab').forEach(btn => btn.classList.remove('active'));
            if (btnEl) btnEl.classList.add('active');
            else if (event && event.target) event.target.classList.add('active');
            
            const content = document.getElementById('sales-content');
            switch(tab) {
                case 'orders': content.innerHTML = renderSalesOrders(); setTimeout(loadSalesOrders, 100); break;
                case 'delivery': content.innerHTML = renderSalesDelivery(); break;
                case 'outbound': content.innerHTML = renderSalesOutbound(); break;
                case 'customers': content.innerHTML = renderSalesCustomers(); break;
            }
        }
        
        function renderSalesOrders() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">销售订单</div>
                <button class="btn btn-primary add-btn" onclick="showSalesOrderModal()">+ 创建销售订单</button>
                <table class="data-table">
                    <thead><tr><th>销售订单号</th><th>客户</th><th>物料编码</th><th>物料名称</th><th>数量</th><th>金额</th><th>付款方式</th><th>库存状态</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody id="sales-orders-tbody"><tr><td colspan="11" style="text-align:center;">${t['loading']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderSalesDelivery() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">发货通知单</div>
                <button class="btn btn-primary add-btn">+ 创建发货通知</button>
                <table class="data-table">
                    <thead><tr><th>发货通知单号</th><th>销售订单号</th><th>客户</th><th>物料编码</th><th>数量</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="7" style="text-align:center;">${t['no-data']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderSalesOutbound() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">销售出库单</div>
                <button class="btn btn-primary add-btn">+ 创建销售出库</button>
                <table class="data-table">
                    <thead><tr><th>出库单号</th><th>发货通知单号</th><th>客户</th><th>物料编码</th><th>批次号</th><th>数量</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="8" style="text-align:center;">${t['no-data']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderSalesCustomers() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">客户管理</div>
                <button class="btn btn-primary add-btn">+ 添加客户</button>
                <table class="data-table">
                    <thead><tr><th>客户编码</th><th>客户名称</th><th>联系人</th><th>电话</th><th>信用额度</th><th>已用额度</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="8" style="text-align:center;">${t['no-data']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderPlan() {
            const t = translations[currentLang];
            return `<div class="content-header"><h2>${t['plan-title']}</h2><p>${t['plan-desc']}</p></div>
                <div class="finance-tabs">
                    <button class="finance-tab active" onclick="renderPlanMainTab('demand')">需求计划</button>
                    <button class="finance-tab" onclick="renderPlanMainTab('purchase')">采购管理</button>
                    <button class="finance-tab" onclick="renderPlanMainTab('outsourcing')">委外加工</button>
                    <button class="finance-tab" onclick="renderPlanMainTab('production')">生产管理</button>
                </div>
                <div id="plan-content">${renderPlanDemand()}</div>`;
        }
        
        function renderPlanMainTab(tab) {
            document.querySelectorAll('.finance-tab').forEach(btn => btn.classList.remove('active'));
            try { if (event && event.target) event.target.classList.add('active'); } catch(e) {}
            
            const content = document.getElementById('plan-content');
            switch(tab) {
                case 'demand': content.innerHTML = renderPlanDemand(); break;
                case 'purchase': content.innerHTML = renderPlanPurchase(); break;
                case 'outsourcing': content.innerHTML = renderPlanOutsourcing(); break;
                case 'production': content.innerHTML = renderPlanProduction(); break;
            }
        }

        function loadForecastOrders() {
            fetch(`${apiBase}/plan/forecast-orders`, { headers: authHeaders })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    const tbody = document.querySelector('#forecast-table tbody');
                    tbody.innerHTML = data.data.items.map(f => `<tr>
                        <td>${f.forecast_no}</td>
                        <td>${f.material_code || '-'}</td>
                        <td>${f.material_name || '-'}</td>
                        <td>${f.forecast_qty}</td>
                        <td>${f.forecast_date || '-'}</td>
                        <td>${getStatusText(f.status)}</td>
                        <td>
                            ${f.status === 'PENDING' ? `<button onclick="approveForecast(${f.id})">审批</button>` : ''}
                            <button onclick="deleteForecast(${f.id})">删除</button>
                        </td>
                    </tr>`).join('');
                }
            });
        }

        function showForecastModal() {
            showModal(`<h3>创建预测单</h3>
                <form id="forecast-form">
                    <div><label>物料</label><select id="fc-material-id"></select></div>
                    <div><label>预测数量</label><input type="number" id="fc-qty" required></div>
                    <div><label>预测日期</label><input type="date" id="fc-date" required></div>
                    <div><label>备注</label><textarea id="fc-remark"></textarea></div>
                </form>`, () => {
                    submitForecast();
                });
            loadMaterialsSelect('fc-material-id');
        }

        function submitForecast() {
            const data = {
                account_set_id: currentAccountSetId,
                material_id: parseInt(document.getElementById('fc-material-id').value),
                forecast_qty: parseInt(document.getElementById('fc-qty').value),
                forecast_date: document.getElementById('fc-date').value,
                remark: document.getElementById('fc-remark').value,
                status: 'PENDING'
            };
            fetch(`${apiBase}/plan/forecast-orders`, {
                method: 'POST',
                headers: { ...authHeaders, 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    closeModal();
                    loadForecastOrders();
                    showMessage('创建成功');
                }
            });
        }

        function approveForecast(id) {
            fetch(`${apiBase}/plan/forecast-orders/${id}/approve`, {
                method: 'PUT',
                headers: authHeaders
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    loadForecastOrders();
                    showMessage('审批成功');
                }
            });
        }

        function deleteForecast(id) {
            if(!confirm('确定删除该预测单？')) return;
            fetch(`${apiBase}/plan/forecast-orders/${id}`, {
                method: 'DELETE',
                headers: authHeaders
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    loadForecastOrders();
                    showMessage('删除成功');
                }
            });
        }
        
        function renderPlanDemand() {
            const t = translations[currentLang];
            setTimeout(() => loadForecastOrders(), 100);
            return `<div class="card"><div class="card-title">需求计划</div>
                <div class="finance-tabs" style="margin-bottom:20px;">
                    <button class="finance-tab active" onclick="renderPlanDemandTab('forecast')">预测单</button>
                    <button class="finance-tab" onclick="renderPlanDemandTab('mrp')">MRP运算</button>
                    <button class="finance-tab" onclick="renderPlanDemandTab('planned')">计划订单</button>
                </div>
                <div id="plan-demand-content">${renderPlanDemandForecast()}</div>`;
        }
        
        function renderPlanDemandTab(tab) {
            document.querySelectorAll('#plan-demand-content + .finance-tabs .finance-tab').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            const content = document.getElementById('plan-demand-content');
            switch(tab) {
                case 'forecast': content.innerHTML = renderPlanDemandForecast(); loadForecastOrders(); break;
                case 'mrp': content.innerHTML = renderPlanDemandMRP(); setTimeout(loadPendingSalesOrders, 200); break;
                case 'planned': content.innerHTML = renderPlanDemandOrders(); setTimeout(loadPlannedOrders, 200); break;
            }
        }
        
        function renderPlanDemandForecast() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">预测单</div>
                <button class="btn btn-primary add-btn" onclick="showForecastModal()">+ 创建预测单</button>
                <table class="data-table" id="forecast-table">
                    <thead><tr><th>预测单号</th><th>物料编码</th><th>物料名称</th><th>预测数量</th><th>预测日期</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="7" style="text-align:center;">${t['loading']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderPlanDemandMRP() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">MRP运算</div>
                <div style="padding:20px;">
                    <div class="form-group">
                        <label>运算来源</label>
                        <select id="mrp-source" style="width:200px;">
                            <option value="sales">销售订单</option>
                            <option value="forecast">预测单</option>
                            <option value="both">销售订单+预测单</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>运算日期</label>
                        <input type="date" id="mrp-date" style="width:200px;">
                    </div>
                    <button class="btn btn-primary" onclick="runMRP()">执行MRP运算</button>
                </div>
                <div class="card" style="margin-top:20px;">
                    <div class="card-title">待处理销售订单（库存不足）</div>
                    <table class="data-table" id="pending-sales-orders">
                        <thead><tr><th>销售订单号</th><th>物料编码</th><th>物料名称</th><th>数量</th><th>金额</th><th>操作</th></tr></thead>
                        <tbody><tr><td colspan="6" style="text-align:center;color:#999;">加载中...</td></tr></tbody>
                    </table>
                </div>
                <div id="mrp-result" style="margin-top:20px;">
                    <div style="text-align:center;padding:40px;color:#7f8c8d;">${t['no-data']}</div>
                </div>
            </div>`;
        }
        
        function renderPlanDemandOrders() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">计划订单</div>
                <div style="margin-bottom:15px;">
                    <select id="planned-order-type" onchange="loadPlannedOrders()" style="margin-right:10px;">
                        <option value="">全部类型</option>
                        <option value="PURCHASE">采购</option>
                        <option value="PRODUCTION">生产</option>
                        <option value="OUTSOURCING">委外</option>
                    </select>
                    <select id="planned-order-status" onchange="loadPlannedOrders()">
                        <option value="">全部状态</option>
                        <option value="PENDING">待下达</option>
                        <option value="RELEASED">已下达</option>
                    </select>
                </div>
                <table class="data-table" id="planned-orders-table">
                    <thead><tr><th>计划订单号</th><th>物料编码</th><th>物料名称</th><th>计划数量</th><th>计划日期</th><th>类型</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="8" style="text-align:center;">${t['loading']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderPlanPurchase() {
            const t = translations[currentLang];
            setTimeout(() => loadPurchaseRequests(), 100);
            return `<div class="card"><div class="card-title">采购管理</div>
                <div class="finance-tabs" style="margin-bottom:20px;">
                    <button class="finance-tab active" onclick="renderPlanPurchaseTab('req')">采购申请</button>
                    <button class="finance-tab" onclick="renderPlanPurchaseTab('order')">采购订单</button>
                    <button class="finance-tab" onclick="renderPlanPurchaseTab('notice')">来料通知</button>
                    <button class="finance-tab" onclick="renderPlanPurchaseTab('inbound')">采购入库</button>
                </div>
                <div id="plan-purchase-content">${renderPlanPurchaseReq()}</div>`;
        }
        
        function renderPlanPurchaseTab(tab) {
            document.querySelectorAll('#plan-purchase-content + .finance-tabs .finance-tab').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            const content = document.getElementById('plan-purchase-content');
            switch(tab) {
                case 'req': content.innerHTML = renderPlanPurchaseReq(); loadPurchaseRequests(); break;
                case 'order': content.innerHTML = renderPlanPurchaseOrder(); loadPurchaseOrders(); break;
                case 'notice': content.innerHTML = renderPlanPurchaseNotice(); loadPreReceipts(); break;
                case 'inbound': content.innerHTML = renderPlanPurchaseInbound(); loadInboundOrders(); break;
            }
        }
        
        function renderPlanPurchaseReq() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">采购申请单</div>
                <button class="btn btn-primary add-btn" onclick="showPurchaseReqModal()">+ 创建采购申请</button>
                <table class="data-table" id="purchase-req-table">
                    <thead><tr><th>申请单号</th><th>物料编码</th><th>物料名称</th><th>申请数量</th><th>需求日期</th><th>供应商</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="8" style="text-align:center;">${t['loading']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderPlanPurchaseOrder() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">采购订单</div>
                <button class="btn btn-primary add-btn" onclick="showPurchaseOrderModal()">+ 创建采购订单</button>
                <table class="data-table" id="purchase-order-table">
                    <thead><tr><th>采购订单号</th><th>供应商</th><th>物料编码</th><th>物料名称</th><th>数量</th><th>单价</th><th>金额</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="9" style="text-align:center;">${t['loading']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderPlanPurchaseNotice() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">来料通知单</div>
                <button class="btn btn-primary add-btn" onclick="showPurchaseNoticeModal()">+ 新建来料通知</button>
                <table class="data-table" id="purchase-notice-table">
                    <thead><tr><th>来料通知单号</th><th>采购订单号</th><th>物料编码</th><th>物料名称</th><th>数量</th><th>预计到货日期</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="8" style="text-align:center;">${t['loading']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderPlanPurchaseInbound() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">采购入库</div>
                <button class="btn btn-primary add-btn" onclick="showPurchaseInboundModal()">+ 新建采购入库</button>
                <table class="data-table" id="purchase-inbound-table">
                    <thead><tr><th>入库单号</th><th>来料通知单号</th><th>物料编码</th><th>物料名称</th><th>数量</th><th>批次号</th><th>质检状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="8" style="text-align:center;">${t['loading']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderPlanOutsourcing() {
            const t = translations[currentLang];
            setTimeout(() => loadOutsourcingRequests(), 100);
            return `<div class="card"><div class="card-title">委外加工</div>
                <div class="finance-tabs" style="margin-bottom:20px;">
                    <button class="finance-tab active" onclick="renderPlanOutsourcingTab('req')">委外申请单</button>
                    <button class="finance-tab" onclick="renderPlanOutsourcingTab('order')">委外订单</button>
                    <button class="finance-tab" onclick="renderPlanOutsourcingTab('issue')">委外投料单</button>
                    <button class="finance-tab" onclick="renderPlanOutsourcingTab('supplement')">委外补发单</button>
                    <button class="finance-tab" onclick="renderPlanOutsourcingTab('return')">委外退料单</button>
                    <button class="finance-tab" onclick="renderPlanOutsourcingTab('receive')">收料通知单</button>
                    <button class="finance-tab" onclick="renderPlanOutsourcingTab('invoice')">发票识别</button>
                    <button class="finance-tab" onclick="renderPlanOutsourcingTab('estimate')">委外入库暂估</button>
                    <button class="finance-tab" onclick="renderPlanOutsourcingTab('account')">委外入库核算</button>
                </div>
                <div id="plan-outsourcing-content">${renderPlanOutsourcingReq()}</div>`;
        }
        
        function renderPlanOutsourcingTab(tab) {
            document.querySelectorAll('#plan-outsourcing-content + .finance-tabs .finance-tab').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            const content = document.getElementById('plan-outsourcing-content');
            switch(tab) {
                case 'req': content.innerHTML = renderPlanOutsourcingReq(); loadOutsourcingRequests(); break;
                case 'order': content.innerHTML = renderPlanOutsourcingOrder(); loadOutsourcingOrders(); break;
                case 'issue': content.innerHTML = renderPlanOutsourcingIssue(); loadOutsourcingIssues(); break;
                case 'supplement': content.innerHTML = renderPlanOutsourcingSupplement(); loadOutsourcingReplenishes(); break;
                case 'return': content.innerHTML = renderPlanOutsourcingReturn(); loadOutsourcingReturns(); break;
                case 'receive': content.innerHTML = renderPlanOutsourcingReceive(); loadOutsourcingReceives(); break;
                case 'invoice': content.innerHTML = renderPlanOutsourcingInvoice(); loadOutsourcingInvoices(); break;
                case 'estimate': content.innerHTML = renderPlanOutsourcingEstimate(); loadOutsourcingEstimates(); break;
                case 'account': content.innerHTML = renderPlanOutsourcingAccount(); loadOutsourcingAccounts(); break;
            }
        }
        
        function renderPlanOutsourcingReq() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">委外申请单</div>
                <button class="btn btn-primary add-btn" onclick="showOutsourcingReqModal()">+ 创建委外申请</button>
                <table class="data-table" id="outsourcing-req-table">
                    <thead><tr><th>申请单号</th><th>物料编码</th><th>物料名称</th><th>数量</th><th>供应商</th><th>需求日期</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="8" style="text-align:center;">${t['loading']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderPlanOutsourcingOrder() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">委外订单</div>
                <button class="btn btn-primary add-btn" onclick="showOutsourcingOrderModal()">+ 创建委外订单</button>
                <table class="data-table" id="outsourcing-order-table">
                    <thead><tr><th>委外订单号</th><th>申请单号</th><th>供应商</th><th>物料编码</th><th>物料名称</th><th>数量</th><th>金额</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="9" style="text-align:center;">${t['loading']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderPlanOutsourcingIssue() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">委外投料单</div>
                <button class="btn btn-primary add-btn" onclick="showOutsourcingIssueModal()">+ 创建委外投料</button>
                <table class="data-table" id="outsourcing-issue-table">
                    <thead><tr><th>投料单号</th><th>委外订单号</th><th>物料编码</th><th>物料名称</th><th>投料数量</th><th>仓库</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="8" style="text-align:center;">${t['loading']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderPlanOutsourcingSupplement() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">委外补发单</div>
                <button class="btn btn-primary add-btn" onclick="showOutsourcingSupplementModal()">+ 创建补发单</button>
                <table class="data-table" id="outsourcing-supplement-table">
                    <thead><tr><th>补发单号</th><th>委外订单号</th><th>物料编码</th><th>物料名称</th><th>补发数量</th><th>原因</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="8" style="text-align:center;">${t['loading']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderPlanOutsourcingReturn() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">委外退料单</div>
                <button class="btn btn-primary add-btn" onclick="showOutsourcingReturnModal()">+ 创建退料单</button>
                <table class="data-table" id="outsourcing-return-table">
                    <thead><tr><th>退料单号</th><th>委外订单号</th><th>物料编码</th><th>物料名称</th><th>退料数量</th><th>原因</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="8" style="text-align:center;">${t['loading']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderPlanOutsourcingReceive() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">收料通知单</div>
                <button class="btn btn-primary add-btn" onclick="showOutsourcingReceiveModal()">+ 新建收料通知</button>
                <table class="data-table" id="outsourcing-receive-table">
                    <thead><tr><th>收料通知单号</th><th>委外订单号</th><th>物料编码</th><th>物料名称</th><th>数量</th><th>预计到货日期</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="8" style="text-align:center;">${t['loading']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderPlanOutsourcingInvoice() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">委外加工发票识别</div>
                <button class="btn btn-primary add-btn" onclick="showOutsourcingInvoiceModal()">+ 识别发票</button>
                <table class="data-table" id="outsourcing-invoice-table">
                    <thead><tr><th>发票号</th><th>委外订单号</th><th>供应商</th><th>金额</th><th>税额</th><th>开票日期</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="8" style="text-align:center;">${t['loading']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderPlanOutsourcingEstimate() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">委外入库暂估</div>
                <button class="btn btn-primary add-btn" onclick="showOutsourcingEstimateModal()">+ 创建暂估</button>
                <table class="data-table" id="outsourcing-estimate-table">
                    <thead><tr><th>暂估单号</th><th>收料通知单号</th><th>物料编码</th><th>物料名称</th><th>数量</th><th>暂估金额</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="8" style="text-align:center;">${t['loading']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderPlanOutsourcingAccount() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">委外入库核算</div>
                <button class="btn btn-primary add-btn" onclick="showOutsourcingAccountModal()">+ 核算入库</button>
                <table class="data-table" id="outsourcing-account-table">
                    <thead><tr><th>核算单号</th><th>暂估单号</th><th>发票号</th><th>物料编码</th><th>物料名称</th><th>数量</th><th>实际金额</th><th>差异金额</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="10" style="text-align:center;">${t['loading']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderPlanProduction() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">生产管理</div>
                <div class="finance-tabs" style="margin-bottom:20px;">
                    <button class="finance-tab active" onclick="renderPlanProductionTab('workorder')">生产工单</button>
                    <button class="finance-tab" onclick="renderPlanProductionTab('material')">领料单</button>
                    <button class="finance-tab" onclick="renderPlanProductionTab('report')">报工单</button>
                    <button class="finance-tab" onclick="renderPlanProductionTab('output')">产成品入库</button>
                </div>
                <div id="plan-production-content">${renderPlanProductionWorkorder()}</div>`;
        }
        
        function renderPlanProductionTab(tab) {
            document.querySelectorAll('#plan-production-content + .finance-tabs .finance-tab').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            const content = document.getElementById('plan-production-content');
            switch(tab) {
                case 'workorder': content.innerHTML = renderPlanProductionWorkorder(); break;
                case 'material': content.innerHTML = renderPlanProductionMaterial(); break;
                case 'report': content.innerHTML = renderPlanProductionReport(); break;
                case 'output': content.innerHTML = renderPlanProductionOutput(); break;
            }
        }
        
        function renderPlanProductionWorkorder() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">生产工单</div>
                <button class="btn btn-primary add-btn" onclick="showProductionWorkorderModal()">+ 创建生产工单</button>
                <table class="data-table" id="production-workorder-table">
                    <thead><tr><th>工单号</th><th>产品编码</th><th>产品名称</th><th>计划数量</th><th>已完成数量</th><th>状态</th><th>计划开始日期</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="8" style="text-align:center;">${t['loading']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderPlanProductionMaterial() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">领料单</div>
                <button class="btn btn-primary add-btn" onclick="showProductionMaterialModal()">+ 创建领料单</button>
                <table class="data-table" id="production-material-table">
                    <thead><tr><th>领料单号</th><th>工单号</th><th>物料编码</th><th>物料名称</th><th>数量</th><th>仓库</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="8" style="text-align:center;">${t['loading']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderPlanProductionReport() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">报工单</div>
                <button class="btn btn-primary add-btn" onclick="showProductionReportModal()">+ 创建报工单</button>
                <table class="data-table" id="production-report-table">
                    <thead><tr><th>报工单号</th><th>工单号</th><th>工序</th><th>完成数量</th><th>工时</th><th>操作人</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="8" style="text-align:center;">${t['loading']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderPlanProductionOutput() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">产成品入库</div>
                <button class="btn btn-primary add-btn" onclick="showProductionOutputModal()">+ 创建产成品入库</button>
                <table class="data-table" id="production-output-table">
                    <thead><tr><th>入库单号</th><th>工单号</th><th>产品编码</th><th>产品名称</th><th>数量</th><th>批次号</th><th>状态</th><th>操作</th></tr></thead>
                    <tbody><tr><td colspan="8" style="text-align:center;">${t['loading']}</td></tr></tbody>
                </table>
            </div>`;
        }

        function loadPurchaseRequests() {
            fetch(`${apiBase}/procurement/purchase-requests`, { headers: authHeaders })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    const tbody = document.querySelector('#purchase-req-table tbody');
                    tbody.innerHTML = data.data.items.map(r => `<tr>
                        <td>${r.request_no}</td>
                        <td>${r.material_code || '-'}</td>
                        <td>${r.material_name || '-'}</td>
                        <td>${r.requested_qty}</td>
                        <td>${r.required_date || '-'}</td>
                        <td>${r.supplier_name || '-'}</td>
                        <td>${getStatusText(r.status)}</td>
                        <td>
                            ${r.status === 'PENDING' ? `<button onclick="approvePurchaseRequest(${r.id})">审批</button>` : ''}
                            <button onclick="createPurchaseOrderFromReq(${r.id})">生成采购订单</button>
                        </td>
                    </tr>`).join('');
                }
            });
        }

        function showPurchaseReqModal() {
            const t = translations[currentLang];
            showModal(`<h3>${t['create']}采购申请</h3>
                <form id="purchase-req-form">
                    <div><label>物料</label><select id="pr-material-id"></select></div>
                    <div><label>申请数量</label><input type="number" id="pr-qty" required></div>
                    <div><label>需求日期</label><input type="date" id="pr-date" required></div>
                    <div><label>供应商</label><select id="pr-supplier-id"></select></div>
                </form>`, () => {
                    submitPurchaseReq();
                });
            loadMaterialsSelect('pr-material-id');
            loadSuppliersSelect('pr-supplier-id');
        }

        function submitPurchaseReq() {
            const data = {
                account_set_id: currentAccountSetId,
                material_id: parseInt(document.getElementById('pr-material-id').value),
                requested_qty: parseInt(document.getElementById('pr-qty').value),
                required_date: document.getElementById('pr-date').value,
                supplier_id: document.getElementById('pr-supplier-id').value ? parseInt(document.getElementById('pr-supplier-id').value) : null,
                status: 'PENDING'
            };
            fetch(`${apiBase}/procurement/purchase-requests`, {
                method: 'POST',
                headers: { ...authHeaders, 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    closeModal();
                    loadPurchaseRequests();
                    showMessage(t['success']);
                }
            });
        }

        function approvePurchaseRequest(id) {
            fetch(`${apiBase}/procurement/purchase-requests/${id}/approve`, {
                method: 'PUT',
                headers: authHeaders
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    loadPurchaseRequests();
                    showMessage('审批成功');
                }
            });
        }

        function createPurchaseOrderFromReq(reqId) {
            fetch(`${apiBase}/procurement/purchase-requests/${reqId}`, { headers: authHeaders })
            .then(res => res.json()).then(data => {
                if(data.success) {
                    const req = data.data;
                    showPurchaseOrderModal(req);
                }
            });
        }

        function loadPurchaseOrders() {
            fetch(`${apiBase}/procurement/purchase-orders`, { headers: authHeaders })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    const tbody = document.querySelector('#purchase-order-table tbody');
                    tbody.innerHTML = data.data.items.map(o => `<tr>
                        <td>${o.po_no}</td>
                        <td>${o.supplier_name || '-'}</td>
                        <td>${o.items ? o.items[0]?.material_code || '-' : '-'}</td>
                        <td>${o.items ? o.items[0]?.material_name || '-' : '-'}</td>
                        <td>${o.items ? o.items.reduce((s,i) => s + i.quantity, 0) : 0}</td>
                        <td>${o.items ? o.items[0]?.unit_price || '-' : '-'}</td>
                        <td>${o.items ? o.items.reduce((s,i) => s + i.quantity * (i.unit_price || 0), 0) : 0}</td>
                        <td>${getStatusText(o.status)}</td>
                        <td>
                            ${o.status === 'APPROVED' ? `<button onclick="createPreReceiptFromOrder(${o.id})">来料通知</button>` : ''}
                        </td>
                    </tr>`).join('');
                }
            });
        }

        function showPurchaseOrderModal(reqData) {
            const t = translations[currentLang];
            showModal(`<h3>${t['create']}采购订单</h3>
                <form id="purchase-order-form">
                    <div><label>供应商</label><select id="po-supplier-id"></select></div>
                    <div><label>订单日期</label><input type="date" id="po-date" required></div>
                    <div><label>物料明细</label><div id="po-items-container"></div></div>
                    <button type="button" onclick="addPurchaseOrderItem()">+ 添加物料</button>
                </form>`, () => {
                    submitPurchaseOrder();
                });
            loadSuppliersSelect('po-supplier-id');
            if(reqData) {
                document.getElementById('po-supplier-id').value = reqData.supplier_id || '';
                addPurchaseOrderItem(reqData.material_id, reqData.requested_qty);
            } else {
                addPurchaseOrderItem();
            }
        }

        function addPurchaseOrderItem(materialId, qty) {
            const container = document.getElementById('po-items-container');
            const idx = container.children.length;
            container.innerHTML += `<div class="form-row">
                <select id="po-item-material-${idx}" onchange="updatePoItemPrice(${idx})"></select>
                <input type="number" id="po-item-qty-${idx}" value="${qty || 1}" placeholder="数量">
                <input type="number" id="po-item-price-${idx}" step="0.01" placeholder="单价">
                <button type="button" onclick="removePoItem(${idx})">删除</button>
            </div>`;
            loadMaterialsSelect(`po-item-material-${idx}`);
            if(materialId) {
                document.getElementById(`po-item-material-${idx}`).value = materialId;
            }
        }

        function updatePoItemPrice(idx) {
            const materialId = document.getElementById(`po-item-material-${idx}`).value;
            const material = materialsData.find(m => m.id == materialId);
            if(material) {
                document.getElementById(`po-item-price-${idx}`).value = material.standard_price || 0;
            }
        }

        function removePoItem(idx) {
            document.getElementById(`po-items-container`).children[idx].remove();
        }

        function submitPurchaseOrder() {
            const items = [];
            const container = document.getElementById('po-items-container');
            for(let i = 0; i < container.children.length; i++) {
                items.push({
                    material_id: parseInt(document.getElementById(`po-item-material-${i}`).value),
                    quantity: parseInt(document.getElementById(`po-item-qty-${i}`).value),
                    unit_price: parseFloat(document.getElementById(`po-item-price-${i}`).value)
                });
            }
            const data = {
                account_set_id: currentAccountSetId,
                supplier_id: parseInt(document.getElementById('po-supplier-id').value),
                order_date: document.getElementById('po-date').value,
                status: 'PENDING',
                items: items
            };
            fetch(`${apiBase}/procurement/purchase-orders`, {
                method: 'POST',
                headers: { ...authHeaders, 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    closeModal();
                    loadPurchaseOrders();
                    showMessage(t['success']);
                }
            });
        }

        function loadPreReceipts() {
            fetch(`${apiBase}/procurement/pre-receipts`, { headers: authHeaders })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    const tbody = document.querySelector('#purchase-notice-table tbody');
                    tbody.innerHTML = data.data.items.map(r => `<tr>
                        <td>${r.pre_receipt_no}</td>
                        <td>${r.purchase_order_no || '-'}</td>
                        <td>${r.material_code || '-'}</td>
                        <td>${r.material_name || '-'}</td>
                        <td>${r.expected_qty}</td>
                        <td>${r.expected_arrival_date || '-'}</td>
                        <td>${getStatusText(r.status)}</td>
                        <td>
                            ${r.status === 'PENDING' ? `<button onclick="confirmPreReceipt(${r.id})">确认到货</button>` : ''}
                            ${r.status === 'CONFIRMED' ? `<button onclick="createInboundFromReceipt(${r.id})">采购入库</button>` : ''}
                        </td>
                    </tr>`).join('');
                }
            });
        }

        function showPurchaseNoticeModal() {
            showModal(`<h3>新建来料通知</h3>
                <form id="pre-receipt-form">
                    <div><label>采购订单</label><select id="pr-purchase-order-id"></select></div>
                    <div><label>物料</label><select id="pr-material-id"></select></div>
                    <div><label>预计数量</label><input type="number" id="pr-qty" required></div>
                    <div><label>预计到货日期</label><input type="date" id="pr-date" required></div>
                </form>`, () => {
                    submitPreReceipt();
                });
            loadPurchaseOrdersSelect('pr-purchase-order-id');
            loadMaterialsSelect('pr-material-id');
        }

        function submitPreReceipt() {
            const data = {
                account_set_id: currentAccountSetId,
                purchase_order_id: parseInt(document.getElementById('pr-purchase-order-id').value),
                material_id: parseInt(document.getElementById('pr-material-id').value),
                expected_qty: parseInt(document.getElementById('pr-qty').value),
                expected_arrival_date: document.getElementById('pr-date').value,
                status: 'PENDING'
            };
            fetch(`${apiBase}/procurement/pre-receipts`, {
                method: 'POST',
                headers: { ...authHeaders, 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    closeModal();
                    loadPreReceipts();
                    showMessage('创建成功');
                }
            });
        }

        function confirmPreReceipt(id) {
            fetch(`${apiBase}/procurement/pre-receipts/${id}/confirm`, {
                method: 'PUT',
                headers: authHeaders
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    loadPreReceipts();
                    showMessage('确认到货成功');
                }
            });
        }

        function createInboundFromReceipt(receiptId) {
            fetch(`${apiBase}/procurement/pre-receipts/${receiptId}`, { headers: authHeaders })
            .then(res => res.json()).then(data => {
                if(data.success) {
                    const receipt = data.data;
                    showPurchaseInboundModal(receipt);
                }
            });
        }

        function loadInboundOrders() {
            fetch(`${apiBase}/procurement/inbound-orders`, { headers: authHeaders })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    const tbody = document.querySelector('#purchase-inbound-table tbody');
                    tbody.innerHTML = data.data.items.map(o => `<tr>
                        <td>${o.inbound_no}</td>
                        <td>${o.pre_receipt_no || '-'}</td>
                        <td>${o.items ? o.items[0]?.material_code || '-' : '-'}</td>
                        <td>${o.items ? o.items[0]?.material_name || '-' : '-'}</td>
                        <td>${o.items ? o.items.reduce((s,i) => s + i.quantity, 0) : 0}</td>
                        <td>${o.items ? o.items[0]?.batch_no || '-' : '-'}</td>
                        <td>${getQualityStatusText(o.quality_status)}</td>
                        <td>
                            ${o.status === 'PENDING' ? `<button onclick="completeInboundOrder(${o.id}, 'PASS')">质检合格入库</button>` : ''}
                            ${o.status === 'PENDING' ? `<button onclick="completeInboundOrder(${o.id}, 'FAIL')">质检不合格</button>` : ''}
                        </td>
                    </tr>`).join('');
                }
            });
        }

        function showPurchaseInboundModal(receiptData) {
            showModal(`<h3>新建采购入库</h3>
                <form id="inbound-order-form">
                    <div><label>来料通知单</label><select id="inbound-pre-receipt-id"></select></div>
                    <div><label>入库日期</label><input type="date" id="inbound-date" required></div>
                    <div><label>物料明细</label><div id="inbound-items-container"></div></div>
                    <button type="button" onclick="addInboundItem()">+ 添加物料</button>
                </form>`, () => {
                    submitInboundOrder();
                });
            loadPreReceiptsSelect('inbound-pre-receipt-id');
            if(receiptData) {
                document.getElementById('inbound-pre-receipt-id').value = receiptData.id;
                addInboundItem(receiptData.material_id, receiptData.expected_qty);
            } else {
                addInboundItem();
            }
        }

        function addInboundItem(materialId, qty) {
            const container = document.getElementById('inbound-items-container');
            const idx = container.children.length;
            container.innerHTML += `<div class="form-row">
                <select id="inbound-item-material-${idx}"></select>
                <input type="number" id="inbound-item-qty-${idx}" value="${qty || 1}" placeholder="数量">
                <input type="text" id="inbound-item-batch-${idx}" placeholder="批次号">
                <input type="text" id="inbound-item-location-${idx}" placeholder="库位">
                <input type="number" id="inbound-item-price-${idx}" step="0.01" placeholder="单价">
                <button type="button" onclick="removeInboundItem(${idx})">删除</button>
            </div>`;
            loadMaterialsSelect(`inbound-item-material-${idx}`);
            if(materialId) {
                document.getElementById(`inbound-item-material-${idx}`).value = materialId;
            }
        }

        function removeInboundItem(idx) {
            document.getElementById(`inbound-items-container`).children[idx].remove();
        }

        function submitInboundOrder() {
            const items = [];
            const container = document.getElementById('inbound-items-container');
            for(let i = 0; i < container.children.length; i++) {
                items.push({
                    material_id: parseInt(document.getElementById(`inbound-item-material-${i}`).value),
                    quantity: parseInt(document.getElementById(`inbound-item-qty-${i}`).value),
                    batch_no: document.getElementById(`inbound-item-batch-${i}`).value,
                    location_code: document.getElementById(`inbound-item-location-${i}`).value || 'WH001',
                    unit_price: parseFloat(document.getElementById(`inbound-item-price-${i}`).value) || 0
                });
            }
            const data = {
                account_set_id: currentAccountSetId,
                pre_receipt_id: document.getElementById('inbound-pre-receipt-id').value ? parseInt(document.getElementById('inbound-pre-receipt-id').value) : null,
                inbound_date: document.getElementById('inbound-date').value,
                status: 'PENDING',
                items: items
            };
            fetch(`${apiBase}/procurement/inbound-orders`, {
                method: 'POST',
                headers: { ...authHeaders, 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    closeModal();
                    loadInboundOrders();
                    showMessage('创建成功');
                }
            });
        }

        function completeInboundOrder(id, qualityStatus) {
            fetch(`${apiBase}/procurement/inbound-orders/${id}/complete?quality_status=${qualityStatus}`, {
                method: 'PUT',
                headers: authHeaders
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    loadInboundOrders();
                    showMessage(qualityStatus === 'PASS' ? '入库完成' : '质检不合格');
                }
            });
        }

        function getStatusText(status) {
            const map = { 'PENDING': '待审批', 'APPROVED': '已审批', 'COMPLETED': '已完成', 'CANCELLED': '已取消', 'CONFIRMED': '已确认', 'DELIVERED': '已发货', 'RECEIVED': '已收货' };
            return map[status] || status;
        }

        function getQualityStatusText(status) {
            const map = { 'PENDING': '待质检', 'PASS': '合格', 'FAIL': '不合格' };
            return map[status] || status;
        }

        function loadPurchaseOrdersSelect(selectId) {
            fetch(`${apiBase}/procurement/purchase-orders`, { headers: authHeaders })
            .then(res => res.json()).then(data => {
                const select = document.getElementById(selectId);
                if(data.success) {
                    select.innerHTML = '<option value="">选择采购订单</option>' + data.data.items.map(o => `<option value="${o.id}">${o.po_no}</option>`).join('');
                }
            });
        }

        function loadPreReceiptsSelect(selectId) {
            fetch(`${apiBase}/procurement/pre-receipts`, { headers: authHeaders })
            .then(res => res.json()).then(data => {
                const select = document.getElementById(selectId);
                if(data.success) {
                    select.innerHTML = '<option value="">选择来料通知单</option>' + data.data.items.map(r => `<option value="${r.id}">${r.pre_receipt_no}</option>`).join('');
                }
            });
        }

        function loadOutsourcingRequests() {
            fetch(`${apiBase}/procurement/outsourcing-requests`, { headers: authHeaders })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    const tbody = document.querySelector('#outsourcing-req-table tbody');
                    tbody.innerHTML = data.data.items.map(r => `<tr>
                        <td>${r.request_no}</td>
                        <td>${r.material_code || '-'}</td>
                        <td>${r.material_name || '-'}</td>
                        <td>${r.requested_qty}</td>
                        <td>${r.supplier_name || '-'}</td>
                        <td>${r.planned_date || '-'}</td>
                        <td>${getStatusText(r.status)}</td>
                        <td>
                            ${r.status === 'PENDING' ? `<button onclick="approveOutsourcingRequest(${r.id})">审批</button>` : ''}
                            ${r.status === 'APPROVED' ? `<button onclick="createOutsourcingOrderFromReq(${r.id})">生成委外订单</button>` : ''}
                        </td>
                    </tr>`).join('');
                }
            });
        }

        function showOutsourcingReqModal() {
            showModal(`<h3>创建委外申请</h3>
                <form id="outsourcing-req-form">
                    <div><label>物料</label><select id="osr-material-id"></select></div>
                    <div><label>数量</label><input type="number" id="osr-qty" required></div>
                    <div><label>供应商</label><select id="osr-supplier-id"></select></div>
                    <div><label>需求日期</label><input type="date" id="osr-date" required></div>
                </form>`, () => {
                    submitOutsourcingReq();
                });
            loadMaterialsSelect('osr-material-id');
            loadSuppliersSelect('osr-supplier-id');
        }

        function submitOutsourcingReq() {
            const data = {
                account_set_id: currentAccountSetId,
                material_id: parseInt(document.getElementById('osr-material-id').value),
                requested_qty: parseInt(document.getElementById('osr-qty').value),
                supplier_id: parseInt(document.getElementById('osr-supplier-id').value),
                planned_date: document.getElementById('osr-date').value,
                status: 'PENDING'
            };
            fetch(`${apiBase}/procurement/outsourcing-requests`, {
                method: 'POST',
                headers: { ...authHeaders, 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    closeModal();
                    loadOutsourcingRequests();
                    showMessage('创建成功');
                }
            });
        }

        function approveOutsourcingRequest(id) {
            fetch(`${apiBase}/procurement/outsourcing-requests/${id}/approve`, {
                method: 'PUT',
                headers: authHeaders
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    loadOutsourcingRequests();
                    showMessage('审批成功');
                }
            });
        }

        function createOutsourcingOrderFromReq(reqId) {
            fetch(`${apiBase}/procurement/outsourcing-requests/${reqId}`, { headers: authHeaders })
            .then(res => res.json()).then(data => {
                if(data.success) {
                    const req = data.data;
                    showOutsourcingOrderModal(req);
                }
            });
        }

        function loadOutsourcingOrders() {
            fetch(`${apiBase}/procurement/outsourcing-orders`, { headers: authHeaders })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    const tbody = document.querySelector('#outsourcing-order-table tbody');
                    tbody.innerHTML = data.data.items.map(o => `<tr>
                        <td>${o.order_no}</td>
                        <td>${o.request_no || '-'}</td>
                        <td>${o.supplier_name || '-'}</td>
                        <td>${o.material_code || '-'}</td>
                        <td>${o.material_name || '-'}</td>
                        <td>${o.ordered_qty}</td>
                        <td>${(o.ordered_qty * (o.unit_price || 0)).toFixed(2)}</td>
                        <td>${getStatusText(o.status)}</td>
                        <td>
                            ${o.status === 'APPROVED' ? `<button onclick="showOutsourcingIssueModal(${o.id})">委外投料</button>` : ''}
                        </td>
                    </tr>`).join('');
                }
            });
        }

        function showOutsourcingOrderModal(reqData) {
            showModal(`<h3>创建委外订单</h3>
                <form id="outsourcing-order-form">
                    <div><label>申请单</label><select id="oso-request-id"></select></div>
                    <div><label>供应商</label><select id="oso-supplier-id"></select></div>
                    <div><label>物料</label><select id="oso-material-id"></select></div>
                    <div><label>数量</label><input type="number" id="oso-qty" required></div>
                    <div><label>单价</label><input type="number" id="oso-price" step="0.01" required></div>
                    <div><label>计划日期</label><input type="date" id="oso-date" required></div>
                </form>`, () => {
                    submitOutsourcingOrder();
                });
            loadOutsourcingRequestsSelect('oso-request-id');
            loadSuppliersSelect('oso-supplier-id');
            loadMaterialsSelect('oso-material-id');
            if(reqData) {
                document.getElementById('oso-request-id').value = reqData.id;
                document.getElementById('oso-supplier-id').value = reqData.supplier_id || '';
                document.getElementById('oso-material-id').value = reqData.material_id;
                document.getElementById('oso-qty').value = reqData.requested_qty;
            }
        }

        function submitOutsourcingOrder() {
            const data = {
                account_set_id: currentAccountSetId,
                request_id: document.getElementById('oso-request-id').value ? parseInt(document.getElementById('oso-request-id').value) : null,
                supplier_id: parseInt(document.getElementById('oso-supplier-id').value),
                material_id: parseInt(document.getElementById('oso-material-id').value),
                ordered_qty: parseInt(document.getElementById('oso-qty').value),
                unit_price: parseFloat(document.getElementById('oso-price').value),
                planned_date: document.getElementById('oso-date').value,
                status: 'PENDING'
            };
            fetch(`${apiBase}/procurement/outsourcing-orders`, {
                method: 'POST',
                headers: { ...authHeaders, 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    closeModal();
                    loadOutsourcingOrders();
                    showMessage('创建成功');
                }
            });
        }

        function loadOutsourcingRequestsSelect(selectId) {
            fetch(`${apiBase}/procurement/outsourcing-requests`, { headers: authHeaders })
            .then(res => res.json()).then(data => {
                const select = document.getElementById(selectId);
                if(data.success) {
                    select.innerHTML = '<option value="">选择委外申请单</option>' + data.data.items.map(r => `<option value="${r.id}">${r.request_no}</option>`).join('');
                }
            });
        }

        function loadOutsourcingOrdersSelect(selectId) {
            fetch(`${apiBase}/procurement/outsourcing-orders`, { headers: authHeaders })
            .then(res => res.json()).then(data => {
                const select = document.getElementById(selectId);
                if(data.success) {
                    select.innerHTML = '<option value="">选择委外订单</option>' + data.data.items.map(o => `<option value="${o.id}">${o.order_no}</option>`).join('');
                }
            });
        }

        function loadOutsourcingIssues() {
            fetch(`${apiBase}/procurement/outsourcing-issues`, { headers: authHeaders })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    const tbody = document.querySelector('#outsourcing-issue-table tbody');
                    tbody.innerHTML = data.data.items.map(i => `<tr>
                        <td>${i.issue_no}</td>
                        <td>${i.order_no || '-'}</td>
                        <td>${i.items ? i.items[0]?.material_code || '-' : '-'}</td>
                        <td>${i.items ? i.items[0]?.material_name || '-' : '-'}</td>
                        <td>${i.items ? i.items.reduce((s,item) => s + item.quantity, 0) : 0}</td>
                        <td>${i.items ? i.items[0]?.location_code || '-' : '-'}</td>
                        <td>${getStatusText(i.status)}</td>
                        <td>
                            ${i.status === 'PENDING' ? `<button onclick="confirmOutsourcingIssue(${i.id})">确认投料</button>` : ''}
                        </td>
                    </tr>`).join('');
                }
            });
        }

        function showOutsourcingIssueModal(orderId) {
            showModal(`<h3>创建委外投料</h3>
                <form id="outsourcing-issue-form">
                    <div><label>委外订单</label><select id="osi-order-id" onchange="loadOrderItemsForIssue()"></select></div>
                    <div><label>投料日期</label><input type="date" id="osi-date" required></div>
                    <div><label>操作员</label><input type="text" id="osi-operator" required></div>
                    <div><label>物料明细</label><div id="osi-items-container"></div></div>
                    <button type="button" onclick="addOutsourcingIssueItem()">+ 添加物料</button>
                </form>`, () => {
                    submitOutsourcingIssue();
                });
            loadOutsourcingOrdersSelect('osi-order-id');
            if(orderId) {
                document.getElementById('osi-order-id').value = orderId;
                setTimeout(() => loadOrderItemsForIssue(), 200);
            }
        }

        function loadOrderItemsForIssue() {
            const orderId = document.getElementById('osi-order-id').value;
            if(orderId) {
                fetch(`${apiBase}/procurement/outsourcing-orders/${orderId}`, { headers: authHeaders })
                .then(res => res.json()).then(data => {
                    if(data.success && data.data.material_id) {
                        addOutsourcingIssueItem(data.data.material_id, data.data.ordered_qty);
                    }
                });
            }
        }

        function addOutsourcingIssueItem(materialId, qty) {
            const container = document.getElementById('osi-items-container');
            const idx = container.children.length;
            container.innerHTML += `<div class="form-row">
                <select id="osi-item-material-${idx}"></select>
                <input type="number" id="osi-item-qty-${idx}" value="${qty || 1}" placeholder="数量">
                <input type="text" id="osi-item-location-${idx}" placeholder="库位" value="WH001">
                <button type="button" onclick="removeOsiItem(${idx})">删除</button>
            </div>`;
            loadMaterialsSelect(`osi-item-material-${idx}`);
            if(materialId) {
                document.getElementById(`osi-item-material-${idx}`).value = materialId;
            }
        }

        function removeOsiItem(idx) {
            document.getElementById(`osi-items-container`).children[idx].remove();
        }

        function submitOutsourcingIssue() {
            const items = [];
            const container = document.getElementById('osi-items-container');
            for(let i = 0; i < container.children.length; i++) {
                items.push({
                    material_id: parseInt(document.getElementById(`osi-item-material-${i}`).value),
                    quantity: parseInt(document.getElementById(`osi-item-qty-${i}`).value),
                    location_code: document.getElementById(`osi-item-location-${i}`).value || 'WH001'
                });
            }
            const data = {
                account_set_id: currentAccountSetId,
                outsourcing_order_id: parseInt(document.getElementById('osi-order-id').value),
                issue_date: document.getElementById('osi-date').value,
                status: 'PENDING',
                operator: document.getElementById('osi-operator').value,
                items: items
            };
            fetch(`${apiBase}/procurement/outsourcing-issues`, {
                method: 'POST',
                headers: { ...authHeaders, 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    closeModal();
                    loadOutsourcingIssues();
                    showMessage('创建成功');
                }
            });
        }

        function confirmOutsourcingIssue(id) {
            fetch(`${apiBase}/procurement/outsourcing-issues/${id}/confirm`, {
                method: 'PUT',
                headers: authHeaders
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    loadOutsourcingIssues();
                    showMessage('投料确认成功');
                }
            });
        }

        function loadOutsourcingReplenishes() {
            fetch(`${apiBase}/procurement/outsourcing-replenishes`, { headers: authHeaders })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    const tbody = document.querySelector('#outsourcing-supplement-table tbody');
                    tbody.innerHTML = data.data.items.map(r => `<tr>
                        <td>${r.replenish_no}</td>
                        <td>${r.order_no || '-'}</td>
                        <td>${r.items ? r.items[0]?.material_code || '-' : '-'}</td>
                        <td>${r.items ? r.items[0]?.material_name || '-' : '-'}</td>
                        <td>${r.items ? r.items.reduce((s,item) => s + item.quantity, 0) : 0}</td>
                        <td>${r.reason || '-'}</td>
                        <td>${getStatusText(r.status)}</td>
                        <td></td>
                    </tr>`).join('');
                }
            });
        }

        function showOutsourcingSupplementModal() {
            showModal(`<h3>创建补发单</h3>
                <form id="outsourcing-supplement-form">
                    <div><label>委外订单</label><select id="osr-order-id"></select></div>
                    <div><label>投料单</label><select id="osr-issue-id"></select></div>
                    <div><label>补发日期</label><input type="date" id="osr-date" required></div>
                    <div><label>原因</label><input type="text" id="osr-reason"></div>
                    <div><label>操作员</label><input type="text" id="osr-operator" required></div>
                    <div><label>物料明细</label><div id="osr-items-container"></div></div>
                    <button type="button" onclick="addOutsourcingReplenishItem()">+ 添加物料</button>
                </form>`, () => {
                    submitOutsourcingReplenish();
                });
            loadOutsourcingOrdersSelect('osr-order-id');
            addOutsourcingReplenishItem();
        }

        function addOutsourcingReplenishItem() {
            const container = document.getElementById('osr-items-container');
            const idx = container.children.length;
            container.innerHTML += `<div class="form-row">
                <select id="osr-item-material-${idx}"></select>
                <input type="number" id="osr-item-qty-${idx}" placeholder="数量">
                <button type="button" onclick="removeOsrItem(${idx})">删除</button>
            </div>`;
            loadMaterialsSelect(`osr-item-material-${idx}`);
        }

        function removeOsrItem(idx) {
            document.getElementById(`osr-items-container`).children[idx].remove();
        }

        function submitOutsourcingReplenish() {
            const items = [];
            const container = document.getElementById('osr-items-container');
            for(let i = 0; i < container.children.length; i++) {
                items.push({
                    material_id: parseInt(document.getElementById(`osr-item-material-${i}`).value),
                    quantity: parseInt(document.getElementById(`osr-item-qty-${i}`).value)
                });
            }
            const data = {
                account_set_id: currentAccountSetId,
                outsourcing_order_id: parseInt(document.getElementById('osr-order-id').value),
                issue_id: document.getElementById('osr-issue-id').value ? parseInt(document.getElementById('osr-issue-id').value) : null,
                replenish_date: document.getElementById('osr-date').value,
                status: 'PENDING',
                operator: document.getElementById('osr-operator').value,
                items: items
            };
            fetch(`${apiBase}/procurement/outsourcing-replenishes`, {
                method: 'POST',
                headers: { ...authHeaders, 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    closeModal();
                    loadOutsourcingReplenishes();
                    showMessage('创建成功');
                }
            });
        }

        function loadOutsourcingReturns() {
            fetch(`${apiBase}/procurement/outsourcing-returns`, { headers: authHeaders })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    const tbody = document.querySelector('#outsourcing-return-table tbody');
                    tbody.innerHTML = data.data.items.map(r => `<tr>
                        <td>${r.return_no}</td>
                        <td>${r.order_no || '-'}</td>
                        <td>${r.items ? r.items[0]?.material_code || '-' : '-'}</td>
                        <td>${r.items ? r.items[0]?.material_name || '-' : '-'}</td>
                        <td>${r.items ? r.items.reduce((s,item) => s + item.quantity, 0) : 0}</td>
                        <td>${r.return_reason || '-'}</td>
                        <td>${getStatusText(r.status)}</td>
                        <td></td>
                    </tr>`).join('');
                }
            });
        }

        function showOutsourcingReturnModal() {
            showModal(`<h3>创建退料单</h3>
                <form id="outsourcing-return-form">
                    <div><label>委外订单</label><select id="osrt-order-id"></select></div>
                    <div><label>投料单</label><select id="osrt-issue-id"></select></div>
                    <div><label>退料日期</label><input type="date" id="osrt-date" required></div>
                    <div><label>退料原因</label><input type="text" id="osrt-reason"></div>
                    <div><label>操作员</label><input type="text" id="osrt-operator" required></div>
                    <div><label>物料明细</label><div id="osrt-items-container"></div></div>
                    <button type="button" onclick="addOutsourcingReturnItem()">+ 添加物料</button>
                </form>`, () => {
                    submitOutsourcingReturn();
                });
            loadOutsourcingOrdersSelect('osrt-order-id');
            addOutsourcingReturnItem();
        }

        function addOutsourcingReturnItem() {
            const container = document.getElementById('osrt-items-container');
            const idx = container.children.length;
            container.innerHTML += `<div class="form-row">
                <select id="osrt-item-material-${idx}"></select>
                <input type="number" id="osrt-item-qty-${idx}" placeholder="数量">
                <button type="button" onclick="removeOsrtItem(${idx})">删除</button>
            </div>`;
            loadMaterialsSelect(`osrt-item-material-${idx}`);
        }

        function removeOsrtItem(idx) {
            document.getElementById(`osrt-items-container`).children[idx].remove();
        }

        function submitOutsourcingReturn() {
            const items = [];
            const container = document.getElementById('osrt-items-container');
            for(let i = 0; i < container.children.length; i++) {
                items.push({
                    material_id: parseInt(document.getElementById(`osrt-item-material-${i}`).value),
                    quantity: parseInt(document.getElementById(`osrt-item-qty-${i}`).value)
                });
            }
            const data = {
                account_set_id: currentAccountSetId,
                outsourcing_order_id: parseInt(document.getElementById('osrt-order-id').value),
                issue_id: document.getElementById('osrt-issue-id').value ? parseInt(document.getElementById('osrt-issue-id').value) : null,
                return_date: document.getElementById('osrt-date').value,
                status: 'PENDING',
                return_reason: document.getElementById('osrt-reason').value,
                operator: document.getElementById('osrt-operator').value,
                items: items
            };
            fetch(`${apiBase}/procurement/outsourcing-returns`, {
                method: 'POST',
                headers: { ...authHeaders, 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    closeModal();
                    loadOutsourcingReturns();
                    showMessage('创建成功');
                }
            });
        }

        function loadOutsourcingReceives() {
            fetch(`${apiBase}/procurement/outsourcing-receives`, { headers: authHeaders })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    const tbody = document.querySelector('#outsourcing-receive-table tbody');
                    tbody.innerHTML = data.data.items.map(r => `<tr>
                        <td>${r.receive_no}</td>
                        <td>${r.order_no || '-'}</td>
                        <td>${r.items ? r.items[0]?.material_code || '-' : '-'}</td>
                        <td>${r.items ? r.items[0]?.material_name || '-' : '-'}</td>
                        <td>${r.items ? r.items.reduce((s,item) => s + item.quantity, 0) : 0}</td>
                        <td>${r.expected_arrival_date || '-'}</td>
                        <td>${getStatusText(r.status)}</td>
                        <td>
                            ${r.status === 'PENDING' ? `<button onclick="confirmOutsourcingReceive(${r.id})">确认收货</button>` : ''}
                            ${r.status === 'CONFIRMED' ? `<button onclick="createOutsourcingEstimate(${r.id})">暂估/核算</button>` : ''}
                        </td>
                    </tr>`).join('');
                }
            });
        }

        function showOutsourcingReceiveModal() {
            showModal(`<h3>新建收料通知</h3>
                <form id="outsourcing-receive-form">
                    <div><label>委外订单</label><select id="osrc-order-id"></select></div>
                    <div><label>预计到货日期</label><input type="date" id="osrc-date" required></div>
                    <div><label>物料明细</label><div id="osrc-items-container"></div></div>
                    <button type="button" onclick="addOutsourcingReceiveItem()">+ 添加物料</button>
                </form>`, () => {
                    submitOutsourcingReceive();
                });
            loadOutsourcingOrdersSelect('osrc-order-id');
            addOutsourcingReceiveItem();
        }

        function addOutsourcingReceiveItem() {
            const container = document.getElementById('osrc-items-container');
            const idx = container.children.length;
            container.innerHTML += `<div class="form-row">
                <select id="osrc-item-material-${idx}"></select>
                <input type="number" id="osrc-item-qty-${idx}" placeholder="数量">
                <button type="button" onclick="removeOsrcItem(${idx})">删除</button>
            </div>`;
            loadMaterialsSelect(`osrc-item-material-${idx}`);
        }

        function removeOsrcItem(idx) {
            document.getElementById(`osrc-items-container`).children[idx].remove();
        }

        function submitOutsourcingReceive() {
            const items = [];
            const container = document.getElementById('osrc-items-container');
            for(let i = 0; i < container.children.length; i++) {
                items.push({
                    material_id: parseInt(document.getElementById(`osrc-item-material-${i}`).value),
                    quantity: parseInt(document.getElementById(`osrc-item-qty-${i}`).value)
                });
            }
            const data = {
                account_set_id: currentAccountSetId,
                outsourcing_order_id: parseInt(document.getElementById('osrc-order-id').value),
                expected_arrival_date: document.getElementById('osrc-date').value,
                status: 'PENDING',
                items: items
            };
            fetch(`${apiBase}/procurement/outsourcing-receives`, {
                method: 'POST',
                headers: { ...authHeaders, 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    closeModal();
                    loadOutsourcingReceives();
                    showMessage('创建成功');
                }
            });
        }

        function confirmOutsourcingReceive(id) {
            fetch(`${apiBase}/procurement/outsourcing-receives/${id}/confirm`, {
                method: 'PUT',
                headers: authHeaders
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    loadOutsourcingReceives();
                    showMessage('收货确认成功');
                }
            });
        }

        function loadOutsourcingInvoices() {
            fetch(`${apiBase}/procurement/outsourcing-invoices`, { headers: authHeaders })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    const tbody = document.querySelector('#outsourcing-invoice-table tbody');
                    tbody.innerHTML = data.data.items.map(i => `<tr>
                        <td>${i.invoice_no}</td>
                        <td>${i.order_no || '-'}</td>
                        <td>${i.supplier_name || '-'}</td>
                        <td>${i.amount || 0}</td>
                        <td>${i.tax_amount || 0}</td>
                        <td>${i.invoice_date || '-'}</td>
                        <td>${getStatusText(i.status)}</td>
                        <td></td>
                    </tr>`).join('');
                }
            });
        }

        function showOutsourcingInvoiceModal() {
            showModal(`<h3>识别发票</h3>
                <form id="outsourcing-invoice-form">
                    <div><label>委外订单</label><select id="osiv-order-id"></select></div>
                    <div><label>收料通知</label><select id="osiv-receive-id"></select></div>
                    <div><label>供应商</label><select id="osiv-supplier-id"></select></div>
                    <div><label>金额</label><input type="number" id="osiv-amount" step="0.01" required></div>
                    <div><label>税额</label><input type="number" id="osiv-tax" step="0.01"></div>
                    <div><label>开票日期</label><input type="date" id="osiv-date" required></div>
                </form>`, () => {
                    submitOutsourcingInvoice();
                });
            loadOutsourcingOrdersSelect('osiv-order-id');
            loadSuppliersSelect('osiv-supplier-id');
        }

        function submitOutsourcingInvoice() {
            const amount = parseFloat(document.getElementById('osiv-amount').value);
            const tax = parseFloat(document.getElementById('osiv-tax').value) || 0;
            const data = {
                account_set_id: currentAccountSetId,
                outsourcing_order_id: parseInt(document.getElementById('osiv-order-id').value),
                receive_id: document.getElementById('osiv-receive-id').value ? parseInt(document.getElementById('osiv-receive-id').value) : null,
                supplier_id: parseInt(document.getElementById('osiv-supplier-id').value),
                amount: amount,
                tax_amount: tax,
                total_amount: amount + tax,
                invoice_date: document.getElementById('osiv-date').value,
                status: 'CONFIRMED'
            };
            fetch(`${apiBase}/procurement/outsourcing-invoices`, {
                method: 'POST',
                headers: { ...authHeaders, 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    closeModal();
                    loadOutsourcingInvoices();
                    showMessage('创建成功');
                }
            });
        }

        function loadOutsourcingEstimates() {
            fetch(`${apiBase}/procurement/outsourcing-estimates`, { headers: authHeaders })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    const tbody = document.querySelector('#outsourcing-estimate-table tbody');
                    tbody.innerHTML = data.data.items.map(e => `<tr>
                        <td>${e.estimate_no}</td>
                        <td>${e.receive_no || '-'}</td>
                        <td>${e.items ? e.items[0]?.material_code || '-' : '-'}</td>
                        <td>${e.items ? e.items[0]?.material_name || '-' : '-'}</td>
                        <td>${e.items ? e.items.reduce((s,item) => s + item.quantity, 0) : 0}</td>
                        <td>${e.estimated_amount || 0}</td>
                        <td>${getStatusText(e.status)}</td>
                        <td>
                            ${e.status === 'PENDING' ? `<button onclick="confirmOutsourcingEstimate(${e.id})">确认暂估</button>` : ''}
                        </td>
                    </tr>`).join('');
                }
            });
        }

        function showOutsourcingEstimateModal(receiveId) {
            showModal(`<h3>创建暂估</h3>
                <form id="outsourcing-estimate-form">
                    <div><label>收料通知</label><select id="ose-receive-id"></select></div>
                    <div><label>委外订单</label><select id="ose-order-id"></select></div>
                    <div><label>暂估金额</label><input type="number" id="ose-amount" step="0.01" required></div>
                    <div><label>物料明细</label><div id="ose-items-container"></div></div>
                    <button type="button" onclick="addOutsourcingEstimateItem()">+ 添加物料</button>
                </form>`, () => {
                    submitOutsourcingEstimate();
                });
            loadOutsourcingReceivesSelect('ose-receive-id');
            loadOutsourcingOrdersSelect('ose-order-id');
            addOutsourcingEstimateItem();
        }

        function loadOutsourcingReceivesSelect(selectId) {
            fetch(`${apiBase}/procurement/outsourcing-receives`, { headers: authHeaders })
            .then(res => res.json()).then(data => {
                const select = document.getElementById(selectId);
                if(data.success) {
                    select.innerHTML = '<option value="">选择收料通知单</option>' + data.data.items.map(r => `<option value="${r.id}">${r.receive_no}</option>`).join('');
                }
            });
        }

        function addOutsourcingEstimateItem() {
            const container = document.getElementById('ose-items-container');
            const idx = container.children.length;
            container.innerHTML += `<div class="form-row">
                <select id="ose-item-material-${idx}"></select>
                <input type="number" id="ose-item-qty-${idx}" placeholder="数量">
                <input type="number" id="ose-item-price-${idx}" step="0.01" placeholder="暂估单价">
                <button type="button" onclick="removeOseItem(${idx})">删除</button>
            </div>`;
            loadMaterialsSelect(`ose-item-material-${idx}`);
        }

        function removeOseItem(idx) {
            document.getElementById(`ose-items-container`).children[idx].remove();
        }

        function submitOutsourcingEstimate() {
            const items = [];
            const container = document.getElementById('ose-items-container');
            for(let i = 0; i < container.children.length; i++) {
                items.push({
                    material_id: parseInt(document.getElementById(`ose-item-material-${i}`).value),
                    quantity: parseInt(document.getElementById(`ose-item-qty-${i}`).value),
                    estimated_cost: parseFloat(document.getElementById(`ose-item-price-${i}`).value) || 0
                });
            }
            const data = {
                account_set_id: currentAccountSetId,
                receive_id: document.getElementById('ose-receive-id').value ? parseInt(document.getElementById('ose-receive-id').value) : null,
                outsourcing_order_id: document.getElementById('ose-order-id').value ? parseInt(document.getElementById('ose-order-id').value) : null,
                estimated_amount: parseFloat(document.getElementById('ose-amount').value),
                status: 'PENDING',
                items: items
            };
            fetch(`${apiBase}/procurement/outsourcing-estimates`, {
                method: 'POST',
                headers: { ...authHeaders, 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    closeModal();
                    loadOutsourcingEstimates();
                    showMessage('创建成功');
                }
            });
        }

        function confirmOutsourcingEstimate(id) {
            fetch(`${apiBase}/procurement/outsourcing-estimates/${id}/confirm`, {
                method: 'PUT',
                headers: authHeaders
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    loadOutsourcingEstimates();
                    showMessage('暂估确认成功');
                }
            });
        }

        function loadOutsourcingAccounts() {
            fetch(`${apiBase}/procurement/outsourcing-accounts`, { headers: authHeaders })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    const tbody = document.querySelector('#outsourcing-account-table tbody');
                    tbody.innerHTML = data.data.items.map(a => `<tr>
                        <td>${a.account_no}</td>
                        <td>${a.estimate_no || '-'}</td>
                        <td>${a.invoice_no || '-'}</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                        <td>${a.actual_amount || 0}</td>
                        <td>${a.variance_amount || 0}</td>
                        <td>${getStatusText(a.status)}</td>
                        <td></td>
                    </tr>`).join('');
                }
            });
        }

        function showOutsourcingAccountModal() {
            showModal(`<h3>核算入库</h3>
                <form id="outsourcing-account-form">
                    <div><label>暂估单</label><select id="osa-estimate-id"></select></div>
                    <div><label>发票</label><select id="osa-invoice-id"></select></div>
                    <div><label>收料通知</label><select id="osa-receive-id"></select></div>
                    <div><label>实际金额</label><input type="number" id="osa-actual" step="0.01" required></div>
                    <div><label>暂估金额</label><input type="number" id="osa-estimated" step="0.01" required></div>
                </form>`, () => {
                    submitOutsourcingAccount();
                });
            loadOutsourcingEstimatesSelect('osa-estimate-id');
        }

        function loadOutsourcingEstimatesSelect(selectId) {
            fetch(`${apiBase}/procurement/outsourcing-estimates`, { headers: authHeaders })
            .then(res => res.json()).then(data => {
                const select = document.getElementById(selectId);
                if(data.success) {
                    select.innerHTML = '<option value="">选择暂估单</option>' + data.data.items.map(e => `<option value="${e.id}">${e.estimate_no}</option>`).join('');
                }
            });
        }

        function submitOutsourcingAccount() {
            const data = {
                account_set_id: currentAccountSetId,
                estimate_id: parseInt(document.getElementById('osa-estimate-id').value),
                invoice_id: document.getElementById('osa-invoice-id').value ? parseInt(document.getElementById('osa-invoice-id').value) : null,
                receive_id: document.getElementById('osa-receive-id').value ? parseInt(document.getElementById('osa-receive-id').value) : null,
                actual_amount: parseFloat(document.getElementById('osa-actual').value),
                estimated_amount: parseFloat(document.getElementById('osa-estimated').value),
                status: 'COMPLETED'
            };
            fetch(`${apiBase}/procurement/outsourcing-accounts`, {
                method: 'POST',
                headers: { ...authHeaders, 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    closeModal();
                    loadOutsourcingAccounts();
                    showMessage('核算完成');
                }
            });
        }

        function createOutsourcingEstimate(receiveId) {
            showOutsourcingEstimateModal(receiveId);
        }

        function renderPurchase() {
            const t = translations[currentLang];
            return `<div class="content-header"><h2>${t['purchase-title']}</h2><p>${t['purchase-desc']}</p></div>
                <div class="card"><div class="card-title">${t['purchase-orders']}</div>
                    <div style="text-align:center;padding:40px;color:#7f8c8d;">${t['no-data']}</div>
                </div>`;
        }
        
        function renderProduction() {
            const t = translations[currentLang];
            return `<div class="content-header"><h2>${t['production-title']}</h2><p>${t['production-desc']}</p></div>
                <div class="card"><div class="card-title">${t['production-orders']}</div>
                    <div style="text-align:center;padding:40px;color:#7f8c8d;">${t['no-data']}</div>
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
            try { if (event && event.target) event.target.classList.add('active'); } catch(e) {}
            
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
                    <div id="balance-sheet-content">${t['loading']}</div>
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
                    <div id="profit-statement-content">${t['loading']}</div>
                </div>
                <div class="card">
                    <h3>${t['cash-flow']}</h3>
                    <div id="cash-flow-content">${t['loading']}</div>
                </div>
            `;
        }
        
        function renderGeneralLedger() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">${t['finance-general']}</div>
                <button class="btn btn-primary add-btn" onclick="showVoucherForm()">+ ${t['generate-voucher']}</button>
                <div id="voucher-list">${t['loading']}</div>
            </div>`;
        }
        
        function renderARAP() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">${t['finance-arap']}</div>
                <div id="arap-content">${t['loading']}</div>
            </div>`;
        }
        
        function renderCashManagement() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">${t['finance-cash']}</div>
                <div id="cash-content">${t['loading']}</div>
            </div>`;
        }
        
        function renderFixedAssets() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">${t['finance-asset']}</div>
                <button class="btn btn-primary add-btn" onclick="showAssetForm()">+ ${t['add-data']}</button>
                <table class="data-table" id="asset-table">
                    <thead><tr><th>${t['code']}</th><th>${t['name']}</th><th>${t['category']}</th><th>${t['price']}</th><th>${t['status']}</th><th>${t['action']}</th></tr></thead>
                    <tbody id="asset-tbody"><tr><td colspan="6" style="text-align:center;">${t['loading']}</td></tr></tbody>
                </table>
            </div>`;
        }
        
        function renderPayroll() {
            const t = translations[currentLang];
            return `<div class="card"><div class="card-title">${t['finance-payroll']}</div>
                <div id="payroll-content">${t['loading']}</div>
            </div>`;
        }
        
        function renderCrossborder() {
            const t = translations[currentLang];
            return `<div class="content-header"><h2>${t['crossborder-title']}</h2><p>${t['crossborder-desc']}</p></div>
                <div class="card">
                    <div class="card-title">${t['product']}</div>
                    <div style="text-align:center;padding:40px;color:#7f8c8d;">${t['no-data']}</div>
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
                                    <tr><td>${currentVoucherDraft.debit?.摘要||'购买货物'}</td><td>${currentVoucherDraft.debit?.科目||'库存商品'}</td><td>${currentVoucherDraft.debit?.金额?.toFixed(2)||''}</td><td></td></tr>
                                    <tr><td>${currentVoucherDraft.debit_tax?.摘要||'进项税额'}</td><td>${currentVoucherDraft.debit_tax?.科目||'应交税费-应交增值税-进项税额'}</td><td>${currentVoucherDraft.debit_tax?.金额?.toFixed(2)||''}</td><td></td></tr>
                                    <tr><td>${currentVoucherDraft.credit?.摘要||'应付货款'}</td><td>${currentVoucherDraft.credit?.科目||'应付账款'}</td><td></td><td>${currentVoucherDraft.credit?.金额?.toFixed(2)||''}</td></tr>
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
                const response = await fetch('/api/v1/finance/reports/balance-sheet');
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
                const response = await fetch('/api/v1/finance/reports/update', {
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
                const response = await fetch('/api/v1/finance/reports/profit-statement');
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
                const response = await fetch('/api/v1/finance/reports/cash-flow');
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
        }
        
        function clearScanData() {
            document.getElementById('scan-input').value = '';
            document.getElementById('scan-results').innerHTML = '';
        }
        
        function handleScanInput(event) {
            if (event.key === 'Enter') {
                const code = event.target.value.trim();
                if (code) {
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
                debit: { '科目': '库存商品', '金额': currentInvoiceInfo.total_amount, '摘要': '购买货物' },
                debit_tax: { '科目': '应交税费-应交增值税-进项税额', '金额': currentInvoiceInfo.tax_amount, '摘要': '进项税额' },
                credit: { '科目': '应付账款', '金额': currentInvoiceInfo.total_with_tax, '摘要': '应付货款' }
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
                    { account_code: '1405', account_name: '库存商品', debit: currentVoucherDraft.debit.金额, credit: null, summary: currentVoucherDraft.debit.摘要||'购买货物', auxiliary_info: null },
                    { account_code: '22210101', account_name: '应交税费-应交增值税-进项税额', debit: currentVoucherDraft.debit_tax.金额, credit: null, summary: currentVoucherDraft.debit_tax.摘要||'进项税额', auxiliary_info: null },
                    { account_code: '2202', account_name: '应付账款', debit: null, credit: currentVoucherDraft.credit.金额, summary: currentVoucherDraft.credit.摘要||'应付货款', auxiliary_info: null }
                ]
            };
            
            try {
                const response = await fetch('/api/v1/finance/vouchers', {
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
        }
        
        function showAssetForm() {
        }
        
        async function loadAssets() {
            try {
                const response = await fetch('/api/v1/finance/fixed-assets');
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
        
        function showSalesOrderModal() {
            document.getElementById('sales-order-modal').classList.add('show');
            document.getElementById('so-no').value = 'SO-' + new Date().toISOString().replace(/[-T:.Z]/g, '').slice(0, 14);
            document.getElementById('sales-order-form').onsubmit = function(event) {
                event.preventDefault();
                handleCreateSalesOrder(event);
            };
        }

        let currentEditingOrderId = null;

        function closeSalesOrderModal() {
            document.getElementById('sales-order-modal').classList.remove('show');
            document.getElementById('sales-order-form').reset();
            document.getElementById('so-items-container').innerHTML = `
                <div class="so-item-row" style="display:flex;gap:10px;margin-bottom:10px;">
                    <input type="number" class="so-item-material-id" placeholder="物料ID" style="width:100px;">
                    <input type="number" class="so-item-quantity" placeholder="数量" style="width:80px;">
                    <input type="number" class="so-item-unit-price" placeholder="单价" style="width:100px;">
                    <input type="text" class="so-item-unit" placeholder="单位" style="width:60px;">
                </div>
            `;
            document.getElementById('delete-so-btn').style.display = 'none';
            document.querySelector('#sales-order-form button[type="submit"]').textContent = '创建订单';
            document.querySelector('.modal h3').textContent = '创建销售订单';
            currentEditingOrderId = null;
        }

        function handleDeleteSalesOrder() {
            if (!currentEditingOrderId) return;
            deleteSalesOrder(currentEditingOrderId);
        }

        async function fetchExchangeRate() {
            const currency = document.getElementById('so-currency').value;
            if (currency === 'CNY') {
                document.getElementById('so-exchange-rate').value = '1.0';
                return;
            }
            
            try {
                const response = await fetch('/api/v1/crossborder/exchange-rates?currencies=' + currency);
                const result = await response.json();
                
                if (result.data && result.data.rates && result.data.rates[currency]) {
                    document.getElementById('so-exchange-rate').value = result.data.rates[currency].toFixed(4);
                } else {
                    alert('获取汇率失败，使用默认汇率');
                }
            } catch (error) {
                alert('获取汇率失败，请检查网络连接');
            }
        }

        function addSOItemRow() {
            const container = document.getElementById('so-items-container');
            const row = document.createElement('div');
            row.className = 'so-item-row';
            row.style.display = 'flex';
            row.style.gap = '10px';
            row.style.marginBottom = '10px';
            row.innerHTML = `
                <input type="number" class="so-item-material-id" placeholder="物料ID" style="width:100px;">
                <input type="number" class="so-item-quantity" placeholder="数量" style="width:80px;">
                <input type="number" class="so-item-unit-price" placeholder="单价" style="width:100px;">
                <input type="text" class="so-item-unit" placeholder="单位" style="width:60px;">
                <button type="button" class="btn btn-danger" onclick="this.parentElement.remove()" style="width:50px;">删除</button>
            `;
            container.appendChild(row);
        }

        async function handleCreateSalesOrder(event) {
            event.preventDefault();
            
            const customerId = document.getElementById('so-customer-id').value;
            const soNo = document.getElementById('so-no').value;
            const tradeTerm = document.getElementById('so-trade-term').value;
            const currency = document.getElementById('so-currency').value;
            const exchangeRate = parseFloat(document.getElementById('so-exchange-rate').value);
            
            const items = [];
            document.querySelectorAll('.so-item-row').forEach(row => {
                const materialId = row.querySelector('.so-item-material-id').value;
                const quantity = row.querySelector('.so-item-quantity').value;
                const unitPrice = row.querySelector('.so-item-unit-price').value;
                const unit = row.querySelector('.so-item-unit').value;
                if (materialId && quantity) {
                    items.push({
                        material_id: parseInt(materialId),
                        quantity: parseInt(quantity),
                        unit_price: parseFloat(unitPrice) || 0
                    });
                }
            });
            
            if (items.length === 0) {
                alert('请至少添加一个商品');
                return;
            }
            
            try {
                const response = await fetch('/api/v1/sales/sales_orders/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        so_no: soNo,
                        customer_id: customerId ? parseInt(customerId) : null,
                        trade_term: tradeTerm,
                        currency: currency,
                        exchange_rate: exchangeRate,
                        account_set_id: 1,
                        items: items
                    })
                });
                
                const result = await response.json();
                
                if (result.success || result.id) {
                    alert('销售订单创建成功！');
                    closeSalesOrderModal();
                    loadSalesOrders();
                } else {
                    alert('创建失败：' + (result.message || '未知错误'));
                }
            } catch (error) {
                alert('创建失败，请检查API服务是否正常运行');
            }
        }

        let materialsCache = {};

async function loadMaterialsCache() {
    try {
        const response = await fetch('/api/v1/materials/materials/');
        const result = await response.json();
        const materials = Array.isArray(result) ? result : (result.data || []);
        materialsCache = {};
        materials.forEach(m => {
            materialsCache[m.id] = m.name || m.material_name || '未知物料';
        });
    } catch (error) {
        console.log('加载物料缓存失败');
    }
}

async function loadSalesOrders() {
            await loadMaterialsCache();
            
            try {
                const response = await fetch('/api/v1/sales/sales_orders/');
                const result = await response.json();
                
                const tbody = document.getElementById('sales-orders-tbody');
                if (!tbody) return;
                
                if (!result || (Array.isArray(result) && result.length === 0)) {
                    tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;color:#999;">暂无数据</td></tr>';
                    return;
                }
                
                const orders = Array.isArray(result) ? result : (result.data || []);
                
                tbody.innerHTML = orders.map(order => {
                    const totalAmount = order.items ? order.items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0) : 0;
                    const materialNames = order.items ? order.items.map(i => materialsCache[i.material_id] || '未知').join(',') : '-';
                    return `<tr>
                        <td>${order.so_no}</td>
                        <td>${order.customer_id || '-'}</td>
                        <td>${order.items ? order.items.map(i => i.material_id).join(',') : '-'}</td>
                        <td>${materialNames}</td>
                        <td>${order.items ? order.items.reduce((sum, i) => sum + i.quantity, 0) : 0}</td>
                        <td>¥${totalAmount.toFixed(2)}</td>
                        <td>${order.trade_term || '-'}</td>
                        <td>${order.status === 'PENDING_PRODUCTION' ? '库存不足' : '充足'}</td>
                        <td><span class="status ${order.status.toLowerCase().replace('_', '-')}">${getStatusText(order.status)}</span></td>
                        <td>
                            ${order.status === 'PENDING' ? `<button class="btn btn-secondary" onclick="approveSalesOrder(${order.id})">审批</button>` : ''}
                            ${order.status === 'APPROVED' ? `<button class="btn btn-primary" onclick="createDelivery(${order.id})">生成发货通知</button>` : ''}
                            ${order.status === 'PENDING' || order.status === 'PENDING_PRODUCTION' ? `<button class="btn btn-warning" onclick="editSalesOrder(${order.id})">修改</button>` : ''}
                            ${order.status === 'PENDING' ? `<button class="btn btn-danger" onclick="deleteSalesOrder(${order.id})">删除</button>` : ''}
                        </td>
                    </tr>`;
                }).join('');
            } catch (error) {
                const tbody = document.getElementById('sales-orders-tbody');
                if (tbody) {
                    tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;color:#999;">加载失败</td></tr>';
                }
            }
        }

        async function approveSalesOrder(orderId) {
            try {
                const response = await fetch(`/api/v1/sales/sales_orders/${orderId}/approve`, {
                    method: 'POST'
                });
                const result = await response.json();
                
                if (result.success || result.status === 'APPROVED') {
                    alert('审批通过');
                } else {
                    alert(result.message || '审批失败');
                }
                loadSalesOrders();
            } catch (error) {
                alert('操作失败');
            }
        }

        async function createDelivery(orderId) {
            try {
                const response = await fetch(`/api/v1/sales/sales_orders/${orderId}/create_delivery`, {
                    method: 'POST'
                });
                const result = await response.json();
                
                if (result.success) {
                    alert('发货通知单创建成功');
                } else {
                    alert(result.message || '创建失败');
                }
                loadSalesOrders();
            } catch (error) {
                alert('操作失败');
            }
        }

        async function deleteSalesOrder(orderId) {
            if (!confirm('确定要删除这个销售订单吗？')) {
                return;
            }
            try {
                const response = await fetch(`/api/v1/sales/sales_orders/${orderId}`, {
                    method: 'DELETE'
                });
                const result = await response.json();
                
                if (result.message || response.status === 200) {
                    alert('删除成功');
                } else {
                    alert(result.detail || '删除失败');
                }
                loadSalesOrders();
            } catch (error) {
                alert('操作失败');
            }
        }

        async function editSalesOrder(orderId) {
            try {
                const response = await fetch(`/api/v1/sales/sales_orders/${orderId}`);
                const order = await response.json();
                
                document.getElementById('so-customer-id').value = order.customer_id || '';
                document.getElementById('so-no').value = order.so_no;
                document.getElementById('so-trade-term').value = order.trade_term || 'FOB';
                document.getElementById('so-currency').value = order.currency || 'CNY';
                document.getElementById('so-exchange-rate').value = order.exchange_rate || 1.0;
                
                const container = document.getElementById('so-items-container');
                container.innerHTML = '';
                if (order.items) {
                    order.items.forEach((item, index) => {
                        const row = document.createElement('div');
                        row.className = 'so-item-row';
                        row.style.display = 'flex';
                        row.style.gap = '10px';
                        row.style.marginBottom = '10px';
                        row.innerHTML = `
                            <input type="number" class="so-item-material-id" value="${item.material_id}" placeholder="物料ID" style="width:100px;">
                            <input type="number" class="so-item-quantity" value="${item.quantity}" placeholder="数量" style="width:80px;">
                            <input type="number" class="so-item-unit-price" value="${item.unit_price}" placeholder="单价" style="width:100px;">
                            <input type="text" class="so-item-unit" placeholder="单位" style="width:60px;">
                            ${order.items.length > 1 ? `<button type="button" class="btn btn-danger" onclick="this.parentElement.remove()" style="width:50px;">删除</button>` : ''}
                        `;
                        container.appendChild(row);
                    });
                }
                
                document.getElementById('sales-order-form').onsubmit = async function(event) {
                    event.preventDefault();
                    await handleUpdateSalesOrder(orderId);
                };
                
                currentEditingOrderId = orderId;
                document.getElementById('delete-so-btn').style.display = 'inline-block';
                document.querySelector('#sales-order-form button[type="submit"]').textContent = '保存修改';
                document.querySelector('.modal h3').textContent = '编辑销售订单';
                
                document.getElementById('sales-order-modal').classList.add('show');
            } catch (error) {
                alert('加载订单失败');
            }
        }

        async function handleUpdateSalesOrder(orderId) {
            const customerId = document.getElementById('so-customer-id').value;
            const soNo = document.getElementById('so-no').value;
            const tradeTerm = document.getElementById('so-trade-term').value;
            const currency = document.getElementById('so-currency').value;
            const exchangeRate = parseFloat(document.getElementById('so-exchange-rate').value);
            
            const items = [];
            document.querySelectorAll('.so-item-row').forEach(row => {
                const materialId = row.querySelector('.so-item-material-id').value;
                const quantity = row.querySelector('.so-item-quantity').value;
                const unitPrice = row.querySelector('.so-item-unit-price').value;
                if (materialId && quantity) {
                    items.push({
                        material_id: parseInt(materialId),
                        quantity: parseInt(quantity),
                        unit_price: parseFloat(unitPrice) || 0
                    });
                }
            });
            
            if (items.length === 0) {
                alert('请至少添加一个商品');
                return;
            }
            
            try {
                const response = await fetch(`/api/v1/sales/sales_orders/${orderId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        so_no: soNo,
                        customer_id: customerId ? parseInt(customerId) : null,
                        trade_term: tradeTerm,
                        currency: currency,
                        exchange_rate: exchangeRate,
                        account_set_id: 1,
                        items: items
                    })
                });
                
                const result = await response.json();
                
                if (result.id) {
                    alert('修改成功');
                } else {
                    alert(result.detail || '修改失败');
                }
                
                closeSalesOrderModal();
                document.getElementById('sales-order-form').onsubmit = handleCreateSalesOrder;
                loadSalesOrders();
            } catch (error) {
                alert('修改失败');
            }
        }

        async function loadPendingSalesOrders() {
            await loadMaterialsCache();
            
            try {
                const response = await fetch('/api/v1/sales/sales_orders/?status=PENDING_PRODUCTION');
                const result = await response.json();
                
                const tbody = document.getElementById('pending-sales-orders');
                if (!tbody) return;
                
                const orders = Array.isArray(result) ? result : (result.data || []);
                
                if (orders.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#999;">暂无库存不足的销售订单</td></tr>';
                    return;
                }
                
                tbody.innerHTML = orders.map(order => {
                    const totalAmount = order.items ? order.items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0) : 0;
                    const materialNames = order.items ? order.items.map(i => materialsCache[i.material_id] || '未知').join(',') : '-';
                    return `<tr>
                        <td>${order.so_no}</td>
                        <td>${order.items ? order.items.map(i => i.material_id).join(',') : '-'}</td>
                        <td>${materialNames}</td>
                        <td>${order.items ? order.items.reduce((sum, i) => sum + i.quantity, 0) : 0}</td>
                        <td>¥${totalAmount.toFixed(2)}</td>
                        <td><button class="btn btn-primary" onclick="runMRPForOrder(${order.id})">执行MRP运算</button></td>
                    </tr>`;
                }).join('');
            } catch (error) {
                const tbody = document.getElementById('pending-sales-orders');
                if (tbody) {
                    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#999;">加载失败</td></tr>';
                }
            }
        }

        async function runMRP() {
            const source = document.getElementById('mrp-source').value;
            const date = document.getElementById('mrp-date').value;
            
            let sourceType = null;
            if (source === 'sales') sourceType = 'SALES_ORDER';
            else if (source === 'forecast') sourceType = 'FORECAST';
            
            try {
                const response = await fetch('/api/v1/plan/mrp/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        account_set_id: 1,
                        source_type: sourceType
                    })
                });
                
                const result = await response.json();
                
                if (result.success || result.mrp_run_no) {
                    displayMRPResult(result);
                } else {
                    alert(result.message || 'MRP运算失败');
                }
            } catch (error) {
                alert('MRP运算失败，请检查API服务');
            }
        }

        async function runMRPForOrder(orderId) {
            try {
                const response = await fetch('/api/v1/plan/mrp/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        account_set_id: 1,
                        source_type: 'SALES_ORDER',
                        source_id: orderId
                    })
                });
                
                const result = await response.json();
                
                if (result.success || result.mrp_run_no) {
                    alert('MRP运算完成！');
                    displayMRPResult(result);
                    loadPendingSalesOrders();
                } else {
                    alert(result.message || 'MRP运算失败');
                }
            } catch (error) {
                alert('MRP运算失败');
            }
        }

        function displayMRPResult(result) {
            const container = document.getElementById('mrp-result');
            if (!container) return;
            
            const data = result.data || result;
            
            let html = `<div class="card">
                <div class="card-title">MRP运算结果 - ${data.mrp_run_no}</div>
                <div style="display:flex;gap:20px;margin-bottom:15px;">
                    <div><strong>需求来源:</strong> ${data.total_demand_items} 项</div>
                    <div><strong>运算结果:</strong> ${data.total_mrp_results} 条</div>
                    <div><strong>计划订单:</strong> ${data.total_planned_orders} 张</div>
                    <div><strong>采购订单:</strong> ${data.total_purchase_orders || 0} 张</div>
                    <div><strong>生产订单:</strong> ${data.total_production_orders || 0} 张</div>
                    <div><strong>委外订单:</strong> ${data.total_outsourcing_orders || 0} 张</div>
                </div>
            </div>`;
            
            if (data.mrp_results && data.mrp_results.length > 0) {
                html += `<div class="card" style="margin-top:20px;">
                    <div class="card-title">物料需求明细</div>
                    <table class="data-table">
                        <thead><tr><th>BOM层级</th><th>物料编码</th><th>物料名称</th><th>物料属性</th><th>毛需求</th><th>现有库存</th><th>在途量</th><th>安全库存</th><th>净需求</th><th>损耗率</th><th>计划数量</th><th>计划日期</th><th>下达日期</th></tr></thead>
                        <tbody>`;
                
                data.mrp_results.forEach(res => {
                    const materialName = materialsCache[res.material_id] || '未知';
                    const property = res.material_property === 'INHOUSE' ? '自制' : (res.material_property === 'OUTSOURCING' ? '委外' : '采购');
                    const plannedDate = res.planned_date ? res.planned_date : '-';
                    const releaseDate = res.planned_release_date ? res.planned_release_date : '-';
                    html += `<tr>
                        <td>L${res.bom_level}</td>
                        <td>${res.material_id}</td>
                        <td>${materialName}</td>
                        <td>${property}</td>
                        <td>${parseFloat(res.gross_requirement).toFixed(2)}</td>
                        <td>${parseFloat(res.on_hand_qty).toFixed(2)}</td>
                        <td>${parseFloat(res.on_order_qty || 0).toFixed(2)}</td>
                        <td>${parseFloat(res.safety_stock || 0).toFixed(2)}</td>
                        <td>${parseFloat(res.net_requirement).toFixed(2)}</td>
                        <td>${parseFloat(res.loss_rate || 0).toFixed(2)}%</td>
                        <td>${parseFloat(res.planned_order_qty).toFixed(2)}</td>
                        <td>${plannedDate}</td>
                        <td>${releaseDate}</td>
                    </tr>`;
                });
                
                html += `</tbody></table></div>`;
            }
            
            if (data.planned_orders && data.planned_orders.length > 0) {
                html += `<div class="card" style="margin-top:20px;">
                    <div class="card-title">生成的计划订单</div>
                    <table class="data-table">
                        <thead><tr><th>计划订单号</th><th>物料编码</th><th>物料名称</th><th>计划数量</th><th>类型</th><th>计划日期</th><th>状态</th><th>操作</th></tr></thead>
                        <tbody>`;
                
                data.planned_orders.forEach(order => {
                    const materialName = materialsCache[order.material_id] || '未知';
                    const orderType = order.order_type === 'PRODUCTION' ? '生产' : (order.order_type === 'PURCHASE' ? '采购' : '委外');
                    const status = order.status === 'PENDING' ? '待下达' : (order.status === 'RELEASED' ? '已下达' : order.status);
                    const statusClass = order.status === 'PENDING' ? 'pending' : 'completed';
                    html += `<tr>
                        <td>${order.planned_no}</td>
                        <td>${order.material_id}</td>
                        <td>${materialName}</td>
                        <td>${parseFloat(order.planned_qty).toFixed(2)}</td>
                        <td>${orderType}</td>
                        <td>${order.planned_date || '-'}</td>
                        <td><span class="status ${statusClass}">${status}</span></td>
                        <td>${order.status === 'PENDING' ? `<button class="btn btn-primary" onclick="releasePlannedOrder(${order.id})">下达</button>` : '-'}</td>
                    </tr>`;
                });
                
                html += `</tbody></table></div>`;
            }
            
            container.innerHTML = html;
        }

        async function loadPlannedOrders() {
            await loadMaterialsCache();
            
            try {
                const type = document.getElementById('planned-order-type')?.value || '';
                const status = document.getElementById('planned-order-status')?.value || '';
                
                let url = '/api/v1/plan/planned_orders/?account_set_id=1';
                if (type) url += `&order_type=${type}`;
                if (status) url += `&status=${status}`;
                
                const response = await fetch(url);
                const result = await response.json();
                
                const tbody = document.querySelector('#plan-content table tbody');
                if (!tbody) return;
                
                const orders = Array.isArray(result) ? result : (result.data || []);
                
                if (orders.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#999;">暂无计划订单</td></tr>';
                    return;
                }
                
                tbody.innerHTML = orders.map(order => {
                    const materialName = materialsCache[order.material_id] || '未知';
                    const orderType = order.order_type === 'PRODUCTION' ? '生产' : (order.order_type === 'PURCHASE' ? '采购' : '委外');
                    const statusText = order.status === 'PENDING' ? '待下达' : (order.status === 'RELEASED' ? '已下达' : order.status);
                    const statusClass = order.status === 'PENDING' ? 'pending' : 'completed';
                    return `<tr>
                        <td>${order.planned_no}</td>
                        <td>${order.material_id}</td>
                        <td>${materialName}</td>
                        <td>${parseFloat(order.planned_qty).toFixed(2)}</td>
                        <td>${order.planned_date || '-'}</td>
                        <td>${orderType}</td>
                        <td><span class="status ${statusClass}">${statusText}</span></td>
                        <td>
                            ${order.status === 'PENDING' ? `<button class="btn btn-primary" onclick="releasePlannedOrder(${order.id})">下达</button>` : ''}
                            <button class="btn btn-danger" onclick="deletePlannedOrder(${order.id})">删除</button>
                        </td>
                    </tr>`;
                }).join('');
            } catch (error) {
                const tbody = document.querySelector('#plan-content table tbody');
                if (tbody) {
                    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#999;">加载失败</td></tr>';
                }
            }
        }

        async function releasePlannedOrder(orderId) {
            try {
                const response = await fetch(`/api/v1/plan/planned_orders/${orderId}/release`, {
                    method: 'POST'
                });
                const result = await response.json();
                
                if (result.success || result.status === 'RELEASED') {
                    alert('计划订单已下达');
                } else {
                    alert(result.message || '下达失败');
                }
                loadPlannedOrders();
            } catch (error) {
                alert('操作失败');
            }
        }

        async function deletePlannedOrder(orderId) {
            if (!confirm('确定要删除这个计划订单吗？')) return;
            
            try {
                const response = await fetch(`/api/v1/plan/planned_orders/${orderId}`, {
                    method: 'DELETE'
                });
                const result = await response.json();
                
                if (result.message) {
                    alert('删除成功');
                } else {
                    alert(result.detail || '删除失败');
                }
                loadPlannedOrders();
            } catch (error) {
                alert('操作失败');
            }
        }

        document.addEventListener('DOMContentLoaded', () => {
            const savedUser = localStorage.getItem('currentUser');
            if (savedUser) {
                currentUser = JSON.parse(savedUser);
                showMainApp();
            } else {
                updateLoginUI();
                document.getElementById('login-form').addEventListener('submit', handleLogin);
            }
            
            setTimeout(() => {
                if (currentModule === 'finance') {
                    loadBalanceSheet();
                    loadProfitStatement();
                    loadCashFlow();
                    loadAssets();
                }
            }, 500);

            // ✅ 页面加载立即安装全局扫码枪监听器（无论在哪个页面都能捕获）
            installGlobalScannerListener();
        });

        // ===== 扫码枪全局监听（增强版）=====
        // 独立于扫码录入tab，任何页面都可以捕获扫码数据
        let gScanBuf = '';
        let gScanLastTs = 0;
        let gScanTimer = null;
        let gScanInInputBuf = '';
        let gScanInInputLastTs = 0;
        let gScanInInputTimer = null;
        let gScannerInstalled = false;

        function installGlobalScannerListener() {
            if (gScannerInstalled) return;
            gScannerInstalled = true;
            // 判断当前是否在"非扫码"的表单中输入（应该跳过）
            function isInFormContext() {
                const activeEl = document.activeElement;
                if (!activeEl) return false;
                // 如果有弹窗/模态框打开，跳过
                const modals = document.querySelectorAll('[style*="position:fixed"]');
                for (const m of modals) {
                    if (m.style.display !== 'none' && m.offsetHeight > 0) return true;
                }
                // 如果在表单输入框中（非扫码专用框），跳过
                if (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA' || activeEl.isContentEditable) {
                    // 只有扫码专用框才不跳过
                    if (activeEl.id === 'material-scan-input') return false;
                    // 搜索框也不跳过
                    if (activeEl.id === 'scan-input') return false;
                    // 其他任何输入框（比如新增物料弹窗）都跳过
                    return true;
                }
                if (activeEl.tagName === 'SELECT') return true;
                return false;
            }

            document.addEventListener('keydown', function(e) {
                const now = Date.now();

                // ====== 表单上下文直接跳过 ======
                if (isInFormContext()) {
                    gScanInInputBuf = '';
                    gScanBuf = '';
                    return;
                }

                // ====== Enter键检测 ======
                if (e.key === 'Enter') {
                    // 全局缓冲
                    if (gScanBuf.length >= 2) {
                        const code = gScanBuf.trim();
                        gScanBuf = '';
                        if (code) {
                            e.preventDefault();
                            triggerScanFlow(code);
                            return;
                        }
                    }
                    gScanBuf = '';
                    return;
                }

                // ====== 非输入框键盘捕获 ======
                if (e.key && e.key.length === 1) {
                    gScanBuf += e.key;
                    gScanLastTs = now;
                    if (gScanTimer) clearTimeout(gScanTimer);
                    gScanTimer = setTimeout(() => {
                        if (gScanBuf.length >= 3) {
                            const code = gScanBuf.trim();
                            gScanBuf = '';
                            if (code) triggerScanFlow(code);
                        }
                    }, 250);
                }
            });
        }

        // 扫码完成后的统一处理流程：跳转+记录
        function triggerScanFlow(rawCode) {
            const code = String(rawCode || '').trim();
            if (!code) return;
            // 自动跳转到：物料管理 -> 扫码录入 tab
            if (currentModule !== 'materials') {
                loadModule('materials');
            }
            setTimeout(() => {
                // 切到扫码录入tab
                const tabs = document.querySelectorAll('.finance-tab');
                tabs.forEach(t => {
                    if (t.textContent && t.textContent.indexOf('扫码录入') >= 0) {
                        t.click();
                    }
                });
                setTimeout(() => {
                    processMaterialScan(code);
                }, 200);
            }, 150);
        }
})();