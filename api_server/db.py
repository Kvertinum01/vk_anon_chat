from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import (
    select, update, and_,
    Column,
    Integer,
    String,
    DateTime,
    Boolean
)

from typing import Optional
from datetime import datetime

from src.config_reader import DB_URL


engine = create_async_engine(DB_URL)
session = AsyncSession(bind=engine, autoflush=False, autocommit=True)
Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, nullable=False, unique=True)
    sex = Column(Integer, default=1)
    age = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    platform = Column(String(5), default="vk")
    end_reg = Column(Boolean, default=False)
    vip_status = Column(Boolean, default=False)
    sub_id = Column(String(32), default="")


    def __repr__(self):
        return f'<User: {self.id}>'
    

class UserRepository:
    def __init__(self, user_id: int, platform = "vk"):
        self.user_id = int(user_id)
        self.platform = platform


    async def get(self) -> Optional[User]:
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