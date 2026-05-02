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

# Temporary storage for user input
user_data = {}

# --- Helper Functions & Validation ---
def is_valid_gst(gst):
    # Regex for Indian GST format (15 characters)
    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    return re.match(pattern, gst.upper())

def is_valid_phone(phone):
    return phone.isdigit() and len(phone) == 10

# --- Flask Routes (For Render Health Checks) ---
@app.route('/')
def index():
    return "Bot is running...", 200

# --- Telegram Bot Logic ---

@bot.message_handler(commands=['start', 'post'])
def start_post(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_buy = types.InlineKeyboardButton("Buy 🔵", callback_data="type_Buy")
    btn_sell = types.InlineKeyboardButton("Sell 🟢", callback_data="type_Sell")
    markup.add(btn_buy, btn_sell)
    
    bot.send_message(message.chat.id, "Welcome to Market India. \nSelect Transaction Type:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('type_'))
def get_type(call):
    user_id = call.from_user.id
    user_data[user_id] = {'type': call.data.split('_')[1]}
    
    # Show Grade Options
    markup = types.InlineKeyboardMarkup(row_width=3)
    grades = ["W180", "W210", "W240", "W320", "W450", "LWP"]
    btns = [types.InlineKeyboardButton(g, callback_data=f"grade_{g}") for g in grades]
    markup.add(*btns)
    
    bot.edit_message_text("Select Grade:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('grade_'))
def get_grade(call):
    user_id = call.from_user.id
    user_data[user_id]['grade'] = call.data.split('_')[1]
    
    msg = bot.send_message(call.message.chat.id, "🔢 Enter Quantity (in kg):")
    bot.register_next_step_handler(msg, get_quantity)

def get_quantity(message):
    user_id = message.from_user.id
    if not message.text.isdigit():
        msg = bot.reply_to(message, "❌ Numbers only please. Enter Quantity:")
        bot.register_next_step_handler(msg, get_quantity)
        return
    
    user_data[user_id]['qty'] = message.text
    msg = bot.send_message(message.chat.id, "📍 Enter 6-digit Pincode:")
    bot.register_next_step_handler(msg, get_pincode)

def get_pincode(message):
    user_id = message.from_user.id
    if not (message.text.isdigit() and len(message.text) == 6):
        msg = bot.reply_to(message, "❌ Invalid Pincode! Enter 6 digits:")
        bot.register_next_step_handler(msg, get_pincode)
        return
    
    user_data[user_id]['pincode'] = message.text
    msg = bot.send_message(message.chat.id, "📞 Enter 10-digit Mobile Number:")
    bot.register_next_step_handler(msg, get_phone)

def get_phone(message):
    user_id = message.from_user.id
    if not is_valid_phone(message.text):
        msg = bot.reply_to(message, "❌ Invalid! Enter a 10-digit number:")
        bot.register_next_step_handler(msg, get_phone)
        return
    
    user_data[user_id]['phone'] = message.text
    msg = bot.send_message(message.chat.id, "🏢 Enter 15-digit GST Number:")
    bot.register_next_step_handler(msg, get_gst)

def get_gst(message):
    user_id = message.from_user.id
    gst_val = message.text.upper()
    
    if not is_valid_gst(gst_val):
        msg = bot.reply_to(message, "❌ Invalid GST Format! Example: 27AAAAA0000A1Z5\nEnter GST again:")
        bot.register_next_step_handler(msg, get_gst)
        return

    data = user_data[user_id]
    
    # Final Payload for Google Sheets
    payload = {
        "user": f"@{message.from_user.username or message.from_user.first_name}",
        "type": data['type'],
        "grade": data['grade'],
        "qty": data['qty'],
        "pincode": data['pincode'],
        "contact": data['phone'],
        "gst": gst_val
    }

    # Send to Google Sheets Web App
    try:
        response = requests.post(SHEET_URL, json=payload, timeout=10)
        if response.status_code == 200:
            summary = (f"✅ **Post Successful!**\n\n"
                       f"🔹 Type: {data['type']}\n"
                       f"🔹 Grade: {data['grade']}\n"
                       f"🔹 Qty: {data['qty']} kg\n"
                       f"🔹 Pin: {data['pincode']}\n"
                       f"🔹 Call: {data['phone']}\n"
                       f"🔹 GST: {gst_val}")
            bot.send_message(message.chat.id, summary, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "⚠️ Sheet Error: Script didn't accept data.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Connection Error: {str(e)}")

# --- Threading & Execution ---

def run_bot():
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    # Start bot thread
    bot_thread = Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start Flask server
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
