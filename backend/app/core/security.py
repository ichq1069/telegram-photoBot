from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import logging
from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger("photobot")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.info(f"Token created: sub={data.get('sub')}, key_prefix={settings.SECRET_KEY[:8]}...")
    return token


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    from app.models.user import AdminUser

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        logger.warning("get_current_user: no token provided")
        raise credentials_exception

    logger.info(f"get_current_user: token received, key_prefix={settings.SECRET_KEY[:8]}...")

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        logger.info(f"get_current_user: token decoded, sub={payload.get('sub')}, type={type(payload.get('sub'))}")
    except JWTError as e:
        logger.error(f"get_current_user: JWT decode failed: {e}")
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        logger.warning("get_current_user: sub not found in token")
        raise credentials_exception

    user_id = int(user_id)
    logger.info(f"get_current_user: looking up user id={user_id}")

    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if user is None:
        logger.warning(f"get_current_user: user id={user_id} not found in database")
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")
    return user
