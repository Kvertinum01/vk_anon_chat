import json

from os import getenv
from datetime import timedelta
from typing import List, Dict, Union

from dotenv import load_dotenv
load_dotenv()


DB_URL = getenv("DB_URL")
PAY_TOKEN = getenv("PAY_TOKEN")


with open("api_config.json") as f:
    api_config: Dict[str, str] = json.load(f)


API_ENDPOINT = "https://api.comby.pro"

sub_info = {
    0: {"next": 399, "interval": "Week", "period": 2, "end": timedelta(hours=1)},
    1: {"next": 399, "interval": "Week", "period": 2, "end": timedelta(hours=36)},
    2: {"next": 399, "interval": "Week", "period": 2, "end": timedelta(weeks=2)},
    3: {"next": 1990, "interval": "Month", "period": 12, "end": timedelta(days=365)}
}


rates: List[Dict[str, Union[int, str]]] = [
    {
        "amount": 1, "desc": "Вип статус на 1 час",
        "confirm": True, "sub_id": 0,
    },
    {
        "amount": 9, "desc": "Вип статус на 36 часов",
        "confirm": False, "sub_id": 1,
    },
    {
        "amount": 199, "desc": "Вип статус на 1 неделю",
        "confirm": False, "sub_id": 2,
    },
    {
        "amount": 1990, "desc": "Вип статус на 365 дней",
        "confirm": False, "sub_id": 3,
    }
]
