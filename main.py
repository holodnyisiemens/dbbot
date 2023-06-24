import sqlite3
import telebot
import config
import hashlib
import random

bot = telebot.TeleBot(config.TOKEN)

class User:
    def __init__(self, login, hashpass):
        self.login = login
        self.hashpass = hashpass
        self.authorized = False

user = User(None, None)

list_markup = telebot.types.InlineKeyboardMarkup()
list_btn = telebot.types.InlineKeyboardButton('Список пользователей', callback_data='list')
list_markup.add(list_btn)

markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
btn1 = telebot.types.KeyboardButton('Регистрация')
btn2 = telebot.types.KeyboardButton('Аутентификация')
markup.row(btn1)
markup.row(btn2)
# Возможность вывода списка пользователей появится после авторизации

cancel_markup = telebot.types.InlineKeyboardMarkup()
cancel_btn = telebot.types.InlineKeyboardButton('Отмена', callback_data='cancel')
cancel_markup.add(cancel_btn)

@bot.message_handler(commands=['start'])
def start(message):
    conn = sqlite3.connect(config.sqlfile)  # подключение к создаваемой базе данных
    cur = conn.cursor()                     # курсор для работы с таблицами
    # команда для создания таблицы users, если такой не существует
    # поле id будет автоматически инкрементироваться, являясь первичным ключом (primery key)
    query = f'CREATE TABLE IF NOT EXISTS users (id int primery key, login varchar({config.loginlen}), passhash varchar({config.passlen}))'
    cur.execute(query)
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(message.chat.id, 'Привет, я Райан Гослинг! Авторизируйтесь, чтобы пообщаться', reply_markup=markup)

@bot.message_handler(content_types=['text'])
def text_handler(message):
    answer_arr = ['Сорян я занят', 'Не сейчас', 'Погодь', 'Отвечу позже', 'Приду домой - отвечу', 'Будет время напишу', 'Давай чуток попозже', 'Занят пока что', 'Я за рулем давай потом',
    'Немного занят, давай потом', 'Времени нет, потом спишемся', 'Давай попозже напишу', 'Подожди немного', 'Ща сек', 'Блин некогда, давай потом поговорим']

    if message.chat.type == 'private':
        if message.text == 'Регистрация':
            bot.send_message(message.chat.id, 'Придумайте логин', reply_markup=cancel_markup)
            bot.register_next_step_handler(message, create_account)

        elif message.text == 'Аутентификация':
            user.authorized = False
            bot.send_message(message.chat.id, 'Введите логин', reply_markup=cancel_markup)
            bot.register_next_step_handler(message, check_login)

        elif user.authorized:
            bot.send_message(message.chat.id, random.choice(answer_arr))

        else:
            bot.send_message(message.chat.id, 'Авторизируйся, потом поговорим', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Невозможно выполнить данную команду в неприватном чате', reply_markup=markup)

def insert_in_table(user: User):
    conn = sqlite3.connect(config.sqlfile)
    cur = conn.cursor()
    # передавать id не нужно: он инкрементируется автоматически
    # для передачи других параметров можно использовать % и кортеж параметров
    query = "INSERT INTO users (login, passhash) VALUES ('%s', '%s')" % (user.login, user.hashpass)
    cur.execute(query)
    conn.commit()
    cur.close()
    conn.close()

def user_exists(username: str) -> bool:
    conn = sqlite3.connect(config.sqlfile)
    cur = conn.cursor()
    query = "SELECT login FROM users"
    cur.execute(query)
    users = cur.fetchall()
    cur.close()
    conn.close()
    login_tup = (username, )
    return login_tup in users

def create_account(login_msg):
    if user_exists(login_msg.text):
        bot.reply_to(login_msg, 'Данный логин занят. Придумайте другой логин', reply_markup=cancel_markup)
        bot.register_next_step_handler(login_msg, create_account)

    else:
        user.login = login_msg.text
        pass_msg = login_msg
        bot.send_message(pass_msg.chat.id, 'Придумайте пароль', reply_markup=cancel_markup)
        bot.register_next_step_handler(pass_msg, create_pass_and_insert, user)

def find_hash(password, local_salt) -> str:
    hash = password
    hash += config.global_salt
    hash += local_salt
    for _ in range(10):
        hash = hashlib.md5(hash.encode()).hexdigest()
    return hash

def check_login(login_msg):
    if user_exists(login_msg.text):
        login = login_msg.text
        pass_msg = login_msg
        bot.send_message(pass_msg.chat.id, 'Введите пароль', reply_markup=cancel_markup)
        bot.register_next_step_handler(pass_msg, check_pass, login, 0)

    else:
        bot.send_message(login_msg.chat.id, 'Данного пользователя не существует. Повторите попытку или отмените операцию', reply_markup=cancel_markup)
        bot.register_next_step_handler(login_msg, check_login)

def check_pass(pass_msg, login, attempts_count: int):
    global list_markup
    conn = sqlite3.connect(config.sqlfile)
    cur = conn.cursor()
    query = f"SELECT passhash FROM users WHERE login = '{login}'"
    cur.execute(query)
    true_passhash = cur.fetchall()

    if find_hash(pass_msg.text, login) == true_passhash[0][0]:
        bot.send_message(pass_msg.chat.id, 'Вы успешно вошли в аккаунт! Теперь мы можем пообщаться', reply_markup=list_markup)
        user.authorized = True

    elif attempts_count < 2:
        attempts_count += 1
        bot.reply_to(pass_msg, f'Пароль неверный. Осталось попыток: {3 - attempts_count}', reply_markup=cancel_markup)
        bot.register_next_step_handler(pass_msg, check_pass, login, attempts_count)

    else:
        bot.send_message(pass_msg.chat.id, 'Попытки закончились', reply_markup=markup)

    cur.close()
    conn.close()

def create_pass_and_insert(pass_msg, user: User):
    user.hashpass = find_hash(pass_msg.text, user.login)
    insert_in_table(user)

    bot.send_message(pass_msg.chat.id, 'Поздравляю! Теперь Вы можете со мной пообщаться', reply_markup=list_markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_message(call):
    if call.message:
        if call.data == 'cancel':
            bot.edit_message_text('Отмена', call.message.chat.id, call.message.message_id)
            bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
            bot.send_message(call.message.chat.id, 'Лучше бы Вы прошли авторизацию', reply_markup=markup)
        elif call.data == 'list':
            conn = sqlite3.connect(config.sqlfile)
            cur = conn.cursor()
            query = "SELECT * FROM users"
            cur.execute(query)
            users = cur.fetchall()
            query = "SELECT COUNT(*) FROM users"
            cur.execute(query)
            count = cur.fetchall()
            user_list = f'Список пользователей (всего: {count[0][0]}):\n'
            for item in users:
                user_list += f"Имя: '{item[1]}'\n"
            cur.close()
            conn.close()
            bot.send_message(call.message.chat.id, user_list)

bot.polling(none_stop=True)
