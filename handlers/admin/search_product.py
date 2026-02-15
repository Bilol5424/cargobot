from aiogram import Router, F
from aiogram.types import Message
from services.admin_search_service import AdminSearchService
from database.repository import ProductRepository

router = Router()


@router.message(F.text == "🔎 Поиск товара")
async def ask_code(message: Message):
    await message.answer("Введите трек‑код")


@router.message()
async def search(message: Message):
    service = AdminSearchService(ProductRepository())

    product = await service.by_track_code(message.text)

    if not product:
        await message.answer("❌ Не найдено")
        return

    await message.answer(
        f"📦 {product.track_code}\nСтатус: {product.status}"
    )
