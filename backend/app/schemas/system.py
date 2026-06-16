from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SystemConfigResponse(BaseModel):
    id: int
    config_key: str
    config_value: Optional[str] = None
    config_type: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class SystemConfigUpdate(BaseModel):
    config_value: str


class LogResponse(BaseModel):
    id: int
    log_type: str
    level: str
    source: Optional[str] = None
    message: Optional[str] = None
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LogListResponse(BaseModel):
    items: list[LogResponse]
    total: int
    page: int
    page_size: int


class LogQuery(BaseModel):
    log_type: Optional[str] = None
    level: Optional[str] = None
    keyword: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    page: int = 1
    page_size: int = 20


class DatabaseStatus(BaseModel):
    current_db: str
    mysql_configured: bool
    mysql_connected: bool
    sync_enabled: bool
    last_sync_time: Optional[datetime] = None


class SystemStats(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    total_images: int
    total_bots: int
    uptime_seconds: int
