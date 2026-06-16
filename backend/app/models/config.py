from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class SystemConfig(Base):
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(128), unique=True, nullable=False, index=True)
    config_value = Column(Text, nullable=True)
    config_type = Column(String(32), default="string")
    description = Column(String(256), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())
