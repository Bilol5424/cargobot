"""
Генерация отчетов для администратора
"""
import logging
from datetime import datetime, timedelta
from io import BytesIO
import pandas as pd
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Product
from database.session import async_session_maker
from keyboards.admin import get_reports_keyboard, get_back_to_admin_keyboard
from config import settings

logger = logging.getLogger(__name__)
reports_router = Router()

@reports_router.callback_query(F.data == "admin_reports")
async def reports_menu(callback: CallbackQuery):
    """Меню отчетов"""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📊 Отчеты и статистика\n\n"
        "Выберите тип отчета:",
        reply_markup=get_reports_keyboard()
    )
    await callback.answer()

@reports_router.callback_query(F.data == "report_monthly_delivered")
async def monthly_delivered_report(callback: CallbackQuery):
    """Отчет по доставленным товарам за месяц"""
    async with async_session_maker() as session:
        # Получаем текущий месяц
        now = datetime.utcnow()
        current_month = now.month
        current_year = now.year
        
        # Статистика доставленных товаров за текущий месяц
        query = select(func.count(Product.id)).where(
            Product.status == "DELIVERED",
            extract('month', Product.updated_at) == current_month,
            extract('year', Product.updated_at) == current_year
        )
        result = await session.execute(query)
        delivered_count = result.scalar() or 0
        
        # Статистика по месяцам за последние 6 месяцев
        monthly_stats = []
        for i in range(6):
            month_date = now - timedelta(days=30*i)
            month = month_date.month
            year = month_date.year
            
            query = select(func.count(Product.id)).where(
                Product.status == "DELIVERED",
                extract('month', Product.updated_at) == month,
                extract('year', Product.updated_at) == year
            )
            result = await session.execute(query)
            count = result.scalar() or 0
            
            monthly_stats.append({
                "period": f"{month:02d}.{year}",
                "delivered": count
            })
        
        # Формируем отчет
        report_text = f"📦 Отчет по доставленным товарам\n\n"
        report_text += f"Текущий месяц ({current_month:02d}.{current_year}):\n"
        report_text += f"  • Доставлено товаров: {delivered_count}\n\n"
        
        report_text += "📈 Статистика за последние 6 месяцев:\n"
        for stat in monthly_stats:
            report_text += f"  • {stat['period']}: {stat['delivered']} товаров\n"
        
        await callback.message.edit_text(
            report_text,
            reply_markup=get_back_to_admin_keyboard()
        )
    
    await callback.answer()

@reports_router.callback_query(F.data == "report_monthly_received")
async def monthly_received_report(callback: CallbackQuery):
    """Отчет по принятым товарам за месяц"""
    async with async_session_maker() as session:
        now = datetime.utcnow()
        current_month = now.month
        current_year = now.year
        
        # Статистика принятых товаров (прибывших в TJ)
        query = select(func.count(Product.id)).where(
            Product.status == "ARRIVED_TJ",
            extract('month', Product.arrival_date) == current_month,
            extract('year', Product.arrival_date) == current_year
        )
        result = await session.execute(query)
        received_count = result.scalar() or 0
        
        # Статистика по статусам за текущий месяц
        status_query = select(
            Product.status,
            func.count(Product.id).label('count')
        ).where(
            extract('month', Product.created_at) == current_month,
            extract('year', Product.created_at) == current_year
        ).group_by(Product.status)
        
        result = await session.execute(status_query)
        status_stats = result.all()
        
        # Формируем отчет
        report_text = f"📥 Отчет по принятым товарам\n\n"
        report_text += f"Текущий месяц ({current_month:02d}.{current_year}):\n"
        report_text += f"  • Принято товаров: {received_count}\n\n"
        
        report_text += "📊 Распределение по статусам:\n"
        for status, count in status_stats:
            if status:
                report_text += f"  • {status}: {count} товаров\n"
        
        # Средние показатели
        avg_query = select(
            func.avg(Product.quantity).label('avg_quantity'),
            func.avg(Product.total_value_usd).label('avg_value'),
            func.avg(Product.weight_kg).label('avg_weight')
        ).where(
            extract('month', Product.created_at) == current_month,
            extract('year', Product.created_at) == current_year
        )
        
        result = await session.execute(avg_query)
        avg_data = result.first()
        
        if avg_data:
            report_text += f"\n📊 Средние показатели:\n"
            report_text += f"  • Среднее количество: {avg_data.avg_quantity:.1f} шт.\n"
            report_text += f"  • Средняя стоимость: ${avg_data.avg_value:.2f}\n"
            report_text += f"  • Средний вес: {avg_data.avg_weight:.2f} кг\n"
        
        await callback.message.edit_text(
            report_text,
            reply_markup=get_back_to_admin_keyboard()
        )
    
    await callback.answer()

@reports_router.callback_query(F.data == "report_database_export")
async def database_export(callback: CallbackQuery):
    """Экспорт базы данных в Excel"""
    async with async_session_maker() as session:
        # Получаем все товары с информацией о пользователях
        query = select(Product)
        result = await session.execute(query)
        products = result.scalars().all()
        
        if not products:
            await callback.message.edit_text(
                "❌ В базе данных нет товаров для экспорта",
                reply_markup=get_back_to_admin_keyboard()
            )
            return
        
        # Создаем DataFrame
        data = []
        for product in products:
            data.append({
                "ID": product.id,
                "Трек-код": product.track_code,
                "Название": product.product_name,
                "Категория": product.product_category,
                "Количество": product.quantity,
                "Цена за ед. ($)": product.unit_price_usd,
                "Общая стоимость ($)": product.total_value_usd,
                "Вес (кг)": product.weight_kg,
                "Статус": product.status,
                "Страна отправления": product.country_from,
                "Тип доставки": product.delivery_type,
                "Дата отправки": product.send_date,
                "Дата прибытия": product.arrival_date,
                "Хрупкий": "Да" if product.fragile else "Нет",
                "Батарея": "Да" if product.has_battery else "Нет",
                "Жидкость": "Да" if product.is_liquid else "Нет",
                "Дата создания": product.created_at,
                "Дата обновления": product.updated_at
            })
        
        df = pd.DataFrame(data)
        
        # Создаем Excel файл в памяти
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Товары', index=False)
            
            # Добавляем лист со статистикой
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
        
        # Отправляем файл
        filename = f"database_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        await callback.message.answer_document(
            document=("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", output, filename),
            caption=f"📊 Экспорт базы данных\n"
                   f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                   f"📦 Товаров: {len(products)}\n"
                   f"💾 Файл: {filename}",
            reply_markup=get_back_to_admin_keyboard()
        )
        
        # Удаляем старое сообщение с меню
        await callback.message.delete()
    
    await callback.answer()

@reports_router.callback_query(F.data == "report_user_statistics")
async def user_statistics_report(callback: CallbackQuery):
    """Статистика по пользователям"""
    async with async_session_maker() as session:
        from database.models import User
        
        # Общая статистика пользователей
        user_query = select(
            func.count(User.id).label('total_users'),
            func.count(User.phone.isnot(None)).label('users_with_phone'),
            func.count(User.full_name.isnot(None)).label('users_with_name')
        )
        result = await session.execute(user_query)
        user_stats = result.first()
        
        # Статистика по регионам
        region_query = select(
            User.region,
            func.count(User.id).label('count')
        ).where(User.region.isnot(None)).group_by(User.region)
        
        result = await session.execute(region_query)
        region_stats = result.all()
        
        # Статистика по языкам
        lang_query = select(
            User.language,
            func.count(User.id).label('count')
        ).group_by(User.language)
        
        result = await session.execute(lang_query)
        lang_stats = result.all()
        
        # Формируем отчет
        report_text = "👥 Статистика пользователей\n\n"
        report_text += f"📊 Общая информация:\n"
        report_text += f"  • Всего пользователей: {user_stats.total_users}\n"
        report_text += f"  • С указанным телефоном: {user_stats.users_with_phone}\n"
        report_text += f"  • С указанным именем: {user_stats.users_with_name}\n\n"
        
        if region_stats:
            report_text += "🌍 Распределение по регионам:\n"
            for region, count in region_stats:
                report_text += f"  • {region or 'Не указан'}: {count}\n"
            report_text += "\n"
        
        if lang_stats:
            report_text += "🗣️ Распределение по языкам:\n"
            for lang, count in lang_stats:
                lang_name = "Русский" if lang == "ru" else "Таджикский" if lang == "tj" else lang
                report_text += f"  • {lang_name}: {count}\n"
        
        await callback.message.edit_text(
            report_text,
            reply_markup=get_back_to_admin_keyboard()
        )
    
    await callback.answer()

@reports_router.callback_query(F.data == "report_financial")
async def financial_report(callback: CallbackQuery):
    """Финансовый отчет"""
    async with async_session_maker() as session:
        # Финансовая статистика по месяцам
        now = datetime.utcnow()
        financial_stats = []
        
        for i in range(3):  # Последние 3 месяца
            month_date = now - timedelta(days=30*i)
            month = month_date.month
            year = month_date.year
            
            # Товары созданные в этом месяце
            query = select(
                func.sum(Product.total_value_usd).label('total_value'),
                func.sum(Product.quantity).label('total_quantity'),
                func.count(Product.id).label('count')
            ).where(
                extract('month', Product.created_at) == month,
                extract('year', Product.created_at) == year,
                Product.total_value_usd.isnot(None)
            )
            
            result = await session.execute(query)
            stats = result.first()
            
            financial_stats.append({
                "period": f"{month:02d}.{year}",
                "total_value": stats.total_value or 0,
                "total_quantity": stats.total_quantity or 0,
                "count": stats.count or 0
            })
        
        # Формируем отчет
        report_text = "💰 Финансовый отчет\n\n"
        
        for stat in financial_stats:
            avg_value = stat['total_value'] / stat['count'] if stat['count'] > 0 else 0
            report_text += f"📅 Период: {stat['period']}\n"
            report_text += f"  • Товаров: {stat['count']} шт.\n"
            report_text += f"  • Общая стоимость: ${stat['total_value']:.2f}\n"
            report_text += f"  • Средняя стоимость товара: ${avg_value:.2f}\n"
            report_text += f"  • Общее количество: {stat['total_quantity']} ед.\n\n"
        
        # Общая статистика
        total_query = select(
            func.sum(Product.total_value_usd).label('total_all'),
            func.count(Product.id).label('count_all')
        ).where(Product.total_value_usd.isnot(None))
        
        result = await session.execute(total_query)
        total_stats = result.first()
        
        report_text += "📊 Общая статистика:\n"
        report_text += f"  • Всего товаров в базе: {total_stats.count_all}\n"
        report_text += f"  • Общая стоимость всех товаров: ${total_stats.total_all or 0:.2f}\n"
        
        await callback.message.edit_text(
            report_text,
            reply_markup=get_back_to_admin_keyboard()
        )
    
    await callback.answer()