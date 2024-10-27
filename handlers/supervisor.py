from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile, Document, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import pandas as pd
import os
import tempfile
from keyboards.supervisor_keyboard import main_supervisor_keyboard
from database.database import get_user_by_id, RoomInit, User, my_db, Room, RoomUser, Duty
from datetime import datetime

router = Router()


class ScheduleUploadStates(StatesGroup):
    waiting_for_file = State()


@router.message(F.text == "Загрузить расписание")
async def upload_schedule(message: Message, state: FSMContext):
    user_role = await my_db.get_user_role(message.from_user.id)
    if user_role == 'supervisor':
        await message.answer(
            "Пришлите расписание в виде Excel таблицы, формат таблицы должен быть такой, как в прикрепленном файле:",
        )
        file_path = "handlers/schedule_sample.xlsx"
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
            schedule_data.append({"room_number": room_number, "duty_date": duty_date})

        add_duties = [
            Duty(
                room_id=await my_db.get_room_id_by_number(duty["room_number"]),
                date=duty["duty_date"],
            ) for duty in schedule_data
        ]

        for duty in add_duties:
            await my_db.add_instance(duty)

        # Ответ с подтверждением
        await message.answer(f"Расписание успешно загружено и обработано.")

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
    # TODO проверка на этаж с которого получаем расписание
    user_role = await my_db.get_user_role(message.from_user.id)
    if user_role == 'supervisor':
        schedule = await my_db.query(Duty)
        text = ""
        for duty in schedule:
            formatted_date = duty.date.strftime("%d.%m.%Y")
            text += f"{formatted_date}: {await my_db.get_room_number_by_id(duty.room_id)}\n"
        await message.answer(
            "Текущее расписание:\n" + text,
        )


# Обработчик для нажатия кнопки "Подтвердить"
@router.callback_query(F.data == "confirm")
async def on_confirm(callback_query: CallbackQuery):
    # TODO оповещение всем участникам комнаты о принятой уборке
    await callback_query.answer("Результат подтвержден.")
    await callback_query.message.edit_text("Результат уборки был подтвержден.")


# Обработчик для нажатия кнопки "Отклонить"
@router.callback_query(F.data == "reject")
async def on_reject(callback_query: CallbackQuery):
    # TODO оповещение всем участникам комнаты об отклоненной уборке
    await callback_query.answer("Результат отклонен.")
    await callback_query.message.edit_text("Результат уборки был отклонен.")
