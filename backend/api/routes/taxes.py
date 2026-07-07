"""Tax record routes - 税金缴纳管理."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.security import get_current_admin, get_current_user, require_finance, require_admin
from models import TaxRecord, AuditLog, User
from pydantic import BaseModel
from datetime import date

router = APIRouter(prefix="/taxes", tags=["税金管理"])


class TaxCreate(BaseModel):
    project_id: Optional[int] = None
    unit_name: Optional[str] = None
    tax_type: str = "增值税"
    amount: Decimal
    tax_period: str
    period_type: str = "月度"
    due_date: Optional[date] = None
    paid_date: Optional[date] = None
    is_paid: bool = False
    file_path: Optional[str] = None
    remark: Optional[str] = None


class TaxResponse(TaxCreate):
    id: int
    tenant_id: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


@router.post("", response_model=TaxResponse)
async def create_tax(
    req: TaxCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    t = TaxRecord(tenant_id=admin.tenant_id or 1, **req.model_dump())
    db.add(t)
    await db.flush()
    await db.refresh(t)
    db.add(AuditLog(tenant_id=admin.tenant_id or 1, user_id=admin.id, username=admin.username,
                    action="create_tax", biz_type="tax", biz_id=t.id))
    return t


@router.get("", response_model=list[TaxResponse])
async def list_taxes(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_finance),
):
    query = select(TaxRecord)
    if user.role != "super_admin" and user.tenant_id:
        query = query.where(TaxRecord.tenant_id == user.tenant_id)
    result = await db.execute(query.order_by(TaxRecord.id.desc()))
    return result.scalars().all()


@router.get("/summary")
async def tax_summary(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_finance),
):
    """税金汇总：按税种统计、已缴/未缴"""
    q = select(TaxRecord)
    if user.role != "super_admin" and user.tenant_id:
        q = q.where(TaxRecord.tenant_id == user.tenant_id)

    r1 = await db.execute(
        select(TaxRecord.tax_type, func.count(TaxRecord.id), func.sum(TaxRecord.amount))
        .select_from(q.subquery()).group_by(TaxRecord.tax_type)
    )
    by_type = [{"tax_type": r[0], "count": r[1], "total": float(r[2] or 0)} for r in r1.all()]

    r2 = await db.execute(
        select(func.coalesce(func.sum(TaxRecord.amount), 0)).where(TaxRecord.is_paid == True)
        .select_from(q.subquery())
    )
    total_paid = float(r2.scalar() or 0)

    r3 = await db.execute(
        select(func.coalesce(func.sum(TaxRecord.amount), 0)).where(TaxRecord.is_paid == False)
        .select_from(q.subquery())
    )
    total_unpaid = float(r3.scalar() or 0)

    r4 = await db.execute(select(func.coalesce(func.sum(TaxRecord.amount), 0)).select_from(q.subquery()))
    total_all = float(r4.scalar() or 0)

    return {"by_type": by_type, "total_all": total_all, "total_paid": total_paid, "total_unpaid": total_unpaid}


@router.put("/{tax_id}", response_model=TaxResponse)
async def update_tax(
    tax_id: int,
    req: TaxCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(TaxRecord).where(TaxRecord.id == tax_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="税金记录不存在")
    for key, val in req.model_dump().items():
        setattr(t, key, val)
    await db.flush()
    await db.refresh(t)
    return t


@router.delete("/{tax_id}")
async def delete_tax(
    tax_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(TaxRecord).where(TaxRecord.id == tax_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="税金记录不存在")
    await db.delete(t)
    await db.flush()
    return {"detail": "删除成功"}
