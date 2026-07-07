"""Project (项目) CRUD."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.security import get_current_admin, get_current_user, require_project
from models import Project, Partner, AuditLog, User
from schemas import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/projects", tags=["项目管理"])


@router.post("", response_model=ProjectResponse)
async def create_project(
    req: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    project = Project(**req.model_dump())
    tid = admin.tenant_id or 1
    project.tenant_id = tid
    db.add(project)
    await db.flush()
    db.add(AuditLog(tenant_id=tid, user_id=admin.id, username=admin.username,
                    action="create_project", biz_type="project", biz_id=project.id))
    # Reload with owner name
    result = await db.execute(
        select(Project).where(Project.id == project.id)
    )
    return result.scalar_one()


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_project),
):
    query = select(Project)
    if user.role != "super_admin" and user.tenant_id:
        query = query.where(Project.tenant_id == user.tenant_id)
    result = await db.execute(query.order_by(Project.id.desc()))
    projects = result.scalars().all()

    # Resolve owner names
    responses = []
    for p in projects:
        owner_name = ""
        if p.owner_id:
            r = await db.execute(select(Partner.name).where(Partner.id == p.owner_id))
            if name := r.scalar_one_or_none():
                owner_name = name
        resp = ProjectResponse.model_validate(p)
        resp.owner_name = owner_name
        responses.append(resp)
    return responses


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_project),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    req: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    for key, val in req.model_dump().items():
        setattr(project, key, val)
    await db.flush()
    await db.refresh(project)
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    await db.delete(project)
    await db.flush()
    db.add(AuditLog(tenant_id=admin.tenant_id or 1, user_id=admin.id, username=admin.username,
                    action="delete_project", biz_type="project", biz_id=project_id))
    return {"detail": "删除成功"}


@router.get("/{project_id}/profit")
async def get_project_profit(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_project),
):
    """单项目利润核算"""
    from sqlalchemy import func
    from models import InvoiceOut, InvoiceIn, CostRecord

    # 总收入（销项发票）
    r1 = await db.execute(
        select(func.coalesce(func.sum(InvoiceOut.amount), 0))
        .where(InvoiceOut.project_id == project_id)
    )
    total_income = r1.scalar()

    # 总成本（进项发票 + 人工 + 杂费）
    r2 = await db.execute(
        select(func.coalesce(func.sum(InvoiceIn.amount), 0))
        .where(InvoiceIn.project_id == project_id)
    )
    total_invoice_cost = r2.scalar()

    r3 = await db.execute(
        select(func.coalesce(func.sum(CostRecord.amount), 0))
        .where(CostRecord.project_id == project_id)
    )
    total_other_cost = r3.scalar()

    profit = total_income - total_invoice_cost - total_other_cost

    return {
        "project_id": project_id,
        "total_income": float(total_income),
        "total_invoice_cost": float(total_invoice_cost),
        "total_other_cost": float(total_other_cost),
        "profit": float(profit),
    }
