import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.session import get_db
from database.repository import ProductRepository
from keyboards.admin import get_admin_main_menu
from utils.states import AdminChinaState, AdminTajikistanState

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text.regexp(r'^[A-Z0-9]{8,20}$'))
async def check_track_code_by_admin(message: Message, state: FSMContext):
    """Проверка трек-кода админом (автоматически при вводе трек-кода)"""
    track_code = message.text.strip()
    
    async for session in get_db():
        product_repo = ProductRepository(session)
        detailed_info = await product_repo.get_detailed_product_info(track_code)
        
        if not detailed_info:
            await message.answer(f"❌ Товар с трек-кодом {track_code} не найден.")
            return
        
        product = detailed_info["product"]
        user = detailed_info["user"]
        product_info = detailed_info["product_info"]
        user_info = detailed_info["user_info"]
        
        # Формируем информацию о товаре
        category_text = product_info["category"] or "Не указана"
        description_text = product_info["description"] or "Не указано"
        dimensions_text = product_info["dimensions"] or "Не указаны"
        
        special_properties = []
        if product_info["fragile"]:
            special_properties.append("⚠️ Хрупкий")
        if product_info["has_battery"]:
            special_properties.append("🔋 С батареей")
        if product_info["is_liquid"]:
            special_properties.append("💧 Жидкость")
        special_text = "\n".join(special_properties) if special_properties else "Нет особых свойств"
        
        text = f"""📦 <b>ДЕТАЛЬНАЯ ИНФОРМАЦИЯ О ТОВАРЕ</b>

🎯 <b>Трек-код:</b> <code>{track_code}</code>

👤 <b>Информация о клиенте:</b>
├ Имя: {user_info["name"] or "Не указано"}
├ Телефон: {user_info["phone"] or "Не указан"}
├ Регион: {user_info["region"] or "Не указан"}
└ Telegram ID: {user_info["telegram_id"]}

🏷️ <b>Информация о товаре:</b>
├ Название: {product_info["name"] or "Не указано"}
├ Категория: {category_text}
├ Описание: {description_text}
├ Количество: {product_info["quantity"]} шт.
├ Цена за единицу: ${product_info["unit_price"]:.2f}
├ Общая стоимость: ${product_info["total_value"]:.2f}
├ Вес: {product_info["weight"]:.2f} кг
├ Габариты: {dimensions_text}
└ Особые свойства: {special_text}

📊 <b>Статус доставки:</b>
├ Текущий статус: {product.status.value}
├ Страна отправления: {product.country_from or "Не указана"}
└ Дата создания: {product.created_at.strftime('%d.%m.%Y %H:%M')}"""
        
        await message.answer(text, parse_mode="HTML")
        
        # Возвращаем админа в его меню
        current_state = await state.get_state()
        if current_state in [AdminChinaState.main_menu, AdminTajikistanState.main_menu]:
            from keyboards.admin import get_admin_main_menu
            await message.answer(
                "Вернуться в меню:",
                reply_markup=get_admin_main_menu("admin_cn" if "china" in str(current_state) else "admin_tj")
            )

@router.message(F.text.contains("🔍 Проверить товар"))
async def check_product_menu(message: Message, state: FSMContext):
    """Меню проверки товара для админов"""
    text = """🔍 <b>Проверка товара</b>

Для просмотра детальной информации о товаре просто введите его трек-код.

Администраторы видят:
• Полную информацию о товаре
• Данные клиента
• Статус доставки
• Стоимость и характеристики

Просто отправьте трек-код в чат."""
    
    await message.answer(text, parse_mode="HTML")