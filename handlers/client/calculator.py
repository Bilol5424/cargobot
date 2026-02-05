"""
Обработчик калькулятора доставки
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.session import get_db
from database.repository import UserRepository
from keyboards.client import get_back_cancel_keyboard, get_country_keyboard, get_main_menu_keyboard
from utils.states import ClientState
from services.calculator import calculate_delivery_cost

logger = logging.getLogger(__name__)
router = Router()

async def calculator_start(message: Message, state: FSMContext):
    """Начало расчета доставки"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            return
        
        texts = {
            "ru": "🧮 <b>Калькулятор доставки</b>\n\nВыберите страну доставки:",
            "tj": "🧮 <b>Калькулятори расонидан</b>\n\nКишвари расониданро интихоб кунед:"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_country_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.calculator_country)

@router.message(ClientState.calculator_country)
async def calculator_country_handler(message: Message, state: FSMContext):
    """Обработка выбора страны для калькулятора"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт"]:
        await message.answer(
            "Главное меню:" if True else "Менюи асосӣ:",  # Без user для простоты
            reply_markup=get_main_menu_keyboard("ru")  # Временно
        )
        await state.set_state(ClientState.main_menu)
        return
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            return
        
        await state.update_data(calculator_country=message.text)
        
        texts = {
            "ru": "Введите длину (в метрах):",
            "tj": "Дарозиро ворид кунед (дар метр):"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language)
        )
        await state.set_state(ClientState.calculator_dimensions)

@router.message(ClientState.calculator_dimensions)
async def calculator_dimensions_handler(message: Message, state: FSMContext):
    """Обработка ввода размеров"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт"]:
        await calculator_start(message, state)
        return
    
    try:
        length = float(message.text.replace(",", "."))
        
        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(message.from_user.id)
            
            if not user:
                return
            
            await state.update_data(length=length)
            
            texts = {
                "ru": "Введите ширину (в метрах):",
                "tj": "Барандозиро ворид кунед (дар метр):"
            }
            
            await message.answer(
                texts[user.language],
                reply_markup=get_back_cancel_keyboard(user.language)
            )
            await state.set_state(ClientState.calculator_dimensions)
            
    except ValueError:
        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(message.from_user.id)
            
            texts = {
                "ru": "❌ Пожалуйста, введите число (например: 0.5, 1, 2.3)",
                "tj": "❌ Лутфан, рақам ворид кунед (масалан: 0.5, 1, 2.3)"
            }
            await message.answer(texts[user.language])

@router.message(ClientState.calculator_weight)
async def calculator_weight_handler(message: Message, state: FSMContext):
    """Обработка ввода веса и расчет стоимости"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт"]:
        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(message.from_user.id)
            
            if not user:
                return
            
            texts = {
                "ru": "Введите высоту (в метрах):",
                "tj": "Баландиро ворид кунед (дар метр):"
            }
            
            await message.answer(
                texts[user.language],
                reply_markup=get_back_cancel_keyboard(user.language)
            )
            await state.set_state(ClientState.calculator_dimensions)
        return
    
    try:
        weight = float(message.text.replace(",", "."))
        
        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(message.from_user.id)
            
            if not user:
                return
            
            data = await state.get_data()
            
            # Расчет стоимости
            cost = calculate_delivery_cost(weight)
            
            texts = {
                "ru": f"""🧮 <b>Результат расчета</b>

Страна доставки: {data.get('calculator_country', 'Не указана')}
Длина: {data.get('length', 0)} м
Ширина: {data.get('width', 0)} м
Высота: {data.get('height', 0)} м
Вес: {weight} кг

<b>Итоговая стоимость: ${cost:.2f}</b>""",
                "tj": f"""🧮 <b>Натиҷаи ҳисоб</b>

Кишвари расонидан: {data.get('calculator_country', 'Муайян нашудааст')}
Дарозӣ: {data.get('length', 0)} м
Барандозӣ: {data.get('width', 0)} м
Баландӣ: {data.get('height', 0)} м
Вазн: {weight} кг

<b>Арзиши ниҳоӣ: ${cost:.2f}</b>"""
            }
            
            await message.answer(
                texts[user.language],
                reply_markup=get_main_menu_keyboard(user.language),
                parse_mode="HTML"
            )
            await state.set_state(ClientState.main_menu)
            
    except ValueError:
        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(message.from_user.id)
            
            texts = {
                "ru": "❌ Пожалуйста, введите число (например: 1, 5.5, 10.2)",
                "tj": "❌ Лутфан, рақам ворид кунед (масалан: 1, 5.5, 10.2)"
            }
            await message.answer(texts[user.language])