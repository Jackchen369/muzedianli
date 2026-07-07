"""系统数据备份 — 创建/下载/删除数据库备份。"""
import os
import shutil
import glob
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.security import get_current_admin, User
from models import AuditLog

router = APIRouter(prefix="/backup", tags=["系统备份"])

BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "eng_mgmt.db")


@router.post("")
async def create_backup(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """创建数据库备份"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, filename)

    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="数据库文件不存在")

    # 关闭所有连接后复制文件（SQLite WAL模式下直接复制是安全的）
    shutil.copy2(DB_PATH, backup_path)

    # 同时备份 WAL 和 SHM 文件（如果有）
    for ext in ["-wal", "-shm"]:
        src = DB_PATH + ext
        if os.path.exists(src):
            shutil.copy2(src, backup_path + ext)

    size = os.path.getsize(backup_path)

    # Audit log
    db.add(AuditLog(
        tenant_id=admin.tenant_id, user_id=admin.id, username=admin.username,
        action="create_backup", biz_type="backup", detail={"filename": filename, "size": size},
    ))

    return {
        "filename": filename,
        "size": size,
        "size_display": format_size(size),
        "created_at": timestamp,
    }


@router.get("")
async def list_backups(
    admin: User = Depends(get_current_admin),
):
    """列出所有备份文件"""
    files = []
    for f in sorted(glob.glob(os.path.join(BACKUP_DIR, "backup_*.db")), reverse=True):
        stat = os.stat(f)
        filename = os.path.basename(f)
        files.append({
            "filename": filename,
            "size": stat.st_size,
            "size_display": format_size(stat.st_size),
            "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        })
    return files


@router.get("/download/{filename}")
async def download_backup(
    filename: str,
    admin: User = Depends(get_current_admin),
):
    """下载备份文件"""
    # 安全检查：防止路径穿越
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="非法的文件名")
    file_path = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="备份文件不存在")
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream",
    )


@router.delete("/{filename}")
async def delete_backup(
    filename: str,
    admin: User = Depends(get_current_admin),
):
    """删除备份文件"""
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="非法的文件名")
    file_path = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="备份文件不存在")
    os.remove(file_path)
    # 清理 WAL/SHM
    for ext in ["-wal", "-shm"]:
        p = file_path + ext
        if os.path.exists(p):
            os.remove(p)
    return {"detail": "删除成功"}


def format_size(size: int) -> str:
    if size < 1024:
        return f"{size}B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f}KB"
    else:
        return f"{size / (1024 * 1024):.1f}MB"
