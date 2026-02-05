"""
Обработчик профиля пользователя
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.session import get_db
from database.repository import UserRepository, ProductRepository
from keyboards.client import get_profile_keyboard, get_main_menu_keyboard, get_back_cancel_keyboard
from utils.states import ClientState

logger = logging.getLogger(__name__)

# Создаем роутер
profile_router = Router()

@profile_router.message(ClientState.profile_menu)
async def profile_handler(message: Message, state: FSMContext):
    """Обработка действий в меню профиля"""
    logger.info(f"Пользователь {message.from_user.id} в меню профиля: {message.text}")
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            return
        
        # Тексты кнопок
        edit_name_ru = "📝 Изменить имя"
        edit_name_tj = "📝 Тағйир додани ном"
        edit_region_ru = "📝 Изменить регион"
        edit_region_tj = "📝 Тағйир додани минтақа"
        back_ru = "⬅️ Назад"
        back_tj = "⬅️ Бозгашт"
        
        if message.text in [edit_name_ru, edit_name_tj]:
            texts = {
                "ru": "✏️ <b>Изменение имени</b>\n\nВведите ваше новое имя:",
                "tj": "✏️ <b>Тағйир додани ном</b>\n\nНоми нави худро ворид кунед:"
            }
            
            await message.answer(
                texts[user.language],
                reply_markup=get_back_cancel_keyboard(user.language),
                parse_mode="HTML"
            )
            await state.set_state(ClientState.edit_name)
            
        elif message.text in [edit_region_ru, edit_region_tj]:
            texts = {
                "ru": "📍 <b>Изменение региона</b>\n\nВведите ваш новый регион:",
                "tj": "📍 <b>Тағйир додани минтақа</b>\n\nМинтақаи нави худро ворид кунед:"
            }
            
            await message.answer(
                texts[user.language],
                reply_markup=get_back_cancel_keyboard(user.language),
                parse_mode="HTML"
            )
            await state.set_state(ClientState.edit_region)
            
        elif message.text in [back_ru, back_tj]:
            await message.answer(
                "Главное меню:" if user.language == "ru" else "Менюи асосӣ:",
                reply_markup=get_main_menu_keyboard(user.language)
            )
            await state.set_state(ClientState.main_menu)
        else:
            await show_profile(message, state)

async def show_profile(message: Message, state: FSMContext):
    """Показать профиль пользователя"""
    async for session in get_db():
        user_repo = UserRepository(session)
        product_repo = ProductRepository(session)
        
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            await message.answer("Пожалуйста, начните с команды /start")
            return
        
        products = await product_repo.get_user_products(user.id)
        
        texts = {
            "ru": f"""👤 <b>Профиль</b>

👤 Имя: {user.full_name or 'Не указано'}
📞 Телефон: {user.phone or 'Не указан'}
📍 Регион: {user.region or 'Не указан'}
📦 Количество товаров: {len(products)}
🆔 UID: {user.telegram_id}

Выберите действие:""",
            "tj": f"""👤 <b>Профил</b>

👤 Ном: {user.full_name or 'Муайян нашудааст'}
📞 Телефон: {user.phone or 'Муайян нашудааст'}
📍 Минтақа: {user.region or 'Муайян нашудааст'}
📦 Миқдори маҳсулот: {len(products)}
🆔 UID: {user.telegram_id}

Амалро интихоб кунед:"""
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_profile_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.profile_menu)

@profile_router.message(ClientState.edit_name)
async def edit_name_handler(message: Message, state: FSMContext):
    """Обработка изменения имени"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            return
        
        # Тексты кнопок
        cancel_ru = "❌ Отмена"
        cancel_tj = "❌ Бекор кардан"
        back_ru = "⬅️ Назад"
        back_tj = "⬅️ Бозгашт"
        
        if message.text in [back_ru, back_tj, cancel_ru, cancel_tj]:
            await show_profile(message, state)
            return
        
        # Обновляем имя
        await user_repo.update_user_profile(
            telegram_id=message.from_user.id,
            full_name=message.text
        )
        
        texts = {
            "ru": f"✅ Имя успешно изменено на: {message.text}",
            "tj": f"✅ Ном бомуваффақият тағйир дода шуд ба: {message.text}"
        }
        
        await message.answer(texts[user.language])
        await show_profile(message, state)

@profile_router.message(ClientState.edit_region)
async def edit_region_handler(message: Message, state: FSMContext):
    """Обработка изменения региона"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            return
        
        # Тексты кнопок
        cancel_ru = "❌ Отмена"
        cancel_tj = "❌ Бекор кардан"
        back_ru = "⬅️ Назад"
        back_tj = "⬅️ Бозгашт"
        
        if message.text in [back_ru, back_tj, cancel_ru, cancel_tj]:
            await show_profile(message, state)
            return
        
        # Обновляем регион
        await user_repo.update_user_profile(
            telegram_id=message.from_user.id,
            region=message.text
        )
        
        texts = {
            "ru": f"✅ Регион успешно изменен на: {message.text}",
            "tj": f"✅ Минтақа бомуваффақият тағйир дода шуд ба: {message.text}"
        }
        
        await message.answer(texts[user.language])
        await show_profile(message, state)