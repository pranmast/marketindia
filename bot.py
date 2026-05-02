import os
import telebot
import requests
from flask import Flask
from threading import Thread

# --- Configuration ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
SHEET_URL = os.getenv("GOOGLE_SHEET_WEBAPP_URL")

# Use threaded=False for better stability on Render
bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is Running", 200

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Split the message into lines exactly as seen in your screenshot
    lines = message.text.split('\n')
    
    # We expect 6 lines. If less, we'll fill with "None"
    data_payload = {
        "user": f"@{message.from_user.username or 'User'}",
        "type": lines[0].strip() if len(lines) > 0 else "",
        "grade": lines[1].strip() if len(lines) > 1 else "",
        "qty": lines[2].strip() if len(lines) > 2 else "",
        "pincode": lines[3].strip() if len(lines) > 3 else "",
        "contact": lines[4].strip() if len(lines) > 4 else "",
        "gst": lines[5].strip() if len(lines) > 5 else ""
    }

    try:
        # Send data to Google Apps Script
        response = requests.post(SHEET_URL, json=data_payload, timeout=10)
        if response.status_code == 200:
            bot.reply_to(message, "✅ Data added to Sheet!")
        else:
            bot.reply_to(message, "⚠️ Script error. Check Google Script Deployment.")
    except Exception as e:
        bot.reply_to(message, "❌ Connection Error. Check Render Environment Variables.")

def run_bot():
    # Crucial: Remove any old connection first
    bot.remove_webhook()
    bot.infinity_polling(timeout=60, long_polling_timeout=30)

if __name__ == "__main__":
    # Start bot in background
    t = Thread(target=run_bot, daemon=True)
    t.start()
    
    # Run Flask for Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
