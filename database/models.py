from dataclasses import dataclass
import asyncpg


@dataclass
class Reciter:
    id: int
    identifier: str
    name: str
    name_ru: str | None
    is_active: int

    @property
    def display_name(self) -> str:
        return self.name_ru or self.name


# ---------- Reciters ----------

async def get_all_reciters(db: asyncpg.Pool) -> list[Reciter]:
    rows = await db.fetch(
        "SELECT id, identifier, name, name_ru, is_active FROM reciters WHERE is_active=1 ORDER BY id"
    )
    return [Reciter(**dict(r)) for r in rows]


async def get_reciter_by_id(db: asyncpg.Pool, reciter_id: int) -> Reciter | None:
    row = await db.fetchrow(
        "SELECT id, identifier, name, name_ru, is_active FROM reciters WHERE id=$1",
        reciter_id,
    )
    return Reciter(**dict(row)) if row else None


async def get_user_reciter(db: asyncpg.Pool, user_id: int) -> Reciter | None:
    row = await db.fetchrow(
        """
        SELECT r.id, r.identifier, r.name, r.name_ru, r.is_active
        FROM user_settings us JOIN reciters r ON r.id = us.reciter_id
        WHERE us.user_id = $1
        """,
        user_id,
    )
    return Reciter(**dict(row)) if row else None


async def set_user_reciter(db: asyncpg.Pool, user_id: int, reciter_id: int) -> None:
    await db.execute(
        """
        INSERT INTO user_settings (user_id, reciter_id, updated_at)
        VALUES ($1, $2, NOW())
        ON CONFLICT (user_id) DO UPDATE SET reciter_id = EXCLUDED.reciter_id, updated_at = NOW()
        """,
        user_id, reciter_id,
    )


# ---------- Language ----------

async def get_user_language(db: asyncpg.Pool, user_id: int) -> str | None:
    return await db.fetchval(
        "SELECT language FROM user_settings WHERE user_id=$1", user_id
    )


async def set_user_language(db: asyncpg.Pool, user_id: int, language: str) -> None:
    await db.execute(
        """
        INSERT INTO user_settings (user_id, language, updated_at)
        VALUES ($1, $2, NOW())
        ON CONFLICT (user_id) DO UPDATE SET language = EXCLUDED.language, updated_at = NOW()
        """,
        user_id, language,
    )


# ---------- Blocked ----------

async def get_all_active_user_ids(db: asyncpg.Pool) -> list[int]:
    rows = await db.fetch("SELECT user_id FROM user_settings WHERE is_blocked = 0")
    return [row["user_id"] for row in rows]


async def mark_user_blocked(db: asyncpg.Pool, user_id: int) -> None:
    await db.execute(
        "UPDATE user_settings SET is_blocked=1 WHERE user_id=$1", user_id
    )


# ---------- Stats ----------

async def get_stats(db: asyncpg.Pool) -> dict:
    total   = await db.fetchval("SELECT COUNT(*) FROM user_settings")
    blocked = await db.fetchval("SELECT COUNT(*) FROM user_settings WHERE is_blocked=1")

    langs = [
        (r["language"], r["n"])
        for r in await db.fetch(
            "SELECT language, COUNT(*) AS n FROM user_settings GROUP BY language ORDER BY n DESC"
        )
    ]

    reciters = [
        (r["name_ru"] or r["name"], r["n"])
        for r in await db.fetch("""
            SELECT r.name_ru, r.name, COUNT(*) AS n
            FROM user_settings us
            JOIN reciters r ON r.id = us.reciter_id
            WHERE us.reciter_id IS NOT NULL
            GROUP BY us.reciter_id, r.name_ru, r.name
            ORDER BY n DESC
        """)
    ]

    row = await db.fetchrow("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN ayah_number IS NULL     THEN 1 ELSE 0 END) AS surahs,
            SUM(CASE WHEN ayah_number IS NOT NULL THEN 1 ELSE 0 END) AS ayahs
        FROM audio_cache
    """)
    cache = {
        "total":  row["total"]  or 0,
        "surahs": row["surahs"] or 0,
        "ayahs":  row["ayahs"]  or 0,
    }

    return {
        "total":    total,
        "blocked":  blocked,
        "active":   total - blocked,
        "langs":    langs,
        "reciters": reciters,
        "cache":    cache,
    }


# ---------- Audio cache ----------

async def get_cached(
    db: asyncpg.Pool,
    reciter_id: str,
    surah_number: int,
    ayah_number: int | None,
) -> dict | None:
    row = await db.fetchrow(
        "SELECT file_id, caption_ru, caption_uz, title, performer FROM audio_cache "
        "WHERE reciter_id=$1 AND surah_number=$2 AND ayah_number IS NOT DISTINCT FROM $3",
        reciter_id, surah_number, ayah_number,
    )
    return dict(row) if row else None


async def save_to_cache(
    db: asyncpg.Pool,
    reciter_id: str,
    surah_number: int,
    ayah_number: int | None,
    file_id: str,
    caption_ru: str,
    caption_uz: str,
    title: str,
    performer: str,
) -> None:
    await db.execute(
        """
        INSERT INTO audio_cache
            (reciter_id, surah_number, ayah_number, file_id, caption_ru, caption_uz, title, performer)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (reciter_id, surah_number, ayah_number) DO UPDATE SET
            file_id    = EXCLUDED.file_id,
            caption_ru = EXCLUDED.caption_ru,
            caption_uz = EXCLUDED.caption_uz,
            title      = EXCLUDED.title,
            performer  = EXCLUDED.performer
        """,
        reciter_id, surah_number, ayah_number,
        file_id, caption_ru, caption_uz, title, performer,
    )
