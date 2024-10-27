from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import re

router = Router()

ADMINS = [930555164]
SUPERVISORS = [930555164]



@router.message(F.text == "Добавить старосту")
async def start_add_supervisor(message: Message):
    # TODO проверка на админа, переделать из БД
    if message.from_user.id in ADMINS:
        await message.answer("Введите никнейм пользователя, например:\n@nsstnc", reply_markup=ReplyKeyboardRemove())
