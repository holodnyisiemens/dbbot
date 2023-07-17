__doc__ = """
this module defines
"""

from sqlalchemy import Column, Integer, String

from .db import Base

class UsersTable(Base):
    """
    This is the class for work with database
    """

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    login = Column(String)
    passhash = Column(String)

    def __init__(self, login: str, passhash: str):
        self.login = login
        self.passhash = passhash
