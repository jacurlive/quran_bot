import asyncpg
from config import DATABASE_URL

_pool: asyncpg.Pool | None = None


async def get_db() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    return _pool


async def close_db() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def init_db() -> None:
    pool = await get_db()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS reciters (
                id          SERIAL PRIMARY KEY,
                identifier  TEXT UNIQUE NOT NULL,
                name        TEXT NOT NULL,
                name_ru     TEXT,
                is_active   INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS user_settings (
                user_id     BIGINT PRIMARY KEY,
                reciter_id  INTEGER REFERENCES reciters(id),
                language    TEXT DEFAULT 'ru',
                is_blocked  INTEGER DEFAULT 0,
                updated_at  TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS audio_cache (
                id              SERIAL PRIMARY KEY,
                reciter_id      TEXT NOT NULL,
                surah_number    INTEGER NOT NULL,
                ayah_number     INTEGER,
                file_id         TEXT NOT NULL,
                caption_ru      TEXT,
                caption_uz      TEXT,
                title           TEXT,
                performer       TEXT,
                created_at      TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE NULLS NOT DISTINCT (reciter_id, surah_number, ayah_number)
            );

            INSERT INTO reciters (identifier, name, name_ru) VALUES
                ('1', 'Mishary Rashid Al Afasy',   'Мишари Рашид Аль-Афаси'),
                ('2', 'Abu Bakr Al Shatri',        'Абу Бакр Аш-Шатри'),
                ('3', 'Nasser Al Qatami',          'Насер Аль-Катами'),
                ('4', 'Yasser Al Dosari',          'Ясир Аль-Досари'),
                ('5', 'Hani Ar Rifai',             'Хани Ар-Рифаи')
            ON CONFLICT (identifier) DO NOTHING;
        """)
