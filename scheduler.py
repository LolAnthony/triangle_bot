from database.database import RoomInit, User, my_db, Room, RoomUser, DutyRoom, Duty
from aiogram import Bot
import pprint
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler(timezone='Europe/Moscow')

async def update_duties(bot: Bot):
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
            room_number = await my_db.get_room_number_by_id(duty.room_id)
            supervisor = await my_db.get_supervisor_tgid_by_resident_tgid(users[0].tgid)
            # TODO функция получить комнату по tgid сделать и использовать здесь и везде!!!
            supervisor_room_user = await my_db.query_one(RoomUser, user_id=supervisor)
            supervisor_full_name = await my_db.get_full_name(supervisor)
            supervisor_room = await my_db.query_one(Room, id=supervisor_room_user.room_id)
            duty_room = await my_db.query_one(DutyRoom, duty_id=duty.id)
            if duty_room and duty_room.is_approved == 0:
                try:
                    await bot.send_message(supervisor, f"Комната {room_number} не убралась")
                except:
                    print("Не удалось отправить сообщение супервайзеру")
                for user in users:
                    message_text = (f"Вы не убрались, обратитесь к старосте - {supervisor_full_name}"
                                    f" в {supervisor_room.number} комнате")
                    try:
                        await bot.send_message(chat_id=user.tgid, text=message_text)
                    except:
                        print("Не удалось отправить сообщение пользователю")
            else:
                for user in users:
                    message_text = f"Отличная работа! {supervisor_full_name} гордится вами =)"
                    try:
                        await bot.send_message(chat_id=user.tgid, text=message_text)
                    except:
                        print("Не удалось отправить сообщение пользователю")
        except IndexError:
            print("Не все данные")


async def send_notification(bot: Bot):
    print("Запушена задача")
    schedule = await my_db.get_schedule_for_date()

    if schedule:
        for user_tgid in schedule['users']:
            message_text = "Напоминание‼️\nВаша комната сегодня убирается"
            try:
                await bot.send_message(chat_id=user_tgid, text=message_text)
            except:
                print("Не удалось отправить сообщение пользователю")
