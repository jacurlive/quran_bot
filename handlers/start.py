from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from config import ADMIN_ID
from database.db import get_db
from database.models import get_user_language, set_user_language
from keyboards.keyboards import language_kb, main_menu_kb
from locales import t

router = Router()


async def show_main_menu(target, lang: str, name: str) -> None:
    """Отправляет главное меню (работает и с Message и с CallbackQuery)."""
    text = t(lang, "greeting", name=name) + "\n\n" + t(lang, "main_menu")
    kb = main_menu_kb(lang)
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    else:
        await target.answer(text, parse_mode="HTML", reply_markup=kb)


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot) -> None:
    db   = await get_db()
    lang = await get_user_language(db, message.from_user.id)
    user = message.from_user

    # Уведомляем админа
    username = f"@{user.username}" if user.username else "—"
    await bot.send_message(
        ADMIN_ID,
        f"👤 <b>Новый /start</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"👤 Имя: {user.full_name}\n"
        f"🔗 Username: {username}\n"
        f"🌍 Язык TG: {user.language_code or '—'}\n"
        f"📱 Бот: {'новый' if lang is None else 'вернулся'}",
        parse_mode="HTML",
    )

    if lang is None:
        await message.answer(t("ru", "choose_language"), reply_markup=language_kb())
        return

    await show_main_menu(message, lang, user.full_name)


@router.message(Command("language"))
async def cmd_language(message: Message) -> None:
    await message.answer(t("ru", "choose_language"), reply_markup=language_kb())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    db   = await get_db()
    lang = await get_user_language(db, message.from_user.id) or "ru"
    await message.answer(t(lang, "help"), parse_mode="HTML")


@router.callback_query(F.data.startswith("lang:"))
async def on_language_chosen(call: CallbackQuery) -> None:
    lang = call.data.split(":")[1]  # "ru" or "uz"
    db = await get_db()
    await set_user_language(db, call.from_user.id, lang)
    await call.answer(t(lang, "language_set"))
    await show_main_menu(call, lang, call.from_user.full_name)
