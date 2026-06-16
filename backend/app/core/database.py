from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
from typing import Generator

SQLALCHEMY_DATABASE_URL = f"sqlite:///{settings.SQLITE_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_mysql_url() -> str:
    return (
        f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
        f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
    )


mysql_engine = None
if settings.MYSQL_HOST:
    mysql_engine = create_engine(
        get_mysql_url(),
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=settings.DEBUG,
    )


def get_mysql_db() -> Generator:
    if mysql_engine is None:
        raise RuntimeError("MySQL not configured")
    db = sessionmaker(autocommit=False, autoflush=False, bind=mysql_engine)()
    try:
        yield db
    finally:
        db.close()
