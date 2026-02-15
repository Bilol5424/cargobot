from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_language_keyboard():
    """Клавиатура для выбора языка"""
    keyboard = ReplyKeyboardBuilder()
    
    # Используем точные тексты, которые ожидаются в обработчике
    keyboard.add(KeyboardButton(text="🇷🇺 Русский"))
    keyboard.add(KeyboardButton(text="🇹🇯 Тоҷикӣ"))
    
    keyboard.adjust(2)
    return keyboard.as_markup(
        resize_keyboard=True,
        one_time_keyboard=True  # Скрыть клавиатуру после выбора
    )

def get_main_menu_keyboard(language: str = "ru"):
    texts = {
        "ru": {
            "track_codes": "📦 ТРЕК КОДЫ",
            "profile": "👤 ПРОФИЛЬ",
            "address": "📍 АДРЕС",
            "calculator": "🧮 КАЛЬКУЛЯТОР",
            "door_delivery": "🚚 ДОСТАВКА ДО ДВЕРЕЙ",
            "forbidden": "🚫 ЗАПРЕЩЁННЫЕ ТОВАРЫ",
            "course": "🎓 БЕСПЛАТНЫЙ КУРС",
            "support": "💬 ПОДДЕРЖКА"
        },
        "tj": {
            "track_codes": "📦 РАКАМҲОИ ТАМОШОБИН",
            "profile": "👤 ПРОФИЛ",
            "address": "📍 АДРЕС",
            "calculator": "🧮 КАЛЬКУЛЯТОР",
            "door_delivery": "🚚 РАСОНИДАН ТО ДАР",
            "forbidden": "🚫 МАҲСУЛОТҲОИ МАМНУА",
            "course": "🎓 КУРСИ БЕПУЛ",
            "support": "💬 ДАСТГИРӢ"
        }
    }
    
    t = texts[language]
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text=t["track_codes"]))
    keyboard.add(KeyboardButton(text=t["profile"]))
    keyboard.add(KeyboardButton(text=t["address"]))
    keyboard.add(KeyboardButton(text=t["calculator"]))
    keyboard.add(KeyboardButton(text=t["door_delivery"]))
    keyboard.add(KeyboardButton(text=t["forbidden"]))
    keyboard.add(KeyboardButton(text=t["course"]))
    keyboard.add(KeyboardButton(text=t["support"]))
    keyboard.adjust(2, 2, 2, 2)
    return keyboard.as_markup(resize_keyboard=True)

def get_back_cancel_keyboard(language: str = "ru"):
    texts = {
        "ru": {"back": "⬅️ Назад", "cancel": "❌ Отмена"},
        "tj": {"back": "⬅️ Бозгашт", "cancel": "❌ Бекор кардан"}
    }
    
    t = texts[language]
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text=t["back"]))
    keyboard.add(KeyboardButton(text=t["cancel"]))
    keyboard.adjust(2)
    return keyboard.as_markup(resize_keyboard=True)

def get_track_codes_keyboard(language: str = "ru"):
    texts = {
        "ru": {
            "check_track": "Проверить трек-код",
            "my_track": "Мои трек-коды",
            "add_pending": "Добавить временный трек-код",
            "back": "⬅️ Назад"
        },
        "tj": {
            "check_track": "Тафтиш кардани рамзи тамошобин",
            "my_track": "Рамзҳои тамошобини ман",
            "add_pending": "Илова кардани рамзи интизорӣ",
            "back": "⬅️ Бозгашт"
        }
    }

    t = texts[language]
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text=t["check_track"]))
    keyboard.add(KeyboardButton(text=t["my_track"]))
    keyboard.add(KeyboardButton(text=t["add_pending"]))
    keyboard.add(KeyboardButton(text=t["back"]))
    keyboard.adjust(2, 1, 1)
    return keyboard.as_markup(resize_keyboard=True)
    
def get_profile_keyboard(language: str = "ru"):
    texts = {
        "ru": {
            "edit_name": "📝 Изменить имя",
            "edit_region": "📝 Изменить регион"
        },
        "tj": {
            "edit_name": "📝 Тағйир додани ном",
            "edit_region": "📝 Тағйир додани минтақа"
        }
    }
    
    t = texts[language]
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text=t["edit_name"]))
    keyboard.add(KeyboardButton(text=t["edit_region"]))
    keyboard.add(KeyboardButton(text="⬅️ Назад" if language == "ru" else "⬅️ Бозгашт"))
    keyboard.adjust(2, 1)
    return keyboard.as_markup(resize_keyboard=True)

def get_country_keyboard(language: str = "ru"):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text="🇹🇯 Таджикистан"))
    keyboard.add(KeyboardButton(text="🇨🇳 Китай"))
    keyboard.add(KeyboardButton(text="🇺🇿 Узбекистан"))
    keyboard.add(KeyboardButton(text="🇰🇿 Казахстан"))
    keyboard.add(KeyboardButton(text="⬅️ Назад" if language == "ru" else "⬅️ Бозгашт"))
    keyboard.adjust(2, 2, 1)
    return keyboard.as_markup(resize_keyboard=True)

def get_course_platform_keyboard(language: str = "ru"):
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text="Taobao"))
    keyboard.add(KeyboardButton(text="Pinduoduo"))
    keyboard.add(KeyboardButton(text="Alibaba"))
    keyboard.add(KeyboardButton(text="⬅️ Назад" if language == "ru" else "⬅️ Бозгашт"))
    keyboard.adjust(1, 1, 1, 1)
    return keyboard.as_markup(resize_keyboard=True)

# Новая функция для калькулятора
def get_calculator_yes_no_keyboard(language: str = "ru"):
    """Клавиатура для подтверждения после предупреждения калькулятора"""
    texts = {
        "ru": {
            "yes": "✅ Да, продолжить",
            "no": "❌ Нет, вернуться"
        },
        "tj": {
            "yes": "✅ Ҳа, давом додан",
            "no": "❌ Не, баргаштан"
        }
    }
    
    t = texts[language]
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text=t["yes"]))
    keyboard.add(KeyboardButton(text=t["no"]))
    keyboard.adjust(2)
    return keyboard.as_markup(resize_keyboard=True)