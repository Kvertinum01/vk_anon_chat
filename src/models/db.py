from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config_reader import DB_URL


engine = create_async_engine(DB_URL)


class Base(AsyncAttrs, DeclarativeBase):
    pass