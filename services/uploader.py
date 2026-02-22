"""
Pyrogram user-client для загрузки аудио в storage-канал.
User-сессия снимает ограничение Bot API в 50 МБ (лимит до 2 ГБ).
Файлы скачиваются стримингом на диск — не грузят RAM.
"""
import os
import tempfile
import aiohttp
from pyrogram import Client
from config import API_ID, API_HASH, PHONE, STORAGE_CHANNEL_ID

_client: Client | None = None


async def get_client() -> Client:
    global _client
    if _client is None:
        _client = Client(
            name="quran_user",
            api_id=API_ID,
            api_hash=API_HASH,
            phone_number=PHONE,
        )
        await _client.start()
        async for _ in _client.get_dialogs():
            pass
    return _client


async def stop_client() -> None:
    global _client
    if _client and _client.is_connected:
        await _client.stop()
        _client = None


async def download_to_tempfile(url: str) -> str:
    """Скачивает URL чанками (1 МБ) во временный файл. Возвращает путь."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=300)) as resp:
                resp.raise_for_status()
                async for chunk in resp.content.iter_chunked(1024 * 1024):
                    tmp.write(chunk)
    finally:
        tmp.close()
    return tmp.name


async def upload_audio(
    filepath: str,
    filename: str,
    title: str = "",
    performer: str = "",
) -> str:
    """
    Загружает аудио из файла на диске в storage-канал через user-сессию.
    Возвращает file_id загруженного сообщения.
    """
    client = await get_client()
    try:
        msg = await client.send_audio(
            chat_id=STORAGE_CHANNEL_ID,
            audio=filepath,
            file_name=filename,
            title=title,
            performer=performer,
        )
    finally:
        os.unlink(filepath)  # удаляем temp файл после загрузки
    return msg.audio.file_id
