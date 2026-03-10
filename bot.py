"""Главный файл запуска бота"""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from database.session import create_tables

# --- СУЩЕСТВУЮЩИЕ АДМИН РОУТЕРЫ ---
from handlers.admin.main_menu import admin_main_router
from handlers.admin.update_status import update_status_router
from handlers.admin.reports import reports_router
from handlers.admin.profile import admin_profile_router
from handlers.admin.add_product import add_product_router
from handlers.admin.bulk_import import bulk_import_router

# --- НОВЫЕ АДМИН ФУНКЦИИ (Reply Keyboard) ---
from handlers.admin.add_track_code import router as add_track_code_router
from handlers.admin.bulk_add_track_codes import router as bulk_add_track_codes_router
from handlers.admin.update_status_bulk import router as update_status_bulk_router
from handlers.admin.search_product import router as search_product_router
from handlers.admin.export_all_products import router as export_all_products_router
from handlers.admin.monthly_report import router as monthly_report_router
from handlers.admin.profile_menu import router as profile_menu_router
from handlers.admin.bulk_update import router as bulk_update_router

# ---------------- ЛОГИРОВАНИЕ ----------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# MAIN
# ============================================================

async def main():
    """Основная функция запуска бота"""

    logger.info("Запуск бота...")

    # ---------- Создание таблиц ----------
    try:
        await create_tables()
        logger.info("✅ Таблицы базы данных созданы успешно")
    except Exception as e:
        logger.error(f"❌ Ошибка при создании таблиц: {e}")
        return

    # ---------- Инициализация ----------
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # ============================================================
    # ПОИСК АДМИН ФАЙЛОВ
    # ============================================================

    admin_files = []
    handlers_dir = "handlers"

    if os.path.exists(handlers_dir):
        for file in os.listdir(handlers_dir):
            if file.startswith("admin") and file.endswith(".py"):
                admin_files.append(file[:-3])

    logger.info(f"Найдены админские файлы: {admin_files}")

    # ============================================================
    # ОБЩИЕ ОБРАБОТЧИКИ
    # ============================================================

    from handlers.common import common_router
    dp.include_router(common_router)

    from handlers.admin_export import router as admin_export_router
    dp.include_router(admin_export_router)

    # ============================================================
    # КЛИЕНТСКИЕ ОБРАБОТЧИКИ
    # ============================================================

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

    # ============================================================
    # СУЩЕСТВУЮЩИЕ АДМИН РОУТЕРЫ
    # ============================================================

    dp.include_router(admin_main_router)
    dp.include_router(update_status_router)
    dp.include_router(reports_router)
    dp.include_router(admin_profile_router)
    dp.include_router(add_product_router)
    dp.include_router(bulk_import_router)

    # ============================================================
    # 🔥 НОВЫЕ АДМИН РОУТЕРЫ (Reply Keyboard функционал)
    # ============================================================

    dp.include_router(add_track_code_router)
    dp.include_router(bulk_add_track_codes_router)
    dp.include_router(update_status_bulk_router)
    dp.include_router(search_product_router)
    dp.include_router(export_all_products_router)
    dp.include_router(monthly_report_router)
    dp.include_router(profile_menu_router)
    dp.include_router(bulk_update_router)

    # ============================================================
    # АВТОИМПОРТ СУЩЕСТВУЮЩИХ ADMIN МОДУЛЕЙ
    # ============================================================

    for admin_file in admin_files:
        if admin_file == "admin_export":
            continue

        try:
            module_name = f"handlers.{admin_file}"
            module = __import__(module_name, fromlist=["router"])

            if hasattr(module, "router"):
                dp.include_router(module.router)
                logger.info(f"✅ Загружен модуль: {admin_file}")

        except Exception as e:
            logger.warning(f"⚠️ Ошибка при загрузке {admin_file}: {e}")

    # ============================================================
    # FALLBACK АДМИН ПАНЕЛЬ
    # ============================================================

    if not admin_files:
        logger.info("⚠️ Админские модули не найдены, создаем базовый функционал")

        from aiogram import Router
        from aiogram.filters import Command
        from aiogram.types import Message

        admin_router = Router()

        @admin_router.message(Command("admin"))
        async def admin_command(message: Message):
            await message.answer(
                "👨‍💼 Админ панель (базовый функционал)\n\n"
                "Доступные команды:\n"
                "/add_track - добавить трек-код\n"
                "/stats - статистика"
            )

        dp.include_router(admin_router)

    # ============================================================
    # ЗАПУСК
    # ============================================================

    logger.info("Бот запущен. Ожидание сообщений...")

    try:
        await dp.start_polling(bot)

    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")

    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}", exc_info=True)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())
