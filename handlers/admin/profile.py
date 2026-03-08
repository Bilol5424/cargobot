"""
Профиль администратора (reply-клавиатура)
"""
import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select, func

from database.models import User, Product
from database.session import async_session_maker  # ИСПРАВЛЕНО
from keyboards.admin import get_back_to_admin_keyboard
from config import settings

logger = logging.getLogger(__name__)
admin_profile_router = Router()


@admin_profile_router.message(F.text == "👨‍💼 Профиль")
async def admin_profile(message: Message):
    if not settings.is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещен")
        return

    user_id = message.from_user.id
    admin_role = settings.get_admin_role(user_id)

    async with async_session_maker() as session:  # ИСПРАВЛЕНО
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        if not user:
            await message.answer(
                "❌ Пользователь не найден в базе данных",
                reply_markup=get_back_to_admin_keyboard()
            )
            return

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

        added_count = await session.scalar(
            select(func.count(Product.id)).where(Product.user_id == user.id)
        ) or 0

        week_ago = datetime.utcnow() - timedelta(days=7)
        updated_count = await session.scalar(
            select(func.count(Product.id)).where(
                Product.updated_at >= week_ago,
                Product.user_id == user.id
            )
        ) or 0

        profile_text += f"📊 Ваша активность:\n"
        profile_text += f"  • Товаров добавлено: {added_count}\n"
        profile_text += f"  • Обновлено за неделю: {updated_count}\n\n"

        total_products = await session.scalar(select(func.count(Product.id))) or 0
        total_users = await session.scalar(select(func.count(User.id))) or 0

        profile_text += f"📈 Статистика системы:\n"
        profile_text += f"  • Всего пользователей: {total_users}\n"
        profile_text += f"  • Всего товаров: {total_products}\n"

        try:
            from sqlalchemy import text
            db_version = await session.execute(text("SELECT sqlite_version()"))
            db_version = db_version.scalar()
            profile_text += f"  • Версия БД: {db_version}\n"
        except:
            pass

        await message.answer(profile_text, reply_markup=get_back_to_admin_keyboard())