from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import AdminUser
from app.schemas.user import UserResponse, UserCreate, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/api/admin/users", tags=["用户管理"])


@router.get("", response_model=List[UserResponse])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    return UserService.get_users(db, skip, limit)


@router.post("", response_model=UserResponse)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")

    existing = UserService.get_user_by_username(db, data.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    return UserService.create_user(db, data)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")

    user = UserService.update_user(db, user_id, data)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="权限不足")
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    if not UserService.delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"message": "删除成功"}
