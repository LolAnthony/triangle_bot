from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from database.database import my_db, Room

main_admin_buttons = [
    [KeyboardButton(text="Добавить старосту")],
]
main_admin_keyboard = ReplyKeyboardMarkup(keyboard=main_admin_buttons, resize_keyboard=True)

choose_floor_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=str(i), callback_data=f"set_floor:{i}") for i in range(1, 6)],
])


async def create_choose_room_keyboard(floor: int) -> InlineKeyboardMarkup:
    rooms = await my_db.query(Room, floor=floor)
    buttons = [
        [InlineKeyboardButton(text=str(room.number), callback_data=f"set_room:{room.id}") for room in rooms[:len(rooms)//3]],
        [InlineKeyboardButton(text=str(room.number), callback_data=f"set_room:{room.id}") for room in rooms[len(rooms)//3+2 : -2]],
        [InlineKeyboardButton(text=str(room.number), callback_data=f"set_room:{room.id}") for room in rooms[-3:]],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def create_choose_resident_keyboard(room_id: int) -> InlineKeyboardMarkup:
    users = await my_db.get_users_in_room(room_id)
    print(users)
    buttons = []
    for user in users:
        buttons.append(
            [InlineKeyboardButton(text=f"{user.surname} {user.name}", callback_data=f"set_user:{user.id}")]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)
