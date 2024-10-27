from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_admin_buttons = [
    [KeyboardButton(text="Добавить комнату")],
    [KeyboardButton(text="Загрузить расписание")],
    [KeyboardButton(text="")],
]

main_admin_keyboard = ReplyKeyboardMarkup(keyboard=main_admin_buttons, resize_keyboard=True)
