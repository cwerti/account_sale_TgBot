import datetime

from src.data.db_session import SqlAlchemyBase
from sqlalchemy import Column, Integer, DateTime, String


class Subscription(SqlAlchemyBase):
    __tablename__ = 'Subscriptions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.datetime.now)
    duration = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    users_id = Column(String)


