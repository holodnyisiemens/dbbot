import models
import config

if __name__ == '__main__':
    bot_client = models.BotClient(config.TELEGRAM_BOT_TOKEN)
    bot_client.register_handlers()
    bot_client.bot.polling(none_stop=True)
