"""Invoice (发票) routes - 销项发票 & 进项发票."""
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.security import get_current_user, require_invoice
from models import InvoiceOut, InvoiceIn, AuditLog, User
from schemas import InvoiceOutCreate, InvoiceOutResponse, InvoiceInCreate, InvoiceInResponse

router = APIRouter(prefix="/invoices", tags=["发票管理"])


# ─── 销项发票 ────────────────────────────────────────────

@router.post("/out", response_model=InvoiceOutResponse)
async def create_invoice_out(
    req: InvoiceOutCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_invoice),
):
    """创建销项发票"""
    inv = InvoiceOut(tenant_id=user.tenant_id or 1, **req.model_dump())
    if req.tax_rate and req.amount:
        rate = Decimal(str(req.tax_rate))
        inv.amount_including_tax = req.amount
        inv.tax_amount = (req.amount * rate / (Decimal("100") + rate)).quantize(Decimal("0.01"))
        inv.amount_excluding_tax = req.amount - inv.tax_amount
    db.add(inv)
    await db.flush()
    await db.refresh(inv)
    db.add(AuditLog(tenant_id=user.tenant_id or 1, user_id=user.id, username=user.username,
                    action="create_invoice_out", biz_type="invoice_out", biz_id=inv.id))
    return inv


@router.get("/out", response_model=list[InvoiceOutResponse])
async def list_invoice_out(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_invoice),
):
    query = select(InvoiceOut)
    if user.role != "super_admin" and user.tenant_id:
        query = query.where(InvoiceOut.tenant_id == user.tenant_id)
    if project_id := request.query_params.get("project_id"):
        query = query.where(InvoiceOut.project_id == int(project_id))
    result = await db.execute(query.order_by(InvoiceOut.id.desc()))
    return result.scalars().all()


@router.put("/out/{invoice_id}", response_model=InvoiceOutResponse)
async def update_invoice_out(
    invoice_id: int,
    req: InvoiceOutCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_invoice),
):
    """编辑销项发票"""
    result = await db.execute(select(InvoiceOut).where(InvoiceOut.id == invoice_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="发票不存在")
    for key, val in req.model_dump().items():
        setattr(inv, key, val)
    if req.tax_rate and req.amount:
        rate = Decimal(str(req.tax_rate))
        inv.amount_including_tax = req.amount
        inv.tax_amount = (req.amount * rate / (Decimal("100") + rate)).quantize(Decimal("0.01"))
        inv.amount_excluding_tax = req.amount - inv.tax_amount
    await db.flush()
    await db.refresh(inv)
    return inv


@router.delete("/out/{invoice_id}")
async def delete_invoice_out(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_invoice),
):
    """编辑销项发票"""
    result = await db.execute(select(InvoiceOut).where(InvoiceOut.id == invoice_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="发票不存在")
    await db.delete(inv)
    await db.flush()
    return {"detail": "删除成功"}


@router.get("/out/stats")
async def invoice_out_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_invoice),
):
    query = select(
        InvoiceOut.invoice_type,
        func.count(InvoiceOut.id),
        func.coalesce(func.sum(InvoiceOut.amount), 0),
    )
    if user.role != "super_admin" and user.tenant_id:
        query = query.where(InvoiceOut.tenant_id == user.tenant_id)
    query = query.group_by(InvoiceOut.invoice_type)
    result = await db.execute(query)
    stats = []
    for row in result.all():
        stats.append({
            "invoice_type": row[0],
            "count": row[1],
            "total_amount": float(row[2]),
        })
    return stats


# ─── 进项发票 ────────────────────────────────────────────

@router.post("/in", response_model=InvoiceInResponse)
async def create_invoice_in(
    req: InvoiceInCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_invoice),
):
    """编辑销项发票"""
    inv = InvoiceIn(tenant_id=user.tenant_id or 1, **req.model_dump())
    if req.tax_rate and req.amount:
        rate = Decimal(str(req.tax_rate))
        inv.amount_including_tax = req.amount
        inv.tax_amount = (req.amount * rate / (Decimal("100") + rate)).quantize(Decimal("0.01"))
        inv.amount_excluding_tax = req.amount - inv.tax_amount
    db.add(inv)
    await db.flush()
    db.add(AuditLog(tenant_id=user.tenant_id or 1, user_id=user.id, username=user.username,
                    action="create_invoice_in", biz_type="invoice_in", biz_id=inv.id))
    return inv


@router.get("/in", response_model=list[InvoiceInResponse])
async def list_invoice_in(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_invoice),
):
    query = select(InvoiceIn)
    if user.role != "super_admin" and user.tenant_id:
        query = query.where(InvoiceIn.tenant_id == user.tenant_id)
    if project_id := request.query_params.get("project_id"):
        query = query.where(InvoiceIn.project_id == int(project_id))
    result = await db.execute(query.order_by(InvoiceIn.id.desc()))
    return result.scalars().all()


@router.put("/in/{invoice_id}", response_model=InvoiceInResponse)
async def update_invoice_in(
    invoice_id: int,
    req: InvoiceInCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_invoice),
):
    """编辑销项发票"""
    result = await db.execute(select(InvoiceIn).where(InvoiceIn.id == invoice_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="发票不存在")
    for key, val in req.model_dump().items():
        setattr(inv, key, val)
    if req.tax_rate and req.amount:
        rate = Decimal(str(req.tax_rate))
        inv.amount_including_tax = req.amount
        inv.tax_amount = (req.amount * rate / (Decimal("100") + rate)).quantize(Decimal("0.01"))
        inv.amount_excluding_tax = req.amount - inv.tax_amount
    await db.flush()
    await db.refresh(inv)
    return inv


@router.delete("/in/{invoice_id}")
async def delete_invoice_in(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_invoice),
):
    """编辑销项发票"""
    result = await db.execute(select(InvoiceIn).where(InvoiceIn.id == invoice_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="发票不存在")
    await db.delete(inv)
    await db.flush()
    return {"detail": "删除成功"}
