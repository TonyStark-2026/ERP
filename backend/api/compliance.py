from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
import re

from .. import crud, schemas, models
from ..database import get_db
from ..app import make_response
from ..models import AlertLevel

router = APIRouter()

PERSONAL_CONSUMPTION_KEYWORDS = ["餐饮", "娱乐", "美容", "健身", "旅游", "机票", "酒店", "香烟", "酒", "礼品"]
COLLECTIVE_WELFARE_KEYWORDS = ["空调", "冰箱", "洗衣机", "微波炉", "电饭煲", "热水器", "电视", "家具"]

@router.post("/tax-check", tags=["合规预警"])
def check_tax_rate(request: schemas.TaxCheckRequest, db: Session = Depends(get_db)):
    db_order = crud.get_purchase_order(db, order_id=request.purchase_order_id)
    if db_order is None:
        return make_response(False, None, "采购订单不存在", "40002")
    
    po_tax_rate = float(db_order.tax_rate)
    invoice_tax_rate = request.invoice_tax_rate
    
    rate_diff = abs(po_tax_rate - invoice_tax_rate)
    
    if rate_diff < 0.001:
        match = True
        warning_level = "LOW"
        suggestion = "税率匹配，无需处理"
    elif rate_diff < 0.05:
        match = False
        warning_level = "MEDIUM"
        suggestion = "税率存在差异，建议核实是否需要补差"
    else:
        match = False
        warning_level = "HIGH"
        suggestion = "税率不匹配，建议联系供应商核实发票信息"
    
    if not match:
        crud.create_compliance_alert(db, schemas.ComplianceAlertCreate(
            alert_type="TAX_RATE_MISMATCH",
            level=warning_level,
            reference_id=request.purchase_order_id,
            message=f"采购订单税率({po_tax_rate*100:.1f}%)与发票税率({invoice_tax_rate*100:.1f}%)不匹配",
            suggestion=suggestion,
            status="PENDING"
        ))
    
    result = {
        "match": match,
        "po_tax_rate": po_tax_rate,
        "invoice_tax_rate": invoice_tax_rate,
        "warning_level": warning_level,
        "suggestion": suggestion
    }
    
    return make_response(True, result, "校验完成")

@router.post("/invoice/check", tags=["合规预警"])
def check_invoice(invoice: schemas.InvoiceCheckRequest, db: Session = Depends(get_db)):
    alerts = []
    suggestions = []
    
    if invoice.supplier_tax_rate and invoice.company_tax_rate:
        rate_diff = abs(invoice.supplier_tax_rate - invoice.company_tax_rate)
        if rate_diff > 0.05:
            alerts.append({
                "type": "TAX_RATE_DISCREPANCY",
                "level": "HIGH",
                "message": f"进销项税率差异较大(进项{invoice.supplier_tax_rate*100:.1f}%,销项{invoice.company_tax_rate*100:.1f}%)",
                "suggestion": "存在税务风险，建议核实业务真实性"
            })
    
    if invoice.items:
        for item in invoice.items:
            item_name = item.get("name", "")
            
            for keyword in PERSONAL_CONSUMPTION_KEYWORDS:
                if keyword in item_name:
                    alerts.append({
                        "type": "PERSONAL_CONSUMPTION",
                        "level": "HIGH",
                        "message": f"识别到个人消费类发票项目: {item_name}",
                        "suggestion": "此发票不得抵扣进项税，需做进项转出"
                    })
                    break
            
            for keyword in COLLECTIVE_WELFARE_KEYWORDS:
                if keyword in item_name:
                    alerts.append({
                        "type": "COLLECTIVE_WELFARE",
                        "level": "MEDIUM",
                        "message": f"识别到集体福利类发票项目: {item_name}",
                        "suggestion": "此发票不得抵扣进项税，需做进项转出"
                    })
                    break
    
    for alert in alerts:
        crud.create_compliance_alert(db, schemas.ComplianceAlertCreate(
            alert_type=alert["type"],
            level=alert["level"],
            reference_id=invoice.invoice_no,
            message=alert["message"],
            suggestion=alert["suggestion"],
            status="PENDING"
        ))
    
    return make_response(True, {
        "has_alerts": len(alerts) > 0,
        "alerts": alerts,
        "suggestions": suggestions
    }, "发票校验完成")

@router.get("/contract-alerts", tags=["合规预警"])
def get_contract_alerts(days_before_expiry: int = 30, days_before_payment: int = 7, db: Session = Depends(get_db)):
    today = datetime.date.today()
    expiry_threshold = today + datetime.timedelta(days=days_before_expiry)
    payment_threshold = today + datetime.timedelta(days=days_before_payment)
    
    contracts = crud.get_contracts(db, status="ACTIVE")
    alerts = []
    
    for contract in contracts:
        if contract.end_date and contract.end_date <= expiry_threshold:
            days_left = (contract.end_date - today).days
            alerts.append({
                "contract_id": contract.id,
                "contract_no": contract.contract_no,
                "contract_type": contract.contract_type,
                "counterparty": contract.counterparty_name,
                "alert_type": "CONTRACT_EXPIRY",
                "level": "HIGH" if days_left <= 7 else "MEDIUM",
                "message": f"合同即将到期，剩余{days_left}天",
                "suggestion": "请及时准备续约"
            })
        
        if contract.payment_due_date and contract.payment_due_date <= payment_threshold:
            days_left = (contract.payment_due_date - today).days
            if contract.payment_status == "PENDING":
                alerts.append({
                    "contract_id": contract.id,
                    "contract_no": contract.contract_no,
                    "contract_type": contract.contract_type,
                    "counterparty": contract.counterparty_name,
                    "alert_type": "PAYMENT_DUE",
                    "level": "HIGH" if days_left <= 0 else "MEDIUM",
                    "message": f"应收款即将到期，剩余{days_left}天",
                    "suggestion": "请及时催收款项"
                })
        
        if contract.delivery_due_date and contract.delivery_due_date <= payment_threshold:
            days_left = (contract.delivery_due_date - today).days
            alerts.append({
                "contract_id": contract.id,
                "contract_no": contract.contract_no,
                "contract_type": contract.contract_type,
                "counterparty": contract.counterparty_name,
                "alert_type": "DELIVERY_DUE",
                "level": "HIGH" if days_left <= 0 else "MEDIUM",
                "message": f"交货期限即将到期，剩余{days_left}天",
                "suggestion": "请确认交货进度"
            })
    
    alerts.sort(key=lambda x: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[x["level"]])
    
    return make_response(True, alerts, "合同预警查询成功")

@router.get("/labor-compliance", tags=["合规预警"])
def get_labor_compliance_alerts(account_set_id: Optional[int] = None, db: Session = Depends(get_db)):
    employees = crud.get_employees(db, account_set_id=account_set_id)
    today = datetime.date.today()
    alerts = []
    
    for emp in employees:
        if emp.contract_start_date and emp.contract_end_date:
            contract_duration = (emp.contract_end_date - emp.contract_start_date).days
            
            if contract_duration <= 365:
                if emp.probation_end_date:
                    probation_duration = (emp.probation_end_date - emp.contract_start_date).days
                    if probation_duration > 60:
                        alerts.append({
                            "employee_id": emp.id,
                            "employee_name": emp.name,
                            "alert_type": "PROBATION_VIOLATION",
                            "level": "HIGH",
                            "message": f"试用期{probation_duration}天超过2个月，合同期限{contract_duration}天不足1年",
                            "suggestion": "违反劳动法规定，建议调整试用期"
                        })
            elif contract_duration <= 730:
                if emp.probation_end_date:
                    probation_duration = (emp.probation_end_date - emp.contract_start_date).days
                    if probation_duration > 90:
                        alerts.append({
                            "employee_id": emp.id,
                            "employee_name": emp.name,
                            "alert_type": "PROBATION_VIOLATION",
                            "level": "HIGH",
                            "message": f"试用期{probation_duration}天超过3个月，合同期限{contract_duration}天不足2年",
                            "suggestion": "违反劳动法规定，建议调整试用期"
                        })
            else:
                if emp.probation_end_date:
                    probation_duration = (emp.probation_end_date - emp.contract_start_date).days
                    if probation_duration > 180:
                        alerts.append({
                            "employee_id": emp.id,
                            "employee_name": emp.name,
                            "alert_type": "PROBATION_VIOLATION",
                            "level": "HIGH",
                            "message": f"试用期{probation_duration}天超过6个月",
                            "suggestion": "违反劳动法规定，建议调整试用期"
                        })
        
        if emp.social_security_start_date:
            if emp.social_security_start_date > today:
                days_until = (emp.social_security_start_date - today).days
                if days_until > 30:
                    alerts.append({
                        "employee_id": emp.id,
                        "employee_name": emp.name,
                        "alert_type": "SOCIAL_SECURITY_DELAY",
                        "level": "HIGH",
                        "message": f"社保缴纳计划延迟{days_until}天",
                        "suggestion": "入职30天内必须缴纳社保"
                    })
        elif emp.hire_date:
            days_since_hire = (today - emp.hire_date).days
            if days_since_hire > 30:
                alerts.append({
                    "employee_id": emp.id,
                    "employee_name": emp.name,
                    "alert_type": "SOCIAL_SECURITY_PENDING",
                    "level": "MEDIUM",
                    "message": f"入职{days_since_hire}天，尚未缴纳社保",
                    "suggestion": "请尽快办理社保缴纳"
                })
    
    return make_response(True, alerts, "劳动合规预警查询成功")

@router.get("/alerts", tags=["合规预警"])
def list_alerts(level: str = None, status: str = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    alerts = crud.get_compliance_alerts(db, level=level, status=status, skip=skip, limit=limit)
    total = crud.get_compliance_alerts_count(db, level=level, status=status)
    return make_response(True, {"items": alerts, "total": total}, "查询成功")

@router.get("/alerts/{alert_id}", tags=["合规预警"])
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    db_alert = crud.get_compliance_alert(db, alert_id=alert_id)
    if db_alert is None:
        return make_response(False, None, "预警记录不存在", "40002")
    return make_response(True, db_alert, "查询成功")

@router.put("/alerts/{alert_id}/resolve", tags=["合规预警"])
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    success = crud.resolve_compliance_alert(db, alert_id=alert_id)
    if not success:
        return make_response(False, None, "预警记录不存在", "40002")
    return make_response(True, None, "预警已处理")

@router.get("/supplier-tax-expiry", tags=["合规预警"])
def check_supplier_tax_expiry(days: int = 30, db: Session = Depends(get_db)):
    expiry_date = datetime.date.today() + datetime.timedelta(days=days)
    suppliers = crud.get_suppliers_with_expiring_tax(db, expiry_date=expiry_date)
    
    expiring_list = []
    for supplier in suppliers:
        days_left = (supplier.tax_id_expiry - datetime.date.today()).days
        expiring_list.append({
            "supplier_id": supplier.id,
            "supplier_name": supplier.name,
            "tax_id": supplier.tax_id,
            "expiry_date": supplier.tax_id_expiry.isoformat(),
            "days_left": days_left
        })
    
    return make_response(True, expiring_list, "查询成功")


@router.post("/invoice/auto-detect", tags=["合规预警"])
def auto_detect_invoice_risk(invoice_data: schemas.InvoiceCheckRequest, db: Session = Depends(get_db)):
    risk_score = 0
    risk_factors = []
    suggestions = []
    
    if invoice_data.supplier_tax_rate and invoice_data.company_tax_rate:
        rate_diff = abs(invoice_data.supplier_tax_rate - invoice_data.company_tax_rate)
        if rate_diff > 0.05:
            risk_score += 30
            risk_factors.append(f"进销项税率差异{rate_diff*100:.1f}%")
            suggestions.append("核实业务真实性，可能存在虚开发票风险")
        elif rate_diff > 0.02:
            risk_score += 10
            risk_factors.append(f"进销项税率差异{rate_diff*100:.1f}%")
    
    if invoice_data.total_amount:
        if invoice_data.total_amount > 100000:
            risk_score += 15
            risk_factors.append("发票金额较大")
            suggestions.append("建议加强合同和物流凭证审核")
    
    if invoice_data.items:
        for item in invoice_data.items:
            item_name = item.get("name", "")
            
            for keyword in PERSONAL_CONSUMPTION_KEYWORDS:
                if keyword in item_name:
                    risk_score += 25
                    risk_factors.append(f"个人消费类项目: {item_name}")
                    suggestions.append("此发票不得抵扣进项税，需做进项转出")
                    break
            
            for keyword in COLLECTIVE_WELFARE_KEYWORDS:
                if keyword in item_name:
                    risk_score += 20
                    risk_factors.append(f"集体福利类项目: {item_name}")
                    suggestions.append("此发票不得抵扣进项税，需做进项转出")
                    break
    
    if invoice_data.invoice_date:
        today = datetime.date.today()
        invoice_date = invoice_data.invoice_date
        days_diff = (today - invoice_date).days
        if days_diff > 180:
            risk_score += 10
            risk_factors.append(f"发票日期距今{days_diff}天")
            suggestions.append("注意进项税抵扣时限")
    
    risk_level = "LOW"
    if risk_score >= 70:
        risk_level = "HIGH"
    elif risk_score >= 40:
        risk_level = "MEDIUM"
    
    if risk_level != "LOW":
        crud.create_compliance_alert(db, schemas.ComplianceAlertCreate(
            alert_type="INVOICE_RISK",
            level=risk_level,
            reference_id=invoice_data.invoice_no,
            message=f"发票风险评估得分: {risk_score}分",
            suggestion="; ".join(suggestions),
            status="PENDING"
        ))
    
    return make_response(True, {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "suggestions": suggestions
    }, "发票风险评估完成")


@router.get("/employee-contract-alerts", tags=["合规预警"])
def get_employee_contract_alerts(days_before_expiry: int = 30, account_set_id: Optional[int] = None, db: Session = Depends(get_db)):
    today = datetime.date.today()
    expiry_threshold = today + datetime.timedelta(days=days_before_expiry)
    
    employees = crud.get_employees(db, account_set_id=account_set_id)
    alerts = []
    
    for emp in employees:
        if emp.contract_end_date and emp.contract_end_date <= expiry_threshold:
            days_left = (emp.contract_end_date - today).days
            alerts.append({
                "employee_id": emp.id,
                "employee_name": emp.name,
                "department": emp.department,
                "contract_start_date": emp.contract_start_date.isoformat() if emp.contract_start_date else None,
                "contract_end_date": emp.contract_end_date.isoformat(),
                "days_left": days_left,
                "alert_type": "CONTRACT_EXPIRY",
                "level": "HIGH" if days_left <= 7 else "MEDIUM",
                "suggestion": "请及时与员工沟通续约事宜"
            })
    
    alerts.sort(key=lambda x: x["days_left"])
    
    return make_response(True, alerts, "员工合同到期预警查询成功")


@router.get("/compliance-dashboard", tags=["合规预警"])
def get_compliance_dashboard(account_set_id: Optional[int] = None, db: Session = Depends(get_db)):
    today = datetime.date.today()
    
    invoice_alerts = crud.get_compliance_alerts(db, alert_type="INVOICE_RISK", status="PENDING")
    contract_alerts = crud.get_compliance_alerts(db, alert_type="CONTRACT_EXPIRY", status="PENDING")
    tax_alerts = crud.get_compliance_alerts(db, alert_type="TAX_RATE_MISMATCH", status="PENDING")
    labor_alerts = crud.get_compliance_alerts(db, alert_type=["PROBATION_VIOLATION", "SOCIAL_SECURITY_PENDING"], status="PENDING")
    
    contracts = crud.get_contracts(db, status="ACTIVE")
    expiring_contracts = [c for c in contracts if c.end_date and c.end_date <= today + datetime.timedelta(days=30)]
    
    employees = crud.get_employees(db, account_set_id=account_set_id)
    pending_ss = [e for e in employees if e.hire_date and (today - e.hire_date).days > 30 and not e.social_security_start_date]
    
    return make_response(True, {
        "total_alerts": len(invoice_alerts) + len(contract_alerts) + len(tax_alerts) + len(labor_alerts),
        "alert_by_type": {
            "invoice_risk": len(invoice_alerts),
            "contract_expiry": len(contract_alerts),
            "tax_rate_mismatch": len(tax_alerts),
            "labor_compliance": len(labor_alerts)
        },
        "pending_items": {
            "expiring_contracts": len(expiring_contracts),
            "pending_social_security": len(pending_ss)
        },
        "recent_alerts": [
            {"type": "INVOICE_RISK", "count": len(invoice_alerts)},
            {"type": "CONTRACT_EXPIRY", "count": len(contract_alerts)},
            {"type": "LABOR_COMPLIANCE", "count": len(labor_alerts)}
        ]
    }, "合规仪表盘查询成功")