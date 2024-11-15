from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile, Document, CallbackQuery, InputFile, \
    BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import pandas as pd
import os
import tempfile
from keyboards.supervisor_keyboard import main_supervisor_keyboard
from database.database import RoomInit, User, my_db, Room, RoomUser, Duty, DutyRoom
from datetime import datetime, timedelta
from keyboards.supervisor_keyboard import create_choose_room_keyboard_for_qr

router = Router()


class ScheduleUploadStates(StatesGroup):
    waiting_for_file = State()


@router.message(F.text == "Загрузить расписание")
async def upload_schedule(message: Message, state: FSMContext):
    user_role = await my_db.get_user_role(message.from_user.id)
    if user_role == 'supervisor':
        # Получаем номер этажа пользователя
        floor = await my_db.get_floor_by_resident_tgid(message.from_user.id)

        # Получаем комнаты на этом этаже
        rooms = await my_db.query(Room, floor=floor)

        # Текущая дата в формате дд.мм.гггг
        start_date = datetime.now()

        # Формируем данные для таблицы
        data = {
            "Ком. №": [room.number for room in rooms],
            "Дата": [(start_date + timedelta(days=i)).strftime("%d.%m.%Y") for i in range(len(rooms))]
        }

        # Создаем DataFrame и временный Excel файл
        df = pd.DataFrame(data)
        file_path = "schedule_sample.xlsx"
        df.to_excel(file_path, index=False)

        # Отправляем созданный файл пользователю
        await message.answer(
            "Пришлите расписание в виде Excel таблицы, формат таблицы должен быть такой, как в прикрепленном файле:"
        )
        await message.answer_document(FSInputFile(file_path))

        # Переход в состояние ожидания файла
        await state.set_state(ScheduleUploadStates.waiting_for_file)


# Хэндлер для получения и обработки файла от пользователя
@router.message(ScheduleUploadStates.waiting_for_file, F.document)
async def handle_schedule_file(message: Message, state: FSMContext):
    document = message.document
    # Скачиваем файл
    file_info = await message.bot.get_file(document.file_id)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
        temp_file_path = temp_file.name  # Получаем путь к временному файлу

        # Скачиваем файл
        await message.bot.download_file(file_info.file_path, destination=temp_file_path)

    # Парсинг Excel-файла
    try:
        df = pd.read_excel(temp_file_path)
        # первый столбец — "номер комнаты", второй столбец — "дата дежурства"
        schedule_data = []
        for index, row in df.iterrows():
            room_number = row[0]
            duty_date = row[1]

            if not isinstance(duty_date, pd.Timestamp):
                duty_date = pd.to_datetime(duty_date)

            schedule_data.append({"room_number": int(room_number), "duty_date": duty_date})

        await my_db.update_duties(schedule_data)
        await message.answer("Расписание успешно загружено и обработано.")

    except Exception as e:
        print(e)
        await message.answer("Произошла ошибка при обработке файла. Убедитесь, что формат файла корректный.")

    finally:
        # Удаляем временный файл
        try:
            os.remove(temp_file_path)

        except PermissionError as e:
            print(f"Не удалось удалить файл {temp_file_path}: {e}")

        await state.clear()


@router.message(F.text == "Получить текущее расписание")
async def upload_schedule(message: Message, state: FSMContext):
    user_role = await my_db.get_user_role(message.from_user.id)
    if user_role == 'supervisor':
        floor = await my_db.get_floor_by_resident_tgid(message.from_user.id)
        schedule = await my_db.get_floor_duties(floor)
        text = ""
        for duty in schedule:
            formatted_date = duty.date.strftime("%d.%m.%Y")
            text += f"{formatted_date}: {await my_db.get_room_number_by_id(duty.room_id)}\n"
        await message.answer(
            "Текущее расписание:\n" + text,
        )


# Обработчик для нажатия кнопки "Подтвердить"
@router.callback_query(F.data.startswith("confirm:"))
async def on_confirm(callback_query: CallbackQuery):
    duty_room_id = int(callback_query.data.split(":")[1])

    duty_room = await my_db.query_one(DutyRoom, id=duty_room_id)
    duty = await my_db.query_one(Duty, id=duty_room.duty_id)

    room_users = await my_db.query(RoomUser, room_id=duty.room_id)
    for room_user in room_users:
        await callback_query.bot.send_message(
            chat_id=room_user.user_id,
            text="Результат был подтвержден"
        )

    await my_db.change_report_approved_status(duty_room_id)
    await callback_query.answer("Результат подтвержден.")
    await callback_query.message.edit_text("Результат уборки был подтвержден.")


# Обработчик для нажатия кнопки "Отклонить"
@router.callback_query(F.data.startswith("reject:"))
async def on_reject(callback_query: CallbackQuery):
    duty_room_id = int(callback_query.data.split(":")[1])

    await my_db.change_report_sent_status(duty_room_id)
    duty_room = await my_db.query_one(DutyRoom, id=duty_room_id)
    duty = await my_db.query_one(Duty, id=duty_room.duty_id)

    room_users = await my_db.query(RoomUser, room_id=duty.room_id)
    for room_user in room_users:
        await callback_query.bot.send_message(
            chat_id=room_user.user_id,
            text="Результат уборки был отклонен."
        )

    await callback_query.answer("Результат отклонен.")
    await callback_query.message.edit_text("Результат уборки был отклонен.")


@router.message(F.text == "Добавить комнату")
async def upload_schedule(message: Message, state: FSMContext):
    user_role = await my_db.get_user_role(message.from_user.id)
    if user_role == 'supervisor':
        floor_number = await my_db.get_floor_by_resident_tgid(message.from_user.id)
        await message.answer("Выберите комнату",
                             reply_markup=await create_choose_room_keyboard_for_qr(floor_number))

    if user_role == 'admin':
        await message.answer("Выберите комнату",
                             reply_markup=await create_choose_room_keyboard_for_qr())


@router.callback_query(lambda c: c.data.startswith("set_room_qr:"))
async def set_room(callback_query: CallbackQuery):
    room_id = int(callback_query.data.split(":")[1])
    await callback_query.answer("Комната выбрана")
    room_number = await my_db.get_room_number_by_id(room_id)
    room_users = await my_db.get_users_in_room(room_id)

    roommates_string = "\n".join(
        f"{i + 1}. {room_users[i].name} {room_users[i].surname}" for i in range(len(room_users)))

    # await callback_query.message.answer(f"QR код для комнаты {room_number}")
    qr = await my_db.get_qrcode_for_room(room_id, room_number)
    qr_image = BufferedInputFile(qr.read(), filename="qr_code.png")
    await callback_query.message.bot.send_photo(chat_id=callback_query.message.chat.id, photo=qr_image)
    await callback_query.message.answer("Зарегистрированные жильцы:\n" + roommates_string)
