from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message

from database.database import User, RoomUser, my_db

router = Router()


class FormStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_surname = State()




@router.message(F.text == "Зарегистрироваться")
async def message(message: Message, state: FSMContext):
    await message.answer("Введите Имя")
    await state.set_state(FormStates.waiting_for_name)

@router.message(F.text, FormStates.waiting_for_name)
async def message(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите Фамилию")
    await state.set_state(FormStates.waiting_for_surname)

@router.message(F.text, FormStates.waiting_for_surname)
async def message(message: Message,  state: FSMContext):
    surname = message.text
    user_data = await state.get_data()
    add_user = User (
        name = user_data.get("name", ''),
        surname = surname,
        tgid = message.from_user.id,
        role_id = 3
    )
    add_room_user = RoomUser (
        room_id = user_data.get("room_id", -1),
        user_id = message.from_user.id,
    )

    await my_db.add_instance(add_user)
    await my_db.add_instance(add_room_user)
    await message.answer("Вы успешно зарегистрировались!")
    await state.clear()
