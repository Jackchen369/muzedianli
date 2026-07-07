"""Auth routes - login, user management."""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.security import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, get_current_admin, get_current_super_admin,
)
from core.config import settings
from models import User, Tenant, AuditLog
from schemas import LoginRequest, TokenResponse, UserCreate, UserResponse, UserUpdate, PasswordReset

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="账户已禁用")

    token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        tenant_id=user.tenant_id,
    )


@router.post("/users", response_model=UserResponse)
async def create_user(
    req: UserCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """创建用户（管理员）"""
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=req.username,
        password_hash=get_password_hash(req.password),
        display_name=req.display_name,
        phone=req.phone,
        role=req.role,
        tenant_id=req.tenant_id if admin.role == "super_admin" else admin.tenant_id,
    )
    db.add(user)
    await db.flush()

    # Audit log
    db.add(AuditLog(
        tenant_id=admin.tenant_id, user_id=admin.id, username=admin.username,
        action="create_user", biz_type="user", biz_id=user.id,
    ))

    # Auto-create staff record in labour module
    from models import Staff
    existing_staff = await db.execute(
        select(Staff).where(Staff.name == user.display_name, Staff.tenant_id == (user.tenant_id or 1))
    )
    existing = existing_staff.scalar_one_or_none()

    # 同名档案优先，其次看是否有已绑定的user_id的档案
    if not existing:
        existing = (await db.execute(
            select(Staff).where(Staff.user_id == user.id, Staff.tenant_id == (user.tenant_id or 1))
        )).scalar_one_or_none()

    if existing:
        # 已有档案 → 更新名称和user_id
        if not existing.user_id:
            existing.user_id = user.id
    else:
        staff = Staff(
            tenant_id=user.tenant_id or 1,
            name=user.display_name or user.username,
            phone=user.phone,
            work_type="员工",
            is_active=True,
            user_id=user.id,
        )
        db.add(staff)

    return user


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """用户列表"""
    query = select(User)
    if admin.role != "super_admin":
        query = query.where(User.tenant_id == admin.tenant_id)
    result = await db.execute(query.order_by(User.id))
    return result.scalars().all()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """当前用户信息"""
    return current_user


# ═══════════════════════════════════════════════════════════
#  用户管理扩展接口
# ═══════════════════════════════════════════════════════════

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    req: UserUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """编辑用户信息（姓名/手机号/角色）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    for key, val in req.model_dump(exclude_none=True).items():
        setattr(user, key, val)
    await db.flush()
    await db.refresh(user)
    return user


@router.put("/users/{user_id}/password")
async def reset_password(
    user_id: int,
    req: PasswordReset,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """重置用户密码"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.password_hash = get_password_hash(req.new_password)
    await db.flush()
    return {"detail": "密码已重置"}


@router.put("/users/{user_id}/toggle-active", response_model=UserResponse)
async def toggle_user_active(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """启用/禁用用户"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="不能禁用自己")
    user.is_active = not user.is_active
    await db.flush()
    await db.refresh(user)
    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """删除用户"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    await db.delete(user)
    await db.flush()
    return {"detail": "删除成功"}
