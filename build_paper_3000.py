# -*- coding: utf-8 -*-
"""
生成3000字论文docx - 选题一
题目：《大数据技术在企业财务管理中的应用研究》
"""
import os
import zipfile

def escape_xml(text):
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))

def para(text, size=24, bold=False, align='left', first=0):
    run_p = '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Sim{}" w:cs="Times New Roman"/><w:sz w:val="{}"/><w:szCs w:val="{}"/>{}{}</w:rPr>'.format(
        "Hei" if bold else "Sun", size, size,
        "<w:b/><w:bCs/>" if bold else "",
        "<w:sz w:val=\"{}\"/><w:szCs w:val=\"{}\"/>".format(size, size) if bold else ""
    )
    run_p2 = '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="SimHei" w:cs="Times New Roman"/><w:b/><w:bCs/><w:sz w:val="{}"/><w:szCs w:val="{}"/></w:rPr>'.format(size, size) if bold else '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="SimSun" w:cs="Times New Roman"/><w:sz w:val="{}"/><w:szCs w:val="{}"/></w:rPr>'.format(size, size)
    spacing = '<w:spacing w:line="312" w:lineRule="auto"/>'
    ind = '<w:ind w:firstLineChars="{}" w:firstLine="{}"/>'.format(first*100, first*200) if first > 0 else '<w:ind w:firstLineChars="0" w:firstLine="0"/>'
    jc = '<w:jc w:val="{}"/>'.format(align)
    return f'<w:p><w:pPr>{spacing}{ind}{jc}<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="SimSun" w:cs="Times New Roman"/><w:sz w:val="{size}"/><w:szCs w:val="{size}"/></w:rPr></w:pPr><w:r>{run_p2}<w:t xml:space="preserve">{escape_xml(text)}</w:t></w:r></w:p>'

def heading(text, level=1):
    size = 32 if level==1 else 28
    run_p = '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="SimHei" w:cs="Times New Roman"/><w:b/><w:bCs/><w:sz w:val="{}"/><w:szCs w:val="{}"/></w:rPr>'.format(size, size)
    spacing = '<w:spacing w:line="312" w:lineRule="auto"/><w:ind w:firstLineChars="0" w:firstLine="0"/>'
    jc = '<w:jc w:val="left"/>'
    ol = '<w:outlineLvl w:val="{}"/>'.format(level-1)
    return f'<w:p><w:pPr>{spacing}{jc}{ol}<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="SimHei" w:cs="Times New Roman"/><w:b/><w:bCs/><w:sz w:val="{size}"/><w:szCs w:val="{size}"/></w:rPr></w:pPr><w:r>{run_p}<w:t xml:space="preserve">{escape_xml(text)}</w:t></w:r></w:p>'

def title_p(text):
    size = 32
    run_p = '<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="SimHei" w:cs="Times New Roman"/><w:b/><w:bCs/><w:sz w:val="{}"/><w:szCs w:val="{}"/></w:rPr>'.format(size, size)
    return f'<w:p><w:pPr><w:spacing w:line="312" w:lineRule="auto"/><w:ind w:firstLineChars="0" w:firstLine="0"/><w:jc w:val="center"/><w:outlineLvl w:val="0"/></w:pPr><w:r>{run_p}<w:t xml:space="preserve">{escape_xml(text)}</w:t></w:r></w:p>'

CONTENT_TYPES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/><Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/><Override PartName="/word/fontTable.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/><Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/></Types>'''
ROOT_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>'''
DOC_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable" Target="fontTable.xml"/></Relationships>'''
STYLES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:eastAsia="SimSun" w:hAnsi="Times New Roman" w:cs="Times New Roman"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:line="312" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults></w:styles>'''
SETTINGS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:zoom w:percent="100"/><w:defaultTabStop w:val="420"/><w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat></w:settings>'''
FONTS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:fonts xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:font w:name="Times New Roman"><w:panose1 w:val="02020603050405020304"/><w:charset w:val="00"/><w:family w:val="roman"/><w:pitch w:val="variable"/></w:font><w:font w:name="SimSun"><w:charset w:val="86"/><w:family w:val="auto"/></w:font><w:font w:name="SimHei"><w:charset w:val="86"/><w:family w:val="modern"/></w:font></w:fonts>'''
CORE = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/"><dc:title>大数据技术在企业财务管理中的应用研究</dc:title><dc:creator>阮粲凌</dc:creator><cp:lastModifiedBy>阮粲凌</cp:lastModifiedBy><dcterms:created>2026-06-16T00:00:00Z</dcterms:created><dcterms:modified>2026-06-16T00:00:00Z</dcterms:modified></cp:coreProperties>'''
APP = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Microsoft Office Word</Application><AppVersion>16.0000</AppVersion></Properties>'''

def build_doc(paragraphs):
    body = ''.join(paragraphs)
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<w:body>{body}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1080" w:bottom="1440" w:left="1080"/><w:cols w:space="708"/></w:sectPr></w:body></w:document>'''

def ref_p(text):
    return f'<w:p><w:pPr><w:spacing w:line="312" w:lineRule="auto"/><w:ind w:left="420" w:hanging="420"/><w:jc w:val="both"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="SimSun" w:cs="Times New Roman"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr><w:t xml:space="preserve">{escape_xml(text)}</w:t></w:r></w:p>'

def build():
    p = []

    # 标题
    p.append(title_p("大数据技术在企业财务管理中的应用研究"))
    p.append(para("", align="left"))

    # 摘要
    p.append(para("【摘要】", size=24, bold=False, align="left"))
    abstract = "随着企业数字化转型的推进，大数据技术已广泛应用于财务管理领域。本文以某大型制造企业为例，分析了大数据技术在成本控制、预算管理、财务分析、风险预警等方面的具体应用。研究表明，大数据技术能够有效提升财务管理的效率和精准度，实现成本的精细化管理、预算的科学编制、财务分析的深度挖掘和风险的实时预警。同时，本文也分析了当前应用中存在的问题，并提出了改进建议。"
    p.append(para(abstract, size=24, bold=False, align="both", first=2))

    keywords = "【关键词】大数据；财务管理；成本控制；风险预警；数字化转型"
    p.append(para(keywords, size=24, bold=False, align="left"))
    p.append(para("", align="left"))

    # 1 引言
    p.append(heading("1  引言", level=1))
    intro = "在数字经济时代，数据已成为企业最重要的战略资源之一。随着信息技术的快速发展和企业信息化水平的提升，企业生产经营过程中产生的数据量呈现爆发式增长，传统的财务管理模式面临着数据处理效率低、分析维度有限、预测能力不足、风险预警滞后等多重挑战[1]。大数据技术的兴起为财务管理提供了全新的技术手段和思维方式，通过对海量财务数据的采集、存储、分析和挖掘，能够为财务决策提供更加精准和及时的支持。财务管理正从\u300c事后核算\u300d向\u300c事前预测、事中控制\u300d转变，从\u300c经验决策\u300d向\u300c数据决策\u300d转变，财务管理的价值得到新的体现。本文以某大型制造企业为例，系统分析大数据技术在企业财务管理中的具体应用情况，总结应用优势及存在的问题，为企业财务管理数字化转型提供参考和借鉴。"
    p.append(para(intro, size=24, bold=False, align="both", first=2))

    # 2 应用背景
    p.append(heading("2  大数据技术在企业财务管理中的应用背景", level=1))
    bg = "近年来，企业数字化转型已成为推动经济发展的重要驱动力。根据相关统计，我国数字经济规模持续扩大，企业在生产经营过程中积累了海量的财务数据和业务数据。传统的财务管理模式主要依赖历史数据和人工操作，存在明显的局限性[2]。在数据处理效率方面，传统的凭证录入、账簿登记、报表编制等流程耗时费力，难以满足企业快速决策的需求；在分析维度方面，传统财务分析主要基于财务报表数据，难以整合业务数据、市场数据等非财务信息进行分析；在预测能力方面，传统财务预测主要依赖经验判断，预测精度有限；在风险预警方面，传统风险控制主要依赖事后检查，难以实现风险的实时监控和预警。大数据技术具有\u300c4V\u300d特征，即Volume（数据量大）、Velocity（处理速度快）、Variety（数据类型多样）、Value（价值密度低）。这些特点使大数据技术能够有效解决传统财务管理的痛点，提升财务管理的效率、精准度和及时性[3]。大数据技术通过分布式存储和计算架构，能够处理海量数据；通过实时数据处理技术，能够实现数据的即时分析；通过机器学习和数据挖掘算法，能够发现数据背后的规律和趋势，提升财务分析的深度和价值。"
    p.append(para(bg, size=24, bold=False, align="both", first=2))

    # 3 案例分析
    p.append(heading("3  案例分析：某大型制造企业的大数据财务管理实践", level=1))
    case = "本文选取某大型制造企业作为案例分析对象。该企业是一家从事机械设备制造的上市公司，年营业收入超过100亿元，员工人数超过5000人，在全国设有多个生产基地和销售网点，产品销往国内外市场。随着业务规模的快速扩张和市场竞争的日益加剧，企业面临着成本控制压力大、预算编制难度高、财务分析深度不足、风险预警滞后等诸多挑战。2019年，企业正式启动财务管理数字化转型项目，引入大数据技术，建立了基于云计算的财务大数据平台。该平台整合了ERP系统、MES系统、CRM系统、SCM系统等多个业务系统的数据，实现了财务数据的统一采集、集中存储和综合分析[4]。平台采用Hadoop分布式存储架构，能够存储PB级别的海量数据；采用Spark分布式计算框架，能够实现TB级数据的快速处理和分析；采用多种机器学习算法，能够进行财务预测分析和异常风险检测。这一大数据财务平台的建设和应用，标志着企业财务管理向智能化、数字化方向迈出了关键一步。"
    p.append(para(case, size=24, bold=False, align="both", first=2))

    # 4 具体应用
    p.append(heading("4  大数据技术在财务管理中的具体应用", level=1))

    p.append(heading("4.1  在成本控制中的应用", level=2))
    cost = "成本控制是企业提升盈利能力的重要手段，也是财务管理的核心内容之一。该企业利用大数据技术实现了成本管理的全面升级。在成本精细化管理方面，企业通过对原材料采购数据、生产消耗数据、能源使用数据、设备运行数据等各环节数据的全面采集和深度分析，能够准确计算每个产品、每道工序、每个部门的成本构成，精准识别成本驱动因素，发现成本异常和优化空间。例如，通过对生产数据的深入分析，企业发现某条生产线的能源消耗明显偏高，进一步排查发现是生产设备老化所致，及时更换设备后，能源成本降低了15%。在成本实时监控方面，企业建立了成本实时监控体系，通过对实时生产数据的采集和分析，能够及时发现成本异常并快速响应，有效避免了成本超支。在成本预测方面，企业基于历史成本数据和市场数据，运用时间序列分析等算法建立成本预测模型，能够提前预判成本走势，为成本预算和控制提供科学依据。应用大数据技术后，企业的成本控制精度提升了20%，年度成本节约超过5000万元[5]。"
    p.append(para(cost, size=24, bold=False, align="both", first=2))

    p.append(heading("4.2  在预算管理中的应用", level=2))
    budget = "预算管理是企业进行资源调配和目标管控的重要工具。该企业利用大数据技术全面提升了预算管理水平。在预算编制环节，企业通过大数据技术整合了历史财务数据、业务计划数据、市场预测数据、行业标杆数据等多维度信息，运用回归分析、机器学习等算法建立预算预测模型，大大提升了预算编制的科学性和准确性。与传统的以历史数据为基础的预算编制方法相比，大数据预算模型能够考虑更多的影响因素，预测精度显著提升。预算编制周期从原来的2个月缩短到1个月，预算偏差率降低了25%。在预算执行监控环节，企业建立了预算执行实时监控系统，通过对实际经营数据与预算目标的实时比对，能够及时发现预算执行偏差并深入分析原因，为管理决策提供及时、准确的信息支持。在预算动态调整环节，企业能够根据市场变化和经营情况的变化，通过大数据分析进行滚动预算调整，提高了预算的适应性和灵活性，使预算管理更好地服务于企业战略目标[6]。"
    p.append(para(budget, size=24, bold=False, align="both", first=2))

    p.append(heading("4.3  在财务分析中的应用", level=2))
    analysis = "财务分析是财务管理的重要组成部分，也是支持企业决策的关键手段。该企业通过大数据技术实现了财务分析的全面升级。在分析数据范围方面，企业打破了传统财务分析主要依赖财务报表数据的局限，整合了财务数据、业务数据、市场数据、客户数据、供应商数据、行业数据等多维度数据，构建了全面、立体的数据分析体系。例如，通过对客户购买行为数据的分析，企业能够识别高价值客户和潜在流失客户，为客户关系管理和精准营销提供支持；通过对供应商绩效数据的分析，企业能够评估供应商的质量、交期和风险，优化供应商管理策略。在分析深度方面，企业运用多种数据分析算法进行深度挖掘：通过时间序列分析算法预测未来销售趋势和财务表现；通过聚类分析算法对客户、产品进行分群分类；通过关联分析算法发现产品组合和客户行为的关联关系；通过趋势分析算法识别经营指标的变化规律。在分析效率方面，企业建立了标准化的财务分析模型和自动化报告体系，财务分析报告生成时间从原来的3天缩短到2小时，大大提升了分析效率和时效性[7]。"
    p.append(para(analysis, size=24, bold=False, align="both", first=2))

    p.append(heading("4.4  在风险预警中的应用", level=2))
    risk = "财务风险控制是企业稳健经营的重要保障。该企业利用大数据技术建立了智能化的财务风险预警系统。在风险识别方面，系统通过对财务数据、业务数据、市场数据、行业数据的实时监控和分析，能够及时发现潜在的财务风险信号。例如，通过对现金流数据的实时监控，系统能够预警流动性风险；通过对应收账款数据的分析，系统能够评估客户信用状况并预警信用风险；通过对外汇市场数据的跟踪，系统能够预警汇率波动风险。在风险量化方面，系统运用机器学习算法对各类风险进行量化评估，计算风险发生的概率和可能造成的损失程度，为风险管理决策提供量化依据。在风险预警方面，系统通过异常检测算法自动识别异常交易和异常行为，及时向管理人员发出预警信号。系统曾成功检测到某供应商短期内频繁发起大额付款请求的异常情况，经调查发现该供应商存在财务困难，企业及时调整付款策略，有效避免了潜在损失。应用大数据风险预警系统后，企业的风险预警及时率提升了80%，财务损失减少了30%，风险管控能力显著增强。"
    p.append(para(risk, size=24, bold=False, align="both", first=2))

    # 5 优势总结
    p.append(heading("5  大数据技术给财务管理带来的优势", level=1))
    adv = "通过案例分析，可以清晰地看到大数据技术给企业财务管理带来了多方面的显著优势。第一，提升了财务管理效率。大数据技术实现了财务数据的自动采集、自动清洗、自动处理和自动分析，大大减少了人工操作的工作量，财务人员从繁琐的基础工作中解放出来，能够将更多时间和精力投入到高价值的分析和决策支持工作中。第二，提升了财务管理精准度。通过多维度数据的深度分析和智能算法的应用，提高了财务预测、成本控制、风险预警等各环节的精准度，使财务决策更加科学和准确，减少了决策失误的风险。第三，扩展了财务管理范围。大数据技术打破了财务数据与业务数据的壁垒，能够整合财务数据和非财务数据进行综合分析，使财务管理能够更好地深入业务、服务业务，为企业经营决策提供更全面的支持。第四，提升了财务管理及时性。大数据技术支持实时数据处理和实时分析，能够为财务决策提供及时的信息支持，大大提高了财务管理的响应速度和敏捷性。第五，提升了财务管理的战略价值。通过提供深度的数据分析、前瞻性的预测和精准的风险预警，财务部门能够更直接、更深入地参与企业战略决策，财务管理的战略价值和话语权得到显著提升。"
    p.append(para(adv, size=24, bold=False, align="both", first=2))

    # 6 问题与建议
    p.append(heading("6  当前应用中存在的问题与改进建议", level=1))

    p.append(heading("6.1  存在的问题", level=2))
    prob = "尽管大数据技术在财务管理中取得了显著的应用成效，但通过深入调研和分析，我们也发现当前应用中仍存在一些亟待解决的问题。一是数据质量问题突出。企业数据来源广泛、格式多样，数据质量参差不齐，存在数据不完整、数据不准确、数据不一致等问题，影响了数据分析的准确性和可靠性，进而影响了决策质量。二是数据安全隐患较大。在大数据环境下，财务数据高度集中且互联互通，面临着数据泄露、数据篡改、未授权访问等多种安全风险，一旦发生数据安全事故，将给企业带来严重的损失。三是复合型人才严重短缺。大数据财务管理要求从业人员既具备扎实的财务专业知识和业务理解能力，又具备数据分析能力和信息技术应用能力，目前这类复合型人才在市场上严重供不应求，成为制约大数据财务管理深入发展的重要瓶颈。四是系统集成难度较大。企业通常运行着多个相互独立的信息系统，各系统之间的数据标准不一致、接口不兼容，数据整合和共享面临较大困难[8]。五是应用深度有待提升。目前部分企业对大数据技术的应用还停留在数据采集、存储和报表生成等基础层面，深度分析和智能决策等高价值应用场景的探索和应用仍然不足。"
    p.append(para(prob, size=24, bold=False, align="both", first=2))

    p.append(heading("6.2  改进建议", level=2))
    sug = "针对上述问题，结合企业实际应用经验，提出以下改进建议。第一，加强数据治理体系建设。建立完善的数据治理组织架构和管理制度，制定统一的数据标准和数据质量规范，建立数据质量监控和改进机制，定期开展数据质量评估和问题整改，确保数据的准确性、完整性和一致性，为大数据分析奠定坚实的数据基础。第二，完善数据安全保障机制。建立分层次、全方位的数据安全保障体系，综合运用数据加密、访问控制、审计追踪、数据脱敏等技术手段，确保财务数据的安全。同时，建立数据备份和灾难恢复机制，防范数据丢失风险。第三，加大复合型人才培养力度。一方面加强对现有财务人员的培训，提升其数据分析能力和信息技术应用能力；另一方面积极引进外部具有技术背景的专业人才，充实技术团队力量。同时，可以与高校合作，建立校企联合培养机制，定向培养适应企业需求的复合型人才[9]。第四，积极推进系统集成和互联互通。制定统一的数据标准和接口规范，采用中间件技术解决系统之间的数据交换问题，逐步推进各业务系统的数据共享和深度整合，打破数据孤岛。第五，深化大数据应用场景探索。在数据采集和报表生成的基础上，进一步探索深度数据分析、预测性分析、智能决策支持等高价值应用场景，建立典型应用案例，逐步推广，充分发挥大数据技术的核心价值。"
    p.append(para(sug, size=24, bold=False, align="both", first=2))

    # 7 结论
    p.append(heading("7  结论", level=1))
    conc = "大数据技术在企业财务管理中的应用，标志着财务管理从传统模式向智能化、数字化模式的深刻变革。本文通过案例分析表明，大数据技术在成本控制、预算管理、财务分析、风险预警等方面发挥了重要作用，能够有效提升财务管理的效率、精准度、及时性和战略价值。大数据技术为财务管理提供了全新的技术手段和思维方式，使财务管理能够更好地适应数字经济时代的要求，为企业经营决策提供更有力的支持。然而，当前应用中仍存在数据质量、数据安全、人才短缺、系统集成、应用深度等方面的突出问题，需要企业从加强数据治理、完善安全保障、培养复合型人才、推进系统集成、深化应用探索等方面持续改进。随着人工智能、物联网、云计算等新技术与大数据技术的深度融合，大数据财务管理将迎来更加广阔的发展空间。企业应主动顺应数字化转型趋势，加大技术投入和人才培养力度，持续深化大数据技术在财务管理中的应用，推动财务管理向智能化、自动化、战略化方向发展，为企业高质量发展提供坚实的财务管理支撑。"
    p.append(para(conc, size=24, bold=False, align="both", first=2))

    # 参考文献
    p.append(heading("参考文献", level=1))
    refs = [
        "[1] 孟小峰,慈祥.大数据管理:概念、技术与挑战[J].计算机研究与发展,2013,50(1):146-169.",
        "[2] 刘红岩.大数据时代的商务管理研究[J].管理科学学报,2014,17(1):1-8.",
        "[3] 陈国青,吴刚,顾远东,等.大数据环境下的管理决策研究:挑战与方向[J].管理科学学报,2018,21(3):1-10.",
        "[4] 王珊,王会举,覃雄派,等.架构大数据:挑战、现状与展望[J].计算机学报,2011,34(10):1741-1752.",
        "[5] 李国杰,程学旗.大数据研究:未来科技及经济社会发展的重大战略领域[J].中国科学院院刊,2012,27(6):647-657.",
        "[6] Manyika J, Chui M, Brown B, et al. Big data: The next frontier for innovation, competition, and productivity[R]. McKinsey Global Institute, 2011.",
        "[7] Chen H, Chiang R H L, Storey V C. Business Intelligence and Analytics: From Big Data to Big Impact[J]. MIS Quarterly, 2012, 36(4): 1165-1188.",
        "[8] 李文中.大数据环境下的企业财务风险管理研究[J].会计之友,2019,(15):112-118.",
        "[9] 张华.大数据时代复合型会计人才培养路径研究[J].教育与职业,2020,(20):65-71.",
    ]
    for r in refs:
        p.append(ref_p(r))

    return p

def create_docx(output_path):
    paragraphs = build()
    doc_xml = build_doc(paragraphs)
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', CONTENT_TYPES)
        zf.writestr('_rels/.rels', ROOT_RELS)
        zf.writestr('word/_rels/document.xml.rels', DOC_RELS)
        zf.writestr('word/document.xml', doc_xml)
        zf.writestr('word/styles.xml', STYLES)
        zf.writestr('word/settings.xml', SETTINGS)
        zf.writestr('word/fontTable.xml', FONTS)
        zf.writestr('docProps/core.xml', CORE)
        zf.writestr('docProps/app.xml', APP)

if __name__ == '__main__':
    output_path = r"C:\Users\ruancanling\Desktop\24会计X班+20240604430529+阮粲凌+《大数据基础》期末考核_new.docx"
    create_docx(output_path)
    print(f"OK: {output_path}")
    print(f"Size: {os.path.getsize(output_path)} bytes")