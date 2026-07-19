"""电子档案管理 — 文件/目录上传、浏览、下载、搜索。"""
import os
import uuid
import shutil
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.security import get_current_admin, get_current_user
from models import ElectronicArchive, User

router = APIRouter(prefix="/archive", tags=["电子档案"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "archive")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _is_admin(user: User) -> bool:
    return user.role in ("super_admin", "company_admin")


# ═══════════════════════════════════════════════════════════
#  Directory
# ═══════════════════════════════════════════════════════════

@router.post("/directory")
async def create_directory(
    name: str = Form(...),
    directory: str = Form("/"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """创建目录 — 所有角色"""
    existing = await db.execute(
        select(ElectronicArchive).where(
            ElectronicArchive.directory == directory,
            ElectronicArchive.name == name,
            ElectronicArchive.is_directory == True,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="目录已存在")

    entry = ElectronicArchive(
        tenant_id=user.tenant_id or 1,
        name=name,
        directory=directory,
        is_directory=True,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


# ═══════════════════════════════════════════════════════════
#  Upload
# ═══════════════════════════════════════════════════════════

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    directory: str = Form("/"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """上传文件 — 所有角色"""
    ext = os.path.splitext(file.filename or "file")[1]
    stored_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, stored_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    entry = ElectronicArchive(
        tenant_id=user.tenant_id or 1,
        name=file.filename or stored_name,
        directory=directory,
        is_directory=False,
        file_type=file.content_type,
        file_size=len(content),
        file_path=stored_name,
        original_filename=file.filename,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


# ═══════════════════════════════════════════════════════════
#  List & Search
# ═══════════════════════════════════════════════════════════

@router.get("")
async def list_archive(
    directory: str = "/",
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """列出目录下文件/子目录"""
    query = select(ElectronicArchive).where(
        ElectronicArchive.directory == directory
    )

    if search:
        query = query.where(ElectronicArchive.name.ilike(f"%{search}%"))

    if search:
        query = select(ElectronicArchive).where(
            ElectronicArchive.name.ilike(f"%{search}%")
        )

    query = query.order_by(ElectronicArchive.is_directory.desc(), ElectronicArchive.name)
    result = await db.execute(query)
    entries = result.scalars().all()

    data = []
    for e in entries:
        d = {
            "id": e.id,
            "name": e.name,
            "directory": e.directory,
            "is_directory": e.is_directory,
            "file_type": e.file_type,
            "file_size": e.file_size,
            "file_size_display": format_size(e.file_size) if e.file_size else "",
            "is_approved": e.is_approved,
            "created_at": str(e.created_at)[:19] if e.created_at else "",
        }
        data.append(d)
    return data


@router.get("/all-directories")
async def list_all_directories(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取所有目录列表"""
    result = await db.execute(
        select(ElectronicArchive).where(
            ElectronicArchive.is_directory == True
        ).order_by(ElectronicArchive.directory, ElectronicArchive.name)
    )
    dirs = result.scalars().all()
    paths = set()
    for d in dirs:
        paths.add(f"{d.directory}{d.name}/")
    return sorted(list(paths))


# ═══════════════════════════════════════════════════════════
#  Download & Preview
# ═══════════════════════════════════════════════════════════

@router.get("/download/{entry_id}")
async def download_file(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """下载文件 — 所有角色"""
    result = await db.execute(select(ElectronicArchive).where(ElectronicArchive.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="文件不存在")
    if entry.is_directory:
        raise HTTPException(status_code=400, detail="目录不可下载")

    file_path = os.path.join(UPLOAD_DIR, entry.file_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件存储已丢失")

    from fastapi.responses import FileResponse
    return FileResponse(
        path=file_path,
        filename=entry.original_filename or entry.name,
        media_type=entry.file_type or "application/octet-stream",
    )


@router.get("/preview/{entry_id}")
async def preview_file(
    entry_id: int,
    token: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """预览文件 — 所有角色"""
    access_token = None
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            access_token = parts[1]
    if not access_token:
        access_token = token
    if not access_token:
        raise HTTPException(status_code=401, detail="未提供认证凭据")

    try:
        from jose import jwt
        from core.config import settings
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub") or 0)
    except Exception:
        raise HTTPException(status_code=401, detail="无效的认证凭据")

    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")

    result = await db.execute(select(ElectronicArchive).where(ElectronicArchive.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="文件不存在")
    if entry.is_directory:
        raise HTTPException(status_code=400, detail="目录不可预览")

    file_path = os.path.join(UPLOAD_DIR, entry.file_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件存储已丢失")

    from fastapi.responses import FileResponse
    from urllib.parse import quote
    filename = entry.original_filename or entry.name
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=entry.file_type or "application/octet-stream",
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{quote(filename)}",
            "Cache-Control": "public, max-age=3600",
        },
    )


# ═══════════════════════════════════════════════════════════
#  Approve
# ═══════════════════════════════════════════════════════════

@router.put("/{entry_id}/approve")
async def approve_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """审核通过/取消审核 — 仅管理员"""
    if not _is_admin(user):
        raise HTTPException(status_code=403, detail="权限不足")
    result = await db.execute(select(ElectronicArchive).where(ElectronicArchive.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="记录不存在")
    entry.is_approved = not entry.is_approved
    await db.flush()
    await db.refresh(entry)
    return entry


# ═══════════════════════════════════════════════════════════
#  Delete
# ═══════════════════════════════════════════════════════════

@router.delete("/{entry_id}")
async def delete_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """删除文件或目录 — 已审核的不可删除"""
    result = await db.execute(select(ElectronicArchive).where(ElectronicArchive.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="记录不存在")

    if entry.is_approved:
        raise HTTPException(status_code=403, detail="已审核的记录不可删除")

    if entry.is_directory:
        prefix = f"{entry.directory}{entry.name}/"
        sub = await db.execute(
            select(ElectronicArchive).where(
                ElectronicArchive.directory.startswith(prefix)
            )
        )
        for s in sub.scalars():
            if s.is_approved:
                raise HTTPException(status_code=403, detail=f"子文件 '{s.name}' 已审核，无法删除此目录")
            if not s.is_directory and s.file_path:
                fp = os.path.join(UPLOAD_DIR, s.file_path)
                if os.path.exists(fp):
                    os.remove(fp)
            await db.delete(s)
    else:
        if entry.file_path:
            fp = os.path.join(UPLOAD_DIR, entry.file_path)
            if os.path.exists(fp):
                os.remove(fp)

    await db.delete(entry)
    await db.flush()
    return {"detail": "删除成功"}


# ═══════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════

def format_size(size: int) -> str:
    if size < 1024:
        return f"{size}B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f}KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f}MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.1f}GB"
