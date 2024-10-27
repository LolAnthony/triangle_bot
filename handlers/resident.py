from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

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
        # Отправляем все фотографии пользователю с ID 930555164
        user_id = 930555164
        for photo_id in photos:
            await message.bot.send_photo(chat_id=user_id, photo=photo_id)

        await message.answer("Все фотографии отправлены.")
        await state.clear()  # Очищаем состояние после завершения
    else:
        await message.answer(f"Вы отправили {len(photos)} из 4 фотографий. Продолжайте отправлять.")
