from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class BotStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    DISABLED = "disabled"


class APIMode(str, enum.Enum):
    OFFICIAL = "official"
    SELF_BUILD = "self_build"


class BotConfig(Base):
    __tablename__ = "bot_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    bot_token = Column(String(256), nullable=False)
    chat_id = Column(String(128), nullable=True)
    group_name = Column(String(128), default="default")
    proxy_url = Column(String(256), nullable=True)
    api_mode = Column(String(16), default="official")
    status = Column(String(16), default="offline")
    is_enabled = Column(Boolean, default=True)
    last_check_time = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    extra_config = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
