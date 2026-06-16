from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import AdminUser
from app.schemas.bot import BotCreate, BotUpdate, BotResponse, BotCheckResult
from app.services.bot_service import BotService

router = APIRouter(prefix="/api/bots", tags=["机器人管理"])


@router.get("", response_model=List[BotResponse])
def list_bots(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    return BotService.get_bots(db, skip, limit)


@router.get("/{bot_id}", response_model=BotResponse)
def get_bot(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bot = BotService.get_bot(db, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    return bot


@router.post("", response_model=BotResponse)
def create_bot(
    data: BotCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    return BotService.create_bot(db, data)


@router.put("/{bot_id}", response_model=BotResponse)
def update_bot(
    bot_id: int,
    data: BotUpdate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    bot = BotService.update_bot(db, bot_id, data)
    if not bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    return bot


@router.delete("/{bot_id}")
def delete_bot(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    if not BotService.delete_bot(db, bot_id):
        raise HTTPException(status_code=404, detail="机器人不存在")
    return {"message": "删除成功"}


@router.post("/{bot_id}/check", response_model=BotCheckResult)
async def check_bot(
    bot_id: int,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    result = await BotService.check_bot(db, bot_id)
    if not result:
        raise HTTPException(status_code=404, detail="机器人不存在")
    return result


@router.post("/check-all", response_model=List[BotCheckResult])
async def check_all_bots(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
):
    return await BotService.check_all_bots(db)
