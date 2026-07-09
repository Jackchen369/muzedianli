"""电子收据 & 财务章管理."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List

from core.database import get_db
from core.security import get_current_admin, get_current_user, require_finance, require_admin, require_basic
from models import ElectronicReceipt, CompanySeal, User, AuditLog


# ─── Helper: 数字金额转中文大写 ────────────────────────

def number_to_words(num) -> str:
    """将数字金额转换为中文大写金额."""
    if not isinstance(num, Decimal):
        num = Decimal(str(num))
    # 规范化到两位小数
    num = num.quantize(Decimal("0.01"))

    digits = "零壹贰叁肆伍陆柒捌玖"
    units = ["", "拾", "佰", "仟"]
    big_units = ["", "万", "亿", "万亿"]

    integer_part = int(num)
    fraction_part = int((num - integer_part) * 100)

    if integer_part == 0 and fraction_part == 0:
        return "零元整"

    # ── 整数部分 ──
    def _read_four(n: int) -> str:
        """读取四位数."""
        result = ""
        for i in range(3, -1, -1):
            factor = 10 ** i
            d = n // factor
            if d:
                result += digits[d] + units[i]
                n %= factor
            else:
                if result and not result.endswith("零"):
                    result += "零"
        return result.rstrip("零")

    if integer_part > 0:
        parts = []
        n = integer_part
        group_index = 0
        while n > 0:
            group = n % 10000
            chunk = _read_four(group)
            if chunk:
                if group_index > 0 and group < 1000:
                    # 前一组有内容，当前组小于1000，补零
                    if parts and parts[-1] != "零":
                        parts.append("零")
                parts.append(chunk + big_units[group_index])
            elif group_index > 0 and parts:
                # 全零组但前面有内容 - 万位全零时补零
                if parts and parts[-1] != "零" and big_units[group_index]:
                    parts.append("零")
            n //= 10000
            group_index += 1
        parts.reverse()
        # 清理相邻零
        cleaned = []
        for p in parts:
            if p == "零" and cleaned and cleaned[-1] == "零":
                continue
            cleaned.append(p)
        integer_words = "".join(cleaned)
    else:
        integer_words = "零"

    # ── 小数部分 ──
    if fraction_part == 0:
        return integer_words + "元整"
    else:
        jiao = fraction_part // 10
        fen = fraction_part % 10
        result = integer_words + "元"
        if jiao > 0:
            result += digits[jiao] + "角"
        else:
            result += "零"
        if fen > 0:
            result += digits[fen] + "分"
        return result


# ─── Pydantic Schemas ────────────────────────────────────

class CompanySealCreate(BaseModel):
    seal_name: str = Field(..., description="印章名称")
    file_path: str = Field(..., description="印章图片路径")

class CompanySealResponse(BaseModel):
    id: int
    seal_name: str
    file_path: str
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ElectronicReceiptCreate(BaseModel):
    payer_name: str = Field(..., description="付款方名称")
    amount: Decimal = Field(..., description="金额")
    reason: str = Field(..., description="收款事由")
    receipt_date: date = Field(..., description="开票日期")
    is_paid: bool = False
    payment_method: Optional[str] = None
    handler: Optional[str] = None
    approver: Optional[str] = None
    seal_id: Optional[int] = Field(None, description="财务章ID")
    remark: Optional[str] = None

class ElectronicReceiptUpdate(BaseModel):
    payer_name: Optional[str] = None
    amount: Optional[Decimal] = None
    amount_words: Optional[str] = None
    reason: Optional[str] = None
    receipt_date: Optional[date] = None
    seal_id: Optional[int] = None
    status: Optional[str] = None
    remark: Optional[str] = None

class ElectronicReceiptResponse(BaseModel):
    id: int
    receipt_no: str
    payer_name: str
    amount: Decimal
    amount_words: Optional[str] = None
    reason: str
    receipt_date: date
    seal_id: Optional[int] = None
    status: str
    remark: Optional[str] = None
    payment_method: Optional[str] = None
    handler: Optional[str] = None
    approver: Optional[str] = None
    tenant_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Router ──────────────────────────────────────────────

router = APIRouter(prefix="/ereceipts", tags=["电子收据"])


# =================== CompanySeal ===================

@router.post("/seals", response_model=CompanySealResponse)
async def create_seal(
    req: CompanySealCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """上传财务章."""
    seal = CompanySeal(
        seal_name=req.seal_name,
        file_path=req.file_path,
        is_active=True,
    )
    db.add(seal)
    await db.flush()
    db.add(AuditLog(
        tenant_id=admin.tenant_id or 1, user_id=admin.id, username=admin.username,
        action="create_seal", biz_type="company_seal", biz_id=seal.id,
    ))
    return seal


@router.get("/seals", response_model=list[CompanySealResponse])
async def list_seals(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_basic),
):
    """获取所有财务章."""
    result = await db.execute(
        select(CompanySeal).where(CompanySeal.is_active == True).order_by(CompanySeal.id)
    )
    return result.scalars().all()


@router.delete("/seals/{seal_id}")
async def delete_seal(
    seal_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """删除财务章."""
    result = await db.execute(select(CompanySeal).where(CompanySeal.id == seal_id))
    seal = result.scalar_one_or_none()
    if not seal:
        raise HTTPException(status_code=404, detail="财务章不存在")
    await db.delete(seal)
    await db.flush()
    db.add(AuditLog(
        tenant_id=admin.tenant_id or 1, user_id=admin.id, username=admin.username,
        action="delete_seal", biz_type="company_seal", biz_id=seal_id,
    ))
    return {"detail": "删除成功"}


# =================== ElectronicReceipt ===================

async def _next_receipt_no(db: AsyncSession, receipt_date: date) -> str:
    """自动生成收据编号: ERP-YYYYMMDD-NNN."""
    date_str = receipt_date.strftime("%Y%m%d")
    prefix = f"ERP-{date_str}-"

    # 查询当天最大序号
    result = await db.execute(
        select(func.max(ElectronicReceipt.receipt_no))
        .where(ElectronicReceipt.receipt_no.like(f"{prefix}%"))
    )
    max_no = result.scalar()
    if max_no:
        seq = int(max_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


@router.post("/receipts", response_model=ElectronicReceiptResponse)
async def create_receipt(
    req: ElectronicReceiptCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """创建电子收据（自动生成编号和大写金额）."""
    if user.role not in ("super_admin", "company_admin", "project_manager", "finance"):
        raise HTTPException(status_code=403, detail="权限不足")
    # 自动生成收据编号
    receipt_no = await _next_receipt_no(db, req.receipt_date)
    # 自动转换大写金额
    amount_words = number_to_words(req.amount)

    receipt = ElectronicReceipt(
        receipt_no=receipt_no,
        payer_name=req.payer_name,
        amount=req.amount,
        amount_words=amount_words,
        reason=req.reason,
        receipt_date=req.receipt_date,
        seal_id=req.seal_id,
        status="已开具",
        payment_method=req.payment_method,
        handler=req.handler,
        approver=req.approver,
        remark=req.remark,
        tenant_id=user.tenant_id or 1,
    )
    db.add(receipt)
    await db.flush()
    db.add(AuditLog(
        tenant_id=user.tenant_id or 1, user_id=user.id, username=user.username,
        action="create_receipt", biz_type="electronic_receipt", biz_id=receipt.id,
    ))
    return receipt


@router.get("/receipts", response_model=list[ElectronicReceiptResponse])
async def list_receipts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_basic),
):
    """获取所有电子收据."""
    result = await db.execute(
        select(ElectronicReceipt).order_by(ElectronicReceipt.id.desc())
    )
    return result.scalars().all()


@router.get("/receipts/{receipt_id}", response_model=ElectronicReceiptResponse)
async def get_receipt(
    receipt_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_basic),
):
    """获取单个电子收据."""
    result = await db.execute(
        select(ElectronicReceipt).where(ElectronicReceipt.id == receipt_id)
    )
    receipt = result.scalar_one_or_none()
    if not receipt:
        raise HTTPException(status_code=404, detail="电子收据不存在")
    return receipt


@router.put("/receipts/{receipt_id}", response_model=ElectronicReceiptResponse)
async def update_receipt(
    receipt_id: int,
    req: ElectronicReceiptUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """更新电子收据."""
    if user.role not in ("super_admin", "company_admin", "project_manager", "finance"):
        raise HTTPException(status_code=403, detail="权限不足")
    result = await db.execute(
        select(ElectronicReceipt).where(ElectronicReceipt.id == receipt_id)
    )
    receipt = result.scalar_one_or_none()
    if not receipt:
        raise HTTPException(status_code=404, detail="电子收据不存在")

    update_data = req.model_dump(exclude_unset=True)
    # 如果金额变更，重新生成大写金额
    if "amount" in update_data and update_data["amount"] is not None:
        update_data["amount_words"] = number_to_words(update_data["amount"])
    for key, val in update_data.items():
        setattr(receipt, key, val)
    await db.flush()
    return receipt


@router.delete("/receipts/{receipt_id}")
async def delete_receipt(
    receipt_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """删除/作废电子收据（软删除：标记为已作废）."""
    if user.role not in ("super_admin", "company_admin", "project_manager", "finance"):
        raise HTTPException(status_code=403, detail="权限不足")
    result = await db.execute(
        select(ElectronicReceipt).where(ElectronicReceipt.id == receipt_id)
    )
    receipt = result.scalar_one_or_none()
    if not receipt:
        raise HTTPException(status_code=404, detail="电子收据不存在")

    receipt.status = "已作废"
    await db.flush()
    db.add(AuditLog(
        tenant_id=user.tenant_id or 1, user_id=user.id, username=user.username,
        action="void_receipt", biz_type="electronic_receipt", biz_id=receipt_id,
    ))
    return {"detail": "已作废"}
