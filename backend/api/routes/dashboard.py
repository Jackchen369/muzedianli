"""Dashboard routes."""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.security import get_current_admin, get_current_user, require_finance, require_admin, require_basic
from models import Project, InvoiceOut, InvoiceIn, Staff, User
from schemas import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["数据大屏"])


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_finance),
):
    """总览数据"""
    q_proj = select(func.count(Project.id))
    q_income = select(func.coalesce(func.sum(InvoiceOut.amount), 0)).where(
        InvoiceOut.invoice_type.in_(["丙→乙", "丙→甲"])
    )
    q_cost = select(func.coalesce(func.sum(InvoiceIn.amount), 0))
    q_staff = select(func.count(Staff.id))
    q_payable = select(func.coalesce(func.sum(InvoiceIn.amount), 0))

    if user.role != "super_admin" and user.tenant_id:
        q_proj = q_proj.where(Project.tenant_id == user.tenant_id)
        q_income = q_income.where(InvoiceOut.tenant_id == user.tenant_id)
        q_cost = q_cost.where(InvoiceIn.tenant_id == user.tenant_id)
        q_staff = q_staff.where(Staff.tenant_id == user.tenant_id)
        q_payable = q_payable.where(InvoiceIn.tenant_id == user.tenant_id)

    project_count = (await db.execute(q_proj)).scalar() or 0
    total_revenue = (await db.execute(q_income)).scalar() or 0
    total_cost = (await db.execute(q_cost)).scalar() or 0
    staff_count = (await db.execute(q_staff)).scalar() or 0
    total_payable = (await db.execute(q_payable)).scalar() or 0

    return DashboardSummary(
        total_revenue=total_revenue,
        total_receivable=total_revenue - total_cost,
        total_payable=total_payable,
        total_invoice_out=total_revenue,
        project_count=project_count,
        staff_count=staff_count,
    )
