import datetime

from src.data.db_session import SqlAlchemyBase
from sqlalchemy import Column, Integer, DateTime, Float


class History(SqlAlchemyBase):
    __tablename__ = 'History'

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.datetime.now)
    user_id = Column(Integer, nullable=False)
    subscription_id = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
