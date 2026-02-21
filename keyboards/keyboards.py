from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, SwitchInlineQueryChosenChat
from locales import t


def language_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇺🇿 O'zbek",  callback_data="lang:uz"),
    ]])


def main_menu_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=t(lang, "btn_choose_reciter"),
            switch_inline_query_current_chat=t(lang, "inline_query_text"),
        )
    ]])


def nav_kb(mode: str, surah_n: int, ayah_n: int = None, lang: str = "ru") -> InlineKeyboardMarkup:
    """Навигация под текстовым сообщением.
    mode = 'surah' | 'ayah'
    """
    if mode == "surah":
        prev_txt = f"◀️ {surah_n - 1}" if surah_n > 1    else "◀️"
        prev_cb  = f"nav:s:{surah_n - 1}" if surah_n > 1 else "nav:none"
        next_txt = f"{surah_n + 1} ▶️" if surah_n < 114  else "▶️"
        next_cb  = f"nav:s:{surah_n + 1}" if surah_n < 114 else "nav:none"
        share_q  = f"share:s:{surah_n}"
    else:
        prev_txt = f"◀️ {surah_n}:{ayah_n - 1}" if ayah_n > 1 else "◀️"
        prev_cb  = f"nav:a:{surah_n}:{ayah_n - 1}" if ayah_n > 1 else "nav:none"
        next_txt = f"{surah_n}:{ayah_n + 1} ▶️"
        next_cb  = f"nav:a:{surah_n}:{ayah_n + 1}"
        share_q  = f"share:a:{surah_n}:{ayah_n}"

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=prev_txt, callback_data=prev_cb),
            InlineKeyboardButton(text="🎙", switch_inline_query_current_chat=""),
            InlineKeyboardButton(text=next_txt, callback_data=next_cb),
        ],
        [
            InlineKeyboardButton(
                text=t(lang, "btn_share"),
                switch_inline_query_chosen_chat=SwitchInlineQueryChosenChat(
                    query=share_q,
                    allow_user_chats=True,
                    allow_group_chats=True,
                    allow_channel_chats=True,
                ),
            ),
        ],
    ])
