"""Partner (往来单位) CRUD."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.security import get_current_admin, get_current_user, require_basic, require_admin
from models import Partner, AuditLog, User
from schemas import PartnerCreate, PartnerResponse

router = APIRouter(prefix="/partners", tags=["往来单位"])


@router.post("", response_model=PartnerResponse)
async def create_partner(
    req: PartnerCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    partner = Partner(**req.model_dump())
    db.add(partner)
    await db.flush()
    db.add(AuditLog(tenant_id=admin.tenant_id, user_id=admin.id, username=admin.username,
                    action="create_partner", biz_type="partner", biz_id=partner.id))
    return partner


@router.get("", response_model=list[PartnerResponse])
async def list_partners(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    result = await db.execute(select(Partner).where(Partner.is_active == True).order_by(Partner.id))
    return result.scalars().all()


@router.get("/{partner_id}", response_model=PartnerResponse)
async def get_partner(
    partner_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    result = await db.execute(select(Partner).where(Partner.id == partner_id))
    partner = result.scalar_one_or_none()
    if not partner:
        raise HTTPException(status_code=404, detail="往来单位不存在")
    return partner


@router.put("/{partner_id}", response_model=PartnerResponse)
async def update_partner(
    partner_id: int,
    req: PartnerCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(Partner).where(Partner.id == partner_id))
    partner = result.scalar_one_or_none()
    if not partner:
        raise HTTPException(status_code=404, detail="往来单位不存在")
    for key, val in req.model_dump().items():
        setattr(partner, key, val)
    await db.flush()
    return partner


@router.delete("/{partner_id}")
async def delete_partner(
    partner_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(Partner).where(Partner.id == partner_id))
    partner = result.scalar_one_or_none()
    if not partner:
        raise HTTPException(status_code=404, detail="往来单位不存在")
    await db.delete(partner)
    await db.flush()
    return {"detail": "删除成功"}
