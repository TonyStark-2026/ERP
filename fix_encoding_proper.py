# -*- coding: utf-8 -*-
"""
正确修复GBK乱码的脚本
当GBK编码的中文被错误地当作UTF-8读取时，会产生乱码
需要先按错误的方式读取，然后找到正确的字符映射
"""
import codecs

file_path = r'c:\Users\ruancanling\Desktop\ERP VIBE CODING\frontend\index.html'

# 读取原始字节
with open(file_path, 'rb') as f:
    raw_bytes = f.read()

# 如果有BOM就移除
if raw_bytes.startswith(b'\xef\xbb\xbf'):
    raw_bytes = raw_bytes[3:]

# 首先尝试正确的UTF-8解码
try:
    content = raw_bytes.decode('utf-8')
    print("文件已经是UTF-8编码")
except UnicodeDecodeError:
    # 如果UTF-8解码失败，说明是GBK被当作UTF-8处理了
    # 需要特殊处理
    print("检测到编码问题，尝试修复...")
    
    # 方案1: 先用UTF-8错误处理读取，然后用正则替换常见乱码模式
    content = raw_bytes.decode('utf-8', errors='replace')
    
    # 常见的GBK乱码模式及其正确字符
    # 这些是GBK双字节字符被错误解码为UTF-8时产生的模式
    gbk_garbage_map = {
        # 单个乱码字符
        '\ufffd': '',
        
        # 中文常见词的乱码形式
        '绯荤粺': '系统',
        '琛屾儏': '状况',
        '鏂囦欢': '文件',
        '绠＄悊': '管理',
        '鎿嶄綔': '操作',
        '妫€娴�': '检查',
        '鍒楄〃': '列表',
        '鏌ヨ': '查询',
        '鐩稿唽': '注册',
        '鐧诲綍': '登录',
        '缂栧彿': '编码',
        '鍚嶇О': '名称',
        '绫诲瀷': '类型',
        '鍊煎惛': '金额',
        '鏃ユ湡': '日期',
        '琛ㄥ崟': '报表',
        '骞冲彴': '平台',
        '绔欑偣': '节点',
        '閫氱煡': '通知',
        '娣诲姞': '添加',
        '璇诲彇': '获取',
        '淇敼': '修改',
        '鍒犻櫎': '删除',
        '鎻愪氦': '提交',
        '鏄庣粰': '告知',
        '鎺ュ彛': '端口',
        '鏈嶅姟': '服务',
        '缃戠粶': '网络',
        '绂忓缓': '恢复',
        '澶勭悊': '处理',
        '璁板綍': '记录',
        '娴嬭瘯': '测试',
        '姹�': '查',
        '璁句负': '设为',
        '閿�': '关',
        '寮�': '开',
        '鏂�': '新',
        '鎵�': '所',
        '涓�': '一',
        '浜�': '人',
        '鍙�': '否',
        '鐩�': '目',
        '鍗�': '件',
        '鏍�': '标',
        '鐨�': '的',
        '鍦�': '在',
        '琛�': '报',
        '鏀�': '修',
        '闄�': '删',
        '鍒�': '到',
        '鐢�': '使',
        '澶�': '大',
        '灏�': '很',
        '鏄�': '是',
        '涓�': '于',
        '浠�': '为',
        '涔�': '存',
        '鐒�': '或',
        '鑰�': '密',
        '鍐�': '加',
        '鎴�': '成',
        '鏈�': '还',
        '杩�': '继',
        '閲�': '查',
        '鍚�': '同',
        '浣�': '你',
        '鐜�': '现',
        '鍏�': '共',
        '闈�': '没',
        '浼氬�': '会',
        '鍙�': '也',
        '閫�': '给',
        '鐢�': '用',
        '鍙�': '那',
        '浣�': '您',
        
        # 状态类
        '浣跨敤': '使用',
        '宸插': '已处',
        '宸叉姤': '已报',
        '璁℃彁': '计提',
        '鏆傛棤': '暂无',
        '鍔犺浇': '加载',
        '淇濆瓨': '保存',
        '纭畾': '确认',
        '鍒犻櫎': '删除',
        
        # 财务相关
        '鎶樻棫': '折旧',
        '鏁版嵁': '数据',
        '澶辫触': '失败',
        '鎴愬姛': '成功',
        
        # 特殊字符
        '楼': '¥',
    }
    
    # 应用修复
    for garbage, correct in gbk_garbage_map.items():
        content = content.replace(garbage, correct)

# 现在修复单个的乱码字符模式
# 许多乱码是GBK双字节被截断的结果
# 使用正则表达式修复常见模式
import re

# 修复 "仪表" 后面跟着乱码的情况
content = re.sub(r'仪表[\ufffd,，]', '仪表盘', content)
content = re.sub(r'报[\ufffd,，]', '报表', content)
content = re.sub(r'状[\ufffd,，]', '状态', content)
content = re.sub(r'供应[\ufffd,，]', '供应商', content)
content = re.sub(r'工单[\ufffd,，]', '工单号', content)
content = re.sub(r'目的[\ufffd,，]', '目的地', content)
content = re.sub(r'申报价[\ufffd,，]', '申报价值', content)
content = re.sub(r'请扫描条[\ufffd,，.。]', '请扫描条码', content)
content = re.sub(r'开票日[\ufffd,，]', '开票日期', content)
content = re.sub(r'购买方信[\ufffd,，]', '购买方信息', content)
content = re.sub(r'不含税金[\ufffd,，]', '不含税金额', content)
content = re.sub(r'合计[\ufffd,，]', '合计', content)
content = re.sub(r'凭证[\ufffd,，]', '凭证字', content)
content = re.sub(r'附单[\ufffd,，]', '附单据', content)
content = re.sub(r'使用[\ufffd,，]', '使用中', content)
content = re.sub(r'已处[\ufffd,，]', '已处置', content)
content = re.sub(r'已报[\ufffd,，]', '已报废', content)
content = re.sub(r'激活[\ufffd,，]', '激活', content)
content = re.sub(r'待处[\ufffd,，]', '待处理', content)
content = re.sub(r'已完[\ufffd,，]', '已完成', content)
content = re.sub(r'进行[\ufffd,，]', '进行中', content)

# 保存修复后的文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("修复完成！")