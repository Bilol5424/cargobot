"""
Генерация отчетов для администратора
"""
import logging
from datetime import datetime, timedelta
from io import BytesIO
import pandas as pd
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy import select, func
import csv

from database.models import Product, User, ProductStatus
from database.session import async_session_maker
from keyboards.admin import get_reports_keyboard, get_back_to_admin_keyboard, get_admin_main_keyboard
from config import settings
from utils.states import AdminStates

logger = logging.getLogger(__name__)
reports_router = Router()


# Статусы отчетов
class ReportStates(StatesGroup):
    waiting_for_period = State()
    waiting_for_export_format = State()


# Маппирование статусов на отображаемые названия
STATUS_DISPLAY = {
    "ru": {
        "created": "📝 Создан",
        "china_warehouse": "🇨🇳 В Китае",
        "in_transit": "✈️ В пути",
        "tajikistan_warehouse": "🇹🇯 Прибыл на склад",
        "ready_for_pickup": "📍 На выдаче",
        "delivered": "✅ Выдан",
        "cancelled": "❌ Отменен",
        "problem": "⚠️ Проблема",
    },
    "tj": {
        "created": "📝 Сохта шуд",
        "china_warehouse": "🇨🇳 Дар Чин",
        "in_transit": "✈️ Дар роҳ",
        "tajikistan_warehouse": "🇹🇯 Дар анбор расид",
        "ready_for_pickup": "📍 Барои супоридан омода",
        "delivered": "✅ Супорида шуд",
        "cancelled": "❌ Бекор шуд",
        "problem": "⚠️ Мушкилот",
    }
}


@reports_router.message(F.text.in_(["📊 Отчеты", "📊 Ҳисоботҳо"]))
async def reports_menu(message: Message, state: FSMContext):
    """Главное меню отчетов"""
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
        "ru": {
            "title": "📊 Отчеты и статистика",
            "description": "Выберите тип отчета:"
        },
        "tj": {
            "title": "📊 Ҳисоботҳо ва омор",
            "description": "Намуди ҳисобот интихоб кунед:"
        }
    }

    t = texts.get(language, texts["ru"])

    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    from aiogram.utils.keyboard import ReplyKeyboardBuilder

    buttons = {
        "ru": {
            "general": "📈 Общая статистика",
            "by_status": "📊 По статусам",
            "by_period": "📅 За период",
            "export": "💾 Экспорт данных",
            "back": "🔙 Назад"
        },
        "tj": {
            "general": "📈 Омори умумӣ",
            "by_status": "📊 Аз рӯи статус",
            "by_period": "📅 Дар давраи вақтӣ",
            "export": "💾 Экспорти маълумот",
            "back": "🔙 Бозгашт"
        }
    }

    b = buttons.get(language, buttons["ru"])

    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=b["general"]))
    builder.add(KeyboardButton(text=b["by_status"]))
    builder.add(KeyboardButton(text=b["by_period"]))
    builder.add(KeyboardButton(text=b["export"]))
    builder.row(KeyboardButton(text=b["back"]))

    await message.answer(
        f"{t['title']}\n\n{t['description']}",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )


@reports_router.message(F.text.in_(["🔙 Назад", "🔙 Бозгашт"]))
async def back_from_reports_menu(message: Message):
    """Возврат из меню отчетов в главное меню администратора"""
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

    from keyboards.admin import get_admin_main_keyboard
    admin_role = settings.get_admin_role(user_id)

    await message.answer(
        "🛠 Админ-панель",
        reply_markup=get_admin_main_keyboard(role=admin_role, language=language)
    )


@reports_router.message(F.text.in_(["📈 Общая статистика", "📈 Омори умумӣ"]))
async def general_statistics(message: Message):
    """Общая статистика по системе"""
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
        admin_role = settings.get_admin_role(user_id)

        # Получаем общую статистику
        total_products = await session.scalar(select(func.count(Product.id))) or 0
        total_users = await session.scalar(select(func.count(User.id))) or 0

        # Статистика по статусам
        status_stats = {}
        for status in ProductStatus:
            count = await session.scalar(
                select(func.count(Product.id)).where(Product.status == status.value)
            ) or 0
            status_stats[status.value] = count

        # Новые посылки за сегодня
        today = datetime.now().date()
        today_products = await session.scalar(
            select(func.count(Product.id)).where(
                Product.created_at >= datetime.combine(today, datetime.min.time())
            )
        ) or 0

        # Новые посылки за неделю
        week_ago = datetime.now() - timedelta(days=7)
        week_products = await session.scalar(
            select(func.count(Product.id)).where(Product.created_at >= week_ago)
        ) or 0

    texts = {
        "ru": {
            "title": "📈 Общая статистика системы",
            "total_packages": "Всего посылок",
            "total_users": "Всего пользователей",
            "today": "Добавлено сегодня",
            "week": "Добавлено за неделю",
            "by_status": "Распределение по статусам",
        },
        "tj": {
            "title": "📈 Омори умумии система",
            "total_packages": "Ҳамаи посилкаҳо",
            "total_users": "Ҳамаи корбарон",
            "today": "Имрӯз илова шуда",
            "week": "Ҳама ҳафта илова шуда",
            "by_status": "Ба статус тақсим",
        }
    }

    t = texts.get(language, texts["ru"])
    status_display = STATUS_DISPLAY.get(language, STATUS_DISPLAY["ru"])

    report_text = f"{t['title']}\n\n"
    report_text += f"📊 {t['total_packages']}: {total_products}\n"
    report_text += f"👥 {t['total_users']}: {total_users}\n"
    report_text += f"📅 {t['today']}: {today_products}\n"
    report_text += f"📆 {t['week']}: {week_products}\n\n"
    report_text += f"📊 {t['by_status']}:\n"

    for status, count in status_stats.items():
        display_name = status_display.get(status, status)
        report_text += f"  {display_name}: {count}\n"

    await message.answer(
        report_text,
        reply_markup=get_admin_main_keyboard(role=admin_role, language=language)
    )


@reports_router.message(F.text.in_(["📊 По статусам", "📊 Аз рӯи статус"]))
async def statistics_by_status(message: Message):
    """Статистика по статусам посылок"""
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
        admin_role = settings.get_admin_role(user_id)

        # Детальная статистика по каждому статусу
        status_details = {}
        for status in ProductStatus:
            count = await session.scalar(
                select(func.count(Product.id)).where(Product.status == status.value)
            ) or 0

            avg_value = await session.scalar(
                select(func.avg(Product.total_value_usd)).where(Product.status == status.value)
            ) or 0

            status_details[status.value] = {
                "count": count,
                "avg_value": avg_value
            }

    texts = {
        "ru": {
            "title": "📊 Статистика по статусам",
            "count": "Посылок",
            "avg_price": "Средняя стоимость",
        },
        "tj": {
            "title": "📊 Омори аз рӯи статус",
            "count": "Посилкаҳо",
            "avg_price": "Қимати миёнаи",
        }
    }

    t = texts.get(language, texts["ru"])
    status_display = STATUS_DISPLAY.get(language, STATUS_DISPLAY["ru"])

    report_text = f"{t['title']}\n\n"

    for status, details in status_details.items():
        display_name = status_display.get(status, status)
        report_text += (
            f"{display_name}\n"
            f"  • {t['count']}: {details['count']}\n"
            f"  • {t['avg_price']}: ${details['avg_value']:.2f}\n\n"
        )

    await message.answer(
        report_text,
        reply_markup=get_admin_main_keyboard(role=admin_role, language=language)
    )


@reports_router.message(F.text.in_(["📅 За период", "📅 Дар давраи вақтӣ"]))
async def report_by_period(message: Message, state: FSMContext):
    """Отчет за выбранный период"""
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
        "ru": {
            "title": "📅 Выберите период",
            "today": "📅 Сегодня",
            "week": "📆 На неделю",
            "month": "📊 За месяц",
            "all_time": "⏰ Всё время",
            "back": "🔙 Назад"
        },
        "tj": {
            "title": "📅 Давраи вақтиро интихоб кунед",
            "today": "📅 Имрӯз",
            "week": "📆 Ҳама ҳафта",
            "month": "📊 Дар моҳ",
            "all_time": "⏰ Ҳама вақт",
            "back": "🔙 Бозгашт"
        }
    }

    t = texts.get(language, texts["ru"])

    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    from aiogram.utils.keyboard import ReplyKeyboardBuilder

    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=t["today"]))
    builder.add(KeyboardButton(text=t["week"]))
    builder.add(KeyboardButton(text=t["month"]))
    builder.add(KeyboardButton(text=t["all_time"]))
    builder.row(KeyboardButton(text=t["back"]))

    await message.answer(
        t["title"],
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

    await state.set_state(ReportStates.waiting_for_period)


@reports_router.message(ReportStates.waiting_for_period)
async def process_period_report(message: Message, state: FSMContext):
    """Обработка выбранного периода"""
    if message.text.startswith("🔙"):
        # Возврат в меню отчетов
        user_id = message.from_user.id
        async with async_session_maker() as session:
            user = await session.execute(
                select(User).where(User.telegram_id == user_id)
            )
            user = user.scalar_one_or_none()
            language = user.language if user else "ru"

        texts = {
            "ru": {
                "title": "📊 Отчеты и статистика",
                "description": "Выберите тип отчета:"
            },
            "tj": {
                "title": "📊 Ҳисоботҳо ва омор",
                "description": "Намуди ҳисобот интихоб кунед:"
            }
        }

        t = texts.get(language, texts["ru"])

        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        from aiogram.utils.keyboard import ReplyKeyboardBuilder

        buttons = {
            "ru": {
                "general": "📈 Общая статистика",
                "by_status": "📊 По статусам",
                "by_period": "📅 За период",
                "export": "💾 Экспорт данных",
                "back": "🔙 Назад"
            },
            "tj": {
                "general": "📈 Омори умумӣ",
                "by_status": "📊 Аз рӯи статус",
                "by_period": "📅 Дар давраи вақтӣ",
                "export": "💾 Экспорти маълумот",
                "back": "🔙 Бозгашт"
            }
        }

        b = buttons.get(language, buttons["ru"])

        builder = ReplyKeyboardBuilder()
        builder.add(KeyboardButton(text=b["general"]))
        builder.add(KeyboardButton(text=b["by_status"]))
        builder.add(KeyboardButton(text=b["by_period"]))
        builder.add(KeyboardButton(text=b["export"]))
        builder.row(KeyboardButton(text=b["back"]))

        await message.answer(
            f"{t['title']}\n\n{t['description']}",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )

