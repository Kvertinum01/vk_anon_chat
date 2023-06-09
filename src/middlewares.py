from vkbottle import BaseMiddleware, API
from vkbottle.bot import Message

from src.repositories.user import UserRepository
from src import app
from src.kbs import reg_first_kb

from typing import Dict


start_commands = [
    "Начать", "Вернуться в старый чат", "Продолжить",
    "Ввести повторно", "Мужской", "Женский"
]


api_manager: Dict[int, API] = {}


class ApiManager(BaseMiddleware[Message]):
    async def pre(self):
        api_manager[self.event.from_id] = self.event.ctx_api


class CheckReg(BaseMiddleware[Message]):
    async def pre(self):
        curr_state = await app.bot.state_dispenser.get(self.event.peer_id)
        if curr_state is not None:
            return
        
        if self.event.text in start_commands:
            return
        
        user_rep = UserRepository(self.event.from_id)
        if not await user_rep.check_reg():
            await self.event.answer("Для начала пройдите регистрацию", keyboard=reg_first_kb)
            return self.stop("User didn't pass registration")
