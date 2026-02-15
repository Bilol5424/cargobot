"""
Главный файл запуска бота
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import settings
from database.session import create_tables
import os
from handlers.admin.main_menu import admin_main_router
from handlers.admin.update_status import update_status_router
from handlers.admin.reports import reports_router
from handlers.admin.profile import admin_profile_router  # ИСПРАВЛЕНО
from handlers.admin.add_product import add_product_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Основная функция запуска бота"""
    logger.info("Запуск бота...")

    # Создаем таблицы в базе данных
    try:
        await create_tables()
        logger.info("✅ Таблицы базы данных созданы успешно")
    except Exception as e:
        logger.error(f"❌ Ошибка при создании таблиц: {e}")
        return

    # Инициализация бота и диспетчера
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Проверяем, какие файлы админа существуют
    admin_files = []
    handlers_dir = "handlers"

    if os.path.exists(handlers_dir):
        for file in os.listdir(handlers_dir):
            if file.startswith("admin") and file.endswith(".py"):
                admin_files.append(file[:-3])  # Убираем .py

    logger.info(f"Найдены админские файлы: {admin_files}")

    # Импортируем и регистрируем роутеры
    # 1. Общие обработчики
    from handlers.common import common_router
    dp.include_router(common_router)

    # В функцию main() добавляем:
    from handlers.admin_export import router as admin_export_router
    dp.include_router(admin_export_router)

    # 2. Клиентские обработчики
    from handlers.client.main_menu import main_menu_router
    dp.include_router(main_menu_router)

    from handlers.client.track_codes import track_codes_router
    dp.include_router(track_codes_router)

    from handlers.client.profile import profile_router
    dp.include_router(profile_router)

    from handlers.client.address import address_router
    dp.include_router(address_router)

    from handlers.client.other_menus import other_menus_router
    dp.include_router(other_menus_router)

    # 3. Новые админские роутеры
    dp.include_router(admin_main_router)
    dp.include_router(update_status_router)
    dp.include_router(reports_router)
    dp.include_router(admin_profile_router)  # ИСПРАВЛЕНО
    dp.include_router(add_product_router)

    # 4. Существующие админские файлы - импортируем все найденные
    # admin_export уже зарегистрирован выше, пропускаем его
    for admin_file in admin_files:
        if admin_file == "admin_export":
            continue
        try:
            module_name = f"handlers.{admin_file}"
            module = __import__(module_name, fromlist=['router'])
            if hasattr(module, 'router'):
                dp.include_router(module.router)
                logger.info(f"✅ Загружен модуль: {admin_file}")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при загрузке {admin_file}: {e}")

    # Если нет админских файлов, создаем простой роутер для админов
    if not admin_files:
        logger.info("⚠️ Админские модули не найдены, создаем базовый функционал")
        from aiogram import Router
        from aiogram.filters import Command
        from aiogram.types import Message

        admin_router = Router()

        @admin_router.message(Command("admin"))
        async def admin_command(message: Message):
            await message.answer("👨‍💼 Админ панель (базовый функционал)\n\n"
                                 "Доступные команды:\n"
                                 "/add_track - добавить трек-код\n"
                                 "/stats - статистика")

        dp.include_router(admin_router)

    logger.info("Бот запущен. Ожидание сообщений...")

    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
