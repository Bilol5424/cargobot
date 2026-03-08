from aiogram import Router, F
from aiogram.types import Message
from keyboards.admin_extra import admin_main_keyboard

admin_main_router = Router()


@admin_main_router.message(F.text.in_(["/admin", "Админ", "🔙 В главное меню"]))
async def admin_menu(message: Message):
    await message.answer(
        "🛠 Админ‑панель",
        reply_markup=admin_main_keyboard
    )