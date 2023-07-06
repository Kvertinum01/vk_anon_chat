from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, and_

from typing import Optional
from datetime import datetime

from src.config_reader import DB_URL
from src.models.user_model import User


engine = create_async_engine(DB_URL)
    

class UserRepository:
    def __init__(self, user_id: int, platform = "vk"):
        self.user_id = int(user_id)
        self.platform = platform


    async def get(self) -> Optional[User]:
        async_session = sessionmaker(
            engine, expire_on_commit=False, class_=AsyncSession
        )
        async with async_session() as session:
            query = select(User).where(and_(User.id == self.user_id, User.platform == self.platform))
            ex_res = await session.execute(query)
            user: Optional[User] = ex_res.scalar()
            return user
    
    async def check_reg(self):
        user = await self.get()

        if user is None:
            return False
        if user.end_reg == False:
            return False
        
        return True
    
    async def set_vip(self, sub_id: str, exp_date: datetime):
        async_session = sessionmaker(
            engine, expire_on_commit=False, class_=AsyncSession
        )
        async with async_session() as session:
            await session.execute(
                update(User)
                .where(and_(User.id == self.user_id, User.platform == self.platform))
                .values(
                    vip_status = True,
                    sub_id = sub_id,
                    exp_vip = exp_date,
                )
            )
            await session.commit()

    async def set_exp(self, exp_date: datetime):
        async_session = sessionmaker(
            engine, expire_on_commit=False, class_=AsyncSession
        )
        async with async_session() as session:
            await session.execute(
                update(User)
                .where(and_(User.id == self.user_id, User.platform == self.platform))
                .values(
                    exp_vip = exp_date,
                )
            )
            await session.commit()