from os import getenv, remove

from aiogram.fsm.context import FSMContext

from database.database import get_user_by_id, RoomInit, User, my_db, Room, RoomUser, DutyRoom

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
from datetime import datetime
from database.database import Database
from database.triangle_init import triangle_init
from keyboards.admin_keyboard import main_admin_keyboard
from keyboards.supervisor_keyboard import main_supervisor_keyboard
from keyboards.resident_keyboard import main_resident_keyboard
from keyboards.unregistered_user_keyboard import main_unregistered_user_keyboard
from handlers import admin, supervisor, resident, registration
from functools import partial

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
    elif not get_user_by_id(message.from_user.id):
        await message.answer(f"Неверный ключ комнаты")
    user_role = await my_db.get_user_role(message.from_user.id)
    if user_role == 'admin':
        await message.answer(f"Доброго времени суток Админ, {html.bold(message.from_user.full_name)}!",
                             reply_markup=main_admin_keyboard)
    elif user_role == 'supervisor':
        await message.answer(f"Привет староста, {html.bold(message.from_user.full_name)}!",
                             reply_markup=main_supervisor_keyboard)
    elif user_role == 'resident':
        await message.answer(f"Привет резидент, {html.bold(message.from_user.full_name)}!",
                             reply_markup=main_resident_keyboard)


async def check_and_send_notifications(bot: Bot):
    while True:
        now = datetime.now()
        schedule = await my_db.get_schedule_for_date(now.date())  # запрос расписания на текущую дату
        if schedule:
            for user_tgid in schedule['users']:
                message_text = f"Напоминание‼️\nВаша комната сегодня убирается"  # текст уведомления
                await bot.send_message(chat_id=user_tgid, text=message_text)

            add_duty_room = DutyRoom(
                duty_id=schedule['duty_id'],
                is_approved=False,
                is_sent=False
            )
            await my_db.add_instance(add_duty_room)

        await asyncio.sleep(24*60*60)  # проверка расписания каждые 24 часа
        # await asyncio.sleep(10)  # проверка расписания каждые 10 секунд


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    asyncio.create_task(check_and_send_notifications(bot))
    # try:
    #     remove('database.db')
    # except FileNotFoundError:
    #     print("Не существует")
    #
    # if DEV:
    #     if not await my_db.is_exist():
    #         await my_db.initialize()
    # if not await my_db.query_one(User, id="0"):
    #     await triangle_init(my_db)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
