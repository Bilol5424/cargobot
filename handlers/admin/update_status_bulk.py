from aiogram import Router, F
from aiogram.types import Message
from keyboards.admin_extra import status_keyboard
from services.admin_status_service import AdminStatusService
from database.repository import ProductRepository

router = Router()


@router.message(F.text == "🔄 Массово обновить статус")
async def choose_status(message: Message):
    await message.answer(
        "Выберите новый статус:",
        reply_markup=status_keyboard
    )


@router.message(F.text.in_(["🚚 В пути", "📦 Прибыл", "✅ Выдан"]))
async def ask_codes(message: Message):
    await message.answer("Отправьте список трек‑кодов")


@router.message()
async def update_status(message: Message):
    lines = message.text.split()
    service = AdminStatusService(ProductRepository())

    updated = await service.bulk_update(lines, "updated")

    await message.answer(f"🔄 Обновлено: {len(updated)}")
