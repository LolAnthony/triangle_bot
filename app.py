from os import getenv

from dotenv import load_dotenv
from os import getenv
import asyncio
import logging
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup
import sys

from database.database import Database
from keyboards.admin_keyboard import main_admin_keyboard
from keyboards.supervisor_keyboard import main_supervisor_keyboard
from handlers import admin, supervisor, resident
load_dotenv()

# Получить значение токена
TOKEN = getenv("TOKEN")
DEV = getenv("DEV") == "TRUE"
CONNECTION_STRING = getenv("CONNECTION_STRING")

# Диспетчер
dp = Dispatcher()
dp.include_routers(admin.router, supervisor.router, resident.router)

ADMINS = []
SUPERVISOR = [930555164]

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    # TODO проверка на роли, переделать из БД
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

    my_db = Database(CONNECTION_STRING)

    if DEV:
        if not await my_db.is_exist():
            await my_db.initialize()

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
