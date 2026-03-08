"""
Генерация отчетов для администратора (reply-клавиатура)
"""
import logging
from datetime import datetime, timedelta
from io import BytesIO
import pandas as pd
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select, func, extract

from database.models import Product, User
from database.session import async_session_maker
from keyboards.admin import get_reports_keyboard, get_back_to_admin_keyboard
from config import settings

logger = logging.getLogger(__name__)
reports_router = Router()


@reports_router.message(F.text == "📊 Отчеты")
async def reports_menu(message: Message):
    if not settings.is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещен")
        return

    await message.answer(
        "📊 Отчеты и статистика\n\n"
        "Выберите тип отчета:",
        reply_markup=get_reports_keyboard()
    )


@reports_router.message(F.text == "📦 Доставлено за месяц")
async def monthly_delivered_report(message: Message):
    async with async_session_maker() as session:
        now = datetime.utcnow()
        current_month = now.month
        current_year = now.year

        delivered_count = await session.scalar(
            select(func.count(Product.id)).where(
                Product.status == "DELIVERED",
                extract('month', Product.updated_at) == current_month,
                extract('year', Product.updated_at) == current_year
            )
        ) or 0

        monthly_stats = []
        for i in range(6):
            month_date = now - timedelta(days=30*i)
            month = month_date.month
            year = month_date.year
            count = await session.scalar(
                select(func.count(Product.id)).where(
                    Product.status == "DELIVERED",
                    extract('month', Product.updated_at) == month,
                    extract('year', Product.updated_at) == year
                )
            ) or 0
            monthly_stats.append({
                "period": f"{month:02d}.{year}",
                "delivered": count
            })

        report_text = (
            f"📦 Отчет по доставленным товарам\n\n"
            f"Текущий месяц ({current_month:02d}.{current_year}):\n"
            f"  • Доставлено товаров: {delivered_count}\n\n"
            f"📈 Статистика за последние 6 месяцев:\n"
        )
        for stat in monthly_stats:
            report_text += f"  • {stat['period']}: {stat['delivered']} товаров\n"

        await message.answer(report_text, reply_markup=get_back_to_admin_keyboard())


@reports_router.message(F.text == "📥 Принято за месяц")
async def monthly_received_report(message: Message):
    async with async_session_maker() as session:
        now = datetime.utcnow()
        current_month = now.month
        current_year = now.year

        received_count = await session.scalar(
            select(func.count(Product.id)).where(
                Product.status == "ARRIVED_TJ",
                extract('month', Product.arrival_date) == current_month,
                extract('year', Product.arrival_date) == current_year
            )
        ) or 0

        status_stats = await session.execute(
            select(
                Product.status,
                func.count(Product.id).label('count')
            ).where(
                extract('month', Product.created_at) == current_month,
                extract('year', Product.created_at) == current_year
            ).group_by(Product.status)
        )
        status_stats = status_stats.all()

        avg_data = await session.execute(
            select(
                func.avg(Product.quantity).label('avg_quantity'),
                func.avg(Product.total_value_usd).label('avg_value'),
                func.avg(Product.weight_kg).label('avg_weight')
            ).where(
                extract('month', Product.created_at) == current_month,
                extract('year', Product.created_at) == current_year
            )
        )
        avg = avg_data.first()

        report_text = (
            f"📥 Отчет по принятым товарам\n\n"
            f"Текущий месяц ({current_month:02d}.{current_year}):\n"
            f"  • Принято товаров: {received_count}\n\n"
            f"📊 Распределение по статусам:\n"
        )
        for status, count in status_stats:
            if status:
                report_text += f"  • {status}: {count} товаров\n"

        if avg and avg.avg_quantity:
            report_text += (
                f"\n📊 Средние показатели:\n"
                f"  • Среднее количество: {avg.avg_quantity:.1f} шт.\n"
                f"  • Средняя стоимость: ${avg.avg_value:.2f}\n"
                f"  • Средний вес: {avg.avg_weight:.2f} кг\n"
            )

        await message.answer(report_text, reply_markup=get_back_to_admin_keyboard())


@reports_router.message(F.text == "💰 Финансовый отчет")
async def financial_report(message: Message):
    async with async_session_maker() as session:
        now = datetime.utcnow()
        financial_stats = []

        for i in range(3):
            month_date = now - timedelta(days=30*i)
            month = month_date.month
            year = month_date.year

            stats = await session.execute(
                select(
                    func.sum(Product.total_value_usd).label('total_value'),
                    func.sum(Product.quantity).label('total_quantity'),
                    func.count(Product.id).label('count')
                ).where(
                    extract('month', Product.created_at) == month,
                    extract('year', Product.created_at) == year,
                    Product.total_value_usd.isnot(None)
                )
            )
            stats = stats.first()
            financial_stats.append({
                "period": f"{month:02d}.{year}",
                "total_value": stats.total_value or 0,
                "total_quantity": stats.total_quantity or 0,
                "count": stats.count or 0
            })

        report_text = "💰 Финансовый отчет\n\n"
        for stat in financial_stats:
            avg_value = stat['total_value'] / stat['count'] if stat['count'] > 0 else 0
            report_text += (
                f"📅 Период: {stat['period']}\n"
                f"  • Товаров: {stat['count']} шт.\n"
                f"  • Общая стоимость: ${stat['total_value']:.2f}\n"
                f"  • Средняя стоимость товара: ${avg_value:.2f}\n"
                f"  • Общее количество: {stat['total_quantity']} ед.\n\n"
            )

        total_stats = await session.execute(
            select(
                func.sum(Product.total_value_usd).label('total_all'),
                func.count(Product.id).label('count_all')
            ).where(Product.total_value_usd.isnot(None))
        )
        total = total_stats.first()
        report_text += (
            f"📊 Общая статистика:\n"
            f"  • Всего товаров в базе: {total.count_all}\n"
            f"  • Общая стоимость всех товаров: ${total.total_all or 0:.2f}\n"
        )

        await message.answer(report_text, reply_markup=get_back_to_admin_keyboard())


@reports_router.message(F.text == "👥 Статистика пользователей")
async def user_statistics_report(message: Message):
    async with async_session_maker() as session:
        user_stats = await session.execute(
            select(
                func.count(User.id).label('total_users'),
                func.count(User.phone).label('users_with_phone'),
                func.count(User.full_name).label('users_with_name')
            )
        )
        user_stats = user_stats.first()

        region_stats = await session.execute(
            select(User.region, func.count(User.id).label('count'))
            .where(User.region.isnot(None))
            .group_by(User.region)
        )
        regions = region_stats.all()

        lang_stats = await session.execute(
            select(User.language, func.count(User.id).label('count'))
            .group_by(User.language)
        )
        langs = lang_stats.all()

        report_text = "👥 Статистика пользователей\n\n"
        report_text += f"📊 Общая информация:\n"
        report_text += f"  • Всего пользователей: {user_stats.total_users}\n"
        report_text += f"  • С указанным телефоном: {user_stats.users_with_phone}\n"
        report_text += f"  • С указанным именем: {user_stats.users_with_name}\n\n"

        if regions:
            report_text += "🌍 Распределение по регионам:\n"
            for region, count in regions:
                report_text += f"  • {region or 'Не указан'}: {count}\n"
            report_text += "\n"

        if langs:
            report_text += "🗣️ Распределение по языкам:\n"
            for lang, count in langs:
                lang_name = "Русский" if lang == "ru" else "Таджикский" if lang == "tj" else lang
                report_text += f"  • {lang_name}: {count}\n"

        await message.answer(report_text, reply_markup=get_back_to_admin_keyboard())


@reports_router.message(F.text == "💾 Экспорт в Excel")
async def database_export(message: Message):
    async with async_session_maker() as session:
        products = await session.execute(select(Product))
        products = products.scalars().all()

        if not products:
            await message.answer(
                "❌ В базе данных нет товаров для экспорта",
                reply_markup=get_back_to_admin_keyboard()
            )
            return

        data = []
        for p in products:
            data.append({
                "ID": p.id,
                "Трек-код": p.track_code,
                "Название": p.product_name,
                "Категория": p.product_category,
                "Количество": p.quantity,
                "Цена за ед. ($)": p.unit_price_usd,
                "Общая стоимость ($)": p.total_value_usd,
                "Вес (кг)": p.weight_kg,
                "Статус": p.status.value if p.status else None,
                "Страна отправления": p.country_from,
                "Тип доставки": p.delivery_type,
                "Дата отправки": p.send_date,
                "Дата прибытия": p.arrival_date,
                "Хрупкий": "Да" if p.fragile else "Нет",
                "Батарея": "Да" if p.has_battery else "Нет",
                "Жидкость": "Да" if p.is_liquid else "Нет",
                "Дата создания": p.created_at,
                "Дата обновления": p.updated_at
            })

        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Товары', index=False)
            stats_df = pd.DataFrame({
                'Показатель': ['Всего товаров', 'Средняя стоимость', 'Средний вес', 'Общая стоимость'],
                'Значение': [
                    len(products),
                    df['Общая стоимость ($)'].mean(),
                    df['Вес (кг)'].mean(),
                    df['Общая стоимость ($)'].sum()
                ]
            })
            stats_df.to_excel(writer, sheet_name='Статистика', index=False)

        output.seek(0)
        filename = f"database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        await message.answer_document(
            document=("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", output, filename),
            caption=f"📊 Экспорт базы данных\n"
                    f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                    f"📦 Товаров: {len(products)}",
            reply_markup=get_back_to_admin_keyboard()
        )


@reports_router.message(F.text == "🖥️ Информация о системе")
async def system_info(message: Message):
    import platform
    import psutil

    system_text = "🖥️ Информация о системе\n\n"
    system_text += f"📋 Система:\n"
    system_text += f"  • ОС: {platform.system()} {platform.release()}\n"
    system_text += f"  • Архитектура: {platform.machine()}\n"
    system_text += f"  • Процессор: {platform.processor()}\n\n"

    memory = psutil.virtual_memory()
    system_text += "💾 Память:\n"
    system_text += f"  • Всего: {memory.total / (1024**3):.1f} GB\n"
    system_text += f"  • Использовано: {memory.used / (1024**3):.1f} GB\n"
    system_text += f"  • Свободно: {memory.available / (1024**3):.1f} GB\n"
    system_text += f"  • Использование: {memory.percent}%\n\n"

    disk = psutil.disk_usage('/')
    system_text += "💿 Диск:\n"
    system_text += f"  • Всего: {disk.total / (1024**3):.1f} GB\n"
    system_text += f"  • Использовано: {disk.used / (1024**3):.1f} GB\n"
    system_text += f"  • Свободно: {disk.free / (1024**3):.1f} GB\n"
    system_text += f"  • Использование: {disk.percent}%\n\n"

    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    system_text += "⏰ Время работы:\n"
    system_text += f"  • Запуск системы: {boot_time.strftime('%d.%m.%Y %H:%M')}\n"
    system_text += f"  • Аптайм: {uptime.days} дн., {uptime.seconds//3600} ч.\n"

    await message.answer(system_text, reply_markup=get_back_to_admin_keyboard())