# -*- coding: utf-8 -*-
"""
使用Word COM自动化接口将txt文件转换为docx文件
"""
import os
import subprocess
import sys

# 定义源文件路径
txt_path = r"C:\Users\ruancanling\Desktop\大数据在财务管理中的应用研究论文.txt"
docx_path = r"C:\Users\ruancanling\Desktop\大数据在财务管理中的应用研究论文.docx"

# 方法1: 使用PowerShell调用Word
ps_script = f'''
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open("{txt_path}")
$doc.SaveAs2("{docx_path}", 16)  # 16 = wdFormatXMLDocument (docx)
$doc.Close()
$word.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
Write-Output "Conversion completed successfully"
'''

# 保存PowerShell脚本
ps_path = r"C:\Users\ruancanling\Desktop\ERP VIBE CODING\convert_to_docx.ps1"
with open(ps_path, 'w', encoding='utf-8') as f:
    f.write(ps_script)

print("PowerShell脚本已创建，开始执行转换...")

# 执行PowerShell脚本
try:
    result = subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_path],
        capture_output=True, text=True, timeout=60
    )
    print("stdout:", result.stdout)
    print("stderr:", result.stderr)
    if os.path.exists(docx_path):
        print(f"成功生成docx文件: {docx_path}")
        print(f"文件大小: {os.path.getsize(docx_path)} 字节")
    else:
        print("docx文件未生成")
except Exception as e:
    print(f"执行出错: {e}")