from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import datetime
import hashlib

from .. import models, schemas, crud
from ..database import get_db

router = APIRouter()

# =============== 7大角色权限注册表 ===============
# 每个角色定义：可访问的模块 + 可执行的操作按钮
ROLE_PERMISSIONS = {
    "super_admin": {
        "name": "超级管理员",
        "modules": ["dashboard", "materials", "sales", "plan", "purchase", "supplier", "production", "inventory_v2", "finance", "engineering", "ai", "subscription"],
        "actions": ["*"]  # 全部操作
    },
    # USER=系统注册的默认账号角色（老板），享有全部模块权限
    "USER": {
        "name": "超级管理员",
        "modules": ["dashboard", "materials", "sales", "plan", "purchase", "supplier", "production", "inventory_v2", "finance", "engineering", "ai", "subscription"],
        "actions": ["*"]
    },
    "project_manager": {
        "name": "项目经理",
        "modules": ["dashboard", "materials", "sales", "plan", "purchase", "production", "inventory_v2", "engineering", "ai"],
        "actions": ["view", "create", "edit", "submit", "wbs_manage", "eco_view", "schedule_manage"]
    },
    "process_engineer": {
        "name": "工艺工程师",
        "modules": ["dashboard", "materials", "plan", "production", "engineering", "ai"],
        "actions": ["view", "bom_manage", "eco_create", "eco_edit", "quality_view", "schedule_view"]
    },
    "purchaser": {
        "name": "采购员",
        "modules": ["dashboard", "materials", "purchase", "supplier", "inventory_v2", "engineering", "ai"],
        "actions": ["view", "purchase_create", "purchase_edit", "purchase_submit", "supplier_manage", "bom_view"]
    },
    "production_supervisor": {
        "name": "生产主管",
        "modules": ["dashboard", "materials", "plan", "production", "inventory_v2", "engineering", "ai"],
        "actions": ["view", "work_order_manage", "pick_manage", "inbound_manage", "equipment_manage", "schedule_manage", "quality_view"]
    },
    "quality_inspector": {
        "name": "质检员",
        "modules": ["dashboard", "materials", "production", "inventory_v2", "engineering", "ai"],
        "actions": ["view", "quality_create", "quality_edit", "quality_trace", "bom_view"]
    },
    "finance_staff": {
        "name": "财务员",
        "modules": ["dashboard", "finance", "sales", "purchase", "inventory_v2", "engineering", "ai"],
        "actions": ["view", "voucher_manage", "report_view", "revenue_confirm", "cost_view", "contract_view"]
    }
}


def get_role_permissions(role: str) -> dict:
    """获取角色权限，未定义的角色返回只读权限"""
    return ROLE_PERMISSIONS.get(role, {
        "name": role,
        "modules": ["dashboard"],
        "actions": ["view"]
    })

@router.post("/register", response_model=schemas.ApiResponse)
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    if user.email:
        existing_email = crud.get_user_by_email(db, user.email)
        if existing_email:
            raise HTTPException(status_code=400, detail="邮箱已被注册")
    
    db_user = crud.create_user(db, user)
    
    return schemas.ApiResponse(
        success=True,
        data={
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "phone": db_user.phone,
            "created_at": db_user.created_at
        },
        message="注册成功"
    )

@router.post("/login", response_model=schemas.ApiResponse)
async def login(user_login: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = crud.verify_user(db, user_login.username, user_login.password)
    
    if not db_user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 获取角色权限
    role = db_user.role or "super_admin"
    perms = get_role_permissions(role)
    
    return schemas.ApiResponse(
        success=True,
        data={
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "phone": db_user.phone,
            "role": role,
            "role_name": perms["name"],
            "permissions": perms,
            "created_at": db_user.created_at
        },
        message="登录成功"
    )


@router.get("/roles")
async def list_roles():
    """返回所有可用角色列表"""
    return {
        "success": True,
        "data": [
            {"key": k, "name": v["name"], "module_count": len(v["modules"]), "action_count": len(v["actions"])}
            for k, v in ROLE_PERMISSIONS.items()
        ]
    }


@router.get("/me")
async def get_current_user_info(username: str, db: Session = Depends(get_db)):
    """获取当前用户的完整权限信息"""
    db_user = crud.get_user_by_username(db, username)
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    role = db_user.role or "super_admin"
    perms = get_role_permissions(role)
    return {
        "success": True,
        "data": {
            "id": db_user.id,
            "username": db_user.username,
            "role": role,
            "role_name": perms["name"],
            "permissions": perms
        }
    }