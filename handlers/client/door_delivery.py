"""
Доставка до дверей
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.session import get_db
from database.repository import UserRepository, ProductRepository
from database.models import ProductStatus
from keyboards.client import get_back_cancel_keyboard, get_main_menu_keyboard
from utils.states import ClientState

logger = logging.getLogger(__name__)
router = Router()

@router.message(ClientState.main_menu, F.text.contains("🚚"))
async def door_delivery_menu(message: Message, state: FSMContext):
    """Меню доставки до дверей"""
    async for session in get_db():
        user_repo = UserRepository(session)
        product_repo = ProductRepository(session)
        
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        # Проверяем, есть ли товары в Таджикистане
        products_in_tj = await product_repo.get_products_by_status(
            ProductStatus.TAJIKISTAN_WAREHOUSE
        )
        
        user_products_in_tj = [p for p in products_in_tj if p.user_id == user.id]
        
        if not user_products_in_tj:
            texts = {
                "ru": "⚠️ Доставка до дверей доступна только для товаров, прибывших в Таджикистан\n\n"
                      "У вас пока нет таких товаров.",
                "tj": "⚠️ Расонидан то дар танҳо барои маҳсулоте дастрас аст, ки ба Тоҷикистон омадаанд\n\n"
                      "Шумо то ҳол чунин маҳсулот надоред."
            }
            await message.answer(
                texts[user.language],
                reply_markup=get_main_menu_keyboard(user.language)
            )
            return
        
        texts = {
            "ru": "🚚 <b>Доставка до дверей</b>\n\n"
                  "Введите трек-код товара (можно несколько через запятую):",
            "tj": "🚚 <b>Расонидан то дар</b>\n\n"
                  "Рамзи тамошобини маҳсулотро ворид кунед (якчанд рамзро бо вергул ҷудо кунед):"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.door_delivery_track)

# Остальную логику доставки можно добавить позже