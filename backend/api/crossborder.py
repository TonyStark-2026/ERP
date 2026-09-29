from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
import urllib.request
import json

from .. import crud, schemas, models
from ..database import get_db
from ..app import make_response

router = APIRouter()

EXCHANGE_RATES = {
    "USD": 7.24,
    "EUR": 7.86,
    "GBP": 9.12,
    "JPY": 0.048,
    "SGD": 5.28,
    "THB": 0.20,
    "MYR": 1.48,
    "MXN": 0.30,
    "AUD": 4.65
}

TAX_ID_EXPIRY_ALERT_DAYS = 30

@router.get("/exchange-rates", tags=["跨境合规"])
def get_exchange_rates(base_currency: str = "CNY", currencies: Optional[str] = None, db: Session = Depends(get_db)):
    target_currencies = currencies.split(",") if currencies else list(EXCHANGE_RATES.keys())
    
    db_rates = crud.get_exchange_rates(db)
    db_rate_map = {r.currency: r.rate for r in db_rates}
    
    rates = {}
    for currency in target_currencies:
        rate = db_rate_map.get(currency, EXCHANGE_RATES.get(currency, 1.0))
        rates[currency] = rate
    
    return make_response(True, {
        "base_currency": base_currency,
        "rates": rates,
        "updated_at": datetime.datetime.now().isoformat()
    }, "查询成功")

@router.post("/exchange-rates/update", tags=["跨境合规"])
def update_exchange_rates(db: Session = Depends(get_db)):
    try:
        with urllib.request.urlopen("https://api.exchangerate-api.com/v4/latest/CNY", timeout=10) as response:
            data = json.loads(response.read().decode())
        
        if "rates" in data:
            for currency, rate in data["rates"].items():
                db_rate = crud.get_exchange_rate(db, currency=currency)
                if db_rate:
                    db_rate.rate = rate
                    db_rate.updated_at = datetime.datetime.now()
                else:
                    crud.create_exchange_rate(db, schemas.ExchangeRateCreate(
                        currency=currency,
                        rate=rate
                    ))
            
            db.commit()
            return make_response(True, {"updated_count": len(data["rates"])}, "汇率更新成功")
        else:
            return make_response(False, None, "API返回数据格式错误", "50000")
    except Exception as e:
        return make_response(False, None, f"获取汇率失败: {str(e)}", "50000")

@router.post("/tax-estimate", tags=["跨境合规"])
def estimate_tax(request: schemas.TaxEstimateRequest, db: Session = Depends(get_db)):
    db_hs_code = crud.get_hs_code(db, hs_code=request.hs_code)
    if db_hs_code is None:
        return make_response(False, None, "HS编码不存在", "40002")
    
    db_tax_rule = crud.get_country_tax_rule(db, country_code=request.country_code)
    if db_tax_rule is None:
        return make_response(False, None, "目的国税制规则不存在", "40002")
    
    db_rate = crud.get_exchange_rate(db, currency=request.currency)
    exchange_rate = db_rate.rate if db_rate else EXCHANGE_RATES.get(request.currency, 1.0)
    declared_value_cny = request.declared_value * exchange_rate
    
    import_tax_rate = float(db_tax_rule.import_tax_rate) if db_tax_rule.import_tax_rate else 0.0
    vat_rate = float(db_tax_rule.vat_rate) if db_tax_rule.vat_rate else 0.0
    
    tax_free_threshold = float(db_tax_rule.tax_free_threshold) if db_tax_rule.tax_free_threshold else 0.0
    
    total_tax = 0
    import_tax = 0
    vat = 0
    
    if declared_value_cny > tax_free_threshold:
        import_tax = declared_value_cny * import_tax_rate
        vat = (declared_value_cny + import_tax) * vat_rate
        total_tax = import_tax + vat
    
    result = {
        "hs_code": request.hs_code,
        "country_code": request.country_code,
        "country_name": db_tax_rule.country_name,
        "declared_value": request.declared_value,
        "currency": request.currency,
        "exchange_rate": exchange_rate,
        "declared_value_cny": round(declared_value_cny, 2),
        "tax_free_threshold": round(tax_free_threshold, 2),
        "exceeds_threshold": declared_value_cny > tax_free_threshold,
        "import_tax_rate": import_tax_rate,
        "vat_rate": vat_rate,
        "import_tax": round(import_tax, 2),
        "vat": round(vat, 2),
        "total_tax": round(total_tax, 2),
        "total_tax_cny": round(total_tax, 2)
    }
    
    return make_response(True, result, "计算完成")

@router.post("/cost-split", tags=["跨境合规"])
def split_costs(request: schemas.CostSplitRequest, db: Session = Depends(get_db)):
    incoterm = request.incoterm.upper()
    
    db_rate = crud.get_exchange_rate(db, currency=request.currency)
    exchange_rate = db_rate.rate if db_rate else EXCHANGE_RATES.get(request.currency, 1.0)
    
    domestic_cost_cny = request.domestic_cost * exchange_rate
    international_cost_cny = (request.international_freight + request.insurance) * exchange_rate
    
    tax_result = None
    if request.hs_code and request.country_code:
        tax_result = estimate_tax(schemas.TaxEstimateRequest(
            hs_code=request.hs_code,
            country_code=request.country_code,
            declared_value=request.declared_value,
            currency=request.currency
        ), db)
        tax_amount = tax_result["data"].get("total_tax", 0) if tax_result["success"] else 0
    else:
        tax_amount = 0
    
    if incoterm == "DDP":
        inventory_cost = domestic_cost_cny + international_cost_cny + tax_amount
        payable_by_customer = 0
        tax_treatment = "计入存货成本"
    elif incoterm == "DAP":
        inventory_cost = domestic_cost_cny + international_cost_cny
        payable_by_customer = tax_amount
        tax_treatment = "代收代付"
    elif incoterm == "CIF":
        inventory_cost = domestic_cost_cny + international_cost_cny
        payable_by_customer = tax_amount
        tax_treatment = "代收代付"
    else:
        inventory_cost = domestic_cost_cny
        payable_by_customer = international_cost_cny + tax_amount
        tax_treatment = "客户承担"
    
    result = {
        "incoterm": incoterm,
        "currency": request.currency,
        "exchange_rate": exchange_rate,
        "domestic_cost": request.domestic_cost,
        "domestic_cost_cny": round(domestic_cost_cny, 2),
        "international_freight": request.international_freight,
        "insurance": request.insurance,
        "international_cost_cny": round(international_cost_cny, 2),
        "estimated_tax": round(tax_amount, 2),
        "inventory_cost": round(inventory_cost, 2),
        "payable_by_customer": round(payable_by_customer, 2),
        "tax_treatment": tax_treatment,
        "breakdown": {
            "国内段成本": round(domestic_cost_cny, 2),
            "国际段成本": round(international_cost_cny, 2),
            "预估税费": round(tax_amount, 2)
        }
    }
    
    return make_response(True, result, "成本拆分完成")

@router.get("/tax-id-alerts", tags=["跨境合规"])
def get_tax_id_alerts(days_before_expiry: int = 30, db: Session = Depends(get_db)):
    today = datetime.date.today()
    threshold_date = today + datetime.timedelta(days=days_before_expiry)
    
    all_tax_ids = []
    
    customers = crud.get_customers(db)
    for customer in customers:
        if customer.foreign_tax_id and customer.tax_id_expiry_date:
            days_left = (customer.tax_id_expiry_date - today).days
            if days_left <= days_before_expiry:
                all_tax_ids.append({
                    "entity_id": customer.id,
                    "entity_name": customer.name,
                    "entity_type": "customer",
                    "tax_id": customer.foreign_tax_id,
                    "country_code": customer.country_code,
                    "expiry_date": customer.tax_id_expiry_date.isoformat(),
                    "days_left": days_left,
                    "alert_level": "HIGH" if days_left <= 0 else "MEDIUM",
                    "message": f"客户{customer.name}的{customer.country_code}税号即将到期"
                })
    
    suppliers = crud.get_suppliers(db)
    for supplier in suppliers:
        if supplier.foreign_tax_id and supplier.tax_id_expiry_date:
            days_left = (supplier.tax_id_expiry_date - today).days
            if days_left <= days_before_expiry:
                all_tax_ids.append({
                    "entity_id": supplier.id,
                    "entity_name": supplier.name,
                    "entity_type": "supplier",
                    "tax_id": supplier.foreign_tax_id,
                    "country_code": supplier.country_code,
                    "expiry_date": supplier.tax_id_expiry_date.isoformat(),
                    "days_left": days_left,
                    "alert_level": "HIGH" if days_left <= 0 else "MEDIUM",
                    "message": f"供应商{supplier.name}的{supplier.country_code}税号即将到期"
                })
    
    all_tax_ids.sort(key=lambda x: x["days_left"])
    
    return make_response(True, all_tax_ids, "税务预警查询成功")

@router.post("/hs-validate", tags=["跨境合规"])
def validate_hs_code(hs_code: str, country_code: str = None, db: Session = Depends(get_db)):
    db_hs_code = crud.get_hs_code(db, hs_code=hs_code)
    
    if db_hs_code is None:
        return make_response(False, None, "HS编码不存在于数据库中", "40002")
    
    required_fields = []
    if country_code:
        db_tax_rule = crud.get_country_tax_rule(db, country_code=country_code)
        if db_tax_rule:
            required_fields = ["商品描述", "数量", "单价", "原产地"]
            
            if country_code in ["US", "CA", "AU"]:
                required_fields.append("制造商信息")
            if country_code in ["EU", "DE", "FR", "UK"]:
                required_fields.append("EC编号")
            if country_code in ["MX", "BR"]:
                required_fields.append("海关编码")
    
    result = {
        "valid": True,
        "hs_code": hs_code,
        "description_cn": db_hs_code.description_cn,
        "description_en": db_hs_code.description_en,
        "unit": db_hs_code.unit,
        "required_fields": required_fields,
        "country_specific_requirements": country_code is not None
    }
    
    return make_response(True, result, "校验完成")

@router.post("/hs-codes", tags=["跨境合规"])
def create_hs_code(hs_code: schemas.HsCodeCreate, db: Session = Depends(get_db)):
    db_hs = crud.get_hs_code(db, hs_code=hs_code.hs_code)
    if db_hs:
        return make_response(False, None, "HS编码已存在", "40003")
    
    created = crud.create_hs_code(db, hs_code)
    return make_response(True, created, "创建成功")

@router.get("/hs-codes", tags=["跨境合规"])
def list_hs_codes(skip: int = 0, limit: int = 100, search: str = None, db: Session = Depends(get_db)):
    codes = crud.get_hs_codes(db, skip=skip, limit=limit, search=search)
    total = crud.get_hs_codes_count(db, search=search)
    return make_response(True, {"items": codes, "total": total}, "查询成功")

@router.post("/country-tax-rules", tags=["跨境合规"])
def create_country_tax_rule(rule: schemas.CountryTaxRuleCreate, db: Session = Depends(get_db)):
    db_rule = crud.get_country_tax_rule(db, country_code=rule.country_code)
    if db_rule:
        return make_response(False, None, "国家税制规则已存在", "40003")
    
    created = crud.create_country_tax_rule(db, rule)
    return make_response(True, created, "创建成功")

@router.get("/country-tax-rules", tags=["跨境合规"])
def list_country_tax_rules(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    rules = crud.get_country_tax_rules(db, skip=skip, limit=limit)
    total = crud.get_country_tax_rules_count(db)
    return make_response(True, {"items": rules, "total": total}, "查询成功")


@router.get("/exchange-rates/history", tags=["跨境合规"])
def get_exchange_rate_history(currency: str, start_date: datetime.date, end_date: datetime.date, db: Session = Depends(get_db)):
    rates = crud.get_exchange_rate_history(db, currency=currency, start_date=start_date, end_date=end_date)
    
    history = []
    for rate in rates:
        history.append({
            "date": rate.created_at.date().isoformat(),
            "rate": float(rate.rate),
            "currency": rate.currency
        })
    
    if not history and currency in EXCHANGE_RATES:
        history.append({
            "date": datetime.date.today().isoformat(),
            "rate": EXCHANGE_RATES[currency],
            "currency": currency
        })
    
    return make_response(True, {
        "currency": currency,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "history": history
    }, "查询成功")


@router.get("/multi-currency-report", tags=["跨境合规"])
def get_multi_currency_report(account_set_id: int = None, period: str = "THIS_MONTH", db: Session = Depends(get_db)):
    today = datetime.date.today()
    
    if period == "THIS_MONTH":
        start_date = datetime.date(today.year, today.month, 1)
        end_date = today
    elif period == "LAST_MONTH":
        last_month = today.month - 1 if today.month > 1 else 12
        last_year = today.year if today.month > 1 else today.year - 1
        start_date = datetime.date(last_year, last_month, 1)
        end_date = datetime.date(last_year, last_month, 1) + datetime.timedelta(days=32)
        end_date = end_date - datetime.timedelta(days=end_date.day)
    elif period == "THIS_YEAR":
        start_date = datetime.date(today.year, 1, 1)
        end_date = today
    else:
        return make_response(False, None, "无效的时间周期", "40003")
    
    sales_orders = crud.get_sales_orders_by_period(db, account_set_id=account_set_id, start_date=start_date, end_date=end_date)
    
    currency_summary = {}
    
    for order in sales_orders:
        currency = order.currency or "CNY"
        total_amount = order.total_amount or 0
        foreign_amount = order.foreign_amount or 0
        
        db_rate = crud.get_exchange_rate(db, currency=currency)
        exchange_rate = db_rate.rate if db_rate else EXCHANGE_RATES.get(currency, 1.0)
        
        if currency not in currency_summary:
            currency_summary[currency] = {
                "currency": currency,
                "exchange_rate": exchange_rate,
                "total_amount_foreign": 0,
                "total_amount_cny": 0,
                "order_count": 0
            }
        
        currency_summary[currency]["total_amount_foreign"] += foreign_amount if foreign_amount > 0 else total_amount
        currency_summary[currency]["total_amount_cny"] += total_amount
        currency_summary[currency]["order_count"] += 1
    
    total_cny = sum(s["total_amount_cny"] for s in currency_summary.values())
    total_orders = sum(s["order_count"] for s in currency_summary.values())
    
    return make_response(True, {
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_orders": total_orders,
        "total_amount_cny": float(total_cny),
        "by_currency": list(currency_summary.values())
    }, "多币种报表查询成功")


@router.post("/order-convert", tags=["跨境合规"])
def convert_order_currency(order_id: int, target_currency: str, db: Session = Depends(get_db)):
    order = crud.get_sales_order(db, order_id=order_id)
    if not order:
        return make_response(False, None, "订单不存在", "40002")
    
    original_currency = order.currency or "CNY"
    
    db_rate = crud.get_exchange_rate(db, currency=target_currency)
    exchange_rate = db_rate.rate if db_rate else EXCHANGE_RATES.get(target_currency, 1.0)
    
    original_amount = order.total_amount or 0
    converted_amount = original_amount / exchange_rate if exchange_rate > 0 else 0
    
    return make_response(True, {
        "order_id": order.id,
        "order_no": order.so_no,
        "original_currency": original_currency,
        "original_amount": float(original_amount),
        "target_currency": target_currency,
        "exchange_rate": exchange_rate,
        "converted_amount": round(converted_amount, 2),
        "conversion_date": datetime.datetime.now().isoformat()
    }, "货币转换完成")