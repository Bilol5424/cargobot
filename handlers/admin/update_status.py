"""
Обновление статусов товаров - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Product
from database.session import async_session_maker  # ИСПРАВЛЕННЫЙ ИМПОРТ
from utils.states import AdminStates
from keyboards.admin import (
    get_status_update_menu_keyboard, 
    get_status_keyboard,
    get_back_to_admin_keyboard
)
from config import settings

logger = logging.getLogger(__name__)
update_status_router = Router()

# Список доступных статусов
PRODUCT_STATUSES = [
    "CREATED",           # Создан
    "IN_CHINA_WAREHOUSE", # На складе в Китае
    "IN_TRANSIT",        # В пути
    "ARRIVED_TJ",        # Прибыл в Таджикистан
    "READY_FOR_PICKUP",  # Готов к выдаче
    "DELIVERED",         # Доставлен
    "CANCELLED",         # Отменен
    "PROBLEM",           # Проблема
]

@update_status_router.callback_query(F.data == "admin_update_status")
async def update_status_menu(callback: CallbackQuery):
    """Меню обновления статусов"""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🔄 Обновление статусов товаров\n\n"
        "Выберите способ обновления:",
        reply_markup=get_status_update_menu_keyboard()
    )
    await callback.answer()

@update_status_router.callback_query(F.data == "update_by_track")
async def update_by_track(callback: CallbackQuery, state: FSMContext):
    """Обновление по трек-коду"""
    await callback.message.edit_text(
        "📝 Введите трек-код товара для обновления статуса:",
        reply_markup=get_back_to_admin_keyboard()
    )
    await state.set_state(AdminStates.WAITING_TRACK_FOR_UPDATE)
    await callback.answer()

@update_status_router.message(AdminStates.WAITING_TRACK_FOR_UPDATE)
async def process_track_for_update(message: Message, state: FSMContext):
    """Обработка введенного трек-кода"""
    track_code = message.text.strip()
    
    # ИСПРАВЛЕННАЯ СЕССИЯ
    async with async_session_maker() as session:
        # Ищем товар
        query = select(Product).where(Product.track_code == track_code)
        result = await session.execute(query)
        product = result.scalar_one_or_none()
        
        if not product:
            await message.answer(
                f"❌ Товар с трек-кодом {track_code} не найден.\n"
                "Попробуйте еще раз:",
                reply_markup=get_back_to_admin_keyboard()
            )
            return
        
        # Сохраняем информацию о товаре
        await state.update_data(
            product_id=product.id,
            track_code=track_code,
            current_status=product.status
        )
        
        # Показываем текущий статус и предлагаем новый
        await message.answer(
            f"📦 Товар найден:\n"
            f"Код: {product.track_code}\n"
            f"Название: {product.product_name or 'Не указано'}\n"
            f"Текущий статус: {product.status or 'Не установлен'}\n\n"
            f"Выберите новый статус:",
            reply_markup=get_status_keyboard()
        )
        
        await state.set_state(AdminStates.WAITING_NEW_STATUS)

@update_status_router.callback_query(F.data.startswith("set_status_"))
async def set_new_status(callback: CallbackQuery, state: FSMContext):
    """Установка нового статуса"""
    new_status = callback.data.replace("set_status_", "")
    
    # Получаем данные из состояния
    data = await state.get_data()
    product_id = data.get("product_id")
    track_code = data.get("track_code")
    current_status = data.get("current_status")
    
    if not product_id:
        await callback.message.edit_text("❌ Ошибка: данные о товаре не найдены")
        await callback.answer()
        return
    
    # ИСПРАВЛЕННАЯ СЕССИЯ
    async with async_session_maker() as session:
        # Обновляем статус
        stmt = update(Product).where(Product.id == product_id).values(
            status=new_status,
            updated_at=datetime.utcnow()
        )
        
        # Если статус "Прибыл в Таджикистан", спрашиваем дату прибытия
        if new_status == "ARRIVED_TJ":
            await callback.message.edit_text(
                f"✅ Статус изменен с '{current_status}' на '{new_status}'\n\n"
                f"Введите дату прибытия в формате ДД.ММ.ГГГГ ЧЧ:ММ\n"
                f"Например: 05.02.2026 14:30\n"
                f"Или нажмите 'Пропустить', чтобы установить текущее время:",
                reply_markup=get_back_to_admin_keyboard()
            )
            await state.update_data(new_status=new_status)
            await state.set_state(AdminStates.WAITING_ARRIVAL_DATE)
        else:
            await session.execute(stmt)
            await session.commit()
            
            await callback.message.edit_text(
                f"✅ Статус успешно обновлен!\n\n"
                f"Трек-код: {track_code}\n"
                f"Старый статус: {current_status}\n"
                f"Новый статус: {new_status}",
                reply_markup=get_back_to_admin_keyboard()
            )
        
        await callback.answer()

@update_status_router.message(AdminStates.WAITING_ARRIVAL_DATE)
async def process_arrival_date(message: Message, state: FSMContext):
    """Обработка даты прибытия"""
    date_text = message.text.strip()
    
    # Получаем данные из состояния
    data = await state.get_data()
    product_id = data.get("product_id")
    track_code = data.get("track_code")
    current_status = data.get("current_status")
    new_status = data.get("new_status")
    
    arrival_date = None
    
    if date_text.lower() != "пропустить":
        try:
            # Парсим дату
            arrival_date = datetime.strptime(date_text, "%d.%m.%Y %H:%M")
        except ValueError:
            await message.answer(
                "❌ Неверный формат даты.\n"
                "Используйте: ДД.ММ.ГГГГ ЧЧ:ММ\n"
                "Пример: 05.02.2026 14:30\n"
                "Или введите 'Пропустить':",
                reply_markup=get_back_to_admin_keyboard()
            )
            return
    
    # ИСПРАВЛЕННАЯ СЕССИЯ
    async with async_session_maker() as session:
        # Обновляем статус и дату прибытия
        update_values = {
            "status": new_status,
            "updated_at": datetime.utcnow()
        }
        
        if arrival_date:
            update_values["arrival_date"] = arrival_date
        
        stmt = update(Product).where(Product.id == product_id).values(**update_values)
        await session.execute(stmt)
        await session.commit()
        
        date_info = f"Дата прибытия: {arrival_date.strftime('%d.%m.%Y %H:%M')}" if arrival_date else "Дата прибытия: текущее время"
        
        await message.answer(
            f"✅ Статус успешно обновлен!\n\n"
            f"Трек-код: {track_code}\n"
            f"Старый статус: {current_status}\n"
            f"Новый статус: {new_status}\n"
            f"{date_info}",
            reply_markup=get_back_to_admin_keyboard()
        )
    
    await state.clear()

@update_status_router.callback_query(F.data == "update_by_date")
async def update_by_date(callback: CallbackQuery, state: FSMContext):
    """Массовое обновление по дате"""
    await callback.message.edit_text(
        "📅 Массовое обновление товаров по дате\n\n"
        "Введите дату в формате ДД.ММ.ГГГГ\n"
        "Будут найдены все товары отправленные в эту дату:",
        reply_markup=get_back_to_admin_keyboard()
    )
    await state.set_state(AdminStates.WAITING_DATE_FOR_BULK_UPDATE)
    await callback.answer()

@update_status_router.message(AdminStates.WAITING_DATE_FOR_BULK_UPDATE)
async def process_date_for_bulk_update(message: Message, state: FSMContext):
    """Обработка даты для массового обновления"""
    date_text = message.text.strip()
    
    try:
        target_date = datetime.strptime(date_text, "%d.%m.%Y").date()
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты.\n"
            "Используйте: ДД.ММ.ГГГГ\n"
            "Пример: 05.02.2026",
            reply_markup=get_back_to_admin_keyboard()
        )
        return
    
    # ИСПРАВЛЕННАЯ СЕССИЯ
    async with async_session_maker() as session:
        # Ищем товары по дате отправки
        query = select(Product).where(
            Product.send_date >= target_date,
            Product.send_date < target_date.replace(day=target_date.day + 1)
        )
        result = await session.execute(query)
        products = result.scalars().all()
        
        if not products:
            await message.answer(
                f"❌ Не найдено товаров отправленных {date_text}",
                reply_markup=get_back_to_admin_keyboard()
            )
            return
        
        # Сохраняем найденные товары
        product_ids = [p.id for p in products]
        await state.update_data(
            bulk_product_ids=product_ids,
            bulk_date=date_text,
            found_count=len(products)
        )
        
        await message.answer(
            f"📋 Найдено товаров: {len(products)}\n"
            f"Дата отправки: {date_text}\n\n"
            "Выберите новый статус для всех товаров:",
            reply_markup=get_status_keyboard(is_bulk=True)
        )
        
        await state.set_state(AdminStates.WAITING_BULK_STATUS)

@update_status_router.callback_query(F.data.startswith("bulk_status_"))
async def process_bulk_status_update(callback: CallbackQuery, state: FSMContext):
    """Массовое обновление статусов"""
    new_status = callback.data.replace("bulk_status_", "")
    
    # Получаем данные из состояния
    data = await state.get_data()
    product_ids = data.get("bulk_product_ids", [])
    found_count = data.get("found_count", 0)
    
    if not product_ids:
        await callback.message.edit_text("❌ Не найдено товаров для обновления")
        await callback.answer()
        return
    
    # ИСПРАВЛЕННАЯ СЕССИЯ
    async with async_session_maker() as session:
        # Массовое обновление
        updated_count = 0
        for product_id in product_ids:
            stmt = update(Product).where(Product.id == product_id).values(
                status=new_status,
                updated_at=datetime.utcnow()
            )
            await session.execute(stmt)
            updated_count += 1
        
        await session.commit()
        
        await callback.message.edit_text(
            f"✅ Массовое обновление завершено!\n\n"
            f"Всего найдено: {found_count}\n"
            f"Обновлено: {updated_count}\n"
            f"Новый статус: {new_status}",
            reply_markup=get_back_to_admin_keyboard()
        )
    
    await state.clear()
    await callback.answer()