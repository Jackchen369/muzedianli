"""Engineering Pricing (工程计价) CRUD routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.security import get_current_user, require_project, get_current_admin
from models import EngineeringPricing, Project, AuditLog, User
from schemas import EngineeringPricingCreate, EngineeringPricingResponse

router = APIRouter(prefix="/pricing", tags=["工程计价"])


def _is_admin(user: User) -> bool:
    return user.role in ("super_admin", "company_admin")


def _can_create(user: User) -> bool:
    """可录入的角色：管理员 + 考勤员"""
    return user.role in ("super_admin", "company_admin", "attendance")


@router.post("", response_model=EngineeringPricingResponse)
async def create_pricing(
    req: EngineeringPricingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """创建工程计价记录 — 管理员和考勤员可录入"""
    if not _can_create(user):
        raise HTTPException(status_code=403, detail="权限不足")
    item = EngineeringPricing(tenant_id=user.tenant_id or 1, **req.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    db.add(AuditLog(tenant_id=user.tenant_id or 1, user_id=user.id, username=user.username,
                    action="create_pricing", biz_type="pricing", biz_id=item.id))
    return item


@router.get("")
async def list_pricing(
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    page: int = 1,
    page_size: int = 10,
):
    """工程计价列表 — 项目负责人只读，考勤员/管理员可查看"""
    page_size = min(page_size, 100)
    query = select(EngineeringPricing)
    count_q = select(func.count(EngineeringPricing.id))
    if user.role != "super_admin" and user.tenant_id:
        query = query.where(EngineeringPricing.tenant_id == user.tenant_id)
        count_q = count_q.where(EngineeringPricing.tenant_id == user.tenant_id)
    if project_id:
        query = query.where(EngineeringPricing.project_id == project_id)
        count_q = count_q.where(EngineeringPricing.project_id == project_id)
    total = (await db.execute(count_q)).scalar() or 0
    result = await db.execute(
        query.order_by(EngineeringPricing.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return {"items": result.scalars().all(), "total": total, "page": page, "page_size": page_size}


@router.put("/{item_id}", response_model=EngineeringPricingResponse)
async def update_pricing(
    item_id: int,
    req: EngineeringPricingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """编辑工程计价记录 — 管理员可编辑未审核记录，已审核不可编辑"""
    if not _is_admin(user):
        raise HTTPException(status_code=403, detail="权限不足")
    result = await db.execute(select(EngineeringPricing).where(EngineeringPricing.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="记录不存在")
    if item.is_approved:
        raise HTTPException(status_code=403, detail="已审核的记录不可编辑")
    for key, val in req.model_dump().items():
        setattr(item, key, val)
    await db.flush()
    await db.refresh(item)
    return item


@router.delete("/{item_id}")
async def delete_pricing(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """删除工程计价记录 — 管理员可删除未审核记录，已审核不可删除"""
    if not _is_admin(user):
        raise HTTPException(status_code=403, detail="权限不足")
    result = await db.execute(select(EngineeringPricing).where(EngineeringPricing.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="记录不存在")
    if item.is_approved:
        raise HTTPException(status_code=403, detail="已审核的记录不可删除")
    await db.delete(item)
    await db.flush()
    return {"detail": "删除成功"}


@router.put("/{item_id}/approve", response_model=EngineeringPricingResponse)
async def approve_pricing(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """审核工程计价记录 — 管理员可切换审核状态"""
    if not _is_admin(user):
        raise HTTPException(status_code=403, detail="权限不足")
    result = await db.execute(select(EngineeringPricing).where(EngineeringPricing.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="记录不存在")
    item.is_approved = not item.is_approved
    await db.flush()
    await db.refresh(item)
    return item


@router.get("/total")
async def pricing_total(
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """工程计价汇总金额"""
    q = select(func.coalesce(func.sum(EngineeringPricing.amount), 0))
    if user.role != "super_admin" and user.tenant_id:
        q = q.where(EngineeringPricing.tenant_id == user.tenant_id)
    if project_id:
        q = q.where(EngineeringPricing.project_id == project_id)
    total = (await db.execute(q)).scalar()
    return {"total": float(total)}
