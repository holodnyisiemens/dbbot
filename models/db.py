from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import config
from sqlalchemy import MetaData, Table # для создания таблицы

engine = create_engine(config.DB_FILEPATH) # двигатель БД

Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)  # сессия

Base = declarative_base() # класс, от которого будут наследоваться таблицы
