import os
import threading
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ================== FLASK ==================
app = Flask(__name__)

@app.route("/")
def home():
    return "Userbot is alive 👌"

@app.route("/health")
def health():
    return {"status": "ok"}

def run_flask():
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

# ================== TELEGRAM USERBOT ==================
api_id = int(os.environ["api_id"])
api_hash = os.environ["api_hash"]
string_session = os.environ["string_session"]

client = TelegramClient(
    StringSession(string_session),
    api_id,
    api_hash
)

@client.on(events.NewMessage)
async def handler(event):
    text = event.raw_text

    if text == ".سلام":
        await event.reply("سلام 👋")

    elif text == ".ping":
        await event.reply("pong 🏓")

    elif text == ".id":
        await event.reply(str(event.chat_id))

    elif text == ".help":
        await event.reply(".سلام\n.ping\n.id\n.help")

# ================== START ==================
def main():
    print("🚀 Starting Flask + Telegram Userbot...")

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    client.start()
    client.run_until_disconnected()

if __name__ == "__main__":
    main()
