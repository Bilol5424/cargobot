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
from keyboards.admin import get_back_to_admin_keyboard, get_admin_main_keyboard
from config import settings

logger = logging.getLogger(__name__)
admin_profile_router = Router()


@admin_profile_router.message(F.text.in_(["👨‍💼 Профиль", "👤 Профиль администратора", "👨‍💼 Профил"]))
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

        # Определяем язык
        language = user.language if user else "ru"
        
        # Тексты на русском и таджикском
        texts = {
            "ru": {
                "title": "👨‍💼 Профиль администратора",
                "info": "📋 Основная информация:",
                "id": "ID",
                "tg_id": "Telegram ID",
                "role": "Роль",
                "name": "Имя",
                "phone": "Телефон",
                "region": "Регион",
                "language": "Язык",
                "created": "Дата регистрации",
                "activity": "📊 Ваша активность:",
                "products_added": "Товаров добавлено",
                "updated_week": "Обновлено за неделю",
                "stats": "📈 Статистика системы:",
                "total_users": "Всего пользователей",
                "total_products": "Всего товаров",
                "db_version": "Версия БД",
                "russian": "Русский",
                "tajik": "Таджикский",
            },
            "tj": {
                "title": "👨‍💼 Профили администратор",
                "info": "📋 Маълумоти асосӣ:",
                "id": "ID",
                "tg_id": "Telegram ID",
                "role": "Мансаб",
                "name": "Ном",
                "phone": "Телефон",
                "region": "Минтақа",
                "language": "Забон",
                "created": "Санаи қайд намудан",
                "activity": "📊 Фаъолияти шумо:",
                "products_added": "Маҳсулот иловашуда",
                "updated_week": "Нав карда шуда ҳафта",
                "stats": "📈 Омори система:",
                "total_users": "Ҳамагӣ корбарон",
                "total_products": "Ҳамаи маҳсулот",
                "db_version": "Нусхаи БД",
                "russian": "Русӣ",
                "tajik": "Тоҷикӣ",
            }
        }
        
        t = texts[language]
        
        # Определяем языковое название
        lang_name = t["russian"] if language == "ru" else t["tajik"] if language == "tj" else language
        
        # Определяем роль
        role_names = {
            "admin_cn": "Admin (Китай)",
            "admin_tj": "Admin (Таджикистан)",
            "admin": "Admin"
        }
        admin_role_display = role_names.get(admin_role, admin_role)
        
        profile_text = f"{t['title']}\n\n"
        profile_text += f"{t['info']}\n"
        profile_text += f"  • {t['id']}: {user.id}\n"
        profile_text += f"  • {t['tg_id']}: {user.telegram_id}\n"
        profile_text += f"  • {t['role']}: {admin_role_display}\n"
        if user.full_name:
            profile_text += f"  • {t['name']}: {user.full_name}\n"
        if user.phone:
            profile_text += f"  • {t['phone']}: {user.phone}\n"
        if user.region:
            profile_text += f"  • {t['region']}: {user.region}\n"
        profile_text += f"  • {t['language']}: {lang_name}\n"
        profile_text += f"  • {t['created']}: {user.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"

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

        profile_text += f"{t['activity']}\n"
        profile_text += f"  • {t['products_added']}: {added_count}\n"
        profile_text += f"  • {t['updated_week']}: {updated_count}\n\n"

        total_products = await session.scalar(select(func.count(Product.id))) or 0
        total_users = await session.scalar(select(func.count(User.id))) or 0

        profile_text += f"{t['stats']}\n"
        profile_text += f"  • {t['total_users']}: {total_users}\n"
        profile_text += f"  • {t['total_products']}: {total_products}\n"

        try:
            from sqlalchemy import text
            db_version = await session.execute(text("SELECT sqlite_version()"))
            db_version = db_version.scalar()
            profile_text += f"  • {t['db_version']}: {db_version}\n"
        except:
            pass

        await message.answer(profile_text, reply_markup=get_back_to_admin_keyboard(language))


@admin_profile_router.message(F.text.in_(["🔙 Назад в админ-панель", "🔙 Бозгашт ба панели админ"]))
async def back_to_admin_menu(message: Message):
    """Возврат в главное меню администратора."""
    if not settings.is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещен")
        return

    # Определяем язык пользователя
    user_id = message.from_user.id
    admin_role = settings.get_admin_role(user_id)

    async with async_session_maker() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"

    # Тексты для разных языков
    texts = {
        "ru": "🛠 Админ-панель",
        "tj": "🛠 Панели админ"
    }

    await message.answer(
        texts.get(language, texts["ru"]),
        reply_markup=get_admin_main_keyboard(role=admin_role, language=language)
    )