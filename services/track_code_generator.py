"""
Генератор понятных трек-кодов
"""
import random
import string
from datetime import datetime
from typing import Dict, List

class TrackCodeGenerator:
    """Генератор понятных трек-кодов"""
    
    @staticmethod
    def generate_track_code(user_id: int, product_type: str = "GEN") -> str:
        """
        Генерация понятного трек-кода:
        Формат: TTYYMMDDUSERID{продукт}{случайная часть}
        
        TT - тип товара (CN-Китай, US-США, EU-Европа, GEN-общий)
        YYMMDD - дата (год/месяц/день)
        USERID - последние 4 цифры ID пользователя
        продукт - 2 буквы типа продукта
        случайная часть - 4 случайные буквы
        """
        
        # Типы товаров и их коды
        product_codes = {
            "electronics": "EL",
            "clothing": "CL",
            "shoes": "SH",
            "home_appliances": "HM",
            "beauty": "BT",
            "toys": "TY",
            "automotive": "AU",
            "sports": "SP",
            "other": "OT"
        }
        
        # Текущая дата
        now = datetime.now()
        date_part = now.strftime("%y%m%d")
        
        # ID пользователя (последние 4 цифры)
        user_part = str(user_id)[-4:].zfill(4)
        
        # Код типа товара
        product_code = product_codes.get(product_type.lower(), "GN")
        
        # Случайная часть (4 буквы)
        random_part = ''.join(random.choices(string.ascii_uppercase, k=4))
        
        return f"{product_type.upper()[:2]}{date_part}{user_part}{product_code}{random_part}"

    @staticmethod
    def decode_track_code(track_code: str) -> Dict[str, str]:
        """Декодирование трек-кода для понимания его структуры"""
        if len(track_code) < 18:
            return {}
        
        return {
            "product_type": track_code[:2],
            "date": f"20{track_code[2:4]}-{track_code[4:6]}-{track_code[6:8]}",
            "user_id_suffix": track_code[8:12],
            "category": track_code[12:14],
            "random": track_code[14:18]
        }
    
    @staticmethod
    def generate_bulk_codes(count: int, user_id: int) -> List[str]:
        """Генерация нескольких уникальных трек-кодов"""
        codes = set()
        while len(codes) < count:
            code = TrackCodeGenerator.generate_track_code(user_id)
            codes.add(code)
        return list(codes)