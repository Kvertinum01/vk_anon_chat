from sqlalchemy import select, or_, and_

from src.models.user_model import User
from src.repositories import UserRepository

from typing import Optional, List


class ChatManager:
    def __init__(self):
        self._active_chats: List[List[int]] = []
        self._queue: List[User] = []


    async def find_companion(self, user_id: int, platform = "vk") -> Optional[User]:
        user_rep = UserRepository(user_id, platform)
        user_inf = await user_rep.get()

        for curr_user in self._queue:
            if curr_user.sex == user_inf.sex:
                continue
            if user_inf.age - 5 < curr_user.age < user_inf.age + 5:
                self._queue.remove(curr_user)
                self.new_chat([user_inf.id, curr_user.id])
                return curr_user

        return self._queue.append(user_inf)
    

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
