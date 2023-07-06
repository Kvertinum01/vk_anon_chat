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
    age = Column(Integer, default=16)
    created_at = Column(DateTime, default=datetime.now)
    platform = Column(String(5), default="vk")
    end_reg = Column(Boolean, default=False)
    vip_status = Column(Boolean, default=False)
    sub_id = Column(String(32), default="")
    exp_vip = Column(DateTime, default=datetime.now)


    def __repr__(self):
        return f'<User: {self.id}>'
