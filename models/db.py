__doc__ = """
this module defines objects for work with SQLalchemy
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import config

engine = create_engine(config.DB_FILEPATH) # двигатель БД

Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)  # сессия

Base = declarative_base() # класс, от которого будут наследоваться таблицы
