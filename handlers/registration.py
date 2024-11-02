from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

from database.database import RoomUser, User, my_db
from keyboards.resident_keyboard import main_resident_keyboard

router = Router()


class FormStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_surname = State()


@router.message(F.text == "Зарегистрироваться")
async def message(message: Message, state: FSMContext):
    user_data = await state.get_data()
    room_id = user_data.get("room_id", -1)
    if room_id == -1:
        await message.answer("Не удалось привязать к комнате!")
    else:
        await message.answer("Введите **Имя** (пример: **Иван**)")
        await state.set_state(FormStates.waiting_for_name)


@router.message(F.text, FormStates.waiting_for_name)
async def message(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите **Фамилию** (пример: **Иванов**)")
    await state.set_state(FormStates.waiting_for_surname)


@router.message(F.text, FormStates.waiting_for_surname)
async def message(message: Message, state: FSMContext):
    surname = message.text
    user_data = await state.get_data()
    name = user_data.get("name", "")
    room_id = user_data.get("room_id", -1)

    add_user = User(name=name, surname=surname, tgid=message.from_user.id, role_id=3)
    add_room_user = RoomUser(
        room_id=room_id,
        user_id=message.from_user.id,
    )
    if room_id != -1:
        await my_db.add_instance(add_user)
        await my_db.add_instance(add_room_user)
        await message.answer(
            "Вы успешно зарегистрировались!", reply_markup=main_resident_keyboard
        )
    else:
        await message.answer("Не удалось привязать к комнате!")
    await state.clear()
