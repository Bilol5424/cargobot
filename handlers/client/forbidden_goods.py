"""
Запрещенные товары (уже есть в other_menus.py, но создаем для полноты)
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.session import get_db
from database.repository import UserRepository
from keyboards.client import get_main_menu_keyboard
from utils.states import ClientState

logger = logging.getLogger(__name__)
router = Router()

@router.message(ClientState.main_menu, F.text.contains("🚫"))
async def forbidden_goods(message: Message, state: FSMContext):
    """Список запрещенных товаров"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        texts = {
            "ru": """🚫 <b>Запрещённые товары</b>

1. Оружие и боеприпасы
2. Наркотические вещества
3. Взрывчатые материалы
4. Животные и растения под охраной
5. Порнографическая продукция
6. Лекарства без рецепта
7. Алкогольная продукция
8. Драгоценные металлы и камни
9. Радиоактивные материалы
10. Поддельные товары

Полный список уточняйте у поддержки.""",
            "tj": """🚫 <b>Маҳсулотҳои мамнуа</b>

1. Оружие ва боёмилҳо
2. Моддаҳои наркотикӣ
3. Маводҳои порхез
4. Ҳайвонот ва набототи зери ҳимоят
5. Маҳсулоти порнографӣ
6. Доруҳо бидуни тавсиянома
7. Маҳсулоти спиртӣ
8. Фулузоти гаронбаҳо ва сангу ҷавҳар
9. Маводҳои радиоактивӣ
10. Маҳсулоти қалбакӣ

Рӯйхати пурраро аз дастгирӣ тафсилот диҳед."""
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_main_menu_keyboard(user.language),
            parse_mode="HTML"
        )