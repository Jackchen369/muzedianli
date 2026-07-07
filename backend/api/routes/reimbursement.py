"""报销管理 CRUD — 报销申请/审核。"""
import os
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_admin, get_current_user
from models import Reimbursement, Project, User

router = APIRouter(prefix="/reimbursement", tags=["报销管理"])

RECEIPT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "receipts")
os.makedirs(RECEIPT_DIR, exist_ok=True)


# ─── Schemas ──────────────────────────────────────────

class ReimbursementCreate(BaseModel):
    expense_type: str = "其他"
    amount: Decimal
    description: Optional[str] = None
    receipt_urls: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None


class ReimbursementResponse(ReimbursementCreate):
    id: int
    user_id: int
    applicant: str
    status: str
    reviewer_id: Optional[int] = None
    review_remark: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReviewRequest(BaseModel):
    action: str  # approve / reject
    remark: Optional[str] = None


# ─── Helpers ──────────────────────────────────────────

def is_admin(user: User) -> bool:
    return user.role in ("super_admin", "company_admin")


# ─── CRUD ─────────────────────────────────────────────

@router.post("", response_model=ReimbursementResponse)
async def create_reimbursement(
    req: ReimbursementCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """员工提交报销申请 — applicant 自动取当前用户姓名"""
    item = Reimbursement(
        tenant_id=user.tenant_id or 1,
        user_id=user.id,
        applicant=user.display_name or user.username,
        **req.model_dump(),
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.get("", response_model=list[ReimbursementResponse])
async def list_reimbursements(
    status: Optional[str] = None,
    applicant: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """报销列表 — 普通员工只看自己的，管理员看全部"""
    query = select(Reimbursement).order_by(Reimbursement.id.desc())
    if not is_admin(user):
        query = query.where(Reimbursement.user_id == user.id)
    if status:
        query = query.where(Reimbursement.status == status)
    if applicant:
        query = query.where(Reimbursement.applicant.ilike(f"%{applicant}%"))
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{reimb_id}", response_model=ReimbursementResponse)
async def get_reimbursement(
    reimb_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """报销详情"""
    result = await db.execute(select(Reimbursement).where(Reimbursement.id == reimb_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="报销记录不存在")
    if not is_admin(user) and item.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权查看此报销")
    return item


@router.put("/{reimb_id}", response_model=ReimbursementResponse)
async def update_reimbursement(
    reimb_id: int,
    req: ReimbursementCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """编辑报销（仅自己的待审核报销可编辑）"""
    result = await db.execute(select(Reimbursement).where(Reimbursement.id == reimb_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="报销记录不存在")
    if not is_admin(user) and item.user_id != user.id:
        raise HTTPException(status_code=403, detail="无权编辑此报销")
    if item.status != "待审核":
        raise HTTPException(status_code=400, detail="仅待审核状态的报销可编辑")
    for key, val in req.model_dump().items():
        setattr(item, key, val)
    await db.flush()
    await db.refresh(item)
    return item


@router.delete("/{reimb_id}")
async def delete_reimbursement(
    reimb_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """管理员删除报销记录"""
    result = await db.execute(select(Reimbursement).where(Reimbursement.id == reimb_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="报销记录不存在")
    await db.delete(item)
    await db.flush()
    return {"detail": "删除成功"}


# ─── 审核/付款（仅管理员）─────────────────────────────

@router.put("/{reimb_id}/review", response_model=ReimbursementResponse)
async def review_reimbursement(
    reimb_id: int,
    req: ReviewRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """管理员审核报销 — 通过或驳回"""
    result = await db.execute(select(Reimbursement).where(Reimbursement.id == reimb_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="报销记录不存在")
    if item.status != "待审核":
        raise HTTPException(status_code=400, detail="该报销已被审核")
    item.status = "已通过" if req.action == "approve" else "已驳回"
    item.reviewer_id = admin.id
    item.review_remark = req.remark
    item.reviewed_at = datetime.now()
    await db.flush()
    await db.refresh(item)
    return item


@router.put("/{reimb_id}/pay", response_model=ReimbursementResponse)
async def pay_reimbursement(
    reimb_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """管理员标记报销为已付款"""
    result = await db.execute(select(Reimbursement).where(Reimbursement.id == reimb_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="报销记录不存在")
    if item.status != "已通过":
        raise HTTPException(status_code=400, detail="仅已通过的报销可付款")
    item.status = "已付款"
    item.paid_at = datetime.now()
    await db.flush()
    await db.refresh(item)
    return item


@router.post("/upload")
async def upload_receipt(
    file: UploadFile = File(...),
):
    """上传报销凭证，返回文件 URL"""
    ext = os.path.splitext(file.filename or "file")[1]
    stored = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(RECEIPT_DIR, stored)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    return {"url": f"/uploads/receipts/{stored}", "filename": file.filename}
