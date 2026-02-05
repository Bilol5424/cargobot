import re
from typing import Optional, List
from datetime import datetime, timedelta

def parse_phone_number(phone: str) -> Optional[str]:
    """
    Парсинг и нормализация номера телефона
    
    Args:
        phone: Номер телефона в любом формате
        
    Returns:
        str: Нормализованный номер или None
    """
    if not phone:
        return None
    
    # Удаляем все нецифровые символы
    digits = re.sub(r'\D', '', phone)
    
    # Проверяем минимальную длину
    if len(digits) < 10:
        return None
    
    # Если номер начинается с 8 (для России/Таджикистана), заменяем на +7
    if digits.startswith('8') and len(digits) == 11:
        digits = '7' + digits[1:]
    
    # Добавляем + если его нет
    if not digits.startswith('+'):
        digits = '+' + digits
    
    return digits

def validate_email(email: str) -> bool:
    """
    Валидация email адреса
    
    Args:
        email: Email для проверки
        
    Returns:
        bool: Валидный ли email
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def format_datetime(dt: datetime, language: str = "ru") -> str:
    """
    Форматирование даты и времени
    
    Args:
        dt: Дата и время
        language: Язык
        
    Returns:
        str: Отформатированная дата
    """
    formats = {
        "ru": {
            "date": "%d.%m.%Y",
            "datetime": "%d.%m.%Y %H:%M",
            "time": "%H:%M"
        },
        "tj": {
            "date": "%d.%m.%Y",
            "datetime": "%d.%m.%Y %H:%M",
            "time": "%H:%M"
        }
    }
    
    fmt = formats.get(language, formats["ru"])
    return dt.strftime(fmt["datetime"])

def calculate_delivery_date(send_date: datetime, 
                           delivery_days: int = 30) -> datetime:
    """
    Расчет даты доставки
    
    Args:
        send_date: Дата отправки
        delivery_days: Количество дней на доставку
        
    Returns:
        datetime: Ожидаемая дата доставки
    """
    return send_date + timedelta(days=delivery_days)

def split_list(input_list: List, chunk_size: int) -> List[List]:
    """
    Разделение списка на части
    
    Args:
        input_list: Исходный список
        chunk_size: Размер части
        
    Returns:
        List[List]: Список списков
    """
    return [input_list[i:i + chunk_size] for i in range(0, len(input_list), chunk_size)]

def escape_markdown(text: str) -> str:
    """
    Экранирование символов Markdown
    
    Args:
        text: Текст для экранирования
        
    Returns:
        str: Экранированный текст
    """
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Форматирование валюты
    
    Args:
        amount: Сумма
        currency: Валюта
        
    Returns:
        str: Отформатированная сумма
    """
    currency_symbols = {
        "USD": "$",
        "RUB": "₽",
        "EUR": "€",
        "CNY": "¥",
        "TJS": "смн"
    }
    
    symbol = currency_symbols.get(currency, currency)
    
    if currency == "USD":
        return f"{symbol}{amount:.2f}"
    else:
        return f"{amount:.2f} {symbol}"

def get_user_language(telegram_id: int) -> str:
    """
    Получение языка пользователя из БД
    
    Args:
        telegram_id: ID пользователя в Telegram
        
    Returns:
        str: Язык пользователя ('ru' или 'tj')
    """
    # Эта функция должна использовать асинхронный контекст
    # Временно возвращаем русский по умолчанию
    return "ru"