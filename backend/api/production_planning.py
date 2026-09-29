"""
生产计划表：根据机器日产能目标 + 项目交付日期自动排产
=====================================================
数据来源：
- 生产需求：技术拆解清单 TechnicalDecomposition（MANUFACTURABLE可加工 / ASSEMBLABLE可装配）
- 交付日期：WBSProject.planned_end
- 机器产能：FactoryEquipment.daily_capacity_target（status=running 的设备）

排产逻辑（倒排 + 均匀分配）：
- 所需工作日 = ceil(数量 / 日产能合计)，至少1天
- 最晚开工日 = 交付日期 - (所需工作日 - 1)
- 建议开工日 = max(今天, 最晚开工日)，均匀铺排每日产量
- 风险判定：今天 > 交付日期 → 已逾期(红)；最晚开工日 < 今天 → 须立即开工(橙)；否则可按期(绿)
- 每日负荷 = 当日全部任务计划产量 / 日产能合计
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date, timedelta
import math

from .. import models
from ..app import make_response
from ..database import get_db

router = APIRouter()


@router.get("/production-plan", tags=["生产计划"])
def get_production_plan(db: Session = Depends(get_db)):
    today = date.today()

    # 1. 机器产能池（运行中的设备，日产能目标>0）
    eqs = db.query(models.FactoryEquipment).filter(
        models.FactoryEquipment.status == "running",
        models.FactoryEquipment.daily_capacity_target > 0
    ).all()
    machines = [{
        "id": e.id, "code": e.equipment_code, "name": e.equipment_name,
        "category": e.category, "daily_capacity": float(e.daily_capacity_target or 0),
        "unit": e.unit or "件",
    } for e in eqs]
    total_cap = sum(m["daily_capacity"] for m in machines)
    cap_unit = machines[0]["unit"] if machines else "件"
    idle_cnt = db.query(models.FactoryEquipment).filter(
        models.FactoryEquipment.status != "running"
    ).count()

    # 2. 项目交付日期
    projects = db.query(models.WBSProject).all()
    proj_map = {p.id: p for p in projects}

    # 3. 生产需求：技术拆解 可加工/可装配
    comps = db.query(models.TechnicalDecomposition).filter(
        models.TechnicalDecomposition.category.in_(["MANUFACTURABLE", "ASSEMBLABLE"])
    ).all()

    # 有交付物料但未做技术拆解的项目（提示）
    decomp_proj_ids = set(c.project_id for c in
        db.query(models.TechnicalDecomposition).filter(
            models.TechnicalDecomposition.category == "PURCHASABLE").all()) | \
        set(c.project_id for c in comps)

    def _dstr(d):
        return d.isoformat() if d else None

    def _mk_task(p, code, name, spec, qty, unit, category_label):
        """构造排产任务：倒排工期 + 均匀分配每日产量"""
        delivery = p.planned_end if p else None
        task = {
            "project_id": p.id if p else None,
            "project_no": p.project_no if p else "",
            "project_name": p.project_name if p else "",
            "part_code": code or "",
            "part_name": name or "",
            "spec": spec or "",
            "category": category_label,
            "qty": float(qty or 0),
            "unit": unit or "个",
            "delivery_date": _dstr(delivery),
            "needed_days": None,
            "latest_start": None,
            "suggested_start": None,
            "suggested_end": None,
            "risk": "OK", "risk_label": "可按期", "late_days": 0,
            "alloc": {},
        }
        if task["qty"] <= 0:
            return None
        if total_cap <= 0:
            task["risk"], task["risk_label"] = "NO_CAP", "无可用产能"
        elif delivery is None:
            task["risk"], task["risk_label"] = "NO_DATE", "缺交付日期"
        else:
            days = max(1, math.ceil(task["qty"] / total_cap))
            latest_start = delivery - timedelta(days=days - 1)
            start = max(today, latest_start)
            end = start + timedelta(days=days - 1)
            base = int(task["qty"] // days)
            rem = int(task["qty"] - base * days)
            alloc = {}
            for i in range(days):
                ds = _dstr(start + timedelta(days=i))
                q = base + (1 if i < rem else 0)
                alloc[ds] = q
                date_load[ds] = date_load.get(ds, 0) + q
            task.update({
                "needed_days": days,
                "latest_start": _dstr(latest_start),
                "suggested_start": _dstr(start),
                "suggested_end": _dstr(end),
                "alloc": alloc,
            })
            if today > delivery:
                task["risk"] = "OVERDUE"
                task["risk_label"] = "已逾期"
                task["late_days"] = (today - delivery).days
            elif latest_start < today:
                task["risk"] = "TIGHT"
                task["risk_label"] = "须立即开工"
            else:
                task["risk"] = "OK"
                task["risk_label"] = "可按期"
        return task

    tasks = []
    date_load = {}  # date_str -> 计划产量合计
    # 3a. 已做技术拆解的项目：排 可加工/可装配 零件
    for c in comps:
        p = proj_map.get(c.project_id)
        if not p:
            continue
        label = "加工" if c.category == "MANUFACTURABLE" else "装配"
        t = _mk_task(p, c.part_code, c.part_name, c.specification, c.quantity, c.unit, label)
        if t:
            tasks.append(t)

    # 3b. 未拆解但有交付物料的项目：排成品总装任务（保证页面立即可用）
    no_decomp_ids = set()
    for p in projects:
        if p.id in decomp_proj_ids or not p.planned_end or p.status in ("COMPLETED", "CANCELLED"):
            continue
        dels = db.query(models.ProjectDeliverable).filter(
            models.ProjectDeliverable.project_id == p.id).all()
        if not dels:
            continue
        no_decomp_ids.add(p.id)
        for dv in dels:
            t = _mk_task(p, dv.material_code, dv.material_name, dv.specification,
                         dv.quantity, dv.unit, "总装")
            if t:
                tasks.append(t)

    # 交付日期早的排前面
    tasks.sort(key=lambda t: (t["delivery_date"] or "9999", t["project_no"] or ""))

    # 4. 每日负荷（从今天起到最后完工日）
    if tasks:
        max_end = max((t["suggested_end"] or t["delivery_date"] or "") for t in tasks)
        end_d = date.fromisoformat(max_end) if max_end and max_end != "9999" else today
    else:
        end_d = today
    end_d = min(end_d, today + timedelta(days=60))
    date_loads = []
    d = today
    while d <= end_d:
        ds = _dstr(d)
        load = round(date_load.get(ds, 0), 2)
        rate = round(load / total_cap * 100, 1) if total_cap > 0 else 0
        date_loads.append({"date": ds, "load": load, "rate": rate})
        d += timedelta(days=1)

    # 未拆解但有交付物料的项目提示
    no_decomp = [
        {"id": p.id, "project_no": p.project_no, "project_name": p.project_name,
         "delivery_date": _dstr(p.planned_end)}
        for p in projects if p.id in no_decomp_ids
    ]

    risk_cnt = len([t for t in tasks if t["risk"] in ("OVERDUE", "TIGHT")])
    return make_response(True, {
        "today": _dstr(today),
        "machines": machines,
        "machine_count": len(machines),
        "idle_machine_count": idle_cnt,
        "total_capacity": round(total_cap, 2),
        "capacity_unit": cap_unit,
        "tasks": tasks,
        "task_count": len(tasks),
        "risk_count": risk_cnt,
        "date_loads": date_loads,
        "no_decomposition_projects": no_decomp,
    })


@router.get("/optimal-schedule", tags=["生产计划"])
def get_optimal_schedule(db: Session = Depends(get_db)):
    try:
        return _optimal_schedule_impl(db)
    except Exception:
        import traceback
        from fastapi.responses import JSONResponse
        return JSONResponse({"success": False, "message": traceback.format_exc()})


# ---------- 智能排产：五规则配置 ----------
# 工序分组：(键, 名称, 设备名称关键词, 工序顺序)
_SP_GROUPS = [
    ("cut",      "下料", ["激光", "切割"], 1),
    ("weld",     "焊接", ["焊"], 2),
    ("machine",  "机加", ["CNC", "加工中心", "车床", "铣床", "线切割", "电火花"], 3),
    ("drill",    "钻孔", ["钻"], 4),
    ("assembly", "装配", ["装配", "组装"], 5),
]
# 自制件 → 工序分组 的品名关键词（按 下料→焊接→机加 的工艺链顺序匹配）
_SP_PART_KW = {
    "weld": ["焊", "底座", "钣金", "框架", "支架", "防护罩", "集尘罩", "管道", "柜体", "不锈钢件"],
    "cut":  ["冷轧", "钢板", "热轧", "钢件"],
}
_SP_RESERVE = 0.85  # 规则五·应急预留：每日只排满 85%，留 15% 弹性给插单返工


def _optimal_schedule_impl(db: Session = Depends(get_db)):
    """五规则智能排产（非标小批量多品种工厂）
    规则1 关键路径优先：焊接结构件 + 装配 标记⭐关键路径，同工序内优先排
    规则2 设备约束优先：瓶颈工序（工作量/产能最大）最先排、优先满负荷，其他工序配合其节奏
    规则3 物料齐套驱动：焊接必须等下料完工、钻孔必须等焊接回厂、装配必须等全部零件完工+采购到料
    规则4 负载平衡：同一工序逐日满负荷连续排产（85%线内），任务集中不碎片化
    规则5 应急预留：每日产能按85%计算，预留15%应对插单/返工
    """
    today = date.today()

    def _d(d):
        return d.isoformat() if isinstance(d, date) else d

    # ===== 1. 设备 → 工序产能池（运行中 + 日产能>0）=====
    eqs = db.query(models.FactoryEquipment).filter(
        models.FactoryEquipment.status == "running",
        models.FactoryEquipment.daily_capacity_target > 0
    ).all()
    cap = {}        # group -> 日产能
    eff_cap = {}    # group -> 扣预留后可用日产能
    equip_names = {g[0]: [] for g in _SP_GROUPS}
    for e in eqs:
        nm = e.equipment_name or ""
        for gkey, glabel, kws, _ in _SP_GROUPS:
            if any(k in nm for k in kws):
                v = float(e.daily_capacity_target or 0)
                cap[gkey] = cap.get(gkey, 0) + v
                equip_names[gkey].append(nm)
                break
    for gk, v in cap.items():
        eff_cap[gk] = v * _SP_RESERVE
    total_cap = sum(cap.values())

    # ===== 2. 任务：技术拆解 可加工/可装配 =====
    comps = db.query(models.TechnicalDecomposition).filter(
        models.TechnicalDecomposition.category.in_(["MANUFACTURABLE", "ASSEMBLABLE"])
    ).all()
    projects = {p.id: p for p in db.query(models.WBSProject).all()}

    # 采购到料日期（规则三·物料齐套）：项目关联采购订单明细的最大交付日期
    proj_arrival = {}
    try:
        po_rows = db.query(
            models.PurchaseOrder.project_id,
            models.PurchaseOrderItem.delivery_date
        ).join(models.PurchaseOrderItem,
               models.PurchaseOrderItem.purchase_order_id == models.PurchaseOrder.id).filter(
            models.PurchaseOrder.project_id.isnot(None),
            models.PurchaseOrder.status != "CANCELLED"
        ).all()
        for pid, dd in po_rows:
            if dd and (pid not in proj_arrival or dd > proj_arrival[pid]):
                proj_arrival[pid] = dd
    except Exception:
        proj_arrival = {}

    tasks = []
    for c in comps:
        p = projects.get(c.project_id)
        if not p:
            continue
        qty = float(c.quantity or 0)
        if qty <= 0:
            continue
        nm = c.part_name or ""
        if c.category == "ASSEMBLABLE":
            gk = "assembly"
        elif any(k in nm for k in _SP_PART_KW["weld"]):
            gk = "weld"   # 注意：焊接关键词先于下料匹配（"不锈钢件"含"钢件"子串但属焊接）
        elif any(k in nm for k in _SP_PART_KW["cut"]):
            gk = "cut"
        else:
            gk = "machine"
        # 规则1：焊接结构件 + 装配 在关键路径上（焊不完装不起来）
        critical = gk in ("weld", "assembly")
        tasks.append({
            "pid": p.id, "project_no": p.project_no or "", "project_name": p.project_name or "",
            "part_code": c.part_code or "", "part_name": nm, "spec": c.specification or "",
            "qty": qty, "unit": c.unit or "个",
            "delivery": p.planned_end, "g": gk,
            "critical": critical,
            "alloc": {}, "start": None, "end": None, "days": 0,
            "scheduled": cap.get(gk, 0) > 0,
        })

    # ===== 3. 瓶颈识别放到排产前（见 3b，仅在有设备工序中选）=====

    # 项目维度任务索引（dict缓存，避免热循环扫描）
    proj_tasks = {}
    for t in tasks:
        proj_tasks.setdefault(t["pid"], []).append(t)

    used = {}   # (group, date) -> 已占用量

    def _fwd(tasks_list, earliest_fn, key_fn):
        """规则4·正向连续排产：按优先级逐任务从最早日开始连续分配，每日不超85%预留线"""
        for t in sorted(tasks_list, key=key_fn):
            g = t["g"]
            if not t["scheduled"] or eff_cap.get(g, 0) <= 0:
                continue
            remain = t["qty"]
            d = earliest_fn(t)
            horizon = today + timedelta(days=365)
            while remain > 1e-9 and d <= horizon:
                free = eff_cap[g] - used.get((g, d), 0)
                if free > 1e-9:
                    take = min(remain, free)
                    used[(g, d)] = used.get((g, d), 0) + take
                    t["alloc"][d.isoformat()] = round(take, 2)
                    remain -= take
                d += timedelta(days=1)
            _finalize(t)

    def _finalize(t):
        if t["alloc"]:
            keys = sorted(t["alloc"].keys())
            t["start"], t["end"], t["days"] = keys[0], keys[-1], len(keys)

    def _proj_group_end(pid, g):
        e = [t["end"] for t in proj_tasks.get(pid, []) if t["g"] == g and t["end"]]
        return max(e) if e else None

    CRIT_KEY = lambda t: (0 if t["critical"] else 1, t["delivery"] or date.max, t["part_name"])
    EDD_KEY = lambda t: (t["delivery"] or date.max, 0 if t["critical"] else 1, t["part_name"])

    # ===== 3b. 规则2：识别瓶颈工序（工作量/可用产能 最大，仅在有设备工序中选；缺设备的工序单独提示）=====
    workload = {}
    for t in tasks:
        workload[t["g"]] = workload.get(t["g"], 0) + t["qty"]
    sched_ratio = {g: (workload[g] / eff_cap[g]) for g in workload if eff_cap.get(g, 0) > 0}
    bottleneck_g = max(sched_ratio, key=sched_ratio.get) if sched_ratio else None

    # ===== 4. 按工艺链顺序正向排产（物料齐套驱动，规则3优先于一切）=====
    # 下料 → 焊接（等下料） ‖ 机加（并行无前置） → 钻孔（等焊接） → 装配（等全部+到料）
    # 瓶颈工序在自身最早可行日内按⭐关键路径+EDF排满（规则2），设备不停闲
    # ① 下料：工艺链起点，今天就排，最早释放物料
    _fwd([t for t in tasks if t["g"] == "cut"], lambda t: today, EDD_KEY)

    # ② 焊接（瓶颈/关键路径）：必须等本项目下料完工
    def _weld_earliest(t):
        ce = _proj_group_end(t["pid"], "cut")
        return date.fromisoformat(ce) + timedelta(days=1) if ce else today
    _fwd([t for t in tasks if t["g"] == "weld"], _weld_earliest, CRIT_KEY)

    # ③ 机加：与焊接并行，无前置，EDF
    _fwd([t for t in tasks if t["g"] == "machine"], lambda t: today, EDD_KEY)

    # ④ 钻孔：焊接件回厂后才能钻
    def _drill_earliest(t):
        we = _proj_group_end(t["pid"], "weld")
        return date.fromisoformat(we) + timedelta(days=1) if we else today
    _fwd([t for t in tasks if t["g"] == "drill"], _drill_earliest, EDD_KEY)

    # ⑤ 装配：全部自制件完工 + 采购件到料 之后（物料齐套）
    def _asm_earliest(t):
        ends = [x["end"] for x in proj_tasks.get(t["pid"], [])
                if x["g"] != "assembly" and x["end"]]
        ready = max((date.fromisoformat(e) for e in ends), default=today)
        arr = proj_arrival.get(t["pid"])
        if arr and arr > ready:
            ready = arr
        return ready + timedelta(days=1)
    _fwd([t for t in tasks if t["g"] == "assembly"], _asm_earliest, CRIT_KEY)

    # ===== 10. 汇总输出 =====
    gmap = {g[0]: g[1] for g in _SP_GROUPS}
    tasks_out = []
    proj_summary = {}
    for t in tasks:
        end_d = date.fromisoformat(t["end"]) if t["end"] else None
        on_time = bool(t["end"] and t["delivery"] and end_d <= t["delivery"])
        if not t["scheduled"] or not t["end"]:
            reason = f"无{gmap[t['g']]}设备（请在设备台账添加/启用对应设备）" if cap.get(t["g"], 0) <= 0 else "产能不足未能排下"
        elif not on_time:
            reason = "缺交付日期" if not t["delivery"] else f"最早{t['end']}完工，晚于交付"
        else:
            reason = ""
        prereq = {"cut": "原材料", "weld": "下料完工", "machine": "图纸齐套",
                  "drill": "焊接件回厂", "assembly": "全部零件齐套+采购到料"}[t["g"]]
        tasks_out.append({
            "project_no": t["project_no"], "project_name": t["project_name"],
            "part_code": t["part_code"], "part_name": t["part_name"], "spec": t["spec"],
            "qty": t["qty"], "unit": t["unit"],
            "group": t["g"], "group_label": gmap[t["g"]],
            "equipment": equip_names.get(t["g"], []),
            "critical": t["critical"], "prereq": prereq,
            "start": t["start"], "end": t["end"], "days": t["days"],
            "alloc": t["alloc"], "on_time": on_time, "reason": reason,
            "delivery_date": _d(t["delivery"]),
        })
        ps = proj_summary.setdefault(t["pid"], {
            "project_no": t["project_no"], "project_name": t["project_name"],
            "delivery_date": _d(t["delivery"]), "parts": 0,
            "start": None, "end": None, "all_on_time": True, "critical": []})
        ps["parts"] += 1
        if t["start"] and (ps["start"] is None or t["start"] < ps["start"]):
            ps["start"] = t["start"]
        if t["end"] and (ps["end"] is None or t["end"] > ps["end"]):
            ps["end"] = t["end"]
        if not on_time:
            ps["all_on_time"] = False
        if t["critical"] and t["part_name"] not in ps["critical"]:
            ps["critical"].append(t["part_name"])

    # 工序分析
    group_analysis = []
    for gk, glabel, _, _ in _SP_GROUPS:
        if workload.get(gk, 0) <= 0:
            continue
        ends = [t["end"] for t in tasks if t["g"] == gk and t["end"]]
        group_analysis.append({
            "group": gk, "pool": glabel, "label": f"{glabel}工序",
            "equipments": equip_names.get(gk, []),
            "equip_count": len(equip_names.get(gk, [])),
            "capacity": round(cap.get(gk, 0), 2),
            "eff_capacity": round(eff_cap.get(gk, 0), 2),
            "unit": "件",
            "workload": round(workload.get(gk, 0), 2),
            "min_days": math.ceil(workload[gk] / eff_cap[gk]) if eff_cap.get(gk, 0) > 0 else None,
            "finish_date": max(ends) if ends else None,
            "is_bottleneck": gk == bottleneck_g,
        })
    bottleneck = None
    if bottleneck_g and group_analysis:
        ga = next((x for x in group_analysis if x["group"] == bottleneck_g), None)
        if ga:
            bottleneck = {"pool": ga["pool"], "label": ga["label"], "finish_date": ga["finish_date"]}

    # 每日负荷（总量+分工序），从今天到最晚完工，上限120天
    end_d = date.fromisoformat(max(t["end"] for t in tasks if t["end"])) if any(t["end"] for t in tasks) else today
    end_d = min(end_d, today + timedelta(days=120))
    daily, d = [], today
    while d <= end_d:
        ds = d.isoformat()
        gl = {gk: round(used.get((gk, d), 0), 2) for gk, *_ in _SP_GROUPS}
        load = round(sum(gl.values()), 2)
        rate = round(load / total_cap * 100, 1) if total_cap > 0 else 0
        daily.append({"date": ds, "load": load, "rate": rate, "groups": gl})
        d += timedelta(days=1)

    fastest = max((t["end"] for t in tasks if t["end"]), default=None)
    late_cnt = len([t for t in tasks_out if not t["on_time"]])
    return make_response(True, {
        "today": today.isoformat(),
        "rules": "①关键路径优先(⭐焊接/装配) ②瓶颈工序优先满负荷 ③物料齐套驱动(下料→焊接→钻孔→装配) ④负载均衡连续排产 ⑤预留15%应急产能",
        "total_capacity": round(total_cap, 2),
        "capacity_unit": "件",
        "reserve_pct": 15,
        "pool_analysis": group_analysis,
        "bottleneck": bottleneck,
        "fastest_finish": fastest,
        "task_count": len(tasks_out),
        "late_count": late_cnt,
        "tasks": tasks_out,
        "projects": list(proj_summary.values()),
        "daily_load": daily,
    })
