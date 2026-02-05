"""
Вспомогательные функции для клиентов
"""
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

router = Router()

@router.message()
async def debug_handler(message: Message, state: FSMContext):
    """Обработчик для отладки (ловит все сообщения)"""
    current_state = await state.get_state()
    print(f"DEBUG: Получено сообщение: '{message.text}'")
    print(f"DEBUG: Текущее состояние: {current_state}")
    print(f"DEBUG: User ID: {message.from_user.id}")
    print(f"DEBUG: Полный объект message: {message}")
    
    # Показываем приветствие для отладки
    from handlers.common import get_welcome_text
    from database.session import get_db
    from database.repository import UserRepository
    from keyboards.client import get_main_menu_keyboard
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if user:
            await message.answer(
                f"Отладка: вы отправили '{message.text}'\n"
                f"Состояние: {current_state}\n"
                f"Ваш язык: {user.language}\n\n"
                f"Вернуться в главное меню:",
                reply_markup=get_main_menu_keyboard(user.language)
            )