from os import getenv, remove
from pprint import pprint

from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.context import FSMContext
from sqlalchemy.util import await_only

from database.database import RoomInit, User, my_db, Room, RoomUser, DutyRoom, Duty

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
from datetime import datetime, timedelta
from database.database import Database
from database.triangle_init import triangle_init
from keyboards.admin_keyboard import main_admin_keyboard
from keyboards.supervisor_keyboard import main_supervisor_keyboard
from keyboards.resident_keyboard import main_resident_keyboard
from keyboards.unregistered_user_keyboard import main_unregistered_user_keyboard
from handlers import admin, supervisor, resident, registration
from functools import partial
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from scheduler import scheduler, send_notification, update_duties

load_dotenv()

# Получить значение токена
TOKEN = getenv("TOKEN")
DEV = getenv("DEV") == "TRUE"

# Диспетчер
dp = Dispatcher()
dp.include_routers(admin.router, supervisor.router, resident.router, registration.router)


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
    # elif not get_user_by_id(message.from_user.id):
    #     await message.answer(f"Неверный ключ комнаты")
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


async def main() -> None:
    if DEV:
        bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    else:
        bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML),
                  session=AiohttpSession(proxy='http://proxy.server:3128'))

    scheduler.start()
    scheduler.add_job(send_notification, args=[bot], trigger=CronTrigger(hour=12, minute=0))
    scheduler.add_job(send_notification, args=[bot], trigger=CronTrigger(hour=20, minute=0))
    scheduler.add_job(send_notification, args=[bot], trigger=CronTrigger(hour=22, minute=0))

    scheduler.add_job(update_duties, args=[bot], trigger=CronTrigger(hour=1, minute=0))
    # scheduler.add_job(send_notification, args=[bot], trigger=IntervalTrigger(seconds=15))
    if not await my_db.is_exist():
        await my_db.initialize()
        await triangle_init(my_db)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
