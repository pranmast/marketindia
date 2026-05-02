import os
import telebot
import requests
from flask import Flask
from threading import Thread

# --- Configuration ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
SHEET_URL = os.getenv("GOOGLE_SHEET_WEBAPP_URL")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Flask health check for Render
@app.route('/')
def index():
    return "Bot is Active", 200

# Original Simple Logic
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "Send your post in this format (one per line):\n\nBuy/Sell\nGrade\nQuantity\nPincode\nContact\nGST")

@bot.message_handler(func=lambda message: True)
def process_post(message):
    # Split text into lines
    lines = message.text.split('\n')
    
    # We need at least 6 pieces of info
    if len(lines) < 6:
        bot.reply_to(message, "❌ Please provide 6 lines:\n1. Type\n2. Grade\n3. Qty\n4. Pin\n5. Phone\n6. GST")
        return

    # Map directly to your Sheet structure
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
        # Send to Google Script
        requests.post(SHEET_URL, json=payload, timeout=10)
        bot.reply_to(message, "✅ Data sent to Sheet!")
    except Exception as e:
        bot.reply_to(message, "❌ Sheet Error. Check script URL.")

# --- The "Anti-Crash" Polling ---
def run_bot():
    bot.remove_webhook()
    print("Bot started polling...")
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    # Start bot thread
    t = Thread(target=run_bot)
    t.daemon = True
    t.start()
    
    # Run Flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
