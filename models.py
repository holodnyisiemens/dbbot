import telebot
import config
import sqlite3
import hashlib
import random
from db import Session, engine, Base
import tables
from sqlalchemy import func, insert
from sqlalchemy_utils import database_exists

class User:
    '''Класс для работы с текущим пользователем'''
    def __init__(self, login: str, passhash: str):
        self.login = login
        self.passhash = passhash
        self.authorized = False     # состояние, в котором находится текущий пользователь (True - авторизован, False - нет)

class BotClient:
    '''Класс для работы с ботом'''

    reg_btn_txt = 'Регистрация'     # текст, который отправляет боту кнопка регистрации
    auth_bnt_txt = 'Аутентификация' # текст, который отправляет боту кнопка аутентификации
    kb_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb_reg_bnt = telebot.types.KeyboardButton(reg_btn_txt)      # кнопка, отправляющая сообщение для регистрации
    kb_auth_bnt = telebot.types.KeyboardButton(auth_bnt_txt)    # кнопка, отправляющая сообщение для аутентификации
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
        '''Функция обработки всех сообщений пользователя'''
        def insert_in_table(user):  # добавление данных пользователя в таблицу
            with Session() as sess:
                sess.add(tables.Users(self.user.login, self.user.passhash)) # добавление данных пользователя в виде экземпляра класса User в базу данных
                sess.commit()

        def user_exists(login: str) -> bool:
            '''Функция для проверки существования пользователя в базе данных пользователей'''
            with Session() as sess:
                # если пользователь существует вернется кортеж состоящий из имени пользователя, иначе None
                result = sess.query(tables.Users.login).filter(tables.Users.login == login).one_or_none()
            return bool(result) # если в результат будет None, то вернется False, иначе True

        def create_account(login_msg):
            '''Функция для создания аккаунта'''
            if user_exists(login_msg.text): # логины в базе данных не должны совпадать
                self.bot.reply_to(login_msg, 'Данный логин занят. Придумайте другой логин', reply_markup=self.cancel_markup)
                self.bot.register_next_step_handler(login_msg, create_account)  # рекурсивный вызов обработчика сообщения с логином
            else:
                self.user.login = login_msg.text
                pass_msg = login_msg
                self.bot.send_message(pass_msg.chat.id, 'Придумайте пароль', reply_markup=self.cancel_markup)
                self.bot.register_next_step_handler(pass_msg, create_pass_and_insert)

        def create_pass_and_insert(pass_msg):
            '''Функция для создания пароля и добавления логина и пароля нового пользователя в базу данных'''
            self.user.passhash = find_hash(pass_msg.text)
            insert_in_table(self.user)  # помещение данных в таблицу
            self.bot.send_message(pass_msg.chat.id, 'Поздравляю! Теперь Вы можете со мной пообщаться', reply_markup=self.list_markup)
            self.user.authorized = True

        def find_hash(password: str, local_salt: str = '') -> str:
            '''Функция, вычисляющая хэш-сумму пароля HASHES_NUMBER раз с применением солей'''
            hash = password
            hash += config.GLOBAL_SALT  # глобальная соль для хэширования (по умолчанию выключена)
            hash += local_salt          # локальная соль для хэширования (по умолчанию выключена)
            for _ in range(config.HASHES_NUMBER):
                hash = hashlib.md5(hash.encode()).hexdigest()
            return hash

        def check_login(login_msg):
            '''Функция проверки логина на существование в базе данных'''
            if user_exists(login_msg.text):
                login = login_msg.text
                pass_msg = login_msg
                self.bot.send_message(pass_msg.chat.id, 'Введите пароль', reply_markup=self.cancel_markup)
                self.bot.register_next_step_handler(pass_msg, check_pass, login, 0)

            else:
                self.bot.send_message(login_msg.chat.id, 'Данного пользователя не существует. Повторите попытку или отмените операцию', reply_markup=self.cancel_markup)
                self.bot.register_next_step_handler(login_msg, check_login)

        def check_pass(pass_msg, login, attempts_count: int):
            '''Функция проверки введенного пользователем пароля при аутентификации'''
            with Session() as sess:
                # если пользователь существует вернется кортеж состоящий из хеш суммы пароля пользователя, иначе None
                result = sess.query(tables.Users.passhash).filter(tables.Users.login == login).one() # кортеж из хэш суммы пароля

            if find_hash(pass_msg.text) == result[0]:
                self.bot.send_message(pass_msg.chat.id, 'Вы успешно вошли в аккаунт! Теперь мы можем пообщаться', reply_markup=self.list_markup)
                self.user.authorized = True

            elif attempts_count < 2:    # количество попыток (максимум 3)
                attempts_count += 1
                self.bot.reply_to(pass_msg, f'Пароль неверный. Осталось попыток: {3 - attempts_count}', reply_markup=self.cancel_markup)
                self.bot.register_next_step_handler(pass_msg, check_pass, login, attempts_count)

            else:
                self.bot.send_message(pass_msg.chat.id, 'Попытки закончились', reply_markup=self.kb_markup)

        @self.bot.message_handler(commands=['start'])
        def start_handler(message):
            '''Функция обработки команды start'''
            if not database_exists(engine.url):
                Base.metadata.create_all(engine)

            self.bot.send_message(message.chat.id, 'Привет, я Райан Гослинг! Авторизируйтесь, чтобы пообщаться', reply_markup=self.kb_markup)

        @self.bot.message_handler(content_types=['text'])
        def text_handler(message):
            '''Функция обработки текстовых сообщений'''
            if message.chat.type == 'private':  # проверка приватности чата
                if message.text == self.reg_btn_txt:
                    self.bot.send_message(message.chat.id, 'Придумайте логин', reply_markup=self.cancel_markup)
                    self.bot.register_next_step_handler(message, create_account)

                elif message.text == self.auth_bnt_txt:
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
            '''Функция обработки вызовов'''
            if call.message:
                if call.data == 'cancel':
                    self.bot.edit_message_text('Лучше бы Вы прошли авторизацию', call.message.chat.id, call.message.message_id)
                    self.bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
                elif call.data == 'list':
                    with Session() as sess:
                        count = sess.query(func.count()).select_from(tables.Users).scalar()
                        result = sess.query(tables.Users.login).all()
                    user_list = f'Список пользователей (всего: {count}):\n'
                    for login, in result:
                        user_list += f'{login}\n'
                    self.bot.send_message(call.message.chat.id, user_list)
