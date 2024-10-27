from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_supervisor_buttons = [
    [KeyboardButton(text="Добавить комнату")],
    [KeyboardButton(text="Загрузить расписание")],
]

main_supervisor_keyboard = ReplyKeyboardMarkup(keyboard=main_supervisor_buttons, resize_keyboard=True)
