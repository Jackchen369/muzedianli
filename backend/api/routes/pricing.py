"""Engineering Pricing (工程计价) CRUD routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.security import get_current_user, require_project
from models import EngineeringPricing, Project, AuditLog, User
from schemas import EngineeringPricingCreate, EngineeringPricingResponse

router = APIRouter(prefix="/pricing", tags=["工程计价"])


@router.post("", response_model=EngineeringPricingResponse)
async def create_pricing(
    req: EngineeringPricingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_project),
):
    """创建工程计价记录"""
    item = EngineeringPricing(tenant_id=user.tenant_id or 1, **req.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    db.add(AuditLog(tenant_id=user.tenant_id or 1, user_id=user.id, username=user.username,
                    action="create_pricing", biz_type="pricing", biz_id=item.id))
    return item


@router.get("", response_model=list[EngineeringPricingResponse])
async def list_pricing(
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_project),
):
    """工程计价列表，可按项目筛选"""
    query = select(EngineeringPricing)
    if user.role != "super_admin" and user.tenant_id:
        query = query.where(EngineeringPricing.tenant_id == user.tenant_id)
    if project_id:
        query = query.where(EngineeringPricing.project_id == project_id)
    result = await db.execute(query.order_by(EngineeringPricing.id.desc()))
    return result.scalars().all()


@router.put("/{item_id}", response_model=EngineeringPricingResponse)
async def update_pricing(
    item_id: int,
    req: EngineeringPricingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_project),
):
    """编辑工程计价记录"""
    result = await db.execute(select(EngineeringPricing).where(EngineeringPricing.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="记录不存在")
    for key, val in req.model_dump().items():
        setattr(item, key, val)
    await db.flush()
    await db.refresh(item)
    return item


@router.delete("/{item_id}")
async def delete_pricing(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_project),
):
    """删除工程计价记录"""
    result = await db.execute(select(EngineeringPricing).where(EngineeringPricing.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="记录不存在")
    await db.delete(item)
    await db.flush()
    return {"detail": "删除成功"}


@router.get("/total")
async def pricing_total(
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_project),
):
    """工程计价汇总金额"""
    q = select(func.coalesce(func.sum(EngineeringPricing.amount), 0))
    if user.role != "super_admin" and user.tenant_id:
        q = q.where(EngineeringPricing.tenant_id == user.tenant_id)
    if project_id:
        q = q.where(EngineeringPricing.project_id == project_id)
    total = (await db.execute(q)).scalar()
    return {"total": float(total)}
