"""
Главное меню клиента
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.session import get_db
from database.repository import UserRepository, ProductRepository
from keyboards.client import get_main_menu_keyboard, get_track_codes_keyboard, get_country_keyboard
from utils.states import ClientState

logger = logging.getLogger(__name__)

# Создаем роутер
main_menu_router = Router()

@main_menu_router.message(ClientState.main_menu, F.text.contains("📦"))
async def track_codes_menu(message: Message, state: FSMContext):
    """Меню трек-кодов"""
    logger.info(f"Пользователь {message.from_user.id} выбрал 'Трек-коды'")
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            await message.answer("Пожалуйста, начните с команды /start")
            return
        
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

@main_menu_router.message(ClientState.main_menu, F.text.contains("👤"))
async def profile_menu(message: Message, state: FSMContext):
    """Меню профиля"""
    logger.info(f"Пользователь {message.from_user.id} выбрал 'Профиль'")
    
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
        
        from keyboards.client import get_profile_keyboard
        await message.answer(
            texts[user.language],
            reply_markup=get_profile_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.profile_menu)

@main_menu_router.message(ClientState.main_menu, F.text.contains("📍"))
async def address_menu(message: Message, state: FSMContext):
    """Меню адресов"""
    logger.info(f"Пользователь {message.from_user.id} выбрал 'Адрес'")
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            await message.answer("Пожалуйста, начните с команды /start")
            return
        
        texts = {
            "ru": "📍 <b>Адреса складов</b>\n\nВыберите страну:",
            "tj": "📍 <b>Адресҳои анбор</b>\n\nКишварро интихоб кунед:"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_country_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.address_menu)

@main_menu_router.message(ClientState.main_menu, F.text.contains("🧮"))
async def calculator_menu(message: Message):
    """Калькулятор"""
    logger.info(f"Пользователь {message.from_user.id} выбрал 'Калькулятор'")
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            return
        
        texts = {
            "ru": "🧮 <b>Калькулятор доставки</b>\n\nФункция находится в разработке. Скоро будет доступна!",
            "tj": "🧮 <b>Калькулятори расонидан</b>\n\nФунксия дар таҳия аст. Ба зудӣ дастрас хоҳад шуд!"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_main_menu_keyboard(user.language),
            parse_mode="HTML"
        )

@main_menu_router.message(ClientState.main_menu, F.text.contains("🚫"))
async def forbidden_goods(message: Message):
    """Запрещенные товары"""
    logger.info(f"Пользователь {message.from_user.id} выбрал 'Запрещенные товары'")
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            return
        
        texts = {
            "ru": """🚫 <b>Запрещённые товары</b>

1. Оружие и боеприпасы
2. Наркотические вещества
3. Взрывчатые материалы
4. Животные под охраной
5. Порнографическая продукция

Полный список уточняйте у поддержки.""",
            "tj": """🚫 <b>Маҳсулотҳои мамнуа</b>

1. Оружие ва боёмилҳо
2. Моддаҳои наркотикӣ
3. Маводҳои порхез
4. Ҳайвоноти зери ҳимоят
5. Маҳсулоти порнографӣ

Рӯйхати пурраро аз дастгирӣ тафсилот диҳед."""
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_main_menu_keyboard(user.language),
            parse_mode="HTML"
        )

@main_menu_router.message(ClientState.main_menu, F.text.contains("💬"))
async def support_info(message: Message):
    """Поддержка"""
    logger.info(f"Пользователь {message.from_user.id} выбрал 'Поддержка'")
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            return
        
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

@main_menu_router.message(ClientState.main_menu, F.text.contains("⬅️"))
async def back_button(message: Message):
    """Кнопка Назад в главном меню"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if user:
            await message.answer(
                "Вы уже в главном меню" if user.language == "ru" else "Шумо аллакай дар менюи асосӣ ҳастед",
                reply_markup=get_main_menu_keyboard(user.language)
            )