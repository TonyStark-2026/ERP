"""
AI Copilot - ERP 智能操作副驾后端
===================================
痛点1：意图驱动的对话式指令面板
痛点2：跨模块智能上下文携带引擎
痛点3：自然语言语义搜索
痛点4：动态业务规则配置器 + 场景规则库
痛点5：智能采购批量处理助手
痛点6：一键纠错动作链

说明：
  - 本系统定位为"独立软件（免安装、可离线）"，不依赖外部 LLM 服务。
  - 意图识别使用"关键词模板 + 模糊匹配 + 同义词词典"实现，可覆盖 ERP 常见业务操作。
  - 所有动作执行复用已有的 models / crud / api 能力，确保数据一致性。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
import re
import datetime
import uuid
from .. import models, crud
from ..database import SessionLocal
from ..app import make_response, get_db

router = APIRouter()


# ============================================================
# 🔹 上下文池（痛点2：跨模块智能上下文携带引擎）
# ============================================================
# 基于内存实现（对单用户绿色版软件足够）；可在未来切换到 Redis / DB
_CONTEXT_POOL: Dict[str, Dict[str, Any]] = {}


def _ctx_key(user_id: Any) -> str:
    return f"u_{user_id}"


def set_context(user_id: Any, key: str, value: Any):
    k = _ctx_key(user_id)
    if k not in _CONTEXT_POOL:
        _CONTEXT_POOL[k] = {}
    _CONTEXT_POOL[k][key] = value
    # 清理：每个用户最多保留 50 条上下文
    if len(_CONTEXT_POOL[k]) > 50:
        first_key = next(iter(_CONTEXT_POOL[k]))
        del _CONTEXT_POOL[k][first_key]


def get_context(user_id: Any, key: Optional[str] = None, default: Any = None):
    k = _ctx_key(user_id)
    pool = _CONTEXT_POOL.get(k, {})
    if key is None:
        return pool
    return pool.get(key, default)


def clear_context(user_id: Any, key: Optional[str] = None):
    k = _ctx_key(user_id)
    if key is None:
        _CONTEXT_POOL[k] = {}
    else:
        if k in _CONTEXT_POOL and key in _CONTEXT_POOL[k]:
            del _CONTEXT_POOL[k][key]


# ============================================================
# 🔹 规则引擎（痛点4：动态业务规则配置器 + 场景规则库）
# ============================================================
_BUILTIN_RULES: List[Dict[str, Any]] = [
    {
        "id": "RULE_GIFT_001",
        "name": "赠品出库：有数量无金额",
        "category": "sales",
        "enabled": False,
        "description": "销售单行项勾选赠品后，单价/金额自动置 0，但保留数量用于出库和扣减库存。",
        "logic": {"set": {"unit_price": 0, "amount": 0}, "when": "is_gift == True"},
    },
    {
        "id": "RULE_CREDIT_001",
        "name": "新客户首单信用临时提升",
        "category": "sales",
        "enabled": False,
        "description": "新增客户首单若超过信用额度，允许临时提额 20%，生成审批提醒。",
        "logic": {"increase_credit_rate": 0.2, "when": "is_first_order and total > credit_limit"},
    },
    {
        "id": "RULE_STOCK_001",
        "name": "低于安全库存自动生成采购申请",
        "category": "purchase",
        "enabled": False,
        "description": "物料库存低于安全库存 (min_stock) 时，自动生成采购申请到默认供应商。",
        "logic": {"auto_pr": True, "when": "qty < min_stock"},
    },
    {
        "id": "RULE_PRICE_001",
        "name": "采购价超警戒线自动预警",
        "category": "purchase",
        "enabled": False,
        "description": "采购单单价超过近 10 次历史平均价 ±15% 时，阻塞并要求审批。",
        "logic": {"threshold_rate": 0.15, "when": "unit_price > avg_price_10 * (1+threshold)"},
    },
    {
        "id": "RULE_VOUCHER_001",
        "name": "附单据汉字竖排数字横排",
        "category": "finance",
        "enabled": True,
        "description": "凭证附件数显示时，汉字竖排，阿拉伯数字横排显示。",
        "logic": {"vertical_chinese": True},
    },
]

# 自定义规则存放
_CUSTOM_RULES: List[Dict[str, Any]] = []


def list_rules(enabled_only: bool = False) -> List[Dict[str, Any]]:
    all_rules = _BUILTIN_RULES + _CUSTOM_RULES
    if enabled_only:
        return [r for r in all_rules if r.get("enabled")]
    return all_rules


def toggle_rule(rule_id: str, enabled: bool) -> Optional[Dict[str, Any]]:
    for r in _BUILTIN_RULES + _CUSTOM_RULES:
        if r["id"] == rule_id:
            r["enabled"] = enabled
            return r
    return None


def add_custom_rule(rule: Dict[str, Any]) -> Dict[str, Any]:
    rule.setdefault("id", "RULE_CUSTOM_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
    rule.setdefault("enabled", False)
    rule.setdefault("category", "general")
    _CUSTOM_RULES.append(rule)
    return rule


# ============================================================
# 🔹 同义词词典 & 意图识别（痛点1/3 基础）
# ============================================================
_SYNONYMS = {
    "create": ["创建", "新增", "建", "开", "录入", "新增一个", "开一张", "做一张", "生成"],
    "query": ["查询", "查", "找", "搜索", "看看", "显示", "列出", "找一下", "检索"],
    "delete": ["删除", "删掉", "移除", "作废", "取消"],
    "update": ["修改", "改", "更新", "调整", "变更"],
    "approve": ["审批", "审核", "批准", "过审"],
    "material": ["物料", "商品", "产品", "存货", "货品"],
    "customer": ["客户", "买方", "购货方"],
    "supplier": ["供应商", "供方", "厂家", "卖方"],
    "sales_order": ["销售单", "销售订单", "订单", "销货单", "SO"],
    "purchase_order": ["采购单", "采购订单", "PO", "购货单", "进货单"],
    "purchase_request": ["采购申请", "请购单", "PR"],
    "work_order": ["工单", "生产工单", "生产订单", "WO"],
    "inventory": ["库存", "存货", "仓库", "现有量", "在库"],
    "finance": ["财务", "账", "报表", "收支"],
    "stock": ["库存", "库存数", "现有量"],
    "total": ["合计", "总额", "总计", "总数"],
}


def _expand_text(text: str) -> str:
    """把同义词统一替换成标准词，便于后续正则匹配"""
    expanded = text
    # 先替换长的词组避免冲突
    for std, words in sorted(_SYNONYMS.items(), key=lambda x: -max(len(w) for w in x[1])):
        for w in words:
            if w in expanded:
                expanded = expanded.replace(w, f" {std} ")
    return expanded


# 数字提取
_NUM_RE = re.compile(r"(\d+(?:\.\d+)?)")
_ID_RE = re.compile(r"(?:ID|id|编号|单号|订单号|单号为|No\.|no\.|#)\s*[:：]?\s*([A-Za-z0-9_\-]+)", re.IGNORECASE)


def parse_intent(text: str) -> Dict[str, Any]:
    """
    解析自然语言指令，返回：
    {
      "intent": "create_sales_order" | "query_material" | ...,
      "action": "create" | "query" | "update" | "delete" | "approve",
      "module": "material" | "sales_order" | "purchase_order" | "customer" | "supplier" |
                "inventory" | "work_order" | "finance",
      "params": { "customer": "XX", "material": "XX", "qty": 100, "price": 50, ... },
      "confidence": 0.0 ~ 1.0,
      "raw": text,
    }
    """
    raw = (text or "").strip()
    if not raw:
        return {"intent": "unknown", "confidence": 0, "raw": raw, "params": {}}

    expanded = _expand_text(raw)

    # --- 1. 动作分类 ---
    action = "query"  # 默认查询
    std_actions = ["create", "delete", "update", "approve", "query"]
    for a in std_actions[:-1]:  # 跳过默认的 query
        if a in expanded:  # 替换后的标准词
            action = a
            break
        if any(k in raw for k in _SYNONYMS.get(a, [])):
            action = a
            break
    if action == "query" and any(k in raw for k in _SYNONYMS["query"]):
        action = "query"

    # --- 2. 模块分类 ---
    module = None
    module_keywords = [
        ("sales_order", ["sales_order", "订单", "销售单", "销货单"]),
        ("purchase_order", ["purchase_order", "采购单", "PO", "购货单", "进货单"]),
        ("purchase_request", ["purchase_request", "请购单", "采购申请"]),
        ("work_order", ["work_order", "工单", "生产工单", "生产订单", "WO"]),
        ("material", ["material", "物料", "商品", "产品", "存货", "货品"]),
        ("customer", ["customer", "客户", "买方", "购货方"]),
        ("supplier", ["supplier", "供应商", "供方", "厂家", "卖方"]),
        ("inventory", ["inventory", "库存", "存货", "仓库", "现有量", "在库"]),
        ("finance", ["finance", "财务", "账", "报表", "收支", "应收", "应付", "利润"]),
    ]
    for mod, keys in module_keywords:
        # 优先匹配标准词，再匹配中文
        if mod in expanded.split():
            module = mod
            break
        if any(k and k in raw for k in keys):
            module = mod
            break

    # --- 3. 参数抽取 ---
    params: Dict[str, Any] = {}

    # 数量： "XX 个" / "XX台" / "数量XX" / "XX件"
    qty_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:个|台|件|套|箱|瓶|kg|吨|克|只)", expanded)
    if qty_match:
        params["qty"] = float(qty_match.group(1)) if "." in qty_match.group(1) else int(qty_match.group(1))
    qty_match2 = re.search(r"(?:数量|qty|QTY)\s*[:：=]?\s*(\d+(?:\.\d+)?)", expanded)
    if qty_match2:
        params["qty"] = float(qty_match2.group(1)) if "." in qty_match2.group(1) else int(qty_match2.group(1))

    # 价格
    price_match = re.search(r"(?:单价|价格|price|¥|￥|RMB|人民币)\s*[:：=]?\s*(\d+(?:\.\d+)?)", expanded)
    if price_match:
        params["price"] = float(price_match.group(1))
    # 金额
    amt_match = re.search(r"(?:金额|总额|合计|total|amount)\s*[:：=]?\s*(\d+(?:\.\d+)?)", expanded)
    if amt_match:
        params["amount"] = float(amt_match.group(1))

    # ID
    id_match = _ID_RE.search(expanded)
    if id_match:
        params["id"] = id_match.group(1)

    # 所有数字列表（给前端预填参考）
    params["numbers"] = [float(x) if "." in x else int(x) for x in _NUM_RE.findall(raw)]

    # 关键字词（去掉动作和模块后的名词）
    stopwords = set()
    for words in _SYNONYMS.values():
        stopwords.update(words)
    tokens = re.split(r"[\s,，。、;；:：!！?？()（）\[\]【】]+", raw)
    keywords = [t for t in tokens if t and t not in stopwords and not _NUM_RE.fullmatch(t)]
    if keywords:
        params["keywords"] = keywords

    # 置信度：有动作+模块=0.9，只有动作或只有模块=0.5，都无=0.1
    confidence = 0.1
    if action and module:
        confidence = 0.9
    elif action or module:
        confidence = 0.5

    intent = "unknown"
    if action and module:
        intent = f"{action}_{module}"
    elif action == "query" and not module:
        intent = "global_search"

    return {
        "intent": intent,
        "action": action,
        "module": module,
        "params": params,
        "confidence": confidence,
        "raw": raw,
    }


def _humanize_intent(parsed: Dict[str, Any]) -> str:
    action_map = {"create": "新建", "query": "查询", "update": "修改", "delete": "删除", "approve": "审批"}
    module_map = {
        "sales_order": "销售订单",
        "purchase_order": "采购订单",
        "purchase_request": "采购申请单",
        "work_order": "生产工单",
        "material": "物料",
        "customer": "客户",
        "supplier": "供应商",
        "inventory": "库存",
        "finance": "财务",
    }
    act = action_map.get(parsed.get("action", ""), "操作")
    mod = module_map.get(parsed.get("module", ""), "业务")
    p = parsed.get("params", {})
    kw = " ".join(p.get("keywords", []))
    extra = []
    if "qty" in p:
        extra.append(f"数量 {p['qty']}")
    if "price" in p:
        extra.append(f"单价 {p['price']}")
    if "id" in p:
        extra.append(f"编号 {p['id']}")
    return f"{act}{mod}" + (f" - {kw}" if kw else "") + (f"（{'，'.join(extra)}）" if extra else "")


# ============================================================
# 🔹 语义搜索（痛点3）
# ============================================================
def semantic_search(db: Session, q: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    基于分词关键词 + 数据库 LIKE 的模糊混合搜索。
    跨模块：物料 / 客户 / 供应商 / 销售单 / 采购单 / 工单 / 库存
    """
    if not q:
        return []
    # 简单分词：以非字符数字作为分隔符 + 数字单独提取
    tokens = [t for t in re.split(r"[\s,，。、;；:：!！?？()（）\[\]【】_/\\\-]+", q) if t]
    if not tokens:
        tokens = [q]
    # 为每个 token 做 LIKE，任意 token 命中就算命中
    def like_any(column, tokens):
        from sqlalchemy import or_
        return or_(column.ilike(f"%{t}%") for t in tokens)

    results: List[Dict[str, Any]] = []
    # 1. 物料
    try:
        rows = db.query(models.Material).filter(like_any(models.Material.name, tokens) |
                                                 like_any(models.Material.code, tokens)).limit(limit).all()
        for m in rows:
            results.append({"type": "物料", "id": m.id, "code": getattr(m, "code", ""),
                            "name": getattr(m, "name", ""), "summary": f"物料 {getattr(m, 'code','')} {getattr(m, 'name','')}"})
    except Exception:
        pass
    # 2. 客户
    try:
        rows = db.query(models.Customer).filter(like_any(models.Customer.name, tokens)).limit(limit).all()
        for c in rows:
            results.append({"type": "客户", "id": c.id, "code": getattr(c, "code", ""),
                            "name": getattr(c, "name", ""), "summary": f"客户 {getattr(c, 'name','')}"})
    except Exception:
        pass
    # 3. 供应商
    try:
        rows = db.query(models.Supplier).filter(like_any(models.Supplier.name, tokens)).limit(limit).all()
        for s in rows:
            results.append({"type": "供应商", "id": s.id, "code": getattr(s, "code", ""),
                            "name": getattr(s, "name", ""), "summary": f"供应商 {getattr(s, 'name','')}"})
    except Exception:
        pass
    # 4. 销售单
    try:
        rows = db.query(models.SalesOrder).filter(like_any(models.SalesOrder.order_no, tokens)).limit(limit).all()
        for so in rows:
            results.append({"type": "销售单", "id": so.id, "code": getattr(so, "order_no", ""),
                            "name": f"客户ID {getattr(so, 'customer_id','')}",
                            "summary": f"销售订单 {getattr(so, 'order_no','')} 状态 {getattr(so, 'status','')}"})
    except Exception:
        pass
    # 5. 采购单
    try:
        rows = db.query(models.PurchaseOrder).filter(like_any(models.PurchaseOrder.order_no, tokens)).limit(limit).all()
        for po in rows:
            results.append({"type": "采购单", "id": po.id, "code": getattr(po, "order_no", ""),
                            "name": f"供应商ID {getattr(po, 'supplier_id','')}",
                            "summary": f"采购订单 {getattr(po, 'order_no','')} 状态 {getattr(po, 'status','')}"})
    except Exception:
        pass
    # 6. 库存记录
    try:
        rows = db.query(models.InventoryRecord).limit(limit).all()
        for ir in rows:
            mid = getattr(ir, "material_id", "")
            mname = ""
            try:
                mat = db.query(models.Material).filter(models.Material.id == mid).first()
                if mat:
                    mname = getattr(mat, "name", "")
            except Exception:
                pass
            hit = False
            for t in tokens:
                if t and (t in (mname or "") or t in str(getattr(ir, "warehouse", ""))):
                    hit = True; break
            if hit:
                results.append({"type": "库存", "id": ir.id, "code": str(mid),
                                "name": mname,
                                "summary": f"物料 {mname} 仓库 {getattr(ir, 'warehouse','')} 数量 {getattr(ir, 'quantity', 0)}"})
    except Exception:
        pass

    return results[:limit]


# ============================================================
# 🔹 智能采购批量助手（痛点5）
# ============================================================
def batch_purchase_assistant(db: Session, requests: List[Dict[str, Any]], user_id: Any = None) -> Dict[str, Any]:
    """
    入参：[{material_id, qty, expected_price, ...}, ...]
    处理：
      1. 按供应商分组（优先物料默认供应商）
      2. 查询近 10 次采购历史单价 → 给出参考价
      3. 命中 RULE_PRICE_001 警戒线 → 标记需要审批
    """
    groups: Dict[str, List[Dict[str, Any]]] = {}  # key: supplier_id
    price_warnings = []
    rule_price = next((r for r in list_rules(enabled_only=True) if r["id"] == "RULE_PRICE_001"), None)
    threshold_rate = (rule_price or {}).get("logic", {}).get("threshold_rate", 0.15)

    for req in requests:
        mid = req.get("material_id")
        if not mid:
            continue
        mat = db.query(models.Material).filter(models.Material.id == mid).first()
        if not mat:
            continue
        default_supplier = req.get("supplier_id") or getattr(mat, "default_supplier_id", None)
        sid = str(default_supplier) if default_supplier else "unspecified"

        # 历史近 10 次采购价
        history_prices: List[float] = []
        try:
            from sqlalchemy import desc
            items = (db.query(models.PurchaseOrderItem)
                     .filter(models.PurchaseOrderItem.material_id == mid)
                     .order_by(desc(models.PurchaseOrderItem.id))
                     .limit(10).all())
            history_prices = [float(i.unit_price or 0) for i in items if getattr(i, "unit_price", 0)]
        except Exception:
            pass
        avg_price = round(sum(history_prices) / len(history_prices), 4) if history_prices else None
        ref_price = avg_price or req.get("expected_price") or getattr(mat, "purchase_price", 0)

        # 价格警戒线
        expected = req.get("expected_price") or ref_price
        warn = None
        if avg_price and expected > avg_price * (1 + threshold_rate):
            warn = f"采购价 {expected} 高于近 10 次平均价 {avg_price} 的 +{int(threshold_rate*100)}%，建议审批。"
            price_warnings.append({"material_id": mid, "warning": warn, "avg_price": avg_price, "expected": expected})

        groups.setdefault(sid, []).append({
            "material_id": mid,
            "material_code": getattr(mat, "code", ""),
            "material_name": getattr(mat, "name", ""),
            "qty": req.get("qty", 0),
            "expected_price": expected,
            "ref_price": ref_price,
            "history_avg_price": avg_price,
            "history_count": len(history_prices),
            "warning": warn,
        })

    return {
        "groups": groups,
        "need_approval": bool(price_warnings),
        "price_warnings": price_warnings,
        "group_count": len(groups),
        "item_count": sum(len(v) for v in groups.values()),
    }


# ============================================================
# 🔹 一键纠错动作链（痛点6）
# ============================================================
def build_fix_chain(db: Session, doc_type: str, doc_id: Any, changes: Dict[str, Any]) -> Dict[str, Any]:
    """
    当修改一张单据时，自动分析关联单据并生成"动作链"供用户一键执行。
    doc_type: sales_order / purchase_order / work_order / material ...
    """
    chain = []
    try:
        if doc_type == "sales_order":
            so = db.query(models.SalesOrder).filter(models.SalesOrder.id == doc_id).first()
            if so and ("customer_id" in changes or "currency" in changes or "amount" in changes):
                chain.append({
                    "id": "update_so_header", "label": "更新销售单表头字段",
                    "doc_type": "sales_order", "doc_id": doc_id,
                    "changes": {k: changes[k] for k in ["customer_id", "currency", "amount"] if k in changes},
                    "impact": "不影响下游单据",
                })
            if so and changes.get("status") in ("CANCELLED", "REJECTED"):
                # 找出关联的工单/发货单（如存在）
                chain.append({
                    "id": "cancel_linked_wo", "label": "作废关联生产工单",
                    "doc_type": "work_order", "doc_id": None,
                    "changes": {"status": "CANCELLED"},
                    "impact": "此销售单已作废，建议同步作废下游工单",
                })
        if doc_type == "material":
            if "purchase_price" in changes or "price" in changes:
                chain.append({
                    "id": "update_po_price", "label": "更新未完成采购单单价",
                    "doc_type": "purchase_order", "doc_id": None,
                    "changes": {"unit_price": changes.get("purchase_price") or changes.get("price")},
                    "impact": "同步调整该物料在未完成 PO 中的单价",
                })
                chain.append({
                    "id": "update_so_price", "label": "更新未完成销售单单价",
                    "doc_type": "sales_order", "doc_id": None,
                    "changes": {"unit_price": changes.get("price") or changes.get("purchase_price")},
                    "impact": "同步调整该物料在未完成 SO 中的单价",
                })
    except Exception:
        pass
    return {"chain": chain, "count": len(chain)}


# ============================================================
# 🔹 API 路由
# ============================================================

# ---------- 痛点1：意图解析 + 快捷指令模板 ----------
@router.post("/parse", tags=["AI副驾"])
async def api_parse_intent(body: Dict[str, Any], db: Session = Depends(get_db)):
    text = (body.get("text") or "").strip()
    user_id = body.get("user_id") or "guest"
    parsed = parse_intent(text)
    # 合并当前上下文（痛点2）
    ctx = get_context(user_id)
    # 若指令缺省一些字段，从上下文补齐
    for k, v in ctx.items():
        if k not in parsed["params"] and v is not None:
            parsed["params"].setdefault(k, v)
    description = _humanize_intent(parsed)
    return make_response(True, {
        "parsed": parsed,
        "description": description,
        "context": ctx,
    }, "意图解析完成")


# 快捷指令模板
_QUICK_TEMPLATES = [
    {"id": "new_sales", "label": "📝 新建销售订单",
     "example": "给XX客户开一张100台机器A的销售单，单价5000元", "module": "sales"},
    {"id": "new_purchase", "label": "🛒 新建采购订单",
     "example": "向XX供应商采购零件X 500个，单价20元", "module": "purchase"},
    {"id": "new_material", "label": "📦 新增物料档案",
     "example": "新增物料'零件Z'，编码Z-001，进价8元，售价15元", "module": "material"},
    {"id": "query_stock", "label": "🔍 查询库存",
     "example": "查机器A的库存有多少", "module": "inventory"},
    {"id": "query_so", "label": "🧾 查询销售单",
     "example": "查客户XX最近的销售订单", "module": "sales"},
    {"id": "finance_overview", "label": "💰 财务总览",
     "example": "看本月应收应付和利润", "module": "finance"},
]


@router.get("/quick-templates", tags=["AI副驾"])
async def api_quick_templates():
    return make_response(True, {"templates": _QUICK_TEMPLATES}, "")


# ---------- 痛点2：上下文池接口 ----------
@router.post("/context/set", tags=["上下文池"])
async def api_set_context(body: Dict[str, Any]):
    user_id = body.get("user_id") or "guest"
    key = body.get("key")
    value = body.get("value")
    if not key:
        return make_response(False, None, "缺少 key")
    set_context(user_id, key, value)
    return make_response(True, {"key": key, "value": value}, "已保存上下文")


@router.get("/context", tags=["上下文池"])
async def api_get_context(user_id: str = "guest", key: Optional[str] = None):
    return make_response(True, {
        "user_id": user_id,
        "key": key,
        "value": get_context(user_id, key),
    }, "")


@router.post("/context/clear", tags=["上下文池"])
async def api_clear_context(body: Dict[str, Any]):
    user_id = body.get("user_id") or "guest"
    key = body.get("key")
    clear_context(user_id, key)
    return make_response(True, None, "已清除上下文")


# ---------- 痛点3：全局语义搜索 ----------
@router.get("/search", tags=["语义搜索"])
async def api_semantic_search(q: str = "", limit: int = 20, db: Session = Depends(get_db)):
    results = semantic_search(db, q, limit)
    # 生成搜索快照（用 query + timestamp 作为快照 ID）
    snapshot_id = "SNAP-" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return make_response(True, {
        "snapshot_id": snapshot_id,
        "query": q,
        "count": len(results),
        "results": results,
    }, f"搜索到 {len(results)} 条结果")


# ---------- 痛点4：规则引擎 ----------
@router.get("/rules", tags=["业务规则"])
async def api_list_rules(enabled_only: bool = False):
    return make_response(True, {"rules": list_rules(enabled_only)}, "")


@router.post("/rules/{rule_id}/toggle", tags=["业务规则"])
async def api_toggle_rule(rule_id: str, body: Dict[str, Any]):
    enabled = bool(body.get("enabled", True))
    rule = toggle_rule(rule_id, enabled)
    if not rule:
        return make_response(False, None, f"规则 {rule_id} 不存在")
    return make_response(True, rule, f"已{'启用' if enabled else '停用'}规则")


@router.post("/rules", tags=["业务规则"])
async def api_add_custom_rule(body: Dict[str, Any]):
    name = body.get("name")
    if not name:
        return make_response(False, None, "缺少规则名称")
    rule = add_custom_rule({
        "name": name,
        "category": body.get("category", "general"),
        "description": body.get("description", ""),
        "logic": body.get("logic", {}),
    })
    return make_response(True, rule, "自定义规则已添加")


# ---------- 痛点5：智能采购批量助手 ----------
@router.post("/purchase/batch-assist", tags=["智能采购"])
async def api_batch_purchase_assist(body: Dict[str, Any], db: Session = Depends(get_db)):
    requests = body.get("requests") or []
    user_id = body.get("user_id") or "guest"
    if not requests:
        return make_response(False, None, "缺少采购需求列表")
    result = batch_purchase_assistant(db, requests, user_id)
    return make_response(True, result, f"已按 {result['group_count']} 个供应商分组")


# ---------- 痛点6：一键纠错动作链 ----------
@router.post("/fix-chain", tags=["纠错动作链"])
async def api_build_fix_chain(body: Dict[str, Any], db: Session = Depends(get_db)):
    doc_type = body.get("doc_type")
    doc_id = body.get("doc_id")
    changes = body.get("changes") or {}
    if not doc_type or not doc_id:
        return make_response(False, None, "缺少 doc_type 或 doc_id")
    chain = build_fix_chain(db, doc_type, doc_id, changes)
    return make_response(True, chain, f"检测到 {chain['count']} 个关联动作")


# ============================================================
# 🔹 AI 智能体：流程知识库引擎 + 任务驱动引导 + 即时问答
# ============================================================
# 流程知识库：按「业务领域 → 场景 → 步骤」三层结构存储完整操作路径
# difficulty: basic（单模块操作）/ advanced（跨模块协同）
PROCESS_LIBRARY: List[Dict[str, Any]] = [
    # ==================== 采购管理 ====================
    {
        "id": "PROC_PUR_001",
        "module": "purchase",
        "module_label": "采购管理",
        "scene": "采购入库",
        "title": "采购订单到货入库完整流程",
        "difficulty": "basic",
        "description": "从新增采购订单、审批、到货入库到生成应付凭证的完整闭环，覆盖采购核心业务路径。",
        "keywords": ["采购", "入库", "到货", "收货", "采购单", "PO"],
        "steps": [
            {"order": 1, "title": "进入采购管理模块", "instruction": "点击左侧菜单「🛒 采购管理」进入采购订单列表页。", "selector": "[onclick=\"loadModule('purchase')\"]", "target_module": "purchase", "tip": "若菜单被角色过滤隐藏，可在顶部切换角色为「全部/采购」。"},
            {"order": 2, "title": "新增采购订单", "instruction": "在采购订单列表点击「新增采购订单」按钮，打开录入表单。", "selector": "#btn-new-po, [onclick*='newPurchaseOrder'], button", "target_module": "purchase", "tip": "确保供应商和物料档案已存在。"},
            {"order": 3, "title": "选择供应商并录入明细", "instruction": "选择供应商，添加采购明细行（物料/数量/单价），系统会自动计算合计金额。", "selector": "select, input[name='supplier'], #po-supplier", "target_module": "purchase", "tip": "可用智能采购批量助手按供应商自动分组。"},
            {"order": 4, "title": "保存并审批采购单", "instruction": "点击「保存」生成采购订单，再点击「审批」将状态变更为已审核。", "selector": "#btn-save-po, [onclick*='savePurchaseOrder'], button", "target_module": "purchase", "tip": "审批后采购单才可执行到货入库。"},
            {"order": 5, "title": "到货入库", "instruction": "在采购订单列表找到该单据，点击「入库」按钮执行收货，库存自动增加。", "selector": "[onclick*='inbound'], [onclick*='入库'], button", "target_module": "purchase", "tip": "入库后可在「库存管理」查看到物料数量增加。"},
            {"order": 6, "title": "生成应付凭证（可选）", "instruction": "进入财务管理模块，根据采购入库单生成应付账款凭证。", "selector": "[onclick=\"loadModule('finance')\"]", "target_module": "finance", "tip": "跨模块协同：采购→财务。"},
        ],
    },
    {
        "id": "PROC_PUR_002",
        "module": "purchase",
        "module_label": "采购管理",
        "scene": "采购退货",
        "title": "采购退货处理流程",
        "difficulty": "advanced",
        "description": "已入库物料发现质量问题需退货，涉及采购退货单、库存退回、应付冲减的跨模块处理。",
        "keywords": ["采购退货", "退货", "退料", "采购退回"],
        "steps": [
            {"order": 1, "title": "确认退货来源单据", "instruction": "在采购管理找到原采购订单编号，作为退货依据。", "selector": "[onclick=\"loadModule('purchase')\"]", "target_module": "purchase", "tip": "记录原采购单号用于退货关联。"},
            {"order": 2, "title": "新增采购退货单", "instruction": "在采购模块新建退货单，关联原采购订单，录入退货物料和数量。", "selector": "[onclick*='return'], [onclick*='退货'], button", "target_module": "purchase", "tip": "退货数量不得超过原入库数量。"},
            {"order": 3, "title": "执行库存退回", "instruction": "审核退货单后执行库存退回操作，库存数量自动扣减。", "selector": "[onclick*='入库'], [onclick*='退库'], button", "target_module": "inventory", "tip": "确保仓库实际物料已退回供应商。"},
            {"order": 4, "title": "冲减应付账款", "instruction": "进入财务管理，根据退货单生成红字凭证冲减应付账款。", "selector": "[onclick=\"loadModule('finance')\"]", "target_module": "finance", "tip": "跨模块：采购→库存→财务。"},
        ],
    },
    # ==================== 销售管理 ====================
    {
        "id": "PROC_SAL_001",
        "module": "sales",
        "module_label": "销售管理",
        "scene": "销售到收款",
        "title": "销售到收款完整流程（从订单到凭证）",
        "difficulty": "basic",
        "recommended": True,
        "estimated_minutes": 10,
        "description": "从创建销售订单、审核、仓库发货、确认出库到财务收款生成凭证的完整闭环，覆盖销售→库存→财务跨模块主线。",
        "keywords": ["销售", "出库", "发货", "销售单", "SO", "订单", "收款", "应收", "凭证"],
        "steps": [
            {"order": 1, "title": "进入销售管理", "instruction": "请点击左侧菜单栏中的【销售管理】，进入销售模块。", "message": "好的，我将带你走完『销售到收款』完整流程。请跟随我的指引，只点击我高亮提示的位置。第一步，我们先进入销售管理。", "selector": "[onclick=\"loadModule('sales')\"], li[data-module='sales'] button", "target_module": "sales", "tip": "菜单被角色过滤隐藏时，可在顶部切换角色为『全部』。"},
            {"order": 2, "title": "点击销售订单", "instruction": "请点击【销售订单】按钮，进入销售订单列表页面。", "message": "很好！现在请点击『销售订单』，进入订单列表。", "selector": "[onclick*='salesOrder'], [onclick*='订单'], button", "target_module": "sales", "tip": "若已有列表页，此步可点击『下一步』跳过。"},
            {"order": 3, "title": "点击新增", "instruction": "请点击【新增】按钮，创建一张新的销售订单。", "message": "现在点击『新增』，打开一张空白的销售订单。", "selector": "[onclick*='new'], [onclick*='新增'], #btn-new-so, button", "target_module": "sales", "tip": "新增按钮通常在列表右上角。"},
            {"order": 4, "title": "选择客户名称", "instruction": "请点击【客户名称】下拉框，选择一位客户（示例：宏远电子）。", "message": "订单已打开。请点击『客户名称』下拉框选择客户，系统会自动带出收货地址、联系人、信用额度。", "selector": "select[name='customer'], #so-customer, select", "target_module": "sales", "tip": "若无客户档案，请先到客户管理新增。"},
            {"order": 5, "title": "添加物料行", "instruction": "请点击【物料编码】输入框，选择本次销售的产品（示例：成品A）。", "message": "客户已选。现在请点击『物料编码』单元格，选择销售产品。", "selector": "input[name='material'], input[placeholder*='物料'], .material-code, td", "target_module": "sales", "tip": "可在弹窗中双击物料快速填回。"},
            {"order": 6, "title": "填写数量和单价", "instruction": "请输入销售数量（示例：50）和销售单价（示例：100元），系统将自动计算金额。", "message": "物料已填入。请输入『数量』和『单价』，系统会自动算出金额、税额与价税合计。", "selector": "input[name='qty'], input[name='price'], input[type='number']", "target_module": "sales", "tip": "金额 = 数量 × 单价，自动计算。"},
            {"order": 7, "title": "保存销售订单", "instruction": "确认信息无误后，点击【保存】按钮，保存这张销售订单。", "message": "信息核对无误后，请点击『保存』。", "selector": "[onclick*='save'], #btn-save-so, button", "target_module": "sales", "tip": "保存成功后订单状态为『待审核』。"},
            {"order": 8, "title": "审核销售订单", "instruction": "点击【审核】按钮，审核这张销售订单。审核通过后进入待发货状态。", "message": "✅ 订单已创建。接下来进入『审核』环节，请点击『审核』。", "selector": "[onclick*='approve'], [onclick*='审核'], button", "target_module": "sales", "tip": "审核后才能执行出库发货。"},
            {"order": 9, "title": "进入仓库管理并发货", "instruction": "请点击左侧菜单【库存管理】（仓库管理），找到该订单并点击【发货】。", "message": "✅ 审核完成！订单已进入待发货状态。接下来进入『仓库发货』环节，请点击左侧【库存管理】。", "selector": "[onclick=\"loadModule('inventory')\"], li[data-module='inventory'] button", "target_module": "inventory", "tip": "跨模块：销售→库存。"},
            {"order": 10, "title": "确认出库", "instruction": "在出库确认窗口核对物料/数量/批次后，点击【确认出库】。", "message": "请点击『发货』并核对出库明细，然后点击『确认出库』。系统将扣减库存并生成销售出库单和应收单。", "selector": "[onclick*='outbound'], [onclick*='出库'], [onclick*='确认'], button", "target_module": "inventory", "tip": "出库后库存自动扣减。"},
            {"order": 11, "title": "进入财务管理收款", "instruction": "请点击左侧菜单【财务管理】，进入财务模块完成收款确认。", "message": "✅ 出库完成！系统已生成销售出库单和应收单。接下来进入最后一步——『收款与凭证』，请点击【财务管理】。", "selector": "[onclick=\"loadModule('finance')\"], li[data-module='finance'] button", "target_module": "finance", "tip": "跨模块：库存→财务。"},
            {"order": 12, "title": "确认收款生成凭证", "instruction": "点击【确认收款】，系统将自动生成记账凭证：借：银行存款 贷：应收账款。", "message": "请点击『确认收款』，系统将自动生成凭证（借：银行存款 贷：应收账款），完成全流程。", "selector": "[onclick*='receive'], [onclick*='收款'], [onclick*='确认'], button", "target_module": "finance", "tip": "🎉 收款完成，凭证已生成！"},
        ],
    },
    {
        "id": "PROC_SAL_002",
        "module": "sales",
        "module_label": "销售管理",
        "scene": "销售退货",
        "title": "销售退货处理流程",
        "difficulty": "advanced",
        "description": "客户退货处理：销售退货单录入、库存回收、应收冲减的跨模块协同。",
        "keywords": ["销售退货", "客户退货", "退货", "退款"],
        "steps": [
            {"order": 1, "title": "查找原销售订单", "instruction": "在销售管理找到原销售订单作为退货依据。", "selector": "[onclick=\"loadModule('sales')\"]", "target_module": "sales", "tip": "可用顶部全局搜索快速定位。"},
            {"order": 2, "title": "新增销售退货单", "instruction": "新建退货单关联原销售单，录入退货明细。", "selector": "[onclick*='return'], [onclick*='退货'], button", "target_module": "sales", "tip": "退货数量不得超过原出库数量。"},
            {"order": 3, "title": "库存回收", "instruction": "审核退货单后执行库存回收，库存数量增加。", "selector": "[onclick*='入库'], [onclick*='回收'], button", "target_module": "inventory", "tip": "确认退回物料已实际入库。"},
            {"order": 4, "title": "冲减应收账款", "instruction": "进入财务管理生成红字凭证冲减应收账款。", "selector": "[onclick=\"loadModule('finance')\"]", "target_module": "finance", "tip": "跨模块：销售→库存→财务。"},
        ],
    },
    # ==================== 库存管理 ====================
    {
        "id": "PROC_INV_001",
        "module": "inventory",
        "module_label": "库存管理",
        "scene": "库存盘点",
        "title": "库存盘点操作流程",
        "difficulty": "basic",
        "description": "定期盘点库存，生成盘点差异，调整账面库存数量。",
        "keywords": ["盘点", "库存", "盘库", "清点"],
        "steps": [
            {"order": 1, "title": "进入库存管理", "instruction": "点击左侧菜单进入库存管理模块查看当前库存列表。", "selector": "[onclick=\"loadModule('inventory')\"]", "target_module": "inventory", "tip": "可按仓库/物料筛选。"},
            {"order": 2, "title": "导出盘点表", "instruction": "导出当前库存清单作为盘点基线。", "selector": "[onclick*='export'], [onclick*='导出'], button", "target_module": "inventory", "tip": "也可直接在系统内录入实际数量。"},
            {"order": 3, "title": "录入盘点结果", "instruction": "逐项录入实际盘点数量，系统自动计算差异。", "selector": "input[name='actual_qty'], .qty-input", "target_module": "inventory", "tip": "差异为正=盘盈，为负=盘亏。"},
            {"order": 4, "title": "审核盘点并调整库存", "instruction": "审核后系统自动调整库存账面数量。", "selector": "[onclick*='approve'], [onclick*='审核'], button", "target_module": "inventory", "tip": "调整会生成库存变动记录。"},
        ],
    },
    {
        "id": "PROC_INV_002",
        "module": "inventory",
        "module_label": "库存管理",
        "scene": "库位调整",
        "title": "库存库位调整流程",
        "difficulty": "basic",
        "description": "物料在不同库位间转移的操作流程。",
        "keywords": ["库位", "调拨", "移库", "转移"],
        "steps": [
            {"order": 1, "title": "选择待调拨物料", "instruction": "在库存管理找到需要调拨的物料记录。", "selector": "[onclick=\"loadModule('inventory')\"]", "target_module": "inventory", "tip": "记录原库位和目标库位。"},
            {"order": 2, "title": "录入调拨单", "instruction": "新建库位调拨单，填写源库位、目标库位、数量。", "selector": "[onclick*='transfer'], [onclick*='调拨'], button", "target_module": "inventory", "tip": "调拨数量不得超过源库位现有量。"},
            {"order": 3, "title": "执行调拨", "instruction": "审核后系统自动扣减源库位、增加目标库位库存。", "selector": "[onclick*='approve'], [onclick*='执行'], button", "target_module": "inventory", "tip": "调拨不改变库存总量。"},
        ],
    },
    # ==================== 生产管理 ====================
    {
        "id": "PROC_PRD_001",
        "module": "production",
        "module_label": "生产管理",
        "scene": "工单领料",
        "title": "生产工单领料流程",
        "difficulty": "advanced",
        "description": "根据生产工单BOM进行物料领用，涉及生产、库存、成本多模块协同。",
        "keywords": ["领料", "工单", "生产", "发料", "BOM"],
        "steps": [
            {"order": 1, "title": "创建生产工单", "instruction": "进入生产管理，新建生产工单，选择产品和BOM。", "selector": "[onclick=\"loadModule('production')\"]", "target_module": "production", "tip": "确保BOM已维护。"},
            {"order": 2, "title": "审核工单并展开BOM", "instruction": "审核工单后系统按BOM展开所需物料清单。", "selector": "[onclick*='approve'], [onclick*='审核'], button", "target_module": "production", "tip": "BOM展开后可查看所需物料及数量。"},
            {"order": 3, "title": "执行领料", "instruction": "根据BOM清单执行领料，系统扣减库存原材料。", "selector": "[onclick*='pick'], [onclick*='领料'], button", "target_module": "production", "tip": "领料前确认原材料库存充足。"},
            {"order": 4, "title": "领料成本归集", "instruction": "领料成本自动归集到工单，进入成本核算。", "selector": "[onclick=\"loadModule('finance')\"]", "target_module": "finance", "tip": "跨模块：生产→库存→成本。"},
        ],
    },
    {
        "id": "PROC_PRD_002",
        "module": "production",
        "module_label": "生产管理",
        "scene": "工单完工入库",
        "title": "工单完工入库流程",
        "difficulty": "advanced",
        "description": "生产完工后将成品入库，涉及生产、库存、成本结转。",
        "keywords": ["完工", "入库", "工单", "成品", "报工"],
        "steps": [
            {"order": 1, "title": "录入完工数量", "instruction": "在生产工单录入实际完工数量和工时。", "selector": "[onclick=\"loadModule('production')\"]", "target_module": "production", "tip": "可分批报工。"},
            {"order": 2, "title": "执行完工入库", "instruction": "点击「完工入库」，成品库存自动增加。", "selector": "[onclick*='complete'], [onclick*='完工'], button", "target_module": "production", "tip": "入库数量为合格品数量。"},
            {"order": 3, "title": "成本结转", "instruction": "系统将工单归集的成本结转到成品，进入成本核算。", "selector": "[onclick=\"loadModule('finance')\"]", "target_module": "finance", "tip": "跨模块：生产→库存→成本。"},
        ],
    },
    # ==================== 财务管理 ====================
    {
        "id": "PROC_FIN_001",
        "module": "finance",
        "module_label": "财务管理",
        "scene": "凭证录入",
        "title": "会计凭证录入流程",
        "difficulty": "basic",
        "description": "手工录入会计凭证的标准操作，含借贷平衡校验。",
        "keywords": ["凭证", "录入", "会计", "记账", "分录"],
        "steps": [
            {"order": 1, "title": "进入财务管理", "instruction": "点击左侧菜单「💰 财务管理」进入凭证列表。", "selector": "[onclick=\"loadModule('finance')\"]", "target_module": "finance", "tip": "可按日期/凭证字号筛选。"},
            {"order": 2, "title": "新增凭证", "instruction": "点击「新增凭证」，填写日期、凭证字号、摘要。", "selector": "[onclick*='newVoucher'], [onclick*='新增凭证'], button", "target_module": "finance", "tip": "凭证字号建议按月连续编号。"},
            {"order": 3, "title": "录入分录", "instruction": "逐行添加借方/贷方分录，选择科目、录入金额。", "selector": "select[name='account'], input[name='amount']", "target_module": "finance", "tip": "借贷必须平衡，系统会实时校验。"},
            {"order": 4, "title": "保存并审核凭证", "instruction": "保存凭证后审核，凭证状态变为已审核。", "selector": "[onclick*='save'], [onclick*='approve'], button", "target_module": "finance", "tip": "已审核凭证不可直接修改。"},
        ],
    },
    {
        "id": "PROC_FIN_002",
        "module": "finance",
        "module_label": "财务管理",
        "scene": "月末成本分摊",
        "title": "月末成本分摊流程",
        "difficulty": "advanced",
        "description": "月末将制造费用、人工等按规则分摊到产品成本，结转销售成本。",
        "keywords": ["成本", "分摊", "月末", "结转", "制造费用"],
        "steps": [
            {"order": 1, "title": "归集期间费用", "instruction": "进入财务管理，确认本月制造费用、人工费用已全部归集。", "selector": "[onclick=\"loadModule('finance')\"]", "target_module": "finance", "tip": "检查所有工单是否已完工入库。"},
            {"order": 2, "title": "执行成本分摊", "instruction": "点击「成本分摊」按钮，系统按工单/产量分摊制造费用。", "selector": "[onclick*='allocate'], [onclick*='分摊'], button", "target_module": "finance", "tip": "分摊规则可在系统配置。"},
            {"order": 3, "title": "结转销售成本", "instruction": "根据本月销售出库自动结转销售成本，生成结转凭证。", "selector": "[onclick*='settle'], [onclick*='结转'], button", "target_module": "finance", "tip": "结转后生成主营业务成本凭证。"},
            {"order": 4, "title": "月末结账", "instruction": "确认所有凭证已审核，执行月末结账。", "selector": "[onclick*='close'], [onclick*='结账'], button", "target_module": "finance", "tip": "结账后期间锁定，不可再录入凭证。"},
        ],
    },
    # ==================== 跨境合规 ====================
    {
        "id": "PROC_CMP_001",
        "module": "compliance",
        "module_label": "跨境合规",
        "scene": "跨境合规申报",
        "title": "跨境贸易合规申报流程",
        "difficulty": "advanced",
        "description": "出口贸易的合规单证准备与申报流程，涉及单证核对、合规预警。",
        "keywords": ["跨境", "合规", "出口", "申报", "报关", "单证"],
        "steps": [
            {"order": 1, "title": "进入跨境合规模块", "instruction": "点击左侧菜单「🌍 跨境合规」查看合规预警与单证清单。", "selector": "[onclick=\"loadModule('crossborder')\"]", "target_module": "crossborder", "tip": "关注预警信息。"},
            {"order": 2, "title": "核对贸易单证", "instruction": "核对发票、装箱单、合同、提单等单证信息一致性。", "selector": "table, .doc-list", "target_module": "crossborder", "tip": "单证信息须与实际一致。"},
            {"order": 3, "title": "处理合规预警", "instruction": "逐条处理系统预警（如受限国家、双用途物项等）。", "selector": "[onclick*='resolve'], [onclick*='处理'], button", "target_module": "crossborder", "tip": "预警需逐条确认或排除。"},
            {"order": 4, "title": "生成申报资料", "instruction": "导出/生成合规申报资料包。", "selector": "[onclick*='export'], [onclick*='生成'], button", "target_module": "crossborder", "tip": "留存申报记录备查。"},
        ],
    },
    # ==================== 宏流程：新手教程推荐路线 ====================
    {
        "id": "PROC_FLOW_PUR_001",
        "module": "purchase",
        "module_label": "采购管理",
        "scene": "采购到付款",
        "title": "采购到付款完整流程（从请购到付钱）",
        "difficulty": "basic",
        "recommended": False,
        "estimated_minutes": 12,
        "description": "从采购申请、审核、生成采购订单、收货入库、三单匹配、发票确认到付款的完整闭环，约9步。",
        "keywords": ["采购", "付款", "请购", "收货", "入库", "三单匹配", "PO", "应付"],
        "steps": [
            {"order": 1, "title": "新增采购申请", "instruction": "进入采购管理，点击【采购申请】→【新增】，录入请购物料和数量。", "message": "开始『采购到付款』流程。第一步，请创建一张采购申请。", "selector": "[onclick=\"loadModule('purchase')\"], li[data-module='purchase'] button", "target_module": "purchase", "tip": "请购是采购起点。"},
            {"order": 2, "title": "审核采购申请", "instruction": "点击【审核】通过采购申请。", "message": "请审核采购申请。", "selector": "[onclick*='approve'], [onclick*='审核'], button", "target_module": "purchase", "tip": "审核后可生成采购订单。"},
            {"order": 3, "title": "选择供应商", "instruction": "为请购明细分配供应商（或用智能批量助手自动分组）。", "message": "请为采购需求选择供应商。", "selector": "select[name='supplier'], #po-supplier, select", "target_module": "purchase", "tip": "可用智能采购批量助手。"},
            {"order": 4, "title": "生成采购订单", "instruction": "点击【生成采购订单】，系统按供应商分组生成PO。", "message": "请生成采购订单。", "selector": "[onclick*='createPO'], [onclick*='生成'], button", "target_module": "purchase", "tip": "一张请购可拆为多张PO。"},
            {"order": 5, "title": "确认收货", "instruction": "到货后点击【收货/入库】确认收货。", "message": "货物到后请确认收货。", "selector": "[onclick*='inbound'], [onclick*='收货'], button", "target_module": "purchase", "tip": "可扫码入库。"},
            {"order": 6, "title": "扫码入库", "instruction": "用扫码枪扫描物料条码完成入库。", "message": "请扫码入库。", "selector": "[onclick=\"loadModule('scanning')\"], li[data-module='scanning'] button", "target_module": "scanning", "tip": "扫码枪作为HID键盘即插即用。"},
            {"order": 7, "title": "三单匹配", "instruction": "在系统核对采购订单、入库单、发票三单一致。", "message": "请核对三单匹配。", "selector": "table, [onclick*='match'], button", "target_module": "purchase", "tip": "三单一致方可付款。"},
            {"order": 8, "title": "确认发票", "instruction": "确认供应商发票并生成应付。", "message": "请确认发票。", "selector": "[onclick*='invoice'], [onclick*='发票'], button", "target_module": "invoice", "tip": "发票确认后生成应付账款。"},
            {"order": 9, "title": "确认付款", "instruction": "进入财务管理，点击【确认付款】生成付款凭证。", "message": "最后请确认付款，系统生成凭证（贷：银行存款 借：应付账款）。", "selector": "[onclick=\"loadModule('finance')\"], li[data-module='finance'] button", "target_module": "finance", "tip": "🎉 付款完成，凭证已生成！"},
        ],
    },
    {
        "id": "PROC_FLOW_PRD_001",
        "module": "production",
        "module_label": "生产管理",
        "scene": "生产到成本",
        "title": "生产到成本完整流程（从工单到分摊）",
        "difficulty": "advanced",
        "recommended": False,
        "estimated_minutes": 15,
        "description": "从创建生产工单、展开BOM、领料、报工、完工入库到约当产量法成本计算并生成成本凭证，约8步。",
        "keywords": ["生产", "工单", "BOM", "领料", "报工", "完工", "成本", "分摊", "约当产量"],
        "steps": [
            {"order": 1, "title": "创建生产工单", "instruction": "进入生产管理，新建生产工单并选择产品和BOM。", "message": "开始『生产到成本』流程。第一步，请创建生产工单。", "selector": "[onclick=\"loadModule('production')\"], li[data-module='production'] button", "target_module": "production", "tip": "确保BOM已维护。"},
            {"order": 2, "title": "展开BOM", "instruction": "审核工单后系统按BOM展开所需物料清单。", "message": "请审核工单，系统将展开BOM。", "selector": "[onclick*='approve'], [onclick*='审核'], button", "target_module": "production", "tip": "BOM展开显示所需物料。"},
            {"order": 3, "title": "生成领料单", "instruction": "根据BOM清单生成领料单。", "message": "请生成领料单。", "selector": "[onclick*='pick'], [onclick*='领料'], button", "target_module": "production", "tip": "领料数量按BOM标准用量。"},
            {"order": 4, "title": "扫码领料", "instruction": "用扫码枪扫描物料完成领料，扣减库存。", "message": "请扫码领料。", "selector": "[onclick=\"loadModule('scanning')\"], li[data-module='scanning'] button", "target_module": "scanning", "tip": "领料前确认原材料库存。"},
            {"order": 5, "title": "工单报工", "instruction": "录入实际完工数量和工时进行报工。", "message": "请录入完工数量和工时报工。", "selector": "[onclick*='report'], [onclick*='报工'], input[type='number']", "target_module": "production", "tip": "可分批报工。"},
            {"order": 6, "title": "完工入库", "instruction": "点击【完工入库】，成品库存增加。", "message": "请执行完工入库。", "selector": "[onclick*='complete'], [onclick*='完工'], button", "target_module": "production", "tip": "入库数量为合格品。"},
            {"order": 7, "title": "约当产量法成本计算", "instruction": "进入财务管理，按约当产量法计算在产品与完工产品成本。", "message": "请进入财务管理进行成本计算。", "selector": "[onclick=\"loadModule('finance')\"], li[data-module='finance'] button", "target_module": "finance", "tip": "约当产量=在产品数量×完工程度。"},
            {"order": 8, "title": "生成成本凭证", "instruction": "执行成本分摊并生成结转凭证。", "message": "请生成成本结转凭证。", "selector": "[onclick*='allocate'], [onclick*='分摊'], [onclick*='结转'], button", "target_module": "finance", "tip": "🎉 成本凭证已生成！"},
        ],
    },
    {
        "id": "PROC_FLOW_INV_001",
        "module": "inventory",
        "module_label": "库存管理",
        "scene": "库存到追溯",
        "title": "库存到追溯完整流程（从入库到盘点）",
        "difficulty": "basic",
        "recommended": False,
        "estimated_minutes": 8,
        "description": "从扫码入库、批次分配、库位上架、先进先出出库、全链路追溯到盘点执行，约6步。",
        "keywords": ["库存", "入库", "批次", "库位", "FIFO", "先进先出", "追溯", "盘点"],
        "steps": [
            {"order": 1, "title": "扫码入库", "instruction": "进入扫码录入模块，扫描物料条码完成入库。", "message": "开始『库存到追溯』流程。第一步，请扫码入库。", "selector": "[onclick=\"loadModule('scanning')\"], li[data-module='scanning'] button", "target_module": "scanning", "tip": "扫码枪即插即用。"},
            {"order": 2, "title": "批次分配", "instruction": "为入库物料分配批次号。", "message": "请为物料分配批次号。", "selector": "input[name='batch'], [onclick*='batch'], button", "target_module": "inventory", "tip": "批次用于追溯。"},
            {"order": 3, "title": "库位上架", "instruction": "将物料上架到指定库位。", "message": "请将物料上架到库位。", "selector": "input[name='location'], select[name='location'], button", "target_module": "inventory", "tip": "记录库位便于查找。"},
            {"order": 4, "title": "先进先出出库", "instruction": "出库时系统按FIFO自动分配批次。", "message": "请执行出库，系统按先进先出分配批次。", "selector": "[onclick*='outbound'], [onclick*='出库'], button", "target_module": "inventory", "tip": "FIFO保证先入库先出库。"},
            {"order": 5, "title": "全链路追溯查询", "instruction": "输入批次号查询物料的入库、出库、生产全链路记录。", "message": "请输入批次号查询全链路追溯。", "selector": "input[placeholder*='批次'], input[type='text'], button", "target_module": "inventory", "tip": "追溯覆盖全生命周期。"},
            {"order": 6, "title": "盘点任务执行", "instruction": "执行盘点任务，录入实际数量，系统计算差异并调整。", "message": "🎉 最后请执行盘点任务。", "selector": "[onclick*='盘点'], [onclick*='stocktake'], button", "target_module": "inventory", "tip": "差异为正=盘盈，为负=盘亏。"},
        ],
    },
    {
        "id": "PROC_FLOW_FIN_001",
        "module": "finance",
        "module_label": "财务管理",
        "scene": "财务到报表",
        "title": "财务到报表完整流程（从凭证到三大表）",
        "difficulty": "advanced",
        "recommended": False,
        "estimated_minutes": 12,
        "description": "从凭证录入、审核、过账、总账查询到生成资产负债表、利润表、现金流量表，约7步。",
        "keywords": ["财务", "凭证", "过账", "总账", "资产负债表", "利润表", "现金流量表", "三大表"],
        "steps": [
            {"order": 1, "title": "凭证中心", "instruction": "进入财务管理，打开凭证中心。", "message": "开始『财务到报表』流程。第一步，请进入凭证中心。", "selector": "[onclick=\"loadModule('finance')\"], li[data-module='finance'] button", "target_module": "finance", "tip": "凭证是财务基础。"},
            {"order": 2, "title": "录入凭证", "instruction": "点击【新增凭证】，录入借贷分录。", "message": "请录入凭证分录。", "selector": "[onclick*='newVoucher'], [onclick*='新增凭证'], button", "target_module": "finance", "tip": "借贷必须平衡。"},
            {"order": 3, "title": "审核凭证", "instruction": "点击【审核】凭证。", "message": "请审核凭证。", "selector": "[onclick*='approve'], [onclick*='审核'], button", "target_module": "finance", "tip": "审核后凭证不可直接修改。"},
            {"order": 4, "title": "过账", "instruction": "点击【过账】，将凭证记入总账。", "message": "请执行过账。", "selector": "[onclick*='post'], [onclick*='过账'], button", "target_module": "finance", "tip": "过账后影响总账余额。"},
            {"order": 5, "title": "总账查询", "instruction": "在总账查询科目余额和发生额。", "message": "请查询总账。", "selector": "[onclick*='ledger'], [onclick*='总账'], button", "target_module": "finance", "tip": "总账是报表数据来源。"},
            {"order": 6, "title": "生成资产负债表/利润表", "instruction": "点击【资产负债表】和【利润表】生成报表。", "message": "请生成资产负债表和利润表。", "selector": "[onclick*='balance'], [onclick*='资产'], [onclick*='利润'], button", "target_module": "finance", "tip": "报表按总账自动汇总。"},
            {"order": 7, "title": "生成现金流量表", "instruction": "点击【现金流量表】生成报表。", "message": "🎉 请生成现金流量表，完成全流程。", "selector": "[onclick*='cashflow'], [onclick*='现金流'], button", "target_module": "finance", "tip": "三大报表齐全！"},
        ],
    },
]

# 模块中英文映射，供问答匹配使用
_MODULE_ALIASES = {
    "采购": "purchase", "进货": "purchase", "PO": "purchase",
    "销售": "sales", "出货": "sales", "SO": "sales", "订单": "sales",
    "库存": "inventory", "仓库": "inventory", "存货": "inventory",
    "生产": "production", "工单": "production", "制造": "production", "WO": "production",
    "财务": "finance", "凭证": "finance", "记账": "finance", "账务": "finance",
    "合规": "compliance", "跨境": "compliance", "报关": "compliance", "出口": "compliance",
}


def list_processes(module: Optional[str] = None, difficulty: Optional[str] = None) -> List[Dict[str, Any]]:
    """列出流程（可按模块/难度过滤），返回精简信息（不含 steps 详情）"""
    result = []
    for p in PROCESS_LIBRARY:
        if module and p["module"] != module:
            continue
        if difficulty and p["difficulty"] != difficulty:
            continue
        result.append({
            "id": p["id"],
            "module": p["module"],
            "module_label": p["module_label"],
            "scene": p["scene"],
            "title": p["title"],
            "difficulty": p["difficulty"],
            "description": p["description"],
            "keywords": p.get("keywords", []),
            "step_count": len(p.get("steps", [])),
            "recommended": p.get("recommended", False),
            "estimated_minutes": p.get("estimated_minutes"),
        })
    return result


def get_process(process_id: str) -> Optional[Dict[str, Any]]:
    """获取单个流程的完整步骤详情"""
    for p in PROCESS_LIBRARY:
        if p["id"] == process_id:
            return p
    return None


def answer_question(question: str) -> Dict[str, Any]:
    """
    即时问答：基于关键词匹配知识库，返回图文并茂的操作说明。
    匹配逻辑：模块别名命中 + 关键词命中 → 综合得分排序
    """
    q = (question or "").strip()
    if not q:
        return {"matched": [], "answer": "请输入您的问题，例如：如何处理采购退货？", "question": q}

    scored = []
    for p in PROCESS_LIBRARY:
        score = 0
        reasons = []
        # 模块别名匹配
        for alias, mod in _MODULE_ALIASES.items():
            if alias in q and mod == p["module"]:
                score += 3
                reasons.append(f"命中模块「{p['module_label']}」")
        # 关键词匹配
        for kw in p.get("keywords", []):
            if kw in q:
                score += 2
                reasons.append(f"命中关键词「{kw}」")
        # 标题/场景匹配
        if p["title"] and p["title"] in q:
            score += 4
            reasons.append("命中流程标题")
        if p["scene"] and p["scene"] in q:
            score += 3
            reasons.append(f"命中场景「{p['scene']}」")
        if score > 0:
            scored.append({"process": p, "score": score, "reasons": reasons})

    scored.sort(key=lambda x: -x["score"])
    matched = scored[:3]  # 最多返回3个相关流程

    if not matched:
        return {
            "matched": [],
            "answer": f"未找到与「{q}」直接匹配的流程。可尝试关键词：采购入库、销售出库、工单领料、凭证录入、月末成本分摊、跨境合规等。",
            "question": q,
        }

    # 生成图文回答
    lines = [f"📌 关于「{q}」，为您找到 {len(matched)} 个相关流程：", ""]
    for i, m in enumerate(matched, 1):
        p = m["process"]
        lines.append(f"{i}. 【{p['module_label']} · {p['scene']}】{p['title']}")
        lines.append(f"   难度：{'基础' if p['difficulty']=='basic' else '进阶（跨模块协同）'} | 共 {len(p['steps'])} 步")
        lines.append(f"   {p['description']}")
        lines.append(f"   操作步骤：")
        for s in p["steps"]:
            lines.append(f"     步骤{s['order']}：{s['title']} — {s['instruction']}")
            if s.get("tip"):
                lines.append(f"       💡 {s['tip']}")
        lines.append("")
    lines.append("💡 提示：可在「新手教程」中选择对应流程，点击「开始引导」启动箭头指引模式，手把手完成操作。")

    return {
        "matched": [{"id": m["process"]["id"], "title": m["process"]["title"],
                      "module_label": m["process"]["module_label"], "scene": m["process"]["scene"],
                      "score": m["score"], "reasons": m["reasons"]} for m in matched],
        "answer": "\n".join(lines),
        "question": q,
    }


# ---------- AI智能体：流程知识库 ----------
@router.get("/processes", tags=["AI智能体"])
async def api_list_processes(module: Optional[str] = None, difficulty: Optional[str] = None):
    """列出所有流程，支持按 module / difficulty 过滤"""
    procs = list_processes(module=module, difficulty=difficulty)
    # 按模块分组返回，方便前端树形展示
    modules_map: Dict[str, Dict[str, Any]] = {}
    for p in procs:
        mod = p["module"]
        if mod not in modules_map:
            modules_map[mod] = {"module": mod, "module_label": p["module_label"], "processes": []}
        modules_map[mod]["processes"].append(p)
    return make_response(True, {
        "total": len(procs),
        "modules": list(modules_map.values()),
        "all": procs,
    }, f"共 {len(procs)} 个流程")


@router.get("/processes/{process_id}", tags=["AI智能体"])
async def api_get_process(process_id: str):
    """获取单个流程的详细步骤"""
    p = get_process(process_id)
    if not p:
        return make_response(False, None, f"流程 {process_id} 不存在")
    return make_response(True, p, f"流程「{p['title']}」共 {len(p['steps'])} 步")


@router.post("/ask", tags=["AI智能体"])
def api_ask(body: Dict[str, Any], db: Session = Depends(get_db)):
    """即时问答：优先调用大模型自由回答；同时返回知识库匹配的关联流程。
    请求体：{ "question": "...", "use_ai": true/false, "context": "业务数据文本" }
    返回：{ "answer": "回答文本", "matched": [...], "ai": true/false, "model": "..." }"""
    question = (body.get("question") or "").strip()
    if not question:
        return make_response(True, {"matched": [], "answer": "请输入您的问题", "ai": False}, "请输入问题")

    # 业务上下文（如成本性态分析/成本决策的当前数据），用于让模型基于真实数据作答
    context = (body.get("context") or "").strip()

    # 成本决策联动：mode=extract 时只做数据提取，返回结构化 JSON 供前端一键填入成本决策
    if (body.get("mode") or "").strip() == "extract":
        src = (body.get("source") or "").strip()
        decision, mdl, err = _extract_decision(db, src, context)
        return make_response(True, {
            "answer": "", "matched": [], "decision": decision,
            "ai": bool(decision), "model": mdl, "ai_error": err,
        }, "AI 已提取决策数据" if decision else "未提取到可填入的数据")

    # 知识库匹配（始终执行，用于推荐相关流程）
    kb = answer_question(question)

    # 默认使用 AI；显式传 use_ai=False 时只走知识库
    use_ai = body.get("use_ai")
    use_ai = True if use_ai is None else bool(use_ai)
    if not use_ai:
        return make_response(True, {**kb, "ai": False}, f"已为您匹配 {len(kb.get('matched', []))} 个相关流程")

    ai_text, ai_model, ai_err = _ask_llm_free(db, question, kb, context)
    if ai_text:
        return make_response(True, {
            "answer": ai_text,
            "matched": kb.get("matched", []),
            "ai": True,
            "model": ai_model,
        }, "AI 已回复")
    # AI 不可用时回退到知识库答案，并附上失败原因
    return make_response(True, {
        **kb,
        "ai": False,
        "ai_error": ai_err,
    }, kb.get("answer", "")[:60] if kb.get("matched") else "AI 未启用，已返回知识库结果")


def _ask_llm_free(db: Session, question: str, kb: Dict[str, Any], context: str = ""):
    """调用大模型进行自由问答。返回 (回答文本, 模型名, 错误信息)。
    context 为可选的业务数据文本（如成本性态分析、成本决策的当前值），
    存在时模型需基于这些真实数据完成计算与分析，数据不足时须向用户提问。"""
    import json as _json, urllib.request, urllib.error
    try:
        from .finance import _get_ai_config, _build_chat_url
    except Exception as e:
        return None, None, f"AI 配置模块不可用：{e}"

    cfg = _get_ai_config(db)
    api_key, base_url, model = cfg["api_key"], cfg["base_url"], cfg["model"]
    if not api_key:
        return None, None, "未配置 AI 接口（可在财务中心右上角 🔑 配置）"

    # 把知识库命中的流程作为参考资料，帮助模型给出贴合本系统的操作说明
    ref_lines = []
    for m in (kb.get("matched") or [])[:3]:
        ref_lines.append(f"- 【{m.get('module_label')} · {m.get('scene')}】{m.get('title')}")
    ref = "\n".join(ref_lines) if ref_lines else "（知识库无直接匹配的流程）"

    # 业务上下文限长，避免超出模型上下文
    ctx = (context or "").strip()
    if len(ctx) > 6000:
        ctx = ctx[:6000] + "\n…（数据过长已截断）"

    sys_role = (
        "你是一位 ERP 系统实施与财务管理专家，服务于一套采购、销售、库存、生产、财务一体化的中小企业 ERP 系统。"
        "请用中文、以自然流畅的书面语回答用户问题。"
        "要求：不使用任何表格（用文字分点叙述，每点说明完整，讲清做法与原因）；"
        "不使用 emoji；回答要具体、可操作，涉及本系统操作时给出清晰的步骤说明；"
        "如果问题与 ERP 或财务无关，也正常作答但保持简洁。"
        "【最高优先级】严禁输出任何思考过程、推理草稿、内心独白或英文草稿，"
        "不要以『让我分析』『Hmm』『首先』『好的』等过渡语开头，直接从最终中文答案正文开始写，全文必须使用中文。"
    )
    if ctx:
        sys_role += (
            "【本轮任务】用户提供了当前管理会计数据，你必须基于这些真实数据完成计算与分析，"
            "不得自行编造数据；每一步计算都要写明所用公式与代入的数值，并给出结论性建议。"
            "若用户问题所需的关键数据在【当前业务数据】中没有提供，"
            "请在回答的最后单独列出『需要您补充的信息』，用简短问句逐条列出，不要臆造。"
            "分析口径：变动成本法下单位产品成本仅含直接材料、直接人工、变动制造费用；"
            "完全成本法下单位产品成本还包含单位固定制造费用；"
            "固定制造费用、管理费用、销售费用、财务费用属于期间费用（或固定成本）。"
        )
    parts = [f"用户问题：{question}"]
    if ctx:
        parts.append(f"【当前业务数据（真实值，请据此计算）】\n{ctx}")
    parts.append(f"【本系统知识库中可能相关的既有流程，仅供参考，可结合使用】\n{ref}")
    user_content = "\n\n".join(parts)
    messages = [
        {"role": "system", "content": sys_role},
        {"role": "user", "content": user_content},
    ]
    try:
        # 注意：本模型为推理模型，思维链会先消耗 token，max_tokens 过小会导致正文 content 为空
        payload = _json.dumps({
            "model": model, "messages": messages,
            "max_tokens": 8000, "temperature": 0.4 if ctx else 0.6,
        }, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            _build_chat_url(base_url),
            data=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = _json.loads(resp.read().decode("utf-8"))
            msg = (result.get("choices") or [{}])[0].get("message") or {}
            text = (msg.get("content") or "").strip()
            if not text:
                # 推理模型可能思考超时：不把英文思维链当作正文返回
                text = "AI 本次未生成正文（思考超时），请稍后重试，或把问题说得更聚焦一些。"
            return (text or None), result.get("model", model), None
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")[:200]
        hint = ""
        if e.code == 401: hint = "Key 无效"
        elif e.code == 402: hint = "账户余额不足"
        elif e.code == 404: hint = "接口地址或模型名不对"
        return None, None, f"AI 调用失败（HTTP {e.code}）{hint}"
    except Exception as e:
        return None, None, f"AI 调用异常：{e}"


# 决策数据提取：把一段问答原文里的数字整理成「成本决策」模块可直接填入的 JSON
_EXTRACT_SCHEMA = """{
  "scenario": "A 或 B 或 C 或 ALL 或 null（A=特殊订单是否接受；B=零部件自制还是外购；C=旧设备是否更新）",
  "opportunity": [{"name": "方案名称", "benefit": 该方案预期收益数字, "selected": true 表示建议采用的方案}],
  "sunk": [{"name": "已发生且无法收回的项目名称", "amount": 金额数字}],
  "out_of_pocket": {"total_cost": 需付现总成本数字, "depreciation": 其中折旧数字, "amortization": 其中摊销数字},
  "marginal": {"q1": 低点产量, "tc1": 低点总成本, "q2": 高点产量, "tc2": 高点总成本, "capacity": 产能极限产量},
  "quote": {"price": 单位报价数字, "qty": 订单数量, "idle_capacity": 闲置产能数量},
  "reason": "一句话说明上面每个数字分别取自原文的哪句话"
}"""


def _extract_decision(db: Session, source: str, context: str = ""):
    """把「问题原文 + AI 结论」中的决策数字提取成 JSON。
    返回 (dict|None, 模型名, 错误信息)。只做提取，不生成新结论，避免编造数字。"""
    import json as _json, re as _re, urllib.request, urllib.error
    if not source:
        return None, None, "缺少待提取的原文"
    try:
        from .finance import _get_ai_config, _build_chat_url
    except Exception as e:
        return None, None, f"AI 配置模块不可用：{e}"

    cfg = _get_ai_config(db)
    api_key, base_url, model = cfg["api_key"], cfg["base_url"], cfg["model"]
    if not api_key:
        return None, None, "未配置 AI 接口"

    src = source[:9000]
    sys_role = (
        "你是一个严谨的数据提取器，只负责把给定文本里已经明确出现的数字整理成 JSON，不做任何新的计算或推断。"
        "【最高优先级】严禁输出思考过程、推理草稿、解释说明、前言后语，你的整个回复必须是一个 JSON 对象。"
        "JSON 结构如下（字段名必须完全一致）：\n" + _EXTRACT_SCHEMA + "\n"
        "硬性规则："
        "① 只填文本中真实出现的数字，绝不编造、绝不用示例数字；"
        "② 文本中未涉及的字段一律写 null；"
        "③ opportunity 需要至少 2 个互斥方案才有意义，只有一个方案时写 null；"
        "④ out_of_pocket 只在原文明确提到「需付现/需支付现金/折旧/摊销」时才填写，"
        "普通的『成本费用』『总成本』不算付现成本，此时写 null；"
        "⑤ sunk 只在原文明确说明某笔支出「已发生且无法收回/已经花掉」时才填写；"
        "⑥ marginal 只在原文给出两组「产量 + 总成本」或明确提到高低点法时才填写；"
        "⑦ quote 只在原文给出单位报价且涉及订单时才填写；"
        "⑧ 数字不要千分位分隔符、不要货币符号、不要单位；"
        "⑨ 不要用 ``` 代码围栏包裹，直接输出 JSON。"
    )
    parts = [f"【待提取文本】\n{src}"]
    if context:
        parts.append(f"【当前系统已有数据（仅供字段对齐参考，不要照抄）】\n{context[:2000]}")
    messages = [{"role": "system", "content": sys_role},
                {"role": "user", "content": "\n\n".join(parts)}]
    try:
        payload = _json.dumps({
            "model": model, "messages": messages,
            "max_tokens": 8000, "temperature": 0.1,
        }, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            _build_chat_url(base_url),
            data=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = _json.loads(resp.read().decode("utf-8"))
            msg = (result.get("choices") or [{}])[0].get("message") or {}
            text = (msg.get("content") or "").strip()
    except urllib.error.HTTPError as e:
        return None, None, f"AI 调用失败（HTTP {e.code}）"
    except Exception as e:
        return None, None, f"AI 调用异常：{e}"

    if not text:
        return None, result.get("model", model), "AI 未返回内容"
    # 容错：截取第一个 { 到最后一个 }，兼容模型误加围栏或前言
    i, j = text.find("{"), text.rfind("}")
    if i < 0 or j <= i:
        return None, result.get("model", model), "AI 未返回 JSON"
    raw = text[i:j + 1]
    raw = _re.sub(r"^```(?:json)?|```$", "", raw, flags=_re.I | _re.M).strip()
    try:
        data = _json.loads(raw)
    except Exception:
        return None, result.get("model", model), "AI 返回的 JSON 无法解析"
    if not isinstance(data, dict):
        return None, result.get("model", model), "AI 返回的不是 JSON 对象"
    # 归一化：把非字典/非列表的噪声字段清成 None
    for k in ("opportunity", "sunk"):
        if data.get(k) is not None and not isinstance(data.get(k), list):
            data[k] = None
    for k in ("out_of_pocket", "marginal", "quote"):
        if data.get(k) is not None and not isinstance(data.get(k), dict):
            data[k] = None
    # 全空的子对象直接丢掉，避免前端显示一堆 0
    for k in ("out_of_pocket", "marginal", "quote"):
        sub = data.get(k)
        if isinstance(sub, dict):
            if all(v is None for v in sub.values()):
                data[k] = None
            else:
                data[k] = {sk: sv for sk, sv in sub.items() if sv is not None}
    data = {k: v for k, v in data.items() if v is not None}
    return (data or None), result.get("model", model), None


# ---------- AI智能体：模块/难度元数据 ----------
@router.get("/meta", tags=["AI智能体"])
async def api_ai_meta():
    """返回流程知识库的模块与难度维度，供前端筛选"""
    modules = {}
    for p in PROCESS_LIBRARY:
        mod = p["module"]
        if mod not in modules:
            modules[mod] = {"module": mod, "module_label": p["module_label"],
                            "basic": 0, "advanced": 0, "total": 0}
        modules[mod][p["difficulty"]] = modules[mod].get(p["difficulty"], 0) + 1
        modules[mod]["total"] += 1
    return make_response(True, {
        "modules": list(modules.values()),
        "difficulties": [
            {"value": "basic", "label": "基础流程", "desc": "单模块操作，适合新手入门"},
            {"value": "advanced", "label": "进阶流程", "desc": "跨模块协同，适合进阶学习"},
        ],
    }, "")
