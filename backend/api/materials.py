from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime
import io

from .. import crud, schemas, models
from ..database import get_db
from ..app import make_response
from ..utils import calculate_value_score, classify_cva_abc, generate_inventory_strategy

router = APIRouter()

@router.get("/qr-image", tags=["物料管理"])
def generate_qr_image(text: str, size: int = 200):
    """生成二维码PNG图片"""
    try:
        import qrcode
        from qrcode.constants import ERROR_CORRECT_H
        qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_H, box_size=8, border=2)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1e3c72", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", tags=["物料管理"])
def create_material(material: schemas.MaterialCreate, db: Session = Depends(get_db)):
    db_material = crud.get_material_by_name(db, name=material.name)
    if db_material:
        return make_response(False, None, "物料名称已存在", "40003")

    # 如果未提供code，自动生成PO编码: POYYYYMMDD[ABC]PPPPNNN
    if not material.code:
        abc = material.abc_class or "C"
        # product_code存在description字段中（临时方案），前端传过来
        product_code = getattr(material, 'description', None) or "0000"
        # 如果description是JSON格式，尝试解析product_code
        if product_code and product_code.startswith("{"):
            try:
                import json
                extra = json.loads(product_code)
                product_code = extra.get("product_code", "0000")
            except:
                product_code = "0000"
        material.code = crud.generate_po_code(db, material.account_set_id, abc, product_code[:4])
    # barcode默认与code一致
    if not material.barcode:
        material.barcode = material.code

    created = crud.create_material(db, material)
    return make_response(True, created, "创建成功")

@router.get("/generate-code", tags=["物料管理"])
def generate_material_code(abc_class: str = "C", product_code: str = "0000", db: Session = Depends(get_db)):
    """生成采购入库编码: PO + YYYYMMDD + ABC分类 + 4位产品编号 + 3位流水号
    示例: PO20260819A0301001
    """
    code = crud.generate_po_code(db, abc_class=abc_class, product_code=product_code)
    return make_response(True, {"code": code, "qr_code": code}, "编码生成成功")

@router.get("/product-catalog", tags=["物料管理"])
def get_product_catalog():
    """产品编号映射表"""
    catalog = [
        {"product_code": "0301", "name": "进口橡木板", "abc_class": "A", "unit": "块", "default_price": 280.00},
        {"product_code": "0302", "name": "国产松木板", "abc_class": "B", "unit": "块", "default_price": 150.00},
        {"product_code": "0303", "name": "胡桃木皮", "abc_class": "A", "unit": "张", "default_price": 320.00},
        {"product_code": "0304", "name": "中密度纤维板", "abc_class": "B", "unit": "张", "default_price": 85.00},
        {"product_code": "0401", "name": "不锈钢铰链", "abc_class": "B", "unit": "副", "default_price": 25.00},
        {"product_code": "0402", "name": "自攻螺丝钉", "abc_class": "C", "unit": "盒", "default_price": 15.00},
        {"product_code": "0501", "name": "包装纸箱", "abc_class": "C", "unit": "个", "default_price": 8.00},
    ]
    return make_response(True, catalog, "查询成功")

@router.get("/", tags=["物料管理"])
def list_materials(skip: int = 0, limit: int = 100, name: str = None, code: str = None, db: Session = Depends(get_db)):
    materials = crud.get_materials(db, skip=skip, limit=limit, name=name, code=code)
    total = crud.get_materials_count(db, name=name, code=code)
    return make_response(True, {"items": materials, "total": total}, "查询成功")

@router.get("/search-by-code/{code}", tags=["物料管理"])
def search_material_by_code(code: str, db: Session = Depends(get_db)):
    db_material = crud.get_material_by_code(db, code=code)
    if db_material is None:
        db_material = crud.get_material_by_barcode(db, barcode=code)
    if db_material is None:
        return make_response(False, None, "物料不存在", "40002")
    return make_response(True, db_material, "查询成功")

@router.get("/search", tags=["物料管理"])
def search_material(q: str, db: Session = Depends(get_db)):
    db_material = crud.get_material_by_code(db, code=q)
    if db_material is None:
        db_material = crud.get_material_by_barcode(db, barcode=q)
    if db_material is None:
        db_material = db.query(crud.models.Material).filter(
            crud.models.Material.name.contains(q)
        ).first()
    if db_material is None:
        return make_response(False, None, "物料不存在", "40002")
    return make_response(True, db_material, "查询成功")

@router.get("/{material_id}", tags=["物料管理"])
def get_material(material_id: int, db: Session = Depends(get_db)):
    db_material = crud.get_material(db, material_id=material_id)
    if db_material is None:
        return make_response(False, None, "物料不存在", "40002")
    return make_response(True, db_material, "查询成功")

@router.put("/{material_id}", tags=["物料管理"])
def update_material(material_id: int, material: schemas.MaterialCreate, db: Session = Depends(get_db)):
    updated = crud.update_material(db, material_id=material_id, material=material)
    if updated is None:
        return make_response(False, None, "物料不存在", "40002")
    return make_response(True, updated, "更新成功")

@router.delete("/{material_id}", tags=["物料管理"])
def delete_material(material_id: int, db: Session = Depends(get_db)):
    success = crud.delete_material(db, material_id=material_id)
    if not success:
        return make_response(False, None, "物料不存在", "40002")
    return make_response(True, None, "删除成功")

@router.post("/{material_id}/cva-classify", tags=["物料管理"])
def classify_material_cva(material_id: int, annual_consumption: float, max_consumption: float, db: Session = Depends(get_db)):
    db_material = crud.get_material(db, material_id=material_id)
    if db_material is None:
        return make_response(False, None, "物料不存在", "40002")
    
    if db_material.criticality is None:
        return make_response(False, None, "物料未设置关键性评分", "40003")
    
    value_score = calculate_value_score(annual_consumption, max_consumption)
    abc_class, cva_class = classify_cva_abc(value_score, db_material.criticality)
    strategy = generate_inventory_strategy(abc_class, cva_class)
    
    crud.update_material_cva(db, material_id=material_id, value_score=value_score, cva_abc_class=f"{abc_class}-{cva_class}")
    
    result = {
        "material_id": material_id,
        "value_score": value_score,
        "abc_class": abc_class,
        "cva_class": cva_class,
        "strategy": strategy
    }
    
    return make_response(True, result, "分类完成")


# =============== 物料分类编码规则 ===============

@router.get("/categories/tree", tags=["物料分类编码"])
def get_category_tree(db: Session = Depends(get_db)):
    """获取物料分类树形结构（三级分类）"""
    level1 = db.query(models.MaterialCategory).filter(models.MaterialCategory.level == 1).order_by(models.MaterialCategory.sort_order).all()
    tree = []
    for l1 in level1:
        l2_list = db.query(models.MaterialCategory).filter(
            models.MaterialCategory.parent_id == l1.id, models.MaterialCategory.level == 2
        ).order_by(models.MaterialCategory.sort_order).all()
        children2 = []
        for l2 in l2_list:
            l3_list = db.query(models.MaterialCategory).filter(
                models.MaterialCategory.parent_id == l2.id, models.MaterialCategory.level == 3
            ).order_by(models.MaterialCategory.sort_order).all()
            children3 = [{
                "id": l3.id, "code": l3.code, "name": l3.name,
                "material_name": l3.material_name, "characteristic": l3.characteristic,
                "spec_standard": l3.spec_standard, "full_code": l3.full_code
            } for l3 in l3_list]
            children2.append({
                "id": l2.id, "code": l2.code, "name": l2.name, "full_code": l2.full_code,
                "children": children3
            })
        tree.append({
            "id": l1.id, "code": l1.code, "name": l1.name, "full_code": l1.full_code,
            "children": children2
        })
    return make_response(True, tree, "获取成功")


@router.post("/generate-code", tags=["物料分类编码"])
def generate_material_code(category_id: int, db: Session = Depends(get_db)):
    """根据三级分类自动生成物料编码：一级(2位)+二级(2位)+三级(3位)+流水号(3位)"""
    cat = db.query(models.MaterialCategory).filter(models.MaterialCategory.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    if cat.level != 3:
        raise HTTPException(status_code=400, detail="请选择三级分类（具体物料）")

    # 获取完整路径
    l3 = cat
    l2 = db.query(models.MaterialCategory).filter(models.MaterialCategory.id == l3.parent_id).first()
    l1 = db.query(models.MaterialCategory).filter(models.MaterialCategory.id == l2.parent_id).first()

    # 流水号+1
    l3.current_sequence = (l3.current_sequence or 0) + 1
    seq = str(l3.current_sequence).zfill(3)
    db.commit()
    db.refresh(l3)

    # 编码结构：一级(2位) + 二级(2位) + 三级(3位) + 流水号(3位) = 10位
    code = f"{l1.code}{l2.code}{l3.code}{seq}"
    return make_response(True, {
        "code": code,
        "sequence": seq,
        "category_path": f"{l1.name} > {l2.name} > {l3.material_name or l3.name}",
        "characteristic": l3.characteristic,
        "spec_standard": l3.spec_standard
    }, "编码生成成功")