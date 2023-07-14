import datetime

from src.data import db_session
from src.data.users import User
from src.data.subscription import Subscription
from src.data.history import History
import more_itertools as mit
from sqlalchemy import and_, all_

import logging
from aiogram import Bot, Dispatcher, executor, types

from aiogram.types.message import ContentType
import config
import nest_asyncio
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

nest_asyncio.apply()

# Объект бота
bot = Bot(token=config.BOT_TOKEN)
# Диспетчер для бота
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())
# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)


@dp.message_handler(commands="start", state="*")
async def cmd_start(message: types.Message):
    """
    приветственное сообщение
    """
    session = db_session.create_session()
    res = session.query(User).filter(User.tg_id == message.from_id).first()
    if not res:
        user = User(tg_id=message.from_id)
        session.add(user)
        session.commit()
    session.close()
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Meta", callback_data="meta0"))
    buttons = [
        [types.InlineKeyboardButton(text="спиок доступных подписок",
                                    callback_data="subscription_list"),
         types.InlineKeyboardButton(text="продать аккаунт",
                                    callback_data="sale_account")],
        [
            types.InlineKeyboardButton(text="мои покупки",
                                       callback_data="my_buy")
        ],
    ]

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return await bot.send_message(chat_id=message.chat.id, text='выберите героя о котром хотите узнать подробрнее',
                                  reply_markup=keyboard)


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
    days: если 1, то меньше или равно 30, если 2, то от 30 до 90, если 3 то больше или равно 90
    name_servise: название сервиса
    """
    tmp = call.data.split('|')
    vir = lambda x: x.duration - (datetime.datetime.now() - x.created_date).days
    flag = [lambda x: vir(x) < 31, lambda x: 30 < vir(x) < 91, lambda x: vir(x) > 90][int(tmp[1]) - 1]
    name_servise = 'кинопоиск'  # tmp[2] пока оставь так, в данной версии у тебя пока что стоит только kino

    sess = db_session.create_session()
    sub = sess.query(Subscription).filter(Subscription.name == name_servise).all()  # фильтрация только по имени
    print(sub[0].duration, sub[0].name, sub[0].created_date)
    sub = list(filter(flag, sub))  # фильтрация по оставшемуся времени(я заколебался в потоке пытаться сделать)
    print('aaa', sub)
    but = []
    for i in sub:
        ostat = (datetime.datetime.now().date() - i.created_date.date()).days
        but.append(types.InlineKeyboardButton(text=f"{ostat} дней {ostat * i.price}р",
                                                  callback_data=f"payment|{ostat}|{ostat * i.price}"))
    but = list(mit.chunked(but, 3))
    print(but)
    buttons = [
        *but,  # ЧТО ТУТ НЕ ТАК? Я УСТАЛ...(ПЕРЕПРОБОВАЛ ВСЕ КОМБИНАЦИИ)
        [types.InlineKeyboardButton(text="назад", callback_data="subscription_list")
         ]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_photo(chat_id=call.message.chat.id, photo=types.InputFile(f"src/images/{name_servise}.png"))
    await bot.send_message(chat_id=call.message.chat.id, text='выберите тариф подписки',
                           reply_markup=keyboard)


@dp.callback_query_handler(lambda call: call.data.startswith('payment'))
async def all_sub(call: types.CallbackQuery):
    PAYMENTS_PROVIDER_TOKEN = '381764678:TEST:61580'
    PRICE = types.LabeledPrice(label="Подписка на 1 месяц", amount=500 * 100)  # в копейках (руб)
    await bot.send_message(call.message.chat.id, "Тестовый платеж!!!")
    await bot.send_invoice(call.message.chat.id,
                           title="Подписка на бота",
                           description="Активация подписки на бота на 1 месяц",
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
    payment_info = message.successful_payment.to_python()

    await bot.send_message(message.chat.id,
                           f"Платеж на сумму {message.successful_payment.total_amount // 100} {message.successful_payment.currency} прошел успешно!!!")


if __name__ == "__main__":
    # Запуск бота
    db_session.global_init('src/db/TestDB.sqlite')
    session = db_session.create_session()
    # for i in [['окко', 13.33, 30, datetime.date(2023, 7, 1)], ['премьер', 6.66, 32, datetime.date(2023, 7, 13)],
    #          ['кинопоиск', 6.66, 65, datetime.date(2023, 7, 13)], ['иви', 13.33, 92, datetime.date(2023, 6, 13)]]:
    #     n, p, d, c = i
    #     session.add(Subscription(name=n, price=p, duration=d, created_date=c))
    # session.commit()
    session.close()
    executor.start_polling(dp, skip_updates=True)


