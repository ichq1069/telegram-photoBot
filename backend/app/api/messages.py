from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import AdminUser
from app.models.bot import BotConfig
from app.schemas.message import (
    MessageTemplateCreate,
    MessageTemplateUpdate,
    MessageTemplateResponse,
    BroadcastRequest,
)
from app.services.message_service import MessageService
from app.services.telegram_adapter import tg_adapter

router = APIRouter(prefix="/api/messages", tags=["消息管理"])


@router.get("/templates", response_model=List[MessageTemplateResponse])
def list_templates(
    bot_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    return MessageService.get_templates(db, bot_id, skip, limit)


@router.post("/templates", response_model=MessageTemplateResponse)
def create_template(
    data: MessageTemplateCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    return MessageService.create_template(db, data)


@router.put("/templates/{template_id}", response_model=MessageTemplateResponse)
def update_template(
    template_id: int,
    data: MessageTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    template = MessageService.update_template(db, template_id, data)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


@router.delete("/templates/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    if not MessageService.delete_template(db, template_id):
        raise HTTPException(status_code=404, detail="模板不存在")
    return {"message": "删除成功"}


@router.post("/broadcast")
async def broadcast(
    data: BroadcastRequest,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bot = db.query(BotConfig).filter(BotConfig.id == data.bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    if not bot.is_enabled:
        raise HTTPException(status_code=400, detail="机器人已禁用")

    result = await tg_adapter.broadcast_message(
        bot.bot_token, data.chat_ids, data.message, data.parse_mode
    )
    return result
