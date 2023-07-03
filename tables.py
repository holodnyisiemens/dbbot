from sqlalchemy import Column, Integer, String
from db import Base

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    login = Column(String)
    passhash = Column(String)

    def __init__(self, login: str, passhash: str):
        self.login = login
        self.passhash = passhash

    def __repr__(self):
        return f"Логин: '{self.login}'. Хэш пароля: '{self.passhash}'"
