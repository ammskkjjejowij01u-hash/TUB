# main2.py
import asyncio
import logging
import os
import shutil
import tempfile
import threading
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession

load_dotenv()

# =========================
# Config
# =========================
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
STRING_SESSION = os.getenv("STRING_SESSION")
PIXELDRAIN_API_KEY = os.getenv("PIXELDRAIN_API_KEY")
PORT = int(os.getenv("PORT", "8000"))

if not API_ID or not API_HASH or not STRING_SESSION:
    raise ValueError("❌ متغیرهای API_ID, API_HASH و STRING_SESSION باید داخل .env تنظیم شوند.")

API_ID = int(API_ID)

# =========================
# Logging
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)
logger = logging.getLogger("ftl-userbot")

# =========================
# Flask
# =========================
app = Flask(__name__)

@app.get("/")
def home():
    return "🚀 یوزربات فایل به لینک (Catbox + Pixeldrain) در حال اجراست!"

@app.get("/health")
def health():
    return {"ok": True}

# =========================
# Telegram Client
# =========================
client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

# =========================
# Helpers
# =========================
def safe_filename(msg, fallback: str = "file.bin") -> str:
    try:
        if msg and msg.file and msg.file.name:
            return Path(msg.file.name).name
    except Exception:
        pass
    return Path(fallback).name


def safe_size_kb(msg) -> int:
    try:
        if msg and msg.file and msg.file.size:
            return max(1, int(msg.file.size) // 1024)
    except Exception:
        pass
    return 1


def response_error_text(resp: requests.Response) -> str:
    try:
        payload = resp.json()
        if isinstance(payload, dict):
            return payload.get("message") or payload.get("value") or str(payload)
        return str(payload)
    except Exception:
        text = (resp.text or "").strip()
        return text if text else f"HTTP {resp.status_code}"


def upload_to_catbox(file_path: str) -> dict | None:
    """
    Catbox upload API.
    خروجی: {"viewer": link, "direct": link}
    """
    url = "https://catbox.moe/user/api.php"

    try:
        with open(file_path, "rb") as f:
            resp = requests.post(
                url,
                files={"fileToUpload": f},
                data={"reqtype": "fileupload"},
                timeout=180,
            )

        link = (resp.text or "").strip()
        if resp.ok and link and not link.lower().startswith("error"):
            return {"viewer": link, "direct": link}

        logger.error("Catbox upload failed: %s", response_error_text(resp))
        return None

    except Exception as e:
        logger.exception("Catbox error: %s", e)
        return None


def upload_to_pixeldrain(file_path: str) -> dict | None:
    """
    Pixeldrain upload API.
    نیاز به API key دارد.
    Docs: PUT /file/{name}
    خروجی:
      {
        "viewer": "https://pixeldrain.com/u/<id>",
        "direct": "https://pixeldrain.com/api/file/<id>?download"
      }
    """
    if not PIXELDRAIN_API_KEY:
        logger.error("PIXELDRAIN_API_KEY is missing")
        return None

    filename = safe_filename(None, Path(file_path).name)
    encoded_name = quote(filename, safe="")
    url = f"https://pixeldrain.com/api/file/{encoded_name}"

    try:
        with open(file_path, "rb") as f:
            resp = requests.put(
                url,
                auth=("", PIXELDRAIN_API_KEY),
                data=f,
                headers={"Content-Type": "application/octet-stream"},
                timeout=600,
            )

        if resp.status_code not in (200, 201):
            logger.error("Pixeldrain upload failed: %s", response_error_text(resp))
            return None

        payload = resp.json()
        file_id = payload.get("id")
        if not file_id:
            logger.error("Pixeldrain response missing file id: %s", payload)
            return None

        return {
            "viewer": f"https://pixeldrain.com/u/{file_id}",
            "direct": f"https://pixeldrain.com/api/file/{file_id}?download",
        }

    except Exception as e:
        logger.exception("Pixeldrain error: %s", e)
        return None


async def _handle_upload(event, service_name: str, uploader_func):
    if not event.is_reply:
        await event.edit("❌ لطفاً روی یک فایل ریپلای کن.")
        return

    reply_msg = await event.get_reply_message()
    if not reply_msg or not reply_msg.file:
        await event.edit("❌ پیام ریپلای‌شده فایل ندارد.")
        return

    temp_dir = tempfile.mkdtemp(prefix="ftl_")

    try:
        await event.edit(f"⏳ در حال دانلود و آپلود به {service_name} ...")

        downloaded_path = await reply_msg.download_media(file=temp_dir)
        if not downloaded_path:
            await event.edit("❌ دانلود فایل از تلگرام ناموفق بود.")
            return

        downloaded_path = str(downloaded_path)
        result = await asyncio.to_thread(uploader_func, downloaded_path)

        if not result:
            await event.edit(f"❌ آپلود به {service_name} ناموفق بود.")
            return

        name = safe_filename(reply_msg, downloaded_path)
        size_kb = safe_size_kb(reply_msg)

        msg_lines = [
            "✅ آپلود موفق",
            "",
            f"فایل: {name}",
            f"حجم: {size_kb} KB",
            "",
            "لینک دانلود:",
            result["direct"],
        ]

        if result.get("viewer") and result["viewer"] != result["direct"]:
            msg_lines += ["", "صفحه فایل:", result["viewer"]]

        msg_lines += ["", f"سرویس: {service_name}"]

        await event.edit("\n".join(msg_lines))

    except Exception as e:
        logger.exception("Upload handler failed: %s", e)
        await event.edit("❌ خطای غیرمنتظره رخ داد.")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

# =========================
# Commands
# =========================
@client.on(events.NewMessage(pattern=r"^\.up1$", outgoing=True))
async def up1_handler(event):
    await _handle_upload(event, "Catbox", upload_to_catbox)


@client.on(events.NewMessage(pattern=r"^\.up2$", outgoing=True))
async def up2_handler(event):
    await _handle_upload(event, "Pixeldrain", upload_to_pixeldrain)

# =========================
# Main
# =========================
def run_flask():
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)


async def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("✅ Flask running on port %s", PORT)

    await client.start()
    me = await client.get_me()
    username = f"@{me.username}" if me.username else "(no username)"
    logger.info("✅ وارد شدید به عنوان: %s %s", me.first_name, username)

    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
