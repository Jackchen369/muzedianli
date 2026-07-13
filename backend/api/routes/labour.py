"""劳务管理 CRUD — 施工人员/工时/薪酬。"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db
from core.security import get_current_admin, get_current_user, require_finance
from models import Staff, WorkHour, Salary, Project, User

import io
from openpyxl import Workbook

router = APIRouter(prefix="/labour", tags=["劳务管理"])


def _is_admin(user: User) -> bool:
    return user.role in ("super_admin", "company_admin")


def _can_edit_hours(user: User) -> bool:
    """可以添加工时记录的角色：管理员 + 工地考勤员"""
    return user.role in ("super_admin", "company_admin", "attendance")


# ═══════════════════════════════════════════════════════════
#  Pydantic Schemas
# ═══════════════════════════════════════════════════════════

# ─── Staff ────────────────────────────────────────────

class StaffCreate(BaseModel):
    name: str
    id_card: Optional[str] = None
    phone: Optional[str] = None
    bank_card: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    id_photo: Optional[str] = None
    work_type: Optional[str] = None
    daily_wage: Optional[Decimal] = None
    user_id: Optional[int] = None


class StaffResponse(StaffCreate):
    id: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── WorkHour ─────────────────────────────────────────

class WorkHourCreate(BaseModel):
    staff_id: int
    project_id: Optional[int] = None
    work_date: date
    position_title: Optional[str] = None
    attendance_subsidy: Optional[Decimal] = Decimal("0")
    meal_allowance: Optional[Decimal] = Decimal("0")
    heat_subsidy: Optional[Decimal] = Decimal("0")
    weather_subsidy: Optional[Decimal] = Decimal("0")
    content: Optional[str] = None

    model_config = {"populate_by_name": True}


class WorkHourResponse(BaseModel):
    id: int
    staff_id: int
    project_id: Optional[int] = None
    work_date: date
    position_title: Optional[str] = None
    attendance_subsidy: Optional[Decimal] = Decimal("0")
    meal_allowance: Optional[Decimal] = Decimal("0")
    heat_subsidy: Optional[Decimal] = Decimal("0")
    weather_subsidy: Optional[Decimal] = Decimal("0")
    daily_total: Optional[Decimal] = Decimal("0")
    content: Optional[str] = None
    is_approved: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Salary ───────────────────────────────────────────

class SalaryCreate(BaseModel):
    staff_id: int
    project_id: Optional[int] = None
    salary_month: str  # YYYY-MM
    base_amount: Decimal = Decimal("0")
    hourly_wage: Decimal = Decimal("0")
    insurance_fund: Decimal = Decimal("0")
    project_bonus: Decimal = Decimal("0")
    net_amount: Decimal = Decimal("0")
    is_paid: bool = False
    paid_at: Optional[datetime] = None
    remark: Optional[str] = None


class SalaryResponse(SalaryCreate):
    id: int
    is_paid: bool
    paid_at: Optional[datetime] = None
    remark: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════
#  Staff CRUD
# ═══════════════════════════════════════════════════════════

@router.post("/staff", response_model=StaffResponse)
async def create_staff(
    req: StaffCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """创建施工人员"""
    staff = Staff(tenant_id=admin.tenant_id or 1, **req.model_dump())
    db.add(staff)
    await db.flush()
    await db.refresh(staff)
    return staff


@router.get("/staff", response_model=list[StaffResponse])
async def list_staff(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """施工人员列表 — 管理员和考勤员看全部，员工只看自己"""
    query = select(Staff).where(Staff.is_active == True)
    if not _is_admin(user) and user.role != "attendance":
        query = query.where(Staff.user_id == user.id)
    result = await db.execute(query.order_by(Staff.id))
    return result.scalars().all()


@router.get("/staff/{staff_id}", response_model=StaffResponse)
async def get_staff(
    staff_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """施工人员详情"""
    result = await db.execute(select(Staff).where(Staff.id == staff_id))
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="施工人员不存在")
    return staff


@router.put("/staff/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: int,
    req: StaffCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """更新施工人员 — 管理员可编辑全部，员工只能编辑自己的"""
    result = await db.execute(select(Staff).where(Staff.id == staff_id))
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="施工人员不存在")
    if not _is_admin(user) and staff.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权编辑此档案")
    for key, val in req.model_dump().items():
        setattr(staff, key, val)
    await db.flush()
    await db.refresh(staff)
    return staff


@router.delete("/staff/{staff_id}")
async def delete_staff(
    staff_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """删除施工人员"""
    result = await db.execute(select(Staff).where(Staff.id == staff_id))
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="施工人员不存在")
    await db.delete(staff)
    await db.flush()
    return {"detail": "删除成功"}


# ═══════════════════════════════════════════════════════════
#  WorkHour CRUD
# ═══════════════════════════════════════════════════════════

@router.post("/work-hours", response_model=WorkHourResponse)
async def create_work_hour(
    req: WorkHourCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """创建工时记录 — 管理员和工地考勤员可操作，自动计算日合计"""
    if not _can_edit_hours(user):
        raise HTTPException(status_code=403, detail="权限不足")
    # 获取关联人员的日薪
    staff_result = await db.execute(select(Staff).where(Staff.id == req.staff_id))
    staff = staff_result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="施工人员不存在")

    daily_wage = staff.daily_wage or Decimal("0")
    daily_total = (
        daily_wage
        + (req.attendance_subsidy or Decimal("0"))
        + (req.meal_allowance or Decimal("0"))
        + (req.heat_subsidy or Decimal("0"))
        + (req.weather_subsidy or Decimal("0"))
    )

    work_hour = WorkHour(
        tenant_id=user.tenant_id or 1,
        staff_id=req.staff_id,
        project_id=req.project_id,
        work_date=req.work_date,
        position_title=req.position_title,
        attendance_subsidy=req.attendance_subsidy,
        meal_allowance=req.meal_allowance,
        heat_subsidy=req.heat_subsidy,
        weather_subsidy=req.weather_subsidy,
        daily_total=daily_total,
        content=req.content,
        created_by=user.id,
    )
    db.add(work_hour)
    await db.flush()
    return work_hour


@router.get("/work-hours", response_model=list[WorkHourResponse])
async def list_work_hours(
    staff_id: Optional[int] = None,
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """工时记录列表 — 管理员看全部，考勤员看自己创建的，其他看自己的"""
    query = select(WorkHour).order_by(WorkHour.work_date.desc(), WorkHour.id)
    if _is_admin(user):
        pass  # 看全部
    elif user.role == "attendance":
        query = query.where(WorkHour.created_by == user.id)
    else:
        # 普通员工通过 staff.user_id 过滤
        subq = select(Staff.id).where(Staff.user_id == user.id).scalar_subquery()
        query = query.where(WorkHour.staff_id.in_(subq))
    if staff_id:
        query = query.where(WorkHour.staff_id == staff_id)
    if project_id:
        query = query.where(WorkHour.project_id == project_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/work-hours/{work_hour_id}", response_model=WorkHourResponse)
async def get_work_hour(
    work_hour_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """工时记录详情"""
    result = await db.execute(select(WorkHour).where(WorkHour.id == work_hour_id))
    wh = result.scalar_one_or_none()
    if not wh:
        raise HTTPException(status_code=404, detail="工时记录不存在")
    return wh


@router.put("/work-hours/{work_hour_id}", response_model=WorkHourResponse)
async def update_work_hour(
    work_hour_id: int,
    req: WorkHourCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """更新工时记录 — 管理员可编辑全部，考勤员只能编辑自己创建的未审核记录"""
    if not _can_edit_hours(user):
        raise HTTPException(status_code=403, detail="权限不足")
    result = await db.execute(select(WorkHour).where(WorkHour.id == work_hour_id))
    wh = result.scalar_one_or_none()
    if not wh:
        raise HTTPException(status_code=404, detail="工时记录不存在")
    # 考勤员只能编辑自己创建的未审核记录
    if user.role == "attendance":
        if wh.created_by != user.id:
            raise HTTPException(status_code=403, detail="只能编辑自己创建的记录")
        if wh.is_approved:
            raise HTTPException(status_code=403, detail="已审核的记录不可编辑")

    # 重新计算日合计
    staff_result = await db.execute(select(Staff).where(Staff.id == req.staff_id))
    staff = staff_result.scalar_one_or_none()
    daily_wage = staff.daily_wage if staff else Decimal("0")
    daily_total = (
        (daily_wage or Decimal("0"))
        + (req.attendance_subsidy or Decimal("0"))
        + (req.meal_allowance or Decimal("0"))
        + (req.heat_subsidy or Decimal("0"))
        + (req.weather_subsidy or Decimal("0"))
    )

    for key, val in req.model_dump().items():
        setattr(wh, key, val)
    wh.daily_total = daily_total
    await db.flush()
    await db.refresh(wh)
    return wh


@router.put("/work-hours/{work_hour_id}/approve", response_model=WorkHourResponse)
async def approve_work_hour(
    work_hour_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """审核工时记录 — 切换审核状态"""
    result = await db.execute(select(WorkHour).where(WorkHour.id == work_hour_id))
    wh = result.scalar_one_or_none()
    if not wh:
        raise HTTPException(status_code=404, detail="工时记录不存在")
    wh.is_approved = not wh.is_approved
    await db.flush()
    await db.refresh(wh)
    return wh


@router.delete("/work-hours/{work_hour_id}")
async def delete_work_hour(
    work_hour_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """删除工时记录 — 管理员可删除全部，考勤员只能删除自己创建的未审核记录"""
    result = await db.execute(select(WorkHour).where(WorkHour.id == work_hour_id))
    wh = result.scalar_one_or_none()
    if not wh:
        raise HTTPException(status_code=404, detail="工时记录不存在")
    if not _is_admin(user):
        if user.role != "attendance":
            raise HTTPException(status_code=403, detail="权限不足")
        if wh.created_by != user.id:
            raise HTTPException(status_code=403, detail="只能删除自己创建的记录")
        if wh.is_approved:
            raise HTTPException(status_code=403, detail="已审核的记录不可删除")
    await db.delete(wh)
    await db.flush()
    return {"detail": "删除成功"}


# ═══════════════════════════════════════════════════════════
#  Hourly Wage (工时工资提取)
# ═══════════════════════════════════════════════════════════

@router.get("/hourly-wage")
async def calc_hourly_wage(
    staff_id: int,
    month: str,  # YYYY-MM
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """计算某人员某月的工时工资 = 日薪 × 出勤天数"""
    staff_result = await db.execute(select(Staff).where(Staff.id == staff_id))
    staff = staff_result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=404, detail="人员不存在")

    daily_wage = staff.daily_wage or Decimal("0")

    # 解析月份为日期范围
    parts = month.split("-")
    y, m = int(parts[0]), int(parts[1])
    start_date = date(y, m, 1)
    if m == 12:
        end_date = date(y + 1, 1, 1)
    else:
        end_date = date(y, m + 1, 1)

    # 查询当月出勤记录
    result = await db.execute(
        select(WorkHour).where(
            WorkHour.staff_id == staff_id,
            WorkHour.work_date >= start_date,
            WorkHour.work_date < end_date,
        )
    )
    work_hours = result.scalars().all()
    work_days = len(work_hours)
    total = sum((wh.daily_total or Decimal("0")) for wh in work_hours)  # 工时工资 = 工时记录日合计之和

    return {
        "staff_id": staff_id,
        "month": month,
        "work_days": work_days,
        "daily_wage": str(staff.daily_wage or Decimal("0")),
        "total": str(total),
    }


# ═══════════════════════════════════════════════════════════
#  Salary CRUD
# ═══════════════════════════════════════════════════════════

@router.post("/salary", response_model=SalaryResponse)
async def create_salary(
    req: SalaryCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """创建薪酬记录"""
    salary = Salary(tenant_id=admin.tenant_id or 1, **req.model_dump())
    salary.is_paid = req.is_paid
    salary.paid_at = req.paid_at
    db.add(salary)
    await db.flush()
    return salary


@router.get("/salary", response_model=list[SalaryResponse])
async def list_salary(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """薪酬记录列表 — 管理员/财务看全部，其他角色看自己的"""
    if user.role == "attendance":
        raise HTTPException(status_code=403, detail="权限不足")
    query = select(Salary).order_by(Salary.salary_month.desc(), Salary.id)
    if not _is_admin(user):
        subq = select(Staff.id).where(Staff.user_id == user.id).scalar_subquery()
        query = query.where(Salary.staff_id.in_(subq))
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/salary/{salary_id}", response_model=SalaryResponse)
async def get_salary(
    salary_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """薪酬记录详情"""
    if user.role == "attendance":
        raise HTTPException(status_code=403, detail="权限不足")
    result = await db.execute(select(Salary).where(Salary.id == salary_id))
    salary = result.scalar_one_or_none()
    if not salary:
        raise HTTPException(status_code=404, detail="薪酬记录不存在")
    return salary


@router.put("/salary/{salary_id}", response_model=SalaryResponse)
async def update_salary(
    salary_id: int,
    req: SalaryCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """更新薪酬记录"""
    result = await db.execute(select(Salary).where(Salary.id == salary_id))
    salary = result.scalar_one_or_none()
    if not salary:
        raise HTTPException(status_code=404, detail="薪酬记录不存在")
    for key, val in req.model_dump().items():
        setattr(salary, key, val)
    await db.flush()
    await db.refresh(salary)
    return salary


@router.delete("/salary/{salary_id}")
async def delete_salary(
    salary_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """删除薪酬记录"""
    result = await db.execute(select(Salary).where(Salary.id == salary_id))
    salary = result.scalar_one_or_none()
    if not salary:
        raise HTTPException(status_code=404, detail="薪酬记录不存在")
    await db.delete(salary)
    await db.flush()
    return {"detail": "删除成功"}


# ═══════════════════════════════════════════════════════════
#  Excel Export
# ═══════════════════════════════════════════════════════════

def _build_excel(headers, rows):
    wb = Workbook(); ws = wb.active
    ws.append(headers)
    for r in rows: ws.append(r)
    for i, h in enumerate(headers, 1):
        ws.column_dimensions[chr(64 + i) if i <= 26 else "A"].width = max(12, len(h) * 2 + 2)
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    return Response(content=buf.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=labour_export.xlsx"})


@router.get("/export/staff")
async def export_staff(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """导出人员档案 Excel"""
    result = await db.execute(select(Staff).where(Staff.is_active == True).order_by(Staff.id))
    staff_list = result.scalars().all()
    headers = ["姓名","身份证号","电话","工种","日薪","开户行","银行账号","状态"]
    rows = [[s.name,s.id_card or "",s.phone or "",s.work_type or "",
             float(s.daily_wage or 0),s.bank_name or "",s.bank_account or "",
             "在职" if s.is_active else "离职"] for s in staff_list]
    return _build_excel(headers, rows)


@router.get("/export/work-hours")
async def export_work_hours(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """导出工时记录 Excel"""
    result = await db.execute(select(WorkHour).order_by(WorkHour.work_date.desc(), WorkHour.id))
    wh_list = result.scalars().all()
    sids = set(w.staff_id for w in wh_list); pids = set(w.project_id for w in wh_list)
    sm = {}; pm = {}
    if sids:
        for s in (await db.execute(select(Staff).where(Staff.id.in_(sids)))).scalars(): sm[s.id] = s.name
    if pids:
        for p in (await db.execute(select(Project).where(Project.id.in_(pids)))).scalars(): pm[p.id] = p.name
    headers = ["人员","项目","日期","临时职务","出工补助","饭补","高温补贴","天气补贴","日合计","审核状态"]
    rows = [[sm.get(w.staff_id,""),pm.get(w.project_id,""),str(w.work_date),
             w.position_title or "",float(w.attendance_subsidy or 0),float(w.meal_allowance or 0),
             float(w.heat_subsidy or 0),float(w.weather_subsidy or 0),float(w.daily_total or 0),
             "通过" if w.is_approved else "待审"] for w in wh_list]
    return _build_excel(headers, rows)


@router.get("/export/salary")
async def export_salary(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """导出薪酬记录 Excel"""
    result = await db.execute(select(Salary).order_by(Salary.salary_month.desc(), Salary.id))
    salary_list = result.scalars().all()
    sids = set(s.staff_id for s in salary_list); pids = set(s.project_id for s in salary_list)
    sm = {}; pm = {}
    if sids:
        for s in (await db.execute(select(Staff).where(Staff.id.in_(sids)))).scalars(): sm[s.id] = s.name
    if pids:
        for p in (await db.execute(select(Project).where(Project.id.in_(pids)))).scalars(): pm[p.id] = p.name
    headers = ["人员","项目","月份","基础工资","工时工资","五险一金","项目提成","实发金额","状态","发放日期","备注"]
    rows = [[sm.get(s.staff_id,""),pm.get(s.project_id,""),s.salary_month,
             float(s.base_amount or 0),float(s.hourly_wage or 0),float(s.insurance_fund or 0),
             float(s.project_bonus or 0),float(s.net_amount or 0),
             "已发放" if s.is_paid else "未发放",str(s.paid_at)[:10] if s.paid_at else "",s.remark or ""]
            for s in salary_list]
    return _build_excel(headers, rows)
