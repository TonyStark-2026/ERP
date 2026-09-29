# API合约文档

## 一、基础信息

| 项目 | 说明 |
|-----|------|
| API版本 | v1 |
| 基础路径 | `/api/v1` |
| 认证方式 | OAuth2 Bearer Token |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |

---

## 二、通用响应格式

### 成功响应
```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "error_code": null,
  "timestamp": "2026-05-18T10:30:00Z"
}
```

### 失败响应
```json
{
  "success": false,
  "data": null,
  "message": "错误描述",
  "error_code": "40001",
  "timestamp": "2026-05-18T10:30:00Z"
}
```

---

## 三、物料管理 API

### 3.1 创建物料
- **路径**: `POST /materials`
- **描述**: 创建新物料

**请求体**:
```json
{
  "name": "string (必填, 物料名称)",
  "description": "string (选填, 物料描述)",
  "unit_price": "number (必填, 单价)",
  "unit": "string (必填, 计量单位)",
  "hs_code": "string (选填, HS编码)",
  "criticality": "number (选填, 关键性评分 1-5)"
}
```

**成功响应**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "原材料A",
    "description": "描述",
    "unit_price": 100.0,
    "unit": "件",
    "hs_code": "85235100",
    "criticality": 4,
    "created_at": "2026-05-18T10:30:00Z"
  },
  "message": "创建成功",
  "error_code": null,
  "timestamp": "2026-05-18T10:30:00Z"
}
```

### 3.2 查询物料列表
- **路径**: `GET /materials`
- **描述**: 获取物料列表

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| skip | int | 否 | 跳过条数，默认0 |
| limit | int | 否 | 返回条数，默认100 |
| name | string | 否 | 物料名称模糊查询 |

**成功响应**:
```json
{
  "success": true,
  "data": {
    "items": [],
    "total": 0
  },
  "message": "查询成功",
  "error_code": null,
  "timestamp": "2026-05-18T10:30:00Z"
}
```

### 3.3 查询单个物料
- **路径**: `GET /materials/{material_id}`
- **描述**: 获取单个物料详情

**路径参数**:
| 参数 | 类型 | 说明 |
|-----|------|------|
| material_id | int | 物料ID |

### 3.4 更新物料
- **路径**: `PUT /materials/{material_id}`
- **描述**: 更新物料信息

### 3.5 删除物料
- **路径**: `DELETE /materials/{material_id}`
- **描述**: 删除物料

---

## 四、生产成本核算 API

### 4.1 创建生产工单
- **路径**: `POST /production/workorders`
- **描述**: 创建生产工单

**请求体**:
```json
{
  "work_order_no": "string (必填, 工单号)",
  "product_id": "int (必填, 产品ID)",
  "planned_qty": "int (必填, 计划产量)",
  "start_date": "string (必填, 开始日期 YYYY-MM-DD)",
  "end_date": "string (选填, 结束日期 YYYY-MM-DD)"
}
```

### 4.2 录入生产成本
- **路径**: `POST /production/costs`
- **描述**: 录入生产成本

**请求体**:
```json
{
  "work_order_id": "int (必填, 工单ID)",
  "cost_type": "string (必填, RAW_MATERIAL/DIRECT_LABOR/MANUFACTURING_OVERHEAD)",
  "amount": "number (必填, 成本金额)",
  "description": "string (选填, 说明)"
}
```

### 4.3 约当产量成本分摊
- **路径**: `POST /production/allocation`
- **描述**: 执行约当产量法成本分摊

**请求体**:
```json
{
  "work_order_id": "int (必填, 工单ID)",
  "completed_qty": "int (必填, 完工数量)",
  "in_progress_qty": "int (必填, 在产数量)",
  "completion_ratio": "number (必填, 在产完工率 0-1)"
}
```

**成功响应**:
```json
{
  "success": true,
  "data": {
    "work_order_id": 1,
    "total_input_cost": 10000.0,
    "equivalent_output": 180,
    "cost_per_equivalent": 55.56,
    "completed_allocation": 11112.0,
    "in_progress_allocation": 5556.0
  },
  "message": "成本分摊成功",
  "error_code": null,
  "timestamp": "2026-05-18T10:30:00Z"
}
```

---

## 五、合规预警 API

### 5.1 发票税率校验
- **路径**: `POST /compliance/tax-check`
- **描述**: 校验采购订单与发票税率是否匹配

**请求体**:
```json
{
  "purchase_order_id": "int (必填, 采购订单ID)",
  "invoice_tax_rate": "number (必填, 发票税率)",
  "invoice_amount": "number (必填, 发票金额)"
}
```

**成功响应**:
```json
{
  "success": true,
  "data": {
    "match": false,
    "po_tax_rate": 0.13,
    "invoice_tax_rate": 0.09,
    "warning_level": "HIGH",
    "suggestion": "税率不匹配，建议联系供应商核实"
  },
  "message": "校验完成",
  "error_code": null,
  "timestamp": "2026-05-18T10:30:00Z"
}
```

### 5.2 获取预警列表
- **路径**: `GET /compliance/alerts`
- **描述**: 获取合规预警列表

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| level | string | 否 | 预警级别 HIGH/MEDIUM/LOW |
| status | string | 否 | 状态 PENDING/RESOLVED |

---

## 六、跨境合规 API

### 6.1 税费估算
- **路径**: `POST /crossborder/tax-estimate`
- **描述**: 估算跨境订单税费

**请求体**:
```json
{
  "hs_code": "string (必填, HS编码)",
  "country_code": "string (必填, 目的国代码)",
  "declared_value": "number (必填, 申报价值)",
  "quantity": "int (必填, 数量)",
  "currency": "string (必填, 货币代码)"
}
```

**成功响应**:
```json
{
  "success": true,
  "data": {
    "hs_code": "85235100",
    "country_code": "US",
    "import_tax": 150.0,
    "vat": 200.0,
    "total_tax": 350.0,
    "exchange_rate": 7.24,
    "total_tax_cny": 2534.0
  },
  "message": "计算完成",
  "error_code": null,
  "timestamp": "2026-05-18T10:30:00Z"
}
```

### 6.2 HS编码校验
- **路径**: `POST /crossborder/hs-validate`
- **描述**: 校验HS编码并获取申报要素

**请求体**:
```json
{
  "hs_code": "string (必填, HS编码)",
  "country_code": "string (选填, 目的国代码)"
}
```

---

## 七、仓库管理 API

### 7.1 扫码入库
- **路径**: `POST /inventory/inbound`
- **描述**: 扫码入库

**请求体**:
```json
{
  "material_id": "int (必填, 物料ID)",
  "quantity": "int (必填, 数量)",
  "location_code": "string (必填, 库位编码)",
  "batch_no": "string (选填, 批次号)",
  "expiry_date": "string (选填, 有效期)"
}
```

### 7.2 扫码出库
- **路径**: `POST /inventory/outbound`
- **描述**: 扫码出库

### 7.3 库存盘点
- **路径**: `POST /inventory/stocktake`
- **描述**: 库存盘点

---

## 八、错误码列表

| 错误码 | 含义 | HTTP状态码 |
|-------|------|-----------|
| 40001 | 参数校验失败 | 400 |
| 40002 | 资源不存在 | 404 |
| 40003 | 业务规则校验失败 | 400 |
| 40004 | 权限不足 | 403 |
| 50001 | 数据库操作失败 | 500 |
| 50002 | 外部服务调用失败 | 503 |