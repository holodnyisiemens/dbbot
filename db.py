from sqlalchemy.orm import sessionmaker # для создания сессии
from sqlalchemy import create_engine # для создания движка
from sqlalchemy.ext.declarative import declarative_base
from config import DB_FILEPATH

# экземпляр класса model позволяющий описывать таблицы
Model = declarative_base(name='Model')

engine = create_engine(DB_FILEPATH) # создание двигателя базы данных (объекта engine)
Session = sessionmaker( # позволит генерировать сколько нужно сессий
    engine, 
    autoflush=False,    # автообновление данных
    autocommit=False
)

session = Session() # получение новой сессии