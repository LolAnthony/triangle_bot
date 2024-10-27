from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_unregistered_user_buttons = [
    [KeyboardButton(text="Зарегистрироваться")],
]

main_unregistered_user_keyboard = ReplyKeyboardMarkup(keyboard=main_unregistered_user_buttons, resize_keyboard=True)
