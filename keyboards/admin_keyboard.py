from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_admin_buttons = [
    [KeyboardButton(text="Добавить старосту")],
]
main_admin_keyboard = ReplyKeyboardMarkup(keyboard=main_admin_buttons, resize_keyboard=True)

choose_floor_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text=str(i), callback_data=f"set_floor{i}") for i in range(1, 5)],
])


def create_choose_room_keyboard(floor: int) -> ReplyKeyboardMarkup:
    pass