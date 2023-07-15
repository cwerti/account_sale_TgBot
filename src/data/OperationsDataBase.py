import datetime

from src.data import db_session
from src.data.users import User
from src.data.subscription import Subscription
from src.data.history import History

from aiogram import types


def start_db():
    db_session.global_init('src/db/TestDB.sqlite')
    # add_subscription(['sasasasa'])


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
    sub = list(filter(flag_day, sub))  # фильтрация по оставшемуся времени
    sub = list(filter(lambda x: ostat(x) * x.price >= 100., sub))  # ограничение телеграмма
    sub = list(filter(lambda x: str(user_id) not in x.users_id, sub))  # убираем подписки, на которые user уже подписан
    sess.close()

    return [types.InlineKeyboardButton(
        text=f"{ostat(i)} дней {round(ostat(i) * i.price, 2)}р",
        callback_data=f"payment|{ostat(i)}|{round(ostat(i) * i.price, 2)}|{name_service}|{i.id}") for i in sub]


def buy_subscription(invoice_payload: str) -> bool:
    sub_id, user_tg_id, price = list(map(int, invoice_payload.split('|')))
    sess = db_session.create_session()
    sub = sess.get(Subscription, sub_id)

    if len(sub.users_id.split()) > 4:
        sess.close()
        return False

    user = sess.query(User).filter(User.tg_id == user_tg_id).first()
    operation = History(subscription_id=sub_id, user_id=user.id, price=float(f"{price // 100}.{price % 100}"))
    sess.add(operation)
    sess.flush()

    user.subscriptions_id += f" {sub.id}"
    sub.users_id += f" {user.id}"
    user.operations_id += f" {operation.id}"

    sess.commit()
    sess.close()
    return True


def get_one_sub(sub_id: int) -> list:
    sess = db_session.create_session()
    sub = sess.get(Subscription, sub_id)
    return [sub.name, sub.login, sub.password]


def get_operations(user_tg_id: int) -> str:
    sess = db_session.create_session()
    user = sess.query(User).filter(User.tg_id == user_tg_id).first()
    user_opers = user.operations_id
    op_user_ids = list(map(int, user_opers.split()))
    operations = sess.query(History).filter(History.id.in_(op_user_ids)).all()
    operations.sort(key=lambda x: x.created_date)
    result = ''

    count_oper = len(operations)
    if count_oper == 0:
        return "Вы не приобрели ни одного аккаунта("
    for i in range(count_oper):
        sub = sess.get(Subscription, operations[i].subscription_id)
        result += f"*{i + 1}) *{operations[i].created_date.replace(microsecond=0)} " \
                  f"Вы купили аккаунт на сервисе _{sub.name}_ длительностью {sub.duration} дней за " \
                  f"{operations[i].price} рублей.\n*Данные аккаунта =>\nЛогин: *{sub.login}\n*Пароль: *{sub.password}\n\n"
    result += 'Спасибо, что выбрали наш _Telegram-бот!_'
    print(result)
    return result


def add_subscription(data: list[str]):
    session = db_session.create_session()
    subscriptions = []

    for one_sub in data:
        info_sub = one_sub.split()
        login, password, name = info_sub[:3]
        duration, price = int(info_sub[3]), float(info_sub[4])
        created_date = info_sub[5] if len(info_sub) == 6 else datetime.datetime.now()
        subscriptions.append(Subscription(name=name, login=login, password=password,
                                          created_date=created_date, duration=duration, price=price))
    session.bulk_save_objects(subscriptions)
    # for i in [['123', '312', 'okko', 30, 133.3, datetime.date(2023, 7, 1)],
    #           ['777', '775', 'prem', 32, 6.66, datetime.date(2023, 7, 13)],
    #           ['gdg', 'zxc','kino', 65, 12.66,  datetime.date(2023, 7, 13)],
    #           ['7sf', 'pudge', 'ivi', 92, 13.33, datetime.date(2023, 6, 13)]]:
    #     l, g, n, d, p, c = i
    #     session.add(Subscription(name=n, price=p, created_date=c, login=l, password=g, duration=d))
    session.commit()
    session.close()

