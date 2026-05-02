import os
import telebot
import requests
from flask import Flask
from threading import Thread

# --- Config ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
SHEET_URL = os.getenv("GOOGLE_SHEET_WEBAPP_URL")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

@app.route('/')
def home():
    return "OK", 200

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    try:
        # Simple extraction - 1 line per column
        lines = message.text.split('\n')
        payload = {
            "user": f"@{message.from_user.username or 'User'}",
            "data": message.text,
            "type": lines[0] if len(lines) > 0 else "",
            "grade": lines[1] if len(lines) > 1 else "",
            "qty": lines[2] if len(lines) > 2 else "",
            "pincode": lines[3] if len(lines) > 3 else "",
            "contact": lines[4] if len(lines) > 4 else "",
            "gst": lines[5] if len(lines) > 5 else ""
        }
        requests.post(SHEET_URL, json=payload, timeout=5)
        bot.reply_to(message, "✅ Recorded in Sheets!")
    except Exception as e:
        bot.reply_to(message, "❌ Error saving. Ensure you sent 6 lines.")

def start_bot():
    bot.remove_webhook()
    print("Bot is polling...")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)

if __name__ == "__main__":
    # Start bot in a background thread
    t = Thread(target=start_bot, daemon=True)
    t.start()
    
    # Run Flask on port 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
