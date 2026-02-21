import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
DB_PATH: str = os.getenv("DB_PATH", "quran_bot.db")

API_ID: int = int(os.environ["API_ID"])
API_HASH: str = os.environ["API_HASH"]
PHONE: str = os.environ["PHONE"]
STORAGE_CHANNEL_ID: int = int(os.environ["STORAGE_CHANNEL_ID"])
ADMIN_ID: int = int(os.environ["ADMIN_ID"])

QURAN_API_BASE = "https://quranapi.pages.dev/api"
