'''Файл для хранения таблиц'''

from sqlalchemy import Boolean, Column, Integer, String
from db import Model

class Users_db(Model):
    '''Класс для работы с таблицей'''
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    login = Column(String)
    passhash = Column(String)
