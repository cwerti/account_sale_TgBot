from src.data import db_session
from src.data.users import User

if __name__ == '__main__':
    db_session.global_init('src/db/TestDB.sqlite')
    session = db_session.create_session()
    user = User(tg_id=123123)
    session.add(user)
    session.commit()
