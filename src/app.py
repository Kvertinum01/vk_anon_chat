from vkbottle.bot import Bot
from vkbottle import API

from src.handlers import labelers
from src.handlers.wrapers import lw
from src.config_reader import BOT_TOKEN, BOT_TOKEN_2
from src.middlewares import CheckReg, ApiManager, CheckVip


api_list = (API(BOT_TOKEN), API(BOT_TOKEN_2))
bot = Bot(loop_wrapper=lw)


for custom_labeler in labelers:
    bot.labeler.load(custom_labeler)


bot.labeler.message_view.register_middleware(CheckReg)
bot.labeler.message_view.register_middleware(ApiManager)
bot.labeler.message_view.register_middleware(CheckVip)
