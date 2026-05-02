import os
import telebot
import requests
from flask import Flask
from threading import Thread

# 1. Setup
TOKEN = os.getenv("TELEGRAM_TOKEN")
SHEET_URL = os.getenv("GOOGLE_SHEET_WEBAPP_URL")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def ping(): 
    return "Bot is Active", 200

@bot.message_handler(commands=['post'])
def handle_post(message):
    msg = bot.reply_to(message, "Enter details: Type, Grade, Qty, Pincode\nExample: Sell, W320, 5, 416516")
    bot.register_next_step_handler(msg, send_to_sheets)

def send_to_sheets(message):
    try:
        parts = message.text.split(',')
        payload = {
            "user": f"@{message.from_user.username}",
            "type": parts[0].strip(),
            "grade": parts[1].strip(),
            "qty": parts[2].strip(),
            "pincode": parts[3].strip()
        }
        response = requests.post(SHEET_URL, json=payload)
        bot.reply_to(message, "✅ Data saved to Sheets & Map!")
    except Exception as e:
        bot.reply_to(message, "❌ Use format: Type, Grade, Qty, Pincode")

# This starts the bot in the background when the web server starts
def run_bot():
    bot.infinity_polling() # FIXED TYPO HERE

Thread(target=run_bot).start()

if __name__ == "__main__":
    # This part is only used for local testing
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
