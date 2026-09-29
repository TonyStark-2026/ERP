from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime

from ..database import get_db
from .. import crud, schemas

router = APIRouter()

@router.get("/employees/", response_model=List[schemas.Employee])
def read_employees(account_set_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    employees = crud.get_employees(db, account_set_id=account_set_id, skip=skip, limit=limit)
    return employees

@router.get("/employees/{employee_id}", response_model=schemas.Employee)
def read_employee(employee_id: int, db: Session = Depends(get_db)):
    db_employee = crud.get_employee(db, employee_id=employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee

@router.post("/employees/", response_model=schemas.Employee)
def create_employee(employee: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    if employee.contract_start_date and employee.contract_end_date:
        contract_duration = (employee.contract_end_date - employee.contract_start_date).days
        if contract_duration <= 365 and employee.probation_end_date:
            probation_duration = (employee.probation_end_date - employee.contract_start_date).days
            if probation_duration > 60:
                raise HTTPException(status_code=400, detail="试用期超过2个月，违反劳动法规定")
    
    if employee.hire_date and not employee.social_security_start_date:
        employee.social_security_start_date = employee.hire_date + datetime.timedelta(days=30)
    
    return crud.create_employee(db=db, employee=employee)

@router.put("/employees/{employee_id}", response_model=schemas.Employee)
def update_employee(employee_id: int, employee: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    db_employee = crud.update_employee(db, employee_id=employee_id, employee=employee)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee

@router.delete("/employees/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    success = crud.delete_employee(db, employee_id=employee_id)
    if not success:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee deleted successfully"}

@router.get("/employees/compliance-alerts")
def get_compliance_alerts(account_set_id: Optional[int] = None, db: Session = Depends(get_db)):
    employees = crud.get_employees(db, account_set_id=account_set_id)
    alerts = []
    today = datetime.date.today()
    
    for emp in employees:
        if emp.probation_end_date and emp.contract_start_date:
            contract_duration = (emp.contract_end_date - emp.contract_start_date).days if emp.contract_end_date else float('inf')
            probation_duration = (emp.probation_end_date - emp.contract_start_date).days
            
            if contract_duration <= 365 and probation_duration > 60:
                alerts.append({
                    "employee_id": emp.id,
                    "employee_name": emp.name,
                    "alert_type": "probation_violation",
                    "message": f"试用期超过2个月，合同期限不足1年",
                    "severity": "HIGH"
                })
        
        if emp.social_security_start_date and emp.social_security_start_date < today:
            days_passed = (today - emp.social_security_start_date).days
            if days_passed > 30:
                alerts.append({
                    "employee_id": emp.id,
                    "employee_name": emp.name,
                    "alert_type": "social_security_delay",
                    "message": f"社保缴纳已逾期{days_passed}天",
                    "severity": "HIGH"
                })
        elif emp.hire_date:
            days_since_hire = (today - emp.hire_date).days
            if days_since_hire > 30 and not emp.social_security_start_date:
                alerts.append({
                    "employee_id": emp.id,
                    "employee_name": emp.name,
                    "alert_type": "social_security_pending",
                    "message": f"入职{days_since_hire}天，尚未缴纳社保",
                    "severity": "MEDIUM"
                })
    
    return alerts