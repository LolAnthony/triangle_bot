from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile, Document, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import pandas as pd
import os
import tempfile
from keyboards.supervisor_keyboard import main_supervisor_keyboard

router = Router()
SUPERVISORS = [930555164]


class ScheduleUploadStates(StatesGroup):
    waiting_for_file = State()


@router.message(F.text == "Загрузить расписание")
async def upload_schedule(message: Message, state: FSMContext):
    # TODO проверка на старосту, переделать из БД
    if message.from_user.id in SUPERVISORS:
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

        # TODO ЗАГРУЗКА РАСПИСАНИЯ В БД

        # Ответ с подтверждением
        await message.answer(f"Расписание успешно загружено и обработано: {schedule_data}")

    except Exception as e:
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
    # TODO проверка на старосту, переделать из БД
    if message.from_user.id in SUPERVISORS:
        # TODO получение текущего расписания из БД
        await message.answer(
            "Текущее расписание",
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
