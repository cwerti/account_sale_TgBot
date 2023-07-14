from src.data.db_session import SqlAlchemyBase
from sqlalchemy import Column, Integer, String


class User(SqlAlchemyBase):
    __tablename__ = 'Users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(Integer, nullable=False, unique=True)
    subscriptions_id = Column(String)

