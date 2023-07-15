import datetime

from src.data import db_session
from src.data.users import User
from src.data.subscription import Subscription
from src.data.history import History

from aiogram import types


def start_DB():
    db_session.global_init('src/db/TestDB.sqlite')
    # add_Subscription()


def add_user(user_tg_id: int):
    session = db_session.create_session()
    res = session.query(User).filter(User.tg_id == user_tg_id).first()
    if not res:
        user = User(tg_id=user_tg_id)
        session.add(user)
        session.commit()
    session.close()


def get_subs(button_index: int, name_service: str, user_tg_id: int) -> list:
    ostat = lambda x: int(x.duration - (datetime.datetime.now() - x.created_date).days)
    flag_day = [lambda x: ostat(x) < 31, lambda x: 30 < ostat(x) < 91, lambda x: ostat(x) > 90][button_index]

    sess = db_session.create_session()
    user_id = sess.query(User).filter(User.tg_id == user_tg_id).first().id
    sub = sess.query(Subscription).filter(Subscription.name == name_service).all()  # фильтрация только по имени
    sub = list(filter(flag_day, sub))  # фильтрация по оставшемуся времени(я заколебался в потоке пытаться сделать)
    sub = list(filter(lambda x: ostat(x) * x.price >= 100., sub))  # ограничение телеграмма
    sub = list(filter(lambda x: str(user_id) not in x.users_id, sub))  # убираем подписки, на которые user уже подписан
    sess.close()
    return [types.InlineKeyboardButton(
        text=f"{ostat(i)} дней {ostat(i) * i.price}р",
        callback_data=f"payment|{ostat(i)}|{ostat(i) * i.price}|{name_service}|{i.id}") for i in sub]


def Buy_Subscription(invoice_payload: str) -> bool:
    sub_id, user_tg_id, price = list(map(int, invoice_payload.split('|')))
    sess = db_session.create_session()
    sub = sess.get(Subscription, sub_id)

    if len(sub.users_id.split()) > 4:
        sess.close()
        return False

    user = sess.query(User).filter(User.tg_id == user_tg_id).first()
    operation = History(subscription_id=sub_id, user_id=user.id, price=float(f"{price // 100}.{price % 100}"))
    sess.add(operation)
    user.subscriptions_id += f" {sub.id}"
    sub.users_id += f" {user.id}"
    user.operations_id += f" {operation.id}"
    sess.commit()
    sess.close()
    return True


def add_Subscription():
    session = db_session.create_session()
    for i in [['okko', 133.3, 30, datetime.date(2023, 7, 1)], ['prem', 6.66, 32, datetime.date(2023, 7, 13)],
             ['kino', 12.66, 65, datetime.date(2023, 7, 13)], ['ivi', 13.33, 92, datetime.date(2023, 6, 13)]]:
        n, p, d, c = i
        session.add(Subscription(name=n, price=p, duration=d, created_date=c))
    session.commit()
    session.close()
    return
