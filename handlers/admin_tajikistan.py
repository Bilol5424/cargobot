import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.session import get_db
from database.repository import UserRepository
from keyboards.admin import get_admin_main_menu
from keyboards.client import get_back_cancel_keyboard  # Импорт из client.py
from utils.states import AdminTajikistanState

logger = logging.getLogger(__name__)
router = Router()

@router.message(AdminTajikistanState.main_menu, F.text.contains("⬅️"))
async def admin_tj_back(message: Message, state: FSMContext):
    """Возврат в главное меню админа Таджикистана"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            return
        
        texts = {
            "ru": "Главное меню админа Таджикистана:",
            "tj": "Менюи асосии админи Тоҷикистон:"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_admin_main_menu("admin_tj", user.language)
        )
        await state.set_state(AdminTajikistanState.main_menu)

@router.message(AdminTajikistanState.main_menu, F.text.contains("✅"))
async def confirm_arrival_start(message: Message):
    """Подтверждение прибытия товара"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            return
        
        texts = {
            "ru": "✅ <b>Подтверждение прибытия</b>\n\n"
                  "Функция в разработке...",
            "tj": "✅ <b>Тасдиқ кардани омадан</b>\n\n"
                  "Функсия дар рушд аст..."
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_admin_main_menu("admin_tj", user.language),
            parse_mode="HTML"
        )

@router.message(AdminTajikistanState.main_menu, F.text.contains("✏️"))
async def update_status_start(message: Message):
    """Изменение статуса товара"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            return
        
        texts = {
            "ru": "✏️ <b>Изменение статуса</b>\n\n"
                  "Функция в разработке...",
            "tj": "✏️ <b>Тағйир додани статус</b>\n\n"
                  "Функсия дар рушд аст..."
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_admin_main_menu("admin_tj", user.language),
            parse_mode="HTML"
        )

@router.message(AdminTajikistanState.main_menu, F.text.contains("🚚"))
async def door_delivery_management(message: Message):
    """Управление доставкой до дверей"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            return
        
        texts = {
            "ru": "🚚 <b>Управление доставкой до дверей</b>\n\n"
                  "Функция в разработке...",
            "tj": "🚚 <b>Идоракунии расонидан то дар</b>\n\n"
                  "Функсия дар рушд аст..."
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_admin_main_menu("admin_tj", user.language),
            parse_mode="HTML"
        )

@router.message(AdminTajikistanState.main_menu, F.text.contains("📊"))
async def reports_menu_tj(message: Message):
    """Меню отчетов для админа Таджикистана"""
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
            reply_markup=get_admin_main_menu("admin_tj", user.language),
            parse_mode="HTML"
        )