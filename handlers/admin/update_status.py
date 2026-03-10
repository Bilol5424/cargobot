"""
Обновление статусов товаров (reply-клавиатура)
"""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select, update

from database.models import Product, User, ProductStatus
from database.session import async_session_maker
from utils.states import AdminStates
from keyboards.admin import (
    get_status_update_menu_keyboard,
    get_status_keyboard,
    get_back_to_admin_keyboard,
    get_admin_main_keyboard,
    get_status_selection_keyboard,
)
from config import settings

logger = logging.getLogger(__name__)
update_status_router = Router()

# Маппирование текста кнопок на коды статусов (русский и таджикский)
STATUS_MAP = {
    # Русский
    "📝 Создан": "created",
    "🇨🇳 В Китае": "china_warehouse",
    "✈️ В пути": "in_transit",
    "🇹🇯 Прибыл в TJ": "tajikistan_warehouse",
    "✅ Готов к выдаче": "ready_for_pickup",
    "📦 Доставлен": "delivered",
    "❌ Отменен": "cancelled",
    "⚠️ Проблема": "problem",
    # Таджикский
    "📝 Сохта шуд": "created",
    "🇨🇳 Дар Чин": "china_warehouse",
    "✈️ Дар роҳ": "in_transit",
    "🇹🇯 Расид ба Тоҷикистон": "tajikistan_warehouse",
    "✅ Омода ба супоридан": "ready_for_pickup",
    "📦 Супорида шуд": "delivered",
    "❌ Бекор карда шуд": "cancelled",
    "⚠️ Мушкилот": "problem",
}

# Маппирование кодов статусов на понятные названия
STATUS_DISPLAY_NAMES = {
    "ru": {
        "created": "📝 Создан",
        "china_warehouse": "🇨🇳 В Китае",
        "in_transit": "✈️ В пути",
        "tajikistan_warehouse": "🇹🇯 Прибыл в TJ",
        "ready_for_pickup": "✅ Готов к выдаче",
        "delivered": "📦 Доставлен",
        "cancelled": "❌ Отменен",
        "problem": "⚠️ Проблема",
    },
    "tj": {
        "created": "📝 Сохта шуд",
        "china_warehouse": "🇨🇳 Дар Чин",
        "in_transit": "✈️ Дар роҳ",
        "tajikistan_warehouse": "🇹🇯 Расид ба Тоҷикистон",
        "ready_for_pickup": "✅ Омода ба супоридан",
        "delivered": "📦 Супорида шуд",
        "cancelled": "❌ Бекор карда шуд",
        "problem": "⚠️ Мушкилот",
    }
}

@update_status_router.message(F.text.in_(["🔄 Обновить статусы", "🔄 Навсозии статус"]))
async def update_status_menu(message: Message, state: FSMContext):
    """Главное меню обновления статусов"""
    if not settings.is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещен")
        return

    user_id = message.from_user.id
    async with async_session_maker() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"

    texts = {
        "ru": "🔄 Обновление статусов посылок\n\nВыберите способ обновления:",
        "tj": "🔄 Навсозии статусҳои посилкаҳо\n\nТарзи навсозиро интихоб кунед:"
    }

    await message.answer(
        texts.get(language, texts["ru"]),
        reply_markup=get_status_update_menu_keyboard(language)
    )
    await state.set_state(AdminStates.WAITING_UPDATE_METHOD)

@update_status_router.message(AdminStates.WAITING_UPDATE_METHOD, F.text.in_(["🔙 Назад", "🔙 Бозгашт"]))
async def back_from_update_method(message: Message, state: FSMContext):
    """Возврат из меню выбора метода обновления"""
    user_id = message.from_user.id
    admin_role = settings.get_admin_role(user_id)

    async with async_session_maker() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"

    await message.answer(
        "🛠 Админ-панель",
        reply_markup=get_admin_main_keyboard(role=admin_role, language=language)
    )
    await state.clear()

@update_status_router.message(AdminStates.WAITING_UPDATE_METHOD, F.text.in_(["🔍 По трек-коду", "🔍 Аз рӯи рамз"]))
async def update_by_track(message: Message, state: FSMContext):
    """Обновление статуса по трек-коду"""
    user_id = message.from_user.id
    async with async_session_maker() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"

    texts = {
        "ru": "📝 Введите трек-код посылки для обновления статуса:",
        "tj": "📝 Трек-коди посилкаро дохил кунед барои навсозии статус:"
    }

    await message.answer(
        texts.get(language, texts["ru"]),
        reply_markup=get_back_to_admin_keyboard(language)
    )
    await state.set_state(AdminStates.WAITING_TRACK_FOR_UPDATE)

@update_status_router.message(AdminStates.WAITING_TRACK_FOR_UPDATE)
async def process_track_for_update(message: Message, state: FSMContext):
    """Обработка введенного трек-кода"""
    if message.text.startswith("🔙"):
        # Возврат в меню выбора метода обновления
        user_id = message.from_user.id
        async with async_session_maker() as session:
            user = await session.execute(
                select(User).where(User.telegram_id == user_id)
            )
            user = user.scalar_one_or_none()
            language = user.language if user else "ru"

        texts = {
            "ru": "🔄 Обновление статусов посылок\n\nВыберите способ обновления:",
            "tj": "🔄 Навсозии статусҳои посилкаҳо\n\nТарзи навсозиро интихоб кунед:"
        }

        await message.answer(
            texts.get(language, texts["ru"]),
            reply_markup=get_status_update_menu_keyboard(language)
        )
        await state.set_state(AdminStates.WAITING_UPDATE_METHOD)
        return

    user_id = message.from_user.id
    admin_role = settings.get_admin_role(user_id)

    async with async_session_maker() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"

        track_code = message.text.strip()

        # Проверяем наличие трек-кода в БД
        product = await session.execute(
            select(Product).where(Product.track_code == track_code)
        )
        product = product.scalar_one_or_none()

        if not product:
            texts = {
                "ru": f"❌ Посылка с трек-кодом '{track_code}' не найдена в системе.\nПопробуйте введить корректный трек-код:",
                "tj": f"❌ Посилка бо рамзи '{track_code}' дар система ёфт нашуд.\nТрек-коди дурусти дохил кунед:"
            }
            await message.answer(
                texts.get(language, texts["ru"]),
                reply_markup=get_back_to_admin_keyboard(language)
            )
            return

        # Сохраняем данные посылки в состояние
        current_status_value = product.status.value if product.status else "unknown"
        current_status_display = STATUS_DISPLAY_NAMES.get(language, {}).get(
            current_status_value, current_status_value
        )

        await state.update_data(
            product_id=product.id,
            track_code=track_code,
            current_status=current_status_value,
            current_status_display=current_status_display,
            product_name=product.product_name
        )

        # Отправляем информацию о посылке
        texts = {
            "ru": {
                "title": "📦 Посылка найдена:",
                "code": "Трек-код",
                "name": "Название",
                "status": "Текущий статус",
                "select_new": "Выберите новый статус:",
                "not_specified": "Не указано"
            },
            "tj": {
                "title": "📦 Посилка ёфт шуд:",
                "code": "Рамзи трек",
                "name": "Ном",
                "status": "Статусҳои ҷорӣ",
                "select_new": "Статусҳои нави интихоб кунед:",
                "not_specified": "Махсус карда нашуда"
            }
        }

        t = texts.get(language, texts["ru"])

        info_text = (
            f"{t['title']}\n\n"
            f"🔐 {t['code']}: {product.track_code}\n"
            f"📝 {t['name']}: {product.product_name or t['not_specified']}\n"
            f"📊 {t['status']}: {current_status_display}\n\n"
            f"{t['select_new']}"
        )

        await message.answer(
            info_text,
            reply_markup=get_status_keyboard(language=language)
        )
        await state.set_state(AdminStates.WAITING_NEW_STATUS)


@update_status_router.message(AdminStates.WAITING_NEW_STATUS)
async def set_new_status(message: Message, state: FSMContext):
    """Установка нового статуса"""
    if message.text.startswith("🔙"):
        # Возврат к вводу трек-кода
        user_id = message.from_user.id
        async with async_session_maker() as session:
            user = await session.execute(
                select(User).where(User.telegram_id == user_id)
            )
            user = user.scalar_one_or_none()
            language = user.language if user else "ru"

        texts = {
            "ru": "📝 Введите трек-код посылки для обновления статуса:",
            "tj": "📝 Трек-коди посилкаро дохил кунед барои навсозии статус:"
        }

        await message.answer(
            texts.get(language, texts["ru"]),
            reply_markup=get_back_to_admin_keyboard(language)
        )
        await state.set_state(AdminStates.WAITING_TRACK_FOR_UPDATE)
        return

    user_id = message.from_user.id
    admin_role = settings.get_admin_role(user_id)

    async with async_session_maker() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"

        # Получаем новый статус
        new_status_code = STATUS_MAP.get(message.text)
        if not new_status_code:
            texts = {
                "ru": "❌ Пожалуйста, выберите статус из предложенного списка.",
                "tj": "❌ Лутфан, статусро аз рӯйхати пешниҳодшуда интихоб кунед."
            }
            await message.answer(
                texts.get(language, texts["ru"]),
                reply_markup=get_status_keyboard(language=language)
            )
            return

        # Получаем данные из состояния
        data = await state.get_data()
        product_id = data.get("product_id")
        track_code = data.get("track_code")
        current_status = data.get("current_status")
        current_status_display = data.get("current_status_display")
        product_name = data.get("product_name")

        # Обновляем статус в БД
        try:
            stmt = update(Product).where(Product.id == product_id).values(
                status=new_status_code,
                updated_at=datetime.utcnow()
            )
            await session.execute(stmt)
            await session.commit()

            new_status_display = STATUS_DISPLAY_NAMES.get(language, {}).get(
                new_status_code, new_status_code
            )

            texts = {
                "ru": {
                    "title": "✅ Статус успешно обновлен!",
                    "code": "Трек-код",
                    "name": "Название",
                    "old": "Старый статус",
                    "new": "Новый статус",
                    "updated": "Время обновления",
                    "not_specified": "Не указано"
                },
                "tj": {
                    "title": "✅ Статус бомуваффақият ба-навсозӣ рафт!",
                    "code": "Рамзи трек",
                    "name": "Ном",
                    "old": "Статусҳои қадима",
                    "new": "Статусҳои нав",
                    "updated": "Вақти навсозӣ",
                    "not_specified": "Махсус карда нашуда"
                }
            }

            t = texts.get(language, texts["ru"])

            result_text = (
                f"{t['title']}\n\n"
                f"🔐 {t['code']}: {track_code}\n"
                f"📝 {t['name']}: {product_name or t['not_specified']}\n"
                f"📊 {t['old']}: {current_status_display}\n"
                f"📊 {t['new']}: {new_status_display}\n"
                f"⏰ {t['updated']}: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )

            await message.answer(
                result_text,
                reply_markup=get_admin_main_keyboard(role=admin_role, language=language)
            )

            logger.info(
                f"✅ Администратор {user_id} обновил статус посылки {track_code}: "
                f"{current_status} → {new_status_code}"
            )

            await state.clear()

        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении статуса: {e}", exc_info=True)
            texts = {
                "ru": f"❌ Ошибка при обновлении статуса: {str(e)[:100]}",
                "tj": f"❌ Хатогӣ дар ҳангоми навсозии статус: {str(e)[:100]}"
            }
            await message.answer(
                texts.get(language, texts["ru"]),
                reply_markup=get_admin_main_keyboard(role=admin_role, language=language)
            )
            await state.clear()


@update_status_router.message(AdminStates.WAITING_UPDATE_METHOD, F.text.in_(["📋 Массовое обновление", "📋 Навсозии оммавӣ"]))
async def bulk_update_menu_in_status(message: Message, state: FSMContext):
    """Меню массового обновления статуса"""
    from handlers.admin.bulk_update import BulkUpdateState
    await state.set_state(BulkUpdateState.waiting_for_status)

    user_id = message.from_user.id
    async with async_session_maker() as session:
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


@update_status_router.message(AdminStates.WAITING_UPDATE_METHOD, F.text.in_(["📅 По дате отправки", "📅 Аз рӯи сана"]))
async def update_by_date(message: Message, state: FSMContext):
    """Обновление статуса по дате отправки"""
    user_id = message.from_user.id
    async with async_session_maker() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"

    texts = {
        "ru": "📅 Введите дату отправки в формате ДД.ММ.ГГГГ (например, 15.03.2026):",
        "tj": "📅 Санаи фиристоданро дар формати РР.ММ.СССС дохил кунед (масалан, 15.03.2026):"
    }

    await message.answer(
        texts.get(language, texts["ru"]),
        reply_markup=get_back_to_admin_keyboard(language)
    )
    await state.set_state(AdminStates.WAITING_DATE_FOR_BULK_UPDATE)


@update_status_router.message(AdminStates.WAITING_UPDATE_METHOD)
async def invalid_update_method(message: Message, state: FSMContext):
    """Обработка некорректного выбора способа обновления"""
    user_id = message.from_user.id
    async with async_session_maker() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"

    texts = {
        "ru": "❌ Пожалуйста, выберите один из предложенных вариантов.",
        "tj": "❌ Лутфан, яке аз вариантҳои пешниҳодшударо интихоб кунед."
    }

    await message.answer(
        texts.get(language, texts["ru"]),
        reply_markup=get_status_update_menu_keyboard(language)
    )


@update_status_router.message(AdminStates.WAITING_DATE_FOR_BULK_UPDATE)
async def process_date_for_update(message: Message, state: FSMContext):
    """Обработка введенной даты"""
    if message.text.startswith("🔙"):
        # Возврат в меню выбора метода обновления
        user_id = message.from_user.id
        async with async_session_maker() as session:
            user = await session.execute(
                select(User).where(User.telegram_id == user_id)
            )
            user = user.scalar_one_or_none()
            language = user.language if user else "ru"

        texts = {
            "ru": "🔄 Обновление статусов посылок\n\nВыберите способ обновления:",
            "tj": "🔄 Навсозии статусҳои посилкаҳо\n\nТарзи навсозиро интихоб кунед:"
        }

        await message.answer(
            texts.get(language, texts["ru"]),
            reply_markup=get_status_update_menu_keyboard(language)
        )
        await state.set_state(AdminStates.WAITING_UPDATE_METHOD)
        return

    user_id = message.from_user.id
    async with async_session_maker() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"

    try:
        date_str = message.text.strip()
        date = datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        texts = {
            "ru": "❌ Неверный формат даты. Введите в формате ДД.ММ.ГГГГ:",
            "tj": "❌ Формати сана нодуруст. Дар формати РР.ММ.СССС дохил кунед:"
        }
        await message.answer(
            texts.get(language, texts["ru"]),
            reply_markup=get_back_to_admin_keyboard(language)
        )
        return

    await state.update_data(update_date=date)

    texts = {
        "ru": f"📅 Выбрана дата: {date.strftime('%d.%m.%Y')}\n\nВыберите новый статус для товаров:",
        "tj": f"📅 Сана интихоб шуд: {date.strftime('%d.%m.%Y')}\n\nСтатуси навро барои маҳсулот интихоб кунед:"
    }

    await message.answer(
        texts.get(language, texts["ru"]),
        reply_markup=get_status_keyboard(language=language)
    )
    await state.set_state(AdminStates.WAITING_BULK_STATUS)


@update_status_router.message(AdminStates.WAITING_BULK_STATUS)
async def set_bulk_status(message: Message, state: FSMContext):
    """Установка нового статуса для товаров по дате"""
    if message.text.startswith("🔙"):
        # Возврат к вводу даты
        user_id = message.from_user.id
        async with async_session_maker() as session:
            user = await session.execute(
                select(User).where(User.telegram_id == user_id)
            )
            user = user.scalar_one_or_none()
            language = user.language if user else "ru"

        texts = {
            "ru": "📅 Введите дату отправки в формате ДД.ММ.ГГГГ:",
            "tj": "📅 Санаи фиристоданро дар формати РР.ММ.СССС дохил кунед:"
        }

        await message.answer(
            texts.get(language, texts["ru"]),
            reply_markup=get_back_to_admin_keyboard(language)
        )
        await state.set_state(AdminStates.WAITING_DATE_FOR_BULK_UPDATE)
        return

    user_id = message.from_user.id
    admin_role = settings.get_admin_role(user_id)

    async with async_session_maker() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"

        new_status_code = STATUS_MAP.get(message.text)
        if not new_status_code:
            texts = {
                "ru": "❌ Пожалуйста, выберите статус из предложенного списка.",
                "tj": "❌ Лутфан, статусро аз рӯйхати пешниҳодшуда интихоб кунед."
            }
            await message.answer(
                texts.get(language, texts["ru"]),
                reply_markup=get_status_keyboard(language=language)
            )
            return

        data = await state.get_data()
        update_date = data.get("update_date")

        from sqlalchemy import func
        products = await session.execute(
            select(Product).where(func.date(Product.created_at) == update_date)
        )
        products = products.scalars().all()

        if not products:
            texts = {
                "ru": f"❌ Товары, отправленные {update_date.strftime('%d.%m.%Y')}, не найдены.",
                "tj": f"❌ Маҳсулотҳои фиристодашуда {update_date.strftime('%d.%m.%Y')} ёфт нашуданд."
            }
            await message.answer(
                texts.get(language, texts["ru"]),
                reply_markup=get_admin_main_keyboard(role=admin_role, language=language)
            )
            await state.clear()
            return

        updated_count = 0
        for product in products:
            try:
                stmt = update(Product).where(Product.id == product.id).values(
                    status=new_status_code,
                    updated_at=datetime.utcnow()
                )
                await session.execute(stmt)
                updated_count += 1
            except Exception as e:
                pass

        await session.commit()

        new_status_display = STATUS_DISPLAY_NAMES.get(language, {}).get(
            new_status_code, new_status_code
        )

        texts = {
            "ru": f"✅ Обновлено {updated_count} из {len(products)} товаров на статус '{new_status_display}'.",
            "tj": f"✅ {updated_count} аз {len(products)} маҳсулот ба статус '{new_status_display}' навсозӣ шуд."
        }

        await message.answer(
            texts.get(language, texts["ru"]),
            reply_markup=get_admin_main_keyboard(role=admin_role, language=language)
        )

        logger.info(
            f"✅ Администратор {user_id} обновил статус {updated_count} товаров по дате {update_date}: {new_status_code}"
        )

        await state.clear()
