from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_type = Column(String(32), nullable=False, index=True)
    level = Column(String(16), default="INFO")
    source = Column(String(64), nullable=True)
    message = Column(Text, nullable=True)
    detail = Column(Text, nullable=True)
    ip_address = Column(String(64), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
