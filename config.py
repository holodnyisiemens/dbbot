import os
from dotenv import load_dotenv

load_dotenv()   # добавление переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SQL_FILEPATH = os.getenv('SQL_FILEPATH', 'users.sql')   # путь к файлу включая расширение .sql

LOGIN_LEN = 50
PASS_LEN = 50

DB_FILEPATH = os.getenv('DB_FILEPATH', 'sqlite:///users.sql')

GLOBAL_SALT=os.getenv('GLOBAL_SALT', '')    # глобальная соль для хэширования пароля

HASHES_NUMBER = 10  # количество применений алгоритма хэширования к паролю перед занесением в БД

ANSWER_LIST = ['Сорян я занят', 'Не сейчас', 'Погодь', 'Отвечу позже', 'Приду домой - отвечу', 'Будет время напишу', 'Давай чуток попозже', 'Занят пока что', 'Я за рулем давай потом',
    'Немного занят, давай потом', 'Времени нет, потом спишемся', 'Давай попозже напишу', 'Подожди немного', 'Ща сек', 'Блин некогда, давай потом поговорим']
