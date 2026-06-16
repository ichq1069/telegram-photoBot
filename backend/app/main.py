import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.services.user_service import UserService
from app.services.image_service import ImageService


def setup_logging():
    os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(settings.LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def init_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        UserService.ensure_admin_exists(db)
        from app.services.system_service import ConfigService
        defaults = {
            "site_title": "Telegram PhotoBot Manager",
            "upload_max_size_mb": str(settings.UPLOAD_MAX_SIZE_MB),
            "upload_allowed_types": settings.UPLOAD_ALLOWED_TYPES,
            "compress_enabled": str(settings.COMPRESS_ENABLED).lower(),
            "compress_quality": str(settings.COMPRESS_QUALITY),
            "tg_api_mode": settings.TG_API_MODE,
            "db_type": settings.DB_TYPE,
            "sync_interval_minutes": str(settings.SYNC_INTERVAL_MINUTES),
            "sync_enabled": "false",
        }
        for key, value in defaults.items():
            existing = ConfigService.get_config(db, key)
            if existing is None:
                ConfigService.set_config(db, key, value, f"系统默认配置: {key}")
    finally:
        db.close()

    ImageService.ensure_dirs()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    init_database()
    logging.getLogger("photobot").info("Telegram PhotoBot Manager starting...")
    yield
    logging.getLogger("photobot").info("Telegram PhotoBot Manager shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import auth, bots, images, messages, admin_users, system

app.include_router(auth.router)
app.include_router(bots.router)
app.include_router(images.router)
app.include_router(messages.router)
app.include_router(admin_users.router)
app.include_router(system.router)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "db_type": settings.DB_TYPE,
    }
