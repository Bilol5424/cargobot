from aiogram import Router, F
from aiogram.types import Message
from services.admin_product_service import AdminProductService
from database.repository import ProductRepository

router = Router()


@router.message(F.text == "➕ Добавить трек-код")
async def ask_track(message: Message):
    await message.answer("Введите трек‑код:")


@router.message()
async def add_track(message: Message):
    service = AdminProductService(ProductRepository())

    try:
        product = await service.add_single(message.text)
        await message.answer(f"✅ Добавлено: {product.track_code}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
