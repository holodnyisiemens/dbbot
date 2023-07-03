import telebot
import config
import sqlite3
import hashlib
import random
from db import session
import tables

# result = session.query(tables.Users_db.login, tables.Users_db.passhash).all()
# print(result)

# import sqlalchemy as db
# conn = engine.connect()
# metadata = db.MetaData() # будет хранить информацию о таблицах
# metadata.create_all(engine)
# def insert_in_table(login: str, password: str):
#     insertion_query = users_db.insert().values([
#         {'login':login, 'passhash': password}
#     ])
#     conn.execute(insertion_query)
# insert_in_table('log', 'pas')
# select_all_query = db.select(users_db)
# select_all_result = conn.execute(select_all_query)
# print(select_all_result.fetchall())
# conn.close()

class User:
    '''Класс для работы с пользователем'''
    def __init__(self, login: str, hashpass: str):
        self.login = login
        self.hashpass = hashpass
        self.authorized = False

class BotClient:
    '''Класс для работы с ботом'''

    reg_btn_txt = 'Регистрация'     # текст, который отправляет боту кнопка регистрации
    auth_bnt_txt = 'Аутентификация' # текст, который отправляет боту кнопка аутентификации
    kb_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb_reg_bnt = telebot.types.KeyboardButton(reg_btn_txt)
    kb_auth_bnt = telebot.types.KeyboardButton(auth_bnt_txt)
    kb_markup.row(kb_reg_bnt)
    kb_markup.row(kb_auth_bnt)

    list_markup = telebot.types.InlineKeyboardMarkup()
    list_btn = telebot.types.InlineKeyboardButton('Список пользователей', callback_data='list')
    list_markup.add(list_btn)
    # Возможность вывода списка пользователей появится после авторизации

    cancel_markup = telebot.types.InlineKeyboardMarkup()
    cancel_btn = telebot.types.InlineKeyboardButton('Отмена', callback_data='cancel')
    cancel_markup.add(cancel_btn)

    def __init__(self, token: str):
        self.bot = telebot.TeleBot(token)
        self.user = User(None, None)

    def register_handlers(self):
        def insert_in_table(user):
            conn = sqlite3.connect(config.SQL_FILEPATH)
            cur = conn.cursor()
            # передавать id не нужно: он инкрементируется автоматически
            # для передачи других параметров можно использовать % и кортеж параметров
            query = "INSERT INTO users (login, passhash) VALUES ('%s', '%s')" % (user.login, user.hashpass)
            cur.execute(query)
            conn.commit()
            cur.close()
            conn.close()

        def user_exists(username: str) -> bool:
            # result = session.query(tables.Users_db.login, tables.Users_db.passhash).filter(tables.Users_db.login == username).one_or_none()
            conn = sqlite3.connect(config.SQL_FILEPATH)
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
                self.bot.reply_to(login_msg, 'Данный логин занят. Придумайте другой логин', reply_markup=self.cancel_markup)
                self.bot.register_next_step_handler(login_msg, create_account)

            else:
                self.user.login = login_msg.text
                pass_msg = login_msg
                self.bot.send_message(pass_msg.chat.id, 'Придумайте пароль', reply_markup=self.cancel_markup)
                self.bot.register_next_step_handler(pass_msg, create_pass_and_insert, self.user)

        def create_pass_and_insert(pass_msg, user):
            user.hashpass = find_hash(pass_msg.text, user.login)
            insert_in_table(user)
            self.bot.send_message(pass_msg.chat.id, 'Поздравляю! Теперь Вы можете со мной пообщаться', reply_markup=self.list_markup)
            user.authorized = True

        def find_hash(password: str, local_salt: str) -> str:
            hash = password
            hash += config.GLOBAL_SALT
            hash += local_salt
            for _ in range(config.HASHES_NUMBER):
                hash = hashlib.md5(hash.encode()).hexdigest()
            return hash

        def check_login(login_msg):
            if user_exists(login_msg.text):
                login = login_msg.text
                pass_msg = login_msg
                self.bot.send_message(pass_msg.chat.id, 'Введите пароль', reply_markup=self.cancel_markup)
                self.bot.register_next_step_handler(pass_msg, check_pass, login, 0)

            else:
                self.bot.send_message(login_msg.chat.id, 'Данного пользователя не существует. Повторите попытку или отмените операцию', reply_markup=self.cancel_markup)
                self.bot.register_next_step_handler(login_msg, check_login)

        def check_pass(pass_msg, login, attempts_count: int):
            conn = sqlite3.connect(config.SQL_FILEPATH)
            cur = conn.cursor()
            query = f"SELECT passhash FROM users WHERE login = '{login}'"
            cur.execute(query)
            true_passhash = cur.fetchall()

            if find_hash(pass_msg.text, login) == true_passhash[0][0]:
                self.bot.send_message(pass_msg.chat.id, 'Вы успешно вошли в аккаунт! Теперь мы можем пообщаться', reply_markup=self.list_markup)
                self.user.authorized = True

            elif attempts_count < 2:
                attempts_count += 1
                self.bot.reply_to(pass_msg, f'Пароль неверный. Осталось попыток: {3 - attempts_count}', reply_markup=self.cancel_markup)
                self.bot.register_next_step_handler(pass_msg, check_pass, login, attempts_count)

            else:
                self.bot.send_message(pass_msg.chat.id, 'Попытки закончились', reply_markup=self.kb_markup)

            cur.close()
            conn.close()

        @self.bot.message_handler(commands=['start'])
        def start_handler(message):
            conn = sqlite3.connect(config.SQL_FILEPATH)  # подключение к создаваемой базе данных
            cur = conn.cursor()                     # курсор для работы с таблицами
            # команда для создания таблицы users, если такой не существует
            # поле id будет автоматически инкрементироваться, являясь первичным ключом (primery key)
            query = f'CREATE TABLE IF NOT EXISTS users (id int primery key, login varchar({config.LOGIN_LEN}), passhash varchar({config.PASS_LEN}))'
            cur.execute(query)
            conn.commit()
            cur.close()
            conn.close()
            self.bot.send_message(message.chat.id, 'Привет, я Райан Гослинг! Авторизируйтесь, чтобы пообщаться', reply_markup=self.kb_markup)

        @self.bot.message_handler(content_types=['text'])
        def text_handler(message):
            if message.chat.type == 'private':
                if message.text == 'Регистрация':
                    self.bot.send_message(message.chat.id, 'Придумайте логин', reply_markup=self.cancel_markup)
                    self.bot.register_next_step_handler(message, create_account)

                elif message.text == 'Аутентификация':
                    self.bot.send_message(message.chat.id, 'Введите логин', reply_markup=self.cancel_markup)
                    self.bot.register_next_step_handler(message, check_login)

                elif self.user.authorized:
                    self.bot.send_message(message.chat.id, random.choice(config.ANSWER_LIST))

                else:
                    self.bot.send_message(message.chat.id, 'Авторизируйся, потом поговорим', reply_markup=self.kb_markup)
            else:
                self.bot.send_message(message.chat.id, 'Невозможно выполнить данную команду в неприватном чате', reply_markup=self.kb_markup)

        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_message(call):
            if call.message:
                if call.data == 'cancel':
                    self.bot.edit_message_text('Лучше бы Вы прошли авторизацию', call.message.chat.id, call.message.message_id)
                    self.bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
                elif call.data == 'list':
                    conn = sqlite3.connect(config.SQL_FILEPATH)
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
                    self.bot.send_message(call.message.chat.id, user_list)

        
