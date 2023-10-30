import os
from flask import Flask, request
import telebot

# Your Telegram bot token
TOKEN = os.environ['5938139823:AAF8SwXNeL9xQB_niIYODUMZWXJh9cWU3_0']
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# Set up a simple webhook route
@app.route(f'/{TOKEN}', methods=['POST'])
def process_update():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

# Define your command handlers as before
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    # Your command handler code

@bot.message_handler(commands=['generate'])
def generate_lottery_numbers(message):
    # Your command handler code

@bot.message_handler(commands=['reset'])
def reset_bot(message):
    # Your command handler code

@bot.message_handler(commands=['list'])
def list_lottery_numbers(message):
    # Your command handler code

@bot.message_handler(commands=['winner'])
def select_winner(message):
    # Your command handler code

@bot.message_handler(commands=['adduser'])
def add_user_authorization(message):
    # Your command handler code

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000))
