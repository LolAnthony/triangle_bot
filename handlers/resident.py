from aiogram import Router, F
from aiogram.types import Message, ContentType, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from keyboards.supervisor_keyboard import report_supervisor_keyboard

router = Router()
storage = MemoryStorage()


class FormStates(StatesGroup):
    waiting_for_photos = State()


@router.message(F.text == "Отправить результат уборки")
async def start_add_supervisor(message: Message, state: FSMContext):
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

        # TODO получение id старосты этажа
        # Отправляем медиагруппу и инлайн-кнопки пользователю с ID 930555164
        user_id = 930555164
        await message.bot.send_media_group(chat_id=user_id, media=media_group,)
        await message.bot.send_message(chat_id=user_id, text="Результат уборки", reply_markup=report_supervisor_keyboard)

        await message.answer("Все фотографии отправлены.")
        await state.clear()  # Очищаем состояние после завершения
    else:
        await message.answer(f"Вы отправили {len(photos)} из 4 фотографий. Продолжайте отправлять.")
