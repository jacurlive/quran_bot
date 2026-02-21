"""Все строки интерфейса на русском и узбекском."""

TEXTS = {
    "ru": {
        "choose_language":    "🌐 Выберите язык / Tilni tanlang:",
        "btn_ru":             "🇷🇺 Русский",
        "btn_uz":             "🇺🇿 O'zbek",
        "language_set":       "✅ Язык установлен: Русский",

        "greeting": (
            "Ассаламу алейкум, <b>{name}</b>! 🕌\n\n"
            "Добро пожаловать в бот для прослушивания Священного Корана."
        ),
        "main_menu":          "Вы в главном меню бота.\nВыберите чтеца 👇",
        "btn_choose_reciter": "🎙 Выберите чтеца",
        "btn_share":          "🔗 Поделиться",
        "inline_query_text":  "Чтецы Корана",

        "search_help": (
            "🟥 Для этого чтеца доступен поиск по сурам и аятам.\n\n"
            "◼️ Введите сообщение в одном из следующих форматов —\n\n"
            "◼️ Для получения суры по номеру:\n"
            "✔️ <code>3</code> — для получения суры из Корана.\n\n"
            "◼️ Для получения аята из Корана:\n"
            "✔️ <code>6:12</code> — где первая цифра сура, вторая аят"
        ),

        "loading_surah":      "⏳ Загружаю суру, подождите...",
        "loading_ayah":       "⏳ Загружаю аят, подождите...",
        "loading_error":      "⚠️ Ошибка скачивания: {e}",
        "upload_error":       "⚠️ Ошибка загрузки в хранилище: {e}",
        "ayah_not_found":     "❌ Аят <b>{surah}:{ayah}</b> не найден.\nПроверьте номер — возможно, в этой суре меньше аятов.",
        "ayah_error":         "⚠️ Ошибка: {e}",
        "no_reciter":         (
            "⚠️ Сначала выберите чтеца, нажав кнопку <b>«Выберите чтеца»</b>.\n"
            "Используйте /start для открытия меню."
        ),
        "bad_surah":          "⚠️ Номер суры должен быть от 1 до 114.",
        "bad_format": (
            "❓ Формат не распознан. Примеры:\n"
            "• <code>3</code> — сура целиком\n"
            "• <code>6:12</code> — конкретный аят"
        ),

        # caption шаблоны
        "surah_caption": (
            "📖 <b>Сура {number} — {arabic} ({name})</b>\n"
            "🎙 {reciter}\n"
            "{translation} · Аятов: {total}"
        ),
        "ayah_caption": (
            "📖 <b>{surah_name} {surah}:{ayah}</b>\n"
            "🎙 {reciter}\n\n"
            "<i>{translation}</i>"
        ),
    },

    "uz": {
        "choose_language":    "🌐 Выберите язык / Tilni tanlang:",
        "btn_ru":             "🇷🇺 Русский",
        "btn_uz":             "🇺🇿 O'zbek",
        "language_set":       "✅ Til o'rnatildi: O'zbek",

        "greeting": (
            "Assalomu alaykum, <b>{name}</b>! 🕌\n\n"
            "Muqaddas Qur'on eshitish botiga xush kelibsiz."
        ),
        "main_menu":          "Siz botning asosiy menyusidasiz.\nQori tanlang 👇",
        "btn_choose_reciter": "🎙 Qori tanlash",
        "btn_share":          "🔗 Ulashish",
        "inline_query_text":  "Qur'on Qorilari",

        "search_help": (
            "🟥 Ushbu qori uchun sura va oyatlar bo'yicha qidiruv mavjud.\n\n"
            "◼️ Quyidagi formatlardan birida xabar yuboring —\n\n"
            "◼️ Sura raqami bo'yicha olish:\n"
            "✔️ <code>3</code> — Qur'ondan sura olish.\n\n"
            "◼️ Qur'ondan oyat olish:\n"
            "✔️ <code>6:12</code> — birinchi raqam sura, ikkinchisi oyat"
        ),

        "loading_surah":      "⏳ Sura yuklanmoqda, kuting...",
        "loading_ayah":       "⏳ Oyat yuklanmoqda, kuting...",
        "loading_error":      "⚠️ Yuklab olishda xato: {e}",
        "upload_error":       "⚠️ Saqlashda xato: {e}",
        "ayah_not_found":     "❌ <b>{surah}:{ayah}</b> oyati topilmadi.\nShu surada buncha oyat yo'q bo'lishi mumkin.",
        "ayah_error":         "⚠️ Xato: {e}",
        "no_reciter":         (
            "⚠️ Avval <b>«Qori tanlash»</b> tugmasini bosib qori tanlang.\n"
            "Menyuni ochish uchun /start dan foydalaning."
        ),
        "bad_surah":          "⚠️ Sura raqami 1 dan 114 gacha bo'lishi kerak.",
        "bad_format": (
            "❓ Format aniqlanmadi. Misollar:\n"
            "• <code>3</code> — to'liq sura\n"
            "• <code>6:12</code> — aniq oyat"
        ),

        "surah_caption": (
            "📖 <b>Sura {number} — {arabic} ({name})</b>\n"
            "🎙 {reciter}\n"
            "{translation} · Oyatlar: {total}"
        ),
        "ayah_caption": (
            "📖 <b>{surah_name} {surah}:{ayah}</b>\n"
            "🎙 {reciter}\n\n"
            "<i>{translation}</i>"
        ),
    },
}

MAX_CAPTION = 1024

def t(lang: str, key: str, **kwargs) -> str:
    text = TEXTS.get(lang, TEXTS["ru"]).get(key, TEXTS["ru"].get(key, key))
    return text.format(**kwargs) if kwargs else text
