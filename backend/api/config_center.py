from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from ..database import get_db
from .. import crud, schemas, models

router = APIRouter()

@router.get("/account_sets/", response_model=List[schemas.AccountSet])
def read_account_sets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    account_sets = crud.get_account_sets(db, skip=skip, limit=limit)
    return account_sets

@router.get("/account_sets/{account_set_id}", response_model=schemas.AccountSet)
def read_account_set(account_set_id: int, db: Session = Depends(get_db)):
    db_account_set = crud.get_account_set(db, account_set_id=account_set_id)
    if db_account_set is None:
        raise HTTPException(status_code=404, detail="Account set not found")
    return db_account_set

@router.post("/account_sets/", response_model=schemas.AccountSet)
def create_account_set(account_set: schemas.AccountSetCreate, db: Session = Depends(get_db)):
    existing = crud.get_account_set_by_code(db, code=account_set.code)
    if existing:
        raise HTTPException(status_code=400, detail="Account set code already exists")
    return crud.create_account_set(db=db, account_set=account_set)

@router.put("/account_sets/{account_set_id}", response_model=schemas.AccountSet)
def update_account_set(account_set_id: int, account_set: schemas.AccountSetCreate, db: Session = Depends(get_db)):
    db_account_set = crud.update_account_set(db, account_set_id=account_set_id, account_set=account_set)
    if db_account_set is None:
        raise HTTPException(status_code=404, detail="Account set not found")
    return db_account_set

@router.delete("/account_sets/{account_set_id}")
def delete_account_set(account_set_id: int, db: Session = Depends(get_db)):
    success = crud.delete_account_set(db, account_set_id=account_set_id)
    if not success:
        raise HTTPException(status_code=404, detail="Account set not found")
    return {"message": "Account set deleted successfully"}

@router.get("/system_config/{account_set_id}", response_model=schemas.SystemConfig)
def read_system_config(account_set_id: int, db: Session = Depends(get_db)):
    config = crud.get_system_config(db, account_set_id=account_set_id)
    if config is None:
        raise HTTPException(status_code=404, detail="System config not found")
    return config

@router.post("/system_config/", response_model=schemas.SystemConfig)
def create_system_config(config: schemas.SystemConfigCreate, db: Session = Depends(get_db)):
    existing = crud.get_system_config(db, account_set_id=config.account_set_id)
    if existing:
        raise HTTPException(status_code=400, detail="System config already exists for this account set")
    return crud.create_system_config(db=db, config=config)

@router.put("/system_config/{config_id}", response_model=schemas.SystemConfig)
def update_system_config(config_id: int, config: schemas.SystemConfigCreate, db: Session = Depends(get_db)):
    db_config = crud.update_system_config(db, config_id=config_id, config=config)
    if db_config is None:
        raise HTTPException(status_code=404, detail="System config not found")
    return db_config

@router.get("/menu_config/{account_set_id}")
def get_menu_config(account_set_id: int, db: Session = Depends(get_db)):
    config = crud.get_system_config(db, account_set_id=account_set_id)
    if config is None:
        config = schemas.SystemConfig(
            id=0,
            account_set_id=account_set_id,
            company_scale=schemas.CompanyScale.SINGLE_USER,
            business_complexity=schemas.BusinessComplexity.TRADE_ONLY
        )
    
    menus = []
    
    if config.company_scale == schemas.CompanyScale.SINGLE_USER:
        menus.append({"name": "采购收货", "path": "/quick-purchase"})
        menus.append({"name": "销售发货", "path": "/quick-sale"})
        menus.append({"name": "记账凭证", "path": "/vouchers"})
        menus.append({"name": "报表中心", "path": "/reports"})
    else:
        menus.append({"name": "采购管理", "path": "/purchase"})
        menus.append({"name": "销售管理", "path": "/sales"})
        menus.append({"name": "库存管理", "path": "/inventory"})
        menus.append({"name": "财务管理", "path": "/finance"})
    
    if config.business_complexity in [schemas.BusinessComplexity.SIMPLE_PROCESSING, schemas.BusinessComplexity.COMPLEX_MANUFACTURING]:
        menus.append({"name": "生产管理", "path": "/production"})
        menus.append({"name": "BOM管理", "path": "/bom"})
    
    if config.crossborder_enabled:
        menus.append({"name": "跨境合规", "path": "/crossborder"})
    
    menus.append({"name": "系统配置", "path": "/settings"})
    
    return {"menus": menus, "config": config}


# =============== 企业级配置（单例，全局唯一）===============

@router.get("/enterprise")
def get_enterprise_config(db: Session = Depends(get_db)):
    """获取企业级配置（单例 id=1）"""
    config = db.query(models.EnterpriseConfig).filter(models.EnterpriseConfig.id == 1).first()
    if not config:
        # 兜底：确保存在
        config = models.EnterpriseConfig(id=1)
        db.add(config)
        db.commit()
        db.refresh(config)
    # 解析 JSON 字段
    picking_modes = []
    try:
        picking_modes = json.loads(config.picking_modes) if config.picking_modes else []
    except Exception:
        picking_modes = ["by_order"]
    return {
        "success": True,
        "data": {
            "id": config.id,
            "industry_type": config.industry_type,
            "business_mode": config.business_mode,
            "revenue_method": config.revenue_method,
            "picking_modes": picking_modes,
            "sub_industry": config.sub_industry,
            "capital_cost_rate": config.capital_cost_rate,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None
        }
    }


@router.put("/enterprise")
def update_enterprise_config(
    industry_type: Optional[str] = None,
    business_mode: Optional[str] = None,
    revenue_method: Optional[str] = None,
    picking_modes: Optional[List[str]] = None,
    sub_industry: Optional[str] = None,
    capital_cost_rate: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """更新企业级配置（单例 id=1），支持部分更新"""
    config = db.query(models.EnterpriseConfig).filter(models.EnterpriseConfig.id == 1).first()
    if not config:
        config = models.EnterpriseConfig(id=1)
        db.add(config)
    if industry_type is not None:
        if industry_type not in ["engineering", "agility", "compliance", "subscription"]:
            raise HTTPException(status_code=400, detail="industry_type 必须是 engineering/agility/compliance/subscription 之一")
        config.industry_type = industry_type
    if business_mode is not None:
        if business_mode not in ["A", "B"]:
            raise HTTPException(status_code=400, detail="business_mode 必须是 A 或 B")
        config.business_mode = business_mode
    if revenue_method is not None:
        if revenue_method not in ["percentage_of_completion", "on_delivery"]:
            raise HTTPException(status_code=400, detail="revenue_method 必须是 percentage_of_completion 或 on_delivery")
        config.revenue_method = revenue_method
    if picking_modes is not None:
        valid_modes = ["by_order", "batch_prep", "central", "backflush"]
        for mode in picking_modes:
            if mode not in valid_modes:
                raise HTTPException(status_code=400, detail=f"picking_mode '{mode}' 无效，必须是 {valid_modes} 之一")
        config.picking_modes = json.dumps(picking_modes, ensure_ascii=False)
    if sub_industry is not None:
        config.sub_industry = sub_industry
    if capital_cost_rate is not None:
        if capital_cost_rate < 0 or capital_cost_rate > 1:
            raise HTTPException(status_code=400, detail="capital_cost_rate 必须在 0~1 之间")
        config.capital_cost_rate = capital_cost_rate
    db.commit()
    db.refresh(config)
    picking_modes_result = []
    try:
        picking_modes_result = json.loads(config.picking_modes) if config.picking_modes else []
    except Exception:
        picking_modes_result = ["by_order"]
    return {
        "success": True,
        "data": {
            "id": config.id,
            "industry_type": config.industry_type,
            "business_mode": config.business_mode,
            "revenue_method": config.revenue_method,
            "picking_modes": picking_modes_result,
            "sub_industry": config.sub_industry,
            "capital_cost_rate": config.capital_cost_rate,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None
        },
        "message": "企业配置已更新"
    }