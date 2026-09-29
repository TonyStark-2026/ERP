from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from .. import crud, schemas

router = APIRouter()

@router.get("/boms/", response_model=List[schemas.BOM])
def read_boms(account_set_id: Optional[int] = None, product_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    boms = crud.get_boms(db, account_set_id=account_set_id, product_id=product_id, skip=skip, limit=limit)
    return boms

@router.get("/boms/{bom_id}", response_model=schemas.BOM)
def read_bom(bom_id: int, db: Session = Depends(get_db)):
    db_bom = crud.get_bom(db, bom_id=bom_id)
    if db_bom is None:
        raise HTTPException(status_code=404, detail="BOM not found")
    return db_bom

@router.post("/boms/", response_model=schemas.BOM)
def create_bom(bom: schemas.BOMCreate, db: Session = Depends(get_db)):
    return crud.create_bom(db=db, bom=bom)

@router.post("/boms/{bom_id}/explode")
def explode_bom(bom_id: int, quantity: int = 1, db: Session = Depends(get_db)):
    db_bom = crud.get_bom(db, bom_id=bom_id)
    if db_bom is None:
        raise HTTPException(status_code=404, detail="BOM not found")
    
    exploded_items = []
    for item in db_bom.items:
        required_qty = item.quantity * quantity * (1 + item.scrap_rate)
        exploded_items.append({
            "material_id": item.material_id,
            "material_name": item.material.name if item.material else "",
            "quantity": required_qty,
            "unit": item.unit,
            "level": item.level
        })
    
    return {
        "product_id": db_bom.product_id,
        "product_name": db_bom.product.name if db_bom.product else "",
        "quantity": quantity,
        "exploded_items": exploded_items
    }