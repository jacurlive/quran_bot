from dataclasses import dataclass
import aiosqlite


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


async def get_all_reciters(db: aiosqlite.Connection) -> list[Reciter]:
    async with db.execute(
        "SELECT id, identifier, name, name_ru, is_active FROM reciters WHERE is_active=1 ORDER BY id"
    ) as cur:
        rows = await cur.fetchall()
    return [Reciter(**dict(r)) for r in rows]


async def get_reciter_by_id(db: aiosqlite.Connection, reciter_id: int) -> Reciter | None:
    async with db.execute(
        "SELECT id, identifier, name, name_ru, is_active FROM reciters WHERE id=?",
        (reciter_id,),
    ) as cur:
        row = await cur.fetchone()
    return Reciter(**dict(row)) if row else None


async def get_user_reciter(db: aiosqlite.Connection, user_id: int) -> Reciter | None:
    async with db.execute(
        """
        SELECT r.id, r.identifier, r.name, r.name_ru, r.is_active
        FROM user_settings us JOIN reciters r ON r.id = us.reciter_id
        WHERE us.user_id = ?
        """,
        (user_id,),
    ) as cur:
        row = await cur.fetchone()
    return Reciter(**dict(row)) if row else None


async def set_user_reciter(db: aiosqlite.Connection, user_id: int, reciter_id: int) -> None:
    await db.execute(
        """
        INSERT INTO user_settings (user_id, reciter_id, updated_at)
        VALUES (?, ?, datetime('now'))
        ON CONFLICT(user_id) DO UPDATE SET reciter_id=excluded.reciter_id, updated_at=datetime('now')
        """,
        (user_id, reciter_id),
    )
    await db.commit()


# ---------- Language ----------

async def get_user_language(db: aiosqlite.Connection, user_id: int) -> str | None:
    """Возвращает язык пользователя или None если пользователь новый."""
    async with db.execute(
        "SELECT language FROM user_settings WHERE user_id=?", (user_id,)
    ) as cur:
        row = await cur.fetchone()
    return row["language"] if row else None


async def set_user_language(db: aiosqlite.Connection, user_id: int, language: str) -> None:
    await db.execute(
        """
        INSERT INTO user_settings (user_id, language, updated_at)
        VALUES (?, ?, datetime('now'))
        ON CONFLICT(user_id) DO UPDATE SET language=excluded.language, updated_at=datetime('now')
        """,
        (user_id, language),
    )
    await db.commit()


# ---------- Blocked ----------

async def get_all_active_user_ids(db: aiosqlite.Connection) -> list[int]:
    async with db.execute(
        "SELECT user_id FROM user_settings WHERE is_blocked = 0"
    ) as cur:
        rows = await cur.fetchall()
    return [row["user_id"] for row in rows]


async def mark_user_blocked(db: aiosqlite.Connection, user_id: int) -> None:
    await db.execute(
        "UPDATE user_settings SET is_blocked=1 WHERE user_id=?", (user_id,)
    )
    await db.commit()


# ---------- Stats ----------

async def get_stats(db: aiosqlite.Connection) -> dict:
    async with db.execute("SELECT COUNT(*) AS n FROM user_settings") as cur:
        total = (await cur.fetchone())["n"]

    async with db.execute("SELECT COUNT(*) AS n FROM user_settings WHERE is_blocked=1") as cur:
        blocked = (await cur.fetchone())["n"]

    async with db.execute(
        "SELECT language, COUNT(*) AS n FROM user_settings GROUP BY language ORDER BY n DESC"
    ) as cur:
        langs = [(row["language"], row["n"]) for row in await cur.fetchall()]

    async with db.execute("""
        SELECT r.name_ru, r.name, COUNT(*) AS n
        FROM user_settings us
        JOIN reciters r ON r.id = us.reciter_id
        WHERE us.reciter_id IS NOT NULL
        GROUP BY us.reciter_id
        ORDER BY n DESC
    """) as cur:
        reciters = [(row["name_ru"] or row["name"], row["n"]) for row in await cur.fetchall()]

    async with db.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN ayah_number IS NULL     THEN 1 ELSE 0 END) AS surahs,
            SUM(CASE WHEN ayah_number IS NOT NULL THEN 1 ELSE 0 END) AS ayahs
        FROM audio_cache
    """) as cur:
        row = await cur.fetchone()
        cache = {"total": row["total"] or 0,
                 "surahs": row["surahs"] or 0,
                 "ayahs": row["ayahs"] or 0}

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
    db: aiosqlite.Connection,
    reciter_id: str,
    surah_number: int,
    ayah_number: int | None,
) -> dict | None:
    async with db.execute(
        "SELECT file_id, caption_ru, caption_uz, title, performer FROM audio_cache "
        "WHERE reciter_id=? AND surah_number=? AND ayah_number IS ?",
        (reciter_id, surah_number, ayah_number),
    ) as cur:
        row = await cur.fetchone()
    return dict(row) if row else None


async def save_to_cache(
    db: aiosqlite.Connection,
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(reciter_id, surah_number, ayah_number) DO UPDATE SET
            file_id=excluded.file_id,
            caption_ru=excluded.caption_ru,
            caption_uz=excluded.caption_uz,
            title=excluded.title,
            performer=excluded.performer
        """,
        (reciter_id, surah_number, ayah_number, file_id, caption_ru, caption_uz, title, performer),
    )
    await db.commit()
