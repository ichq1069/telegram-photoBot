from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class MessageTemplate(Base):
    __tablename__ = "message_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_id = Column(Integer, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    trigger_keyword = Column(String(256), nullable=True)
    reply_type = Column(String(32), default="text")
    reply_content = Column(Text, nullable=True)
    welcome_message = Column(Text, nullable=True)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
