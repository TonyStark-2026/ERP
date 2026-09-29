from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import Optional, Any
import datetime
import os

from . import models, schemas, crud
from .database import SessionLocal, engine, Base

Base.metadata.create_all(bind=engine)


# =============== 数据库字段迁移（SQLite ALTER TABLE）===============
def _migrate_schema():
    """为已存在的表补充新字段（SQLite 不支持自动 ALTER，需手动迁移）"""
    import sqlite3
    from .database import DATABASE_URL
    # 解析 SQLite 文件路径
    db_path = DATABASE_URL.replace("sqlite:///", "")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # 需要补充的列：(表名, 列名, 列定义)
        new_columns = [
            ("purchase_orders", "project_id", "INTEGER REFERENCES wbs_projects(id)"),
            ("purchase_orders", "bom_line_ref", "VARCHAR(100)"),
            ("contracts", "project_id", "INTEGER REFERENCES wbs_projects(id)"),
            ("contracts", "milestone_payments", "TEXT"),
            ("contracts", "contract_amount", "DECIMAL(18,2)"),
            ("suppliers", "rating_score", "DECIMAL(5,2)"),
            ("suppliers", "is_overseas", "BOOLEAN DEFAULT 0"),
            ("customers", "is_overseas", "BOOLEAN DEFAULT 0"),
            ("wbs_projects", "customer_name", "VARCHAR(100)"),
            ("wbs_projects", "currency", "VARCHAR(10) DEFAULT 'CNY'"),
            ("wbs_projects", "delivery_mode", "VARCHAR(20) DEFAULT 'MTO'"),
            ("wbs_projects", "business_mode", "VARCHAR(10) DEFAULT 'B'"),
            ("warehouses", "warehouse_type", "VARCHAR(30) DEFAULT 'RAW'"),
            # WBSNode 扩展字段
            ("wbs_nodes", "node_type", "VARCHAR(20) DEFAULT 'TASK'"),
            ("wbs_nodes", "budget_labor", "DECIMAL(18,2) DEFAULT 0"),
            ("wbs_nodes", "budget_material", "DECIMAL(18,2) DEFAULT 0"),
            ("wbs_nodes", "budget_outsource", "DECIMAL(18,2) DEFAULT 0"),
            ("wbs_nodes", "budget_other", "DECIMAL(18,2) DEFAULT 0"),
            ("wbs_nodes", "plan_start", "DATE"),
            ("wbs_nodes", "plan_end", "DATE"),
            ("wbs_nodes", "actual_start", "DATE"),
            ("wbs_nodes", "actual_end", "DATE"),
            ("wbs_nodes", "progress", "DECIMAL(5,2) DEFAULT 0"),
            # BOM 扩展字段
            ("boms", "bom_code", "VARCHAR(50)"),
            ("boms", "name", "VARCHAR(200)"),
            ("boms", "bom_type", "VARCHAR(10) DEFAULT 'EBOM'"),
            # BOMItem 扩展字段
            ("bom_items", "parent_item_id", "INTEGER REFERENCES bom_items(id)"),
            ("bom_items", "material_code", "VARCHAR(50)"),
            ("bom_items", "material_name", "VARCHAR(200)"),
            ("bom_items", "spec", "VARCHAR(200)"),
            ("bom_items", "loss_rate", "DECIMAL(5,2) DEFAULT 0"),
            ("bom_items", "item_type", "VARCHAR(20) DEFAULT 'PURCHASE'"),
            ("bom_items", "process_name", "VARCHAR(100)"),
            ("bom_items", "material_grade", "VARCHAR(100)"),
            ("bom_items", "surface_treatment", "VARCHAR(100)"),
            ("bom_items", "bom_level", "INTEGER DEFAULT 1"),
            ("bom_items", "remark", "VARCHAR(200)"),
            # Equipment 扩展字段
            ("equipments", "work_center", "VARCHAR(50)"),
            ("equipments", "commission_date", "DATE"),
            # Material 扩展字段：领料模式
            ("materials", "picking_mode", "INTEGER DEFAULT 1"),
            # ERP上线基础数据字段
            ("customers", "payment_terms", "VARCHAR(100)"),
            ("customers", "settlement_method", "VARCHAR(50)"),
            ("suppliers", "lead_time_days", "INTEGER"),
            ("suppliers", "payment_terms", "VARCHAR(100)"),
            ("warehouses", "stocktake_cycle", "VARCHAR(20)"),
            ("warehouses", "location_rule", "VARCHAR(100)"),
        ]
        for table, col, definition in new_columns:
            try:
                cursor.execute(f"PRAGMA table_info({table})")
                existing_cols = [row[1] for row in cursor.fetchall()]
                if col not in existing_cols:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")
                    print(f"[migrate] {table}.{col} 已添加")
            except Exception as e:
                print(f"[migrate] {table}.{col} 跳过（{e}）")

        # 总账管理新表（SQLite CREATE TABLE IF NOT EXISTS）
        new_tables = [
            """CREATE TABLE IF NOT EXISTS gl_ledgers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER DEFAULT 1,
                name VARCHAR(200) NOT NULL,
                code VARCHAR(50) UNIQUE NOT NULL,
                fiscal_year INTEGER DEFAULT 1,
                currency VARCHAR(10) DEFAULT 'CNY',
                accounting_std VARCHAR(50) DEFAULT '企业会计准则',
                status VARCHAR(20) DEFAULT 'ACTIVE',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS gl_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ledger_id INTEGER NOT NULL REFERENCES gl_ledgers(id),
                code VARCHAR(20) NOT NULL,
                name VARCHAR(200) NOT NULL,
                parent_id INTEGER REFERENCES gl_accounts(id),
                level INTEGER DEFAULT 1,
                category VARCHAR(20) NOT NULL,
                direction VARCHAR(10) DEFAULT '借',
                is_leaf BOOLEAN DEFAULT 1,
                aux_required TEXT DEFAULT '[]',
                status VARCHAR(20) DEFAULT 'ACTIVE',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS gl_aux_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ledger_id INTEGER NOT NULL REFERENCES gl_ledgers(id),
                code VARCHAR(50) NOT NULL,
                name VARCHAR(100) NOT NULL,
                source_type VARCHAR(20) DEFAULT '内置',
                source_table VARCHAR(100),
                status VARCHAR(20) DEFAULT 'ACTIVE',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS gl_aux_values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aux_type_id INTEGER NOT NULL REFERENCES gl_aux_types(id),
                code VARCHAR(50) NOT NULL,
                name VARCHAR(200) NOT NULL,
                parent_id INTEGER REFERENCES gl_aux_values(id),
                status VARCHAR(20) DEFAULT 'ACTIVE',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS gl_vouchers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ledger_id INTEGER NOT NULL REFERENCES gl_ledgers(id),
                voucher_no VARCHAR(50) NOT NULL,
                voucher_date DATE NOT NULL,
                period_id INTEGER NOT NULL REFERENCES gl_periods(id),
                voucher_type VARCHAR(30) DEFAULT '记账凭证',
                source_type VARCHAR(30) DEFAULT '手工',
                source_id INTEGER,
                summary VARCHAR(200),
                status VARCHAR(20) DEFAULT '草稿',
                created_by VARCHAR(50),
                audited_by VARCHAR(50),
                posted_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS gl_voucher_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                voucher_id INTEGER NOT NULL REFERENCES gl_vouchers(id),
                line_no INTEGER NOT NULL,
                account_id INTEGER NOT NULL REFERENCES gl_accounts(id),
                summary VARCHAR(200),
                debit_amount DECIMAL(18,2) DEFAULT 0,
                credit_amount DECIMAL(18,2) DEFAULT 0,
                currency VARCHAR(10) DEFAULT 'CNY',
                exchange_rate DECIMAL(10,4) DEFAULT 1,
                original_amount DECIMAL(18,2) DEFAULT 0,
                aux_values TEXT DEFAULT '{}'
            )""",
            """CREATE TABLE IF NOT EXISTS gl_periods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ledger_id INTEGER NOT NULL REFERENCES gl_ledgers(id),
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                status VARCHAR(20) DEFAULT '未结账',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS gl_balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ledger_id INTEGER NOT NULL REFERENCES gl_ledgers(id),
                period_id INTEGER NOT NULL REFERENCES gl_periods(id),
                account_id INTEGER NOT NULL REFERENCES gl_accounts(id),
                aux_values TEXT DEFAULT '{}',
                begin_debit DECIMAL(18,2) DEFAULT 0,
                begin_credit DECIMAL(18,2) DEFAULT 0,
                period_debit DECIMAL(18,2) DEFAULT 0,
                period_credit DECIMAL(18,2) DEFAULT 0,
                end_debit DECIMAL(18,2) DEFAULT 0,
                end_credit DECIMAL(18,2) DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
        ]
        for sql in new_tables:
            try:
                cursor.execute(sql)
                print(f"[migrate] 总账表创建成功")
            except Exception as e:
                print(f"[migrate] 总账表跳过（{e}）")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[migrate] 迁移跳过：{e}")

_migrate_schema()


# =============== 物料分类编码规则种子数据 ===============
# 《物料编码分类细则2022》Sheet「物料编码」标准数据：一级(1位)+二级(2位)+三级(2位)+流水号(3位)=8位编码
# 结构：(一级代号, 一级名称, [(二级代号, 二级名称, [(三级代号, 物料名称, 分类定义/规格参考), ...]), ...])
_MATERIAL_CODE_STANDARD = [
    ("0", "原材料", [
        ("01", "金属类", [
            ("01", "板材", "A3、45#、SUS201、SUS304、SUS316、SUS316L、钛"),
            ("02", "型材", "方通、扁通、角钢 、槽钢、铝型材……"),
            ("03", "其它", ""),
        ]),
        ("02", "非金属类", [
            ("01", "板材", "PP、PVC、PVDF、PTFE"),
            ("02", "型材", "棒"),
            ("03", "其它", ""),
        ]),
    ]),
    ("1", "电气类标准件", [
        ("01", "控制系统", [
            ("01", "人机界面（HMI）", "触摸屏、工控机、显示器等附件"),
            ("02", "PLC/PAC系统", "PLC、CPU控制器/卡、输入输出卡、通讯模块、扩展接口模块、电源模块、定位模块、计数模块、背板、附件"),
            ("03", "工业软件", "编程软件、Mes、上位机软件、下位机软件、视觉软件、数据库软件"),
            ("04", "伺服驱动系统", "伺服驱动器（单体）、电源模块、滤波器、电抗器、逆变单元、功能卡件、端子及连接器附件、通讯电缆、动力电缆、伺服驱动器（单体）、底板、制动电阻、电容箱、整体采购部套"),
            ("05", "变频器及附件", "变频器主体、通讯卡、面板、功能卡"),
            ("06", "调速器及附件", "调速器主体、通讯卡、面板、功能卡"),
        ]),
        ("02", "传感器&仪表", [
            ("01", "温湿度传感器", "热电阻、热电偶、激光测温、红外测温、热敏开关、湿度传感器及附件。"),
            ("02", "光电传感器", "光电开关、激光传感器、光纤传感器、色标传感器、轮廓扫描仪、"),
            ("03", "接近传感器", "接近开关、行程开关（限位开关）、微动开关、对刀仪及附件"),
            ("04", "液位传感器", "光电式液位、电容式液位、磁致伸缩液位、超声波液位、磁翻板液位、浮球开关、浮球式液位传感器、音叉及附件"),
            ("05", "流量传感器", "超声波流量计、电磁流量计、涡轮流量计、涡街流量计、塑管流量计、质量流量计及附件"),
            ("06", "力学传感器", "称重传感器、压力传感器、力传感器（单/多维传感器）、张力传感器及附件"),
            ("07", "速度传感器", "增量编码器、绝对值编码器、旋转变压器，码盘、加速度传感器及附件、电子手轮"),
            ("08", "位移传感器", "磁栅尺、光栅尺、激光测距、超声波、磁致伸缩、拉绳式、电阻式、电涡流传感器、LVDT、角位移传感器等及附件。"),
            ("09", "安全类传感器", "安全光幕、安全门锁、安全扫描仪、安全地毯、拉绳开关及附件 可扩展区域光栅"),
            ("10", "气液分析类传感器", "PH传感器、电导率仪、粘度计、溶氧分析、气体含量传感器及附件"),
            ("11", "噪声及振动传感器", "声学传感器、工业麦克风，加速度传感器、振动传感器等"),
            ("12", "仪表", "控制仪表、显示仪表、变送器、互感器、功能卡件等附件"),
            ("13", "视觉系统", "工业相机、镜头、光源、视觉控制器、视觉专用电缆、视觉采集卡及附件"),
            ("14", "扫码系统", "条码读取器类：条形码读取器、二位码读取器、CCD条码读取器、附件等。"),
            ("15", "RFID", "读写头、RFID电子标签"),
            ("16", "静电消除系统", "棒型、风扇型、定点型等各类静电消除系统、附件等。"),
            ("17", "传感器&仪表其他", ""),
        ]),
        ("03", "低压电器&辅材", [
            ("01", "配电类器件", "断路器、马达开关、接触器、电源、继电器、指示灯、急停、旋钮、按钮、脚踏开关、照明灯、报警灯、电子门锁、指纹锁、变压器、"),
            ("02", "通讯类器件", "路由器、交换机、UPS、网卡及配件"),
            ("03", "微电子类器件", "电位器、电阻、电容、光电偶合器、晶振、运算放大器、单片机、芯片等电子类器件"),
            ("04", "线缆", "动力电缆、信号电缆、通讯电缆"),
            ("05", "电器辅材", "按钮盒、接线端子、线槽、卡轨、冷压端子、扎带、波纹管、插头、插排、铜鼻子、水晶头、桥架、铜排、热缩管、绝缘胶带、缠绕管、保险丝（熔断芯）、色带、线号管、导电滑环"),
            ("06", "配电柜及辅材", "电箱、柜式空调、轴流风机及配件、"),
            ("07", "其他", ""),
        ]),
    ]),
    ("2", "机械类标准件", [
        ("01", "电机", [
            ("01", "伺服电机", "交流异步伺服电机、交流同步伺服电机、力矩伺服电机"),
            ("02", "步进电机", "两相步进电机、五相步进电机"),
            ("03", "减速电机", "单相交流电机、三相交流电机"),
            ("04", "变频电机", "交流变频电机、矢量变频电机"),
            ("05", "防爆电机", "防爆普通电机、防爆伺服电机"),
            ("06", "其它", "DD马达、直线电机、音圈电机、振动电机"),
        ]),
        ("02", "减速机", [
            ("01", "行星齿轮减速机", "普通行星齿轮减速机、精密行星齿轮减速机、摆线针轮减速机"),
            ("02", "齿轮减速机", "直齿、斜齿、（准）双曲面斜齿、中空旋转平台"),
            ("03", "蜗轮蜗杆减速机", ""),
            ("04", "谐波减速机", ""),
            ("05", "转向器", "直角、"),
            ("06", "变速器", "无级变速器、有级变速器"),
            ("07", "其它", "RV减速机"),
        ]),
        ("03", "轴承", [
            ("01", "滚动轴承", "深沟球轴承、角接触轴承、推力轴承、调心轴承、转台轴承、圆锥轴承、圆柱轴承、滚针轴承、密珠套筒、带座轴承、轴承座及辅件、、螺栓式轴承（凸轮轴承随动器）、包胶轴承"),
            ("02", "滑动轴承", "径向滑动轴承、轴向滑动轴承、关节轴承"),
            ("03", "非接触轴承", "静压轴承、动压轴承、空气轴承、磁悬浮轴承"),
        ]),
        ("04", "丝杠&导轨", [
            ("01", "丝杠类", "梯形丝杠、滚珠丝杠、丝杠支撑座"),
            ("02", "导轨类", "直线导轨、RBS圆导轨、（IGUS）滑动导轨和滑块、导向轴/光轴、滚珠导轨、滚柱导轨、滚动花键、弧形导轨、双轴心导轨、滚轮式（弧形）导轨及配套滚轮、导轨压块"),
            ("03", "电缸类", "模组、电缸、滑台、排线器"),
            ("04", "其它", ""),
        ]),
        ("05", "传动联接", [
            ("01", "联轴器", "梅花、膜片、十字万向、链条联轴器、波纹管、轮胎联轴器"),
            ("02", "皮传动", "同步带（圆弧同步齿形）、模组带、输送带、V带、联组V带、多楔带、"),
            ("03", "带轮", "同步带轮、平带轮、同步惰轮（同步带轮背面张紧）、圆皮带用惰轮、带轮锥套、V带轮、"),
            ("04", "链轮", "滚子链链轮、板链链轮、倍速链链轮、链条支撑用（小型）惰轮、惰轮链轮"),
            ("05", "链条", "滚子链、输送链"),
            ("06", "齿轮", "直齿轮、斜齿轮、伞齿轮、人字齿轮、蜗轮、蜗杆"),
            ("07", "齿条", "直齿齿条、斜齿齿条"),
            ("08", "制动器", "电磁制动器、盘式制动器、鼓式制动器、磁粉制动器、导轨钳制器"),
            ("09", "离合器", "电磁离合器、磁粉离合器"),
            ("10", "减震器", "橡胶减震器、弹簧减震器、油压减震器/缓冲器、空气弹簧/缓冲器、阻挡器"),
            ("11", "传动联接其他", "胀紧套、扭力限制器"),
        ]),
        ("06", "气动系统", [
            ("01", "气源处理类", "三联件、过滤减压阀、空气过滤器、油雾分离器"),
            ("02", "气动执行元件类", "气缸、气动马达、气液转换器、增压缸、风刀、夹紧缸、气动旋转接头、货盘阻挡器、磁力吸盘"),
            ("03", "气动控制阀类", "气动电磁阀、气动/手动阀、气动比例阀、阀岛、筏板、精密（普通）减压阀/调压阀、单向阀、节流阀、调速阀、气动夹管阀、（气控）压力阀"),
            ("04", "真空元件类", "真空发生器、真空吸盘、真空过滤器、真空逻辑阀"),
            ("05", "气动附件类", "接头、气管、浮动接头、磁开、气枪、压力开关、气动（真空）压力表、消音器、气用喷嘴、FESTO/SMC/CKD/AirTAC压力（流量）传感器、真空用附件（管、接头等）、空气过滤器滤芯"),
            ("06", "气源装置及辅助元件", "空压机、储气罐、冷干机、管道过滤器"),
        ]),
        ("07", "液压水路系统", [
            ("01", "泵类", "磁力泵、气动隔膜泵、计量泵、（单）多级离心泵、管道泵、蠕动泵、齿轮泵、叶片泵、柱塞泵、、砂浆泵、手动液压泵"),
            ("02", "阀类", "(手动/气动)隔膜阀、球阀、蝶阀、针阀、单向阀、节流阀、溢流阀、换向阀、伺服阀、马达阀、液压锁、液用旋转接头"),
            ("03", "液压、水路附件类", "管接头、胶管、快换接头、水枪、干燥器、蓄能器、管堵、丝堵、无缝钢管、 PPR（及其他材料/复合材料）管及接头、弯头、三通、变径直通、管卡 液用喷嘴、液用压力表、有机玻璃液位计、管夹"),
            ("04", "过滤器系统", "前置过滤器、Y型过滤器、过滤桶、滤袋过滤器、滤网过滤器、纸袋过滤器、RO渗透膜、压滤机及配件、滤芯、滤袋、油滤、磁粉分离机、（不锈钢）滤网、滤纸"),
            ("05", "换热器", "板式换热器、管壳式换热器、钎焊换热器"),
            ("06", "水冷机", "水冷式水冷机、风冷式水冷机、蒸发冷却式水冷机"),
            ("07", "液路系统", "液路系统委外、液位报警装置委外、称重模块委外、管路系统委外、喷淋管组件委外、液路改造费"),
            ("08", "液压组件类", "液压站、液压缸、液压管路、伺服阀清洗板、水压爆破系统"),
        ]),
        ("08", "新风&排风系统", [
            ("01", "风机", "FFU单元、离心风机 、中压风机、高压鼓风机、罗茨风机、管道轴流风机"),
            ("02", "风阀、管件", "风阀、弯头、三通、法兰、软连接"),
            ("03", "过滤类", "初效过滤器、中效过滤器、高效过滤器、化学过滤器、"),
            ("04", "辅件", ""),
        ]),
        ("09", "设备附件", [
            ("01", "加热类", "在线加热器、加热管 、加热带、加热毯、"),
            ("02", "超声波&兆声波", "超声波发生器、震头"),
            ("03", "电镀、电解类", "电极 、钛篮、钛钣金、钛管、整流机"),
            ("04", "安全防护类", "标准围栏、风琴护罩、弹性皮腔、刮削板、盔甲护罩"),
            ("05", "拖链类", "塑料拖链、钢制拖链"),
            ("06", "操作箱", "悬臂箱、操作台、按钮盒、接线盒"),
            ("07", "标牌类", "钢制标牌、铝制标牌、PVC标牌、不干胶标牌、丝网印刷"),
            ("08", "卷帘门类", "卷帘门"),
            ("09", "设备附件其他", "附图外购"),
        ]),
        ("10", "工业五金配件", [
            ("01", "外观件", "如门锁，铰链，扣手，把手，脚轮、地脚、支脚、门吸、挂钩"),
            ("02", "铝型材及附件", "铝型材、角件、方螺母、T-lock、端盖"),
            ("03", "定位元件", "支柱、底座、支柱固定夹、导向轴固定座"),
            ("04", "调整元件", "柱塞、调整限位件、缓冲减震零件、调整垫铁"),
            ("05", "紧固件", "螺钉、螺栓、螺母、圆螺母、垫圈、垫片、销、键、铆钉、精密锁紧螺母"),
            ("06", "密封件", "O型圈、密封条、油封、唇形密封圈、VD密封圈、机械密封"),
            ("07", "粘胶剂", "密封胶、AB胶、502、发泡胶、厌氧胶、磁材胶"),
            ("08", "功能元件", "磁铁、防滑贴、弹簧（扭簧）、模具弹簧、碟簧、板簧、弹簧平衡器、气门嘴、遥控器、滚轮、钢球、油杯、"),
        ]),
        ("11", "润滑系统&油品", [
            ("01", "油脂润滑", "油脂润滑泵、分配器及附属管接头和管件"),
            ("02", "油气润滑", "油气混合阀、油气润滑泵、附属管接头和管件"),
            ("03", "油脂类", "润滑油、润滑脂、液压油"),
            ("04", "防锈类", "防锈漆、防锈油、防锈蜡、除锈剂"),
        ]),
        ("12", "自动化产线", [
            ("01", "工业机器人", "六轴机器人、蜘蛛机器人 、桁架机器人 、铰接机器人"),
            ("02", "AGV&RGV", "AGV&RGV"),
            ("12", "上下料机械装置", "硅棒上下料小车、主辊小车、助力机械手、手动堆高车、半电动堆高车、液压手动平台车、上胎小车"),
            ("04", "输送线", "倍速链、板链线、滚筒、滚筒输送线、升降移栽机、连续升降移栽机、万向球"),
            ("05", "升降机", "丝杆升降机、滚珠丝杠升降机、十字换向器、多轴输出减速箱、举升机、液压升降机（平台）"),
            ("06", "皮带机", "皮带输送线"),
            ("07", "清洁设备", "超声波清洗机、激光清洗机、工业除尘机、油雾收集器、除尘系统委外"),
            ("08", "加热装置", "烘干箱、微波、电磁、"),
            ("09", "打标机", "激光、气动、电腐蚀、电磁、划刻"),
            ("10", "立库", ""),
            ("16", "自动化产线其他", "磁材分类器、自动化产线调试费、自动化产线安装费、拆胎机"),
        ]),
    ]),
    ("3", "辅料工具类&生产&服务", [
        ("01", "包装材料（MRO）", [
            ("01", "木制品", "木箱、木托盘、木垫块、枕木"),
            ("02", "纸制品", "纸箱、纸袋、纸品、纸托盘"),
            ("03", "防锈袋", "抽真空袋、普通防锈袋、镀铝膜"),
            ("04", "发泡制品", "EPE、泡沫盒"),
            ("05", "包装辅材", "气柱袋、气泡膜、胶带、打包带、塑料托盘、缠绕膜、防震棉、（矿物）干燥剂"),
        ]),
        ("02", "工、量、夹具（MRO）", [
            ("01", "工具", "壁纸刀、镊子、手锤、手钳、管钳、剪刀、活扳手、内六角扳手、叉扳手、套筒扳手、棘轮扳手、扭矩扳手、链条扳手、卡钳、尖嘴钳、螺丝刀、锉刀、刮刀、样冲、断丝取出器、电笔、平尺、工具箱、工具包（袋）、角磨机、手电钻、手锯、拉铆枪、热烘枪、手动（自动）打包机、放大镜、金刚笔、焊枪、氧气瓶、氮气瓶、氩气瓶、干冰、液氮、手动（气动）黄油枪、千斤顶、液压螺母、电容笔、手电筒、矿灯"),
            ("02", "量具", "游标卡尺、外径千分尺、内径百分表、卷尺、钢板尺、角度尺、扭簧表、百分表、千分表、杠杆千分表、磁力表座、条式水平仪、数显水平仪、框式水平仪、合像水平仪、量块、V型块、手持式噪声仪、手持式测振仪、手持式测力计、手持式温湿度仪、红外测温枪、万用表、通规、止规、螺纹规、弹簧秤、台秤、推拉力计、砝码、天平"),
            ("03", "刀具", "钻头、丝攻、铰刀、板牙、开孔器、砂纸、砂带、抛光轮、切割片、打磨片、带锯、砂轮、金刚线、环形丝、钼丝、金刚笔"),
            ("04", "夹具", "台钳、卡盘、中心架、三导轮紧丝器、气动夹钳"),
        ]),
        ("03", "化工原料（MRO）", [
            ("01", "计量器皿", "量杯、量筒、量瓶、烧杯、烧瓶、试管、试管夹、移液器、搅拌棒、坩埚、酒精灯、注射器、滴定管、滚镀瓶、实验室用真空泵、玻璃温度计等玻璃器皿、镀覆用喷壶、硅胶铲"),
            ("02", "过滤材料", "（不锈钢）筛网及配件、布套（滤布）、（椰壳）活性炭、硅藻土、砂滤滤料石英砂"),
            ("03", "化工材料", "切削液、切削油、防冻液、氯化钾、氢氧化钠、氯化铵、硝酸钾等无机试剂；滴定用/元素分析用/pH电极用标准溶液；乙炔/氮气等气体；聚合氯化铝/聚丙烯酰胺等水处理药剂；酸、碱、醇、醛、酯、胺等有机试剂；复配添加剂、镀覆用阴阳极、阳极袋、导电夹、阳极模块等配件；镍类化学品；滴定溶液、分析纯、其他试剂"),
            ("04", "镍类", "金属镍、其他表面镀层金属（金、银、钴、钛、铬等）"),
        ]),
        ("04", "生产运营相关物料（MRO）", [
            ("01", "原材料", "硅棒、大理石板、玻璃板、（废）轮胎、石棒、蓝宝石棒、磁材、水晶、金刚线、树脂板、硅片、碳化硅棒、氮化硅块"),
            ("02", "吊具", "吊带、钢丝绳、滑轮、吊扣、高空作业安全带、钢丝绳卡扣"),
            ("03", "设备配件", "各种生产设备使用配件"),
            ("04", "低值资产", "小打印机、工作桌、呼吸器、报警仪、风扇、小冰箱、小冷藏柜、台灯、小空调、小电视（显示屏）、电话、电暖器、风幕、消防用品"),
        ]),
        ("05", "消耗品（MRO）", [
            ("01", "生产辅料", "保鲜袋、贴纸、标签、棉线、纱布、抹布、高温布、打火机、开孔器、公文包、焊条、焊丝、焊锡膏、生料带、防松标记油漆笔、清洗剂、喷壶、（不锈钢）丝网、铝合金条刷、防火泥、油石、毛刷、紫铜棒、紫铜皮、铜板打印纸、洗手粉、青稞纸、湿度卡、PH试纸、PH试剂、移液枪枪头、洗眼器、吸音棉、塑料盆、硅片盒、玻璃钢格栅板、汽油、煤油、MBR配套膜片、（风机）过滤棉"),
            ("02", "仓储物流用品", "隔板式货架、周转箱、移动平台梯、推车、周转车、压力车、网格托盘、不锈钢托盘"),
            ("03", "劳保用品", "丁腈手套、耐高温手套、耐酸碱手套、一次性橡胶手套、礼仪手套、工作服、工作鞋、护目镜、防护服、口罩、防毒面具、耳塞、面罩、围巾、套袖"),
        ]),
        ("06", "服务类", [
            ("02", "人工", "安装委外、刮研、环形丝编制、开槽、润滑系统安装费、线束制作费、维修费、（外购件）补加工费、CE认证费、UL认证费、体系认证费、技术培训费"),
        ]),
    ]),
    ("4", "固定资产专家", [
        ("01", "固定资产投资及化学仪器", [
            ("01", "IT类硬件资产", "电脑主机、显示器、打印机、投影仪、电视、服务器"),
            ("02", "IT类无形资产", "操作系统、ERP系统、管理软件、工具软件等使用权"),
            ("03", "量具检验工具类资产", "检测平台、张力仪、测高仪、三坐标、圆度仪、偏摆仪、经纬仪、水准仪、激光准直仪、激光干涉仪、对中仪、示波器、热成像仪、光学显微镜、扫描电镜、原子力显微镜、频谱仪、表面粗糙度仪"),
            ("04", "生产设备类资产", "装配工作平台、线体、桁车、悬臂吊、高层货架、叉车、升降车、小车、电锯、砂轮机、切管机、弯管机、圆盘锯、攻丝机、钻床、车床、磨床、铣床、加工中心、雕铣机、动平衡机、电火花、焊机、轴承加热器、变电站、发电机、温控系统、新风系统、保温房、污水处理系统、车间配电系统、车间用储气罐及空压机、金刚线生产设备、硅片分选设备、硅片清洗设备"),
            ("05", "行政办公类资产", "空调、大型净水饮水机、厨房设备、路灯（含风光互补）、太阳能热水器、太阳能发电屋顶、车辆识别系统"),
            ("06", "行政运输工具类资产", "办公用车（轿车、SUV、皮卡车、货车等）、班车"),
            ("07", "工装模具类资产", "注塑、吹塑、挤出、压铸、锻压和铸造等过程中所需要的工装夹具或模具"),
            ("08", "研发工艺类资产", "研发测试使用的专用设备"),
            ("09", "化学仪器", "紫外、红外、元素分析仪、废水在线分析仪、pH计、电导率仪、消解仪、COD及Ni分析仪、光谱仪，粘度计，以上设备的辅材及耗材"),
        ]),
    ]),
    ("5", "半成品（零、部件）", [
        ("01", "机械加工类", [
            ("02", "车床件", "车床件、圆钢、铝棒、含车床件的委外组件"),
            ("03", "铣床件", "铣床件、钢板、铝板、含洗床件的委外组件"),
            ("04", "高精密件", "精密主轴、主轴轴套、主辊轴、轴承箱精密法兰及隔圈、精密磨床件、含高精密件的委外组件（除轴箱类）"),
            ("05", "涂覆导轮及切割辊", "涂覆件、涂覆导轮、切割轮及切割轮组件、主辊"),
            ("06", "其他组件部套类", "主要指小部套类、小导轮组件"),
        ]),
        ("02", "焊接&加工类", [
            ("01", "焊接底座类", "焊接底座类"),
            ("02", "焊接架体类", "焊接架体类"),
            ("03", "小型焊接件", "小型焊接件、方管、角钢、槽钢、含小型焊接件的委外组件"),
        ]),
        ("03", "钣金类", [
            ("01", "小钣金", "小钣金、铝钣金件、铝管焊接"),
            ("02", "防护罩", "防护罩、轮胎检测设备类围栏护罩"),
            ("03", "箱体类", "箱体、缸体、柜体、含箱体类件的委外组件"),
        ]),
        ("04", "铸件&加工类", [
            ("01", "灰铸铁", "灰铸铁、含灰铁件的委外组件"),
            ("02", "球墨铸铁", "球墨铸铁、含球磨铸铁件的委外组件"),
            ("03", "铸钢", "铸钢、含铸钢件的委外组件"),
            ("04", "304精铸", "304精铸、含304精铸件的委外组件"),
            ("05", "铸铝", "铸铝、含铸铝件的委外组件"),
            ("06", "铸铜", "铸铜、含铸铜件的委外组件"),
        ]),
        ("05", "零件类", [
            ("01", "金属加工类", "碳钢、不锈钢、铜"),
            ("02", "非金属加工类", "橡胶、尼龙、聚氨酯、聚四氟乙烯类橡塑材料产品、非金属焊接件、含非金属（焊接）加工件的委外组件"),
            ("03", "购件改制加工", "外购标准件二次加工"),
        ]),
        ("06", "部件类", [
            ("01", "部件类", "部装品"),
        ]),
    ]),
    ("6", "成品", [
        ("01", "光伏行业", [
            ("01", "硅料、硅片", ""),
            ("02", "电池", ""),
        ]),
        ("02", "半导体行业", [
            ("01", "Wafer", ""),
            ("02", "IC", ""),
        ]),
        ("03", "面板行业", [
            ("01", "面板行业", ""),
        ]),
        ("04", "传统行业", [
            ("01", "传统行业", ""),
        ]),
        ("05", "其它行业", [
            ("01", "其它行业", ""),
        ]),
    ]),
]

def _seed_material_categories():
    """按《物料编码分类细则2022》对齐分类数据（幂等：缺失则补录，已有则校正为标准）"""
    db = SessionLocal()
    created = [0, 0, 0]
    updated = [0, 0, 0]
    try:
        # 体系版本检测：存在旧版8类体系（机械工程材料类等）则整体清空，切换为新版分类
        old_names = {c.name for c in db.query(models.MaterialCategory).filter(models.MaterialCategory.level == 1).all()}
        if old_names and not ({"电气类标准件", "机械类标准件"} <= old_names):
            db.query(models.MaterialCategory).delete()
            db.commit()
            print("[seed] 检测到旧版物料分类体系，已清空并切换为《物料编码分类细则2022》新版体系")
        l1_all = {c.name: c for c in db.query(models.MaterialCategory).filter(models.MaterialCategory.level == 1).all()}
        for sort1, (code1, name1, subs) in enumerate(_MATERIAL_CODE_STANDARD, 1):
            l1 = l1_all.get(name1)
            if not l1:
                l1 = models.MaterialCategory(level=1, name=name1, code=code1, full_code=code1,
                                             sort_order=sort1, current_sequence=0)
                db.add(l1); db.flush(); created[0] += 1
            elif l1.code != code1 or l1.full_code != code1:
                l1.code, l1.full_code = code1, code1; updated[0] += 1

            l2_all = {c.code: c for c in db.query(models.MaterialCategory).filter(
                models.MaterialCategory.level == 2, models.MaterialCategory.parent_id == l1.id).all()}
            for sort2, (code2, name2, mats) in enumerate(subs, 1):
                l2 = l2_all.get(code2)
                full2 = f"{code1}.{code2}"
                if not l2:
                    l2 = models.MaterialCategory(level=2, name=name2, code=code2, full_code=full2,
                                                 parent_id=l1.id, sort_order=sort2, current_sequence=0)
                    db.add(l2); db.flush(); created[1] += 1
                elif l2.name != name2 or l2.full_code != full2:
                    l2.name, l2.full_code = name2, full2; updated[1] += 1

                l3_all = db.query(models.MaterialCategory).filter(
                    models.MaterialCategory.level == 3, models.MaterialCategory.parent_id == l2.id).all()
                for sort3, (code3, mat_name, spec) in enumerate(mats, 1):
                    full3 = f"{code1}.{code2}.{code3}"
                    # 优先按物料名称匹配，再按三级代号匹配
                    l3 = next((c for c in l3_all if (c.material_name or c.name) == mat_name), None) \
                        or next((c for c in l3_all if c.code == code3), None)
                    if not l3:
                        l3 = models.MaterialCategory(level=3, name=mat_name, code=code3, full_code=full3,
                                                     parent_id=l2.id, material_name=mat_name, spec_standard=spec,
                                                     sort_order=sort3, current_sequence=0)
                        db.add(l3); db.flush(); created[2] += 1
                    else:
                        new_vals = {"name": mat_name, "material_name": mat_name, "code": code3,
                                    "full_code": full3, "spec_standard": spec}
                        if any(getattr(l3, k) != v for k, v in new_vals.items()):
                            for k, v in new_vals.items():
                                setattr(l3, k, v)
                            updated[2] += 1

        db.commit()
        total = db.query(models.MaterialCategory).count()
        print(f"[seed] 物料编码规则已对齐：新增 L1={created[0]} L2={created[1]} L3={created[2]}，"
              f"校正 L1={updated[0]} L2={updated[1]} L3={updated[2]}，共{total}条分类")
    except Exception as e:
        db.rollback()
        print(f"[seed] 物料分类对齐失败：{e}")
    finally:
        db.close()

_seed_material_categories()


# =============== 默认管理员账号初始化 ===============
# 确保系统启动时存在 admin / admin123 超级管理员账号
def _ensure_default_admin():
    import hashlib
    db = SessionLocal()
    try:
        admin_user = db.query(models.User).filter(models.User.username == "admin").first()
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        if not admin_user:
            admin_user = models.User(
                username="admin",
                password=admin_hash,
                email="admin@erp.local",
                phone="",
                role="super_admin"
            )
            db.add(admin_user)
            db.commit()
            print("[init] 默认管理员账号 admin/admin123 已创建")
        else:
            # 确保角色和密码正确（符合需求：默认账号 admin/admin123）
            changed = False
            if admin_user.role != "super_admin":
                admin_user.role = "super_admin"
                changed = True
            if admin_user.password != admin_hash:
                admin_user.password = admin_hash
                changed = True
            if changed:
                db.commit()
                print("[init] 管理员账号 admin 已更新为 super_admin / admin123")
    finally:
        db.close()

_ensure_default_admin()


# =============== 工程行业会计科目预置 ===============
def _seed_engineering_accounts():
    """启动时预置工程行业常用会计科目"""
    try:
        from .api.auto_voucher import seed_engineering_accounts
        db = SessionLocal()
        try:
            result = seed_engineering_accounts(db, account_set_id=1)
            if result.get("created", 0) > 0:
                print(f"[init] 工程行业会计科目预置完成：新增{result['created']}个科目")
        finally:
            db.close()
    except Exception as e:
        print(f"[init] 工程行业会计科目预置跳过（{e}）")

_seed_engineering_accounts()


# =============== 设备水电费自动计提（模拟数据→财务制造费用）===============
def _seed_utility_fees():
    """启动时自动计提本月设备每日水电费并生成财务凭证（幂等）"""
    try:
        from .api.factory_api import auto_accrue_utility_fees
        db = SessionLocal()
        try:
            recs, vouchers = auto_accrue_utility_fees(db)
            if recs:
                print(f"[init] 设备水电费自动计提：{recs}条明细 / {vouchers}张凭证")
        finally:
            db.close()
    except Exception as e:
        print(f"[init] 设备水电费计提跳过（{e}）")

_seed_utility_fees()


# =============== 企业级配置初始化（单例）===============
def _seed_enterprise_config():
    """启动时确保存在一条企业配置记录（id=1），不存在则创建默认值"""
    db = SessionLocal()
    try:
        config = db.query(models.EnterpriseConfig).filter(models.EnterpriseConfig.id == 1).first()
        if not config:
            config = models.EnterpriseConfig(
                id=1,
                industry_type="engineering",
                business_mode="B",
                revenue_method="percentage_of_completion",
                picking_modes='["by_order"]',
                sub_industry=None,
                capital_cost_rate=0.08
            )
            db.add(config)
            db.commit()
            print("[init] 企业级配置默认记录已创建（id=1, engineering/B）")
    finally:
        db.close()

_seed_enterprise_config()

app = FastAPI(title="ERP System API", version="1.0.0")

# 🔥 GZip 压缩中间件：减少 80%+ 传输体积（263KB → ~40KB），手机加载提速明显
app.add_middleware(GZipMiddleware, minimum_size=500)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件服务（支持 /frontend/* 以及根路径下的 /jsQR.min.js 等）
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.middleware("http")
async def api_response_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        # 统一为 JSON 响应声明 UTF-8，避免中文乱码
        ctype = response.headers.get("content-type", "")
        if ctype.startswith("application/json") and "charset" not in ctype.lower():
            response.headers["content-type"] = "application/json; charset=utf-8"
        return response
    except HTTPException as exc:
        return JSONResponse(
            status_code=exc.status_code,
            media_type="application/json; charset=utf-8",
            content={
                "success": False,
                "data": None,
                "message": exc.detail,
                "error_code": str(exc.status_code) + "01",
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            media_type="application/json; charset=utf-8",
            content={
                "success": False,
                "data": None,
                "message": str(exc),
                "error_code": "50001",
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        )

def make_response(success: bool, data: Any = None, message: str = "", error_code: Optional[str] = None):
    return {
        "success": success,
        "data": data,
        "message": message,
        "error_code": error_code,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

@app.get("/", tags=["首页"])
async def root():
    # HTML 入口不缓存，确保用户每次拿到最新页面（JS/CSS 用版本号控制缓存）
    return FileResponse("frontend/index.html", headers={"Cache-Control": "no-cache, must-revalidate"})

@app.get("/health", tags=["系统"])
async def health_check():
    return make_response(True, {"status": "healthy"}, "系统运行正常")

from .api import materials, purchase, production, inventory, compliance, crossborder, scanning, invoice_recognition, finance, auth, sales, bom, contracts, employees, config_center, plan, procurement, simulation, ai_copilot, auto_voucher_router, print_router, voucher_settings, report_center, purchase_module, base_settings, sales_module, production_module, inventory_v2, finance_v2, cost_accounting, analytics, production_docs, engineering, engineering_adaptation, engineering_modules, procurement_optimization, api_integration, factory_api, production_planning, notifications, gl_ledger

app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(config_center.router, prefix="/api/v1/config", tags=["系统配置"])
app.include_router(materials.router, prefix="/api/v1/materials", tags=["物料管理"])
app.include_router(purchase.router, prefix="/api/v1/purchase", tags=["采购管理"])
app.include_router(purchase_module.router, prefix="/api/v1/pm", tags=["采购管理V2"])
app.include_router(sales.router, prefix="/api/v1/sales", tags=["销售管理"])
app.include_router(production.router, prefix="/api/v1/production", tags=["生产管理"])
app.include_router(plan.router, prefix="/api/v1/plan", tags=["计划管理"])
app.include_router(procurement.router, prefix="/api/v1/procurement", tags=["采购管理"])
app.include_router(bom.router, prefix="/api/v1/bom", tags=["BOM管理"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["库存管理"])
app.include_router(compliance.router, prefix="/api/v1/compliance", tags=["合规预警"])
app.include_router(crossborder.router, prefix="/api/v1/crossborder", tags=["跨境合规"])
app.include_router(contracts.router, prefix="/api/v1/contracts", tags=["合同管理"])
app.include_router(employees.router, prefix="/api/v1/employees", tags=["员工管理"])
app.include_router(scanning.router, prefix="/api/v1/scanning", tags=["扫码录入"])
app.include_router(invoice_recognition.router, prefix="/api/v1/invoice", tags=["发票识别"])
app.include_router(finance.router, prefix="/api/v1/finance", tags=["财务管理"])
app.include_router(simulation.router, prefix="/api/v1/simulation", tags=["模拟教学"])
app.include_router(ai_copilot.router, prefix="/api/v1/ai", tags=["AI副驾"])
app.include_router(auto_voucher_router.router, prefix="/api/v1/vouchers", tags=["自动凭证"])
app.include_router(print_router.router, prefix="/api/v1/print", tags=["打印中心"])
app.include_router(voucher_settings.router, prefix="/api/v1/voucher-settings", tags=["凭证设置"])
app.include_router(report_center.router, prefix="/api/v1/reports", tags=["报表中心"])
app.include_router(base_settings.router, prefix="/api/v1/base", tags=["基础设置"])
app.include_router(sales_module.router, prefix="/api/v1/sm", tags=["销售管理V2"])
app.include_router(production_module.router, prefix="/api/v1/pm2", tags=["生产管理V2"])
app.include_router(inventory_v2.router, prefix="/api/v1/inv2", tags=["库存管理V2"])
app.include_router(finance_v2.router, prefix="/api/v1/fn2", tags=["财务期末"])
app.include_router(cost_accounting.router, prefix="/api/v1/cost", tags=["成本会计"])
app.include_router(analytics.router, prefix="/api/v1/an", tags=["报表分析"])
app.include_router(production_docs.router, prefix="/api/v1/pd", tags=["生产单据体系"])
app.include_router(engineering.router, prefix="/api/v1/eng", tags=["工程导向型专属模块"])
app.include_router(engineering_adaptation.router, prefix="/api/v1/eng-adapt", tags=["工程导向型适配"])
app.include_router(engineering_modules.router, prefix="/api/v1/eng-modules", tags=["工程导向型7大核心模块"])
app.include_router(procurement_optimization.router, prefix="/api/v1/opt", tags=["采购优化与选型门"])
app.include_router(api_integration.router, prefix="/api/v1/api-center", tags=["API对接中心"])
app.include_router(factory_api.router, prefix="/api/v1/factory", tags=["我的工厂"])
app.include_router(production_planning.router, prefix="/api/v1/pp", tags=["生产计划"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["跨部门通知"])
app.include_router(gl_ledger.router, prefix="/api/v1/gl", tags=["总账管理"])
# app.include_router(api_integration.router, prefix="/api/v1/api-center", tags=["API对接中心"])  # 需安装httpx后启用


# =============== 启动完成后：自动计提水电费 + 归集项目成本（全模块加载后，避免循环导入）===============
@app.on_event("startup")
def _startup_auto_cost():
    try:
        from .api.factory_api import auto_accrue_utility_fees
        from .api.engineering import recalc_project_costs
        db = SessionLocal()
        try:
            recs, vouchers = auto_accrue_utility_fees(db)
            if recs:
                print(f"[startup] 设备水电费自动计提：{recs}条明细 / {vouchers}张凭证")
            r = recalc_project_costs(db)
            # 注意：Windows 控制台为 GBK 编码，避免使用 ¥ 等特殊字符导致 UnicodeEncodeError
            print(f"[startup] 项目成本自动归集：{len(r.get('projects', []))}个项目，制造费用池 CNY {r.get('overhead_pool')}")
        finally:
            db.close()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[startup] 自动成本归集跳过（{e}）")

# ✅ 把 jsQR.min.js 等 frontend 内的平铺文件直接挂到根路径，避免跨网段 CDN 阻塞
# 注意：必须放在所有路由定义之后，否则会覆盖 /health、/ 等 GET 路由
app.mount("/", StaticFiles(directory="frontend", html=False), name="frontend_root")