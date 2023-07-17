__doc__ = """
This module contains classes and functions for work with bot and user 
"""
import hashlib
import random

import telebot
from sqlalchemy import func
from sqlalchemy_utils import database_exists
from telebot.types import *

import config
from .db import Session, engine, Base
from .tables import *

class BotUser:
    '''Класс для работы с текущим пользователем'''
    def __init__(self, login: str, passhash: str):
        self.login = login
        self.passhash = passhash
        # Состояние, в котором находится пользователь
        # (True - авторизован, False - нет).
        self.authorized = False

class BotClient:
    '''Класс для работы с ботом'''

    # Текст, который отправляет боту кнопка регистрации.
    __reg_btn_txt = 'Регистрация'
    # Текст, который отправляет боту кнопка аутентификации.
    __auth_bnt_txt = 'Аутентификация'
    __list_btn_txt = 'Список пользователей'
    __cancel_btn_txt = 'Отмена'

    def __init__(self, token: str):
        self.bot = telebot.TeleBot(token=token)
        self.user = BotUser(login=None, passhash=None)

        self._kb_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        # Кнопка, отправляющая сообщение для регистрации.
        self._kb_reg_bnt = KeyboardButton(text=self.__reg_btn_txt)
        # Кнопка, отправляющая сообщение для аутентификации.
        self._kb_auth_bnt = KeyboardButton(text=self.__auth_bnt_txt)
        self._kb_markup.row(self._kb_reg_bnt)
        self._kb_markup.row(self._kb_auth_bnt)

        self._list_markup = InlineKeyboardMarkup()
        self._list_btn = InlineKeyboardButton(
            text=self.__list_btn_txt,
            callback_data='list'
        )
        self._list_markup.add(self._list_btn)

        self._cancel_markup = InlineKeyboardMarkup()
        self._cancel_btn = InlineKeyboardButton(
            text=self.__cancel_btn_txt,
            callback_data='cancel'
        )
        self._cancel_markup.add(self._cancel_btn)


    def find_hash(
        self,
        password: str,
        local_salt: str = ''
    ) -> str:
        '''
        Функция, вычисляющая хэш-сумму пароля несколько раз с применением солей
        '''

        passhash: str = password
        # Глобальная соль для хэширования (по умолчанию выключена).
        passhash += config.GLOBAL_SALT
        # Локальная соль для хэширования (по умолчанию выключена).
        passhash += local_salt
        for _ in range(config.HASHES_NUMBER):
            passhash = hashlib.md5(passhash.encode()).hexdigest()
        return passhash

    def insert_in_table(self):
        '''
        Добавление данных пользователя в таблицу.
        '''
        with Session() as sess:
            # Добавление данных пользователя в БД.
            sess.add(
                UsersTable(
                    login=self.user.login,
                    passhash=self.user.passhash
                )
            )
            sess.commit()

    def user_exists(
        self,
        login: str
    ) -> bool:
        '''
        Функция для проверки существования 
        пользователя в базе данных пользователей.
        '''
        with Session() as sess:
            # Если пользователь существует вернется
            # кортеж состоящий из имени пользователя,
            # иначе None.
            result = sess.query(UsersTable.login) \
                         .filter(UsersTable.login == login) \
                         .one_or_none()
        # Если в результат будет None, то вернется
        # False, иначе True.
        return bool(result)

    def create_account(self, login_msg: Message) -> None:
        '''Функция для создания аккаунта'''
        # логины в базе данных не должны совпадать
        if self.user_exists(login=login_msg.text):    # рекурсивный случай
            self.bot.reply_to(
                message=login_msg,
                text='Данный логин занят. Придумайте другой логин',
                reply_markup=self._cancel_markup,
            )
            self.bot.register_next_step_handler(
                message=login_msg,
                callback=self.create_account,
            )
        else:       # базовый случай
            self.user.login = login_msg.text
            pass_msg = login_msg
            self.bot.send_message(
                chat_id=pass_msg.chat.id,
                text='Придумайте пароль',
                reply_markup=self._cancel_markup,
            )
            self.bot.register_next_step_handler(
                message=pass_msg,
                callback=self.create_pass_and_insert,
            )

    def check_pass(
        self,
        pass_msg: Message,
        login: str,
        attempts_count: int
    ) -> None:
        '''
        Функция проверки введенного пользователем 
        пароля при аутентификации.
        '''
        with Session() as sess:
            # Если пользователь существует, вернется
            # кортеж состоящий из хэш суммы пароля
            # пользователя, иначе None.
            result = sess.query(UsersTable.passhash) \
                         .filter(UsersTable.login == login) \
                         .one()

        # result[0] - первый элемент кортежа - хэш сумма пароля
        if self.find_hash(password=pass_msg.text) == result[0]:
            self.bot.send_message(
                chat_id=pass_msg.chat.id,
                text='Вы успешно вошли в аккаунт! Теперь мы можем пообщаться',
                reply_markup=self._list_markup,
            )
            self.user.authorized = True
        elif attempts_count < 2:    # количество попыток (максимум 3)
            attempts_count += 1
            self.bot.reply_to(
                message=pass_msg,
                text=f'Пароль неверный. Осталось попыток: {3 - attempts_count}',
                reply_markup=self._cancel_markup,
            )
            self.bot.register_next_step_handler(
                message=pass_msg,
                callback=self.check_pass,
                login=login,
                attempts_count=attempts_count,
            )
        else:
            self.bot.send_message(
                chat_id=pass_msg.chat.id,
                text='Попытки закончились',
                reply_markup=self._kb_markup,
            )

    def create_pass_and_insert(
        self,
        pass_msg: Message
    ) -> None:
        '''
        Функция для создания пароля и добавления 
        логина и пароля нового пользователя в базу данных.
        '''
        self.user.passhash = self.find_hash(password=pass_msg.text)
        self.insert_in_table()  # помещение данных в таблицу
        self.bot.send_message(
            chat_id=pass_msg.chat.id,
            text='Поздравляю! Теперь Вы можете со мной пообщаться',
            reply_markup=self._list_markup)
        self.user.authorized = True

    def check_login(
        self,
        login_msg: Message
    ) -> None:
        '''
        Функция проверки логина на существование 
        в базе данных.
        '''
        if self.user_exists(login=login_msg.text):
            login = login_msg.text
            pass_msg = login_msg
            self.bot.send_message(
                chat_id=pass_msg.chat.id,
                text='Введите пароль',
                reply_markup=self._cancel_markup,
                )
            self.bot.register_next_step_handler(
                message=pass_msg,
                callback=self.check_pass,
                login=login,
                attempts_count=0,
                )
        else:
            self.bot.send_message(
                chat_id=login_msg.chat.id,
                text='Данного пользователя не существует. ' +
                'Повторите попытку или отмените операцию',
                reply_markup=self._cancel_markup,
                )

            self.bot.register_next_step_handler(
                message=login_msg,
                callback=self.check_login,
                )

    def start(self) -> None:
        '''Функция обработки всех сообщений пользователя'''
        if not database_exists(engine.url):
            Base.metadata.create_all(engine)

        @self.bot.message_handler(commands=['start'])
        def start_handler(message: Message):
            '''Функция обработки команды start'''
            self.bot.send_message(
                chat_id=message.chat.id,
                text='Привет, я Райан Гослинг! Авторизируйтесь, чтобы пообщаться',
                reply_markup=self._kb_markup,
            )

        @self.bot.message_handler(content_types=['text'])
        def text_handler(message: Message):
            '''Функция обработки текстовых сообщений'''
            if message.chat.type == 'private':  # проверка приватности чата
                if message.text == self.__reg_btn_txt:
                    self.bot.send_message(
                        chat_id=message.chat.id,
                        text='Придумайте логин',
                        reply_markup=self._cancel_markup,
                    )
                    self.bot.register_next_step_handler(
                        message=message,
                        callback=self.create_account,
                    )
                elif message.text == self.__auth_bnt_txt:
                    self.bot.send_message(
                        chat_id=message.chat.id,
                        text='Введите логин',
                        reply_markup=self._cancel_markup,
                    )
                    self.bot.register_next_step_handler(
                        message=message,
                        callback=self.check_login,
                    )
                elif self.user.authorized:
                    self.bot.send_message(
                        chat_id=message.chat.id,
                        text=random.choice(config.ANSWER_LIST),
                    )
                else:
                    self.bot.send_message(
                        chat_id=message.chat.id,
                        text='Авторизируйся, потом поговорим',
                        reply_markup=self._kb_markup,
                    )
            else:
                self.bot.send_message(
                    chat_id=message.chat.id,
                    text='Невозможно выполнить данную команду ' +
                    'в неприватном чате',
                    reply_markup=self._kb_markup,
                )

        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_message(call):
            '''Функция обработки вызовов'''
            if call.message:
                if call.data == 'cancel':
                    self.bot.edit_message_text(
                        text='Лучше бы Вы прошли авторизацию',
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                    )
                    self.bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
                elif call.data == 'list':
                    with Session() as sess:
                        user_count = sess.query(func.count()).select_from(UsersTable).scalar()
                        result = sess.query(UsersTable.login).all()
                        user_list = f'Список пользователей (всего: {user_count}):\n'
                    for login, in result:
                        user_list += f'{login}\n'
                    self.bot.send_message(
                        chat_id=call.message.chat.id,
                        text=user_list,
                    )

        self.bot.polling(none_stop=True)
