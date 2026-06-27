import os
from telethon import TelegramClient, events

api_id = int(os.environ["api_id"])
api_hash = os.environ["api_hash"]
string_session = os.environ["string_session"]

client = TelegramClient(string_session, api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    text = event.raw_text

    if text == ".سلام":
        await event.reply("سلام 👋")

    if text == ".ping":
        await event.reply("pong 🏓")

    if text == ".id":
        await event.reply(str(event.chat_id))


print("Userbot running...")
client.start()
client.run_until_disconnected()
