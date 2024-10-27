from os import getenv, remove

from aiogram.fsm.context import FSMContext

from database.database import get_user_by_id, RoomInit, User, my_db, Room, RoomUser

from dotenv import load_dotenv
from os import getenv
import asyncio
import logging
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, InlineKeyboardMarkup
import sys

from database.database import Database
from database.triangle_init import triangle_init
from keyboards.admin_keyboard import main_admin_keyboard
from keyboards.supervisor_keyboard import main_supervisor_keyboard
from keyboards.resident_keyboard import main_resident_keyboard
from keyboards.unregistered_user_keyboard import main_unregistered_user_keyboard
from handlers import admin, supervisor, resident, registration
load_dotenv()

# Получить значение токена
TOKEN = getenv("TOKEN")
DEV = getenv("DEV") == "TRUE"

# Диспетчер
dp = Dispatcher()
dp.include_routers(admin.router, supervisor.router, resident.router, registration.router)

ADMINS = []
SUPERVISOR = []

@dp.message(CommandStart())
async def command_start_handler(message: Message, command: CommandObject, state: FSMContext) -> None:
    room_key = command.args
    if room := await my_db.query_one(RoomInit, key=room_key):
        ans = await my_db.query(RoomUser, room_id=room.id)
        if len(ans) > 2:
                await message.answer("В комнате уже зарегистрированы 3 пользователя, обратитесь к старосте")
        else:
            await state.update_data(room_id=room.id)
            await message.answer(f"Привет, {html.bold(message.from_user.full_name)}!",
                                reply_markup=main_unregistered_user_keyboard)
    else:
        await message.answer(f"Неверный ключ комнаты")
    user_role = await my_db.get_user_role(message.from_user.id)
    if user_role == 'admin':
        await message.answer(f"Привет админ, {html.bold(message.from_user.full_name)}!",
                             reply_markup=main_admin_keyboard)
    elif user_role == 'supervisor':
        await message.answer(f"Привет староста, {html.bold(message.from_user.full_name)}!",
                             reply_markup=main_supervisor_keyboard)
    elif user_role == 'resident':
        await message.answer(f"Привет резидент, {html.bold(message.from_user.full_name)}!", reply_markup=main_resident_keyboard)


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    try:
        remove('database.db')
    except FileNotFoundError:
        print("Не существует")

    if DEV:
        if not await my_db.is_exist():
            await my_db.initialize()
    if not await my_db.query_one(User, id="0"):
        await triangle_init(my_db)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
