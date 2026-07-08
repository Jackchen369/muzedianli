"""JWT authentication and password hashing."""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import settings
from core.database import get_db
from models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    # sub must be a string for python-jose
    if "sub" in to_encode and not isinstance(to_encode["sub"], str):
        to_encode["sub"] = str(to_encode["sub"])
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require super admin or company admin role."""
    if current_user.role not in ("super_admin", "company_admin"):
        raise HTTPException(status_code=403, detail="权限不足")
    return current_user


async def get_current_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="需要超级管理员权限")
    return current_user


# ═══════════════════════════════════════════════════════════
#  Role-based permission dependencies
# ═══════════════════════════════════════════════════════════

def require_role(*roles: str):
    """权限依赖工厂 — 检查当前用户是否拥有指定角色之一。

    用法:  admin: User = Depends(require_role('super_admin', 'company_admin'))
    """
    async def _role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"权限不足，需要 {'/'.join(roles)} 角色",
            )
        return current_user
    return _role_checker


# 预定义常用权限组合
require_admin = require_role('super_admin', 'company_admin')
require_partner = require_role('super_admin', 'company_admin', 'project_manager')
require_finance = require_role('super_admin', 'company_admin', 'finance')
require_project = require_role('super_admin', 'company_admin', 'project_manager')
require_basic = require_role('super_admin', 'company_admin', 'project_manager', 'finance', 'worker', 'attendance')
require_invoice = require_role('super_admin', 'company_admin', 'finance', 'project_manager')
