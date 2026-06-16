from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, BigInteger
from sqlalchemy.sql import func
from app.core.database import Base


class ImageResource(Base):
    __tablename__ = "image_resources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(256), nullable=False)
    original_name = Column(String(256), nullable=False)
    file_size = Column(BigInteger, default=0)
    mime_type = Column(String(64), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    thumbnail_path = Column(String(512), nullable=True)
    tg_file_id = Column(String(256), nullable=True)
    tg_channel_id = Column(String(128), nullable=True)
    tg_message_id = Column(String(64), nullable=True)
    direct_link = Column(String(1024), nullable=True)
    https_link = Column(String(1024), nullable=True)
    markdown_link = Column(Text, nullable=True)
    bbcode_link = Column(Text, nullable=True)
    custom_domain = Column(String(256), nullable=True)
    category = Column(String(64), default="uncategorized")
    tags = Column(String(512), nullable=True)
    is_public = Column(Boolean, default=True)
    access_password = Column(String(128), nullable=True)
    expire_time = Column(DateTime, nullable=True)
    view_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())
