"""
Вспомогательные функции для работы с товарами
"""
from datetime import datetime
from database.models import ProductCategory
from keyboards.client import get_track_codes_keyboard

async def track_codes_menu_back(message, state):
    """Возврат в меню трек-кодов"""
    async for db in get_db():
        user_repo = UserRepository(db)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        texts = {
            "ru": "📦 <b>Трек-коды</b>\n\nВыберите действие:",
            "tj": "📦 <b>Рамзҳои тамошобин</b>\n\nАмалро интихоб кунед:"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_track_codes_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.track_codes_menu)

def get_status_text(status: str, language: str = "ru") -> str:
    """Получение текста статуса на нужном языке"""
    status_texts = {
        "ru": {
            "created": "Создан",
            "china_warehouse": "На складе в Китае",
            "in_transit": "В пути",
            "tajikistan_warehouse": "На складе в Таджикистане",
            "delivered": "Доставлен",
            "completed": "Завершен"
        },
        "tj": {
            "created": "Сохта шудааст",
            "china_warehouse": "Дар анбори Чин",
            "in_transit": "Дар роҳ",
            "tajikistan_warehouse": "Дар анбори Тоҷикистон",
            "delivered": "Расонида шуд",
            "completed": "Анҷом ёфт"
        }
    }
    
    return status_texts.get(language, status_texts["ru"]).get(status, status)

async def show_product_success_message(
    message, state, product, user, track_code, product_name, product_category,
    quantity, unit_price, total_value, weight, length, width, height,
    fragile, has_battery, is_liquid, product_description
):
    """Показать сообщение об успешном добавлении товара"""
    from keyboards.client import get_track_codes_keyboard
    
    # Получаем русское название категории для отображения
    category_names_ru = {
        ProductCategory.ELECTRONICS: "Электроника",
        ProductCategory.CLOTHING: "Одежда",
        ProductCategory.SHOES: "Обувь",
        ProductCategory.HOME_APPLIANCES: "Бытовая техника",
        ProductCategory.BEAUTY: "Косметика",
        ProductCategory.TOYS: "Игрушки",
        ProductCategory.AUTOMOTIVE: "Автозапчасти",
        ProductCategory.SPORTS: "Спорттовары",
        ProductCategory.OTHER: "Другое"
    }
    
    category_names_tj = {
        ProductCategory.ELECTRONICS: "Электроника",
        ProductCategory.CLOTHING: "Либос",
        ProductCategory.SHOES: "Пойафзол",
        ProductCategory.HOME_APPLIANCES: "Асбобҳои хонагӣ",
        ProductCategory.BEAUTY: "Косметика",
        ProductCategory.TOYS: "Бозичаҳо",
        ProductCategory.AUTOMOTIVE: "Қисмҳои автомобил",
        ProductCategory.SPORTS: "Ашёҳои варзишӣ",
        ProductCategory.OTHER: "Дигар"
    }
    
    category_name = category_names_ru[product_category] if user.language == "ru" else category_names_tj[product_category]
    
    # Формируем информацию о добавленном товаре
    dimensions_text = ""
    if length and width and height:
        dimensions_text = f"📏 Габариты: {length}×{width}×{height} см\n" if user.language == "ru" else f"📏 Андозаҳо: {length}×{width}×{height} см\n"
    
    special_text = ""
    if fragile:
        special_text = "⚠️ Хрупкий\n" if user.language == "ru" else "⚠️ Нозук\n"
    if has_battery:
        special_text += "🔋 С батареей\n" if user.language == "ru" else "🔋 Бо батарея\n"
    if is_liquid:
        special_text += "💧 Жидкость\n" if user.language == "ru" else "💧 Моеъ\n"
    
    if special_text == "":
        special_text = "✅ Без особых свойств\n" if user.language == "ru" else "✅ Бе хусусияти махсус\n"
    
    texts = {
        "ru": f"""✅ <b>Товар успешно добавлен!</b>

📦 <b>Информация о товаре:</b>
🎯 Трек-код: <code>{track_code}</code>
🏷️ Название: {product_name}
📂 Категория: {category_name}
📝 Описание: {product_description or 'Не указано'}
🔢 Количество: {quantity} шт.
💰 Цена за единицу: ${unit_price:.2f}
💵 Общая стоимость: ${total_value:.2f}
⚖️ Вес: {weight:.2f} кг
{dimensions_text}{special_text}
📅 Дата добавления: {product.created_at.strftime('%d.%m.%Y %H:%M')}

<i>Администраторы теперь видят полную информацию о вашем товаре.</i>""",
        "tj": f"""✅ <b>Маҳсулот бомуваффақият илова карда шуд!</b>

📦 <b>Маълумот дар бораи маҳсулот:</b>
🎯 Рамзи тамошобин: <code>{track_code}</code>
🏷️ Ном: {product_name}
📂 Гурӯҳ: {category_name}
📝 Тавсиф: {product_description or 'Муайян нашудааст'}
🔢 Миқдор: {quantity} дона
💰 Нарх барои як воҳид: ${unit_price:.2f}
💵 Арзиши умумӣ: ${total_value:.2f}
⚖️ Вазн: {weight:.2f} кг
{dimensions_text}{special_text}
📅 Сании илова: {product.created_at.strftime('%d.%m.%Y %H:%M')}

<i>Администраторҳо акнун маълумоти пурра дар бораи маҳсулоти шуморо мебинанд.</i>"""
    }
    
    await message.answer(
        texts[user.language],
        reply_markup=get_track_codes_keyboard(user.language),
        parse_mode="HTML"
    )
    await state.set_state(ClientState.track_codes_menu)