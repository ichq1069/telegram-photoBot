from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MessageTemplateCreate(BaseModel):
    bot_id: int
    name: str
    trigger_keyword: Optional[str] = None
    reply_type: str = "text"
    reply_content: Optional[str] = None
    welcome_message: Optional[str] = None
    is_enabled: bool = True


class MessageTemplateUpdate(BaseModel):
    name: Optional[str] = None
    trigger_keyword: Optional[str] = None
    reply_type: Optional[str] = None
    reply_content: Optional[str] = None
    welcome_message: Optional[str] = None
    is_enabled: Optional[bool] = None


class MessageTemplateResponse(BaseModel):
    id: int
    bot_id: int
    name: str
    trigger_keyword: Optional[str] = None
    reply_type: str
    reply_content: Optional[str] = None
    welcome_message: Optional[str] = None
    is_enabled: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BroadcastRequest(BaseModel):
    bot_id: int
    chat_ids: list[str]
    message: str
    parse_mode: str = "HTML"
