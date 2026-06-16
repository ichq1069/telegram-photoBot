from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    last_login_ip: Optional[str] = None
    last_login_time: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    role: str = "admin"


class UserUpdate(BaseModel):
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=128)
