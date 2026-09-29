# -*- coding: utf-8 -*-
"""
重新构建translations对象，修复所有中文乱码
"""
import re

file_path = r'c:\Users\ruancanling\Desktop\ERP VIBE CODING\frontend\index.html'

# 读取文件
with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# 正确的中文翻译
correct_translations = {
    'zh': {
        'dashboard-title': '仪表盘',
        'dashboard-desc': '欢迎使用ERP系统',
        'materials-title': '物料管理',
        'materials-desc': '管理企业物料库存',
        'purchase-title': '采购管理',
        'purchase-desc': '采购订单管理',
        'production-title': '生产管理',
        'production-desc': '生产订单管理',
        'finance-title': '财务管理',
        'finance-desc': '总账、应收应付、出纳、固定资产、工资、报表',
        'finance-general': '总账管理',
        'finance-arap': '应收应付',
        'finance-cash': '出纳管理',
        'finance-asset': '固定资产',
        'finance-payroll': '工资管理',
        'finance-reports': '财务报表',
        'crossborder-title': '跨境合规',
        'crossborder-desc': '跨境贸易合规',
        'scanning-title': '扫码录入',
        'scanning-desc': '扫描条码生成凭证',
        'invoice-title': '发票识别',
        'invoice-desc': '上传PDF发票识别',
        'total-materials': '物料总数',
        'purchase-orders': '采购订单',
        'production-orders': '生产订单',
        'compliance-alerts': '合规预警',
        'name': '名称',
        'code': '编码',
        'unit': '单位',
        'price': '单价',
        'status': '状态',
        'action': '操作',
        'view': '查看',
        'edit': '编辑',
        'delete': '删除',
        'PO-no': '采购单号',
        'supplier': '供应商',
        'material': '物料',
        'quantity': '数量',
        'work-order-no': '工单号',
        'product': '产品',
        'hs-code': 'HS编码',
        'description': '商品描述',
        'country': '目的地',
        'declared-value': '申报价值',
        'tax-estimate': '预估税费',
        'scan-input-placeholder': '请扫描条码...',
        'batch-mode': '批量模式',
        'single-mode': '单条模式',
        'generate-vouchers': '生成凭证',
        'clear-all': '清空全部',
        'total': '合计',
        'documents': '单据',
        'debit': '借方',
        'credit': '贷方',
        'click-or-drag': '点击或拖拽上传PDF发票',
        'supported-pdf': '支持格式：PDF',
        'load-sample': '加载示例发票',
        'generate-voucher': '生成凭证',
        'clear-data': '清空数据',
        'recognition-result': '识别结果',
        'invoice-info': '发票信息',
        'invoice-no': '发票号码',
        'invoice-code': '发票代码',
        'issue-date': '开票日期',
        'buyer-info': '购买方信息',
        'seller-info': '销售方信息',
        'tax-id': '税号',
        'amount-info': '金额信息',
        'subtotal': '不含税金额',
        'tax': '税额',
        'total-cn': '合计',
        'prepared-by': '制单人：',
        'accounting-voucher': '记账凭证',
        'voucher-type': '凭证字',
        'voucher-no': '凭证号',
        'voucher-date': '日期',
        'attachments': '附单据',
        'sheets': '张',
        'summary': '摘要',
        'account': '会计科目',
        'debit-amount': '借方金额',
        'credit-amount': '贷方金额',
        'hide-voucher': '隐藏凭证',
        'items': '商品明细',
        'unit-price': '单价',
        'tax-rate': '税率',
        'save-voucher': '保存凭证',
        'active': '激活',
        'pending': '待处理',
        'completed': '已完成',
        'in_progress': '进行中',
        'in_use': '使用中',
        'disposed': '已处置',
        'scrapped': '已报废'
    },
    'en': {
        'dashboard-title': 'Dashboard',
        'dashboard-desc': 'Welcome to ERP',
        'materials-title': 'Materials',
        'materials-desc': 'Manage inventory',
        'purchase-title': 'Purchase',
        'purchase-desc': 'Purchase orders',
        'production-title': 'Production',
        'production-desc': 'Work orders',
        'finance-title': 'Finance',
        'finance-desc': 'GL, AR/AP, Cash, Assets, Payroll, Reports',
        'finance-general': 'General Ledger',
        'finance-arap': 'AR/AP',
        'finance-cash': 'Cash Management',
        'finance-asset': 'Fixed Assets',
        'finance-payroll': 'Payroll',
        'finance-reports': 'Financial Reports',
        'crossborder-title': 'Cross-border',
        'crossborder-desc': 'Trade compliance',
        'scanning-title': 'Scan Entry',
        'scanning-desc': 'Scan to generate vouchers',
        'invoice-title': 'Invoice Recognition',
        'invoice-desc': 'Upload PDF invoice',
        'total-materials': 'Total Materials',
        'purchase-orders': 'Purchase Orders',
        'production-orders': 'Production Orders',
        'compliance-alerts': 'Compliance Alerts',
        'name': 'Name',
        'code': 'Code',
        'unit': 'Unit',
        'price': 'Price',
        'status': 'Status',
        'action': 'Action',
        'view': 'View',
        'edit': 'Edit',
        'delete': 'Delete',
        'PO-no': 'PO No.',
        'supplier': 'Supplier',
        'material': 'Material',
        'quantity': 'Quantity',
        'work-order-no': 'WO No.',
        'product': 'Product',
        'hs-code': 'HS Code',
        'description': 'Description',
        'country': 'Country',
        'declared-value': 'Declared Value',
        'tax-estimate': 'Tax Estimate',
        'scan-input-placeholder': 'Scan barcode...',
        'batch-mode': 'Batch Mode',
        'single-mode': 'Single Mode',
        'generate-vouchers': 'Generate Vouchers',
        'clear-all': 'Clear All',
        'total': 'Total',
        'documents': 'Documents',
        'debit': 'Debit',
        'credit': 'Credit',
        'click-or-drag': 'Click or drag to upload PDF',
        'supported-pdf': 'Supported: PDF',
        'load-sample': 'Load Sample',
        'generate-voucher': 'Generate Voucher',
        'clear-data': 'Clear Data',
        'recognition-result': 'Recognition Result',
        'invoice-info': 'Invoice Info',
        'invoice-no': 'Invoice No.',
        'invoice-code': 'Invoice Code',
        'issue-date': 'Issue Date',
        'buyer-info': 'Buyer Info',
        'seller-info': 'Seller Info',
        'tax-id': 'Tax ID',
        'amount-info': 'Amount Info',
        'subtotal': 'Subtotal',
        'tax': 'Tax',
        'total-cn': 'Total',
        'prepared-by': 'Prepared by:',
        'accounting-voucher': 'Accounting Voucher',
        'voucher-type': 'Voucher Type',
        'voucher-no': 'Voucher No.',
        'voucher-date': 'Date',
        'attachments': 'Attachments',
        'sheets': 'sheets',
        'summary': 'Summary',
        'account': 'Account',
        'debit-amount': 'Debit Amount',
        'credit-amount': 'Credit Amount',
        'hide-voucher': 'Hide Voucher',
        'items': 'Items',
        'unit-price': 'Unit Price',
        'tax-rate': 'Tax Rate',
        'save-voucher': 'Save Voucher'
    }
}

# 构建正确的translations字符串
translations_str = "        const translations = {\n"
translations_str += "            'zh': {\n"
for key, value in correct_translations['zh'].items():
    translations_str += f"                '{key}': '{value}', "
translations_str = translations_str.rstrip(', ') + "\n"
translations_str += "            },\n"
translations_str += "            'en': {\n"
for key, value in correct_translations['en'].items():
    translations_str += f"                '{key}': '{value}', "
translations_str = translations_str.rstrip(', ') + "\n"
translations_str += "            }\n"
translations_str += "        };"

# 使用正则表达式替换旧的translations对象
# 找到const translations = { ... };的位置并替换
pattern = r'const translations = \{.*?\};'
content = re.sub(pattern, translations_str, content, flags=re.DOTALL)

# 保存修复后的文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Translations对象修复完成！")