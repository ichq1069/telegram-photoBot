from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.bot import BotConfig
from app.models.message import MessageTemplate
from app.services.telegram_adapter import tg_adapter


class BotListener:
    """Bot 监听器 - 轮询 Telegram 获取消息并触发自动回复"""

    def __init__(self):
        self.running = False
        self.bots: dict[int, tuple[int, int]] = {}  # bot_id -> (last_update_id, chat_id)

    async def start(self):
        self.running = True
        import asyncio
        while self.running:
            try:
                await self._poll_bots()
            except Exception as e:
                logging.getLogger("photobot").error(f"BotListener error: {e}")
            await asyncio.sleep(2)

    async def stop(self):
        self.running = False
        await tg_adapter.close()

    async def _poll_bots(self):
        db = SessionLocal()
        try:
            bots = db.query(BotConfig).filter(
                BotConfig.is_enabled == True,
                BotConfig.status.in_(["online", "offline"]),
            ).all()

            for bot in bots:
                await self._poll_single_bot(db, bot)
        finally:
            db.close()

    async def _poll_single_bot(self, db: Session, bot: BotConfig):
        api_mode = bot.api_mode or "official"
        try:
            result = await tg_adapter.get_me(
                bot.bot_token,
                api_mode=api_mode,
                self_build_url=bot.self_build_api_url,
                self_build_key=bot.self_build_api_key,
            )

            if not result.get("ok"):
                bot.status = "error"
                bot.last_error = result.get("description", "Unknown")
                bot.last_check_time = __import__("datetime").datetime.utcnow()
                db.commit()
                return

            if bot.status != "online":
                bot.status = "online"
                bot.last_check_time = __import__("datetime").datetime.utcnow()
                db.commit()

            offset = self.bots.get(bot.id, (0, 0))[0]

            updates = await tg_adapter.call_method(
                bot.bot_token,
                "getUpdates",
                {"offset": offset, "timeout": 1},
                api_mode=api_mode,
                self_build_url=bot.self_build_api_url,
                self_build_key=bot.self_build_api_key,
            )

            if not updates.get("ok"):
                return

            updates_list = updates.get("result", [])
            if updates_list:
                last_update_id = updates_list[-1]["update_id"]
                self.bots[bot.id] = (last_update_id + 1, bot.chat_id or 0)

                for update in updates_list:
                    await self._handle_update(db, bot, update)

        except Exception as e:
            bot.status = "error"
            bot.last_error = str(e)
            bot.last_check_time = __import__("datetime").datetime.utcnow()
            db.commit()

    async def _handle_update(self, db: Session, bot: BotConfig, update: dict):
        message = update.get("message", {})
        text = (message.get("text") or "").strip()
        if not text:
            return

        chat_id = str(message.get("chat", {}).get("id", ""))
        if not chat_id:
            return

        if not bot.chat_id:
            bot.chat_id = chat_id
            db.commit()

        templates = db.query(MessageTemplate).filter(
            MessageTemplate.bot_id == bot.id,
            MessageTemplate.is_enabled == True,
        ).all()

        for tpl in templates:
            if tpl.trigger_keyword and text.lower() == tpl.trigger_keyword.lower():
                reply_type = tpl.reply_type or "text"
                if reply_type == "text" or reply_type == "photo" or reply_type == "document":
                    content = tpl.reply_content or ""
                    if reply_type == "photo":
                        await tg_adapter.send_photo(
                            bot.bot_token, chat_id, content,
                            api_mode=bot.api_mode or "official",
                            self_build_url=bot.self_build_api_url,
                            self_build_key=bot.self_build_api_key,
                        )
                    elif reply_type == "document":
                        await tg_adapter.send_document(
                            bot.bot_token, chat_id, content,
                            api_mode=bot.api_mode or "official",
                            self_build_url=bot.self_build_api_url,
                            self_build_key=bot.self_build_api_key,
                        )
                    else:
                        await tg_adapter.send_message(
                            bot.bot_token, chat_id, content,
                            api_mode=bot.api_mode or "official",
                            self_build_url=bot.self_build_api_url,
                            self_build_key=bot.self_build_api_key,
                        )
                    break
                elif reply_type == "welcome":
                    welcome = tpl.welcome_message or "Welcome!"
                    await tg_adapter.send_message(
                        bot.bot_token, chat_id, welcome,
                        api_mode=bot.api_mode or "official",
                        self_build_url=bot.self_build_api_url,
                        self_build_key=bot.self_build_api_key,
                    )
                    break
