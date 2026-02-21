"""
Pyrogram user-client для загрузки аудио в storage-канал.
User-сессия снимает ограничение Bot API в 50 МБ (лимит до 2 ГБ).
"""
import io
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
        # Загружаем диалоги чтобы Pyrogram закэшировал все пиры (включая storage-канал)
        async for _ in _client.get_dialogs():
            pass
    return _client


async def stop_client() -> None:
    global _client
    if _client and _client.is_connected:
        await _client.stop()
        _client = None


async def upload_audio(
    data: bytes,
    filename: str,
    title: str = "",
    performer: str = "",
) -> str:
    """
    Загружает аудио в storage-канал через user-сессию.
    Возвращает file_id загруженного сообщения.
    """
    client = await get_client()
    buf = io.BytesIO(data)
    buf.name = filename  # имя файла как оно будет в Telegram
    msg = await client.send_audio(
        chat_id=STORAGE_CHANNEL_ID,
        audio=buf,
        title=title,
        performer=performer,
    )
    return msg.audio.file_id
