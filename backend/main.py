"""FastAPI main application for Engineering Management System."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from core.config import settings
from core.database import init_db, close_db
from core.security import get_password_hash
from api.routes import api_router

FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "dist"
UPLOADS_DIR = Path(__file__).parent / "api" / "routes" / "uploads"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from core.database import async_session_factory
    from models import User, Tenant

    async with async_session_factory() as db:
        for code, name in [("乙", "乙公司"), ("丙", "丙公司")]:
            r = await db.execute(select(Tenant).where(Tenant.code == code))
            if not r.scalar_one_or_none():
                db.add(Tenant(name=name, code=code))
        await db.flush()  # 确保租户 ID 生成

        # Create super admin
        r = await db.execute(select(User).where(User.username == settings.SUPER_ADMIN_USERNAME))
        if not r.scalar_one_or_none():
            # 获取默认租户 ID
            tenant_r = await db.execute(select(Tenant).where(Tenant.code == "乙"))
            tenant = tenant_r.scalar_one_or_none()
            tenant_id = tenant.id if tenant else 1
            db.add(User(
                username=settings.SUPER_ADMIN_USERNAME,
                password_hash=get_password_hash(settings.SUPER_ADMIN_PASSWORD),
                display_name="超级管理员",
                role="super_admin",
                tenant_id=tenant_id,
            ))
        await db.commit()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix="/api/v1")


# Serve frontend SPA
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

    # Mount upload directories for file access
    uploads_dir = UPLOADS_DIR
    if uploads_dir.exists():
        app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return JSONResponse({"detail": "Frontend not built"}, status_code=404)
