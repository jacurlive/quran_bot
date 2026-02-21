from aiogram import Router, Bot
from aiogram.types import (
    InlineQuery, InlineQueryResultArticle, InlineQueryResultCachedAudio,
    InputTextMessageContent, ChosenInlineResult,
)

from database.db import get_db
from database.models import (
    get_all_reciters, set_user_reciter, get_reciter_by_id,
    get_user_language, get_user_reciter, get_cached,
)
from locales import t

router = Router()

MAX_CAPTION = 1024


@router.inline_query()
async def inline_handler(query: InlineQuery) -> None:
    if query.query.startswith("share:"):
        await _handle_share(query)
    else:
        await _handle_reciters(query)


async def _handle_reciters(query: InlineQuery) -> None:
    db      = await get_db()
    reciters = await get_all_reciters(db)
    lang    = await get_user_language(db, query.from_user.id) or "ru"

    results = []
    for reciter in reciters:
        results.append(InlineQueryResultArticle(
            id=str(reciter.id),
            title=reciter.display_name,
            description=reciter.name,
            input_message_content=InputTextMessageContent(
                message_text=f"✅ {reciter.display_name}",
                parse_mode="HTML",
            ),
            thumbnail_url=(
                f"https://ui-avatars.com/api/?name="
                f"{reciter.display_name.replace(' ', '+')}&background=1a6b3c&color=fff&size=64"
            ),
        ))

    await query.answer(results, cache_time=60, is_personal=True)


async def _handle_share(query: InlineQuery) -> None:
    # query format: share:s:{surah}  or  share:a:{surah}:{ayah}
    parts = query.query.split(":")
    db      = await get_db()
    lang    = await get_user_language(db, query.from_user.id) or "ru"
    reciter = await get_user_reciter(db, query.from_user.id)

    if not reciter:
        await query.answer([], cache_time=0)
        return

    try:
        if parts[1] == "s":
            surah_n = int(parts[2])
            cached  = await get_cached(db, reciter.identifier, surah_n, None)
        else:
            surah_n = int(parts[2])
            ayah_n  = int(parts[3])
            cached  = await get_cached(db, reciter.identifier, surah_n, ayah_n)
    except (IndexError, ValueError):
        await query.answer([], cache_time=0)
        return

    if not cached:
        await query.answer([], cache_time=0)
        return

    caption = cached["caption_ru"] if lang == "ru" else cached["caption_uz"]

    result = InlineQueryResultCachedAudio(
        id="share",
        audio_file_id=cached["file_id"],
        caption=caption[:MAX_CAPTION],
        parse_mode="HTML",
    )
    await query.answer([result], cache_time=0, is_personal=True)


@router.chosen_inline_result()
async def on_reciter_chosen(result: ChosenInlineResult, bot: Bot) -> None:
    try:
        reciter_id = int(result.result_id)
    except ValueError:
        return  # share result — игнорируем

    db = await get_db()
    await set_user_reciter(db, result.from_user.id, reciter_id)

    reciter = await get_reciter_by_id(db, reciter_id)
    lang    = await get_user_language(db, result.from_user.id) or "ru"

    if not reciter:
        return

    await bot.send_message(
        chat_id=result.from_user.id,
        text=t(lang, "search_help"),
        parse_mode="HTML",
    )
