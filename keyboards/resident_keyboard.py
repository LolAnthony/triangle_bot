from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_resident_buttons = [
    [KeyboardButton(text="Отправить результат уборки")],
]

main_resident_keyboard = ReplyKeyboardMarkup(keyboard=main_resident_buttons, resize_keyboard=True)
