import zipfile
import xml.etree.ElementTree as ET
import sys
import re

def read_word_document(file_path):
    try:
        # Word文档实际上是一个zip文件
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            # 读取主文档内容
            xml_content = zip_ref.read('word/document.xml')
            
        # 解析XML
        root = ET.fromstring(xml_content)
        
        # 定义命名空间
        namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        }
        
        # 提取所有文本
        text_elements = root.findall('.//w:t', namespaces)
        text_content = []
        
        for elem in text_elements:
            if elem.text:
                text_content.append(elem.text)
        
        # 提取表格内容
        tables = root.findall('.//w:tbl', namespaces)
        table_content = []
        
        for table in tables:
            rows = table.findall('.//w:tr', namespaces)
            for row in rows:
                cells = row.findall('.//w:tc', namespaces)
                row_data = []
                for cell in cells:
                    cell_texts = cell.findall('.//w:t', namespaces)
                    cell_text = ''.join([t.text for t in cell_texts if t.text])
                    if cell_text.strip():
                        row_data.append(cell_text.strip())
                if row_data:
                    table_content.append(' | '.join(row_data))
        
        # 组合所有内容
        full_text = ''.join(text_content)
        
        # 清理文本
        full_text = re.sub(r'\s+', ' ', full_text)
        full_text = full_text.strip()
        
        return full_text, table_content
        
    except Exception as e:
        return f"Error reading document: {str(e)}", []

if __name__ == "__main__":
    file_path = r"C:\Users\ruancanling\Desktop\大数据基础课程考查题目及要求.docx"
    text_content, table_content = read_word_document(file_path)
    
    print("=== 文档文本内容 ===")
    print(text_content)
    print("\n=== 表格内容 ===")
    for row in table_content:
        print(row)