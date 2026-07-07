"""Database engine and session management."""
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from core.config import settings

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_url = settings.DATABASE_URL

# Fix relative SQLite path
if db_url.startswith("sqlite") and "/./" in db_url:
    db_url = db_url.replace("/./", f"/{BACKEND_DIR}/")

engine = create_async_engine(db_url, echo=False, pool_size=5, max_overflow=10)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    """Get database session - FastAPI dependency."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_session() -> AsyncSession:
    """Utility for getting a session outside of FastAPI dependency injection."""
    session = async_session_factory()
    try:
        return session
    except:
        await session.close()
        raise


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    await engine.dispose()
