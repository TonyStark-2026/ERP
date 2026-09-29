# -*- coding: utf-8 -*-
import zipfile
import xml.etree.ElementTree as ET

path = r'C:\Users\ruancanling\Desktop\24会计X班+20240604430529+阮粲凌+《大数据基础》期末考核.docx'
z = zipfile.ZipFile(path)
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

# 验证所有XML有效性
print('=== XML 验证 ===')
all_ok = True
for name in z.namelist():
    if name.endswith('.xml') or name.endswith('.rels'):
        try:
            ET.fromstring(z.read(name))
            print(f'OK   {name}')
        except Exception as e:
            print(f'FAIL {name}: {e}')
            all_ok = False

# 统计内容
root = ET.fromstring(z.read('word/document.xml'))
texts = [t.text for t in root.findall('.//w:t', ns) if t.text]
full = ''.join(texts)
paragraphs = root.findall('.//w:p', ns)

print()
print('=== 内容统计 ===')
print(f'段落数: {len(paragraphs)}')
print(f'正文字符数: {len(full)}')
import re
# 计算参考文献条数
refs = re.findall(r'\[\d+\]', full)
print(f'参考文献条数: {len(refs)}')

# 显示结构
print()
print('=== 论文结构 ===')
for p in paragraphs:
    para_texts = [t.text for t in p.findall('.//w:t', ns) if t.text]
    if para_texts:
        text = ''.join(para_texts)
        if len(text) < 50:
            print(f'  {text}')
        else:
            print(f'  {text[:50]}...')

if all_ok:
    print()
    print('✓ 文档结构完整，Word可正常打开')
else:
    print()
    print('✗ 文档存在错误')
