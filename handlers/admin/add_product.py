"""
Добавление товаров администратором (reply-клавиатура)
"""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select

from database.models import Product, User
from database.session import async_session_maker
from database.repository import UserTrackCodeRepository
from utils.states import AdminStates
from keyboards.admin import (
    get_back_to_admin_keyboard,
    get_product_categories_keyboard,
    get_yes_no_keyboard,
)
from services.track_code_generator import TrackCodeGenerator
from config import settings

logger = logging.getLogger(__name__)
add_product_router = Router()

CATEGORY_MAP = {
    "📱 Электроника": "electronics",
    "👕 Одежда": "clothing",
    "👟 Обувь": "shoes",
    "🏠 Бытовая техника": "home_appliances",
    "💄 Косметика": "beauty",
    "🧸 Игрушки": "toys",
    "🚗 Автозапчасти": "automotive",
    "⚽ Спорттовары": "sports",
    "📦 Другое": "other",
    "📱 Электроника": "electronics",
    "👕 Либос": "clothing",
    "👟 Пойафзол": "shoes",
    "🏠 Асбобҳои хонагӣ": "home_appliances",
    "💄 Косметика": "beauty",
    "🧸 Бозичаҳо": "toys",
    "🚗 Қисмҳои автомобил": "automotive",
    "⚽ Ашёҳои варзишӣ": "sports",
    "📦 Дигар": "other",
}


@add_product_router.message(F.text == "📦 Добавить трек-код")
async def add_product_start(message: Message, state: FSMContext):
    if not settings.is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещен")
        return

    track_code = TrackCodeGenerator.generate_track_code(message.from_user.id)
    await state.update_data(track_code=track_code, user_id=message.from_user.id)

    await message.answer(
        f"📦 Добавление нового товара\n\n"
        f"📋 Сгенерирован трек-код: {track_code}\n\n"
        f"Введите название товара:",
        reply_markup=get_back_to_admin_keyboard()
    )
    await state.set_state(AdminStates.WAITING_PRODUCT_NAME)


@add_product_router.message(AdminStates.WAITING_PRODUCT_NAME)
async def process_product_name(message: Message, state: FSMContext):
    if message.text in ("🔙 Назад", "🔙 Бозгашт", "🔙 Назад в админ-панель"):
        await state.clear()
        from handlers.admin.main_menu import admin_menu
        await admin_menu(message)
        return

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
        reply_markup=get_product_categories_keyboard(language="ru")
    )
    await state.set_state(AdminStates.WAITING_PRODUCT_CATEGORY)


@add_product_router.message(AdminStates.WAITING_PRODUCT_CATEGORY)
async def process_product_category(message: Message, state: FSMContext):
    if message.text in ("🔙 Назад", "🔙 Бозгашт", "🔙 Назад в админ-панель"):
        data = await state.get_data()
        await message.answer(
            f"📦 Добавление нового товара\n\n"
            f"📋 Трек-код: {data.get('track_code')}\n\n"
            f"Введите название товара:",
            reply_markup=get_back_to_admin_keyboard()
        )
        await state.set_state(AdminStates.WAITING_PRODUCT_NAME)
        return

    category_code = CATEGORY_MAP.get(message.text)
    if not category_code:
        await message.answer("❌ Пожалуйста, выберите категорию из списка.")
        return

    await state.update_data(product_category=category_code)

    await message.answer(
        "🔢 Введите количество товара (целое число):",
        reply_markup=get_back_to_admin_keyboard()
    )
    await state.set_state(AdminStates.WAITING_PRODUCT_QUANTITY)


@add_product_router.message(AdminStates.WAITING_PRODUCT_QUANTITY)
async def process_product_quantity(message: Message, state: FSMContext):
    if message.text in ("🔙 Назад", "🔙 Бозгашт", "🔙 Назад в админ-панель"):
        await message.answer(
            "📋 Выберите категорию товара:",
            reply_markup=get_product_categories_keyboard()
        )
        await state.set_state(AdminStates.WAITING_PRODUCT_CATEGORY)
        return

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
    if message.text in ("🔙 Назад", "🔙 Бозгашт", "🔙 Назад в админ-панель"):
        await message.answer(
            "🔢 Введите количество товара (целое число):",
            reply_markup=get_back_to_admin_keyboard()
        )
        await state.set_state(AdminStates.WAITING_PRODUCT_QUANTITY)
        return

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
    if message.text in ("🔙 Назад", "🔙 Бозгашт", "🔙 Назад в админ-панель"):
        await message.answer(
            "💰 Введите цену за единицу:",
            reply_markup=get_back_to_admin_keyboard()
        )
        await state.set_state(AdminStates.WAITING_PRODUCT_PRICE)
        return

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


@add_product_router.message(AdminStates.WAITING_PRODUCT_SPECIAL, F.text.in_(["✅ Да", "❌ Нет"]))
async def process_fragile(message: Message, state: FSMContext):
    fragile = (message.text == "✅ Да")
    await state.update_data(fragile=fragile)

    await message.answer(
        "🔋 Товар содержит батареи или аккумуляторы?",
        reply_markup=get_yes_no_keyboard("battery")
    )
    await state.update_data(special_step="battery")


@add_product_router.message(AdminStates.WAITING_PRODUCT_SPECIAL, F.text.in_(["✅ Да", "❌ Нет"]))
async def process_battery(message: Message, state: FSMContext):
    data = await state.get_data()
    step = data.get("special_step")
    if step != "battery":
        return

    has_battery = (message.text == "✅ Да")
    await state.update_data(has_battery=has_battery)

    await message.answer(
        "💧 Товар является жидкостью?",
        reply_markup=get_yes_no_keyboard("liquid")
    )
    await state.update_data(special_step="liquid")


@add_product_router.message(AdminStates.WAITING_PRODUCT_SPECIAL, F.text.in_(["✅ Да", "❌ Нет"]))
async def process_liquid(message: Message, state: FSMContext):
    data = await state.get_data()
    step = data.get("special_step")
    if step != "liquid":
        return

    is_liquid = (message.text == "✅ Да")
    await state.update_data(is_liquid=is_liquid)

    await message.answer(
        "🌍 Введите страну отправления товара:\n"
        "Пример: Китай, США, Россия",
        reply_markup=get_back_to_admin_keyboard()
    )
    await state.set_state(AdminStates.WAITING_PRODUCT_COUNTRY)


@add_product_router.message(AdminStates.WAITING_PRODUCT_COUNTRY)
async def process_country(message: Message, state: FSMContext):
    if message.text in ("🔙 Назад", "🔙 Бозгашт", "🔙 Назад в админ-панель"):
        await message.answer(
            "💧 Товар является жидкостью?",
            reply_markup=get_yes_no_keyboard("liquid")
        )
        await state.update_data(special_step="liquid")
        await state.set_state(AdminStates.WAITING_PRODUCT_SPECIAL)
        return

    country = message.text.strip()
    await state.update_data(country_from=country)

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
    if message.text in ("🔙 Назад", "🔙 Бозгашт", "🔙 Назад в админ-панель"):
        await message.answer(
            "🌍 Введите страну отправления товара:",
            reply_markup=get_back_to_admin_keyboard()
        )
        await state.set_state(AdminStates.WAITING_PRODUCT_COUNTRY)
        return

    delivery_type = message.text.strip()
    if delivery_type in ["1", "авиа", "авиадоставка", "aviation"]:
        delivery_type = "Авиадоставка"
    elif delivery_type in ["2", "морская", "море", "sea"]:
        delivery_type = "Морская доставка"
    elif delivery_type in ["3", "авто", "автодоставка", "car"]:
        delivery_type = "Автодоставка"

    await state.update_data(delivery_type=delivery_type)

    data = await state.get_data()
    quantity = data.get('quantity', 1)
    unit_price = data.get('unit_price_usd', 0)
    total_value = quantity * unit_price

    summary = (
        f"📋 Сводка по товару:\n\n"
        f"📦 Трек-код: {data.get('track_code')}\n"
        f"📝 Название: {data.get('product_name')}\n"
        f"🏷️ Категория: {data.get('product_category')}\n"
        f"🔢 Количество: {quantity} шт.\n"
        f"💰 Цена за ед.: ${unit_price:.2f}\n"
        f"💵 Общая стоимость: ${total_value:.2f}\n"
        f"⚖️ Вес: {data.get('weight_kg')} кг\n"
        f"🎯 Хрупкий: {'Да' if data.get('fragile') else 'Нет'}\n"
        f"🔋 Батарея: {'Да' if data.get('has_battery') else 'Нет'}\n"
        f"💧 Жидкость: {'Да' if data.get('is_liquid') else 'Нет'}\n"
        f"🌍 Страна: {data.get('country_from')}\n"
        f"🚚 Доставка: {delivery_type}\n\n"
        f"✅ Все верно? (да/нет)"
    )

    await message.answer(
        summary,
        reply_markup=get_yes_no_keyboard("confirm")
    )
    await state.update_data(total_value_usd=total_value)
    await state.set_state(AdminStates.WAITING_CONFIRMATION)


@add_product_router.message(AdminStates.WAITING_CONFIRMATION, F.text.in_(["✅ Да", "❌ Нет"]))
async def process_confirmation(message: Message, state: FSMContext):
    confirm = (message.text == "✅ Да")
    if not confirm:
        await message.answer(
            "❌ Добавление товара отменено.",
            reply_markup=get_back_to_admin_keyboard()
        )
        await state.clear()
        return

    data = await state.get_data()

    async with async_session_maker() as session:
        existing = await session.execute(
            select(Product).where(Product.track_code == data['track_code'])
        )
        if existing.scalar_one_or_none():
            await message.answer(
                f"❌ Товар с трек-кодом {data['track_code']} уже существует.",
                reply_markup=get_back_to_admin_keyboard()
            )
            await state.clear()
            return

        product_data = {
            "track_code": data['track_code'],
            "user_id": data['user_id'],
            "product_name": data['product_name'],
            "product_category": data['product_category'],
            "quantity": data['quantity'],
            "unit_price_usd": data['unit_price_usd'],
            "total_value_usd": data['total_value_usd'],
            "weight_kg": data['weight_kg'],
            "fragile": data.get('fragile', False),
            "has_battery": data.get('has_battery', False),
            "is_liquid": data.get('is_liquid', False),
            "status": "CREATED",
            "country_from": data.get('country_from'),
            "delivery_type": data.get('delivery_type'),
            "send_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        new_product = Product(**product_data)
        session.add(new_product)
        await session.commit()

        utc_repo = UserTrackCodeRepository(session)
        pending_user_ids = await utc_repo.activate_pending_track_codes(data['track_code'])

        notified_count = 0
        for uid in pending_user_ids:
            try:
                user = await session.execute(select(User).where(User.id == uid))
                u = user.scalar_one_or_none()
                if u:
                    notify_text = {
                        "ru": f"📦 Ваш трек-код <code>{data['track_code']}</code> зарегистрирован!\n\n"
                              f"🏷️ Товар: {data['product_name']}\n"
                              f"📍 Статус: Создан",
                        "tj": f"📦 Рамзи тамошобини шумо <code>{data['track_code']}</code> сабт шуд!\n\n"
                              f"🏷️ Маҳсулот: {data['product_name']}\n"
                              f"📍 Статус: Сохта шудааст"
                    }
                    await message.bot.send_message(
                        u.telegram_id,
                        notify_text.get(u.language, notify_text["ru"]),
                        parse_mode="HTML"
                    )
                    notified_count += 1
            except Exception as e:
                logger.error(f"Ошибка уведомления пользователя {uid}: {e}")

        notify_info = f"\n\n📨 Уведомлено пользователей: {notified_count}" if notified_count else ""

        await message.answer(
            f"✅ Товар успешно добавлен!\n\n"
            f"📦 Трек-код: {data['track_code']}\n"
            f"📝 Название: {data['product_name']}\n"
            f"🏷️ Категория: {data['product_category']}\n"
            f"🔢 Количество: {data['quantity']} шт.\n"
            f"💰 Общая стоимость: ${data['total_value_usd']:.2f}\n\n"
            f"📊 Статус: CREATED\n"
            f"⏰ Дата добавления: {datetime.utcnow().strftime('%d.%m.%Y %H:%M')}"
            f"{notify_info}",
            reply_markup=get_back_to_admin_keyboard()
        )

    await state.clear()