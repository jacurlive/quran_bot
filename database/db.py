import aiosqlite
from config import DB_PATH

_db: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        _db = await aiosqlite.connect(DB_PATH)
        _db.row_factory = aiosqlite.Row
    return _db


async def close_db() -> None:
    global _db
    if _db:
        await _db.close()
        _db = None


async def init_db() -> None:
    db = await get_db()
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS reciters (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            identifier  TEXT UNIQUE NOT NULL,
            name        TEXT NOT NULL,
            name_ru     TEXT,
            is_active   INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS user_settings (
            user_id     INTEGER PRIMARY KEY,
            reciter_id  INTEGER REFERENCES reciters(id),
            language    TEXT DEFAULT 'ru',
            updated_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS audio_cache (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            reciter_id      TEXT NOT NULL,
            surah_number    INTEGER NOT NULL,
            ayah_number     INTEGER,
            file_id         TEXT NOT NULL,
            caption_ru      TEXT,
            caption_uz      TEXT,
            title           TEXT,
            performer       TEXT,
            created_at      TEXT DEFAULT (datetime('now')),
            UNIQUE(reciter_id, surah_number, ayah_number)
        );

        INSERT OR IGNORE INTO reciters (identifier, name, name_ru) VALUES
            ('1', 'Mishary Rashid Al Afasy',   'Мишари Рашид Аль-Афаси'),
            ('2', 'Abu Bakr Al Shatri',        'Абу Бакр Аш-Шатри'),
            ('3', 'Nasser Al Qatami',          'Насер Аль-Катами'),
            ('4', 'Yasser Al Dosari',          'Ясир Аль-Досари'),
            ('5', 'Hani Ar Rifai',             'Хани Ар-Рифаи');
    """)
    await db.commit()

    # migrations
    try:
        await db.execute("ALTER TABLE user_settings ADD COLUMN is_blocked INTEGER DEFAULT 0")
        await db.commit()
    except Exception:
        pass  # column already exists
