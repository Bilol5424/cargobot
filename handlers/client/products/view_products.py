"""
Просмотр товаров с пагинацией
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.session import get_db
from database.repository import UserRepository, ProductRepository
from utils.states import ClientState
from .utils import get_status_text

logger = logging.getLogger(__name__)
router = Router()

@router.message(ClientState.track_codes_menu, F.text.contains("Мои трек-коды"))
@router.message(ClientState.track_codes_menu, F.text.contains("Рамзҳои тамошобини ман"))
async def my_products_list(message: Message, state: FSMContext):
    """Показать товары пользователя с пагинацией"""
    async for session in get_db():
        user_repo = UserRepository(session)
        product_repo = ProductRepository(session)
        
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        products = await product_repo.get_user_products(user.id)
        
        if not products:
            texts = {
                "ru": "❗ У вас пока нет добавленных товаров",
                "tj": "❗ Шумо то ҳол маҳсулоти иловашуда надоред"
            }
            await message.answer(texts[user.language])
            return
        
        # Получаем текущую страницу из состояния
        state_data = await state.get_data()
        current_page = state_data.get('products_page', 1)
        page_size = 5  # 5 товаров на страницу
        
        # Вычисляем общее количество страниц
        total_pages = (len(products) + page_size - 1) // page_size
        
        # Ограничиваем текущую страницу
        current_page = max(1, min(current_page, total_pages))
        
        # Получаем товары для текущей страницы
        start_idx = (current_page - 1) * page_size
        end_idx = min(start_idx + page_size, len(products))
        products_to_show = products[start_idx:end_idx]
        
        # Формируем сообщение с пагинацией
        text = f"📦 <b>Ваши товары (страница {current_page}/{total_pages}):</b>\n\n" if user.language == "ru" else f"📦 <b>Маҳсулотҳои шумо (саҳифа {current_page}/{total_pages}):</b>\n\n"
        
        for i, product in enumerate(products_to_show, start_idx + 1):
            status_text = get_status_text(product.status.value, user.language)
            
            # Добавляем базовую информацию о товаре
            product_name = product.product_name or "Без названия"
            if user.language == "tj":
                product_name = product.product_name or "Беном"
            
            text += f"<b>{i}.</b> <code>{product.track_code}</code>\n"
            text += f"   🏷️ {product_name}\n"
            text += f"   📍 Статус: {status_text}\n"
            
            # Добавляем стоимость, если есть
            if product.total_value_usd and product.total_value_usd > 0:
                text += f"   💰 Стоимость: ${product.total_value_usd:.2f}\n" if user.language == "ru" else f"   💰 Арзиш: ${product.total_value_usd:.2f}\n"
            
            # Добавляем дату добавления
            text += f"   📅 Добавлен: {product.created_at.strftime('%d.%m.%Y')}\n"
            
            if i < end_idx:
                text += "\n"
        
        # Сохраняем текущую страницу в состоянии
        await state.update_data(products_page=current_page)
        
        # Создаем клавиатуру пагинации
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = []
        
        if total_pages > 1:
            if current_page > 1:
                keyboard.append(
                    InlineKeyboardButton(
                        text="◀️ Назад" if user.language == "ru" else "◀️ Бозгашт",
                        callback_data=f"prev_page_{current_page-1}"
                    )
                )
            
            if current_page < total_pages:
                keyboard.append(
                    InlineKeyboardButton(
                        text="Вперед ▶️" if user.language == "ru" else "Оёд ▶️",
                        callback_data=f"next_page_{current_page+1}"
                    )
                )
        
        # Кнопка просмотра деталей
        if len(products_to_show) == 1:
            product = products_to_show[0]
            keyboard.append(
                InlineKeyboardButton(
                    text="🔍 Подробнее" if user.language == "ru" else "🔍 Тафсилот",
                    callback_data=f"view_product_{product.id}"
                )
            )
        
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[keyboard]) if keyboard else None
        
        await message.answer(
            text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

from aiogram.types import CallbackQuery

@router.callback_query(F.data.startswith("prev_page_"))
async def prev_page(callback: CallbackQuery, state: FSMContext):
    """Переход на предыдущую страницу"""
    page_num = int(callback.data.split("_")[2])
    await state.update_data(products_page=page_num)
    
    # Повторно вызываем функцию отображения товаров
    await my_products_list(callback.message, state)
    await callback.answer()

@router.callback_query(F.data.startswith("next_page_"))
async def next_page(callback: CallbackQuery, state: FSMContext):
    """Переход на следующую страницу"""
    page_num = int(callback.data.split("_")[2])
    await state.update_data(products_page=page_num)
    
    # Повторно вызываем функцию отображения товаров
    await my_products_list(callback.message, state)
    await callback.answer()