"""
Бесплатный курс
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.session import get_db
from database.repository import UserRepository
from keyboards.client import get_main_menu_keyboard, get_course_platform_keyboard
from utils.states import ClientState

logger = logging.getLogger(__name__)
router = Router()

@router.message(ClientState.main_menu, F.text.contains("🎓"))
async def free_course_menu(message: Message, state: FSMContext):
    """Меню бесплатного курса"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        texts = {
            "ru": "🎓 <b>Бесплатный курс по покупкам в Китае</b>\n\n"
                  "Выберите платформу:",
            "tj": "🎓 <b>Курси бепул оид ба харид дар Чин</b>\n\n"
                  "Платформаро интихоб кунед:"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_course_platform_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.course_menu)

# Остальную логику курса можно добавить позже