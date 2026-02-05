import os
from typing import Dict, Set
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Настройки приложения"""
    
    # Загружаем значения из .env
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///database.db")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    _ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
    
    @classmethod
    def get_admin_ids(cls) -> Dict[int, str]:
        """Возвращает словарь с ID админов и их ролями"""
        admin_dict = {}
        if not cls._ADMIN_IDS_STR:
            return admin_dict
        
        try:
            # Формат: "1929084151:admin_cn,1929084152:admin_tj"
            parts = cls._ADMIN_IDS_STR.strip().split(',')
            for part in parts:
                if ':' in part:
                    user_id, role = part.split(':', 1)
                    admin_dict[int(user_id.strip())] = role.strip()
                elif part.strip():
                    # Если только ID без роли, назначаем admin_cn по умолчанию
                    admin_dict[int(part.strip())] = 'admin_cn'
        except (ValueError, AttributeError) as e:
            print(f"Ошибка парсинга ADMIN_IDS: {e}")
            
        return admin_dict
    
    @classmethod
    def get_admin_ids_set(cls) -> Set[int]:
        """Возвращает множество ID админов"""
        return set(cls.get_admin_ids().keys())
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Проверяет, является ли пользователь админом"""
        return user_id in cls.get_admin_ids()
    
    @classmethod
    def get_admin_role(cls, user_id: int) -> str:
        """Возвращает роль админа"""
        return cls.get_admin_ids().get(user_id, "client")

# Создаем экземпляр настроек
settings = Settings()

# Добавляем атрибут ADMIN_IDS для обратной совместимости
settings.ADMIN_IDS = settings.get_admin_ids_set()