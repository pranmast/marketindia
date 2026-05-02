import os
import re
import telebot
import requests
from flask import Flask
from threading import Thread
from telebot import types

# --- Configuration ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
SHEET_URL = os.getenv("GOOGLE_SHEET_WEBAPP_URL")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Temporary storage (In-memory)
user_data = {}

# --- Validation ---
def is_valid_gst(gst):
    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    return re.match(pattern, gst.upper())

# --- Flask for Render ---
@app.route('/')
def index():
    return "Bot is Active", 200

# --- Telegram Logic ---

@bot.message_handler(commands=['start', 'post'])
def start_command(message):
    user_id = message.from_user.id
    user_data[user_id] = {} # Reset data for new post
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Buy 🔵", callback_data="type_Buy"),
               types.InlineKeyboardButton("Sell 🟢", callback_data="type_Sell"))
    
    bot.send_message(message.chat.id, "Welcome! Select Transaction Type:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('type_'))
def handle_type(call):
    user_id = call.from_user.id
    if user_id not in user_data: user_data[user_id] = {}
    
    user_data[user_id]['type'] = call.data.split('_')[1]
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    grades = ["W180", "W210", "W240", "W320", "W450", "LWP"]
    btns = [types.InlineKeyboardButton(g, callback_data=f"grade_{g}") for g in grades]
    markup.add(*btns)
    
    bot.edit_message_text("Great. Now select the Grade:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('grade_'))
def handle_grade(call):
    user_id = call.from_user.id
    if user_id not in user_data: return
    
    user_data[user_id]['grade'] = call.data.split('_')[1]
    user_data[user_id]['step'] = 'quantity' # Track the step manually
    
    bot.send_message(call.message.chat.id, "🔢 Enter Quantity (in kg):")

@bot.message_handler(func=lambda message: True) # Catch-all for text inputs
def handle_text_inputs(message):
    user_id = message.from_user.id
    if user_id not in user_data or 'step' not in user_data[user_id]:
        return # Ignore random messages

    step = user_data[user_id]['step']
    text = message.text

    if step == 'quantity':
        if not text.isdigit():
            bot.reply_to(message, "❌ Numbers only. Enter Quantity:")
            return
        user_data[user_id]['qty'] = text
        user_data[user_id]['step'] = 'pincode'
        bot.send_message(message.chat.id, "📍 Enter 6-digit Pincode:")

    elif step == 'pincode':
        if not (text.isdigit() and len(text) == 6):
            bot.reply_to(message, "❌ Invalid Pincode. Enter 6 digits:")
            return
        user_data[user_id]['pincode'] = text
        user_data[user_id]['step'] = 'phone'
        bot.send_message(message.chat.id, "📞 Enter 10-digit Mobile:")

    elif step == 'phone':
        if not (text.isdigit() and len(text) == 10):
            bot.reply_to(message, "❌ Invalid! Enter 10 digits:")
            return
        user_data[user_id]['phone'] = text
        user_data[user_id]['step'] = 'gst'
        bot.send_message(message.chat.id, "🏢 Enter 15-digit GST:")

    elif step == 'gst':
        if not is_valid_gst(text):
            bot.reply_to(message, "❌ Invalid GST Format. Try again:")
            return
        
        # FINAL SUBMISSION
        data = user_data[user_id]
        payload = {
            "user": f"@{message.from_user.username or 'NoUser'}",
            "type": data['type'],
            "grade": data['grade'],
            "qty": data['qty'],
            "pincode": data['pincode'],
            "contact": data['phone'],
            "gst": text.upper()
        }

        try:
            requests.post(SHEET_URL, json=payload, timeout=10)
            bot.send_message(message.chat.id, "✅ **Live Data Posted Successfully!**")
            del user_data[user_id] # Clear session
        except:
            bot.send_message(message.chat.id, "❌ Error saving data.")

# --- Background Polling ---
def run_bot():
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
