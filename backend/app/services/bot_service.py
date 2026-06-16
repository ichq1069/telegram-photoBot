from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.bot import BotConfig, BotStatus
from app.schemas.bot import BotCreate, BotUpdate, BotCheckResult
from app.services.telegram_adapter import tg_adapter


class BotService:

    @staticmethod
    def get_bots(db: Session, skip: int = 0, limit: int = 100) -> List[BotConfig]:
        return db.query(BotConfig).offset(skip).limit(limit).all()

    @staticmethod
    def get_bot(db: Session, bot_id: int) -> Optional[BotConfig]:
        return db.query(BotConfig).filter(BotConfig.id == bot_id).first()

    @staticmethod
    def create_bot(db: Session, data: BotCreate) -> BotConfig:
        bot = BotConfig(
            name=data.name,
            bot_token=data.bot_token,
            chat_id=data.chat_id,
            group_name=data.group_name,
            proxy_url=data.proxy_url,
            api_mode=data.api_mode,
            status="offline",
        )
        db.add(bot)
        db.commit()
        db.refresh(bot)
        return bot

    @staticmethod
    def update_bot(db: Session, bot_id: int, data: BotUpdate) -> Optional[BotConfig]:
        bot = db.query(BotConfig).filter(BotConfig.id == bot_id).first()
        if not bot:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(bot, key, value)
        db.commit()
        db.refresh(bot)
        return bot

    @staticmethod
    def delete_bot(db: Session, bot_id: int) -> bool:
        bot = db.query(BotConfig).filter(BotConfig.id == bot_id).first()
        if not bot:
            return False
        db.delete(bot)
        db.commit()
        return True

    @staticmethod
    async def check_bot(db: Session, bot_id: int) -> Optional[BotCheckResult]:
        bot = db.query(BotConfig).filter(BotConfig.id == bot_id).first()
        if not bot:
            return None

        try:
            result = await tg_adapter.get_me(
                bot.bot_token,
                api_mode=bot.api_mode or "official",
                self_build_url=bot.self_build_api_url,
                self_build_key=bot.self_build_api_key,
            )
            from datetime import datetime

            if result.get("ok"):
                bot.status = BotStatus.ONLINE.value
                bot.last_error = None
                bot.last_check_time = datetime.utcnow()
                db.commit()
                return BotCheckResult(
                    bot_id=bot.id,
                    name=bot.name,
                    online=True,
                    username=result["result"].get("username"),
                )
            else:
                bot.status = BotStatus.ERROR.value
                bot.last_error = result.get("description", "Unknown error")
                bot.last_check_time = datetime.utcnow()
                db.commit()
                return BotCheckResult(
                    bot_id=bot.id,
                    name=bot.name,
                    online=False,
                    error=result.get("description"),
                )
        except Exception as e:
            from datetime import datetime
            bot.status = BotStatus.ERROR.value
            bot.last_error = str(e)
            bot.last_check_time = datetime.utcnow()
            db.commit()
            return BotCheckResult(
                bot_id=bot.id,
                name=bot.name,
                online=False,
                error=str(e),
            )

    @staticmethod
    async def check_all_bots(db: Session) -> List[BotCheckResult]:
        bots = db.query(BotConfig).filter(BotConfig.is_enabled == True).all()
        results = []
        for bot in bots:
            result = await BotService.check_bot(db, bot.id)
            if result:
                results.append(result)
        return results
