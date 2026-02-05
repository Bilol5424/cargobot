"""
Экспорт товаров в Excel
"""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.session import get_db
from database.repository import UserRepository, ProductRepository
from utils.states import ClientState
from .utils import track_codes_menu_back

logger = logging.getLogger(__name__)
router = Router()

@router.message(ClientState.track_codes_menu, F.text.contains("Экспорт в Excel"))
async def export_products_to_excel(message: Message, state: FSMContext):
    """Экспорт товаров пользователя в Excel"""
    async for session in get_db():
        user_repo = UserRepository(session)
        product_repo = ProductRepository(session)
        
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        products = await product_repo.get_user_products(user.id, limit=1000)  # Большой лимит для экспорта
        
        if not products:
            texts = {
                "ru": "❗ У вас нет товаров для экспорта",
                "tj": "❗ Шумо маҳсулот барои экспорт надоред"
            }
            await message.answer(texts[user.language])
            return
        
        try:
            # Импортируем здесь, чтобы избежать циклических импортов
            from services.excel_export import generate_user_products_report
            
            # Генерируем Excel файл
            file_path = await generate_user_products_report(products, user.language)
            
            # Отправляем файл пользователю
            from aiogram.types import FSInputFile
            
            texts = {
                "ru": f"📊 <b>Экспорт завершен!</b>\n\n"
                      f"Создан файл с {len(products)} товарами.",
                "tj": f"📊 <b>Экспорт анҷом ёфт!</b>\n\n"
                      f"Файл бо {len(products)} маҳсулот сохта шуд."
            }
            
            await message.answer(texts[user.language], parse_mode="HTML")
            
            # Отправляем файл
            file = FSInputFile(file_path, filename=f"мои_товары_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx")
            await message.answer_document(file)
            
        except Exception as e:
            logger.error(f"Ошибка при экспорте в Excel: {e}")
            texts = {
                "ru": "❌ Ошибка при создании Excel файла",
                "tj": "❌ Хато дар сохтани файли Excel"
            }
            await message.answer(texts[user.language])
        
        # Возвращаемся в меню трек-кодов
        from keyboards.client import get_track_codes_keyboard
        await message.answer(
            "📦 Меню трек-кодов:" if user.language == "ru" else "📦 Менюи рамзҳои тамошобин:",
            reply_markup=get_track_codes_keyboard(user.language)
        )
        await state.set_state(ClientState.track_codes_menu)