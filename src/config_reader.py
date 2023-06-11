import json

from os import getenv
from datetime import timedelta
from typing import List, Dict, Union

from dotenv import load_dotenv
load_dotenv()


BOT_TOKEN = getenv("BOT_TOKEN")
BOT_TOKEN_2 = getenv("BOT_TOKEN_2")
DB_URL = getenv("DB_URL")
PAY_TOKEN = getenv("PAY_TOKEN")

sub_info = {
    0: {"interval": "Week", "period": 2, "end": timedelta(hours=1)},
    1: {"interval": "Week", "period": 2, "end": timedelta(hours=36)},
    2: {"interval": "Week", "period": 2, "end": timedelta(weeks=2)},
    3: {"interval": "Month", "period": 12, "end": timedelta(days=365)}
}

rates: List[Dict[str, Union[int, str]]] = [
    {
        "amount": 1, "desc": "Вип статус на 1 час",
        "confirm": True, "json_data": json.dumps({"sub_id": 0})
    },
    {
        "amount": 9, "desc": "Вип статус на 36 часов",
        "confirm": False, "json_data": json.dumps({"sub_id": 1})
    },
    {
        "amount": 199, "desc": "Вип статус на 1 неделю",
        "confirm": False, "json_data": json.dumps({"sub_id": 2})
    },
    {
        "amount": 1990, "desc": "Вип статус на 365 дней",
        "confirm": False, "json_data": json.dumps({"sub_id": 3})
    }
]
