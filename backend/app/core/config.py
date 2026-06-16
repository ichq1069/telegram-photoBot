from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "Telegram PhotoBot Manager"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DB_TYPE: str = "sqlite"
    SQLITE_PATH: str = "/app/data/photobot.db"
    MYSQL_HOST: Optional[str] = None
    MYSQL_PORT: int = 3306
    MYSQL_USER: Optional[str] = None
    MYSQL_PASSWORD: Optional[str] = None
    MYSQL_DATABASE: Optional[str] = "photobot"
    SYNC_INTERVAL_MINUTES: int = 60

    SECRET_KEY: str = "change-me-in-production-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    TG_API_MODE: str = "official"
    TG_SELF_BUILD_API_URL: Optional[str] = None
    TG_SELF_BUILD_API_KEY: Optional[str] = None
    TG_API_TIMEOUT: int = 30

    UPLOAD_MAX_SIZE_MB: int = 20
    UPLOAD_ALLOWED_TYPES: str = "jpg,jpeg,png,gif,webp,bmp"
    COMPRESS_ENABLED: bool = True
    COMPRESS_QUALITY: int = 85
    COMPRESS_MAX_WIDTH: int = 2560

    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "/app/data/logs/app.log"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
