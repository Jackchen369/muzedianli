"""API dependency injection."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.security import get_current_user, get_current_admin, get_current_super_admin
from models import User


def get_tenant_db(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Inject tenant context into the request."""
    if current_user.role == "super_admin":
        return db  # super admin sees all
    if current_user.tenant_id is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="用户未关联租户")
    return db
