__doc__ = """
This is the file with configurations for bot and database.
You can only specify TELEGRAM_BOT_TOKEN like environment variable.
The rest of the entries can be left unchanged.
"""

import os
from dotenv import load_dotenv

load_dotenv()   # добавление переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

DATABASE_NAME="tg_bot_users.sql" # имя файла с расширением
DB_FILEPATH = f'sqlite:///{DATABASE_NAME}' # драйвер и имя файла

GLOBAL_SALT=os.getenv('GLOBAL_SALT', '')    # глобальная соль для хэширования пароля

HASHES_NUMBER = 10  # количество применений алгоритма хэширования к паролю перед занесением в БД

ANSWER_LIST = ['Сорян я занят', 'Не сейчас', 'Погодь', 'Отвечу позже', 'Приду домой - отвечу',
               'Будет время напишу', 'Давай чуток попозже', 'Занят пока что', 
               'Я за рулем давай потом', 'Немного занят, давай потом', 
               'Времени нет, потом спишемся', 'Давай попозже напишу', 
               'Подожди немного', 'Ща сек', 'Блин некогда, давай потом поговорим']
