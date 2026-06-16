from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    verify_password,
    create_access_token,
    get_current_user,
    get_password_hash,
)
from app.schemas.user import (
    Token,
    UserResponse,
    UserCreate,
    UserUpdate,
    PasswordChange,
)
from app.services.user_service import UserService
from app.models.user import AdminUser

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = UserService.get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    client_ip = request.client.host if request.client else "unknown"
    UserService.record_login(db, user, client_ip)

    access_token = create_access_token(data={"sub": user.id})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
def get_me(current_user: AdminUser = Depends(get_current_user)):
    return current_user


@router.put("/me/password")
def change_password(
    data: PasswordChange,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    current_user.password_hash = get_password_hash(data.new_password)
    db.commit()
    return {"message": "密码修改成功"}
