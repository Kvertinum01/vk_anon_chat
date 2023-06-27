from sqlalchemy.ext.asyncio import AsyncSession, AsyncAttrs, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config_reader import DB_URL


engine = create_async_engine(DB_URL)
session = AsyncSession(bind=engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass