"""API对接中心：管理外部第三方API连接配置"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
import json
import datetime

from ..database import get_db
from .. import models

router = APIRouter()


@router.get("/integrations")
def list_integrations(db: Session = Depends(get_db)):
    """获取所有API对接配置"""
    items = db.query(models.ApiIntegration).order_by(models.ApiIntegration.id.desc()).all()
    return {
        "success": True,
        "data": [
            {
                "id": i.id,
                "name": i.name,
                "api_type": i.api_type,
                "base_url": i.base_url,
                "auth_type": i.auth_type,
                "status": i.status,
                "last_tested_at": i.last_tested_at.isoformat() if i.last_tested_at else None,
                "last_test_result": i.last_test_result,
                "created_at": i.created_at.isoformat() if i.created_at else None
            } for i in items
        ]
    }


@router.post("/integrations")
def create_integration(
    name: str,
    base_url: str,
    api_type: str = "custom",
    auth_type: str = "bearer",
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    app_id: Optional[str] = None,
    extra_config: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """创建API对接配置"""
    if not name or not base_url:
        raise HTTPException(status_code=400, detail="名称和API地址不能为空")
    if auth_type not in ["bearer", "basic", "apikey", "oauth2"]:
        raise HTTPException(status_code=400, detail="认证方式无效")
    integration = models.ApiIntegration(
        name=name,
        api_type=api_type,
        base_url=base_url,
        auth_type=auth_type,
        api_key=api_key,
        api_secret=api_secret,
        app_id=app_id,
        extra_config=extra_config,
        status="active"
    )
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return {"success": True, "data": {"id": integration.id, "name": integration.name}, "message": "创建成功"}


@router.put("/integrations/{integration_id}")
def update_integration(
    integration_id: int,
    name: Optional[str] = None,
    base_url: Optional[str] = None,
    api_type: Optional[str] = None,
    auth_type: Optional[str] = None,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    app_id: Optional[str] = None,
    extra_config: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """更新API对接配置"""
    integration = db.query(models.ApiIntegration).filter(models.ApiIntegration.id == integration_id).first()
    if not integration:
        raise HTTPException(status_code=404, detail="配置不存在")
    if name is not None: integration.name = name
    if base_url is not None: integration.base_url = base_url
    if api_type is not None: integration.api_type = api_type
    if auth_type is not None: integration.auth_type = auth_type
    if api_key is not None: integration.api_key = api_key
    if api_secret is not None: integration.api_secret = api_secret
    if app_id is not None: integration.app_id = app_id
    if extra_config is not None: integration.extra_config = extra_config
    if status is not None: integration.status = status
    db.commit()
    return {"success": True, "message": "更新成功"}


@router.delete("/integrations/{integration_id}")
def delete_integration(integration_id: int, db: Session = Depends(get_db)):
    """删除API对接配置"""
    integration = db.query(models.ApiIntegration).filter(models.ApiIntegration.id == integration_id).first()
    if not integration:
        raise HTTPException(status_code=404, detail="配置不存在")
    db.delete(integration)
    db.commit()
    return {"success": True, "message": "删除成功"}


@router.post("/integrations/{integration_id}/test")
def test_integration(integration_id: int, db: Session = Depends(get_db)):
    """测试API连接（发送一个简单的GET请求验证可达性）"""
    integration = db.query(models.ApiIntegration).filter(models.ApiIntegration.id == integration_id).first()
    if not integration:
        raise HTTPException(status_code=404, detail="配置不存在")

    import urllib.request
    import urllib.error

    url = integration.base_url
    if not url.startswith("http"):
        url = "https://" + url

    headers = {}
    if integration.auth_type == "bearer" and integration.api_key:
        headers["Authorization"] = "Bearer " + integration.api_key
    elif integration.auth_type == "apikey" and integration.api_key:
        headers["X-API-Key"] = integration.api_key
    elif integration.auth_type == "basic" and integration.api_key:
        import base64
        credentials = integration.api_key + ":" + (integration.api_secret or "")
        headers["Authorization"] = "Basic " + base64.b64encode(credentials.encode()).decode()

    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            status_code = resp.status
            result_msg = f"连接成功（HTTP {status_code}）"
            integration.last_tested_at = datetime.datetime.utcnow()
            integration.last_test_result = result_msg
            db.commit()
            return {"success": True, "message": result_msg, "status_code": status_code}
    except urllib.error.HTTPError as e:
        # 4xx/5xx也说明可达
        result_msg = f"服务器可达，但返回 HTTP {e.code}"
        integration.last_tested_at = datetime.datetime.utcnow()
        integration.last_test_result = result_msg
        db.commit()
        return {"success": True, "message": result_msg, "status_code": e.code}
    except Exception as e:
        result_msg = f"连接失败：{str(e)[:200]}"
        integration.last_tested_at = datetime.datetime.utcnow()
        integration.last_test_result = result_msg
        db.commit()
        return {"success": False, "message": result_msg}


@router.get("/integrations/presets")
def get_presets():
    """获取常见API对接预设"""
    presets = [
        {"type": "taobao", "name": "淘宝开放平台", "url": "https://eco.taobao.com/", "desc": "淘宝/天猫店铺订单同步"},
        {"type": "1688", "name": "1688开放平台", "url": "https://open.1688.com/", "desc": "1688采购订单同步"},
        {"type": "jd", "name": "京东开放平台", "url": "https://open.jd.com/", "desc": "京东店铺订单同步"},
        {"type": "shopify", "name": "Shopify", "url": "https://your-store.myshopify.com/admin/api/2024-01/", "desc": "Shopify电商平台"},
        {"type": "wechat", "name": "微信小程序", "url": "https://api.weixin.qq.com/", "desc": "微信小程序订单推送"},
        {"type": "feishu", "name": "飞书开放平台", "url": "https://open.feishu.cn/", "desc": "飞书机器人/审批/通知"},
        {"type": "dingtalk", "name": "钉钉开放平台", "url": "https://oapi.dingtalk.com/", "desc": "钉钉机器人/通知"},
        {"type": "custom", "name": "自定义API", "url": "", "desc": "其他第三方API"}
    ]
    return {"success": True, "data": presets}
