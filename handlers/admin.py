import asyncio

from aiogram import Router, Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_ID
from database.db import get_db
from database.models import get_stats, get_all_active_user_ids, mark_user_blocked

router = Router()

LANG_FLAG = {"ru": "🇷🇺", "uz": "🇺🇿"}


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if message.from_user.id != ADMIN_ID:
        return

    db = await get_db()
    s  = await get_stats(db)

    lang_lines = "\n".join(
        f"  {LANG_FLAG.get(lang, '🌐')} {lang}: <b>{cnt}</b>"
        for lang, cnt in s["langs"]
    ) or "  —"

    reciter_lines = "\n".join(
        f"  • {name}: <b>{cnt}</b>" for name, cnt in s["reciters"]
    ) or "  —"

    text = (
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: <b>{s['total']}</b>\n"
        f"🟢 Активных: <b>{s['active']}</b>\n"
        f"🔴 Заблокировали: <b>{s['blocked']}</b>\n\n"
        f"🌍 <b>По языкам:</b>\n{lang_lines}\n\n"
        f"🎙 <b>По чтецам:</b>\n{reciter_lines}\n\n"
        f"💾 <b>Кэш:</b> {s['cache']['surahs']} сур · {s['cache']['ayahs']} аятов"
    )
    await message.answer(text)


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, bot: Bot) -> None:
    if message.from_user.id != ADMIN_ID:
        return

    # Текст берём из reply или из самого сообщения после команды
    if message.reply_to_message:
        src = message.reply_to_message
    else:
        text = message.text.removeprefix("/broadcast").strip()
        if not text:
            await message.answer(
                "Использование:\n"
                "• <code>/broadcast Текст сообщения</code>\n"
                "• Ответьте на сообщение командой /broadcast",
                parse_mode="HTML",
            )
            return
        src = None

    db       = await get_db()
    user_ids = await get_all_active_user_ids(db)
    total    = len(user_ids)

    status = await message.answer(f"📤 Начинаю рассылку — {total} пользователей...")

    ok = blocked = failed = 0

    for user_id in user_ids:
        try:
            if src:
                await src.copy_to(user_id)
            else:
                await bot.send_message(user_id, text, parse_mode="HTML")
            ok += 1
        except TelegramForbiddenError:
            await mark_user_blocked(db, user_id)
            blocked += 1
        except (TelegramBadRequest, Exception):
            failed += 1

        # ~25 сообщений/сек — не превышаем flood limit
        await asyncio.sleep(0.04)

    await status.edit_text(
        f"✅ Рассылка завершена\n\n"
        f"📨 Отправлено: <b>{ok}</b>\n"
        f"🔴 Заблокировали: <b>{blocked}</b>\n"
        f"⚠️ Ошибки: <b>{failed}</b>\n"
        f"👥 Всего: <b>{total}</b>",
        parse_mode="HTML",
    )
