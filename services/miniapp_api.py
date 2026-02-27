import hashlib
import hmac
import json
import logging
from urllib.parse import parse_qsl

from aiohttp import web

from config import BOT_TOKEN
from database.db import get_db
from database.models import get_user_language, set_user_language

logger = logging.getLogger(__name__)


def _verify_init_data(init_data: str) -> dict | None:
    """Validates Telegram WebApp initData. Returns user dict or None."""
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, received_hash):
        return None

    user_json = parsed.get("user")
    if not user_json:
        return None

    try:
        return json.loads(user_json)
    except Exception:
        return None


async def handle_register(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "invalid json"}, status=400)

    init_data = body.get("initData", "")
    user = _verify_init_data(init_data)
    if not user:
        return web.json_response({"ok": False, "error": "invalid initData"}, status=403)

    user_id = user.get("id")
    if not user_id:
        return web.json_response({"ok": False, "error": "no user id"}, status=400)

    db = await get_db()
    lang = await get_user_language(db, user_id)
    is_new = lang is None

    if is_new:
        tg_lang = user.get("language_code", "")
        default_lang = "uz" if tg_lang.startswith("uz") else "ru"
        await set_user_language(db, user_id, default_lang)
        lang = default_lang
        logger.info("miniapp: registered new user %s (lang=%s)", user_id, lang)

    return web.json_response({"ok": True, "lang": lang, "is_new": is_new})


def make_app() -> web.Application:
    app = web.Application()
    app.router.add_post("/api/register", handle_register)

    async def _cors(request, handler):
        response = await handler(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    app.middlewares.append(_cors)
    return app
