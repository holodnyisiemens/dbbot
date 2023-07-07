import config
from models import BotClient

if __name__ == '__main__':
    bot_client = BotClient(token=config.TELEGRAM_BOT_TOKEN)
    bot_client.start()
