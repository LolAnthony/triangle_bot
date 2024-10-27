from aiogram import Router, F
from aiogram.types import Message

router = Router()


@router.message(F.text)
async def message(message: Message):
    await message.answer("Это текстовое сообщение!")