from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import re
from database.database import my_db, get_user_by_id
from keyboards.admin_keyboard import choose_floor_keyboard, create_choose_room_keyboard, create_choose_resident_keyboard

router = Router()


@router.message(F.text == "Добавить старосту")
async def start_add_supervisor(message: Message):
    if await my_db.get_user_role(message.from_user.id) == "admin":
        await message.answer("Выберите этаж", reply_markup=choose_floor_keyboard)

@router.callback_query(lambda c: c.data.startswith("set_floor:"))
async def set_floor(callback_query: CallbackQuery):
    floor_number = int(callback_query.data.split(":")[1])
    await callback_query.answer("Этаж выбран")
    await callback_query.message.answer("Выберите комнату", reply_markup=await create_choose_room_keyboard(floor_number))

@router.callback_query(lambda c: c.data.startswith("set_room:"))
async def set_room(callback_query: CallbackQuery):
    room_number = int(callback_query.data.split(":")[1])
    await callback_query.answer("Комната выбрана")
    await callback_query.message.answer("Выберите студента", reply_markup=await create_choose_resident_keyboard(room_number))

@router.callback_query(lambda c: c.data.startswith("set_user:"))
async def set_room(callback_query: CallbackQuery):
    user_id = int(callback_query.data.split(":")[1])
    await my_db.set_user_role(user_id, 2)
    await callback_query.answer("+1 в рядах комсомолов")
    await callback_query.message.answer("Староста добавлен")
