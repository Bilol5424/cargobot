"""
Главное меню администратора
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config import settings

from keyboards.admin import get_admin_main_keyboard

logger = logging.getLogger(__name__)
admin_main_router = Router()

@admin_main_router.message(Command("admin"))
async def admin_command(message: Message):
    """Команда /admin для админов"""
    if not settings.is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещен")
        return
    
    admin_role = settings.get_admin_role(message.from_user.id)
    await message.answer(
        f"👨‍💼 Админ панель | Роль: {admin_role}\n\n"
        "Выберите действие:",
        reply_markup=get_admin_main_keyboard(admin_role)
    )

@admin_main_router.callback_query(F.data == "admin_menu")
async def admin_menu_callback(callback: CallbackQuery):
    """Возврат в главное меню админа"""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    admin_role = settings.get_admin_role(callback.from_user.id)
    await callback.message.edit_text(
        f"👨‍💼 Админ панель | Роль: {admin_role}\n\n"
        "Выберите действие:",
        reply_markup=get_admin_main_keyboard(admin_role)
    )
    await callback.answer()