import os
from dotenv import load_dotenv

load_dotenv()   # добавление переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SQL_FILEPATH = os.getenv('SQL_FILEPATH', 'users.sql')   # путь к файлу включая расширение .sql

LOGIN_LEN = 50
PASS_LEN = 50

GLOBAL_SALT=os.getenv('GLOBAL_SALT', '')    # глобальная соль для хэширования
