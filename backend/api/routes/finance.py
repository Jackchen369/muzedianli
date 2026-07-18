"""Finance routes - 回款, 付款, 应收应付."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.security import get_current_admin, get_current_user, require_finance, require_admin
from models import Receipt, Payment, InvoiceOut, InvoiceIn, AuditLog, User
from schemas import ReceiptCreate, ReceiptResponse, PaymentCreate, PaymentResponse

router = APIRouter(prefix="/finance", tags=["财务管理"])


# ─── 回款登记 ────────────────────────────────────────────

@router.post("/receipts", response_model=ReceiptResponse)
async def create_receipt(
    req: ReceiptCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    r = Receipt(tenant_id=admin.tenant_id or 1, **req.model_dump())
    db.add(r)
    await db.flush()
    db.add(AuditLog(tenant_id=admin.tenant_id or 1, user_id=admin.id, username=admin.username,
                    action="create_receipt", biz_type="receipt", biz_id=r.id))
    return r


# ─── 回款 PUT/DELETE ─────────────────────────────────────

@router.put("/receipts/{receipt_id}", response_model=ReceiptResponse)
async def update_receipt(
    receipt_id: int,
    req: ReceiptCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(Receipt).where(Receipt.id == receipt_id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="回款记录不存在")
    for key, val in req.model_dump().items():
        setattr(r, key, val)
    await db.flush()
    await db.refresh(r)
    return r


@router.delete("/receipts/{receipt_id}")
async def delete_receipt(
    receipt_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(Receipt).where(Receipt.id == receipt_id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="回款记录不存在")
    await db.delete(r)
    await db.flush()
    return {"detail": "删除成功"}


@router.get("/receipts", response_model=list[ReceiptResponse])
async def list_receipts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_finance),
):
    query = select(Receipt)
    if user.role != "super_admin" and user.tenant_id:
        query = query.where(Receipt.tenant_id == user.tenant_id)
    result = await db.execute(query.order_by(Receipt.id.desc()))
    return result.scalars().all()


# ─── 付款登记 ────────────────────────────────────────────

@router.post("/payments", response_model=PaymentResponse)
async def create_payment(
    req: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    p = Payment(tenant_id=admin.tenant_id or 1, **req.model_dump())
    db.add(p)
    await db.flush()
    db.add(AuditLog(tenant_id=admin.tenant_id or 1, user_id=admin.id, username=admin.username,
                    action="create_payment", biz_type="payment", biz_id=p.id))
    return p


# ─── 付款 PUT/DELETE ─────────────────────────────────────

@router.put("/payments/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: int,
    req: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="付款记录不存在")
    for key, val in req.model_dump().items():
        setattr(p, key, val)
    await db.flush()
    await db.refresh(p)
    return p


@router.delete("/payments/{payment_id}")
async def delete_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="付款记录不存在")
    await db.delete(p)
    await db.flush()
    return {"detail": "删除成功"}


@router.get("/payments", response_model=list[PaymentResponse])
async def list_payments(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_finance),
):
    query = select(Payment)
    if user.role != "super_admin" and user.tenant_id:
        query = query.where(Payment.tenant_id == user.tenant_id)
    result = await db.execute(query.order_by(Payment.id.desc()))
    return result.scalars().all()


# ─── 应收应付统计 ────────────────────────────────────────

@router.get("/summary")
async def finance_summary(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_finance),
):
    """财务汇总：应收、应付、总收入、总支出"""
    query_base = select(InvoiceOut)
    if user.role != "super_admin" and user.tenant_id:
        query_base = query_base.where(InvoiceOut.tenant_id == user.tenant_id)

    # 销项总额（应收）
    r1 = await db.execute(
        select(func.coalesce(func.sum(InvoiceOut.amount), 0)).select_from(query_base.subquery())
    )
    # 销项总额仅统计丙公司（丙→乙/丙→甲）
    q = select(func.coalesce(func.sum(InvoiceOut.amount), 0)).where(
        InvoiceOut.invoice_type.in_(["丙→乙", "丙→甲"])
    )
    if user.role != "super_admin" and user.tenant_id:
        q = q.where(InvoiceOut.tenant_id == user.tenant_id)
    total_invoice = (await db.execute(q)).scalar()

    q2 = select(func.coalesce(func.sum(Receipt.amount), 0))
    if user.role != "super_admin" and user.tenant_id:
        q2 = q2.where(Receipt.tenant_id == user.tenant_id)
    total_receipt = (await db.execute(q2)).scalar()

    q3 = select(func.coalesce(func.sum(InvoiceIn.amount), 0))
    if user.role != "super_admin" and user.tenant_id:
        q3 = q3.where(InvoiceIn.tenant_id == user.tenant_id)
    total_invoice_in = (await db.execute(q3)).scalar()

    q4 = select(func.coalesce(func.sum(Payment.amount), 0))
    if user.role != "super_admin" and user.tenant_id:
        q4 = q4.where(Payment.tenant_id == user.tenant_id)
    total_payment = (await db.execute(q4)).scalar()

    return {
        "total_invoice_out": float(total_invoice),
        "total_receipt": float(total_receipt),
        "receivable_balance": float(total_invoice - total_receipt),
        "total_invoice_in": float(total_invoice_in),
        "total_payment": float(total_payment),
        "payable_balance": float(total_invoice_in - total_payment),
    }
