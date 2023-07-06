from src.models.user_model import User
from src.models.db import engine

from typing import Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import sessionmaker


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
    
    
    async def new(self, age: int):
        async_session = sessionmaker(
            engine, expire_on_commit=False, class_=AsyncSession
        )
        async with async_session() as session:
            async with session.begin():
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
    

    async def end_reg(self):
        async_session = sessionmaker(
            engine, expire_on_commit=False, class_=AsyncSession
        )
        async with async_session() as session:
            await session.execute(
                update(User)
                .where(and_(User.id == self.user_id, User.platform == self.platform))
                .values(end_reg = True)
            )
            await session.commit()


    async def update_age(self, new_age: int):
        async_session = sessionmaker(
            engine, expire_on_commit=False, class_=AsyncSession
        )
        async with async_session() as session:
            await session.execute(
                update(User)
                .where(and_(User.id == self.user_id, User.platform == self.platform))
                .values(age=new_age)
            )
            await session.commit()


    async def update_sex(self, new_sex: int):
        async_session = sessionmaker(
            engine, expire_on_commit=False, class_=AsyncSession
        )
        async with async_session() as session:
            await session.execute(
                update(User)
                .where(and_(User.id == self.user_id, User.platform == self.platform))
                .values(sex=new_sex)
            )
            await session.commit()
