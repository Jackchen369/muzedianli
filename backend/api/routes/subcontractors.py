"""Subcontractor (分包单位) management routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.security import get_current_user, require_project
from models import ProjectSubcontractor, Partner, AuditLog, User
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

router = APIRouter(prefix="/subcontractors", tags=["分包管理"])


class SubcontractorCreate(BaseModel):
    project_id: int
    partner_id: int
    contract_amount: Optional[Decimal] = None
    remark: Optional[str] = None


class SubcontractorResponse(SubcontractorCreate):
    id: int
    partner_name: Optional[str] = None

    model_config = {"from_attributes": True}


@router.post("", response_model=SubcontractorResponse)
async def add_subcontractor(
    req: SubcontractorCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_project),
):
    """为项目添加分包单位"""
    sc = ProjectSubcontractor(**req.model_dump())
    db.add(sc)
    await db.flush()
    await db.refresh(sc)
    db.add(AuditLog(tenant_id=user.tenant_id or 1, user_id=user.id, username=user.username,
                    action="add_subcontractor", biz_type="subcontractor", biz_id=sc.id))
    # Resolve partner name
    r = await db.execute(select(Partner.name).where(Partner.id == req.partner_id))
    name = r.scalar_one_or_none()
    resp = SubcontractorResponse.model_validate(sc)
    resp.partner_name = name
    return resp


@router.get("/{project_id}", response_model=list[SubcontractorResponse])
async def list_subcontractors(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取项目的分包单位列表"""
    result = await db.execute(
        select(ProjectSubcontractor).where(ProjectSubcontractor.project_id == project_id)
    )
    scs = result.scalars().all()
    responses = []
    for sc in scs:
        r = await db.execute(select(Partner.name).where(Partner.id == sc.partner_id))
        name = r.scalar_one_or_none()
        resp = SubcontractorResponse.model_validate(sc)
        resp.partner_name = name
        responses.append(resp)
    return responses


@router.delete("/{sc_id}")
async def remove_subcontractor(
    sc_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_project),
):
    """移除分包单位"""
    result = await db.execute(select(ProjectSubcontractor).where(ProjectSubcontractor.id == sc_id))
    sc = result.scalar_one_or_none()
    if not sc:
        raise HTTPException(status_code=404, detail="分包关联不存在")
    await db.delete(sc)
    await db.flush()
    return {"detail": "移除成功"}
