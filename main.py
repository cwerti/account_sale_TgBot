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
    days: если 1, то меньше или равно 30, если 2б то от 30 до 90, если 3 то больше или равно 90
    name_servise: название сервиса
    """
    tmp = call.data.split('|')
    days = tmp[1]
    name_servise = tmp[2]
    buttons = [
        [types.InlineKeyboardButton(text="29 дней 290р",
                                    callback_data=f"payment|29|290"),
         types.InlineKeyboardButton(text="10 дней 100р",
                                    callback_data=f"payment10|100"),
         types.InlineKeyboardButton(text="17 дней 170р",
                                    callback_data=f"payment|17|170")
         ],
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
    executor.start_polling(dp, skip_updates=True)
