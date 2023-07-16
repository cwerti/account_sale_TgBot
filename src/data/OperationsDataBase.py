import datetime

from src.data import db_session
from src.data.users import User
from src.data.subscription import Subscription
from src.data.history import History

from aiogram import types

createded = False


def start_db():
    db_session.global_init('src/db/TestDB.sqlite')
    if createded:
        t = add_subscription(['sasasasa'])


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


def buy_subscription_check(invoice_payload: str) -> bool:
    sub_id, _, _ = list(map(int, invoice_payload.split('|')))
    sess = db_session.create_session()
    sub = sess.get(Subscription, sub_id)
    sess.close()

    if len(sub.users_id.split()) > 3:
        return False
    return True


def buy_subscription_registration(invoice_payload: str) -> list:
    sub_id, user_tg_id, price = list(map(int, invoice_payload.split('|')))
    sess = db_session.create_session()
    sub = sess.get(Subscription, sub_id)

    user = sess.query(User).filter(User.tg_id == user_tg_id).first()
    operation = History(subscription_id=sub_id, user_id=user.id, price=float(f"{price // 100}.{price % 100}"))
    sess.add(operation)
    sess.flush()

    user.subscriptions_id += f" {sub.id}"
    user.operations_id += f" {operation.id}"
    sub.users_id += f" {user.id}"
    sess.flush()
    name, login, password = sub.name, sub.login, sub.password
    sess.commit()
    sess.close()
    return [name, login, password]


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
    return result


def add_subscription(data: list[str]) -> str:
    session = db_session.create_session()
    try:
        if not createded:
            subscriptions = []

            for one_sub in data:
                info_sub = one_sub.split()
                login, password, name = info_sub[:3]
                duration, price = int(info_sub[3]), float(info_sub[4])
                created_date = datetime.datetime.now().replace(microsecond=0)
                if len(info_sub) == 6:
                    created_date = datetime.datetime.strptime(info_sub[5], "%Y-%m-%d %H:%M:%S")

                subscriptions.append(Subscription(name=name, login=login, password=password,
                                                  created_date=created_date, duration=duration, price=price))
            session.bulk_save_objects(subscriptions)
        else:
            for i in [['123', '312', 'okko', 30, 133.3, datetime.datetime(2023, 7, 1)],
                      ['777', '775', 'premier', 32, 6.66, datetime.datetime(2023, 7, 13)],
                      ['gdg', 'zxc','КиноПоиск', 65, 12.66,  datetime.datetime(2023, 7, 13)],
                      ['7sf', 'pudge', 'ivi', 92, 13.33, datetime.datetime(2023, 6, 13)],
                      ['asds', 'nameee', 'wink', 967, 10.33, datetime.datetime(2023, 6, 13)],
                      ['bbbb', 'gfggf', 'kion', 123, 13.33, datetime.datetime(2023, 5, 13)]]:
                l, g, n, d, p, c = i
                session.add(Subscription(name=n, price=p, created_date=c, login=l, password=g, duration=d))
        session.commit()
        return 'данные успешно добавлены!'
    except:
        return '*Данные некорректны.* _Каждую подписку пишите с новой строки!_'
    finally:
        session.close()

