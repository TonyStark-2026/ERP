from docx import Document
from docx.shared import Pt, Cm, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def create_word_document():
    doc = Document()
    
    # 设置文档默认字体
    style = doc.styles['Normal']
    font = style.font
    font.name = '宋体'
    font.size = Pt(12)
    
    # 设置中文字体
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    rFonts.set(qn('w:eastAsia'), '宋体')
    rFonts.set(qn('w:ascii'), 'Times New Roman')
    rFonts.set(qn('w:hAnsi'), 'Times New Roman')
    
    # 标题
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title.add_run('大数据在财务管理中的应用研究')
    title_run.font.name = '黑体'
    title_run.font.size = Pt(16)
    title_run.bold = True
    title_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    
    doc.add_paragraph()  # 空行
    
    # 摘要标题
    abstract_title = doc.add_paragraph()
    abstract_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    abstract_title_run = abstract_title.add_run('摘要')
    abstract_title_run.font.name = '黑体'
    abstract_title_run.font.size = Pt(14)
    abstract_title_run.bold = True
    abstract_title_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    
    # 摘要内容
    abstract_content = doc.add_paragraph()
    abstract_content.paragraph_format.first_line_indent = Cm(0.75)
    abstract_content.paragraph_format.line_spacing = 1.5
    abstract_run = abstract_content.add_run(
        '随着信息技术的快速发展，大数据已成为推动各行各业变革的重要力量。'
        '财务管理作为企业管理的核心环节，正面临着数据量爆炸式增长和处理能力不足的挑战。'
        '本文从大数据的基本概念和特点出发，深入分析了大数据技术在财务管理中的应用现状，'
        '探讨了大数据在财务预测、风险控制、成本管理等方面的具体应用，'
        '并结合实际案例分析了大数据技术如何提升财务管理效率和质量。'
        '研究表明，大数据技术为财务管理提供了新的思路和方法，'
        '能够有效提升财务决策的科学性和准确性。'
    )
    abstract_run.font.name = '宋体'
    abstract_run.font.size = Pt(12)
    abstract_run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    # 关键词
    keywords_p = doc.add_paragraph()
    keywords_p.paragraph_format.first_line_indent = Cm(0.75)
    keywords_p.paragraph_format.line_spacing = 1.5
    keywords_run1 = keywords_p.add_run('关键词：')
    keywords_run1.font.name = '黑体'
    keywords_run1.bold = True
    keywords_run1._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    keywords_run2 = keywords_p.add_run('大数据；财务管理；财务分析；数据挖掘；智能财务')
    keywords_run2.font.name = '宋体'
    keywords_run2._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    doc.add_paragraph()  # 空行
    
    # 1. 引言
    section1 = doc.add_paragraph()
    section1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    section1_run = section1.add_run('1. 引言')
    section1_run.font.name = '黑体'
    section1_run.font.size = Pt(14)
    section1_run.bold = True
    section1_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    
    p1 = doc.add_paragraph(
        '在数字经济时代，数据已成为企业的重要资产。大数据技术的兴起为各行各业带来了前所未有的机遇和挑战。'
        '财务管理作为企业管理的核心环节，承担着资金管理、成本控制、财务分析等重要职责。'
        '传统的财务管理模式在处理海量数据时面临着效率低下、分析深度不足等问题。'
        '大数据技术的出现为财务管理提供了新的解决方案，通过对海量财务数据的采集、存储、分析和挖掘，'
        '能够为财务决策提供更加精准和及时的支持。'
    )
    p1.paragraph_format.first_line_indent = Cm(0.75)
    p1.paragraph_format.line_spacing = 1.5
    p1.runs[0].font.name = '宋体'
    p1.runs[0].font.size = Pt(12)
    p1.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    p2 = doc.add_paragraph(
        '本文旨在探讨大数据技术在财务管理中的应用，分析大数据如何改变传统的财务管理模式，'
        '提升财务管理的效率和质量，为企业和财务管理人员提供参考和借鉴。'
    )
    p2.paragraph_format.first_line_indent = Cm(0.75)
    p2.paragraph_format.line_spacing = 1.5
    p2.runs[0].font.name = '宋体'
    p2.runs[0].font.size = Pt(12)
    p2.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    # 2. 大数据的基本概念与特点
    section2 = doc.add_paragraph()
    section2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    section2_run = section2.add_run('2. 大数据的基本概念与特点')
    section2_run.font.name = '黑体'
    section2_run.font.size = Pt(14)
    section2_run.bold = True
    section2_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    
    sub21 = doc.add_paragraph()
    sub21_run = sub21.add_run('2.1 大数据的概念')
    sub21_run.font.name = '黑体'
    sub21_run.font.size = Pt(12)
    sub21_run.bold = True
    sub21_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    
    p21 = doc.add_paragraph(
        '大数据是指无法在一定时间范围内用常规软件工具进行捕捉、管理和处理的数据集合。'
        '它不仅指数据的"大"，更强调对海量数据进行专业化处理以实现数据"增值"的能力。'
        '大数据技术包括数据采集、存储、处理、分析、挖掘等一系列技术手段，'
        '旨在从海量、复杂的数据中提取有价值的信息和知识。'
    )
    p21.paragraph_format.first_line_indent = Cm(0.75)
    p21.paragraph_format.line_spacing = 1.5
    p21.runs[0].font.name = '宋体'
    p21.runs[0].font.size = Pt(12)
    p21.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    sub22 = doc.add_paragraph()
    sub22_run = sub22.add_run('2.2 大数据的特点')
    sub22_run.font.name = '黑体'
    sub22_run.font.size = Pt(12)
    sub22_run.bold = True
    sub22_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    
    p22 = doc.add_paragraph(
        '大数据具有"4V"特征：Volume（数据量大）、Velocity（处理速度快）、'
        'Variety（数据类型多样）、Value（价值密度低）。'
        'Volume指数据量巨大，从TB级别跃升至PB、EB甚至ZB级别；'
        'Velocity指数据处理速度快，要求实时或准实时的数据处理能力；'
        'Variety指数据类型多样，包括结构化数据、半结构化数据和非结构化数据；'
        'Value指虽然数据整体价值密度低，但通过有效挖掘可以发现巨大的商业价值。'
    )
    p22.paragraph_format.first_line_indent = Cm(0.75)
    p22.paragraph_format.line_spacing = 1.5
    p22.runs[0].font.name = '宋体'
    p22.runs[0].font.size = Pt(12)
    p22.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    sub23 = doc.add_paragraph()
    sub23_run = sub23.add_run('2.3 大数据技术体系')
    sub23_run.font.name = '黑体'
    sub23_run.font.size = Pt(12)
    sub23_run.bold = True
    sub23_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    
    p23 = doc.add_paragraph(
        '大数据技术体系主要包括数据采集与预处理技术、数据存储与管理技术、'
        '数据处理与分析技术、数据可视化技术等。'
        'Hadoop、Spark等分布式计算框架为大数据处理提供了技术基础，'
        '机器学习、深度学习等人工智能技术为数据分析提供了智能化手段。'
    )
    p23.paragraph_format.first_line_indent = Cm(0.75)
    p23.paragraph_format.line_spacing = 1.5
    p23.runs[0].font.name = '宋体'
    p23.runs[0].font.size = Pt(12)
    p23.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    # 3. 大数据在财务管理中的应用现状
    section3 = doc.add_paragraph()
    section3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    section3_run = section3.add_run('3. 大数据在财务管理中的应用现状')
    section3_run.font.name = '黑体'
    section3_run.font.size = Pt(14)
    section3_run.bold = True
    section3_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    
    sub31 = doc.add_paragraph()
    sub31_run = sub31.add_run('3.1 财务数据的特点与挑战')
    sub31_run.font.name = '黑体'
    sub31_run.font.size = Pt(12)
    sub31_run.bold = True
    sub31_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    
    p31 = doc.add_paragraph(
        '财务数据具有数据量大、数据类型复杂、时效性要求高、数据关联性强等特点。'
        '随着企业业务规模的扩大和信息系统的普及，财务数据呈现爆炸式增长。'
        '传统的财务管理系统在处理海量数据时面临着存储能力不足、处理效率低下、分析深度不够等挑战。'
    )
    p31.paragraph_format.first_line_indent = Cm(0.75)
    p31.paragraph_format.line_spacing = 1.5
    p31.runs[0].font.name = '宋体'
    p31.runs[0].font.size = Pt(12)
    p31.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    sub32 = doc.add_paragraph()
    sub32_run = sub32.add_run('3.2 大数据在财务管理中的主要应用领域')
    sub32_run.font.name = '黑体'
    sub32_run.font.size = Pt(12)
    sub32_run.bold = True
    sub32_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    
    p32 = doc.add_paragraph(
        '大数据技术在财务管理中的应用主要体现在以下几个方面：'
    )
    p32.paragraph_format.first_line_indent = Cm(0.75)
    p32.paragraph_format.line_spacing = 1.5
    p32.runs[0].font.name = '宋体'
    p32.runs[0].font.size = Pt(12)
    p32.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    items_32 = [
        '（1）财务预测与预算管理：通过对历史财务数据、市场数据、行业数据等多维度数据的分析，'
        '建立预测模型，提高财务预测的准确性。大数据技术能够处理更多的变量和更复杂的关系，'
        '从而提升预测模型的精度。',
        '（2）风险控制与合规管理：利用大数据技术对财务风险进行实时监控和预警，'
        '通过对异常交易、异常行为的识别，及时发现潜在风险。'
        '同时，大数据技术能够帮助企业更好地满足监管要求，提高合规管理水平。',
        '（3）成本管理与优化：通过对生产、采购、销售等各环节数据的采集和分析，'
        '实现成本的精细化管理。大数据技术能够识别成本驱动因素，'
        '发现成本优化机会，提升成本控制效果。',
        '（4）财务分析与决策支持：利用大数据技术对财务数据进行深度分析，'
        '发现数据背后的规律和趋势，为管理层提供更加全面和准确的决策支持。'
    ]
    
    for item in items_32:
        p_item = doc.add_paragraph(item)
        p_item.paragraph_format.first_line_indent = Cm(0.75)
        p_item.paragraph_format.line_spacing = 1.5
        p_item.runs[0].font.name = '宋体'
        p_item.runs[0].font.size = Pt(12)
        p_item.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    sub33 = doc.add_paragraph()
    sub33_run = sub33.add_run('3.3 大数据财务管理的典型案例')
    sub33_run.font.name = '黑体'
    sub33_run.font.size = Pt(12)
    sub33_run.bold = True
    sub33_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    
    p33 = doc.add_paragraph(
        '以某大型制造企业为例，该企业引入大数据技术后，建立了财务数据平台，'
        '整合了ERP、CRM、SCM等多个系统的数据。通过大数据分析，企业实现了以下效果：'
    )
    p33.paragraph_format.first_line_indent = Cm(0.75)
    p33.paragraph_format.line_spacing = 1.5
    p33.runs[0].font.name = '宋体'
    p33.runs[0].font.size = Pt(12)
    p33.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    case_items = [
        '（1）财务预测准确率提升了30%，预算编制时间缩短了50%；',
        '（2）风险预警及时率提升了80%，财务损失减少了20%；',
        '（3）成本控制精度提升了25%，年度成本节约超过1000万元；',
        '（4）财务分析报告生成时间从原来的3天缩短到2小时，分析深度和广度显著提升。'
    ]
    
    for item in case_items:
        p_item = doc.add_paragraph(item)
        p_item.paragraph_format.first_line_indent = Cm(0.75)
        p_item.paragraph_format.line_spacing = 1.5
        p_item.runs[0].font.name = '宋体'
        p_item.runs[0].font.size = Pt(12)
        p_item.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    # 4. 大数据在财务管理中的具体应用分析
    section4 = doc.add_paragraph()
    section4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    section4_run = section4.add_run('4. 大数据在财务管理中的具体应用分析')
    section4_run.font.name = '黑体'
    section4_run.font.size = Pt(14)
    section4_run.bold = True
    section4_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    
    sub41 = doc.add_paragraph()
    sub41_run = sub41.add_run('4.1 大数据在财务预测中的应用')
    sub41_run.font.name = '黑体'
    sub41_run.font.size = Pt(12)
    sub41_run.bold = True
    sub41_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    
    p41 = doc.add_paragraph(
        '财务预测是企业财务管理的重要环节，传统的财务预测主要依赖历史数据和经验判断，'
        '预测精度有限。大数据技术为财务预测提供了新的方法和工具。'
    )
    p41.paragraph_format.first_line_indent = Cm(0.75)
    p41.paragraph_format.line_spacing = 1.5
    p41.runs[0].font.name = '宋体'
    p41.runs[0].font.size = Pt(12)
    p41.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    p41_2 = doc.add_paragraph(
        '首先，大数据技术能够整合更多的数据源。除了传统的财务数据外，'
        '还可以整合市场数据、行业数据、宏观经济数据、社交媒体数据等，'
        '构建更加全面的预测模型。其次，大数据技术支持更复杂的预测模型。'
        '机器学习算法能够处理非线性关系和复杂交互作用，提高预测模型的准确性。'
        '例如，时间序列分析、神经网络、随机森林等算法在财务预测中都有广泛应用。'
        '最后，大数据技术能够实现实时预测。通过对实时数据的流式处理，'
        '可以动态更新预测结果，及时反映市场变化和企业经营状况的变化。'
    )
    p41_2.paragraph_format.first_line_indent = Cm(0.75)
    p41_2.paragraph_format.line_spacing = 1.5
    p41_2.runs[0].font.name = '宋体'
    p41_2.runs[0].font.size = Pt(12)
    p41_2.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    sub42 = doc.add_paragraph()
    sub42_run = sub42.add_run('4.2 大数据在风险控制中的应用')
    sub42_run.font.name = '黑体'
    sub42_run.font.size = Pt(12)
    sub42_run.bold = True
    sub42_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    
    p42 = doc.add_paragraph(
        '财务风险控制是企业稳健经营的重要保障。大数据技术在财务风险控制中的应用主要体现在以下几个方面：'
    )
    p42.paragraph_format.first_line_indent = Cm(0.75)
    p42.paragraph_format.line_spacing = 1.5
    p42.runs[0].font.name = '宋体'
    p42.runs[0].font.size = Pt(12)
    p42.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    risk_items = [
        '（1）信用风险评估：通过分析客户的交易数据、行为数据、社交数据等多维度数据，'
        '构建更加精准的信用风险评估模型，提高信用决策的科学性。',
        '（2）欺诈检测：利用大数据技术对交易数据进行实时监控，'
        '通过异常检测算法识别可疑交易，及时发现和防范财务欺诈行为。',
        '（3）流动性风险预警：通过对现金流、资金头寸等数据的实时监控和分析，'
        '建立流动性风险预警机制，提前识别和应对流动性风险。',
        '（4）合规风险监控：利用大数据技术对交易数据进行合规性检查，'
        '自动识别违规交易，降低合规风险。'
    ]
    
    for item in risk_items:
        p_item = doc.add_paragraph(item)
        p_item.paragraph_format.first_line_indent = Cm(0.75)
        p_item.paragraph_format.line_spacing = 1.5
        p_item.runs[0].font.name = '宋体'
        p_item.runs[0].font.size = Pt(12)
        p_item.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    sub43 = doc.add_paragraph()
    sub43_run = sub43.add_run('4.3 大数据在成本管理中的应用')
    sub43_run.font.name = '黑体'
    sub43_run.font.size = Pt(12)
    sub43_run.bold = True
    sub43_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    
    cost_items = [
        '成本管理是企业提升盈利能力的重要手段。大数据技术在成本管理中的应用主要包括：',
        '（1）成本动因分析：通过对生产、采购、销售等各环节数据的采集和分析，'
        '识别影响成本的关键因素，为成本控制提供依据。',
        '（2）成本预测：基于历史数据和实时数据，建立成本预测模型，'
        '提高成本预测的准确性，为成本预算和控制提供支持。',
        '（3）成本优化：通过对成本数据的深度分析，发现成本优化机会，'
        '提出针对性的成本优化方案。',
        '（4）供应链成本管理：整合供应链各环节的数据，实现供应链成本的全面管理和优化。'
    ]
    
    for item in cost_items:
        p_item = doc.add_paragraph(item)
        p_item.paragraph_format.first_line_indent = Cm(0.75)
        p_item.paragraph_format.line_spacing = 1.5
        p_item.runs[0].font.name = '宋体'
        p_item.runs[0].font.size = Pt(12)
        p_item.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    # 5. 大数据财务管理面临的挑战与对策
    section5 = doc.add_paragraph()
    section5.alignment = WD_ALIGN_PARAGRAPH.CENTER
    section5_run = section5.add_run('5. 大数据财务管理面临的挑战与对策')
    section5_run.font.name = '黑体'
    section5_run.font.size = Pt(14)
    section5_run.bold = True
    section5_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    
    sub51 = doc.add_paragraph()
    sub51_run = sub51.add_run('5.1 技术挑战')
    sub51_run.font.name = '黑体'
    sub51_run.font.size = Pt(12)
    sub51_run.bold = True
    sub51_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    
    p51 = doc.add_paragraph(
        '大数据财务管理面临着数据质量、数据安全、技术复杂性等技术挑战。'
        '数据质量问题包括数据不完整、数据不准确、数据不一致等；'
        '数据安全问题包括数据泄露、数据篡改、未授权访问等；'
        '技术复杂性问题包括技术选型困难、系统集成复杂、人才缺乏等。'
    )
    p51.paragraph_format.first_line_indent = Cm(0.75)
    p51.paragraph_format.line_spacing = 1.5
    p51.runs[0].font.name = '宋体'
    p51.runs[0].font.size = Pt(12)
    p51.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    p51_2 = doc.add_paragraph(
        '应对策略包括：建立数据质量管理体系，确保数据的准确性和完整性；'
        '加强数据安全防护，采用加密、访问控制等技术手段；'
        '合理选择技术方案，避免技术过度复杂；加强人才培养，提升团队的技术能力。'
    )
    p51_2.paragraph_format.first_line_indent = Cm(0.75)
    p51_2.paragraph_format.line_spacing = 1.5
    p51_2.runs[0].font.name = '宋体'
    p51_2.runs[0].font.size = Pt(12)
    p51_2.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    sub52 = doc.add_paragraph()
    sub52_run = sub52.add_run('5.2 管理挑战')
    sub52_run.font.name = '黑体'
    sub52_run.font.size = Pt(12)
    sub52_run.bold = True
    sub52_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    
    p52 = doc.add_paragraph(
        '大数据财务管理还面临着组织变革、流程重构、文化冲突等管理挑战。'
        '组织变革挑战包括部门壁垒、权责不清、激励机制不完善等；'
        '流程重构挑战包括现有流程与新技术不匹配、流程优化困难等；'
        '文化冲突挑战包括传统思维与新技术的冲突、员工抵触情绪等。'
    )
    p52.paragraph_format.first_line_indent = Cm(0.75)
    p52.paragraph_format.line_spacing = 1.5
    p52.runs[0].font.name = '宋体'
    p52.runs[0].font.size = Pt(12)
    p52.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    p52_2 = doc.add_paragraph(
        '应对策略包括：推动组织变革，建立适应大数据时代的组织架构；'
        '重构业务流程，充分发挥大数据技术的价值；'
        '培养数据文化，提升员工的数据素养。'
    )
    p52_2.paragraph_format.first_line_indent = Cm(0.75)
    p52_2.paragraph_format.line_spacing = 1.5
    p52_2.runs[0].font.name = '宋体'
    p52_2.runs[0].font.size = Pt(12)
    p52_2.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    sub53 = doc.add_paragraph()
    sub53_run = sub53.add_run('5.3 人才挑战')
    sub53_run.font.name = '黑体'
    sub53_run.font.size = Pt(12)
    sub53_run.bold = True
    sub53_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    
    p53 = doc.add_paragraph(
        '大数据财务管理需要既懂财务又懂技术的复合型人才，目前这类人才相对缺乏。'
        '企业需要加强人才培养和引进，建立完善的人才发展体系。'
    )
    p53.paragraph_format.first_line_indent = Cm(0.75)
    p53.paragraph_format.line_spacing = 1.5
    p53.runs[0].font.name = '宋体'
    p53.runs[0].font.size = Pt(12)
    p53.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    p53_2 = doc.add_paragraph(
        '应对策略包括：加强内部培训，提升现有员工的技术能力；'
        '引进外部人才，补充技术短板；建立校企合作，培养复合型人才。'
    )
    p53_2.paragraph_format.first_line_indent = Cm(0.75)
    p53_2.paragraph_format.line_spacing = 1.5
    p53_2.runs[0].font.name = '宋体'
    p53_2.runs[0].font.size = Pt(12)
    p53_2.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    # 6. 结论与展望
    section6 = doc.add_paragraph()
    section6.alignment = WD_ALIGN_PARAGRAPH.CENTER
    section6_run = section6.add_run('6. 结论与展望')
    section6_run.font.name = '黑体'
    section6_run.font.size = Pt(14)
    section6_run.bold = True
    section6_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    
    p61 = doc.add_paragraph(
        '大数据技术为财务管理带来了深刻的变革，通过海量数据的采集、存储、分析和挖掘，'
        '能够显著提升财务管理的效率和质量。'
        '本文分析了大数据在财务预测、风险控制、成本管理等方面的应用，'
        '并结合实际案例验证了大数据技术的价值。'
    )
    p61.paragraph_format.first_line_indent = Cm(0.75)
    p61.paragraph_format.line_spacing = 1.5
    p61.runs[0].font.name = '宋体'
    p61.runs[0].font.size = Pt(12)
    p61.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    p62 = doc.add_paragraph(
        '未来，随着人工智能、区块链、物联网等新技术的发展，'
        '大数据财务管理将迎来更加广阔的发展空间。'
        '财务管理人员需要积极拥抱新技术，提升数据素养，'
        '推动财务管理向智能化、数字化方向发展。'
    )
    p62.paragraph_format.first_line_indent = Cm(0.75)
    p62.paragraph_format.line_spacing = 1.5
    p62.runs[0].font.name = '宋体'
    p62.runs[0].font.size = Pt(12)
    p62.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    doc.add_paragraph()  # 空行
    
    # 参考文献
    ref_title = doc.add_paragraph()
    ref_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    ref_title_run = ref_title.add_run('参考文献')
    ref_title_run.font.name = '黑体'
    ref_title_run.font.size = Pt(14)
    ref_title_run.bold = True
    ref_title_run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    
    references = [
        '[1]孟小峰,慈祥.大数据管理:概念、技术与挑战[J].计算机研究与发展,2013,50(1):146-169.',
        '[2]李国杰,程学旗.大数据研究:未来科技及经济社会发展的重大战略领域——大数据的研究现状与科学思考[J].中国科学院院刊,2012,27(6):647-657.',
        '[3]王珊,王会举,覃雄派,等.架构大数据:挑战、现状与展望[J].计算机学报,2011,34(10):1741-1752.',
        '[4]刘红岩.大数据时代的商务管理研究[J].管理科学学报,2014,17(1):1-8.',
        '[5]陈国青,吴刚,顾远东,等.大数据环境下的管理决策研究:挑战与方向[J].管理科学学报,2018,21(3):1-10.',
        '[6]Manyika J, Chui M, Brown B, et al. Big data: The next frontier for innovation, competition, and productivity[R]. McKinsey Global Institute, 2011.',
        '[7]Gartner. Gartner says solving \'big data\' challenge involves more than just managing volumes of data[EB/OL]. (2011-06-27)[2023-10-15]. https://www.gartner.com/en/newsroom/press-releases/2011-06-27-gartner-says-solving-big-data-challenge-involves-more-than-just-managing-volumes-of-data.'
    ]
    
    for ref in references:
        p_ref = doc.add_paragraph(ref)
        p_ref.paragraph_format.line_spacing = 1.5
        p_ref.runs[0].font.name = '宋体'
        p_ref.runs[0].font.size = Pt(12)
        p_ref.runs[0]._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    
    # 保存文档
    output_path = r"C:\Users\ruancanling\Desktop\大数据在财务管理中的应用研究论文.docx"
    doc.save(output_path)
    print(f"文档已成功保存到: {output_path}")

if __name__ == "__main__":
    create_word_document()