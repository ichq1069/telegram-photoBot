import os
import time
import psutil
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text, desc
from app.core.config import settings
from app.core.database import mysql_engine, SessionLocal, Base
from app.models.log import SystemLog
from app.models.config import SystemConfig
from app.models.image import ImageResource
from app.models.bot import BotConfig
from app.schemas.system import SystemStats, DatabaseStatus


START_TIME = time.time()


class LogService:

    @staticmethod
    def add_log(
        db: Session,
        log_type: str,
        message: str,
        level: str = "INFO",
        source: str = None,
        detail: str = None,
        ip_address: str = None,
    ):
        log_entry = SystemLog(
            log_type=log_type,
            level=level,
            source=source,
            message=message,
            detail=detail,
            ip_address=ip_address,
        )
        db.add(log_entry)
        db.commit()

    @staticmethod
    def get_logs(
        db: Session,
        log_type: Optional[str] = None,
        level: Optional[str] = None,
        keyword: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple:
        query = db.query(SystemLog)
        if log_type:
            query = query.filter(SystemLog.log_type == log_type)
        if level:
            query = query.filter(SystemLog.level == level)
        if keyword:
            query = query.filter(
                SystemLog.message.contains(keyword)
                | SystemLog.detail.contains(keyword)
            )
        if start_time:
            query = query.filter(SystemLog.created_at >= start_time)
        if end_time:
            query = query.filter(SystemLog.created_at <= end_time)

        total = query.count()
        logs = (
            query.order_by(desc(SystemLog.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return logs, total


class ConfigService:

    @staticmethod
    def get_config(db: Session, key: str) -> Optional[str]:
        config = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
        return config.config_value if config else None

    @staticmethod
    def set_config(db: Session, key: str, value: str, description: str = None):
        config = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
        if config:
            config.config_value = value
            if description:
                config.description = description
        else:
            config = SystemConfig(
                config_key=key,
                config_value=value,
                description=description,
            )
            db.add(config)
        db.commit()

    @staticmethod
    def get_all_configs(db: Session) -> List[SystemConfig]:
        return db.query(SystemConfig).all()


class MonitorService:

    @staticmethod
    def get_system_stats(db: Session) -> SystemStats:
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        total_images = db.query(ImageResource).count()
        total_bots = db.query(BotConfig).count()
        uptime = int(time.time() - START_TIME)

        return SystemStats(
            cpu_percent=cpu,
            memory_percent=mem,
            disk_percent=disk,
            total_images=total_images,
            total_bots=total_bots,
            uptime_seconds=uptime,
        )


class DatabaseSyncService:

    @staticmethod
    def get_status(db: Session) -> DatabaseStatus:
        mysql_configured = bool(settings.MYSQL_HOST)
        mysql_connected = False
        if mysql_engine:
            try:
                with mysql_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                mysql_connected = True
            except Exception:
                pass

        last_sync = ConfigService.get_config(db, "last_sync_time")
        last_sync_time = (
            datetime.fromisoformat(last_sync) if last_sync else None
        )

        return DatabaseStatus(
            current_db=settings.DB_TYPE,
            mysql_configured=mysql_configured,
            mysql_connected=mysql_connected,
            sync_enabled=ConfigService.get_config(db, "sync_enabled") == "true",
            last_sync_time=last_sync_time,
        )

    @staticmethod
    def switch_database(db: Session, target: str):
        if target not in ("sqlite", "mysql"):
            raise ValueError("Invalid database target")
        if target == "mysql" and not mysql_engine:
            raise RuntimeError("MySQL not configured")

    @staticmethod
    def sync_to_mysql(db: Session):
        if not mysql_engine:
            raise RuntimeError("MySQL not configured")
        try:
            target_tables = Base.metadata.tables.keys()
            source_session = SessionLocal()

            for table_name in target_tables:
                table = Base.metadata.tables[table_name]
                rows = source_session.execute(table.select()).fetchall()
                with mysql_engine.connect() as conn:
                    for row in rows:
                        row_dict = dict(row._mapping)
                        pk_columns = [c.name for c in table.primary_key.columns]
                        existing = conn.execute(
                            table.select().where(
                                *[
                                    getattr(table.c, col) == row_dict[col]
                                    for col in pk_columns
                                ]
                            )
                        ).first()
                        if existing:
                            conn.execute(
                                table.update()
                                .where(
                                    *[
                                        getattr(table.c, col) == row_dict[col]
                                        for col in pk_columns
                                    ]
                                )
                                .values(**row_dict)
                            )
                        else:
                            conn.execute(table.insert().values(**row_dict))
                    conn.commit()

            source_session.close()
            ConfigService.set_config(
                db, "last_sync_time", datetime.utcnow().isoformat()
            )
            LogService.add_log(db, "sync", "数据库同步到MySQL完成", "INFO", "db_sync")
        except Exception as e:
            LogService.add_log(
                db, "sync", f"数据库同步失败: {str(e)}", "ERROR", "db_sync"
            )
            raise
