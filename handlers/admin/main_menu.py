from aiogram import Router, F
from aiogram.types import Message
from keyboards.admin import get_admin_main_keyboard
from database.session import async_session_maker
from database.models import User
from sqlalchemy import select
from config import settings

admin_main_router = Router()


@admin_main_router.message(F.text.in_(["/admin", "Админ", "🔙 В главное меню"]))
async def admin_menu(message: Message):
    # Получаем роль и язык администратора
    user_id = message.from_user.id
    admin_role = settings.get_admin_role(user_id)

    async with async_session_maker() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"

    await message.answer(
        "🛠 Админ‑панель",
        reply_markup=get_admin_main_keyboard(role=admin_role, language=language)
    )