# keyboards/admin.py - дополняем существующий файл
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_admin_main_keyboard(role: str = "admin_cn"):
    """Главное меню админа"""
    keyboard = InlineKeyboardBuilder()
    
    # Основные кнопки для всех админов
    keyboard.button(text="📦 Добавить трек-код", callback_data="admin_add_product")
    keyboard.button(text="🔄 Обновить статусы", callback_data="admin_update_status")
    keyboard.button(text="📊 Отчеты", callback_data="admin_reports")
    keyboard.button(text="👨‍💼 Профиль", callback_data="admin_profile")
    
    # Дополнительные функции
    keyboard.button(text="📋 Все товары", callback_data="admin_all_products")
    keyboard.button(text="🔍 Поиск", callback_data="admin_search")
    
    # Специфичные кнопки в зависимости от роли
    if role == "admin_cn":
        keyboard.button(text="🇨🇳 Китайский склад", callback_data="admin_china_warehouse")
    elif role == "admin_tj":
        keyboard.button(text="🇹🇯 Таджикский склад", callback_data="admin_tj_warehouse")
    
    keyboard.button(text="⚙️ Настройки", callback_data="admin_settings")
    keyboard.button(text="🔙 В главное меню", callback_data="main_menu")
    
    keyboard.adjust(2, 2, 2, 1, 1)
    return keyboard.as_markup()

def get_status_update_menu_keyboard():
    """Меню обновления статусов"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.button(text="🔍 По трек-коду", callback_data="update_by_track")
    keyboard.button(text="📅 По дате отправки", callback_data="update_by_date")
    keyboard.button(text="📋 Массовое обновление", callback_data="update_bulk")
    keyboard.button(text="🔙 Назад", callback_data="admin_menu")
    
    keyboard.adjust(2, 1, 1)
    return keyboard.as_markup()

def get_status_keyboard(is_bulk: bool = False):
    """Клавиатура выбора статуса"""
    statuses = [
        ("CREATED", "📝 Создан"),
        ("IN_CHINA_WAREHOUSE", "🇨🇳 В Китае"),
        ("IN_TRANSIT", "✈️ В пути"),
        ("ARRIVED_TJ", "🇹🇯 Прибыл в TJ"),
        ("READY_FOR_PICKUP", "✅ Готов к выдаче"),
        ("DELIVERED", "📦 Доставлен"),
        ("CANCELLED", "❌ Отменен"),
        ("PROBLEM", "⚠️ Проблема"),
    ]
    
    keyboard = InlineKeyboardBuilder()
    
    for status_code, status_text in statuses:
        callback_data = f"bulk_status_{status_code}" if is_bulk else f"set_status_{status_code}"
        keyboard.button(text=status_text, callback_data=callback_data)
    
    keyboard.button(text="🔙 Назад", callback_data="admin_update_status")
    keyboard.adjust(2, 2, 2, 2, 1)
    return keyboard.as_markup()

def get_reports_keyboard():
    """Клавиатура отчетов"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.button(text="📦 Доставлено за месяц", callback_data="report_monthly_delivered")
    keyboard.button(text="📥 Принято за месяц", callback_data="report_monthly_received")
    keyboard.button(text="💰 Финансовый отчет", callback_data="report_financial")
    keyboard.button(text="👥 Статистика пользователей", callback_data="report_user_statistics")
    keyboard.button(text="💾 Экспорт в Excel", callback_data="report_database_export")
    keyboard.button(text="🖥️ Информация о системе", callback_data="admin_system_info")
    keyboard.button(text="🔙 Назад", callback_data="admin_menu")
    
    keyboard.adjust(2, 2, 2, 1)
    return keyboard.as_markup()

def get_back_to_admin_keyboard():
    """Кнопка назад в админ-меню"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Назад в админ-панель", callback_data="admin_menu")
    return keyboard.as_markup()