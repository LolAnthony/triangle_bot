from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import re
from database.database import my_db
from keyboards.admin_keyboard import choose_floor_keyboard

router = Router()


@router.message(F.text == "Добавить старосту")
async def start_add_supervisor(message: Message):
    if my_db.get_user_role == "admin":
        await message.answer("Выберите этаж", reply_markup=choose_floor_keyboard)


@router.callback_query(lambda c: c.data.startswith("set_floor:"))
async def set_floor(callback_query: CallbackQuery):
    floor_number = callback_query.data.split(":")[1]
    await callback_query.answer("Выберите комнату", reply_markup=create_choose_room_keyboard(floor_number))
