import more_itertools as mit

import logging

import nest_asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types.message import ContentType
from aiogram.dispatcher import filters

from src.data.OperationsDataBase import add_user, get_subs, buy_subscription_check, \
    start_db, get_operations, buy_subscription_registration, add_subscription
import config

nest_asyncio.apply()

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())
logging.basicConfig(level=logging.INFO)


@dp.message_handler(commands="start", state="*")
async def smd_start(message: types.Message):
    add_user(message.from_id)
    text = f"""Привет, _{message.chat.first_name}_👋
С помощью этого бота вы сможете купить подписки для различных сервисов, таких как _kion, okko, sсarlet_ и др.

Для открытия меню нажмите /menu"""
    await bot.send_message(chat_id=message.chat.id, text=text, parse_mode="Markdown")


@dp.message_handler(commands="menu", state="*")
async def start_menu(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Meta", callback_data="meta0"))
    buttons = [
        [types.InlineKeyboardButton(text="💫список подписок💫",
                                    callback_data="subscription_list"),
         types.InlineKeyboardButton(text="💸продать аккаунт💸",
                                    callback_data="sale_account")],
        [
            types.InlineKeyboardButton(text="📱сертификат scarlet📱",
                                       callback_data="scarlett")
        ],
        [
            types.InlineKeyboardButton(text="🛒мои покупки🛒",
                                       callback_data="my_buy"),
            types.InlineKeyboardButton(text="💬поддержка💬",
                                       callback_data="help")
        ],
    ]
    if message['from']['id'] in config.admins_id:
        buttons.append([types.InlineKeyboardButton(text="добавить данные в БД",
                                                   callback_data="add_bd")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_photo(chat_id=message.chat.id, photo=types.InputFile(f"src/images/logo.jpg"))
    return await bot.send_message(chat_id=message.chat.id, text='Что будем делать❓',
                                  reply_markup=keyboard)


@dp.callback_query_handler(lambda call: call.data.startswith('menu'))
async def start_menu(call: types.CallbackQuery):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Meta", callback_data="meta0"))
    buttons = [
        [types.InlineKeyboardButton(text="💫список подписок💫",
                                    callback_data="subscription_list"),
         types.InlineKeyboardButton(text="💸продать аккаунт💸",
                                    callback_data="sale_account")],
        [
            types.InlineKeyboardButton(text="📱подписка scarlett📱",
                                       callback_data="scarlet")
        ],
        [
            types.InlineKeyboardButton(text="🛒мои покупки🛒",
                                       callback_data="my_buy"),
            types.InlineKeyboardButton(text="💬поддержка💬",
                                       callback_data="help")
        ],
    ]
    if call.message['from']['id'] in config.admins_id:
        buttons.append([types.InlineKeyboardButton(text="добавить данные в БД",
                                                   callback_data="add_bd")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_photo(chat_id=call.message.chat.id, photo=types.InputFile(f"src/images/logo.jpg"))
    return await bot.send_message(chat_id=call.message.chat.id, text='Что будем делать❓',
                                  reply_markup=keyboard)


@dp.callback_query_handler(lambda call: call.data.startswith('my_buy'))
async def my_buy(call: types.CallbackQuery):
    text = get_operations(call['from']['id'])
    await bot.send_message(chat_id=call.message.chat.id, text=text, parse_mode='Markdown')


@dp.callback_query_handler(lambda call: call.data.startswith('add_bd'))
async def information_add(call: types.CallbackQuery):
    text = """Отправьте текст формата:
    добавление в bd{Enter}
    login password имя-сервиса длительность-подписки цена-за-день дата-создания(по умолчанию сегодня){Enter}
    Например: *
    добавление в bd
    log1 pass1 name1 30 123.45 2023-07-13 00:00:00
    log2 pass2 name2 95 678.90*
    """
    await bot.send_message(chat_id=call.message.chat.id, text=text, parse_mode='Markdown')


@dp.message_handler(filters.Text(contains="добавление в bd", ignore_case=True))
async def text_example(message: types.Message):
    """она будет обрабатывать и добавлять данные в бд
       формат данных описан в функции выше
    """
    if message['from']['id'] in config.admins_id:
        text = add_subscription(message.text.split('\n')[1:])
        await bot.send_message(chat_id=message.chat.id, text=text, parse_mode="Markdown")
    else:
        await bot.send_message(chat_id=message.chat.id, text='такой команды не существует!')


@dp.callback_query_handler(lambda call: call.data.startswith('sale_account'))
async def sale_account(call: types.CallbackQuery):
    text = """Для продажи аккаунта обращайтесь к @HraVsu

для возврата в главное меню /menu"""
    await bot.send_message(chat_id=call.message.chat.id, text=text)


@dp.callback_query_handler(lambda call: call.data.startswith('scarlet'))
async def scarlett(call: types.CallbackQuery):
    text = """Для покупки обращайтесь к @HraVsu
обычный-600₽
двойной-900₽
моментальный-1400₽
сертификат на ipad(обычный)-300₽

для возврата в главное меню /menu"""
    await bot.send_photo(chat_id=call.message.chat.id, photo=types.InputFile(f"src/images/scarlet.png"))
    await bot.send_message(chat_id=call.message.chat.id, text=text)


@dp.callback_query_handler(lambda call: call.data.startswith('help'))
async def help_msg(call: types.CallbackQuery):
    text = """Вопросы о покупке @HraVsu
Вопросы/предложения по технической части @Qqqeeeq

для возврата в главное меню /menu"""
    await bot.send_message(chat_id=call.message.chat.id, text=text)


@dp.callback_query_handler(lambda call: call.data.startswith('subscription_list'))
async def subscription_list(call: types.CallbackQuery):
    buttons = [
        [types.InlineKeyboardButton(text="Wink",
                                    callback_data=f"service|Wink"),
         types.InlineKeyboardButton(text="Okko",
                                    callback_data=f"service|Okko"),
         types.InlineKeyboardButton(text="ivi",
                                    callback_data=f"service|ivi")
         ],
        [types.InlineKeyboardButton(text="Kion",
                                    callback_data=f"service|Kion"),
         types.InlineKeyboardButton(text="КиноПоиск",
                                    callback_data=f"service|КиноПоиск"),
         types.InlineKeyboardButton(text="Premier",
                                    callback_data=f"service|Premier")],
        [types.InlineKeyboardButton(text="Назад",
                                    callback_data=f"menu")
         ]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(chat_id=call.message.chat.id, text='Выберите нужный вам сервис✅',
                           reply_markup=keyboard)


@dp.callback_query_handler(lambda call: call.data.startswith('service'))
async def subscription_list(call: types.CallbackQuery):
    """
    выводит сервисы
    """
    name_service = call.data.split('|')[1]
    buttons = [
        [types.InlineKeyboardButton(text="меньше 30",
                                    callback_data=f"buy|0|{name_service}"),
         types.InlineKeyboardButton(text="от 30 до 90",
                                    callback_data=f"buy|1|{name_service}"),
         types.InlineKeyboardButton(text="больше 90",
                                    callback_data=f"buy|2|{name_service}")
         ]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_photo(chat_id=call.message.chat.id, photo=types.InputFile(f"src/images/{name_service}.png"))
    await bot.send_message(chat_id=call.message.chat.id, text='выберите количество дней подписки',
                           reply_markup=keyboard)


@dp.callback_query_handler(lambda call: call.data.startswith('buy'))
async def all_sub(call: types.CallbackQuery):
    """
    функция вывода доступных подписок
    days: если 0, то меньше или равно 30, если 1 то от 30 до 90, если 2 то больше или равно 90
    name_service: название сервиса
    """
    tmp = call.data.split('|')
    name_service = tmp[2]
    but = get_subs(int(tmp[1]), name_service, call['from']['id'])

    buttons = [
        *mit.batched(but, 3),
        [types.InlineKeyboardButton(text="назад", callback_data="subscription_list")
         ]
    ]
    text = 'выберите тариф подписки'
    if len(but) == 0:
        text = f"К сожалению, все подписки на сервис _{name_service}_ раскуплены."
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(chat_id=call.message.chat.id, text=text,
                           reply_markup=keyboard, parse_mode='Markdown')


@dp.callback_query_handler(lambda call: call.data.startswith('payment'))
async def buy_sub(call: types.CallbackQuery):
    tmp = call.data.split('|')
    day = tmp[1]
    price = int(float(tmp[2]) * 100)
    name_service = tmp[3]
    sub_id = int(tmp[4])
    PAYMENTS_PROVIDER_TOKEN = config.pay_token
    PRICE = types.LabeledPrice(label=f"Подписка на {day} дн.", amount=price)  # в копейках (руб)
    await bot.send_invoice(call.message.chat.id,
                           title=f"Подписка на {name_service}",
                           description=f"""Аккаунт с подпиской {name_service} на {day} дн.""",
                           provider_token=PAYMENTS_PROVIDER_TOKEN,
                           currency="rub",
                           is_flexible=False,
                           prices=[PRICE],
                           start_parameter="one-month-subscription",
                           payload=f"{sub_id}|{call['from']['id']}|{price}")


@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    flag = buy_subscription_check(pre_checkout_query.invoice_payload)
    return await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=flag, error_message=
    'К сожалению, кто-то уже успел купить данную подписку.\nПожалуйста, попробуйте приобрести другую')


@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: types.Message):
    inf = message.successful_payment
    name, login, password = buy_subscription_registration(inf.invoice_payload)
    await bot.send_message(message.chat.id,
                           f"_Поздравляем!_ Вы пробрели подписку на _{name}_ за "
                           f"_{inf.total_amount // 100},{inf.total_amount % 100}_ {inf.currency}!\n"
                           f"*Данные аккаунта =>\nЛогин:* {login}\n*Пароль:* {password}\n_До новых встреч!_\n\nДля возврата в меню /menu",
                           parse_mode='Markdown')


@dp.message_handler(content_types=ContentType.DOCUMENT)
async def qwe(message: types.Message):
    if message['from']['id'] in config.admins_id:
        file_id = message.document.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        await bot.download_file(file_path, "data.txt")
    else:
        await bot.send_message(message.chat.id,
                               f"К сожалению, такая команда отсутствует \n\nДля перехода в меню нажмите /menu")


if __name__ == "__main__":
    # Запуск бота
    start_db()
    executor.start_polling(dp, skip_updates=True)
