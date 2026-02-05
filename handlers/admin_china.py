import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.session import get_db
from database.repository import UserRepository
from keyboards.admin import get_admin_main_menu
from keyboards.client import get_back_cancel_keyboard  # Импорт из client.py
from utils.states import AdminChinaState

logger = logging.getLogger(__name__)
router = Router()

@router.message(AdminChinaState.main_menu, F.text.contains("⬅️"))
async def admin_china_back(message: Message, state: FSMContext):
    """Возврат в главное меню админа Китая"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            return
        
        texts = {
            "ru": "Главное меню админа Китая:",
            "tj": "Менюи асосии админи Чин:"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_admin_main_menu("admin_cn", user.language)
        )
        await state.set_state(AdminChinaState.main_menu)

@router.message(AdminChinaState.main_menu, F.text.contains("➕"))
async def add_products_start(message: Message, state: FSMContext):
    """Начало добавления товаров"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            return
        
        texts = {
            "ru": "➕ <b>Добавление товаров</b>\n\n"
                  "Введите количество товаров для добавления (1-100):",
            "tj": "➕ <b>Илова кардани маҳсулотҳо</b>\n\n"
                  "Миқдори маҳсулотҳоро барои илова кардан ворид кунед (1-100):"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(AdminChinaState.add_product)

@router.message(AdminChinaState.add_product)
async def add_products_process(message: Message, state: FSMContext):
    """Обработка добавления товаров"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт", "❌ Отмена", "❌ Бекор кардан"]:
        await admin_china_back(message, state)
        return
    
    if not message.text.isdigit() or not (1 <= int(message.text) <= 100):
        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(message.from_user.id)
            
            if not user:
                return
            
            texts = {
                "ru": "Пожалуйста, введите число от 1 до 100:",
                "tj": "Лутфан, рақами аз 1 то 100 ворид кунед:"
            }
            
            await message.answer(texts[user.language])
            return
    
    count = int(message.text)
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            return
        
        from services.track_code import generate_track_code
        
        track_codes = []
        for i in range(count):
            track_code = generate_track_code()
            track_codes.append(track_code)
        
        texts = {
            "ru": f"✅ Будет создано {count} товаров с трек-кодами:\n\n" + "\n".join(track_codes),
            "tj": f"✅ {count} маҳсулот бо рамзҳои тамошобин сохта мешавад:\n\n" + "\n".join(track_codes)
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_admin_main_menu("admin_cn", user.language)
        )
        await state.set_state(AdminChinaState.main_menu)

@router.message(AdminChinaState.main_menu, F.text.contains("🔄"))
async def bulk_update_start(message: Message):
    """Массовое обновление статусов"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            return
        
        texts = {
            "ru": "🔄 <b>Массовое обновление статусов</b>\n\n"
                  "Функция в разработке...",
            "tj": "🔄 <b>Навсозии оммавии статусҳо</b>\n\n"
                  "Функсия дар рушд аст..."
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_admin_main_menu("admin_cn", user.language),
            parse_mode="HTML"
        )

@router.message(AdminChinaState.main_menu, F.text.contains("📊"))
async def reports_menu(message: Message, state: FSMContext):
    """Меню отчетов"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            return
        
        texts = {
            "ru": "📊 <b>Отчеты</b>\n\nФункция в разработке...",
            "tj": "📊 <b>Ҳисоботҳо</b>\n\nФунксия дар рушд аст..."
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_admin_main_menu("admin_cn", user.language),
            parse_mode="HTML"
        )
        await state.set_state(AdminChinaState.main_menu)
@router.message(AdminChinaState.main_menu, F.text.contains("🔍"))
async def check_product_china(message: Message, state: FSMContext):
    """Проверка товара для админа Китая"""
    from handlers.admin.product_info import check_product_menu
    await check_product_menu(message, state)