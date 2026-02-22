import re
import aiohttp
from aiohttp import ClientResponseError
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup

from database.db import get_db
from database.models import get_user_reciter, get_user_language, get_cached, save_to_cache
from services.quran_api import get_surah, get_ayah
from services.uploader import upload_audio, download_to_tempfile
from keyboards.keyboards import nav_kb
from locales import t

router = Router()

RE_SURAH = re.compile(r"^\d{1,3}$")
RE_AYAH  = re.compile(r"^(\d{1,3}):(\d{1,3})$")
MAX_SURAH = 114
MAX_TEXT  = 4096


@router.message(~F.via_bot)
async def handle_quran_query(message: Message) -> None:
    text = (message.text or "").strip()
    if not text:
        return

    db = await get_db()
    lang    = await get_user_language(db, message.from_user.id) or "ru"
    reciter = await get_user_reciter(db, message.from_user.id)

    if not reciter:
        await message.answer(t(lang, "no_reciter"), parse_mode="HTML")
        return

    if m := RE_AYAH.match(text):
        surah_n, ayah_n = int(m.group(1)), int(m.group(2))
        await _send_ayah(message, surah_n, ayah_n, reciter, lang)

    elif RE_SURAH.match(text):
        surah_n = int(text)
        if not 1 <= surah_n <= MAX_SURAH:
            await message.answer(t(lang, "bad_surah"))
            return
        await _send_surah(message, surah_n, reciter, lang)

    else:
        await message.answer(t(lang, "bad_format"), parse_mode="HTML")


@router.callback_query(F.data.startswith("nav:"))
async def nav_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    parts = callback.data.split(":")

    if parts[1] == "none":
        return

    db      = await get_db()
    lang    = await get_user_language(db, callback.from_user.id) or "ru"
    reciter = await get_user_reciter(db, callback.from_user.id)

    if not reciter:
        await callback.message.answer(t(lang, "no_reciter"), parse_mode="HTML")
        return

    if parts[1] == "s":
        await _send_surah(callback.message, int(parts[2]), reciter, lang)
    elif parts[1] == "a":
        await _send_ayah(callback.message, int(parts[2]), int(parts[3]), reciter, lang)


# ─── helpers ────────────────────────────────────────────────────────────────

async def _send_audio(message: Message, file_id: str, title: str, performer: str) -> None:
    await message.answer_audio(audio=file_id, title=title, performer=performer)


async def _send_text(message: Message, text: str, markup: InlineKeyboardMarkup) -> None:
    for i in range(0, len(text), MAX_TEXT):
        kb = markup if i + MAX_TEXT >= len(text) else None
        await message.answer(text[i:i + MAX_TEXT], parse_mode="HTML", reply_markup=kb)


# ─── surah ──────────────────────────────────────────────────────────────────

async def _send_surah(message: Message, surah_n: int, reciter, lang: str) -> None:
    db     = await get_db()
    cached = await get_cached(db, reciter.identifier, surah_n, None)

    if cached:
        await _send_audio(message, cached["file_id"], cached["title"], cached["performer"])
        caption = cached["caption_ru"] if lang == "ru" else cached["caption_uz"]
        await _send_text(message, caption, nav_kb("surah", surah_n, lang=lang))
        return

    wait_msg = await message.answer(t(lang, "loading_surah"))
    try:
        async with aiohttp.ClientSession() as session:
            info = await get_surah(session, surah_n, reciter.identifier)
        filepath = await download_to_tempfile(info.audio_url)
    except Exception as e:
        await wait_msg.delete()
        await message.answer(t(lang, "loading_error", e=e))
        return

    title     = f"Sura {info.surah_number} - {info.name_arabic} ({info.name})"
    performer = reciter.display_name
    filename  = f"Sura {info.surah_number} - {info.name} - {performer}.mp3"

    caption_ru = t("ru", "surah_caption",
        number=info.surah_number, arabic=info.name_arabic,
        name=info.name, reciter=performer,
        translation=info.name_translation, total=info.total_ayah)
    caption_uz = t("uz", "surah_caption",
        number=info.surah_number, arabic=info.name_arabic,
        name=info.name, reciter=performer,
        translation=info.name_translation, total=info.total_ayah)

    try:
        file_id = await upload_audio(filepath, filename, title=title, performer=performer)
    except Exception as e:
        await wait_msg.delete()
        await message.answer(t(lang, "upload_error", e=e))
        return

    await save_to_cache(db, reciter.identifier, surah_n, None,
                        file_id, caption_ru, caption_uz, title, performer)
    await wait_msg.delete()

    caption = caption_ru if lang == "ru" else caption_uz
    await _send_audio(message, file_id, title, performer)
    await _send_text(message, caption, nav_kb("surah", surah_n, lang=lang))


# ─── ayah ───────────────────────────────────────────────────────────────────

async def _send_ayah(message: Message, surah_n: int, ayah_n: int, reciter, lang: str) -> None:
    db     = await get_db()
    cached = await get_cached(db, reciter.identifier, surah_n, ayah_n)

    if cached:
        await _send_audio(message, cached["file_id"], cached["title"], cached["performer"])
        caption = cached["caption_ru"] if lang == "ru" else cached["caption_uz"]
        await _send_text(message, caption, nav_kb("ayah", surah_n, ayah_n, lang=lang))
        return

    wait_msg = await message.answer(t(lang, "loading_ayah"))
    try:
        async with aiohttp.ClientSession() as session:
            ayah = await get_ayah(session, surah_n, ayah_n, reciter.identifier)
        filepath = await download_to_tempfile(ayah.audio_url)
    except ClientResponseError as e:
        await wait_msg.delete()
        if e.status == 404:
            await message.answer(t(lang, "ayah_not_found", surah=surah_n, ayah=ayah_n), parse_mode="HTML")
        else:
            await message.answer(t(lang, "ayah_error", e=e))
        return
    except Exception as e:
        await wait_msg.delete()
        await message.answer(t(lang, "ayah_error", e=e))
        return

    title     = f"{ayah.surah_name} {surah_n}:{ayah_n}"
    performer = reciter.display_name
    filename  = f"{ayah.surah_name} {surah_n}-{ayah_n} - {performer}.mp3"

    caption_ru = t("ru", "ayah_caption",
        surah_name=ayah.surah_name, surah=surah_n, ayah=ayah_n,
        reciter=performer, translation=ayah.russian_text)
    caption_uz = t("uz", "ayah_caption",
        surah_name=ayah.surah_name, surah=surah_n, ayah=ayah_n,
        reciter=performer, translation=ayah.uzbek_text)

    try:
        file_id = await upload_audio(filepath, filename, title=title, performer=performer)
    except Exception as e:
        await wait_msg.delete()
        await message.answer(t(lang, "upload_error", e=e))
        return

    await save_to_cache(db, reciter.identifier, surah_n, ayah_n,
                        file_id, caption_ru, caption_uz, title, performer)
    await wait_msg.delete()

    caption = caption_ru if lang == "ru" else caption_uz
    await _send_audio(message, file_id, title, performer)
    await _send_text(message, caption, nav_kb("ayah", surah_n, ayah_n, lang=lang))
