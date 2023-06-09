from os import getenv

from dotenv import load_dotenv
load_dotenv()


BOT_TOKEN = getenv("BOT_TOKEN")
BOT_TOKEN_2 = getenv("BOT_TOKEN_2")
DB_URL = getenv("DB_URL")