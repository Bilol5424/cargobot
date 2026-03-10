from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from services.admin_status_service import AdminStatusService
from database.repository import ProductRepository
from database.session import async_session_maker
from keyboards.admin import get_admin_main_keyboard, get_status_selection_keyboard
from config import settings

router = Router()

class BulkUpdateState(StatesGroup):
    waiting_for_status = State()
    waiting_for_track_codes = State()

@router.message(F.text == "📋 Массовое обновление")
async def bulk_update_menu(message: Message, state: FSMContext):
    """Меню массового обновления статуса товаров"""
    if not settings.is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещен")
        return

    user_id = message.from_user.id
    async with async_session_maker() as session:
        from database.models import User
        from sqlalchemy import select
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"

    texts = {
        "ru": "📋 Массовое обновление статуса\n\nВыберите новый статус для товаров:",
        "tj": "📋 Навсозии оммавии статус\n\nСтатуси навро барои маҳсулот интихоб кунед:"
    }

    await message.answer(
        texts.get(language, texts["ru"]),
        reply_markup=get_status_selection_keyboard(language)
    )
    await state.set_state(BulkUpdateState.waiting_for_status)

@router.callback_query(BulkUpdateState.waiting_for_status)
async def select_status(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора статуса"""
    status = callback.data
    await state.update_data(selected_status=status)

    user_id = callback.from_user.id
    async with async_session_maker() as session:
        from database.models import User
        from sqlalchemy import select
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"

    texts = {
        "ru": f"📋 Выбран статус: {status}\n\nВведите трек-коды товаров через запятую:",
        "tj": f"📋 Статус интихоб шуд: {status}\n\nРамзҳои трек-кодро тавассути вергул дохил кунед:"
    }

    await callback.message.answer(texts.get(language, texts["ru"]))
    await state.set_state(BulkUpdateState.waiting_for_track_codes)
    await callback.answer()

@router.message(BulkUpdateState.waiting_for_status)
async def invalid_status_selection(message: Message):
    """Обработка некорректного выбора статуса"""
    await message.answer("❌ Пожалуйста, выберите один из предложенных вариантов.")

@router.message(BulkUpdateState.waiting_for_track_codes)
async def process_bulk_update(message: Message, state: FSMContext):
    """Обработка ввода трек-кодов и обновление"""
    data = await state.get_data()
    selected_status = data.get("selected_status")
    track_codes = [code.strip() for code in message.text.split(',') if code.strip()]

    if not track_codes:
        await message.answer("❌ Введите хотя бы один трек-код.")
        return

    user_id = message.from_user.id
    async with async_session_maker() as session:
        from database.models import User
        from sqlalchemy import select
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"

        repo = ProductRepository(session)
        service = AdminStatusService(repo)

        updated_count = 0
        for track_code in track_codes:
            try:
                await service.update_status(track_code, selected_status)
                updated_count += 1
            except Exception as e:
                # Логируем ошибку, но продолжаем
                pass

        texts = {
            "ru": f"✅ Обновлено {updated_count} из {len(track_codes)} товаров.",
            "tj": f"✅ {updated_count} аз {len(track_codes)} маҳсулот навсозӣ шуд."
        }

        admin_role = settings.get_admin_role(user_id)
        await message.answer(
            texts.get(language, texts["ru"]),
            reply_markup=get_admin_main_keyboard(role=admin_role, language=language)
        )

    await state.clear()
