import datetime

from src.data import db_session
from src.data.users import User
from src.data.subscription import Subscription
from src.data.history import History
import more_itertools as mit
from sqlalchemy import and_, all_

import logging

import nest_asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types.message import ContentType

import config

nest_asyncio.apply()

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())
logging.basicConfig(level=logging.INFO)


@dp.message_handler(commands="start", state="*")
async def smd_start(message: types.Message):
    text = f"""Привет, _{message.chat.first_name}_👋
С помошью этого бота вы сможете купить подписки для различных сервисов, таких как _kion, okko, skarlett_ и д. р.

Для открытия меню нажмите /menu"""
    await bot.send_message(chat_id=message.chat.id, text=text, parse_mode="Markdown")


@dp.message_handler(commands="menu", state="*")
async def start_menu(message: types.Message):
    session = db_session.create_session()
    res = session.query(User).filter(User.tg_id == message.from_id).first()
    if not res:
        user = User(tg_id=message.from_id)
        session.add(user)
        session.commit()
    session.close()
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Meta", callback_data="meta0"))
    if message['from']['id'] != 1076674186:
        buttons = [
            [types.InlineKeyboardButton(text="💫спиок подписок💫",
                                        callback_data="subscription_list"),
             types.InlineKeyboardButton(text="💸продать аккаунт💸",
                                        callback_data="sale_account")],
            [
                types.InlineKeyboardButton(text="📱подписка scarlett📱",
                                           callback_data="scarlett")
            ],
            [
                types.InlineKeyboardButton(text="🛒мои покупки🛒",
                                           callback_data="my_buy"),
                types.InlineKeyboardButton(text="💬поддержка💬",
                                           callback_data="help")
            ]
        ]
    else:
        buttons = [
            [types.InlineKeyboardButton(text="💫спиок подписок💫",
                                        callback_data="subscription_list"),
             types.InlineKeyboardButton(text="💸продать аккаунт💸",
                                        callback_data="sale_account")],
            [
                types.InlineKeyboardButton(text="📱подписка scarlett📱",
                                           callback_data="scarlett")
            ],
            [
                types.InlineKeyboardButton(text="🛒мои покупки🛒",
                                           callback_data="my_buy"),
                types.InlineKeyboardButton(text="💬поддержка💬",
                                           callback_data="help")
            ],
            [types.InlineKeyboardButton(text="добавить данные в БД",
                                        callback_data="add_bd")
             ]
        ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return await bot.send_message(chat_id=message.chat.id, text='выберите героя о котром хотите узнать подробрнее',
                                  reply_markup=keyboard)


@dp.callback_query_handler(lambda call: call.data.startswith('add_bd'))
async def sale_account(call: types.CallbackQuery):
    text = """Отправьте файл формата txt с поляи:
    имя дата_создания(по умолчанию текущий день) длительность_подписки цена_за_день 
    """
    await bot.send_message(chat_id=call.message.chat.id, text=text)


@dp.callback_query_handler(lambda call: call.data.startswith('sale_account'))
async def sale_account(call: types.CallbackQuery):
    text = """Для продажи аккаунта обращайтесь к @HraVsu

для возврата в главное меню /menu"""
    await bot.send_message(chat_id=call.message.chat.id, text=text)


@dp.callback_query_handler(lambda call: call.data.startswith('scarlett'))
async def scarlett(call: types.CallbackQuery):
    text = """Для покупки обращайтесь к @HraVsu
обычный-600₽
двойной-900₽
моментальный-1400₽
сертификат на ipad(обычный)-300₽

для возврата в главное меню /menu"""
    await bot.send_photo(chat_id=call.message.chat.id, photo=types.InputFile(f"src/images/scarlett.png"))
    await bot.send_message(chat_id=call.message.chat.id, text=text)


@dp.callback_query_handler(lambda call: call.data.startswith('help'))
async def help_msg(call: types.CallbackQuery):
    text = """Вопросы о покупке @HraVsu
Вопросы/предложения по технической части @Qqqeeeq

для возврата в главное меню /menu"""
    await bot.send_message(chat_id=call.message.chat.id, text=text)


@dp.callback_query_handler(lambda call: call.data.startswith('subscription_list'))
async def subscription_list(call: types.CallbackQuery):
    """
    выводит все сервисы
    """
    for i in config.service_lst:
        buttons = [
            [types.InlineKeyboardButton(text="меньше 30",
                                        callback_data=f"buy|1|{i}"),
             types.InlineKeyboardButton(text="от 30 до 90",
                                        callback_data=f"buy|2|{i}"),
             types.InlineKeyboardButton(text="больше 90",
                                        callback_data=f"buy|3|{i}")
             ]
        ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await bot.send_photo(chat_id=call.message.chat.id, photo=types.InputFile(f"src/images/{i}.png"))
        await bot.send_message(chat_id=call.message.chat.id, text='выберите количество дней подписки',
                               reply_markup=keyboard)


@dp.callback_query_handler(lambda call: call.data.startswith('buy'))
async def all_sub(call: types.CallbackQuery):
    """
    функция выода доступных подписок
    days: если 1, то меньше или равно 30, если 2 то от 30 до 90, если 3 то больше или равно 90
    name_servise: название сервиса
    """
    tmp = call.data.split('|')
    vir = lambda x: x.duration - (datetime.datetime.now() - x.created_date).days
    flag = [lambda x: vir(x) < 31, lambda x: 30 < vir(x) < 91, lambda x: vir(x) > 90][int(tmp[1]) - 1]
    name_servise = 'кинопоиск'  # tmp[2] пока оставь так, в данной версии у тебя пока что стоит только kino

    sess = db_session.create_session()
    sub = sess.query(Subscription).filter(Subscription.name == name_servise).all()  # фильтрация только по имени
    sub = list(filter(flag, sub))  # фильтрация по оставшемуся времени(я заколебался в потоке пытаться сделать)
    sess.close()
    but = []
    name_servise = 'kino'  # для теста
    for i in sub:
        ostat = (datetime.datetime.now().date() - i.created_date.date()).days
        but.append(types.InlineKeyboardButton(text=f"{ostat} дней {int(ostat * i.price)}р",
                                                  callback_data=f"payment|{ostat}|{int(ostat * i.price)}|{name_servise}"))
    buttons = [
        [types.InlineKeyboardButton(text=f"{12} дней {120}р",
                                                  callback_data=f"payment|{12}|{120}|{name_servise}"),
         but[0]],
        [types.InlineKeyboardButton(text="назад", callback_data="subscription_list")
         ]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_photo(chat_id=call.message.chat.id, photo=types.InputFile(f"src/images/{name_servise}.png"))  #
    await bot.send_message(chat_id=call.message.chat.id, text='выберите тариф подписки',
                           reply_markup=keyboard)


@dp.callback_query_handler(lambda call: call.data.startswith('payment'))
async def all_sub(call: types.CallbackQuery):
    tmp = call.data.split('|')
    day = tmp[1]
    price = tmp[2]
    name_servise = tmp[3]
    PAYMENTS_PROVIDER_TOKEN = '381764678:TEST:61580'
    PRICE = types.LabeledPrice(label=f"Подписка на {day} месяц", amount=int(price) * 100)  # в копейках (руб)
    await bot.send_invoice(call.message.chat.id,
                           title=f"Подписка на {name_servise}",
                           description=f"""Аккаунт с подпиской {name_servise} на {day} дней""",
                           provider_token=PAYMENTS_PROVIDER_TOKEN,
                           currency="rub",
                           is_flexible=False,
                           prices=[PRICE],
                           start_parameter="one-month-subscription",
                           payload="test-invoice-payload")


@dp.pre_checkout_query_handler(lambda query: True)
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    print("SUCCESSFUL PAYMENT:")
    inf = message.successful_payment
    payment_info = inf.to_python()
    for k, v in payment_info.items():
        print(f"{k} = {v}")
    await bot.send_message(message.chat.id,
                           f"Платеж на сумму {inf.total_amount // 100} {inf.currency} прошёл успешно!!!")


@dp.message_handler(content_types=ContentType.DOCUMENT)
async def qwe(message: types.Message):
    if message['from']['id'] != 1076674186:
        file_id = message.document.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        await bot.download_file(file_path, "data.txt")
    else:
        await bot.send_message(message.chat.id,
                               f"К сожалению такая команда отсутствует \n\nДля перехода в менб нажмите /menu")


if __name__ == "__main__":
    # Запуск бота
    db_session.global_init('src/db/TestDB.sqlite')
    session = db_session.create_session()
    # for i in [['окко', 13.33, 30, datetime.date(2023, 7, 1)], ['премьер', 6.66, 32, datetime.date(2023, 7, 13)],
    #          ['кинопоиск', 12.66, 65, datetime.date(2023, 7, 13)], ['иви', 13.33, 92, datetime.date(2023, 6, 13)]]:
    #     n, p, d, c = i
    #     session.add(Subscription(name=n, price=p, duration=d, created_date=c))
    # session.commit()
    session.close()
    executor.start_polling(dp, skip_updates=True)
