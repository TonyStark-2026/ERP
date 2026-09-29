低保真线框说明

概览：本目录包含针对中小企业会计驱动ERP的桌面优先低保真线框占位文件（SVG），以及示例数据。线框以灰度与淡蓝点缀表现，主要用于功能与布局评审。

交付文件：
- design/wireframes/01-dashboard.svg — 仪表盘（成本与合规概览）
- design/wireframes/02-purchase-invoice.svg — 采购/开票录入（含税率校验预警）
- design/wireframes/03-warehouse-scan.svg — 入库/出库/盘点（扫码流程）
- design/wireframes/04-materials-cva-abc.svg — 物料档案与CVA-ABC分类
- design/wireframes/05-production-workorder.svg — 生产工单/在产与约当产量核算
- design/wireframes/06-sales-invoice.svg — 销售/发货（发票语言切换）
- design/wireframes/07-crossborder-order.svg — 跨境订单（HS校验、关税/VAT估算）
- design/wireframes/08-reports.svg — 报表与凭证浏览
- design/sample-data.csv — 示例数据（示例物料/采购/工单/跨境订单）

每页说明：
- 仪表盘：展示总体成本摘要、在产量、关键合规预警（税率不匹配、税号到期提醒）、库存ABC汇总与待处理跨境问题计数。
- 采购/开票：采购订单字段、发票上传/录入、税率智能校验提示、不匹配时的高亮与处理建议。
- 仓库扫码：扫码输入框、当前单据概要、异常提示（超量、批次缺失）、快速入库确认按钮。
- 物料档案：物料基本信息、价值/关键性评分、CVA-ABC 分类标签与推荐库存策略（最小/最大/安全库存）。
- 生产工单：工单BOM、报工入口、在产数量、约当产量计算占位与结果展示。
- 销售/发货：销售单录入、发票语言切换（中文/英文占位）、发货面单模板选择。
- 跨境订单：HS 编码输入与自动校验结果、关税和目标国 VAT 估算、贸易术语成本拆分占位。
- 报表：凭证浏览、成本报表导出、库存ABC明细导出。

验收要点：
1. 每个 SVG 能表达主要输入点与关键交互位置（例如税率校验、扫码确认）。
2. 示例数据能在说明中定位到相关示例行。

下一步：如果你希望我继续导出 PNG 或生成可交互 HTML/React 原型，请告知；否则我将等待你的评审反馈并按需迭代。