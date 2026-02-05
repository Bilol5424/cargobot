from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_calculator_route_keyboard(language: str = "ru"):
    """Клавиатура для выбора маршрута калькулятора"""
    texts = {
        "ru": {
            "urumchi": "Urumchi → Khujand",
            "yiwu": "Yiwu → Khujand",
            "back": "⬅️ Назад",
            "cancel": "❌ Отмена"
        },
        "tj": {
            "urumchi": "Урумчӣ → Хуҷанд",
            "yiwu": "Иву → Хуҷанд",
            "back": "⬅️ Бозгашт",
            "cancel": "❌ Бекор кардан"
        }
    }
    
    t = texts[language]
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text=t["urumchi"]))
    keyboard.add(KeyboardButton(text=t["yiwu"]))
    keyboard.add(KeyboardButton(text=t["back"]))
    keyboard.add(KeyboardButton(text=t["cancel"]))
    keyboard.adjust(2, 2)
    return keyboard.as_markup(resize_keyboard=True)