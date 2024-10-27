from aiogram import Router, F
from aiogram.types import Message

router = Router()


@router.message(F.text == "Зарегистрироваться")
async def message(message: Message):
    print(await message.answer("Введите имя"))
