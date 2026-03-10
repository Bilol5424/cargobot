# keyboards/admin.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_main_keyboard(role: str = "admin_cn", language: str = "ru") -> ReplyKeyboardMarkup:
    """
    Главное меню администратора (reply-клавиатура).
    """
    texts = {
        "ru": {
            "add_product": "➕ Добавить трек-код",
            "bulk_import": "📥 Массовое добавление",
            "update_status": "🔄 Обновить статусы",
            "reports": "📊 Отчеты",
            "profile": "👨‍💼 Профиль",
            "search": "🔍 Поиск",
            "china_warehouse": "🇨🇳 Китайский склад",
            "tj_warehouse": "🇹🇯 Таджикский склад",
            "settings": "⚙️ Настройки",
            "main_menu": "🔙 В главное меню",
        },
        "tj": {
            "add_product": "➕ Илова кардани рамз",
            "bulk_import": "📥 Боркунии оммавӣ",
            "update_status": "🔄 Навсозии статус",
            "reports": "📊 Ҳисоботҳо",
            "profile": "👨‍💼 Профил",
            "search": "🔍 Ҷустуҷӯ",
            "china_warehouse": "🇨🇳 Анбори Чин",
            "tj_warehouse": "🇹🇯 Анбори Тоҷикистон",
            "settings": "⚙️ Танзимот",
            "main_menu": "🔙 Ба менюи асосӣ",
        }
    }
    t = texts[language]

    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=t["add_product"]),
        KeyboardButton(text=t["bulk_import"]),
        width=2
    )
    builder.row(
        KeyboardButton(text=t["update_status"]),
        KeyboardButton(text=t["reports"]),
        width=2
    )
    builder.row(
        KeyboardButton(text=t["profile"]),
        width=1
    )
    builder.row(
        KeyboardButton(text=t["search"]),
        width=1
    )
    if role == "admin_cn":
        builder.row(KeyboardButton(text=t["china_warehouse"]), width=1)
    elif role == "admin_tj":
        builder.row(KeyboardButton(text=t["tj_warehouse"]), width=1)
    builder.row(
        KeyboardButton(text=t["settings"]),
        KeyboardButton(text=t["main_menu"]),
        width=2
    )
    return builder.as_markup(resize_keyboard=True)


def get_status_update_menu_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    """Меню выбора способа обновления статусов."""
    texts = {
        "ru": {
            "by_track": "🔍 По трек-коду",
            "by_date": "📅 По дате отправки",
            "bulk": "📋 Массовое обновление",
            "back": "🔙 Назад",
        },
        "tj": {
            "by_track": "🔍 Аз рӯи рамз",
            "by_date": "📅 Аз рӯи сана",
            "bulk": "📋 Навсозии оммавӣ",
            "back": "🔙 Бозгашт",
        }
    }
    t = texts[language]
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=t["by_track"]),
        KeyboardButton(text=t["by_date"]),
        width=2
    )
    builder.row(KeyboardButton(text=t["bulk"]), width=1)
    builder.row(KeyboardButton(text=t["back"]), width=1)
    return builder.as_markup(resize_keyboard=True)


def get_status_keyboard(is_bulk: bool = False, language: str = "ru") -> ReplyKeyboardMarkup:
    """Клавиатура выбора статуса."""
    status_names = {
        "ru": {
            "CREATED": "📝 Создан",
            "IN_CHINA_WAREHOUSE": "🇨🇳 В Китае",
            "IN_TRANSIT": "✈️ В пути",
            "ARRIVED_TJ": "🇹🇯 Прибыл в TJ",
            "READY_FOR_PICKUP": "✅ Готов к выдаче",
            "DELIVERED": "📦 Доставлен",
            "CANCELLED": "❌ Отменен",
            "PROBLEM": "⚠️ Проблема",
        },
        "tj": {
            "CREATED": "📝 Сохта шуд",
            "IN_CHINA_WAREHOUSE": "🇨🇳 Дар Чин",
            "IN_TRANSIT": "✈️ Дар роҳ",
            "ARRIVED_TJ": "🇹🇯 Расид ба Тоҷикистон",
            "READY_FOR_PICKUP": "✅ Омода ба супоридан",
            "DELIVERED": "📦 Супорида шуд",
            "CANCELLED": "❌ Бекор карда шуд",
            "PROBLEM": "⚠️ Мушкилот",
        }
    }
    t = status_names[language]
    # Все коды статусов в том же порядке
    status_codes = [
        "CREATED",
        "IN_CHINA_WAREHOUSE",
        "IN_TRANSIT",
        "ARRIVED_TJ",
        "READY_FOR_PICKUP",
        "DELIVERED",
        "CANCELLED",
        "PROBLEM",
    ]
    builder = ReplyKeyboardBuilder()
    for code in status_codes:
        builder.add(KeyboardButton(text=t[code]))
    builder.adjust(2, 2, 2, 2)  # по две в ряд
    builder.row(KeyboardButton(text="🔙 Назад" if language == "ru" else "🔙 Бозгашт"))
    return builder.as_markup(resize_keyboard=True)


def get_reports_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    """Меню отчетов."""
    texts = {
        "ru": {
            "general": "📈 Общая статистика",
            "by_status": "📊 По статусам",
            "by_period": "📅 За период",
            "export": "💾 Экспорт данных",
            "back": "🔙 Назад",
        },
        "tj": {
            "general": "📈 Омори умумӣ",
            "by_status": "📊 Аз рӯи статус",
            "by_period": "📅 Дар давраи вақтӣ",
            "export": "💾 Экспорти маълумот",
            "back": "🔙 Бозгашт",
        }
    }
    t = texts[language]
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=t["general"]))
    builder.add(KeyboardButton(text=t["by_status"]))
    builder.add(KeyboardButton(text=t["by_period"]))
    builder.add(KeyboardButton(text=t["export"]))
    builder.row(KeyboardButton(text=t["back"]))
    return builder.as_markup(resize_keyboard=True)


def get_back_to_admin_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    """Кнопка 'Назад' в админ-панель."""
    text = "🔙 Назад в админ-панель" if language == "ru" else "🔙 Бозгашт ба панели админ"
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=text))
    return builder.as_markup(resize_keyboard=True)


def get_product_categories_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    """Клавиатура выбора категории товара."""
    categories = {
        "ru": [
            "📱 Электроника",
            "👕 Одежда",
            "👟 Обувь",
            "🏠 Бытовая техника",
            "💄 Косметика",
            "🧸 Игрушки",
            "🚗 Автозапчасти",
            "⚽ Спорттовары",
            "📦 Другое",
        ],
        "tj": [
            "📱 Электроника",
            "👕 Либос",
            "👟 Пойафзол",
            "🏠 Асбобҳои хонагӣ",
            "💄 Косметика",
            "🧸 Бозичаҳо",
            "🚗 Қисмҳои автомобил",
            "⚽ Ашёҳои варзишӣ",
            "📦 Дигар",
        ]
    }
    builder = ReplyKeyboardBuilder()
    for cat in categories[language]:
        builder.add(KeyboardButton(text=cat))
    builder.adjust(2, 2, 2, 3)
    builder.row(KeyboardButton(text="🔙 Назад" if language == "ru" else "🔙 Бозгашт"))
    return builder.as_markup(resize_keyboard=True)


def get_yes_no_keyboard(prefix: str, language: str = "ru") -> ReplyKeyboardMarkup:
    """
    Клавиатура Да/Нет.
    prefix не используется для reply, оставлен для совместимости.
    """
    texts = {
        "ru": ["✅ Да", "❌ Нет"],
        "tj": ["✅ Ҳа", "❌ Не"],
    }
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=texts[language][0]))
    builder.add(KeyboardButton(text=texts[language][1]))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def get_bulk_import_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    """Меню выбора способа массовой загрузки."""
    texts = {
        "ru": {
            "text_list": "📝 Список трек-кодов",
            "excel": "📄 Excel файл",
            "download_template": "📥 Скачать шаблон Excel",
            "manual": "✍️ Ручной ввод трек-кода",
            "back": "🔙 Назад",
        },
        "tj": {
            "text_list": "📝 Рӯйхати рамзҳо",
            "excel": "📄 Файли Excel",
            "download_template": "📥 Боргирии шаблон",
            "manual": "✍️ Воридкунии дастӣ",
            "back": "🔙 Бозгашт",
        }
    }
    t = texts[language]
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=t["text_list"]),
        KeyboardButton(text=t["excel"]),
        width=2
    )
    builder.row(
        KeyboardButton(text=t["download_template"]),
        width=1
    )
    builder.row(
        KeyboardButton(text=t["manual"]),
        width=1
    )
    builder.row(KeyboardButton(text=t["back"]), width=1)
    return builder.as_markup(resize_keyboard=True)


def get_status_selection_keyboard(language: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура для выбора статуса товара."""
    statuses = {
        "ru": {
            "created": "📝 Создан",
            "china_warehouse": "🇨🇳 В Китае",
            "in_transit": "✈️ В пути",
            "tajikistan_warehouse": "🇹🇯 Прибыл на склад",
            "ready_for_pickup": "📍 На выдаче",
            "delivered": "✅ Выдан",
            "cancelled": "❌ Отменен",
            "problem": "⚠️ Проблема",
        },
        "tj": {
            "created": "📝 Сохта шуд",
            "china_warehouse": "🇨🇳 Дар Чин",
            "in_transit": "✈️ Дар роҳ",
            "tajikistan_warehouse": "🇹🇯 Дар анбор расид",
            "ready_for_pickup": "📍 Барои супоридан омода",
            "delivered": "✅ Супорида шуд",
            "cancelled": "❌ Бекор шуд",
            "problem": "⚠️ Мушкилот",
        }
    }

    status_dict = statuses.get(language, statuses["ru"])
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=status)]
        for status, name in status_dict.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# Для обратной совместимости
get_admin_main_menu = get_admin_main_keyboard