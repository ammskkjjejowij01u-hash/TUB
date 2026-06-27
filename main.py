from flask import Flask
import threading
from telethon import TelegramClient, events
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "OK"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

api_id = int(os.environ["api_id"])
api_hash = os.environ["api_hash"]
string_session = os.environ["string_session"]

client = TelegramClient(string_session, api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    if event.raw_text == ".سلام":
        await event.reply("سلام 👋")

def main():
    threading.Thread(target=run).start()
    client.start()
    client.run_until_disconnected()

main()
