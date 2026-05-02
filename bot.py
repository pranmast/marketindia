import os
import telebot
import requests
from flask import Flask
from threading import Thread

# --- Config ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
SHEET_URL = os.getenv("GOOGLE_SHEET_WEBAPP_URL")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running", 200

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    instructions = (
        "Welcome to Market India! 🥥\n\n"
        "To post, send a message with details in this order (one per line):\n"
        "1. Buy or Sell\n"
        "2. Grade (e.g. W320)\n"
        "3. Quantity (kg)\n"
        "4. Pincode\n"
        "5. Phone Number\n"
        "6. GST Number"
    )
    bot.reply_to(message, instructions)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # Split the message by lines
    lines = message.text.splitlines()
    
    # Check if we have at least 6 lines of data
    if len(lines) < 6:
        bot.reply_to(message, "❌ Please provide all 6 details, each on a NEW line.")
        return

    # Map the lines to variables
    payload = {
        "user": f"@{message.from_user.username or message.from_user.first_name}",
        "type": lines[0].strip(),
        "grade": lines[1].strip(),
        "qty": lines[2].strip(),
        "pincode": lines[3].strip(),
        "contact": lines[4].strip(),
        "gst": lines[5].strip()
    }

    try:
        response = requests.post(SHEET_URL, json=payload, timeout=10)
        if response.status_code == 200:
            bot.reply_to(message, "✅ Successfully posted to Market India Sheet!")
        else:
            bot.reply_to(message, "⚠️ Failed to save. Check Google Script.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# --- Polling Logic ---
def run_bot():
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
