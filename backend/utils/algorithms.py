from typing import List, Tuple, Dict, Optional
from decimal import Decimal, ROUND_HALF_UP

def calculate_equivalent_production(
    completed_qty: int,
    in_progress_qty: int,
    completion_ratio: float
) -> float:
    """
    计算约当产量
    :param completed_qty: 完工数量
    :param in_progress_qty: 在产数量
    :param completion_ratio: 在产完工率 (0-1)
    :return: 约当产量
    """
    return completed_qty + (in_progress_qty * completion_ratio)

def allocate_cost(
    total_cost_input: float,
    completed_qty: int,
    in_progress_qty: int,
    completion_ratio: float
) -> Dict[str, float]:
    """
    约当产量法成本分摊
    :param total_cost_input: 总投入成本
    :param completed_qty: 完工数量
    :param in_progress_qty: 在产数量
    :param completion_ratio: 在产完工率 (0-1)
    :return: 分摊结果字典
    """
    equivalent_output = calculate_equivalent_production(
        completed_qty, in_progress_qty, completion_ratio
    )
    
    if equivalent_output == 0:
        return {
            "total_input_cost": total_cost_input,
            "equivalent_output": 0,
            "cost_per_equivalent": 0,
            "completed_allocation": 0,
            "in_progress_allocation": 0
        }
    
    cost_per_equivalent = total_cost_input / equivalent_output
    completed_allocation = cost_per_equivalent * completed_qty
    in_progress_allocation = cost_per_equivalent * (in_progress_qty * completion_ratio)
    
    return {
        "total_input_cost": total_cost_input,
        "equivalent_output": round(equivalent_output, 4),
        "cost_per_equivalent": round(cost_per_equivalent, 4),
        "completed_allocation": round(completed_allocation, 4),
        "in_progress_allocation": round(in_progress_allocation, 4)
    }

def allocate_cost_by_type(
    costs: List[Dict[str, float]],
    completed_qty: int,
    in_progress_qty: int,
    completion_ratio: float
) -> Dict[str, Dict[str, float]]:
    """
    按成本类型分别进行约当产量法分摊
    :param costs: 成本列表，每项包含 cost_type 和 amount
    :param completed_qty: 完工数量
    :param in_progress_qty: 在产数量
    :param completion_ratio: 在产完工率 (0-1)
    :return: 各成本类型的分摊结果
    """
    result = {}
    total_allocation = {
        "total_input_cost": 0,
        "equivalent_output": 0,
        "cost_per_equivalent": 0,
        "completed_allocation": 0,
        "in_progress_allocation": 0
    }
    
    for cost_item in costs:
        cost_type = cost_item["cost_type"]
        amount = cost_item["amount"]
        
        allocation = allocate_cost(amount, completed_qty, in_progress_qty, completion_ratio)
        result[cost_type] = allocation
        
        total_allocation["total_input_cost"] += allocation["total_input_cost"]
        total_allocation["equivalent_output"] = allocation["equivalent_output"]
        total_allocation["completed_allocation"] += allocation["completed_allocation"]
        total_allocation["in_progress_allocation"] += allocation["in_progress_allocation"]
    
    if total_allocation["equivalent_output"] > 0:
        total_allocation["cost_per_equivalent"] = round(
            total_allocation["total_input_cost"] / total_allocation["equivalent_output"],
            4
        )
    
    result["total"] = total_allocation
    return result

def calculate_value_score(
    annual_consumption_amount: float,
    max_consumption_amount: float
) -> float:
    """
    计算物料价值分数（归一化）
    :param annual_consumption_amount: 年度消耗金额
    :param max_consumption_amount: 所有物料中最大年度消耗金额
    :return: 价值分数 (0-1)
    """
    if max_consumption_amount == 0:
        return 0.0
    return min(annual_consumption_amount / max_consumption_amount, 1.0)

def classify_cva_abc(
    value_score: float,
    criticality: int
) -> Tuple[str, str]:
    """
    CVA-ABC 分类
    :param value_score: 价值分数 (0-1)
    :param criticality: 关键性评分 (1-5)
    :return: (ABC分类, CVA分类)
    """
    if value_score >= 0.8:
        abc_class = "A"
    elif value_score >= 0.5:
        abc_class = "B"
    else:
        abc_class = "C"
    
    if criticality >= 4:
        cva_class = "Vital"
    elif criticality >= 3:
        cva_class = "Essential"
    elif criticality >= 2:
        cva_class = "Important"
    else:
        cva_class = "Desirable"
    
    return (abc_class, cva_class)

def generate_inventory_strategy(
    abc_class: str,
    cva_class: str
) -> Dict[str, str]:
    """
    根据CVA-ABC分类生成库存管理策略
    :param abc_class: ABC分类
    :param cva_class: CVA分类
    :return: 库存策略建议
    """
    strategies = {
        ("A", "Vital"): {
            "reorder_policy": "连续盘点，安全库存高",
            "order_frequency": "频繁",
            "safety_stock": "高",
            "review_cycle": "每日",
            "priority": "最高"
        },
        ("A", "Essential"): {
            "reorder_policy": "定期盘点，安全库存较高",
            "order_frequency": "频繁",
            "safety_stock": "较高",
            "review_cycle": "每周",
            "priority": "高"
        },
        ("A", "Important"): {
            "reorder_policy": "定期盘点，安全库存适中",
            "order_frequency": "较频繁",
            "safety_stock": "适中",
            "review_cycle": "每周",
            "priority": "中"
        },
        ("A", "Desirable"): {
            "reorder_policy": "常规管理",
            "order_frequency": "正常",
            "safety_stock": "低",
            "review_cycle": "每月",
            "priority": "低"
        },
        ("B", "Vital"): {
            "reorder_policy": "定期盘点，安全库存较高",
            "order_frequency": "较频繁",
            "safety_stock": "较高",
            "review_cycle": "每周",
            "priority": "高"
        },
        ("B", "Essential"): {
            "reorder_policy": "定期盘点，安全库存适中",
            "order_frequency": "正常",
            "safety_stock": "适中",
            "review_cycle": "每两周",
            "priority": "中"
        },
        ("B", "Important"): {
            "reorder_policy": "常规管理",
            "order_frequency": "正常",
            "safety_stock": "适中",
            "review_cycle": "每月",
            "priority": "中"
        },
        ("B", "Desirable"): {
            "reorder_policy": "宽松管理",
            "order_frequency": "较低",
            "safety_stock": "低",
            "review_cycle": "每月",
            "priority": "低"
        },
        ("C", "Vital"): {
            "reorder_policy": "定期盘点，安全库存适中",
            "order_frequency": "正常",
            "safety_stock": "适中",
            "review_cycle": "每月",
            "priority": "中"
        },
        ("C", "Essential"): {
            "reorder_policy": "宽松管理",
            "order_frequency": "较低",
            "safety_stock": "低",
            "review_cycle": "每季度",
            "priority": "低"
        },
        ("C", "Important"): {
            "reorder_policy": "宽松管理",
            "order_frequency": "低",
            "safety_stock": "低",
            "review_cycle": "每季度",
            "priority": "低"
        },
        ("C", "Desirable"): {
            "reorder_policy": "最小化库存",
            "order_frequency": "按需",
            "safety_stock": "极低",
            "review_cycle": "每季度",
            "priority": "最低"
        }
    }
    
    return strategies.get((abc_class, cva_class), {
        "reorder_policy": "常规管理",
        "order_frequency": "正常",
        "safety_stock": "适中",
        "review_cycle": "每月",
        "priority": "中"
    })

def calculate_reorder_point(
    avg_daily_demand: float,
    lead_time_days: int,
    safety_stock: float
) -> float:
    """
    计算再订货点
    :param avg_daily_demand: 日均需求量
    :param lead_time_days: 提前期天数
    :param safety_stock: 安全库存
    :return: 再订货点
    """
    return (avg_daily_demand * lead_time_days) + safety_stock

def calculate_eoq(
    annual_demand: float,
    ordering_cost: float,
    holding_cost_per_unit: float
) -> float:
    """
    计算经济订货批量 (EOQ)
    :param annual_demand: 年度需求量
    :param ordering_cost: 每次订货成本
    :param holding_cost_per_unit: 单位持有成本
    :return: 经济订货批量
    """
    if holding_cost_per_unit == 0:
        return annual_demand
    
    eoq = ((2 * annual_demand * ordering_cost) / holding_cost_per_unit) ** 0.5
    return round(eoq, 2)