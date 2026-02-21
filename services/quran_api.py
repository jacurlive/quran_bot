"""
Аудио: https://quranapi.pages.dev/api/
Русский перевод: https://api.alquran.cloud/v1 (ru.kuliev — Эльмир Кулиев)
"""
import asyncio
import aiohttp
from dataclasses import dataclass

API_BASE      = "https://quranapi.pages.dev/api"
ALQURAN_BASE  = "https://api.alquran.cloud/v1"
RU_EDITION    = "ru.kuliev"
UZ_EDITION    = "uz.sodik"


@dataclass
class SurahInfo:
    surah_number: int
    name: str
    name_arabic: str
    name_translation: str
    total_ayah: int
    audio_url: str


@dataclass
class AyahInfo:
    surah_number: int
    ayah_number: int
    surah_name: str
    arabic_text: str
    russian_text: str
    uzbek_text: str
    audio_url: str


async def _fetch(session: aiohttp.ClientSession, url: str) -> dict:
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
        resp.raise_for_status()
        return await resp.json(content_type=None)


async def _get_translation(session: aiohttp.ClientSession, surah: int, ayah: int, edition: str) -> str:
    try:
        data = await _fetch(session, f"{ALQURAN_BASE}/ayah/{surah}:{ayah}/{edition}")
        return data["data"].get("text", "")
    except Exception:
        return ""


async def get_surah(
    session: aiohttp.ClientSession,
    surah_number: int,
    reciter_id: str,
) -> SurahInfo:
    data = await _fetch(session, f"{API_BASE}/{surah_number}.json")
    audio = data["audio"][reciter_id]
    return SurahInfo(
        surah_number=surah_number,
        name=data["surahName"],
        name_arabic=data["surahNameArabic"],
        name_translation=data["surahNameTranslation"],
        total_ayah=data["totalAyah"],
        audio_url=audio["url"],
    )


async def get_ayah(
    session: aiohttp.ClientSession,
    surah_number: int,
    ayah_number: int,
    reciter_id: str,
) -> AyahInfo:
    # Запрашиваем аудио, русский и узбекский переводы параллельно
    audio_task = _fetch(session, f"{API_BASE}/{surah_number}/{ayah_number}.json")
    ru_task    = _get_translation(session, surah_number, ayah_number, RU_EDITION)
    uz_task    = _get_translation(session, surah_number, ayah_number, UZ_EDITION)
    data, russian_text, uzbek_text = await asyncio.gather(audio_task, ru_task, uz_task)

    audio = data["audio"][reciter_id]
    arabic = data.get("arabic2", data.get("arabic1", ""))
    if isinstance(arabic, list):
        arabic = arabic[ayah_number - 1] if ayah_number <= len(arabic) else ""

    return AyahInfo(
        surah_number=surah_number,
        ayah_number=ayah_number,
        surah_name=data["surahName"],
        arabic_text=arabic,
        russian_text=russian_text,
        uzbek_text=uzbek_text,
        audio_url=audio["url"],
    )
