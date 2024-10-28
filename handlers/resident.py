from aiogram import Router, F
from aiogram.types import Message, ContentType, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from keyboards.supervisor_keyboard import report_supervisor_keyboard
from datetime import datetime
from database.database import my_db, DutyRoom

router = Router()
storage = MemoryStorage()


class FormStates(StatesGroup):
    waiting_for_photos = State()


@router.message(F.text == "Отправить результат уборки")
async def start_add_supervisor(message: Message, state: FSMContext):
    current_duty_room_id = await my_db.get_current_duty_room_id()

    duty_room = await my_db.query_one(DutyRoom, duty_id=current_duty_room_id)

    if duty_room.is_sent:
        await message.answer("Результат по вашей уборке уже был отправлен")
    else:
        await state.set_state(FormStates.waiting_for_photos)
        await message.answer("Отправьте 4 фотографии:\n"
                             "1. Фото убранных плит\n"
                             "2. Фото убранных раковин\n"
                             "3. Фото стола с микроволновкой\n"
                             "4. Общий план убранной кухни со стороны входа")


@router.message(FormStates.waiting_for_photos, F.content_type == ContentType.PHOTO)
async def handle_photos(message: Message, state: FSMContext):
    user_data = await state.get_data()
    photos = user_data.get("photos", [])

    photos.append(message.photo[-1].file_id)  # Сохраняем фото

    # Сохраняем обновленный список фотографий в состояние
    await state.update_data(photos=photos)

    # Проверяем, получили ли мы все 4 фотографии
    if len(photos) == 4:
        # Формируем список InputMediaPhoto для отправки медиагруппой
        media_group = [InputMediaPhoto(media=photo_id) for photo_id in photos]

        # Отправляем медиагруппу и инлайн-кнопки пользователю с ID 930555164
        supervisor_id = await my_db.get_supervisor_tgid_by_resident_tgid(message.from_user.id)

        await message.bot.send_media_group(chat_id=supervisor_id, media=media_group, )
        await message.bot.send_message(chat_id=supervisor_id, text="Результат уборки",
                                       reply_markup=report_supervisor_keyboard)

        current_duty_room_id = await my_db.get_current_duty_room_id()

        await my_db.change_report_sent_status(current_duty_room_id)

        schedule = await my_db.get_schedule_for_date(datetime.now().date())

        for user_tgid in schedule['users']:
            await message.bot.send_message(chat_id=user_tgid, text="Отчет об уборке отправлен")

        await state.clear()  # Очищаем состояние после завершения
    else:
        await message.answer(f"Вы отправили {len(photos)} из 4 фотографий. Продолжайте отправлять.")
