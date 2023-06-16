from src.models.user_model import User
from src.repositories import UserRepository

from typing import Optional, Union, Dict, List
from datetime import datetime


class ChatManager:
    def __init__(self, platform = "vk"):
        self._active_chats: List[List[int]] = []
        self._queue: List[User] = []
        self._prefers: Dict[int, int] = {}
        self._platform = platform
        self._daily_chats: Dict[int, Dict[str, Union[int, datetime]]] = {}


    async def find_companion(self, user_id: int, sex_prefer: Optional[int] = None) -> Optional[User]:
        user_rep = UserRepository(user_id, self._platform)
        user_inf = await user_rep.get()

        for curr_user in self._queue:
            if sex_prefer:
                if curr_user.sex != sex_prefer:
                    continue
            if self._prefers.get(curr_user.id):
                if self._prefers[curr_user.id] != user_inf.sex:
                    continue
            if user_inf.age - 5 < curr_user.age < user_inf.age + 5:
                self._queue.remove(curr_user)
                self.new_chat([user_inf.id, curr_user.id])
                self.set_daily_chat([user_inf, curr_user])
                return curr_user

        if sex_prefer:
            self._prefers[user_id] = sex_prefer
        return self._queue.append(user_inf)
    

    def set_daily_chat(self, user_infs: List[User]):
        for curr_user in user_infs:
            if curr_user.vip_status:
                continue
            self._daily_chats[curr_user.id]["limit"] += 1

    def check_daily_chats(self, user_id: int, vip_status: bool) -> bool:
        if vip_status:
            return False
        
        dt = datetime.now()
        if user_id not in self._daily_chats:
            self._daily_chats[user_id] = {"date": dt, "limit": 0}
            return False
        
        curr_info = self._daily_chats[user_id]

        if curr_info["date"].day != dt.day:
            self._daily_chats[user_id] = {"date": dt, "limit": 0}
            return False
        
        return curr_info["limit"] > 29
    

    def check_queue(self, user_id: int):
        for curr_user in self._queue:
            if curr_user.id == user_id:
                return True
        return False
    

    def leave_queue(self, user_id: int):
        for curr_user in self._queue:
            if curr_user.id != user_id:
                continue
            self._queue.remove(curr_user)
            return True
        return False


    def new_chat(self, user_ids: List[int]):
        self._active_chats.append(user_ids)


    def remove_active_chat(self, user_id):
        for curr_chat in self._active_chats:
            if user_id in curr_chat:
                self._active_chats.remove(curr_chat)
                break

    def get_active_user(self, user_id: int) -> Optional[int]:
        for curr_chat in self._active_chats:
            if user_id in curr_chat:
                tmp_chat = curr_chat.copy()
                tmp_chat.remove(user_id)
                return tmp_chat[0]
        return None


    def check_active_chats(self, user_id: int):
        for curr_chat in self._active_chats:
            if user_id in curr_chat:
                return True
        return False
