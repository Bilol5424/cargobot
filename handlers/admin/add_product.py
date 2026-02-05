"""
Добавление товаров администратором
"""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Product
from database.session import async_session_maker
from utils.states import AdminStates
from keyboards.admin import (
    get_back_to_admin_keyboard,
    get_product_categories_keyboard,
    get_yes_no_keyboard
)
from services.track_code_generator import generate_track_code
from config import settings

logger = logging.getLogger(__name__)
add_product_router = Router()

@add_product_router.callback_query(F.data == "admin_add_product")
async def add_product_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления товара"""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    # Генерируем трек-код
    track_code = generate_track_code()
    
    await state.update_data(
        track_code=track_code,
        user_id=callback.from_user.id
    )
    
    await callback.message.edit_text(
        f"📦 Добавление нового товара\n\n"
        f"📋 Сгенерирован трек-код: {track_code}\n\n"
        f"Введите название товара:",
        reply_markup=get_back_to_admin_keyboard()
    )
    
    await state.set_state(AdminStates.WAITING_PRODUCT_NAME)
    await callback.answer()

@add_product_router.message(AdminStates.WAITING_PRODUCT_NAME)
async def process_product_name(message: Message, state: FSMContext):
    """Обработка названия товара"""
    product_name = message.text.strip()
    
    if len(product_name) < 2:
        await message.answer(
            "❌ Название слишком короткое. Введите название товара:",
            reply_markup=get_back_to_admin_keyboard()
        )
        return
    
    await state.update_data(product_name=product_name)
    
    await message.answer(
        "📋 Выберите категорию товара:",
        reply_markup=get_product_categories_keyboard()
    )
    
    await state.set_state(AdminStates.WAITING_PRODUCT_CATEGORY)

@add_product_router.callback_query(F.data.startswith("category_"))
async def process_product_category(callback: CallbackQuery, state: FSMContext):
    """Обработка категории товара"""
    category = callback.data.replace("category_", "")
    
    await state.update_data(product_category=category)
    
    await callback.message.edit_text(
        "🔢 Введите количество товара (целое число):",
        reply_markup=get_back_to_admin_keyboard()
    )
    
    await state.set_state(AdminStates.WAITING_PRODUCT_QUANTITY)
    await callback.answer()

@add_product_router.message(AdminStates.WAITING_PRODUCT_QUANTITY)
async def process_product_quantity(message: Message, state: FSMContext):
    """Обработка количества товара"""
    try:
        quantity = int(message.text.strip())
        if quantity <= 0:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Неверное количество. Введите целое положительное число:",
            reply_markup=get_back_to_admin_keyboard()
        )
        return
    
    await state.update_data(quantity=quantity)
    
    await message.answer(
        "💰 Введите цену за единицу (в долларах США):\n"
        "Пример: 15.50",
        reply_markup=get_back_to_admin_keyboard()
    )
    
    await state.set_state(AdminStates.WAITING_PRODUCT_PRICE)

@add_product_router.message(AdminStates.WAITING_PRODUCT_PRICE)
async def process_product_price(message: Message, state: FSMContext):
    """Обработка цены товара"""
    try:
        price = float(message.text.strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Неверная цена. Введите число (например: 15.50):",
            reply_markup=get_back_to_admin_keyboard()
        )
        return
    
    await state.update_data(unit_price_usd=price)
    
    await message.answer(
        "⚖️ Введите вес товара в килограммах:\n"
        "Пример: 2.5",
        reply_markup=get_back_to_admin_keyboard()
    )
    
    await state.set_state(AdminStates.WAITING_PRODUCT_WEIGHT)

@add_product_router.message(AdminStates.WAITING_PRODUCT_WEIGHT)
async def process_product_weight(message: Message, state: FSMContext):
    """Обработка веса товара"""
    try:
        weight = float(message.text.strip())
        if weight <= 0:
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Неверный вес. Введите число (например: 2.5):",
            reply_markup=get_back_to_admin_keyboard()
        )
        return
    
    await state.update_data(weight_kg=weight)
    
    await message.answer(
        "📦 Товар хрупкий?\n"
        "(легко бьется, требует особой упаковки)",
        reply_markup=get_yes_no_keyboard("fragile")
    )
    
    await state.set_state(AdminStates.WAITING_PRODUCT_SPECIAL)

@add_product_router.callback_query(F.data.startswith("fragile_"))
async def process_fragile(callback: CallbackQuery, state: FSMContext):
    """Обработка хрупкости товара"""
    fragile = callback.data.replace("fragile_", "") == "yes"
    
    await state.update_data(fragile=fragile)
    
    await callback.message.edit_text(
        "🔋 Товар содержит батареи или аккумуляторы?",
        reply_markup=get_yes_no_keyboard("battery")
    )
    
    await state.set_state(AdminStates.WAITING_PRODUCT_SPECIAL)
    await callback.answer()

@add_product_router.callback_query(F.data.startswith("battery_"))
async def process_battery(callback: CallbackQuery, state: FSMContext):
    """Обработка наличия батареи"""
    has_battery = callback.data.replace("battery_", "") == "yes"
    
    await state.update_data(has_battery=has_battery)
    
    await callback.message.edit_text(
        "💧 Товар является жидкостью?",
        reply_markup=get_yes_no_keyboard("liquid")
    )
    
    await state.set_state(AdminStates.WAITING_PRODUCT_SPECIAL)
    await callback.answer()

@add_product_router.callback_query(F.data.startswith("liquid_"))
async def process_liquid(callback: CallbackQuery, state: FSMContext):
    """Обработка жидкости"""
    is_liquid = callback.data.replace("liquid_", "") == "yes"
    
    await state.update_data(is_liquid=is_liquid)
    
    # Запрашиваем страну отправления
    await callback.message.edit_text(
        "🌍 Введите страну отправления товара:\n"
        "Пример: Китай, США, Россия",
        reply_markup=get_back_to_admin_keyboard()
    )
    
    await state.set_state(AdminStates.WAITING_PRODUCT_COUNTRY)
    await callback.answer()

@add_product_router.message(AdminStates.WAITING_PRODUCT_COUNTRY)
async def process_country(message: Message, state: FSMContext):
    """Обработка страны отправления"""
    country = message.text.strip()
    
    await state.update_data(country_from=country)
    
    # Запрашиваем тип доставки
    await message.answer(
        "🚚 Выберите тип доставки:\n"
        "1. Авиадоставка (быстро, дорого)\n"
        "2. Морская доставка (медленно, дешево)\n"
        "3. Автодоставка\n"
        "Введите номер или название:",
        reply_markup=get_back_to_admin_keyboard()
    )
    
    await state.set_state(AdminStates.WAITING_DELIVERY_TYPE)

@add_product_router.message(AdminStates.WAITING_DELIVERY_TYPE)
async def process_delivery_type(message: Message, state: FSMContext):
    """Обработка типа доставки"""
    delivery_type = message.text.strip()
    
    # Определяем тип доставки по вводу
    if delivery_type in ["1", "авиа", "авиадоставка", "aviation"]:
        delivery_type = "Авиадоставка"
    elif delivery_type in ["2", "морская", "море", "sea"]:
        delivery_type = "Морская доставка"
    elif delivery_type in ["3", "авто", "автодоставка", "car"]:
        delivery_type = "Автодоставка"
    
    await state.update_data(delivery_type=delivery_type)
    
    # Собираем все данные
    data = await state.get_data()
    
    # Рассчитываем общую стоимость
    quantity = data.get('quantity', 1)
    unit_price = data.get('unit_price_usd', 0)
    total_value = quantity * unit_price
    
    # Формируем сводку
    summary = f"📋 Сводка по товару:\n\n"
    summary += f"📦 Трек-код: {data.get('track_code')}\n"
    summary += f"📝 Название: {data.get('product_name')}\n"
    summary += f"🏷️ Категория: {data.get('product_category')}\n"
    summary += f"🔢 Количество: {quantity} шт.\n"
    summary += f"💰 Цена за ед.: ${unit_price:.2f}\n"
    summary += f"💵 Общая стоимость: ${total_value:.2f}\n"
    summary += f"⚖️ Вес: {data.get('weight_kg')} кг\n"
    summary += f"🎯 Хрупкий: {'Да' if data.get('fragile') else 'Нет'}\n"
    summary += f"🔋 Батарея: {'Да' if data.get('has_battery') else 'Нет'}\n"
    summary += f"💧 Жидкость: {'Да' if data.get('is_liquid') else 'Нет'}\n"
    summary += f"🌍 Страна: {data.get('country_from')}\n"
    summary += f"🚚 Доставка: {delivery_type}\n\n"
    summary += f"✅ Все верно? (да/нет)"
    
    await message.answer(
        summary,
        reply_markup=get_yes_no_keyboard("confirm")
    )
    
    await state.update_data(total_value_usd=total_value)
    await state.set_state(AdminStates.WAITING_CONFIRMATION)

@add_product_router.callback_query(F.data.startswith("confirm_"))
async def process_confirmation(callback: CallbackQuery, state: FSMContext):
    """Обработка подтверждения"""
    confirm = callback.data.replace("confirm_", "") == "yes"
    
    if not confirm:
        await callback.message.edit_text(
            "❌ Добавление товара отменено.",
            reply_markup=get_back_to_admin_keyboard()
        )
        await state.clear()
        await callback.answer()
        return
    
    # Получаем данные
    data = await state.get_data()
    
    # Создаем товар в базе данных
    async with async_session_maker() as session:
        product_data = {
            "track_code": data.get('track_code'),
            "user_id": data.get('user_id'),
            "product_name": data.get('product_name'),
            "product_category": data.get('product_category'),
            "quantity": data.get('quantity'),
            "unit_price_usd": data.get('unit_price_usd'),
            "total_value_usd": data.get('total_value_usd'),
            "weight_kg": data.get('weight_kg'),
            "fragile": data.get('fragile', False),
            "has_battery": data.get('has_battery', False),
            "is_liquid": data.get('is_liquid', False),
            "status": "CREATED",
            "country_from": data.get('country_from'),
            "delivery_type": data.get('delivery_type'),
            "send_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Проверяем, нет ли уже товара с таким трек-кодом
        existing_query = select(Product).where(Product.track_code == data.get('track_code'))
        result = await session.execute(existing_query)
        existing_product = result.scalar_one_or_none()
        
        if existing_product:
            await callback.message.edit_text(
                f"❌ Товар с трек-кодом {data.get('track_code')} уже существует.",
                reply_markup=get_back_to_admin_keyboard()
            )
        else:
            # Создаем новый товар
            new_product = Product(**product_data)
            session.add(new_product)
            await session.commit()
            
            await callback.message.edit_text(
                f"✅ Товар успешно добавлен!\n\n"
                f"📦 Трек-код: {data.get('track_code')}\n"
                f"📝 Название: {data.get('product_name')}\n"
                f"🏷️ Категория: {data.get('product_category')}\n"
                f"🔢 Количество: {data.get('quantity')} шт.\n"
                f"💰 Общая стоимость: ${data.get('total_value_usd'):.2f}\n\n"
                f"📊 Статус: CREATED\n"
                f"⏰ Дата добавления: {datetime.utcnow().strftime('%d.%m.%Y %H:%M')}",
                reply_markup=get_back_to_admin_keyboard()
            )
    
    await state.clear()
    await callback.answer()