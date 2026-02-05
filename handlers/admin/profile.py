"""
Профиль администратора
"""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from database.models import User
from database.session import get_async_session
from keyboards.admin import get_back_to_admin_keyboard
from config import settings

logger = logging.getLogger(__name__)
admin_profile_router = Router()

@admin_profile_router.callback_query(F.data == "admin_profile")
async def admin_profile(callback: CallbackQuery):
    """Профиль администратора"""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    user_id = callback.from_user.id
    admin_role = settings.get_admin_role(user_id)
    
    async with get_async_session() as session:
        # Получаем информацию о пользователе
        query = select(User).where(User.telegram_id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.message.edit_text(
                "❌ Пользователь не найден в базе данных",
                reply_markup=get_back_to_admin_keyboard()
            )
            return
        
        # Формируем информацию профиля
        profile_text = f"👨‍💼 Профиль администратора\n\n"
        
        profile_text += f"📋 Основная информация:\n"
        profile_text += f"  • ID: {user.id}\n"
        profile_text += f"  • Telegram ID: {user.telegram_id}\n"
        profile_text += f"  • Роль: {admin_role}\n"
        
        if user.full_name:
            profile_text += f"  • Имя: {user.full_name}\n"
        
        if user.phone:
            profile_text += f"  • Телефон: {user.phone}\n"
        
        if user.region:
            profile_text += f"  • Регион: {user.region}\n"
        
        profile_text += f"  • Язык: {'Русский' if user.language == 'ru' else 'Таджикский' if user.language == 'tj' else user.language}\n"
        profile_text += f"  • Дата регистрации: {user.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        # Статистика действий админа
        from database.models import Product
        from sqlalchemy import func
        
        # Товары добавленные админом
        added_query = select(func.count(Product.id)).where(Product.user_id == user.id)
        result = await session.execute(added_query)
        added_count = result.scalar() or 0
        
        # Товары обновленные админом (за последнюю неделю)
        week_ago = datetime.utcnow() - timedelta(days=7)
        updated_query = select(func.count(Product.id)).where(
            Product.updated_at >= week_ago,
            Product.user_id == user.id
        )
        result = await session.execute(updated_query)
        updated_count = result.scalar() or 0
        
        profile_text += f"📊 Ваша активность:\n"
        profile_text += f"  • Товаров добавлено: {added_count}\n"
        profile_text += f"  • Обновлено за неделю: {updated_count}\n\n"
        
        # Информация о системе
        from sqlalchemy import text
        
        # Общая статистика системы
        total_products_query = select(func.count(Product.id))
        result = await session.execute(total_products_query)
        total_products = result.scalar() or 0
        
        total_users_query = select(func.count(User.id))
        result = await session.execute(total_users_query)
        total_users = result.scalar() or 0
        
        profile_text += f"📈 Статистика системы:\n"
        profile_text += f"  • Всего пользователей: {total_users}\n"
        profile_text += f"  • Всего товаров: {total_products}\n"
        
        # Версия базы данных (если SQLite)
        try:
            version_query = text("SELECT sqlite_version()")
            result = await session.execute(version_query)
            db_version = result.scalar()
            profile_text += f"  • Версия БД: {db_version}\n"
        except:
            pass
        
        await callback.message.edit_text(
            profile_text,
            reply_markup=get_back_to_admin_keyboard()
        )
    
    await callback.answer()

@admin_profile_router.callback_query(F.data == "admin_system_info")
async def system_info(callback: CallbackQuery):
    """Информация о системе"""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    import platform
    import psutil
    from datetime import datetime
    
    # Собираем системную информацию
    system_text = "🖥️ Информация о системе\n\n"
    
    # Информация о системе
    system_text += "📋 Система:\n"
    system_text += f"  • ОС: {platform.system()} {platform.release()}\n"
    system_text += f"  • Архитектура: {platform.machine()}\n"
    system_text += f"  • Процессор: {platform.processor()}\n\n"
    
    # Использование памяти
    memory = psutil.virtual_memory()
    system_text += "💾 Память:\n"
    system_text += f"  • Всего: {memory.total / (1024**3):.1f} GB\n"
    system_text += f"  • Использовано: {memory.used / (1024**3):.1f} GB\n"
    system_text += f"  • Свободно: {memory.available / (1024**3):.1f} GB\n"
    system_text += f"  • Использование: {memory.percent}%\n\n"
    
    # Диск
    disk = psutil.disk_usage('/')
    system_text += "💿 Диск:\n"
    system_text += f"  • Всего: {disk.total / (1024**3):.1f} GB\n"
    system_text += f"  • Использовано: {disk.used / (1024**3):.1f} GB\n"
    system_text += f"  • Свободно: {disk.free / (1024**3):.1f} GB\n"
    system_text += f"  • Использование: {disk.percent}%\n\n"
    
    # Время работы системы
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    system_text += "⏰ Время работы:\n"
    system_text += f"  • Запуск системы: {boot_time.strftime('%d.%m.%Y %H:%M')}\n"
    system_text += f"  • Аптайм: {uptime.days} дн., {uptime.seconds//3600} ч.\n"
    
    await callback.message.edit_text(
        system_text,
        reply_markup=get_back_to_admin_keyboard()
    )
    
    await callback.answer()