from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_product_categories_keyboard(language: str = "ru"):
    """Клавиатура для выбора категории товара"""
    categories = {
        "ru": {
            "electronics": "📱 Электроника",
            "clothing": "👕 Одежда",
            "shoes": "👟 Обувь",
            "home_appliances": "🏠 Бытовая техника",
            "beauty": "💄 Косметика",
            "toys": "🧸 Игрушки",
            "automotive": "🚗 Автозапчасти",
            "sports": "⚽ Спорттовары",
            "other": "📦 Другое",
            "back": "⬅️ Назад",
            "cancel": "❌ Отмена"
        },
        "tj": {
            "electronics": "📱 Электроника",
            "clothing": "👕 Либос",
            "shoes": "👟 Пойафзол",
            "home_appliances": "🏠 Асбобҳои хонагӣ",
            "beauty": "💄 Косметика",
            "toys": "🧸 Бозичаҳо",
            "automotive": "🚗 Қисмҳои автомобил",
            "sports": "⚽ Ашёҳои варзишӣ",
            "other": "📦 Дигар",
            "back": "⬅️ Бозгашт",
            "cancel": "❌ Бекор кардан"
        }
    }
    
    t = categories[language]
    keyboard = ReplyKeyboardBuilder()
    
    keyboard.add(KeyboardButton(text=t["electronics"]))
    keyboard.add(KeyboardButton(text=t["clothing"]))
    keyboard.add(KeyboardButton(text=t["shoes"]))
    keyboard.add(KeyboardButton(text=t["home_appliances"]))
    keyboard.add(KeyboardButton(text=t["beauty"]))
    keyboard.add(KeyboardButton(text=t["toys"]))
    keyboard.add(KeyboardButton(text=t["automotive"]))
    keyboard.add(KeyboardButton(text=t["sports"]))
    keyboard.add(KeyboardButton(text=t["other"]))
    keyboard.add(KeyboardButton(text=t["back"]))
    keyboard.add(KeyboardButton(text=t["cancel"]))
    
    keyboard.adjust(2, 2, 2, 2, 1, 2)
    return keyboard.as_markup(resize_keyboard=True)

def get_special_info_keyboard(language: str = "ru"):
    """Клавиатура для специальной информации о товаре"""
    texts = {
        "ru": {
            "fragile": "Хрупкий",
            "battery": "С батареей",
            "liquid": "Жидкость",
            "none": "Нет особых свойств",
            "back": "⬅️ Назад",
            "cancel": "❌ Отмена"
        },
        "tj": {
            "fragile": "Нозук",
            "battery": "Бо батарея",
            "liquid": "Моеъ",
            "none": "Хусусияти махсус нест",
            "back": "⬅️ Бозгашт",
            "cancel": "❌ Бекор кардан"
        }
    }
    
    t = texts[language]
    keyboard = ReplyKeyboardBuilder()
    
    keyboard.add(KeyboardButton(text=t["fragile"]))
    keyboard.add(KeyboardButton(text=t["battery"]))
    keyboard.add(KeyboardButton(text=t["liquid"]))
    keyboard.add(KeyboardButton(text=t["none"]))
    keyboard.add(KeyboardButton(text=t["back"]))
    keyboard.add(KeyboardButton(text=t["cancel"]))
    
    keyboard.adjust(2, 2, 2)
    return keyboard.as_markup(resize_keyboard=True)

def get_edit_product_keyboard(language: str = "ru"):
    """Клавиатура для редактирования товара"""
    texts = {
        "ru": {
            "edit_name": "📝 Изменить название",
            "edit_desc": "📝 Изменить описание",
            "edit_quantity": "🔢 Изменить количество",
            "edit_price": "💰 Изменить цену",
            "edit_weight": "⚖️ Изменить вес",
            "edit_category": "🏷️ Изменить категорию",
            "back": "⬅️ Назад",
            "cancel": "❌ Отмена"
        },
        "tj": {
            "edit_name": "📝 Тағйир додани ном",
            "edit_desc": "📝 Тағйир додани тавсиф",
            "edit_quantity": "🔢 Тағйир додани миқдор",
            "edit_price": "💰 Тағйир додани нарх",
            "edit_weight": "⚖️ Тағйир додани вазн",
            "edit_category": "🏷️ Тағйир додани гурӯҳ",
            "back": "⬅️ Бозгашт",
            "cancel": "❌ Бекор кардан"
        }
    }
    
    t = texts[language]
    keyboard = ReplyKeyboardBuilder()
    
    keyboard.add(KeyboardButton(text=t["edit_name"]))
    keyboard.add(KeyboardButton(text=t["edit_desc"]))
    keyboard.add(KeyboardButton(text=t["edit_quantity"]))
    keyboard.add(KeyboardButton(text=t["edit_price"]))
    keyboard.add(KeyboardButton(text=t["edit_weight"]))
    keyboard.add(KeyboardButton(text=t["edit_category"]))
    keyboard.add(KeyboardButton(text=t["back"]))
    keyboard.add(KeyboardButton(text=t["cancel"]))
    
    keyboard.adjust(2, 2, 2, 2)
    return keyboard.as_markup(resize_keyboard=True)

def get_yes_no_keyboard(language: str = "ru", prefix: str = ""):
    """Клавиатура Да/Нет"""
    texts = {
        "ru": {
            "yes": "✅ Да",
            "no": "❌ Нет",
            "back": "⬅️ Назад",
            "cancel": "❌ Отмена"
        },
        "tj": {
            "yes": "✅ Ҳа",
            "no": "❌ Не",
            "back": "⬅️ Бозгашт",
            "cancel": "❌ Бекор кардан"
        }
    }
    
    t = texts[language]
    keyboard = ReplyKeyboardBuilder()
    
    keyboard.add(KeyboardButton(text=t["yes"]))
    keyboard.add(KeyboardButton(text=t["no"]))
    keyboard.add(KeyboardButton(text=t["back"]))
    keyboard.add(KeyboardButton(text=t["cancel"]))
    
    keyboard.adjust(2, 2)
    return keyboard.as_markup(resize_keyboard=True)