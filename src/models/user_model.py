from src.models.db import Base

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean
)

from datetime import datetime


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, nullable=False, unique=True)
    sex = Column(Integer, default=1)
    age = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    platform = Column(String(5), default="vk")
    end_reg = Column(Boolean, default=False)


    def __repr__(self):
        return f'<User: {self.id}>'
