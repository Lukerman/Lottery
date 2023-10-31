import telebot
from telebot import types
import random
import string
from pymongo import MongoClient

# Replace 'YOUR_BOT_TOKEN' with your actual Telegram bot token
TOKEN = '5938139823:AAF8SwXNeL9xQB_niIYODUMZWXJh9cWU3_0'
bot = telebot.TeleBot(TOKEN)

# Replace 'YOUR_CHANNEL_ID' with the ID of your Telegram channel
CHANNEL_ID = -1001783918221  # Replace with your channel ID

# Replace 'OWNER_USER_ID' with the user ID of the owner
OWNER_USER_ID = 1778070005  # Replace with the owner's user ID

# Define a list of allowed user IDs who can generate lottery numbers
allowed_user_ids = [1778070005, 987654321]  # Replace with your allowed user IDs

# Set up MongoDB connection
# Replace 'YOUR_CONNECTION_STRING' with your MongoDB Atlas connection string
connection_string = "mongodb+srv://sujithasatheesan8:ZoA8Pqr0jOaC314V@cluster0.54frnzg.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(connection_string)

# Access your database and collection
db = client["cluster0"]
collection = db["your_collection_name"]

# Initialize dictionaries to store user data
user_mobile_numbers = {}
user_lottery_status = {}
lottery_tickets = []

# Load user data and lottery tickets from MongoDB on bot startup
for document in collection.find():
    user_id = document["user_id"]
    mobile_number = document["mobile_number"]
    ticket = document["ticket"]
    user_mobile_numbers[user_id] = mobile_number
    user_lottery_status[user_id] = True
    lottery_tickets.append((user_id, mobile_number, ticket))

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id in user_mobile_numbers:
        bot.reply_to(message, "Welcome to the Lottery Number Generator Bot! Send /generate to get your lottery number (one per user).")
    else:
        bot.reply_to(message, "To get started, please send your mobile number to register.")
        bot.register_next_step_handler(message, process_mobile_number)

def process_mobile_number(message):
    user_id = message.from_user.id
    mobile_number = message.text

    if not mobile_number.isdigit() or len(mobile_number) != 10:
        bot.reply_to(message, "Please enter a valid 10-digit mobile number.")
        bot.register_next_step_handler(message, process_mobile_number)
    else:
        user_mobile_numbers[user_id] = mobile_number
        bot.reply_to(message, "Mobile number registered successfully. You can now generate a lottery number by typing /generate.")

@bot.message_handler(commands=['generate'])
def generate_lottery_numbers(message):
    user_id = message.from_user.id

    if user_id not in user_mobile_numbers:
        bot.reply_to(message, "Please send your mobile number to register first.")
        return

    if user_id in allowed_user_ids:
        if user_id in user_lottery_status and user_lottery_status[user_id]:
            bot.reply_to(message, "Sorry, you have already generated a lottery number.")
        else:
            num_digits = 4   # Number of random digits
            num_letters = 2  # Number of random uppercase letters

            letters = ''.join(random.choice(string.ascii_uppercase) for _ in range(num_letters))
            digits = ''.join(str(random.randint(0, 9)) for _ in range(num_digits))
            ticket = f"{letters}-{digits}"

            user_lottery_status[user_id] = True  # Mark the user as having generated a lottery number
            mobile_number = user_mobile_numbers.get(user_id)  # Retrieve mobile number

            # Send the lottery ticket to the user
            bot.reply_to(message, f"Your lottery ticket: {ticket}")

            # Store the lottery ticket in MongoDB
            collection.insert_one({
                "user_id": user_id,
                "mobile_number": mobile_number,
                "ticket": ticket
            })

            # Update in-memory lottery_tickets list
            lottery_tickets.append((user_id, mobile_number, ticket))
    else:
        bot.reply_to(message, "Sorry, you are not authorized to generate lottery numbers.")

@bot.message_handler(commands=['reset'])
def reset_bot(message):
    user_id = message.from_user.id

    if user_id == OWNER_USER_ID:
        global user_mobile_numbers
        global user_lottery_status
        global lottery_tickets
        global allowed_user_ids

        # Clear user data
        user_mobile_numbers = {}
        user_lottery_status = {}
        lottery_tickets = []

        # Clear the list of allowed users
        allowed_user_ids = []

        # Delete all user documents from the MongoDB collection
        collection.delete_many({})

        bot.reply_to(message, "Bot has been reset. User data, lottery tickets, and user restrictions have been cleared.")
    else:
        bot.reply_to(message, "You are not authorized to reset the bot.")


@bot.message_handler(commands=['list'])
def list_lottery_numbers(message):
    user_id = message.from_user.id

    if user_id == OWNER_USER_ID:
        lottery_list = []
        for index, (user_id, mobile_number, ticket) in enumerate(lottery_tickets, start=1):
            lottery_list.append(f"{index}. User ID: {user_id}, Mobile Number: {mobile_number}, Ticket: {ticket}")

        if lottery_list:
            response = "\n".join(lottery_list)
            bot.send_message(user_id, "List of generated lottery numbers:\n" + response)
        else:
            bot.reply_to(message, "No lottery numbers have been generated yet.")
    else:
        bot.reply_to(message, "You are not authorized to view the list.")

@bot.message_handler(commands=['winner'])
def select_winner(message):
    user_id = message.from_user.id

    if user_id == OWNER_USER_ID:
        if not lottery_tickets:
            bot.reply_to(message, "No lottery tickets available to select a winner.")
        else:
            winner = random.choice(lottery_tickets)
            user_id, mobile_number, ticket = winner
            user_message = f"Congratulations! You are the winner of the lottery.\nLottery Ticket: {ticket}"
            bot.send_message(user_id, user_message)

            # Send the winner's info to the channel
            channel_message = f"Winner selected:\nUser ID: {user_id}\nMobile Number: {mobile_number}\nTicket: {ticket}"
            bot.send_message(CHANNEL_ID, channel_message)

            bot.reply_to(message, f"The winner with User ID {user_id} has been notified.")
    else:
        bot.reply_to(message, "You are not authorized to select a winner.")

@bot.message_handler(commands=['adduser'])
def add_user_authorization(message):
    user_id = message.from_user.id

    if user_id == OWNER_USER_ID:
        if message.reply_to_message and message.reply_to_message.from_user:
            authorized_user_id = message.reply_to_message.from_user.id
            if authorized_user_id not in allowed_user_ids:
                allowed_user_ids.append(authorized_user_id)
                collection.update_one({"user_id": authorized_user_id}, {"$set": {"is_authorized": True}}, upsert=True)
                bot.reply_to(message, f"User with ID {authorized_user_id} has been authorized to use the bot.")
            else:
                bot.reply_to(message, f"User with ID {authorized_user_id} is already authorized.")
        else:
            bot.reply_to(message, "Please reply to a user's message to authorize them to use the bot.")
    else:
        bot.reply_to(message, "You are not authorized to add user authorization.")

if __name__ == '__main__':
    bot.polling()
