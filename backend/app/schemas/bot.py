from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class BotCreate(BaseModel):
    name: str = Field(max_length=128)
    bot_token: str = Field(max_length=256)
    chat_id: Optional[str] = None
    group_name: str = "default"
    proxy_url: Optional[str] = None
    api_mode: str = "official"
    self_build_api_url: Optional[str] = None
    self_build_api_key: Optional[str] = None


class BotUpdate(BaseModel):
    name: Optional[str] = None
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    group_name: Optional[str] = None
    proxy_url: Optional[str] = None
    api_mode: Optional[str] = None
    self_build_api_url: Optional[str] = None
    self_build_api_key: Optional[str] = None
    is_enabled: Optional[bool] = None


class BotResponse(BaseModel):
    id: int
    name: str
    bot_token: str
    chat_id: Optional[str] = None
    group_name: str
    proxy_url: Optional[str] = None
    api_mode: str
    self_build_api_url: Optional[str] = None
    self_build_api_key: Optional[str] = None
    status: str
    is_enabled: bool
    last_check_time: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BotCheckResult(BaseModel):
    bot_id: int
    name: str
    online: bool
    username: Optional[str] = None
    error: Optional[str] = None
