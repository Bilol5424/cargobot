#!/usr/bin/env python3
"""Тестирование генератора трек-кодов"""

from services.track_code_generator import TrackCodeGenerator

# Генерируем тестовые трек-коды
print("=" * 50)
print("ТЕСТИРОВАНИЕ ГЕНЕРАТОРА ТРЕК-КОДОВ")
print("=" * 50)

code1 = TrackCodeGenerator.generate_track_code(user_id=1929084151, product_type='CN')
print(f"\n✓ Трек-код (Админ Китай): {code1}")

code2 = TrackCodeGenerator.generate_track_code(user_id=1929084152, product_type='TJ')
print(f"✓ Трек-код (Админ Таджикистан): {code2}")

code3 = TrackCodeGenerator.generate_track_code(user_id=123456, product_type='GEN')
print(f"✓ Трек-код (Generic): {code3}")

# Декодирование
print("\n" + "=" * 50)
print("ДЕКОДИРОВАНИЕ ТРЕК-КОДОВ")
print("=" * 50)

decoded1 = TrackCodeGenerator.decode_track_code(code1)
print(f"\nДекодированные данные для {code1}:")
for key, value in decoded1.items():
    print(f"  • {key}: {value}")

# Генерация нескольких кодов
print("\n" + "=" * 50)
print("МАССОВАЯ ГЕНЕРАЦИЯ")
print("=" * 50)

bulk_codes = TrackCodeGenerator.generate_bulk_codes(count=5, user_id=1929084151)
print(f"\n✓ Сгенерировано 5 уникальных трек-кодов:")
for i, code in enumerate(bulk_codes, 1):
    print(f"  {i}. {code}")

print("\n" + "=" * 50)
print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
print("=" * 50)

