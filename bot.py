import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import ErrorEvent

from config import BOT_TOKEN
from database.db import init_db, close_db, get_db
from database.models import mark_user_blocked
from handlers import start, reciter, quran, admin
from services.uploader import get_client, stop_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    session = AiohttpSession(timeout=300)  # 5 минут — для больших аудиофайлов
    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Init DB tables & seed reciters
    await init_db()

    # Запускаем Pyrogram user-клиент (может запросить код из SMS при первом запуске)
    await get_client()

    # Register routers (order matters — more specific first)
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(reciter.router)
    dp.include_router(quran.router)

    @dp.error()
    async def on_error(event: ErrorEvent) -> bool:
        if isinstance(event.exception, TelegramForbiddenError):
            upd = event.update
            user_id = None
            if upd.message:
                user_id = upd.message.from_user.id
            elif upd.callback_query:
                user_id = upd.callback_query.from_user.id
            if user_id:
                db = await get_db()
                await mark_user_blocked(db, user_id)
        return True

    logger.info("Bot started")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await close_db()
        await stop_client()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
