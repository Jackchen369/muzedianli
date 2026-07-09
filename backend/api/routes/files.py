"""Contract file upload/download routes."""
import os, uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.config import settings
from core.security import get_current_admin, get_current_user
from models import ContractFile, AuditLog, User

router = APIRouter(prefix="/files", tags=["文件管理"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "contracts")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload/{project_id}")
async def upload_file(
    project_id: int,
    file: UploadFile = File(...),
    filetype: str = Form("contract"),
    ft: Optional[str] = Query(None, alias="filetype"),
    partner_id: Optional[int] = Form(None),
    remark: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """上传合同/发票/回单等电子文件"""
    if user.role not in ("super_admin", "company_admin", "project_manager"):
        raise HTTPException(status_code=403, detail="权限不足")
    # 优先使用查询参数中的 filetype（el-upload 不发送 Form 字段）
    if ft:
        filetype = ft
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名为空")

    # Generate unique filename
    ext = os.path.splitext(file.filename)[1] or ""
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # Save file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Seals & invoices: 只存文件，不写 DB（由调用方管理）
    if filetype in ("seal", "invoice"):
        return {"filename": file.filename, "filepath": unique_name, "filesize": len(content)}

    # DB record
    cf = ContractFile(
        tenant_id=user.tenant_id or 1,
        project_id=project_id,
        partner_id=partner_id,
        filename=file.filename,
        filepath=unique_name,
        filesize=len(content),
        filetype=filetype,
        remark=remark,
    )
    db.add(cf)
    await db.flush()
    await db.refresh(cf)

    db.add(AuditLog(
        tenant_id=user.tenant_id or 1, user_id=user.id, username=user.username,
        action="upload_file", biz_type="contract_file", biz_id=cf.id,
    ))
    return cf


@router.get("/list/{project_id}")
async def list_files(
    project_id: int,
    partner_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取项目的文件列表，可选按分包单位筛选"""
    query = select(ContractFile).where(ContractFile.project_id == project_id)
    if partner_id is not None:
        query = query.where(ContractFile.partner_id == partner_id)
    result = await db.execute(query.order_by(ContractFile.id.desc()))
    return result.scalars().all()


@router.get("/download/{file_id}")
async def download_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """下载文件"""
    result = await db.execute(select(ContractFile).where(ContractFile.id == file_id))
    cf = result.scalar_one_or_none()
    if not cf:
        raise HTTPException(status_code=404, detail="文件不存在")

    file_path = os.path.join(UPLOAD_DIR, cf.filepath)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件已被删除")

    return FileResponse(
        path=file_path,
        filename=cf.filename,
        media_type="application/octet-stream",
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """删除文件"""
    result = await db.execute(select(ContractFile).where(ContractFile.id == file_id))
    cf = result.scalar_one_or_none()
    if not cf:
        raise HTTPException(status_code=404, detail="文件不存在")

    # Delete physical file
    file_path = os.path.join(UPLOAD_DIR, cf.filepath)
    if os.path.exists(file_path):
        os.remove(file_path)

    await db.delete(cf)
    await db.flush()
    return {"detail": "删除成功"}


@router.get("/by-filename/{filename:path}")
async def get_file_by_filename(filename: str):
    """通过文件名直接获取上传的文件（用于印章图片等）"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(path=file_path)
