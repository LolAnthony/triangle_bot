from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

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



