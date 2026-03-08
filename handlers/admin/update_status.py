"""
Обновление статусов товаров (reply-клавиатура)
"""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select, update

from database.models import Product
from database.session import async_session_maker
from utils.states import AdminStates
from keyboards.admin import (
    get_status_update_menu_keyboard,
    get_status_keyboard,
    get_back_to_admin_keyboard,
)
from config import settings

logger = logging.getLogger(__name__)
update_status_router = Router()

STATUS_MAP = {
    "📝 Создан": "CREATED",
    "🇨🇳 В Китае": "IN_CHINA_WAREHOUSE",
    "✈️ В пути": "IN_TRANSIT",
    "🇹🇯 Прибыл в TJ": "ARRIVED_TJ",
    "✅ Готов к выдаче": "READY_FOR_PICKUP",
    "📦 Доставлен": "DELIVERED",
    "❌ Отменен": "CANCELLED",
    "⚠️ Проблема": "PROBLEM",
    # таджикские варианты
    "📝 Сохта шуд": "CREATED",
    "🇨🇳 Дар Чин": "IN_CHINA_WAREHOUSE",
    "✈️ Дар роҳ": "IN_TRANSIT",
    "🇹🇯 Расид ба Тоҷикистон": "ARRIVED_TJ",
    "✅ Омода ба супоридан": "READY_FOR_PICKUP",
    "📦 Супорида шуд": "DELIVERED",
    "❌ Бекор карда шуд": "CANCELLED",
    "⚠️ Мушкилот": "PROBLEM",
}

@update_status_router.message(F.text == "🔄 Обновить статусы")
async def update_status_menu(message: Message, state: FSMContext):
    if not settings.is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещен")
        return

    await message.answer(
        "🔄 Обновление статусов товаров\n\n"
        "Выберите способ обновления:",
        reply_markup=get_status_update_menu_keyboard()
    )
    await state.set_state(AdminStates.WAITING_UPDATE_METHOD)

@update_status_router.message(AdminStates.WAITING_UPDATE_METHOD, F.text == "🔍 По трек-коду")
async def update_by_track(message: Message, state: FSMContext):
    await message.answer(
        "📝 Введите трек-код товара для обновления статуса:",
        reply_markup=get_back_to_admin_keyboard()
    )
    await state.set_state(AdminStates.WAITING_TRACK_FOR_UPDATE)

@update_status_router.message(AdminStates.WAITING_TRACK_FOR_UPDATE)
async def process_track_for_update(message: Message, state: FSMContext):
    if message.text in ("🔙 Назад", "🔙 Бозгашт", "🔙 Назад в админ-панель"):
        await update_status_menu(message, state)
        return

    track_code = message.text.strip()
    async with async_session_maker() as session:
        product = await session.execute(
            select(Product).where(Product.track_code == track_code)
        )
        product = product.scalar_one_or_none()
        if not product:
            await message.answer(
                f"❌ Товар с трек-кодом {track_code} не найден.\n"
                "Попробуйте еще раз:",
                reply_markup=get_back_to_admin_keyboard()
            )
            return

        await state.update_data(
            product_id=product.id,
            track_code=track_code,
            current_status=product.status.value if product.status else None
        )

        await message.answer(
            f"📦 Товар найден:\n"
            f"Код: {product.track_code}\n"
            f"Название: {product.product_name or 'Не указано'}\n"
            f"Текущий статус: {product.status.value if product.status else 'Не установлен'}\n\n"
            f"Выберите новый статус:",
            reply_markup=get_status_keyboard(language="ru")
        )
        await state.set_state(AdminStates.WAITING_NEW_STATUS)

@update_status_router.message(AdminStates.WAITING_NEW_STATUS)
async def set_new_status(message: Message, state: FSMContext):
    if message.text in ("🔙 Назад", "🔙 Бозгашт", "🔙 Назад в админ-панель"):
        await update_status_menu(message, state)
        return

    new_status_code = STATUS_MAP.get(message.text)
    if not new_status_code:
        await message.answer("❌ Пожалуйста, выберите статус из списка.")
        return

    data = await state.get_data()
    product_id = data.get("product_id")
    track_code = data.get("track_code")
    current_status = data.get("current_status")

    async with async_session_maker() as session:
        if new_status_code == "ARRIVED_TJ":
            await state.update_data(new_status=new_status_code)
            await message.answer(
                f"✅ Статус изменен с '{current_status}' на '{new_status_code}'\n\n"
                f"Введите дату прибытия в формате ДД.ММ.ГГГГ ЧЧ:ММ\n"
                f"Например: 05.02.2026 14:30\n"
                f"Или напишите 'Пропустить', чтобы установить текущее время:",
                reply_markup=get_back_to_admin_keyboard()
            )
            await state.set_state(AdminStates.WAITING_ARRIVAL_DATE)
        else:
            stmt = update(Product).where(Product.id == product_id).values(
                status=new_status_code,
                updated_at=datetime.utcnow()
            )
            await session.execute(stmt)
            await session.commit()

            await message.answer(
                f"✅ Статус успешно обновлен!\n\n"
                f"Трек-код: {track_code}\n"
                f"Старый статус: {current_status}\n"
                f"Новый статус: {new_status_code}",
                reply_markup=get_back_to_admin_keyboard()
            )
            await state.clear()

@update_status_router.message(AdminStates.WAITING_ARRIVAL_DATE)
async def process_arrival_date(message: Message, state: FSMContext):
    if message.text in ("🔙 Назад", "🔙 Бозгашт", "🔙 Назад в админ-панель"):
        await message.answer(
            "Выберите новый статус:",
            reply_markup=get_status_keyboard()
        )
        await state.set_state(AdminStates.WAITING_NEW_STATUS)
        return

    date_text = message.text.strip()
    data = await state.get_data()
    product_id = data["product_id"]
    track_code = data["track_code"]
    current_status = data["current_status"]
    new_status = data["new_status"]

    arrival_date = None
    if date_text.lower() != "пропустить":
        try:
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

    async with async_session_maker() as session:
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

@update_status_router.message(AdminStates.WAITING_UPDATE_METHOD, F.text == "📅 По дате отправки")
async def update_by_date(message: Message, state: FSMContext):
    await message.answer(
        "📅 Массовое обновление товаров по дате\n\n"
        "Введите дату в формате ДД.ММ.ГГГГ\n"
        "Будут найдены все товары отправленные в эту дату:",
        reply_markup=get_back_to_admin_keyboard()
    )
    await state.set_state(AdminStates.WAITING_DATE_FOR_BULK_UPDATE)

@update_status_router.message(AdminStates.WAITING_DATE_FOR_BULK_UPDATE)
async def process_date_for_bulk_update(message: Message, state: FSMContext):
    if message.text in ("🔙 Назад", "🔙 Бозгашт", "🔙 Назад в админ-панель"):
        await update_status_menu(message, state)
        return

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

    async with async_session_maker() as session:
        from sqlalchemy import cast, Date
        result = await session.execute(
            select(Product).where(cast(Product.send_date, Date) == target_date)
        )
        products = result.scalars().all()

        if not products:
            await message.answer(
                f"❌ Не найдено товаров отправленных {date_text}",
                reply_markup=get_back_to_admin_keyboard()
            )
            return

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

@update_status_router.message(AdminStates.WAITING_BULK_STATUS)
async def process_bulk_status_update(message: Message, state: FSMContext):
    if message.text in ("🔙 Назад", "🔙 Бозгашт", "🔙 Назад в админ-панель"):
        await update_status_menu(message, state)
        return

    new_status_code = STATUS_MAP.get(message.text)
    if not new_status_code:
        await message.answer("❌ Пожалуйста, выберите статус из списка.")
        return

    data = await state.get_data()
    product_ids = data.get("bulk_product_ids", [])
    found_count = data.get("found_count", 0)

    async with async_session_maker() as session:
        updated_count = 0
        for pid in product_ids:
            stmt = update(Product).where(Product.id == pid).values(
                status=new_status_code,
                updated_at=datetime.utcnow()
            )
            await session.execute(stmt)
            updated_count += 1
        await session.commit()

        await message.answer(
            f"✅ Массовое обновление завершено!\n\n"
            f"Всего найдено: {found_count}\n"
            f"Обновлено: {updated_count}\n"
            f"Новый статус: {new_status_code}",
            reply_markup=get_back_to_admin_keyboard()
        )
    await state.clear()

@update_status_router.message(AdminStates.WAITING_UPDATE_METHOD, F.text == "📋 Массовое обновление")
async def bulk_update_general(message: Message, state: FSMContext):
    await message.answer(
        "⚙️ Функция массового обновления в разработке.\n"
        "Пока доступно обновление по дате.",
        reply_markup=get_status_update_menu_keyboard()
    )