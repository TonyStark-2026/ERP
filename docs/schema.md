# 数据模型文档

## 一、数据库表结构

### 1. 物料表 (materials)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 物料ID |
| name | VARCHAR(100) | NOT NULL, UNIQUE | 物料名称 |
| description | TEXT | NULL | 物料描述 |
| unit_price | DECIMAL(18,4) | NOT NULL, DEFAULT 0 | 单价 |
| unit | VARCHAR(20) | NOT NULL | 计量单位 |
| hs_code | VARCHAR(20) | NULL | HS编码 |
| criticality | TINYINT | NULL | 关键性评分(1-5) |
| value_score | DECIMAL(5,2) | NULL | 价值分数 |
| cva_abc_class | VARCHAR(10) | NULL | CVA-ABC分类 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

### 2. 采购订单表 (purchase_orders)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 订单ID |
| po_no | VARCHAR(50) | NOT NULL, UNIQUE | 采购订单号 |
| material_id | INT | FOREIGN KEY | 物料ID |
| supplier_id | INT | FOREIGN KEY | 供应商ID |
| quantity | INT | NOT NULL, DEFAULT 1 | 数量 |
| unit_price | DECIMAL(18,4) | NOT NULL | 单价 |
| tax_rate | DECIMAL(5,2) | NOT NULL | 税率 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'PENDING' | 状态 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 3. 生产工单单 (production_workorders)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 工单ID |
| work_order_no | VARCHAR(50) | NOT NULL, UNIQUE | 工单号 |
| product_id | INT | FOREIGN KEY | 产品ID |
| planned_qty | INT | NOT NULL | 计划产量 |
| completed_qty | INT | NOT NULL, DEFAULT 0 | 完工数量 |
| in_progress_qty | INT | NOT NULL, DEFAULT 0 | 在产数量 |
| completion_ratio | DECIMAL(5,2) | NULL | 在产完工率 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'PLANNED' | 状态 |
| start_date | DATE | NOT NULL | 开始日期 |
| end_date | DATE | NULL | 结束日期 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 4. 生产成本表 (production_costs)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 成本ID |
| work_order_id | INT | FOREIGN KEY | 工单ID |
| cost_type | VARCHAR(30) | NOT NULL | 成本类型 |
| amount | DECIMAL(18,4) | NOT NULL | 金额 |
| description | TEXT | NULL | 说明 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 5. 成本分摊结果表 (cost_allocations)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 分摊ID |
| work_order_id | INT | FOREIGN KEY | 工单ID |
| total_input_cost | DECIMAL(18,4) | NOT NULL | 总投入成本 |
| equivalent_output | DECIMAL(18,4) | NOT NULL | 约当产量 |
| cost_per_equivalent | DECIMAL(18,4) | NOT NULL | 单位约当成本 |
| completed_allocation | DECIMAL(18,4) | NOT NULL | 完工产品分摊 |
| in_progress_allocation | DECIMAL(18,4) | NOT NULL | 在产品分摊 |
| allocated_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 分摊时间 |

### 6. 库存记录表 (inventory_records)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 记录ID |
| material_id | INT | FOREIGN KEY | 物料ID |
| location_code | VARCHAR(50) | NOT NULL | 库位编码 |
| batch_no | VARCHAR(50) | NULL | 批次号 |
| expiry_date | DATE | NULL | 有效期 |
| quantity | INT | NOT NULL | 数量 |
| stock_type | VARCHAR(20) | NOT NULL | 库存类型 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 7. 库存变动日志 (inventory_transactions)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 日志ID |
| material_id | INT | FOREIGN KEY | 物料ID |
| transaction_type | VARCHAR(20) | NOT NULL | 变动类型 |
| quantity | INT | NOT NULL | 数量 |
| before_qty | INT | NOT NULL | 变动前数量 |
| after_qty | INT | NOT NULL | 变动后数量 |
| reference_no | VARCHAR(50) | NULL | 关联单号 |
| operator | VARCHAR(50) | NOT NULL | 操作人 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 8. 合规预警表 (compliance_alerts)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 预警ID |
| alert_type | VARCHAR(30) | NOT NULL | 预警类型 |
| level | VARCHAR(20) | NOT NULL | 预警级别 |
| reference_id | INT | NULL | 关联ID |
| message | TEXT | NOT NULL | 预警信息 |
| suggestion | TEXT | NULL | 处理建议 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'PENDING' | 状态 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| resolved_at | DATETIME | NULL | 解决时间 |

### 9. 供应商表 (suppliers)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 供应商ID |
| name | VARCHAR(100) | NOT NULL | 供应商名称 |
| tax_id | VARCHAR(50) | NULL | 税号 |
| tax_id_expiry | DATE | NULL | 税号有效期 |
| contact | VARCHAR(50) | NULL | 联系人 |
| phone | VARCHAR(20) | NULL | 电话 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 10. HS编码表 (hs_codes)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | ID |
| hs_code | VARCHAR(20) | NOT NULL, UNIQUE | HS编码 |
| description_cn | TEXT | NOT NULL | 中文描述 |
| description_en | TEXT | NULL | 英文描述 |
| unit | VARCHAR(20) | NULL | 计量单位 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 11. 国家税制表 (country_tax_rules)

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | ID |
| country_code | VARCHAR(10) | NOT NULL | 国家代码 |
| country_name | VARCHAR(100) | NOT NULL | 国家名称 |
| vat_rate | DECIMAL(5,2) | NULL | VAT税率 |
| import_tax_rate | DECIMAL(5,2) | NULL | 进口税率 |
| currency_code | VARCHAR(10) | NOT NULL | 货币代码 |
| invoice_language | VARCHAR(20) | NULL | 发票语言 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

## 二、ER关系图

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────┐
│  suppliers   │───────│  purchase_orders │───────│  materials   │
└──────────────┘       └──────────────────┘       └──────────────┘
                              │                         │
                              │                         │
                              ▼                         ▼
                    ┌─────────────────┐       ┌──────────────────┐
                    │production_costs │       │inventory_records │
                    └────────┬────────┘       └────────┬─────────┘
                             │                         │
                             ▼                         ▼
                    ┌─────────────────┐       ┌──────────────────┐
                    │cost_allocations │       │inventory_trans   │
                    └─────────────────┘       └──────────────────┘

┌──────────────┐       ┌──────────────────┐       ┌──────────────┐
│   hs_codes   │───────│country_tax_rules │───────│compliance_   │
└──────────────┘       └──────────────────┘       │  alerts      │
                                                  └──────────────┘
```

---

## 三、枚举类型定义

### 成本类型 (cost_type)
| 值 | 说明 |
|-----|------|
| RAW_MATERIAL | 原材料成本 |
| DIRECT_LABOR | 直接人工成本 |
| MANUFACTURING_OVERHEAD | 制造费用 |

### 预警级别 (level)
| 值 | 说明 |
|-----|------|
| HIGH | 高 |
| MEDIUM | 中 |
| LOW | 低 |

### 工单状态 (status)
| 值 | 说明 |
|-----|------|
| PLANNED | 计划中 |
| IN_PROGRESS | 生产中 |
| COMPLETED | 已完成 |
| CANCELLED | 已取消 |

### 交易类型 (transaction_type)
| 值 | 说明 |
|-----|------|
| INBOUND | 入库 |
| OUTBOUND | 出库 |
| ADJUSTMENT | 调整 |
| STOCKTAKE | 盘点 |