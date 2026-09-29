# -*- coding: utf-8 -*-
"""
简单但有效的编码修复脚本
"""

file_path = r'c:\Users\ruancanling\Desktop\ERP VIBE CODING\frontend\index.html'

# 读取原始字节
with open(file_path, 'rb') as f:
    raw_bytes = f.read()

# 移除BOM
if raw_bytes.startswith(b'\xef\xbb\xbf'):
    raw_bytes = raw_bytes[3:]

# 尝试用GBK解码（这是最常见的问题：GBK被当作UTF-8处理）
try:
    content = raw_bytes.decode('gbk')
    print("成功用GBK解码！")
except UnicodeDecodeError:
    # 如果GBK失败，尝试UTF-8
    try:
        content = raw_bytes.decode('utf-8')
        print("成功用UTF-8解码！")
    except:
        # 最后尝试带错误替换的UTF-8
        content = raw_bytes.decode('utf-8', errors='replace')
        print("使用UTF-8解码（带错误替换）")

# 现在检查是否需要修复
# 如果内容包含常见的GBK乱码字符，说明文件是GBK编码但被错误保存了
if '浠〃' in content or '鐩?' in content or '浣跨敤' in content:
    print("检测到GBK乱码模式，文件应该是GBK编码")
    # 重新用GBK解码
    try:
        content = raw_bytes.decode('gbk')
        print("重新用GBK解码成功！")
    except:
        pass

# 保存为UTF-8
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("文件已保存！")