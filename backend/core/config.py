"""Core configuration for engineering management system."""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    APP_NAME: str = "工程管理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENV: str = os.getenv("ENV", "development")

    # Database
    @property
    def DATABASE_URL(self) -> str:
        if self.ENV == "production":
            return "postgresql+asyncpg://engadmin:EngMgmt%402026@127.0.0.1:5432/eng_mgmt"
        return "sqlite+aiosqlite:///./eng_mgmt.db"

    @property
    def DATABASE_URL_SYNC(self) -> str:
        if self.ENV == "production":
            return "postgresql://engadmin:EngMgmt%402026@127.0.0.1:5432/eng_mgmt"
        return "sqlite:///./eng_mgmt.db"

    SECRET_KEY: str = "eng-mgmt-secret-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    WEBDAV_URL: str = "http://127.0.0.1:19798/"
    WEBDAV_USER: str = "admin"
    WEBDAV_PASS: str = "115backup"
    FILE_STORAGE_PATH: str = "/mnt/115pan/工程管理系统"
    WXPUSHER_TOKEN: Optional[str] = None
    SUPER_ADMIN_USERNAME: str = "admin"
    SUPER_ADMIN_PASSWORD: str = "admin123"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
