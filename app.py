from os import getenv, remove
from pprint import pprint

from aiogram.fsm.context import FSMContext
from sqlalchemy.util import await_only

from database.database import get_user_by_id, RoomInit, User, my_db, Room, RoomUser, DutyRoom, Duty

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
    times_for_send = ["01:00", "01:01", "12:00", "20:00", "22:00"]

    while True:
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")

        if current_time_str in times_for_send and current_time_str != "01:00":
            schedule = await my_db.get_schedule_for_date()

            if schedule:
                for user_tgid in schedule['users']:
                    message_text = "Напоминание‼️\nВаша комната сегодня убирается"
                    await bot.send_message(chat_id=user_tgid, text=message_text)

                for duty_id in schedule['duties']:
                    add_duty_room = DutyRoom(
                        duty_id=duty_id,
                        is_approved=False,
                        is_sent=False
                    )
                    await my_db.add_instance(add_duty_room)
            await asyncio.sleep(60)
        elif current_time_str == "01:00":
            schedule = await my_db.get_schedule_for_date()
            current_duty = schedule['duties']
            duties = [
                await my_db.query_one(Duty, id=i) for i in current_duty
            ]
            print(duties)
            pprint(schedule)
            print("DUTIES", duties)
            for duty in duties:
                try:
                    users = await my_db.get_users_in_room(duty.room_id)
                    print(users)
                    supervisor = await my_db.get_supervisor_tgid_by_resident_tgid(users[0].tgid)
                    # TODO функция получить комнату по tgid сделать и использовать здесь и везде!!!
                    supervisor_room_user = await my_db.query(RoomUser.room_id, user_id=supervisor)
                    print(supervisor_room_user)
                    supervisor_full_name = await my_db.get_full_name(supervisor)
                    print(supervisor_full_name)
                    supervisor_room = await my_db.query_one(Room, room_id=supervisor_room_user)
                    print(supervisor_room)
                    duty_room = await my_db.query_one(DutyRoom, duty_id=duty.id)
                    print(duty_room)
                    if duty_room and duty_room.is_approved == 0:
                        for user in users:
                            message_text = "Вы не убрались сегодня" if duty_room.is_sent == 0 else (f"Староста не принял вашу уборку, обратитесь к старосте - {supervisor_full_name}"
                                                                                                    f"в {supervisor_room.number} комнате")
                            await bot.send_message(chat_id=user.tgid, text=message_text)
                    else:
                        for user in users:
                            message_text = f"Отличная работа! {supervisor_full_name} гордится вами =)"
                            await bot.send_message(chat_id=user.tgid, text=message_text)
                except IndexError:
                    print("Не все данные")
        else:
            if schedule:
                for user_tgid in schedule['users']:
                    message_text = "Напоминание‼️\nВаша комната сегодня убирается"
                    await bot.send_message(chat_id=user_tgid, text=message_text)

                for duty_id in schedule['duties']:
                    add_duty_room = DutyRoom(
                        duty_id=duty_id,
                        is_approved=False,
                        is_sent=False
                    )
                    await my_db.add_instance(add_duty_room)
            await asyncio.sleep(60)

        next_check_time = min(
            (
                datetime.combine(now.date(), datetime.strptime(t, "%H:%M").time())
                if datetime.strptime(t, "%H:%M").time() > now.time()
                else datetime.combine(now.date() + timedelta(days=1), datetime.strptime(t, "%H:%M").time())
            )
            for t in times_for_send
        )
        wait_time = (next_check_time - now).total_seconds()
        await asyncio.sleep(wait_time)


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
