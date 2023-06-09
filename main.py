from src.app import bot, api_list
from vkbottle.bot import run_multibot


if __name__ == "__main__":
    run_multibot(bot, api_list)