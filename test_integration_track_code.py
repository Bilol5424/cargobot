#!/usr/bin/env python3
"""
Интеграционный тест функционала добавления трек-кода
"""
import asyncio
from sqlalchemy import select
from database.session import async_session_maker, create_tables
from database.models import User, Product, UserRole
from database.repository import ProductRepository
from services.track_code_generator import TrackCodeGenerator

async def main():
    print("=" * 60)
    print("ИНТЕГРАЦИОННЫЙ ТЕСТ: ДОБАВЛЕНИЕ ТРЕК-КОДА")
    print("=" * 60)

    # Создаем таблицы
    print("\n1️⃣  Создание таблиц БД...")
    try:
        await create_tables()
        print("   ✅ Таблицы созданы/проверены")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return

    async with async_session_maker() as session:
        # Проверяем/создаем тестового администратора
        print("\n2️⃣  Проверка администратора в БД...")
        admin_user = await session.execute(
            select(User).where(User.telegram_id == 1929084151)
        )
        admin_user = admin_user.scalar_one_or_none()

        if admin_user is None:
            print("   Администратор не найден, создаем...")
            admin_user = User(
                telegram_id=1929084151,
                full_name="Test Admin CN",
                phone="+86 123456789",
                language="ru",
                role=UserRole.ADMIN_CN
            )
            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)
            print(f"   ✅ Администратор создан (ID: {admin_user.id})")
        else:
            print(f"   ✅ Администратор найден (ID: {admin_user.id})")

        # Генерируем трек-код
        print("\n3️⃣  Генерация трек-кода...")
        track_code = TrackCodeGenerator.generate_track_code(
            user_id=1929084151,
            product_type="CN"
        )
        print(f"   ✅ Сгенерирован трек-код: {track_code}")

        # Проверяем уникальность
        print("\n4️⃣  Проверка уникальности...")
        existing = await session.execute(
            select(Product).where(Product.track_code == track_code)
        )
        existing_product = existing.scalar_one_or_none()

        if existing_product is None:
            print(f"   ✅ Трек-код уникален (не дублируется)")
        else:
            print(f"   ⚠️  Трек-код уже существует в БД")

        # Создаем Product
        print("\n5️⃣  Создание Product в БД...")
        repo = ProductRepository(session)
        try:
            product = await repo.create_product(
                track_code=track_code,
                user_id=admin_user.id,
                country_from="China"
            )
            print(f"   ✅ Product создан:")
            print(f"      • ID: {product.id}")
            print(f"      • Трек-код: {product.track_code}")
            print(f"      • Статус: {product.status.value}")
            print(f"      • Страна: {product.country_from}")
        except Exception as e:
            print(f"   ❌ Ошибка создания Product: {e}")
            return

        # Проверяем, что Product в БД
        print("\n6️⃣  Проверка Product в БД...")
        verify = await session.execute(
            select(Product).where(Product.track_code == track_code)
        )
        verify_product = verify.scalar_one_or_none()

        if verify_product:
            print(f"   ✅ Product найден в БД:")
            print(f"      • Трек-код: {verify_product.track_code}")
            print(f"      • Дата создания: {verify_product.created_at}")
            print(f"      • Admin ID: {verify_product.user_id}")
        else:
            print(f"   ❌ Product не найден в БД!")
            return

        # Получаем всю информацию для сообщения
        print("\n7️⃣  Формирование ответного сообщения...")

        # Русский вариант
        ru_message = (
            f"📦 Новый трек-код создан\n\n"
            f"🔐 Трек-код: {product.track_code}\n"
            f"✅ Статус: Создан\n"
            f"🌍 Страна: Китай"
        )
        print("   📝 Русский вариант:")
        for line in ru_message.split('\n'):
            print(f"      {line}")

        # Таджикский вариант
        tj_message = (
            f"📦 Рамзи навъи трек созданишуд\n\n"
            f"🔐 Рамзи трек: {product.track_code}\n"
            f"✅ Ҳолат: Созданишуд\n"
            f"🌍 Кишвар: Чин"
        )
        print("\n   📝 Таджикский вариант:")
        for line in tj_message.split('\n'):
            print(f"      {line}")

    print("\n" + "=" * 60)
    print("✅ ИНТЕГРАЦИОННЫЙ ТЕСТ УСПЕШНО ЗАВЕРШЕН")
    print("=" * 60)
    print("\n🎉 Функционал готов к использованию!")
    print("   Администратор может использовать кнопку '➕ Добавить трек-код'")
    print("   для автоматического создания новых посылок.")

if __name__ == "__main__":
    asyncio.run(main())

