算法规范（伪代码与测试向量）

1) 约当产量法（Equivalent Production） — 概要
输入：工单总投入量、已完工数量、在产数量、在产完工率（或按工序权重）
输出：分配到完工产品与在产产品的成本金额

伪代码：
- equivalent_output = completed_qty + in_progress_qty * completion_ratio
- cost_per_equivalent = total_cost_input / equivalent_output
- cost_allocated_to_completed = cost_per_equivalent * completed_qty
- cost_allocated_to_inprogress = cost_per_equivalent * (in_progress_qty * completion_ratio)

测试向量：提供示例数据并验证数值一致性

2) CVA‑ABC 分类 — 概要
- 价值维度（Value Score）：基于历史消耗金额与单位成本计算
- 关键性维度（Criticality）：手动评分或通过工序依赖分析得出
- 分类：A/B/C 由价值阈值确定，CVA 从组合维度得出最终策略

流程：
- 计算 12 个月消耗金额，归一化生成 value_score
- 根据 value_score 与 criticality 矩阵决定分组与补货策略

3) 合规规则（示例）
- 发票税率校验：采购单税率 != 发票税率 → 标记预警并给出建议（如需补差、联系供应商）
- 税号有效期：到期前 30 天提醒
- HS 校验：校验 HS 是否在内置库中，若需目的国特殊申报字段则提示缺失

每个算法条目需附带边界条件、异常处理与预期测试用例。