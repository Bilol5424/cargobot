"""
Детальная информация о товаре
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from database.session import get_db
from database.repository import UserRepository, ProductRepository
from utils.states import ClientState
from .utils import get_status_text

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data.startswith("view_product_"))
async def view_product_details(callback: CallbackQuery, state: FSMContext):
    """Просмотр детальной информации о товаре"""
    product_id = int(callback.data.split("_")[2])
    
    async for session in get_db():
        product_repo = ProductRepository(session)
        user_repo = UserRepository(session)
        
        user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
        product = await session.get(product_repo.model, product_id)
        
        if not product:
            await callback.answer("❌ Товар не найден")
            return
        
        # Проверяем, принадлежит ли товар пользователю
        if product.user_id != user.id:
            await callback.answer("❌ Нет доступа к этому товару")
            return
        
        # Формируем детальную информацию
        status_text = get_status_text(product.status.value, user.language)
        
        # Перевод категории
        category_names_ru = {
            "electronics": "Электроника",
            "clothing": "Одежда",
            "shoes": "Обувь",
            "home_appliances": "Бытовая техника",
            "beauty": "Косметика",
            "toys": "Игрушки",
            "automotive": "Автозапчасти",
            "sports": "Спорттовары",
            "other": "Другое"
        }
        
        category_names_tj = {
            "electronics": "Электроника",
            "clothing": "Либос",
            "shoes": "Пойафзол",
            "home_appliances": "Асбобҳои хонагӣ",
            "beauty": "Косметика",
            "toys": "Бозичаҳо",
            "automotive": "Қисмҳои автомобил",
            "sports": "Ашёҳои варзишӣ",
            "other": "Дигар"
        }
        
        category_name = category_names_ru.get(product.product_category, product.product_category) if user.language == "ru" else category_names_tj.get(product.product_category, product.product_category)
        
        # Описание
        description = product.product_description or ("Не указано" if user.language == "ru" else "Муайян нашудааст")
        
        # Габариты
        dimensions = ""
        if product.length_cm and product.width_cm and product.height_cm:
            dimensions = f"{product.length_cm}×{product.width_cm}×{product.height_cm} см"
        else:
            dimensions = "Не указаны" if user.language == "ru" else "Муайян нашудааст"
        
        # Особые свойства
        special_properties = []
        if product.fragile:
            special_properties.append("Хрупкий" if user.language == "ru" else "Нозук")
        if product.has_battery:
            special_properties.append("С батареей" if user.language == "ru" else "Бо батарея")
        if product.is_liquid:
            special_properties.append("Жидкость" if user.language == "ru" else "Моеъ")
        
        special_text = ", ".join(special_properties) if special_properties else ("Нет" if user.language == "ru" else "Не")
        
        text = {
            "ru": f"""📦 <b>Детальная информация о товаре</b>

🎯 <b>Трек-код:</b> <code>{product.track_code}</code>
🏷️ <b>Название:</b> {product.product_name or 'Не указано'}
📂 <b>Категория:</b> {category_name}
📝 <b>Описание:</b> {description}
📍 <b>Статус:</b> {status_text}

🔢 <b>Количество:</b> {product.quantity or 1} шт.
💰 <b>Цена за единицу:</b> ${product.unit_price_usd:.2f} USD
💵 <b>Общая стоимость:</b> ${product.total_value_usd:.2f} USD
⚖️ <b>Вес:</b> {product.weight_kg:.2f} кг
📏 <b>Габариты:</b> {dimensions}

⚠️ <b>Особые свойства:</b> {special_text}

🏬 <b>Страна отправления:</b> {product.country_from or 'Не указана'}
🚚 <b>Тип доставки:</b> {product.delivery_type or 'Не указан'}

📅 <b>Дата отправки:</b> {product.send_date.strftime('%d.%m.%Y') if product.send_date else 'Не указана'}
📅 <b>Ожидаемая доставка:</b> {product.expected_delivery_date.strftime('%d.%m.%Y') if product.expected_delivery_date else 'Не указана'}

📅 <b>Дата добавления:</b> {product.created_at.strftime('%d.%m.%Y %H:%M')}
🆔 <b>ID товара:</b> {product.id}""",
            "tj": f"""📦 <b>Маълумоти тафсилотӣ оид ба маҳсулот</b>

🎯 <b>Рамзи тамошобин:</b> <code>{product.track_code}</code>
🏷️ <b>Ном:</b> {product.product_name or 'Муайян нашудааст'}
📂 <b>Гурӯҳ:</b> {category_name}
📝 <b>Тавсиф:</b> {description}
📍 <b>Статус:</b> {status_text}

🔢 <b>Миқдор:</b> {product.quantity or 1} дона
💰 <b>Нарх барои як воҳид:</b> ${product.unit_price_usd:.2f} USD
💵 <b>Арзиши умумӣ:</b> ${product.total_value_usd:.2f} USD
⚖️ <b>Вазн:</b> {product.weight_kg:.2f} кг
📏 <b>Андозаҳо:</b> {dimensions}

⚠️ <b>Хусусиятҳои махсус:</b> {special_text}

🏬 <b>Кишвари фиристод:</b> {product.country_from or 'Муайян нашудааст'}
🚚 <b>Навъи расонидан:</b> {product.delivery_type or 'Муайян нашудааст'}

📅 <b>Санаи фиристод:</b> {product.send_date.strftime('%d.%m.%Y') if product.send_date else 'Муайян нашудааст'}
📅 <b>Расониидани интизоршаванда:</b> {product.expected_delivery_date.strftime('%d.%m.%Y') if product.expected_delivery_date else 'Муайян нашудааст'}

📅 <b>Сании илова:</b> {product.created_at.strftime('%d.%m.%Y %H:%M')}
🆔 <b>ID маҳсулот:</b> {product.id}"""
        }
        
        # Кнопки управления
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = [
            [
                InlineKeyboardButton(
                    text="🔙 К списку" if user.language == "ru" else "🔙 Ба рӯйхат",
                    callback_data="back_to_list"
                )
            ]
        ]
        
        # Если товар еще не отправлен, можно предложить редактирование
        from database.models import ProductStatus
        if product.status in [ProductStatus.CREATED, ProductStatus.CHINA_WAREHOUSE]:
            keyboard[0].append(
                InlineKeyboardButton(
                    text="✏️ Редактировать" if user.language == "ru" else "✏️ Таҳрир кардан",
                    callback_data=f"edit_product_{product.id}"
                )
            )
        
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        await callback.message.edit_text(
            text[user.language],
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        await callback.answer()

@router.callback_query(F.data == "back_to_list")
async def back_to_products_list(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку товаров"""
    from .view_products import my_products_list
    await my_products_list(callback.message, state)
    await callback.answer()