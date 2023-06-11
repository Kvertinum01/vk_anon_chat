from src.models.db import session
from src.models.user_model import User

from typing import Optional

from sqlalchemy import select, update, and_


class UserRepository:
    def __init__(self, user_id: int, platform = "vk"):
        self.user_id = int(user_id)
        self.platform = platform


    async def get(self) -> Optional[User]:
        query = select(User).where(and_(User.id == self.user_id, User.platform == self.platform))
        ex_res = await session.execute(query)
        user: Optional[User] = ex_res.scalar()
        return user
    
    
    async def new(self, age: int):
        user_obj = User(
            id=self.user_id,
            age=age,
            platform=self.platform
        )
        session.add(user_obj)
        await session.commit()


    async def check_reg(self):
        user = await self.get()

        if user is None:
            return False
        if user.end_reg == False:
            return False
        
        return True
    

    async def set_vip(self, sub_id: str):
        await session.execute(
            update(User)
            .where(and_(User.id == self.user_id, User.platform == self.platform))
            .values(
                vip_status = True,
                sub_id = sub_id
            )
        )
        await session.commit()


    async def del_vip(self):
        await session.execute(
            update(User)
            .where(and_(User.id == self.user_id, User.platform == self.platform))
            .values(
                vip_status = False,
            )
        )
        await session.commit()
    

    async def end_reg(self):
        await session.execute(
            update(User)
            .where(and_(User.id == self.user_id, User.platform == self.platform))
            .values(end_reg = True)
        )
        await session.commit()


    async def update_age(self, new_age: int):
        await session.execute(
            update(User)
            .where(and_(User.id == self.user_id, User.platform == self.platform))
            .values(age=new_age)
        )
        await session.commit()


    async def update_sex(self, new_sex: int):
        await session.execute(
            update(User)
            .where(and_(User.id == self.user_id, User.platform == self.platform))
            .values(sex=new_sex)
        )
        await session.commit()
