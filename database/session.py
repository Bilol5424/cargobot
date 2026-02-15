"""
Модуль для работы с базой данных
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from config import settings

# Базовый класс моделей
Base = declarative_base()

# Асинхронный движок
engine = create_async_engine(
    settings.DB_URL,
    echo=False,
    future=True,
)

# Фабрика сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Основной генератор сессий"""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 🔥 ВАЖНО — для обратной совместимости
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Alias для старого кода"""
    async for session in get_async_session():
        yield session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Alias для старого кода"""
    async for session in get_async_session():
        yield session


async def create_tables():
    """Создание таблиц"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Таблицы базы данных созданы успешно")


# ✅ ВОТ ЭТОГО НЕ ХВАТАЛО
async def drop_tables():
    """Удаление таблиц (только для тестов!)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("🗑️ Все таблицы удалены")
