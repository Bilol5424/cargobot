"""
Обработчики экспорта для администратора
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from datetime import datetime

from database.session import get_db
from database.repository import UserRepository, ProductRepository
from keyboards.admin import get_admin_main_keyboard as get_admin_main_menu
from utils.states import AdminState

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text.contains("💾 Экспорт"))
async def admin_export_excel(message: Message, state: FSMContext):
    """Экспорт всей базы данных в Excel для администратора"""
    async for session in get_db():
        user_repo = UserRepository(session)
        product_repo = ProductRepository(session)
        
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        # Получаем ВСЕ товары из базы данных
        from sqlalchemy import select
        result = await session.execute(select(product_repo.model))
        all_products = result.scalars().all()
        
        if not all_products:
            texts = {
                "ru": "❌ В базе данных нет товаров для экспорта",
                "tj": "❌ Дар пойгоҳи маълумот маҳсулот барои экспорт нест"
            }
            await message.answer(texts[user.language])
            return
        
        try:
            # Экспортируем в Excel
            excel_data = await product_repo.export_to_excel(all_products)
            
            if not excel_data:
                raise Exception("Не удалось создать Excel файл")
            
            # Сохраняем временный файл
            import os
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"вся_база_данных_{timestamp}.xlsx"
            
            with open(filename, "wb") as f:
                f.write(excel_data)
            
            texts = {
                "ru": f"💾 <b>Экспорт базы данных завершен!</b>\n\n"
                      f"Количество товаров: {len(all_products)}\n"
                      f"Дата экспорта: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                "tj": f"💾 <b>Экспорти пойгоҳи маълумот анҷом ёфт!</b>\n\n"
                      f"Миқдори маҳсулот: {len(all_products)}\n"
                      f"Сании экспорт: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            }
            
            await message.answer(texts[user.language], parse_mode="HTML")
            
            # Отправляем файл
            file = FSInputFile(filename, filename=filename)
            await message.answer_document(file)
            
            # Удаляем временный файл
            os.remove(filename)
            
        except Exception as e:
            logger.error(f"Ошибка при экспорте в Excel: {e}")
            texts = {
                "ru": f"❌ Ошибка при создании Excel файла: {str(e)}",
                "tj": f"❌ Хато дар сохтани файли Excel: {str(e)}"
            }
            await message.answer(texts[user.language])
        
        # Возвращаем в главное меню
        role = "admin_cn" if "admin_cn" in user.role.value else "admin_tj"
        await message.answer(
            "Главное меню администратора:" if user.language == "ru" else "Менюи асосии администратор:",
            reply_markup=get_admin_main_menu(role, user.language)
        )