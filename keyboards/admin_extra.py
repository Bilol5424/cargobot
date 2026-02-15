from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


admin_main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить трек-код")],
        [KeyboardButton(text="📥 Массовое добавление")],
        [KeyboardButton(text="🔄 Массово обновить статус")],
        [KeyboardButton(text="🔎 Поиск товара")],
        [KeyboardButton(text="📤 Выгрузить все товары")],
        [KeyboardButton(text="📊 Месячный отчёт")],
        [KeyboardButton(text="👤 Профиль администратора")],
    ],
    resize_keyboard=True
)


bulk_add_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Ввести список")],
        [KeyboardButton(text="📎 Загрузить Excel")],
        [KeyboardButton(text="⬅️ Назад")],
    ],
    resize_keyboard=True
)


status_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚚 В пути")],
        [KeyboardButton(text="📦 Прибыл")],
        [KeyboardButton(text="✅ Выдан")],
        [KeyboardButton(text="⬅️ Назад")],
    ],
    resize_keyboard=True
)


reports_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 Отчёт за текущий месяц")],
        [KeyboardButton(text="⬅️ Назад")],
    ],
    resize_keyboard=True
)


profile_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✏️ Изменить имя")],
        [KeyboardButton(text="📞 Изменить телефон")],
        [KeyboardButton(text="📧 Изменить email")],
        [KeyboardButton(text="⬅️ Назад")],
    ],
    resize_keyboard=True
)
