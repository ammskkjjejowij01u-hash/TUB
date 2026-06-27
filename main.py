from telethon import TelegramClient, events
from flask import Flask
import threading

api_id = 33765228
api_hash = "d2767c387914ee3b344f2c1367e69a1f"
string_session = "1BJWap1sBu199Ig5LND4HD5rCrLWoq8j3KSNfLa2WnuO4yLU7gx6RvjwBb_6a3ewdokiirIqdLz9Ulohe2cHmTAo1FwVD3ArAPrQ7629zY9cia2Erd865VdY1C-sm219bludLAHuwrnmEo0FcHdtHX1RjY779UpHUq13RfnUwvwu9aP2d4L-gDn566wuJw79ztbglp7WD8hNRIFl1G655lmfoD3Il28EeOK64ZCpi5dmR2WJhGvsGqYWykWpY3Mc-4-jpdMFoxsEe5pH_kFlRV2e9TotMatboxaZoXeRC20_csFDNM25h9kEPAmZz-nbvhUYBRIQKFuP_LpQaO4THqELAfAR-0Eg="

client = TelegramClient(string_session, api_id, api_hash)

# ---------------- Flask fake server ----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Userbot is alive"

@app.route("/health")
def health():
    return {"status": "ok"}

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# ---------------- Telegram userbot ----------------
@client.on(events.NewMessage)
async def handler(event):
    text = event.raw_text

    if text == ".سلام":
        await event.reply("سلام 👋")

# ---------------- Start ----------------
def main():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    client.start()
    print("Userbot is running...")
    client.run_until_disconnected()

if __name__ == "__main__":
    main()
