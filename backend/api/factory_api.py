"""
我的工厂模块API
================
1. 设备台账管理（CRUD）
2. 每日产能上报（手动录入 + Excel导入）
3. 产能进度线数据（每日进度 + 累计进度）
"""
import io
import re
import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from .. import models

router = APIRouter()


def _to_date(v):
    if v is None or v == "":
        return None
    if isinstance(v, datetime.datetime):
        return v.date()
    if isinstance(v, datetime.date):
        return v
    # Excel日期序列号（单元格被设为数值格式时）
    if isinstance(v, (int, float)) and 20000 < v < 80000:
        try:
            return datetime.date(1899, 12, 30) + datetime.timedelta(days=int(v))
        except Exception:
            return None
    s = str(v).strip()
    if not s:
        return None
    # 2026-08-15 / 2026/8/15 / 2026.8.15 / 2026年8月15日
    m = re.match(r"^(\d{4})[-/.年](\d{1,2})[-/.月](\d{1,2})日?$", s)
    if m:
        try:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except Exception:
            return None
    # 8月15日 / 8/15 / 8.15 / 8-15（默认当年）
    m = re.match(r"^(\d{1,2})[-/.月](\d{1,2})日?号?$", s)
    if m:
        try:
            return datetime.date(datetime.date.today().year, int(m.group(1)), int(m.group(2)))
        except Exception:
            return None
    try:
        return datetime.date.fromisoformat(s[:10])
    except Exception:
        return None


# ============================================================
# 1. 设备台账 CRUD
# ============================================================

@router.get("/equipments")
def list_equipments(db: Session = Depends(get_db)):
    """获取所有工厂设备列表"""
    items = db.query(models.FactoryEquipment).order_by(models.FactoryEquipment.id.desc()).all()
    return {
        "success": True,
        "data": [{
            "id": e.id,
            "equipment_code": e.equipment_code,
            "equipment_name": e.equipment_name,
            "category": e.category,
            "specification": e.specification or "",
            "location": e.location or "",
            "status": e.status,
            "daily_capacity_target": e.daily_capacity_target or 0,
            "unit": e.unit or "件",
            "remark": e.remark or "",
            "created_at": e.created_at.isoformat() if e.created_at else None,
        } for e in items],
        "total": len(items),
    }


@router.post("/equipments")
def create_equipment(data: Dict[str, Any], db: Session = Depends(get_db)):
    """新增设备"""
    code = (data.get("equipment_code") or "").strip()
    name = (data.get("equipment_name") or "").strip()
    if not code or not name:
        raise HTTPException(status_code=400, detail="设备编码和名称不能为空")
    # 检查编码唯一
    if db.query(models.FactoryEquipment).filter_by(equipment_code=code).first():
        raise HTTPException(status_code=400, detail=f"设备编码 {code} 已存在")
    eq = models.FactoryEquipment(
        equipment_code=code,
        equipment_name=name,
        category=data.get("category", "加工设备"),
        specification=data.get("specification", ""),
        location=data.get("location", ""),
        status=data.get("status", "running"),
        daily_capacity_target=float(data.get("daily_capacity_target") or 0),
        unit=data.get("unit", "件"),
        remark=data.get("remark", ""),
    )
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return {"success": True, "message": "设备已新增", "data": {"id": eq.id}}


@router.put("/equipments/{eq_id}")
def update_equipment(eq_id: int, data: Dict[str, Any], db: Session = Depends(get_db)):
    """更新设备"""
    eq = db.query(models.FactoryEquipment).filter_by(id=eq_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="设备不存在")
    for field in ["equipment_code", "equipment_name", "category", "specification",
                  "location", "status", "unit", "remark"]:
        if field in data:
            setattr(eq, field, data[field])
    if "daily_capacity_target" in data:
        eq.daily_capacity_target = float(data.get("daily_capacity_target") or 0)
    db.commit()
    return {"success": True, "message": "设备已更新"}


@router.delete("/equipments/{eq_id}")
def delete_equipment(eq_id: int, db: Session = Depends(get_db)):
    """删除设备（级联删除产能记录）"""
    eq = db.query(models.FactoryEquipment).filter_by(id=eq_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="设备不存在")
    db.delete(eq)
    db.commit()
    return {"success": True, "message": "设备已删除"}


@router.get("/equipments/export")
def export_equipments(db: Session = Depends(get_db)):
    """导出设备台账（与导入模板同表头，可直接回导）"""
    from fastapi.responses import StreamingResponse
    import openpyxl
    eqs = db.query(models.FactoryEquipment).order_by(models.FactoryEquipment.equipment_code).all()
    status_map = {"running": "运行", "idle": "停机", "maintenance": "维修", "scrapped": "报废"}
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "设备台账"
    headers = ["设备编码", "设备名称", "类别", "规格型号", "位置", "状态", "日产能目标", "单位", "备注"]
    ws.append(headers)
    for e in eqs:
        ws.append([
            e.equipment_code or "", e.equipment_name or "", e.category or "",
            e.specification or "", e.location or "", status_map.get(e.status or "", e.status or ""),
            float(e.daily_capacity_target or 0), e.unit or "", e.remark or "",
        ])
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 18
    from fastapi.responses import StreamingResponse as _SR
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return _SR(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=equipments.xlsx"})


@router.get("/capacity-daily/export")
def export_capacity_daily(
    equipment_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """导出产能记录（支持日期范围筛选，含达成率）"""
    from fastapi.responses import StreamingResponse
    import openpyxl
    q = db.query(models.EquipmentCapacityDaily, models.FactoryEquipment).join(
        models.FactoryEquipment, models.EquipmentCapacityDaily.equipment_id == models.FactoryEquipment.id
    )
    if equipment_id:
        q = q.filter(models.EquipmentCapacityDaily.equipment_id == equipment_id)
    sd = _to_date(start_date)
    ed = _to_date(end_date)
    if sd:
        q = q.filter(models.EquipmentCapacityDaily.report_date >= sd)
    if ed:
        q = q.filter(models.EquipmentCapacityDaily.report_date <= ed)
    rows = q.order_by(models.EquipmentCapacityDaily.report_date.desc(),
                      models.EquipmentCapacityDaily.id.desc()).all()
    shift_map = {"day": "白班", "night": "夜班", "full": "全天"}
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "产能记录"
    headers = ["日期", "设备编码", "设备名称", "班次", "实际产量", "目标产量", "达成率%", "操作人", "备注"]
    ws.append(headers)
    for r in rows:
        c, e = r.EquipmentCapacityDaily, r.FactoryEquipment
        actual = float(c.actual_output or 0)
        target = float(c.target_output or 0)
        rate = round(actual / target * 100, 1) if target > 0 else ""
        ws.append([
            c.report_date.isoformat() if c.report_date else "",
            e.equipment_code or "", e.equipment_name or "",
            shift_map.get(c.shift or "", c.shift or ""),
            actual, target, rate, c.operator or "", c.remark or "",
        ])
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 16
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=capacity_daily.xlsx"})


@router.get("/capacity-daily/template")
def download_capacity_template(db: Session = Depends(get_db)):
    """下载产能上报Excel模板：自动带全部设备的真实编码/名称/日产能目标，填数量即可导入"""
    from fastapi.responses import StreamingResponse
    import openpyxl
    equipments = db.query(models.FactoryEquipment).all()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "产能上报"
    headers = ["设备编码", "设备名称", "日期", "班次", "目标产量", "实际产量", "操作人", "备注"]
    ws.append(headers)
    for e in equipments:
        ws.append([
            e.equipment_code or "", e.equipment_name or "",
            "", "白班", float(e.daily_capacity_target or 0), "", "", "",
        ])
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 14
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=capacity_import_template.xlsx"})


@router.get("/equipments/template")
def download_equipment_template():
    """下载设备Excel导入模板"""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "设备台账"
    # 表头
    headers = ["设备编码", "设备名称", "类别", "规格型号", "位置", "状态", "日产能目标", "单位", "备注"]
    ws.append(headers)
    # 示例行
    ws.append(["EQ-003", "立式铣床", "加工设备", "X7132", "车间A-03", "running", 50, "件", "示例数据"])
    ws.append(["EQ-004", "装配台", "装配设备", "AT-200", "车间C-01", "idle", 30, "件", "示例数据"])
    # 调整列宽
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 18
    # 返回文件流
    from fastapi.responses import StreamingResponse
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=equipment_template.xlsx"}
    )


@router.post("/equipments/import")
async def import_equipments(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Excel批量导入设备台账
    表头：设备编码 | 设备名称 | 类别 | 规格型号 | 位置 | 状态 | 日产能目标 | 单位 | 备注
    """
    content = await file.read()
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        ws = wb.active
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Excel解析失败: {str(e)}")

    # 读取表头并规范化
    headers = []
    for cell in ws[1]:
        val = str(cell.value or "").strip()
        import re
        norm = re.sub(r'[（(].*?[)）]', '', val).replace(' ', '').lower()
        headers.append(norm)

    def _find_col(keywords):
        for i, h in enumerate(headers):
            for kw in keywords:
                if kw in h:
                    return i
        return -1

    col_code = _find_col(["设备编码", "编码", "code"])
    col_name = _find_col(["设备名称", "名称", "name"])
    col_cat = _find_col(["类别", "category"])
    col_spec = _find_col(["规格型号", "规格", "spec"])
    col_loc = _find_col(["位置", "location"])
    col_status = _find_col(["状态", "status"])
    col_target = _find_col(["日产能目标", "产能目标", "目标", "target"])
    col_unit = _find_col(["单位", "unit"])
    col_remark = _find_col(["备注", "remark"])

    if col_code < 0 or col_name < 0:
        raise HTTPException(status_code=400, detail="Excel必须包含「设备编码」和「设备名称」列")

    # 类别中文映射
    valid_categories = ["加工设备", "装配设备", "检测与调试设备", "辅助设备"]
    # 状态映射
    status_map = {
        "运行": "running", "闲置": "idle", "维修": "maintenance", "报废": "scrapped",
        "running": "running", "idle": "idle", "maintenance": "maintenance", "scrapped": "scrapped",
    }

    success_count = 0
    error_rows = []
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not row or not any(row):
            continue
        code = str(row[col_code] or "").strip() if col_code < len(row) else ""
        name = str(row[col_name] or "").strip() if col_name < len(row) else ""
        if not code or not name:
            error_rows.append(f"第{row_idx}行：设备编码或名称为空")
            continue
        # 检查编码唯一
        if db.query(models.FactoryEquipment).filter_by(equipment_code=code).first():
            error_rows.append(f"第{row_idx}行：设备编码 {code} 已存在")
            continue
        # 类别
        cat = str(row[col_cat] or "加工设备").strip() if col_cat >= 0 and col_cat < len(row) else "加工设备"
        if cat not in valid_categories:
            cat = "加工设备"
        # 状态
        raw_status = str(row[col_status] or "running").strip() if col_status >= 0 and col_status < len(row) else "running"
        status = status_map.get(raw_status, "running")
        # 日产能目标
        target = float(row[col_target] or 0) if col_target >= 0 and col_target < len(row) else 0
        unit = str(row[col_unit] or "件").strip() if col_unit >= 0 and col_unit < len(row) else "件"
        spec = str(row[col_spec] or "").strip() if col_spec >= 0 and col_spec < len(row) else ""
        loc = str(row[col_loc] or "").strip() if col_loc >= 0 and col_loc < len(row) else ""
        remark = str(row[col_remark] or "").strip() if col_remark >= 0 and col_remark < len(row) else ""

        eq = models.FactoryEquipment(
            equipment_code=code,
            equipment_name=name,
            category=cat,
            specification=spec,
            location=loc,
            status=status,
            daily_capacity_target=target,
            unit=unit,
            remark=remark,
        )
        db.add(eq)
        success_count += 1

    db.commit()
    return {
        "success": True,
        "message": f"导入完成：成功{success_count}台，失败{len(error_rows)}条",
        "success_count": success_count,
        "error_rows": error_rows,
    }


# ============================================================
# 2. 每日产能上报
# ============================================================

@router.get("/capacity-daily")
def list_capacity_daily(
    equipment_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """查询每日产能记录，支持按设备和日期范围筛选"""
    q = db.query(models.EquipmentCapacityDaily, models.FactoryEquipment).join(
        models.FactoryEquipment, models.EquipmentCapacityDaily.equipment_id == models.FactoryEquipment.id
    )
    if equipment_id:
        q = q.filter(models.EquipmentCapacityDaily.equipment_id == equipment_id)
    sd = _to_date(start_date)
    ed = _to_date(end_date)
    if sd:
        q = q.filter(models.EquipmentCapacityDaily.report_date >= sd)
    if ed:
        q = q.filter(models.EquipmentCapacityDaily.report_date <= ed)
    rows = q.order_by(models.EquipmentCapacityDaily.report_date.desc(),
                      models.EquipmentCapacityDaily.id.desc()).all()
    return {
        "success": True,
        "data": [{
            "id": r.EquipmentCapacityDaily.id,
            "equipment_id": r.EquipmentCapacityDaily.equipment_id,
            "equipment_code": r.FactoryEquipment.equipment_code,
            "equipment_name": r.FactoryEquipment.equipment_name,
            "report_date": r.EquipmentCapacityDaily.report_date.isoformat() if r.EquipmentCapacityDaily.report_date else None,
            "shift": r.EquipmentCapacityDaily.shift,
            "actual_output": r.EquipmentCapacityDaily.actual_output or 0,
            "target_output": r.EquipmentCapacityDaily.target_output or 0,
            "operator": r.EquipmentCapacityDaily.operator or "",
            "remark": r.EquipmentCapacityDaily.remark or "",
            "created_at": r.EquipmentCapacityDaily.created_at.isoformat() if r.EquipmentCapacityDaily.created_at else None,
        } for r in rows],
        "total": len(rows),
    }


@router.post("/capacity-daily")
def create_capacity_daily(data: Dict[str, Any], db: Session = Depends(get_db)):
    """手动录入一条每日产能记录"""
    eq_id = data.get("equipment_id")
    report_date = _to_date(data.get("report_date"))
    if not eq_id or not report_date:
        raise HTTPException(status_code=400, detail="设备和日期不能为空")
    eq = db.query(models.FactoryEquipment).filter_by(id=eq_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="设备不存在")
    actual = float(data.get("actual_output") or 0)
    # 如果没传目标产量，默认取设备日产能目标
    target = float(data.get("target_output") or eq.daily_capacity_target or 0)
    rec = models.EquipmentCapacityDaily(
        equipment_id=eq_id,
        report_date=report_date,
        shift=data.get("shift", "day"),
        actual_output=actual,
        target_output=target,
        operator=data.get("operator", ""),
        remark=data.get("remark", ""),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {"success": True, "message": "产能记录已录入", "data": {"id": rec.id}}


@router.delete("/capacity-daily/{rec_id}")
def delete_capacity_daily(rec_id: int, db: Session = Depends(get_db)):
    """删除一条产能记录"""
    rec = db.query(models.EquipmentCapacityDaily).filter_by(id=rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(rec)
    db.commit()
    return {"success": True, "message": "记录已删除"}


@router.post("/capacity-daily/import")
async def import_capacity_daily(file: UploadFile = File(...), report_date: Optional[str] = Form(None), db: Session = Depends(get_db)):
    """Excel批量导入每日产能
    表头：设备编码（必填） | 日期 | 班次 | 实际产量 | 目标产量 | 操作人 | 备注
    说明：Excel可只含「设备编码」列，日期由前端手动传入（report_date）。
    """
    content = await file.read()
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        ws = wb.active
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Excel解析失败: {str(e)}")

    # 读取表头
    headers = []
    for cell in ws[1]:
        val = str(cell.value or "").strip()
        # 规范化：去括号内容、去空格、转小写
        import re
        norm = re.sub(r'[（(].*?[)）]', '', val).replace(' ', '').lower()
        headers.append(norm)

    def _find_col(keywords):
        # 优先精确匹配表头，避免「实际产量」被「产量」子串错配到「目标产量」列
        for kw in keywords:
            for i, h in enumerate(headers):
                if h == kw:
                    return i
        for kw in keywords:
            for i, h in enumerate(headers):
                if kw in h:
                    return i
        return -1

    col_code = _find_col(["设备编码", "编码", "设备编号", "编号", "设备名称", "设备", "code", "name"])
    col_date = _find_col(["日期", "date"])
    col_shift = _find_col(["班次", "shift"])
    col_actual = _find_col(["实际产量", "实际", "actual", "产量"])
    col_target = _find_col(["目标产量", "目标", "target"])
    col_operator = _find_col(["操作人", "工人", "operator"])
    col_remark = _find_col(["备注", "remark"])

    if col_code < 0:
        raise HTTPException(status_code=400, detail="Excel必须包含「设备编码」列")

    # 解析手动传入的默认日期
    default_date = None
    if report_date:
        default_date = _to_date(report_date)
        if not default_date:
            raise HTTPException(status_code=400, detail="手动录入的日期格式无效")

    # 日期列不存在时必须有手动传入的日期
    if col_date < 0 and not default_date:
        raise HTTPException(status_code=400, detail="Excel未含「日期」列，请先在页面上手动选择录入日期")

    # 预加载设备：编码（忽略大小写/空格/全角/横线变体）与名称多级匹配
    _DASHES = '－—–‐―ー'
    def _norm(s):
        s = str(s or "").strip().replace('（', '(').replace('）', ')').replace(' ', '').lower()
        for d in _DASHES:
            s = s.replace(d, '-')
        return s

    def _alnum(s):
        # 只保留字母数字汉字，横线/下划线/点等全部忽略（如 EQ-Lathe-01 与 EQinLathe01 互认）
        return re.sub(r'[^a-z0-9\u4e00-\u9fff]', '', _norm(s))

    equipments = db.query(models.FactoryEquipment).all()
    eq_by_code = {_norm(e.equipment_code): e for e in equipments}
    eq_by_code_alnum = {_alnum(e.equipment_code): e for e in equipments if e.equipment_code}
    eq_by_name = {str(e.equipment_name or "").strip(): e for e in equipments}
    eq_by_name_norm = {_norm(e.equipment_name): e for e in equipments}

    _SHIFT_MAP = {"白班": "day", "day": "day", "夜班": "night", "night": "night",
                  "全天": "full", "full": "full", "白": "day", "夜": "night"}

    def _to_float(v):
        if v is None or v == "":
            return 0.0
        try:
            return float(v)
        except (TypeError, ValueError):
            try:
                return float(re.sub(r"[^\d.\-]", "", str(v)) or 0)
            except Exception:
                return 0.0

    success_count = 0
    error_rows = []
    seen_codes = []  # Excel里没匹配上的设备编码（去重，用于提示对照）
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not row or not any(row):
            continue
        code = str(row[col_code] or "").strip() if col_code < len(row) else ""
        if not code:
            error_rows.append(f"第{row_idx}行：设备编码为空")
            continue
        # 五级匹配：编码规范→编码字母数字→名称精确→名称规范→双向包含（唯一才认）
        eq = eq_by_code.get(_norm(code)) or eq_by_code_alnum.get(_alnum(code))
        if not eq:
            eq = eq_by_name.get(code) or eq_by_name_norm.get(_norm(code))
        if not eq:
            cands = [e for e in equipments
                     if code in str(e.equipment_name or "") or str(e.equipment_name or "") in code]
            eq = cands[0] if len(cands) == 1 else None
        if not eq:
            error_rows.append(f"第{row_idx}行：设备「{code}」不存在")
            if code not in seen_codes:
                seen_codes.append(code)
            continue
        # 日期：优先Excel列，否则用手动传入的默认日期
        rd = None
        if col_date >= 0 and col_date < len(row) and row[col_date]:
            rd = _to_date(row[col_date])
            if not rd:
                error_rows.append(f"第{row_idx}行：日期格式错误")
                continue
        else:
            rd = default_date
        shift_raw = str(row[col_shift] or "").strip() if col_shift >= 0 and col_shift < len(row) else ""
        shift = _SHIFT_MAP.get(shift_raw, _SHIFT_MAP.get(shift_raw.lower(), "day"))
        actual = _to_float(row[col_actual]) if col_actual >= 0 and col_actual < len(row) else 0.0
        target = _to_float(row[col_target]) if col_target >= 0 and col_target < len(row) else (eq.daily_capacity_target or 0)
        operator = str(row[col_operator] or "").strip() if col_operator >= 0 and col_operator < len(row) else ""
        remark = str(row[col_remark] or "").strip() if col_remark >= 0 and col_remark < len(row) else ""

        rec = models.EquipmentCapacityDaily(
            equipment_id=eq.id,
            report_date=rd,
            shift=shift,
            actual_output=actual,
            target_output=target,
            operator=operator,
            remark=remark,
        )
        db.add(rec)
        success_count += 1

    db.commit()
    hint = ""
    if error_rows and success_count == 0 and equipments:
        hint = "。系统现有设备：" + "、".join(f"{e.equipment_code} {e.equipment_name}" for e in equipments)
        if seen_codes:
            hint += "；你表中填的：" + "、".join(seen_codes[:10])
    return {
        "success": True,
        "message": f"导入完成：成功{success_count}条，失败{len(error_rows)}条{hint}",
        "success_count": success_count,
        "error_rows": error_rows,
    }


# ============================================================
# 3. 产能进度线数据（每日进度 + 累计进度）
# ============================================================

@router.get("/capacity-daily/progress")
def get_capacity_progress(
    equipment_id: Optional[int] = None,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """获取产能进度线数据
    - daily: 每日实际产量 vs 目标产量（每日进度线）
    - cumulative: 累计实际产量 vs 累计目标产量（总项目进度线）
    """
    # 计算日期范围
    today = datetime.date.today()
    start = today - datetime.timedelta(days=days - 1)

    q = db.query(models.EquipmentCapacityDaily).filter(
        models.EquipmentCapacityDaily.report_date >= start,
        models.EquipmentCapacityDaily.report_date <= today,
    )
    if equipment_id:
        q = q.filter(models.EquipmentCapacityDaily.equipment_id == equipment_id)
    records = q.order_by(models.EquipmentCapacityDaily.report_date).all()

    # 按日期聚合
    daily_map = {}
    for r in records:
        d = r.report_date.isoformat()
        if d not in daily_map:
            daily_map[d] = {"actual": 0.0, "target": 0.0}
        daily_map[d]["actual"] += r.actual_output or 0
        daily_map[d]["target"] += r.target_output or 0

    # 生成连续日期序列
    dates = []
    daily_actual = []
    daily_target = []
    cum_actual = []
    cum_target = []
    sum_a = 0.0
    sum_t = 0.0
    cur = start
    while cur <= today:
        d = cur.isoformat()
        dates.append(d)
        a = daily_map.get(d, {}).get("actual", 0.0)
        t = daily_map.get(d, {}).get("target", 0.0)
        daily_actual.append(round(a, 2))
        daily_target.append(round(t, 2))
        sum_a += a
        sum_t += t
        cum_actual.append(round(sum_a, 2))
        cum_target.append(round(sum_t, 2))
        cur += datetime.timedelta(days=1)

    return {
        "success": True,
        "data": {
            "dates": dates,
            "daily_actual": daily_actual,
            "daily_target": daily_target,
            "cumulative_actual": cum_actual,
            "cumulative_target": cum_target,
            "total_actual": round(sum_a, 2),
            "total_target": round(sum_t, 2),
        },
    }


# ============================================================
# 设备每日水电费（模拟数据自动计提 → 财务制造费用）
# ============================================================
# 各设备模拟日水电费标准（元/天）：按设备名称关键词匹配，大功率设备耗电高
_UTIL_STD = [
    # (关键词, 电费/天, 水费/天)
    (["激光"], 150.0, 8.0),
    (["加工中心", "CNC"], 120.0, 3.0),
    (["数控车", "车床"], 85.0, 2.0),
    (["铣床"], 60.0, 2.0),
    (["线切割"], 55.0, 6.0),
    (["焊"], 45.0, 1.0),
    (["钻"], 25.0, 1.0),
]
_UTIL_DEFAULT = (40.0, 2.0)


def _equipment_daily_utility(name: str):
    """按设备名返回模拟 (电费, 水费) 元/天"""
    for kws, ele, wtr in _UTIL_STD:
        if any(k in (name or "") for k in kws):
            return ele, wtr
    return _UTIL_DEFAULT


def auto_accrue_utility_fees(db, start_date=None, end_date=None):
    """自动计提设备每日水电费（模拟数据）并生成财务凭证。
    - 范围：默认本月1号 ~ 今天，每台运行中设备每天一条明细
    - 凭证：按天汇总一张，借 5101 制造费用-水电费 / 贷 2202 应付账款
    - 幂等：明细按(设备,日期)查重，凭证按 reference_doc=UTIL-日期 查重
    返回 (明细数, 凭证数)
    """
    import uuid
    today = datetime.date.today()
    end_date = end_date or today
    if start_date is None:
        start_date = end_date.replace(day=1)

    eqs = db.query(models.FactoryEquipment).filter(
        models.FactoryEquipment.status == "running").all()
    if not eqs:
        return 0, 0

    # 已有明细键集合（幂等）
    existing = {(r.equipment_id, r.fee_date) for r in
                db.query(models.UtilityFeeRecord).all()}
    new_records = []
    d = start_date
    while d <= end_date:
        for e in eqs:
            if (e.id, d) in existing:
                continue
            ele, wtr = _equipment_daily_utility(e.equipment_name)
            rec = models.UtilityFeeRecord(
                account_set_id=1,
                equipment_id=e.id, equipment_code=e.equipment_code,
                equipment_name=e.equipment_name,
                fee_date=d, electric_fee=ele, water_fee=wtr,
                total_amount=round(ele + wtr, 2), source="auto")
            db.add(rec)
            new_records.append((d, rec))
        d += datetime.timedelta(days=1)
    if not new_records:
        return 0, 0
    db.flush()

    # 按天汇总生成凭证
    voucher_cnt = 0
    by_date = {}
    for d, rec in new_records:
        by_date.setdefault(d, []).append(rec)
    for d, recs in by_date.items():
        ref = f"UTIL-{d.isoformat()}"
        dup = db.query(models.VoucherDB).filter(
            models.VoucherDB.reference_type == "UTILITY_FEE",
            models.VoucherDB.reference_doc == ref).first()
        if dup:
            continue
        total = round(sum(float(r.total_amount) for r in recs), 2)
        if total <= 0:
            continue
        vno = f"SD-{d.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        vdb = models.VoucherDB(
            account_set_id=1, voucher_no=vno,
            voucher_type=models.VoucherType.GENERAL,
            voucher_date=d, status=models.VoucherStatus.POSTED,
            preparer="系统自动", poster="系统自动",
            reference_doc=ref, reference_type="UTILITY_FEE",
            approved_at=datetime.datetime.now(),
            posted_at=datetime.datetime.now())
        db.add(vdb)
        db.flush()
        names = "、".join(sorted({r.equipment_name for r in recs}))
        summ = f"车间设备水电费 {d.isoformat()}（{len(recs)}台·{names}）"
        db.add(models.VoucherEntry(
            voucher_id=vdb.id, account_code="5101", account_name="制造费用",
            debit=total, credit=0, summary=summ))
        db.add(models.VoucherEntry(
            voucher_id=vdb.id, account_code="2202", account_name="应付账款",
            debit=0, credit=total, summary=summ))
        for r in recs:
            r.voucher_id = vdb.id
        voucher_cnt += 1
    db.commit()
    return len(new_records), voucher_cnt


@router.get("/utility-fee", tags=["我的工厂"])
def list_utility_fee(month: Optional[str] = None, db: Session = Depends(get_db)):
    """查询设备每日水电费明细（默认本月）+ 自动补提（保证模拟数据齐全）"""
    try:
        auto_accrue_utility_fees(db)
    except Exception:
        import traceback
        traceback.print_exc()
    today = datetime.date.today()
    if month:
        try:
            y, m = month.split("-")
            start = datetime.date(int(y), int(m), 1)
        except Exception:
            start = today.replace(day=1)
    else:
        start = today.replace(day=1)
    recs = db.query(models.UtilityFeeRecord).filter(
        models.UtilityFeeRecord.fee_date >= start,
        models.UtilityFeeRecord.fee_date <= today
    ).order_by(models.UtilityFeeRecord.fee_date.desc(),
               models.UtilityFeeRecord.equipment_id).all()
    # 按设备汇总
    by_equip = {}
    by_date = {}
    total = 0.0
    for r in recs:
        amt = float(r.total_amount or 0)
        total += amt
        k = r.equipment_name or r.equipment_code
        e = by_equip.setdefault(k, {"name": k, "code": r.equipment_code,
                                    "electric": 0.0, "water": 0.0, "total": 0.0, "days": 0})
        e["electric"] += float(r.electric_fee or 0)
        e["water"] += float(r.water_fee or 0)
        e["total"] += amt
        e["days"] += 1
        ds = r.fee_date.isoformat()
        by_date[ds] = by_date.get(ds, 0.0) + amt
    return {
        "success": True,
        "data": {
            "total": round(total, 2),
            "by_equipment": sorted(by_equip.values(), key=lambda x: -x["total"]),
            "by_date": [{"date": k, "amount": round(by_date[k], 2)} for k in sorted(by_date.keys(), reverse=True)],
            "records": [{
                "date": r.fee_date.isoformat(),
                "equipment": r.equipment_name, "code": r.equipment_code,
                "electric": float(r.electric_fee or 0), "water": float(r.water_fee or 0),
                "total": float(r.total_amount or 0),
                "voucher_id": r.voucher_id,
            } for r in recs],
        },
    }
