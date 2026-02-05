"""
Основные роутеры для работы с товарами
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.session import get_db
from database.repository import UserRepository
from keyboards.client import get_track_codes_keyboard
from utils.states import ClientState
from .utils import track_codes_menu_back

logger = logging.getLogger(__name__)
router = Router()

# ========== МЕНЮ ТРЕК-КОДОВ ==========

@router.message(ClientState.main_menu, F.text.contains("📦"))
async def track_codes_menu(message: Message, state: FSMContext):
    """Меню трек-кодов"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        texts = {
            "ru": "📦 <b>Трек-коды</b>\n\nВыберите действие:",
            "tj": "📦 <b>Рамзҳои тамошобин</b>\n\nАмалро интихоб кунед:"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_track_codes_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.track_codes_menu)