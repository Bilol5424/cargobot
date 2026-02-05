from sqlalchemy import select
"""
Редактирование товара
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.session import get_db
from database.repository import UserRepository, ProductRepository
from keyboards.client import get_back_cancel_keyboard, get_track_codes_keyboard
from keyboards.products import get_edit_product_keyboard
from utils.states import ClientState
from .utils import track_codes_menu_back

logger = logging.getLogger(__name__)
router = Router()

@router.message(ClientState.track_codes_menu, F.text.contains("Изменить товар"))
@router.message(ClientState.track_codes_menu, F.text.contains("Тағйир додани маҳсулот"))
async def edit_product_start(message: Message, state: FSMContext):
    """Начало редактирования товара"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        texts = {
            "ru": "✏️ <b>Изменение товара</b>\n\n"
                  "Введите трек-код товара, который хотите изменить:",
            "tj": "✏️ <b>Тағйир додани маҳсулот</b>\n\n"
                  "Рамзи тамошобини маҳсулотро ворид кунед, ки мехоҳед тағйир диҳед:"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.edit_product_start)

@router.message(ClientState.edit_product_start)
async def edit_product_select(message: Message, state: FSMContext):
    """Выбор товара для редактирования"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт"]:
        await track_codes_menu_back(message, state)
        return
    
    track_code = message.text.strip()
    
    async for session in get_db():
        user_repo = UserRepository(session)
        product_repo = ProductRepository(session)
        
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        product = await product_repo.get_product_by_track_code(track_code)
        
        if not product:
            texts = {
                "ru": f"❌ Товар с трек-кодом {track_code} не найден",
                "tj": f"❌ Маҳсулот бо рамзи тамошобин {track_code} ёфт нашуд"
            }
            await message.answer(texts[user.language])
            return
        
        # Проверяем, принадлежит ли товар пользователю
        if product.user_id != user.id:
            texts = {
                "ru": "❌ Этот товар не принадлежит вам",
                "tj": "❌ Ин маҳсулот ба шумо тааллуқ надорад"
            }
            await message.answer(texts[user.language])
            return
        
        # Проверяем, можно ли редактировать товар
        from database.models import ProductStatus
        if product.status not in [ProductStatus.CREATED, ProductStatus.CHINA_WAREHOUSE]:
            texts = {
                "ru": "⚠️ Этот товар уже отправлен. Вы можете изменить только название и описание.",
                "tj": "⚠️ Ин маҳсулот аллакай фиристода шудааст. Шумо метавонед танҳо ном ва тавсифро тағйир диҳед."
            }
            await message.answer(texts[user.language])
        
        # Сохраняем данные товара
        await state.update_data(
            edit_track_code=track_code,
            edit_product_id=product.id
        )
        
        # Показываем информацию о товаре
        from .utils import get_status_text
        
        status_text = get_status_text(product.status.value, user.language)
        
        texts = {
            "ru": f"""✏️ <b>Редактирование товара</b>

🎯 Трек-код: <code>{track_code}</code>
🏷️ Название: {product.product_name or 'Не указано'}
📝 Описание: {product.product_description or 'Не указано'}
📍 Статус: {status_text}

Что вы хотите изменить?""",
            "tj": f"""✏️ <b>Таҳрир кардани маҳсулот</b>

🎯 Рамзи тамошобин: <code>{track_code}</code>
🏷️ Ном: {product.product_name or 'Муайян нашудааст'}
📝 Тавсиф: {product.product_description or 'Муайян нашудааст'}
📍 Статус: {status_text}

Шумо чӣ мехоҳед тағйир диҳед?"""
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_edit_product_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.edit_product_menu)

@router.message(ClientState.edit_product_menu)
async def edit_product_menu_handler(message: Message, state: FSMContext):
    """Обработка выбора в меню редактирования"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if message.text in ["⬅️ Назад", "⬅️ Бозгашт"]:
            await track_codes_menu_back(message, state)
            return
        
        texts = {
            "ru": {
                "edit_name": "📝 Изменить название",
                "edit_desc": "📝 Изменить описание",
                "edit_quantity": "🔢 Изменить количество",
                "edit_price": "💰 Изменить цену",
                "edit_weight": "⚖️ Изменить вес",
                "edit_category": "🏷️ Изменить категорию",
                "back": "⬅️ Назад"
            },
            "tj": {
                "edit_name": "📝 Тағйир додани ном",
                "edit_desc": "📝 Тағйир додани тавсиф",
                "edit_quantity": "🔢 Тағйир додани миқдор",
                "edit_price": "💰 Тағйир додани нарх",
                "edit_weight": "⚖️ Тағйир додани вазн",
                "edit_category": "🏷️ Тағйир додани гурӯҳ",
                "back": "⬅️ Бозгашт"
            }
        }
        
        t = texts[user.language]
        
        if message.text == t["edit_name"]:
            texts = {
                "ru": "Введите новое название товара:",
                "tj": "Номи нави маҳсулотро ворид кунед:"
            }
            await message.answer(
                texts[user.language],
                reply_markup=get_back_cancel_keyboard(user.language)
            )
            await state.set_state(ClientState.edit_product_name)
            
        elif message.text == t["edit_desc"]:
            texts = {
                "ru": "Введите новое описание товара:",
                "tj": "Тавсифи нави маҳсулотро ворид кунед:"
            }
            await message.answer(
                texts[user.language],
                reply_markup=get_back_cancel_keyboard(user.language)
            )
            await state.set_state(ClientState.edit_product_desc)
        
        elif message.text == t["edit_quantity"]:
            texts = {
                "ru": "Введите новое количество товара:",
                "tj": "Миқдори нави маҳсулотро ворид кунед:"
            }
            await message.answer(
                texts[user.language],
                reply_markup=get_back_cancel_keyboard(user.language)
            )
            await state.set_state(ClientState.edit_product_quantity)
        
        elif message.text == t["edit_price"]:
            texts = {
                "ru": "Введите новую цену за единицу (в USD):",
                "tj": "Нархи нави барои як воҳидро ворид кунед (дар USD):"
            }
            await message.answer(
                texts[user.language],
                reply_markup=get_back_cancel_keyboard(user.language)
            )
            await state.set_state(ClientState.edit_product_price)
        
        elif message.text == t["edit_weight"]:
            texts = {
                "ru": "Введите новый вес товара (в кг):",
                "tj": "Вазни нави маҳсулотро ворид кунед (дар кг):"
            }
            await message.answer(
                texts[user.language],
                reply_markup=get_back_cancel_keyboard(user.language)
            )
            await state.set_state(ClientState.edit_product_weight)
        
        elif message.text == t["edit_category"]:
            from keyboards.products import get_product_categories_keyboard
            texts = {
                "ru": "Выберите новую категорию товара:",
                "tj": "Гурӯҳи нави маҳсулотро интихоб кунед:"
            }
            await message.answer(
                texts[user.language],
                reply_markup=get_product_categories_keyboard(user.language)
            )
            await state.set_state(ClientState.edit_product_category)
        
        else:
            await edit_product_select(message, state)

@router.message(ClientState.edit_product_name)
async def edit_product_name_handler(message: Message, state: FSMContext):
    """Изменение названия товара"""
    await _edit_product_field(message, state, "product_name", message.text)

@router.message(ClientState.edit_product_desc)
async def edit_product_desc_handler(message: Message, state: FSMContext):
    """Изменение описания товара"""
    await _edit_product_field(message, state, "product_description", message.text)

@router.message(ClientState.edit_product_quantity)
async def edit_product_quantity_handler(message: Message, state: FSMContext):
    """Изменение количества товара"""
    try:
        quantity = int(message.text)
        if quantity <= 0:
            raise ValueError
        await _edit_product_field(message, state, "quantity", quantity)
    except ValueError:
        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(message.from_user.id)
            
            texts = {
                "ru": "❌ Пожалуйста, введите целое положительное число",
                "tj": "❌ Лутфан, рақами бутуни мусбат ворид кунед"
            }
            await message.answer(texts[user.language])

@router.message(ClientState.edit_product_price)
async def edit_product_price_handler(message: Message, state: FSMContext):
    """Изменение цены товара"""
    try:
        price = float(message.text.replace(",", "."))
        if price < 0:
            raise ValueError
        
        data = await state.get_data()
        quantity = data.get('quantity', 1)
        total_value = price * quantity
        
        # Обновляем и цену и общую стоимость
        async for session in get_db():
            product_repo = ProductRepository(session)
            await product_repo.update_product(
                data['edit_product_id'],
                unit_price_usd=price,
                total_value_usd=total_value
            )
        
        await _show_edit_success(message, state)
    except ValueError:
        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(message.from_user.id)
            
            texts = {
                "ru": "❌ Пожалуйста, введите число (например: 50, 99.99)",
                "tj": "❌ Лутфан, рақам ворид кунед (масалан: 50, 99.99)"
            }
            await message.answer(texts[user.language])

async def _edit_product_field(message: Message, state: FSMContext, field: str, value):
    """Общая функция для изменения поля товара"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт"]:
        await edit_product_select(message, state)
        return
    
    data = await state.get_data()
    
    async for session in get_db():
        product_repo = ProductRepository(session)
        await product_repo.update_product(data['edit_product_id'], **{field: value})
    
    await _show_edit_success(message, state)

async def _show_edit_success(message: Message, state: FSMContext):
    """Показать сообщение об успешном изменении"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        data = await state.get_data()
        track_code = data.get('edit_track_code')
        
        texts = {
            "ru": f"✅ Товар с трек-кодом <code>{track_code}</code> успешно обновлен!",
            "tj": f"✅ Маҳсулот бо рамзи тамошобин <code>{track_code}</code> бомуваффақият навсозӣ шуд!"
        }
        
        await message.answer(
            texts[user.language],
            parse_mode="HTML"
        )
        
        # Возвращаемся в меню редактирования
        await edit_product_select(message, state)