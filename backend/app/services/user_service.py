from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.user import AdminUser
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash


class UserService:

    @staticmethod
    def get_user(db: Session, user_id: int) -> Optional[AdminUser]:
        return db.query(AdminUser).filter(AdminUser.id == user_id).first()

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[AdminUser]:
        return db.query(AdminUser).filter(AdminUser.username == username).first()

    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[AdminUser]:
        return db.query(AdminUser).offset(skip).limit(limit).all()

    @staticmethod
    def create_user(db: Session, data: UserCreate) -> AdminUser:
        user = AdminUser(
            username=data.username,
            password_hash=get_password_hash(data.password),
            role=data.role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_user(db: Session, user_id: int, data: UserUpdate) -> Optional[AdminUser]:
        user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
        if not user:
            return None
        if data.password:
            user.password_hash = get_password_hash(data.password)
        if data.role is not None:
            user.role = data.role
        if data.is_active is not None:
            user.is_active = data.is_active
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
        if not user:
            return False
        db.delete(user)
        db.commit()
        return True

    @staticmethod
    def record_login(db: Session, user: AdminUser, ip: str):
        from datetime import datetime
        user.last_login_ip = ip
        user.last_login_time = datetime.utcnow()
        user.login_count = (user.login_count or 0) + 1
        db.commit()

    @staticmethod
    def ensure_admin_exists(db: Session):
        existing = db.query(AdminUser).first()
        if not existing:
            admin = AdminUser(
                username="admin",
                password_hash=get_password_hash("admin123"),
                role="admin",
            )
            db.add(admin)
            db.commit()
