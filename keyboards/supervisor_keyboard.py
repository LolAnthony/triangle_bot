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


async def create_choose_room_keyboard_for_qr(floor: int) -> InlineKeyboardMarkup:
    rooms = await my_db.query(Room, floor=floor)
    buttons = [
        [InlineKeyboardButton(text=str(room.number), callback_data=f"set_room_qr:{room.id}") for room in rooms[:len(rooms)//3]],
        [InlineKeyboardButton(text=str(room.number), callback_data=f"set_room_qr:{room.id}") for room in rooms[len(rooms)//3+2 : -2]],
        [InlineKeyboardButton(text=str(room.number), callback_data=f"set_room_qr:{room.id}") for room in rooms[-3:]],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

