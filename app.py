from dotenv import load_dotenv
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup
import sys
from keyboards.admin_keyboard import main_admin_keyboard
from keyboards.supervisor_keyboard import main_supervisor_keyboard

load_dotenv()

# Получить значение токена
TOKEN = os.getenv("TOKEN")

# Диспетчер
dp = Dispatcher()

ADMINS = [930555164]
SUPERVISOR = [930555164]

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    if message.from_user.id in ADMINS:
        await message.answer(f"Привет админ, {html.bold(message.from_user.full_name)}!",
                             reply_markup=main_admin_keyboard)
    elif message.from_user.id in SUPERVISOR:
        await message.answer(f"Привет староста, {html.bold(message.from_user.full_name)}!",
                             reply_markup=main_supervisor_keyboard)
    else:
        await message.answer(f"Привет, {html.bold(message.from_user.full_name)}!")


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
