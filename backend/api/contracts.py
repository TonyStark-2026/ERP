from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime

from ..database import get_db
from .. import crud, schemas

router = APIRouter()

@router.get("/contracts/", response_model=List[schemas.Contract])
def read_contracts(account_set_id: Optional[int] = None, contract_type: Optional[str] = None, status: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    contracts = crud.get_contracts(db, account_set_id=account_set_id, contract_type=contract_type, status=status, skip=skip, limit=limit)
    return contracts

@router.get("/contracts/{contract_id}", response_model=schemas.Contract)
def read_contract(contract_id: int, db: Session = Depends(get_db)):
    db_contract = crud.get_contract(db, contract_id=contract_id)
    if db_contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    return db_contract

@router.post("/contracts/", response_model=schemas.Contract)
def create_contract(contract: schemas.ContractCreate, db: Session = Depends(get_db)):
    return crud.create_contract(db=db, contract=contract)

@router.put("/contracts/{contract_id}", response_model=schemas.Contract)
def update_contract(contract_id: int, contract: schemas.ContractCreate, db: Session = Depends(get_db)):
    db_contract = crud.update_contract(db, contract_id=contract_id, contract=contract)
    if db_contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    return db_contract

@router.post("/contracts/{contract_id}/activate")
def activate_contract(contract_id: int, db: Session = Depends(get_db)):
    db_contract = crud.get_contract(db, contract_id=contract_id)
    if db_contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    db_contract.status = schemas.ContractStatus.ACTIVE
    db.commit()
    db.refresh(db_contract)
    return db_contract

@router.post("/contracts/{contract_id}/terminate")
def terminate_contract(contract_id: int, db: Session = Depends(get_db)):
    db_contract = crud.get_contract(db, contract_id=contract_id)
    if db_contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    db_contract.status = schemas.ContractStatus.TERMINATED
    db.commit()
    db.refresh(db_contract)
    return db_contract

@router.get("/contracts/expiring")
def get_expiring_contracts(days: int = 30, db: Session = Depends(get_db)):
    threshold_date = datetime.date.today() + datetime.timedelta(days=days)
    contracts = db.query(schemas.Contract).filter(
        schemas.Contract.end_date <= threshold_date,
        schemas.Contract.status == schemas.ContractStatus.ACTIVE
    ).all()
    return contracts