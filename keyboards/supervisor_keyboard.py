from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database.database import my_db, Room

main_supervisor_buttons = [
    [KeyboardButton(text="Добавить комнату")],
    [KeyboardButton(text="Загрузить расписание")],
    [KeyboardButton(text="Получить текущее расписание")],
]

main_supervisor_keyboard = ReplyKeyboardMarkup(keyboard=main_supervisor_buttons, resize_keyboard=True)

# inline клавиатура с подтверждениями/отклонением уборки
report_supervisor_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Подтвердить", callback_data="confirm")],
    [InlineKeyboardButton(text="Отклонить", callback_data="reject")]
])


async def create_choose_room_keyboard_for_qr(floor: int = None) -> InlineKeyboardMarkup:
    if floor is None:
        rooms = await my_db.query(Room)
    else:
        rooms = await my_db.query(Room, floor=floor)
    print(rooms)
    buttons_per_row = 8
    buttons = []

    # Формируем кнопки с разбивкой на ряды
    for i in range(0, len(rooms), buttons_per_row):
        row_buttons = [
            InlineKeyboardButton(text=str(room.number), callback_data=f"set_room_qr:{room.id}")
            for room in rooms[i:i + buttons_per_row]
        ]
        buttons.append(row_buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)

