import telebot
from telebot import types
import random
import string
from pymongo import MongoClient

# Replace 'YOUR_BOT_TOKEN' with your actual Telegram bot token
TOKEN = '6332642386:AAHwR790oXAj2iQQZh1QrAg0HAiiX8aM97k'
bot = telebot.TeleBot(TOKEN)

# Replace 'YOUR_CHANNEL_ID' with the ID of your Telegram channel
CHANNEL_ID = -1001783918221  # Replace with your channel ID

# Replace 'OWNER_USER_ID' with the user ID of the owner
OWNER_USER_ID = 1778070005  # Replace with the owner's user ID

# Define a list of allowed user IDs who can generate lottery numbers
allowed_user_ids = [OWNER_USER_ID]  # Replace with your allowed user IDs

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

# Price pool parameters
ticket_price = 10  # The price of a single ticket in rupees
price_pool_percentage = 80  # The percentage of ticket sales allocated to the prize pool
def calculate_prize_pool():
    total_sales = len(lottery_tickets) * ticket_price
    prize_pool = (total_sales * price_pool_percentage) / 100
    return prize_pool

def reset_bot_data():
    # Clear all user data, including user authorities, and lottery tickets
    user_mobile_numbers.clear()
    user_lottery_status.clear()
    lottery_tickets.clear()

    # Reset allowed user IDs to include only the owner
    allowed_user_ids.clear()
    allowed_user_ids.append(OWNER_USER_ID)

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

            # Calculate the current prize pool
            prize_pool = calculate_prize_pool()

            # Send the prize pool to the user
            bot.send_message(user_id, f"Current Prize Pool: {prize_pool} rupees")

            # Send the prize pool to all other users who generated lotteries
            for user in lottery_tickets:
                other_user_id, _, _ = user
                if other_user_id != user_id:
                    bot.send_message(other_user_id, f"Current Prize Pool: {prize_pool} rupees")
    else:
        bot.reply_to(message, "Sorry, you are not authorized to generate lottery numbers.")

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

            # Calculate the prize for the winner
            total_sales = len(lottery_tickets) * ticket_price
            prize = (total_sales * price_pool_percentage) / 100
            bot.send_message(user_id, f"You have won {prize} rupees!")

            # Send the winner's info to the channel
            channel_message = f"Winner selected:\nUser ID: {user_id}\nMobile Number: {mobile_number}\nTicket: {ticket}\nPrize: {prize} rupees"
            bot.send_message(CHANNEL_ID, channel_message)

            # Send a list of all users' lottery tickets, mobile numbers, and user IDs to the channel
            all_users_info = "\n".join([f"User ID: {user[0]}, Mobile Number: {user[1]}, Ticket: {user[2]}" for user in lottery_tickets])
            bot.send_message(CHANNEL_ID, f"List of All Users' Lottery Tickets:\n{all_users_info}")

            bot.reply_to(message, f"The winner with User ID {user_id} has been notified.")
    else:
        bot.reply_to(message, "You are not authorized to select a winner.")

@bot.message_handler(commands=['adduser'])
def add_user(message):
    user_id = message.from_user.id

    if user_id == OWNER_USER_ID:
        bot.reply_to(message, "Please enter the user's Telegram User ID to add them as an allowed user.")
        bot.register_next_step_handler(message, process_add_user)
    else:
        bot.reply_to(message, "You are not authorized to add users.")

def process_add_user(message):
    owner_id = message.from_user.id
    user_id_to_add = message.text

    if not user_id_to_add.isdigit():
        bot.reply_to(message, "Please enter a valid numeric User ID.")
        bot.register_next_step_handler(message, process_add_user)
    else:
        user_id_to_add = int(user_id_to_add)

        if user_id_to_add in allowed_user_ids:
            bot.reply_to(message, "This user is already allowed to generate lottery numbers.")
        else:
            allowed_user_ids.append(user_id_to_add)
            bot.reply_to(message, f"User with User ID {user_id_to_add} has been added as an allowed user.")

            # Send a message to the channel
            bot.send_message(CHANNEL_ID, f"New User Added: User ID {user_id_to_add}")

            # Send a message to the owner
            bot.send_message(OWNER_USER_ID, f"User with User ID {user_id_to_add} has been added as an allowed user.")

            # Send a message to the newly added user
            bot.send_message(user_id_to_add, "You have been added as an allowed user. You can now generate lottery tickets by typing /generate.")

@bot.message_handler(commands=['list'])
def list_users_data(message):
    user_id = message.from_user.id

    if user_id == OWNER_USER_ID:
        user_data_list = []
        for user in lottery_tickets:
            user_id, mobile_number, ticket = user
            user_data = f"User ID: {user_id}, Mobile Number: {mobile_number}, Ticket: {ticket}"
            user_data_list.append(user_data)
        
        # Calculate the current prize pool
        prize_pool = calculate_prize_pool()
        user_data_list.append(f"Current Prize Pool: {prize_pool} rupees")

        user_data_text = "\n".join(user_data_list)
        bot.send_message(user_id, "List of All Users' Lottery Tickets and Data:\n" + user_data_text)
    else:
        bot.reply_to(message, "You are not authorized to access the user data list.")

@bot.message_handler(commands=['reset'])
def reset_bot(message):
    user_id = message.from_user.id

    if user_id == OWNER_USER_ID:
        reset_bot_data()
        bot.reply_to(message, "Bot data has been reset. You can now start fresh.")
    else:
        bot.reply_to(message, "You are not authorized to reset the bot.")
        
if __name__ == '__main__':
    bot.polling()
