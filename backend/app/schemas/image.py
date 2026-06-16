from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ImageResponse(BaseModel):
    id: int
    filename: str
    original_name: str
    file_size: int
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    tg_file_id: Optional[str] = None
    tg_channel_id: Optional[str] = None
    direct_link: Optional[str] = None
    https_link: Optional[str] = None
    markdown_link: Optional[str] = None
    bbcode_link: Optional[str] = None
    category: str
    tags: Optional[str] = None
    is_public: bool
    expire_time: Optional[datetime] = None
    view_count: int
    uploaded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ImageUpdate(BaseModel):
    filename: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    is_public: Optional[bool] = None
    access_password: Optional[str] = None
    expire_time: Optional[datetime] = None


class ImageUploadResponse(BaseModel):
    id: int
    filename: str
    file_size: int
    direct_link: Optional[str] = None
    https_link: Optional[str] = None
    markdown_link: Optional[str] = None
    bbcode_link: Optional[str] = None


class UploadStats(BaseModel):
    today_upload_count: int
    month_upload_count: int
    total_count: int
    total_size: int
    total_views: int
