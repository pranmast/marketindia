import os
import telebot
import requests
from flask import Flask
from threading import Thread

# --- Essential Config ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
SHEET_URL = os.getenv("GOOGLE_SHEET_WEBAPP_URL")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def health_check():
    return "OK", 200

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # This is the EXACT logic that worked for you originally
    payload = {"data": message.text, "user": message.from_user.username}
    try:
        requests.post(SHEET_URL, json=payload, timeout=5)
        bot.reply_to(message, "✅ Received and sent to sheet.")
    except:
        bot.reply_to(message, "❌ Failed to connect to sheet.")

def run_polling():
    bot.remove_webhook()
    bot.infinity_polling()

if __name__ == "__main__":
    # Standard threading for Render
    t = Thread(target=run_polling, daemon=True)
    t.start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
