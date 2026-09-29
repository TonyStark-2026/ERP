# -*- coding: utf-8 -*-
"""
终极编码修复脚本
检测文件编码并正确转换
"""
import chardet

file_path = r'c:\Users\ruancanling\Desktop\ERP VIBE CODING\frontend\index.html'

# 读取原始字节
with open(file_path, 'rb') as f:
    raw_bytes = f.read()

# 检测编码
result = chardet.detect(raw_bytes)
encoding = result['encoding']
confidence = result['confidence']

print(f"检测到编码: {encoding}, 置信度: {confidence}")

# 移除BOM
if raw_bytes.startswith(b'\xef\xbb\xbf'):
    raw_bytes = raw_bytes[3:]
    print("已移除UTF-8 BOM")

# 尝试多种解码方式
try:
    # 先尝试GBK解码（因为乱码看起来是GBK被当作UTF-8）
    content = raw_bytes.decode('gbk')
    print("使用GBK解码成功")
except:
    try:
        content = raw_bytes.decode('utf-8')
        print("使用UTF-8解码成功")
    except:
        try:
            content = raw_bytes.decode('gb2312')
            print("使用GB2312解码成功")
        except:
            content = raw_bytes.decode('utf-8', errors='replace')
            print("使用UTF-8解码（带错误替换）")

# 保存为正确的UTF-8编码
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"文件已保存为UTF-8编码")