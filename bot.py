import os
import telebot
import requests  # To send data to Google Sheets
from flask import Flask

# 1. Setup
TOKEN = os.getenv("TELEGRAM_TOKEN")
SHEET_URL = os.getenv("GOOGLE_SHEET_WEBAPP_URL") # Your Apps Script URL

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def ping(): return "Bot is Active", 200

@bot.message_handler(commands=['post'])
def handle_post(message):
    msg = bot.reply_to(message, "Enter details: Type, Grade, Qty, Pincode\nExample: Sell, W320, 5, 416516")
    bot.register_next_step_handler(msg, send_to_sheets)

def send_to_sheets(message):
    try:
        # Split user input
        parts = message.text.split(',')
        payload = {
            "user": f"@{message.from_user.username}",
            "type": parts[0].strip(),
            "grade": parts[1].strip(),
            "qty": parts[2].strip(),
            "pincode": parts[3].strip()
        }
        
        # Send to Google Sheet Webhook
        response = requests.post(SHEET_URL, json=payload)
        
        if response.status_code == 200:
            bot.reply_to(message, "✅ Data saved to Google Sheets & Map!")
        else:
            bot.reply_to(message, "❌ Sheet Error.")
            
    except Exception as e:
        bot.reply_to(message, "❌ Use format: Type, Grade, Qty, Pincode")

if __name__ == "__main__":
    from threading import Thread
    # Corrected name: infinity_polling
    Thread(target=bot.infinity_polling, daemon=True).start()
    
    # Render needs this Flask app to stay alive
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
