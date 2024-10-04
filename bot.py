from telebot import types

import config
import telebot
import sqlite3

bot = telebot.TeleBot(config.TOKEN)

db_connection = sqlite3.connect('wishlist.db', check_same_thread=False)
cursor = db_connection.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS wishlists (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    wishlist TEXT
)
''')
db_connection.commit()


def create_keyboard(buttons):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(*buttons)
    return markup


def create_main_keyboard():
    buttons = [
        types.KeyboardButton("/add"),
        types.KeyboardButton("/view"),
        types.KeyboardButton("/view_other"),
        types.KeyboardButton("/remove"),
    ]
    return create_keyboard(buttons)


main_markup = create_main_keyboard()


def get_user_data(user_id):
    cursor.execute('SELECT wishlist FROM wishlists WHERE user_id = ?', (user_id,))
    return cursor.fetchone()


def update_wishlist(user_id, wishlist):
    cursor.execute('UPDATE wishlists SET wishlist = ? WHERE user_id = ?', (wishlist, user_id))
    db_connection.commit()


def add_user_wishlist(user_id, username, wishlist):
    cursor.execute('INSERT INTO wishlists (user_id, username, wishlist) VALUES (?, ?, ?)', (user_id, username, wishlist))
    db_connection.commit()


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id,
                     "Commands:"
                     "\n/add - add item"
                     "\n/view - view your list"
                     "\n/view_other - view another person's list"
                     "\n/remove - remove item",
                     reply_markup=main_markup)


@bot.message_handler(commands=['add'])
def add_wish(message):
    bot.send_message(message.chat.id, "Enter what you want to add to your wishlist:", reply_markup=main_markup)
    bot.register_next_step_handler(message, process_add_wish)


def process_add_wish(message):
    user_id = message.from_user.id
    username = message.from_user.username
    wish = message.text

    result = get_user_data(user_id)

    if result:
        current_wishlist = result[0]
        new_wishlist = current_wishlist + '\n' + wish
        update_wishlist(user_id, new_wishlist)
    else:
        add_user_wishlist(user_id, username, wish)

    bot.send_message(message.chat.id, "Item added to wishlist!", reply_markup=main_markup)


@bot.message_handler(commands=['view'])
def view_wishlist(message):
    user_id = message.from_user.id
    result = get_user_data(user_id)

    if result:
        wishlist = result[0]
        bot.send_message(message.chat.id, f"Your wishlist:\n{wishlist}", reply_markup=main_markup)
    else:
        bot.send_message(message.chat.id, "Your wishlist is empty.", reply_markup=main_markup)


@bot.message_handler(commands=['view_other'])
def view_other_wishlist(message):
    bot.send_message(message.chat.id, "Enter the Telegram ID of the user whose wishlist you want to view (@username):",
                     reply_markup=main_markup)
    bot.register_next_step_handler(message, process_view_other_wishlist)


def process_view_other_wishlist(message):
    other_username = message.text.lstrip('@')

    cursor.execute('SELECT user_id, wishlist FROM wishlists WHERE username = ?', (other_username,))
    result = cursor.fetchone()

    if result:
        user_id, wishlist = result
        bot.send_message(message.chat.id, f"Wishlist of user @{other_username}:\n{wishlist}", reply_markup=main_markup)
    else:
        bot.send_message(message.chat.id, f"User @{other_username} not found or their wishlist is empty.",
                         reply_markup=main_markup)


@bot.message_handler(commands=['remove'])
def remove_wish(message):
    bot.send_message(message.chat.id, "Enter the item you want to remove from your wishlist:", reply_markup=main_markup)
    bot.register_next_step_handler(message, process_remove_wish)


def process_remove_wish(message):
    user_id = message.from_user.id
    item_to_remove = message.text

    result = get_user_data(user_id)

    if result:
        current_wishlist = result[0]
        new_wishlist = '\n'.join([item for item in current_wishlist.split('\n') if item != item_to_remove])
        update_wishlist(user_id, new_wishlist)
        bot.send_message(message.chat.id, "Item removed from wishlist!", reply_markup=main_markup)
    else:
        bot.send_message(message.chat.id, "Your wishlist is empty.", reply_markup=main_markup)


@bot.message_handler(content_types=['text'])
def unknown(message):
    bot.send_message(message.chat.id, 'Unknown command', reply_markup=main_markup)


bot.polling()
