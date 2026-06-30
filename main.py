# main.py
import os
import asyncio
import threading
import requests
import logging
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ========== تنظیمات از متغیرهای محیطی ==========
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
STRING_SESSION = os.getenv("STRING_SESSION")
PORT = int(os.getenv("PORT", 8000))  # ← مقدار پیش‌فرض ۸۰۰۰

# ========== Flask Server ==========
app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 یوزربات فایل به لینک در حال اجراست!"

# ========== اتصال به تلگرام ==========
client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== تابع آپلود به File.io ==========
def upload_to_fileio(file_path: str) -> str:
    try:
        with open(file_path, 'rb') as f:
            response = requests.post('https://file.io/', files={'file': f})
        if response.status_code == 200:
            data = response.json()
            return data.get('link')
        return None
    except Exception as e:
        logger.error(f"خطا در آپلود: {e}")
        return None

# ========== هندلر .upload ==========
@client.on(events.NewMessage(pattern=r'^\.upload$', outgoing=True))
async def upload_handler(event):
    if not event.is_reply:
        await event.edit("❌ لطفاً روی یک فایل ریپلای کنید.")
        return
    
    reply_msg = await event.get_reply_message()
    if not reply_msg.file:
        await event.edit("❌ پیام ریپلای‌شده حاوی فایل نیست!")
        return
    
    status_msg = await event.edit("📤 در حال آپلود...")
    
    try:
        file_path = await reply_msg.download_media()
        if not file_path:
            await status_msg.edit("❌ خطا در دانلود فایل!")
            return
        
        link = upload_to_fileio(file_path)
        os.remove(file_path)
        
        if link:
            await status_msg.edit(
                f"✅ **فایل آپلود شد!**\n\n"
                f"📁 نام: `{reply_msg.file.name}`\n"
                f"📦 حجم: `{reply_msg.file.size // 1024} KB`\n"
                f"🔗 لینک:\n{link}\n\n"
                f"⚠️ این لینک فقط **یک بار** قابل استفاده است."
            )
        else:
            await status_msg.edit("❌ خطا در آپلود!")
    except Exception as e:
        logger.error(f"خطا: {e}")
        await status_msg.edit("❌ خطایی رخ داد!")

# ========== اجرای Flask ==========
def run_flask():
    app.run(host='0.0.0.0', port=PORT, debug=False)

# ========== اجرای یوزربات ==========
async def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info(f"✅ Flask running on port {PORT}")
    
    await client.start()
    me = await client.get_me()
    logger.info(f"✅ وارد شدید به عنوان: {me.first_name} (@{me.username})")
    
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
