from aiogram import Router, F
from aiogram.types import Message
from keyboards.admin_extra import bulk_add_keyboard
from services.admin_product_service import AdminProductService
from database.repository import ProductRepository

router = Router()


@router.message(F.text == "📥 Массовое добавление")
async def bulk_menu(message: Message):
    await message.answer(
        "Выберите способ добавления:",
        reply_markup=bulk_add_keyboard
    )


@router.message(F.text == "📝 Ввести список")
async def bulk_text(message: Message):
    await message.answer("Отправьте список трек‑кодов (каждый с новой строки)")


@router.message()
async def process_bulk(message: Message):
    codes = message.text.split()

    service = AdminProductService(ProductRepository())
    success, failed = await service.add_bulk(codes)

    await message.answer(
        f"✅ Добавлено: {success}\n❌ Ошибок: {failed}"
    )
