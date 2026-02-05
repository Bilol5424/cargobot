"""
Модуль для работы с базой данных
"""
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from config import settings

# Создаем базовый класс для моделей
Base = declarative_base()

# Создаем асинхронный движок базы данных
engine = create_async_engine(
    settings.DB_URL,
    echo=False,  # Установите True для отладки SQL запросов
    future=True
)

# Создаем фабрику сессий
async_session_maker = async_sessionmaker(
    engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронный генератор сессий базы данных.
    Использование:
        async with get_async_session() as session:
            # работа с сессией
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

async def create_tables():
    """
    Создание всех таблиц в базе данных.
    Вызывается при старте приложения.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Таблицы базы данных созданы успешно")

async def drop_tables():
    """
    Удаление всех таблиц (только для тестирования!)
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("🗑️ Все таблицы удалены")

async def get_db():
    """Альтернативное название для get_async_session (для обратной совместимости)"""
    async with async_session_maker() as session:
        yield session

# Для обратной совместимости с существующим кодом
async def get_session():
    """Альтернативное название для get_async_session"""
    return get_async_session()