"""
Поддержка
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

@router.message(ClientState.main_menu, F.text.contains("💬"))
async def support_info(message: Message, state: FSMContext):
    """Информация о поддержке"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        texts = {
            "ru": """💬 <b>Поддержка</b>

📞 Телефон: +992 123 45 67 89
📧 Email: support@example.com
🕒 Часы работы: 9:00 - 18:00 (Пн-Пт)

Свяжитесь с нами по любым вопросам!""",
            "tj": """💬 <b>Дастгирӣ</b>

📞 Телефон: +992 123 45 67 89
📧 Email: support@example.com
🕒 Вақти кор: 9:00 - 18:00 (Душ-Ҷум)

Барои ҳама саволҳо бо мо тамос гиред!"""
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_main_menu_keyboard(user.language),
            parse_mode="HTML"
        )