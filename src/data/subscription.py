import datetime

from src.data.db_session import SqlAlchemyBase
from sqlalchemy import Column, Integer, DateTime, String, Float


class Subscription(SqlAlchemyBase):
    __tablename__ = 'Subscriptions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    created_date = Column(DateTime, default=datetime.datetime.now)
    duration = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    users_id = Column(String, default=' ')


