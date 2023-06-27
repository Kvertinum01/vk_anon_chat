from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import QueuePool

from src.config_reader import DB_URL


engine = create_async_engine(DB_URL, poolclass=QueuePool)
Base = declarative_base()
session = AsyncSession(bind=engine, expire_on_commit=False)