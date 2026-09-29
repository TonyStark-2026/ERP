# -*- coding: utf-8 -*-
"""
手动生成一个完整的docx文件
.docx本质上是一个ZIP压缩包，包含XML文件
"""
import os
import zipfile
import io
import re


def escape_xml(text):
    """转义XML特殊字符"""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))


def make_paragraph(text, size=24, bold=False, align='left', first_line_indent=0, line_rule='auto', line=312):
    """
    生成段落XML
    size: 字号（半点单位，24=小四，32=四号）
    bold: 是否加粗
    align: 对齐方式 (left, center, right, both)
    first_line_indent: 首行缩进字符数 * 100
    line_rule: 行距规则 (auto, exact, atLeast)
    line: 行距值（240=单倍, 360=1.5倍, 480=双倍, 312=1.25倍）
    """
    if bold:
        run_props = '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="SimHei" w:cs="Times New Roman"/><w:b/><w:bCs/><w:sz w:val="{}"/><w:szCs w:val="{}"/></w:rPr>'.format(size, size)
    else:
        run_props = '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="SimSun" w:cs="Times New Roman"/><w:sz w:val="{}"/><w:szCs w:val="{}"/></w:rPr>'.format(size, size)

    # 行距
    spacing = '<w:spacing w:line="{}" w:lineRule="{}"/>'.format(line, line_rule)

    # 缩进
    if first_line_indent > 0:
        spacing += '<w:ind w:firstLineChars="{}" w:firstLine="{}"/>'.format(first_line_indent * 100, first_line_indent * 200)
    else:
        spacing += '<w:ind w:firstLineChars="0" w:firstLine="0"/>'

    # 对齐
    jc = '<w:jc w:val="{}"/>'.format(align)

    return f'<w:p><w:pPr>{spacing}{jc}<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="SimSun" w:cs="Times New Roman"/><w:sz w:val="{size}"/><w:szCs w:val="{size}"/></w:rPr></w:pPr><w:r>{run_props}<w:t xml:space="preserve">{escape_xml(text)}</w:t></w:r></w:p>'


def make_heading(text, level=1):
    """生成标题段落"""
    if level == 1:
        size = 32  # 三号
        bold = True
        ind_chars = 0
    elif level == 2:
        size = 28  # 四号
        bold = True
        ind_chars = 0
    else:
        size = 24
        bold = True
        ind_chars = 0

    if bold:
        run_props = '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="SimHei" w:cs="Times New Roman"/><w:b/><w:bCs/><w:sz w:val="{}"/><w:szCs w:val="{}"/></w:rPr>'.format(size, size)
    else:
        run_props = '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="SimSun" w:cs="Times New Roman"/><w:sz w:val="{}"/><w:szCs w:val="{}"/></w:rPr>'.format(size, size)

    spacing = '<w:spacing w:line="312" w:lineRule="auto"/>'
    if level == 1:
        spacing += '<w:ind w:firstLineChars="0" w:firstLine="0"/>'
    jc = '<w:jc w:val="left"/>'

    # 大纲级别
    outline_lvl = f'<w:outlineLvl w:val="{level-1}"/>'

    return f'<w:p><w:pPr>{spacing}{jc}{outline_lvl}<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="SimHei" w:cs="Times New Roman"/><w:b/><w:bCs/><w:sz w:val="{size}"/><w:szCs w:val="{size}"/></w:rPr></w:pPr><w:r>{run_props}<w:t xml:space="preserve">{escape_xml(text)}</w:t></w:r></w:p>'


def make_title(text):
    """生成论文主标题"""
    size = 32  # 三号
    run_props = '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="SimHei" w:cs="Times New Roman"/><w:b/><w:bCs/><w:sz w:val="{}"/><w:szCs w:val="{}"/></w:rPr>'.format(size, size)

    spacing = '<w:spacing w:line="312" w:lineRule="auto"/><w:ind w:firstLineChars="0" w:firstLine="0"/>'
    jc = '<w:jc w:val="center"/>'
    outline_lvl = '<w:outlineLvl w:val="0"/>'

    return f'<w:p><w:pPr>{spacing}{jc}{outline_lvl}<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="SimHei" w:cs="Times New Roman"/><w:b/><w:bCs/><w:sz w:val="{size}"/><w:szCs w:val="{size}"/></w:rPr></w:pPr><w:r>{run_props}<w:t xml:space="preserve">{escape_xml(text)}</w:t></w:r></w:p>'


def build_document_xml(paragraphs):
    """构建完整的document.xml"""
    body = ''.join(paragraphs)
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:cx="http://schemas.microsoft.com/office/drawing/2014/chartex" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" mc:Ignorable="w14 w15 wp14"><w:body>{body}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1080" w:bottom="1440" w:left="1080" w:header="851" w:footer="992" w:gutter="0"/><w:cols w:space="708"/><w:docGrid w:linePitch="360"/></w:sectPr></w:body></w:document>'''


CONTENT_TYPES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/><Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/><Override PartName="/word/fontTable.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/><Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/></Types>'''

ROOT_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>'''

DOCUMENT_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable" Target="fontTable.xml"/></Relationships>'''

STYLES_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml" mc:Ignorable="w14 w15"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:eastAsia="SimSun" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="24"/><w:szCs w:val="24"/><w:lang w:val="en-US" w:eastAsia="zh-CN" w:bidi="ar-SA"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:line="312" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults><w:style w:type="paragraph" w:default="1" w:styleId="a"><w:name w:val="Normal"/><w:qFormat/></w:style><w:style w:type="character" w:default="1" w:styleId="a0"><w:name w:val="Default Paragraph Font"/><w:uiPriority w:val="1"/><w:semiHidden/><w:unhideWhenUsed/></w:style><w:style w:type="table" w:default="1" w:styleId="a1"><w:name w:val="Normal Table"/><w:uiPriority w:val="99"/><w:semiHidden/><w:unhideWhenUsed/></w:style><w:style w:type="numbering" w:default="1" w:styleId="a2"><w:name w:val="No List"/><w:uiPriority w:val="99"/><w:semiHidden/><w:unhideWhenUsed/></w:style></w:styles>'''

SETTINGS_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml" xmlns:sl="http://schemas.openxmlformats.org/schemaLibrary/2006/main"><w:zoom w:percent="100"/><w:proofState w:spelling="clean" w:grammar="clean"/><w:defaultTabStop w:val="420"/><w:characterSpacingControl w:val="compressPunctuation"/><w:compat><w:useFELayout/><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/><w:compatSetting w:name="overrideTableStyleFontSizeAndJustification" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/><w:compatSetting w:name="enableOpenTypeFeatures" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/><w:compatSetting w:name="doNotFlipMirrorIndents" w:uri="http://schemas.microsoft.com/office/word" w:val="1"/></w:compat><w:themeFontLang w:val="en-US" w:eastAsia="zh-CN"/></w:settings>'''

FONT_TABLE_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:fonts xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml" mc:Ignorable="w14 w15"><w:font w:name="Times New Roman"><w:panose1 w:val="02020603050405020304"/><w:charset w:val="00"/><w:family w:val="roman"/><w:pitch w:val="variable"/></w:font><w:font w:name="SimSun"><w:altName w:val="宋体"/><w:panose1 w:val="02010600030101010101"/><w:charset w:val="86"/><w:family w:val="auto"/><w:pitch w:val="variable"/></w:font><w:font w:name="SimHei"><w:altName w:val="黑体"/><w:panose1 w:val="02010609060101010101"/><w:charset w:val="86"/><w:family w:val="modern"/><w:pitch w:val="fixed"/></w:font></w:fonts>'''

CORE_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>大数据时代会计职业发展的机遇与挑战</dc:title><dc:creator>阮粲凌</dc:creator><cp:lastModifiedBy>阮粲凌</cp:lastModifiedBy><dcterms:created xsi:type="dcterms:W3CDTF">2026-06-16T00:00:00Z</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">2026-06-16T00:00:00Z</dcterms:modified></cp:coreProperties>'''

APP_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Application>Microsoft Office Word</Application><AppVersion>16.0000</AppVersion></Properties>'''


def build_paper():
    """构建论文内容"""
    paragraphs = []

    # 标题：三号黑体加粗居中
    paragraphs.append(make_title("大数据时代会计职业发展的机遇与挑战"))

    # 空行
    paragraphs.append(make_paragraph("", align="left"))

    # 摘要标题
    paragraphs.append(make_paragraph("【摘要】", size=24, bold=False, align="left"))
    # 摘要内容
    abstract = "随着大数据、人工智能、云计算等信息技术的快速发展，会计行业正经历着前所未有的变革。传统的手工记账、会计核算模式逐渐被自动化记账、智能报表、智能审计等新技术所取代，会计人员的职业能力要求也发生了深刻变化。本文从大数据时代会计工作的主要变化出发，分析了大数据技术对传统会计核算、财务分析、审计工作的影响，从\u300c机遇\u300d和\u300c挑战\u300d两个方面进行了系统论述，并结合会计专业学生实际，提出了未来会计人员应具备的核心能力以及会计专业学生适应大数据时代的学习建议。研究表明，大数据时代为会计职业发展带来了重要机遇，也带来了严峻挑战，会计人员需要积极转变思维、提升能力，主动适应技术变革。"
    paragraphs.append(make_paragraph(abstract, size=24, bold=False, align="both", first_line_indent=2))

    # 关键词
    keywords = "【关键词】大数据；会计职业；智能财务；数据分析；职业发展"
    paragraphs.append(make_paragraph(keywords, size=24, bold=False, align="left"))

    # 空行
    paragraphs.append(make_paragraph("", align="left"))

    # 1. 引言
    paragraphs.append(make_heading("1  引言", level=1))
    intro = "在数字经济时代，大数据、云计算、人工智能等新兴技术正深刻地改变着各行各业。作为经济管理的重要组成部分，会计行业也面临着技术变革带来的机遇与挑战。传统的会计工作以手工记账、纸质凭证为基础，主要依赖会计人员的专业判断和经验积累。然而，随着企业业务规模的扩大和信息化水平的提高，会计数据呈现爆炸式增长，传统的会计处理方式已经难以满足现代企业管理的需要[1]。大数据技术的兴起，为会计行业提供了全新的技术手段和思维方式，使会计工作从传统的事后核算向事前的预测分析、事中的实时控制转变。深入研究大数据时代会计职业发展的机遇与挑战，对于会计专业学生明确学习方向、提升专业能力具有重要的现实意义。"
    paragraphs.append(make_paragraph(intro, size=24, bold=False, align="both", first_line_indent=2))

    # 2. 大数据时代会计工作的主要变化
    paragraphs.append(make_heading("2  大数据时代会计工作的主要变化", level=1))

    paragraphs.append(make_heading("2.1  工作方式的变化", level=2))
    content_2_1 = "在大数据时代，会计工作的方式发生了根本性变化。传统的手工记账方式逐渐被电子化、自动化的会计信息系统所取代。会计人员不再需要花费大量时间在凭证录入、账簿登记等基础性工作上，而是可以通过会计软件实现凭证的自动生成、账簿的自动登记、报表的自动编制[2]。例如，财务机器人流程自动化（RPA）技术可以自动完成发票识别、银行对账、费用报销等重复性工作，大大提高了会计工作的效率。同时，云会计、移动会计等新型工作方式的出现，使会计人员可以随时随地处理会计业务，进一步提升了工作的灵活性。"
    paragraphs.append(make_paragraph(content_2_1, size=24, bold=False, align="both", first_line_indent=2))

    paragraphs.append(make_heading("2.2  工作内容的变化", level=2))
    content_2_2 = "大数据时代，会计工作的内容从传统的\u300c记账、算账、报账\u300d向\u300c管理决策支持\u300d转变。会计人员不仅需要完成基础的会计核算工作，还需要运用大数据技术对企业经营数据进行分析，为企业管理层的决策提供数据支持。例如，通过对销售数据、成本数据、市场数据的分析，会计人员可以帮助企业进行产品定价、库存管理、营销策略制定等经营决策[3]。会计工作的价值从\u300c反映过去\u300d向\u300c预测未来、控制现在\u300d转变，会计人员从\u300c账房先生\u300d向\u300c管理参谋\u300d角色转变。"
    paragraphs.append(make_paragraph(content_2_2, size=24, bold=False, align="both", first_line_indent=2))

    paragraphs.append(make_heading("2.3  工作要求的变化", level=2))
    content_2_3 = "大数据时代对会计人员的素质要求发生了显著变化。除了传统的会计专业知识外，会计人员还需要具备数据分析能力、信息技术应用能力、跨领域沟通能力等综合素质。会计人员需要能够运用大数据工具对企业数据进行采集、清洗、分析和可视化呈现，需要能够理解业务、解读数据、提供有价值的财务分析报告[4]。同时，会计人员还需要具备持续学习的能力，以适应不断更新的技术环境和业务需求。"
    paragraphs.append(make_paragraph(content_2_3, size=24, bold=False, align="both", first_line_indent=2))

    # 3. 大数据技术对会计工作的影响
    paragraphs.append(make_heading("3  大数据技术对会计工作的影响", level=1))

    paragraphs.append(make_heading("3.1  对会计核算的影响", level=2))
    content_3_1 = "大数据技术对会计核算工作产生了深远影响。首先，大数据技术实现了会计核算的自动化。通过OCR（光学字符识别）技术、语音识别技术等，可以实现发票、合同等纸质凭证的自动识别和数据录入；通过财务机器人流程自动化（RPA）技术，可以实现银行对账、凭证生成、报表编制等流程的自动化处理。其次，大数据技术提升了会计核算的准确性。通过预设的规则和算法，可以减少人工操作中的错误和舞弊风险；通过实时的数据校验和监控，可以及时发现和纠正核算错误。最后，大数据技术扩展了会计核算的维度。传统会计核算主要关注财务数据，而大数据技术可以将非财务数据纳入核算范围，实现财务与非财务数据的融合分析[5]。例如，可以将客户满意度、员工绩效、市场份额等非财务指标与财务指标结合分析，为企业提供更全面的价值评估。"
    paragraphs.append(make_paragraph(content_3_1, size=24, bold=False, align="both", first_line_indent=2))

    paragraphs.append(make_heading("3.2  对财务分析的影响", level=2))
    content_3_2 = "大数据技术为财务分析工作带来了革命性的变化。传统的财务分析主要基于财务报表数据，采用比较分析、比率分析、趋势分析等方法进行分析，数据的维度和深度有限。而大数据技术能够整合企业内外部的多种数据源，包括财务数据、业务数据、市场数据、行业数据、宏观经济数据等，构建更加全面的数据分析体系。在分析方法上，机器学习、深度学习等人工智能技术可以应用于财务分析中，实现更加复杂和精准的分析模型。例如，可以利用时间序列分析、神经网络等算法进行销售预测、风险预警；可以利用聚类分析、关联分析等方法进行客户分群、产品关联分析；可以利用文本分析技术进行舆情监控、合同风险分析等[6]。大数据技术使财务分析从\u300c描述性分析\u300d向\u300c诊断性分析\u300d、\u300c预测性分析\u300d、\u300c指导性分析\u300d转变，分析的深度和价值显著提升。"
    paragraphs.append(make_paragraph(content_3_2, size=24, bold=False, align="both", first_line_indent=2))

    paragraphs.append(make_heading("3.3  对审计工作的影响", level=2))
    content_3_3 = "大数据技术对审计工作也产生了重要影响。在审计数据采集方面，传统的审计主要采用抽样方法，存在样本代表性不足的风险。大数据技术可以实现全量数据分析，使审计人员能够对被审计单位的全部交易数据进行分析，大大提高了审计的全面性和准确性。在审计分析方法方面，大数据技术支持更加复杂的分析模型，如异常检测、模式识别、关联分析等，能够发现传统抽样审计难以发现的舞弊和异常情况。在审计工作方式方面，远程审计、持续审计等新型审计模式得以实现，审计工作的效率和及时性显著提升[7]。同时，大数据技术也对审计人员的专业能力提出了更高要求，审计人员需要具备数据分析能力、信息技术应用能力等新技能。"
    paragraphs.append(make_paragraph(content_3_3, size=24, bold=False, align="both", first_line_indent=2))

    # 4. 大数据时代会计职业发展的机遇与挑战
    paragraphs.append(make_heading("4  大数据时代会计职业发展的机遇与挑战", level=1))

    paragraphs.append(make_heading("4.1  发展机遇", level=2))
    content_4_1 = "大数据时代为会计职业发展带来了重要机遇。第一，工作效率显著提升。自动化、智能化的会计工具使会计人员从繁琐的基础工作中解放出来，可以将更多时间和精力投入到高价值的分析、决策支持工作中。第二，职业发展空间得到拓展。大数据时代产生了许多新兴的会计岗位，如数据分析师、财务数据科学家、智能财务系统管理员等，会计人员的职业选择更加多元化。第三，职业价值得到提升。会计人员通过提供深度的数据分析和管理建议，能够更直接地参与企业经营管理，职业的不可替代性增强。第四，专业能力得到提升的机会增多。大数据技术为会计人员提供了更多的学习资源和实践机会，会计人员可以通过应用新技术不断提升自己的专业能力[8]。第五，跨领域发展成为可能。会计人员可以结合数据分析、商业分析、信息技术等领域的知识，实现跨领域发展，职业的复合性和竞争力增强。"
    paragraphs.append(make_paragraph(content_4_1, size=24, bold=False, align="both", first_line_indent=2))

    paragraphs.append(make_heading("4.2  面临挑战", level=2))
    content_4_2 = "大数据时代会计职业发展也面临着严峻挑战。第一，岗位竞争加剧。大数据技术使部分基础会计岗位被自动化工具和智能系统所取代，传统的\u300c记账型\u300d会计人员面临失业风险，而具备数据分析能力的新型会计人才需求旺盛，供需结构性矛盾突出。第二，知识更新压力加大。大数据技术更新速度快，会计人员需要不断学习新技术、新方法，更新知识结构，学习压力和成本增加。第三，数据安全与合规风险增加。大数据环境下，会计数据面临着泄露、篡改、未授权访问等安全风险，会计人员需要承担数据安全管理的责任，违规风险和法律风险增加[9]。第四，职业能力要求提高。大数据时代要求会计人员具备数据分析、信息技术应用、跨领域沟通等综合能力，传统单一会计专业的会计人员面临能力转型的压力。第五，伦理和隐私问题突出。大数据分析涉及大量的个人和商业数据，会计人员在使用数据时需要面对数据使用边界、隐私保护、算法公平性等伦理问题。"
    paragraphs.append(make_paragraph(content_4_2, size=24, bold=False, align="both", first_line_indent=2))

    # 5. 未来会计人员应具备的能力
    paragraphs.append(make_heading("5  未来会计人员应具备的能力", level=1))
    content_5 = "结合大数据时代的特点和会计职业发展的要求，未来会计人员应具备以下几方面的核心能力。第一，扎实的会计专业基础能力。包括会计核算、财务报表分析、税务筹划、内部控制、审计等专业知识，这是会计人员的立身之本。第二，数据分析能力。包括数据采集、清洗、可视化、统计分析和机器学习应用等能力，能够运用数据分析工具解决实际财务问题[10]。第三，信息技术应用能力。包括会计信息系统操作、数据处理工具应用、数据库管理、基础编程等能力，能够适应智能化会计工作环境。第四，业务理解能力。深入了解企业业务、行业特点、宏观经济环境，能够将会计工作与业务紧密结合，提供有价值的财务分析和支持。第五，沟通协作能力。能够与业务部门、管理层、信息技术部门等进行有效沟通，推动跨部门协作。第六，持续学习能力。能够主动跟踪新技术、新方法、新法规的发展，不断更新知识结构，适应快速变化的职业环境。第七，职业判断和决策能力。在复杂多变的环境中，能够基于数据和专业判断做出合理决策。"
    paragraphs.append(make_paragraph(content_5, size=24, bold=False, align="both", first_line_indent=2))

    # 6. 会计专业学生的学习建议
    paragraphs.append(make_heading("6  会计专业学生的学习建议", level=1))
    content_6 = "面对大数据时代的机遇和挑战，会计专业学生应从以下几个方面加强学习。第一，夯实专业基础。系统学习会计学、财务管理、审计学、税法等核心课程，建立完整的会计专业知识体系，为未来的职业发展奠定坚实基础。第二，加强数据分析能力培养。主动学习统计学、数据分析、机器学习等课程或培训内容，掌握Excel高级应用、SQL、Python等数据分析工具，提升数据处理和分析能力。第三，提升信息技术素养。学习企业管理信息系统、ERP系统、数据库原理等信息技术相关知识，了解人工智能、区块链等前沿技术的发展趋势，培养信息技术应用能力。第四，重视实践能力培养。积极参加实习、实践项目、学科竞赛等活动，将理论知识应用于实际，提升解决实际问题的能力[1]。第五，培养跨领域思维。除了会计专业知识外，还应学习金融、管理、市场营销、信息技术等相关领域的知识，建立复合型知识结构。第六，提升英语和沟通能力。关注国际财务报告准则的发展，具备一定的英语沟通能力，提升跨文化沟通和协作能力。第七，培养职业道德和终身学习习惯。树立诚信、严谨、专业的职业道德观念，培养持续学习、主动学习的习惯，为未来的职业发展奠定良好基础。"
    paragraphs.append(make_paragraph(content_6, size=24, bold=False, align="both", first_line_indent=2))

    # 结论
    paragraphs.append(make_heading("7  结论", level=1))
    conclusion = "大数据时代为会计职业发展带来了前所未有的变革和重要机遇。通过大数据技术的应用，会计工作的效率和质量显著提升，会计人员的职业价值得到新的体现，职业发展空间得到新的拓展。但同时，大数据时代也带来了岗位结构调整、能力要求提升、数据安全风险等多方面的挑战。会计人员需要积极转变观念，主动学习新技术、新方法，不断提升数据分析能力、信息技术应用能力、业务理解能力和综合职业素养。会计专业学生应在校期间夯实专业基础，加强数据分析能力培养，提升信息技术素养，重视实践能力培养，培养跨领域思维和终身学习习惯，以适应大数据时代的要求，实现个人职业的可持续发展。"
    paragraphs.append(make_paragraph(conclusion, size=24, bold=False, align="both", first_line_indent=2))

    # 参考文献
    paragraphs.append(make_heading("参考文献", level=1))
    refs = [
        "[1] 孟小峰,慈祥.大数据管理:概念、技术与挑战[J].计算机研究与发展,2013,50(1):146-169.",
        "[2] 李国杰,程学旗.大数据研究:未来科技及经济社会发展的重大战略领域[J].中国科学院院刊,2012,27(6):647-657.",
        "[3] 王珊,王会举,覃雄派,等.架构大数据:挑战、现状与展望[J].计算机学报,2011,34(10):1741-1752.",
        "[4] 刘红岩.大数据时代的商务管理研究[J].管理科学学报,2014,17(1):1-8.",
        "[5] 陈国青,吴刚,顾远东,等.大数据环境下的管理决策研究:挑战与方向[J].管理科学学报,2018,21(3):1-10.",
        "[6] Manyika J, Chui M, Brown B, et al. Big data: The next frontier for innovation, competition, and productivity[R]. McKinsey Global Institute, 2011.",
        "[7] Chen H, Chiang R H L, Storey V C. Business Intelligence and Analytics: From Big Data to Big Impact[J]. MIS Quarterly, 2012, 36(4): 1165-1188.",
    ]
    for ref in refs:
        # 参考文献：两端对齐，无首行缩进，悬挂缩进2字符
        ref_para = f'<w:p><w:pPr><w:spacing w:line="312" w:lineRule="auto"/><w:ind w:left="420" w:hanging="420"/><w:jc w:val="both"/><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="SimSun" w:cs="Times New Roman"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="SimSun" w:cs="Times New Roman"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr><w:t xml:space="preserve">{escape_xml(ref)}</w:t></w:r></w:p>'
        paragraphs.append(ref_para)

    return paragraphs


def create_docx(output_path):
    """创建docx文件"""
    paragraphs = build_paper()
    document_xml = build_document_xml(paragraphs)

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', CONTENT_TYPES)
        zf.writestr('_rels/.rels', ROOT_RELS)
        zf.writestr('word/_rels/document.xml.rels', DOCUMENT_RELS)
        zf.writestr('word/document.xml', document_xml)
        zf.writestr('word/styles.xml', STYLES_XML)
        zf.writestr('word/settings.xml', SETTINGS_XML)
        zf.writestr('word/fontTable.xml', FONT_TABLE_XML)
        zf.writestr('docProps/core.xml', CORE_XML)
        zf.writestr('docProps/app.xml', APP_XML)


if __name__ == '__main__':
    output_path = r"C:\Users\ruancanling\Desktop\24会计X班+20240604430529+阮粲凌+《大数据基础》期末考核.docx"
    create_docx(output_path)
    print(f"论文docx文件已成功创建: {output_path}")
    print(f"文件大小: {os.path.getsize(output_path)} 字节")
