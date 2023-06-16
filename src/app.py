from vkbottle.bot import Bot
from vkbottle import API

from src.handlers import labelers
from src.handlers.wrapers import lw
from src.config_reader import api_config
from src.middlewares import CheckReg, ApiManager, CheckVip


api_list = (API(curr_api) for curr_api in api_config.values())
bot = Bot(loop_wrapper=lw)


for custom_labeler in labelers:
    bot.labeler.load(custom_labeler)


bot.labeler.message_view.register_middleware(CheckReg)
bot.labeler.message_view.register_middleware(ApiManager)
bot.labeler.message_view.register_middleware(CheckVip)
