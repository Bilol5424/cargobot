"""
Добавление нового товара (8 шагов)
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.session import get_db
from database.repository import UserRepository, ProductRepository
from database.models import ProductCategory
from keyboards.client import get_back_cancel_keyboard
from keyboards.products import get_product_categories_keyboard, get_special_info_keyboard
from utils.states import ClientState
from .utils import track_codes_menu_back, get_status_text

logger = logging.getLogger(__name__)
router = Router()

# ========== ДОБАВЛЕНИЕ ТОВАРА С ИНФОРМАЦИЕЙ ==========

@router.message(ClientState.track_codes_menu, F.text.contains("Добавить трек-код"))
@router.message(ClientState.track_codes_menu, F.text.contains("Илова кардани рамзи тамошобин"))
async def add_track_code_start(message: Message, state: FSMContext):
    """Начало добавления трек-кода"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        texts = {
            "ru": "📦 <b>Добавление нового товара</b>\n\n"
                  "Введите трек-код товара:",
            "tj": "📦 <b>Илова кардани маҳсулоти нав</b>\n\n"
                  "Рамзи тамошобини маҳсулотро ворид кунед:"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.add_track_code)
# В существующий файл добавляем:

@router.message(ClientState.product_special_info)
async def process_product_special_info(message: Message, state: FSMContext):
    """Обработка выбора особых свойств и сохранение товара"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт"]:
        await product_dimensions_back(message, state)
        return
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        # Генерация трек-кода
        from services.track_code import TrackCodeGenerator
        data = await state.get_data()
        
        # Определяем категорию для генерации трек-кода
        category = data.get('product_category')
        if category:
            category_str = category.value
        else:
            category_str = "other"
        
        track_code = TrackCodeGenerator.generate_track_code(
            user_id=message.from_user.id,
            product_type=category_str
        )
        
        # Сохраняем трек-код
        await state.update_data(track_code=track_code)
        
        # Продолжаем сохранение товара...
        
@router.message(ClientState.add_track_code)
async def process_track_code(message: Message, state: FSMContext):
    """Обработка ввода трек-кода и переход к сбору информации"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт"]:
        await track_codes_menu_back(message, state)
        return
    
    async for session in get_db():
        user_repo = UserRepository(session)
        product_repo = ProductRepository(session)
        
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        # Проверяем, существует ли уже такой трек-код
        existing_product = await product_repo.get_product_by_track_code(message.text)
        
        if existing_product:
            texts = {
                "ru": "❌ Этот трек-код уже существует в системе",
                "tj": "❌ Ин рамзи тамошобин аллакай дар система мавҷуд аст"
            }
            await message.answer(texts[user.language])
            return
        
        # Сохраняем трек-код
        await state.update_data(track_code=message.text)
        
        texts = {
            "ru": "✏️ <b>Шаг 1 из 8: Название товара</b>\n\n"
                  "Введите название товара:\n"
                  "<i>Пример: Смартфон iPhone 15 Pro</i>",
            "tj": "✏️ <b>Қадами 1 аз 8: Номи маҳсулот</b>\n\n"
                  "Номи маҳсулотро ворид кунед:\n"
                  "<i>Намуна: Смартфони iPhone 15 Pro</i>"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.product_name)

@router.message(ClientState.product_name)
async def process_product_name(message: Message, state: FSMContext):
    """Обработка ввода названия товара"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт"]:
        # Возврат к вводу трек-кода
        await add_track_code_back(message, state)
        return
    
    await state.update_data(product_name=message.text)
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        texts = {
            "ru": "🏷️ <b>Шаг 2 из 8: Категория товара</b>\n\n"
                  "Выберите категорию товара:",
            "tj": "🏷️ <b>Қадами 2 аз 8: Гурӯҳи маҳсулот</b>\n\n"
                  "Гурӯҳи маҳсулотро интихоб кунед:"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_product_categories_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.product_category)

@router.message(ClientState.product_category)
async def process_product_category(message: Message, state: FSMContext):
    """Обработка выбора категории товара"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт"]:
        await product_name_back(message, state)
        return
    
    # Маппинг названий категорий на значения enum
    category_map = {
        "ru": {
            "📱 Электроника": ProductCategory.ELECTRONICS,
            "👕 Одежда": ProductCategory.CLOTHING,
            "👟 Обувь": ProductCategory.SHOES,
            "🏠 Бытовая техника": ProductCategory.HOME_APPLIANCES,
            "💄 Косметика": ProductCategory.BEAUTY,
            "🧸 Игрушки": ProductCategory.TOYS,
            "🚗 Автозапчасти": ProductCategory.AUTOMOTIVE,
            "⚽ Спорттовары": ProductCategory.SPORTS,
            "📦 Другое": ProductCategory.OTHER
        },
        "tj": {
            "📱 Электроника": ProductCategory.ELECTRONICS,
            "👕 Либос": ProductCategory.CLOTHING,
            "👟 Пойафзол": ProductCategory.SHOES,
            "🏠 Асбобҳои хонагӣ": ProductCategory.HOME_APPLIANCES,
            "💄 Косметика": ProductCategory.BEAUTY,
            "🧸 Бозичаҳо": ProductCategory.TOYS,
            "🚗 Қисмҳои автомобил": ProductCategory.AUTOMOTIVE,
            "⚽ Ашёҳои варзишӣ": ProductCategory.SPORTS,
            "📦 Дигар": ProductCategory.OTHER
        }
    }
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        selected_category = category_map[user.language].get(message.text)
        if not selected_category:
            texts = {
                "ru": "❌ Пожалуйста, выберите категорию из списка",
                "tj": "❌ Лутфан, гурӯҳро аз рӯйхат интихоб кунед"
            }
            await message.answer(texts[user.language])
            return
        
        await state.update_data(product_category=selected_category)
        
        texts = {
            "ru": "📝 <b>Шаг 3 из 8: Описание товара</b>\n\n"
                  "Опишите товар (цвет, размер, особенности):\n"
                  "<i>Пример: Черный, 256 ГБ, чехол в комплекте</i>\n\n"
                  "Или напишите 'Пропустить', если не хотите добавлять описание",
            "tj": "📝 <b>Қадами 3 аз 8: Тавсифи маҳсулот</b>\n\n"
                  "Маҳсулотро тавсиф кунед (ранг, андоза, хусусиятҳо):\n"
                  "<i>Намуна: Сиёҳ, 256 ГБ, ҷилд дар комплект</i>\n\n"
                  "Ё 'Гузарон' нависед, агар тавсиф илова кардан намехоҳед"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.product_description)

@router.message(ClientState.product_description)
async def process_product_description(message: Message, state: FSMContext):
    """Обработка ввода описания товара"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт"]:
        await product_category_back(message, state)
        return
    
    skip_texts = ["Пропустить", "Гузарон"]
    description = None if message.text in skip_texts else message.text
    await state.update_data(product_description=description)
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        texts = {
            "ru": "🔢 <b>Шаг 4 из 8: Количество</b>\n\n"
                  "Введите количество единиц товара:\n"
                  "<i>Пример: 1 или 10</i>",
            "tj": "🔢 <b>Қадами 4 аз 8: Миқдор</b>\n\n"
                  "Миқдори воҳидҳои маҳсулотро ворид кунед:\n"
                  "<i>Намуна: 1 ё 10</i>"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.product_quantity)

@router.message(ClientState.product_quantity)
async def process_product_quantity(message: Message, state: FSMContext):
    """Обработка ввода количества"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт"]:
        await product_description_back(message, state)
        return
    
    try:
        quantity = int(message.text)
        if quantity <= 0:
            raise ValueError
        
        await state.update_data(quantity=quantity)
        
        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(message.from_user.id)
            
            texts = {
                "ru": "💰 <b>Шаг 5 из 8: Цена за единицу</b>\n\n"
                      "Введите цену за одну единицу товара (в USD):\n"
                      "<i>Пример: 199.99</i>",
                "tj": "💰 <b>Қадами 5 аз 8: Нарх барои як воҳид</b>\n\n"
                      "Нархи як воҳиди маҳсулотро ворид кунед (дар USD):\n"
                      "<i>Намуна: 199.99</i>"
            }
            
            await message.answer(
                texts[user.language],
                reply_markup=get_back_cancel_keyboard(user.language),
                parse_mode="HTML"
            )
            await state.set_state(ClientState.product_unit_price)
            
    except ValueError:
        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(message.from_user.id)
            
            texts = {
                "ru": "❌ Пожалуйста, введите целое положительное число (например: 1, 5, 10)",
                "tj": "❌ Лутфан, рақами бутуни мусбат ворид кунед (масалан: 1, 5, 10)"
            }
            await message.answer(texts[user.language])

@router.message(ClientState.product_unit_price)
async def process_product_unit_price(message: Message, state: FSMContext):
    """Обработка ввода цены за единицу"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт"]:
        await product_quantity_back(message, state)
        return
    
    try:
        cleaned_text = message.text.replace(",", ".")
        unit_price = float(cleaned_text)
        
        if unit_price < 0:
            raise ValueError
        
        await state.update_data(unit_price=unit_price)
        
        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(message.from_user.id)
            
            texts = {
                "ru": "⚖️ <b>Шаг 6 из 8: Вес товара</b>\n\n"
                      "Введите вес одной единицы товара (в кг):\n"
                      "<i>Пример: 0.5 или 2.3</i>",
                "tj": "⚖️ <b>Қадами 6 аз 8: Вазни маҳсулот</b>\n\n"
                      "Вазни як воҳиди маҳсулотро ворид кунед (дар кг):\n"
                      "<i>Намуна: 0.5 ё 2.3</i>"
            }
            
            await message.answer(
                texts[user.language],
                reply_markup=get_back_cancel_keyboard(user.language),
                parse_mode="HTML"
            )
            await state.set_state(ClientState.product_weight)
            
    except ValueError:
        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(message.from_user.id)
            
            texts = {
                "ru": "❌ Пожалуйста, введите число (например: 50, 99.99, 150.50)",
                "tj": "❌ Лутфан, рақам ворид кунед (масалан: 50, 99.99, 150.50)"
            }
            await message.answer(texts[user.language])

@router.message(ClientState.product_weight)
async def process_product_weight(message: Message, state: FSMContext):
    """Обработка ввода веса"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт"]:
        await product_unit_price_back(message, state)
        return
    
    try:
        cleaned_text = message.text.replace(",", ".")
        weight = float(cleaned_text)
        
        if weight <= 0:
            raise ValueError
        
        await state.update_data(weight=weight)
        
        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(message.from_user.id)
            
            texts = {
                "ru": "📏 <b>Шаг 7 из 8: Габариты товара</b>\n\n"
                      "Введите размеры одной единицы (длина×ширина×высота в см):\n"
                      "<i>Пример: 15×8×3 или 20 10 5</i>\n\n"
                      "Или напишите 'Пропустить'",
                "tj": "📏 <b>Қадами 7 аз 8: Андозаҳои маҳсулот</b>\n\n"
                      "Андозаҳои як воҳидро ворид кунед (дарозӣ×барандозӣ×баландӣ дар см):\n"
                      "<i>Намуна: 15×8×3 ё 20 10 5</i>\n\n"
                      "Ё 'Гузарон' нависед"
            }
            
            await message.answer(
                texts[user.language],
                reply_markup=get_back_cancel_keyboard(user.language),
                parse_mode="HTML"
            )
            await state.set_state(ClientState.product_dimensions)
            
    except ValueError:
        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(message.from_user.id)
            
            texts = {
                "ru": "❌ Пожалуйста, введите положительное число (например: 0.5, 1.2, 3.0)",
                "tj": "❌ Лутфан, рақами мусбат ворид кунед (масалан: 0.5, 1.2, 3.0)"
            }
            await message.answer(texts[user.language])

@router.message(ClientState.product_dimensions)
async def process_product_dimensions(message: Message, state: FSMContext):
    """Обработка ввода габаритов"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт"]:
        await product_weight_back(message, state)
        return
    
    skip_texts = ["Пропустить", "Гузарон"]
    if message.text in skip_texts:
        await state.update_data(length=None, width=None, height=None)
    else:
        try:
            # Парсим размеры: 15×8×3 или 15x8x3 или 15 8 3
            text = message.text.replace('×', 'x').replace('х', 'x').replace('Х', 'x')
            parts = text.replace('x', ' ').split()
            
            if len(parts) == 3:
                length = float(parts[0])
                width = float(parts[1])
                height = float(parts[2])
                
                if length <= 0 or width <= 0 or height <= 0:
                    raise ValueError
                
                await state.update_data(length=length, width=width, height=height)
            else:
                raise ValueError
                
        except (ValueError, IndexError):
            async for session in get_db():
                user_repo = UserRepository(session)
                user = await user_repo.get_user_by_telegram_id(message.from_user.id)
                
                texts = {
                    "ru": "❌ Пожалуйста, введите размеры в формате: длина×ширина×высота\n"
                          "<i>Пример: 15×8×3 или 20 10 5</i>",
                    "tj": "❌ Лутфан, андозаҳоро дар формати: дарозӣ×барандозӣ×баландӣ ворид кунед\n"
                          "<i>Намуна: 15×8×3 ё 20 10 5</i>"
                }
                await message.answer(texts[user.language], parse_mode="HTML")
                return
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        texts = {
            "ru": "⚠️ <b>Шаг 8 из 8: Особые свойства</b>\n\n"
                  "Выберите особые свойства товара:",
            "tj": "⚠️ <b>Қадами 8 аз 8: Хусусиятҳои махсус</b>\n\n"
                  "Хусусиятҳои махсуси маҳсулотро интихоб кунед:"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_special_info_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.product_special_info)

@router.message(ClientState.product_special_info)
async def process_product_special_info(message: Message, state: FSMContext):
    """Обработка выбора особых свойств и сохранение товара"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт"]:
        await product_dimensions_back(message, state)
        return
    
    # Определяем выбранные свойства
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        property_texts = {
            "ru": {
                "Хрупкий": "fragile",
                "С батареей": "battery",
                "Жидкость": "liquid",
                "Нет особых свойств": "none"
            },
            "tj": {
                "Нозук": "fragile",
                "Бо батарея": "battery",
                "Моеъ": "liquid",
                "Хусусияти махсус нест": "none"
            }
        }
        
        selected_property = property_texts[user.language].get(message.text)
        if not selected_property:
            texts = {
                "ru": "❌ Пожалуйста, выберите вариант из списка",
                "tj": "❌ Лутфан, вариантро аз рӯйхат интихоб кунед"
            }
            await message.answer(texts[user.language])
            return
        
        # Получаем все данные из состояния
        data = await state.get_data()
        track_code = data.get('track_code')
        product_name = data.get('product_name')
        product_category = data.get('product_category')
        product_description = data.get('product_description')
        quantity = data.get('quantity', 1)
        unit_price = data.get('unit_price', 0.0)
        weight = data.get('weight', 0.0)
        length = data.get('length')
        width = data.get('width')
        height = data.get('height')
        
        # Рассчитываем общую стоимость
        total_value = unit_price * quantity
        
        # Определяем свойства
        fragile = selected_property == "fragile"
        has_battery = selected_property == "battery"
        is_liquid = selected_property == "liquid"
        
        # Сохраняем товар в БД
        product_repo = ProductRepository(session)
        
        try:
            product = await product_repo.create_product(
                track_code=track_code,
                user_id=user.id,
                product_name=product_name,
                product_category=product_category.value,
                product_description=product_description,
                quantity=quantity,
                unit_price_usd=unit_price,
                total_value_usd=total_value,
                weight_kg=weight,
                length_cm=length,
                width_cm=width,
                height_cm=height,
                fragile=fragile,
                has_battery=has_battery,
                is_liquid=is_liquid
            )
            
            from .utils import show_product_success_message
            await show_product_success_message(
                message=message,
                state=state,
                product=product,
                user=user,
                track_code=track_code,
                product_name=product_name,
                product_category=product_category,
                quantity=quantity,
                unit_price=unit_price,
                total_value=total_value,
                weight=weight,
                length=length,
                width=width,
                height=height,
                fragile=fragile,
                has_battery=has_battery,
                is_liquid=is_liquid,
                product_description=product_description
            )
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении товара: {e}")
            texts = {
                "ru": "❌ Произошла ошибка при сохранении товара. Пожалуйста, попробуйте еще раз.",
                "tj": "❌ Дар захира кардани маҳсулот хато рух дод. Лутфан, бори дигар кӯшиш кунед."
            }
            from keyboards.client import get_track_codes_keyboard
            await message.answer(
                texts[user.language],
                reply_markup=get_track_codes_keyboard(user.language)
            )
            await state.set_state(ClientState.track_codes_menu)

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ВОЗВРАТА ==========

async def add_track_code_back(message: Message, state: FSMContext):
    """Возврат к вводу трек-кода"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        texts = {
            "ru": "📦 <b>Добавление нового товара</b>\n\n"
                  "Введите трек-код товара:",
            "tj": "📦 <b>Илова кардани маҳсулоти нав</b>\n\n"
                  "Рамзи тамошобини маҳсулотро ворид кунед:"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.add_track_code)

async def product_name_back(message: Message, state: FSMContext):
    """Возврат к вводу названия товара"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        texts = {
            "ru": "✏️ <b>Шаг 1 из 8: Название товара</b>\n\n"
                  "Введите название товара:\n"
                  "<i>Пример: Смартфон iPhone 15 Pro</i>",
            "tj": "✏️ <b>Қадами 1 аз 8: Номи маҳсулот</b>\n\n"
                  "Номи маҳсулотро ворид кунед:\n"
                  "<i>Намуна: Смартфони iPhone 15 Pro</i>"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.product_name)

async def product_category_back(message: Message, state: FSMContext):
    """Возврат к выбору категории"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        texts = {
            "ru": "🏷️ <b>Шаг 2 из 8: Категория товара</b>\n\n"
                  "Выберите категорию товара:",
            "tj": "🏷️ <b>Қадами 2 аз 8: Гурӯҳи маҳсулот</b>\n\n"
                  "Гурӯҳи маҳсулотро интихоб кунед:"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_product_categories_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.product_category)

async def product_description_back(message: Message, state: FSMContext):
    """Возврат к вводу описания"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        texts = {
            "ru": "📝 <b>Шаг 3 из 8: Описание товара</b>\n\n"
                  "Опишите товар (цвет, размер, особенности):\n"
                  "<i>Пример: Черный, 256 ГБ, чехол в комплекте</i>\n\n"
                  "Или напишите 'Пропустить', если не хотите добавлять описание",
            "tj": "📝 <b>Қадами 3 аз 8: Тавсифи маҳсулот</b>\n\n"
                  "Маҳсулотро тавсиф кунед (ранг, андоза, хусусиятҳо):\n"
                  "<i>Намуна: Сиёҳ, 256 ГБ, ҷилд дар комплект</i>\n\n"
                  "Ё 'Гузарон' нависед, агар тавсиф илова кардан намехоҳед"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.product_description)

async def product_quantity_back(message: Message, state: FSMContext):
    """Возврат к вводу количества"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        texts = {
            "ru": "🔢 <b>Шаг 4 из 8: Количество</b>\n\n"
                  "Введите количество единиц товара:\n"
                  "<i>Пример: 1 или 10</i>",
            "tj": "🔢 <b>Қадами 4 аз 8: Миқдор</b>\n\n"
                  "Миқдори воҳидҳои маҳсулотро ворид кунед:\n"
                  "<i>Намуна: 1 ё 10</i>"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.product_quantity)

async def product_unit_price_back(message: Message, state: FSMContext):
    """Возврат к вводу цены за единицу"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        texts = {
            "ru": "💰 <b>Шаг 5 из 8: Цена за единицу</b>\n\n"
                  "Введите цену за одну единицу товара (в USD):\n"
                  "<i>Пример: 199.99</i>",
            "tj": "💰 <b>Қадами 5 аз 8: Нарх барои як воҳид</b>\n\n"
                  "Нархи як воҳиди маҳсулотро ворид кунед (дар USD):\n"
                  "<i>Намуна: 199.99</i>"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.product_unit_price)

async def product_weight_back(message: Message, state: FSMContext):
    """Возврат к вводу веса"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        texts = {
            "ru": "⚖️ <b>Шаг 6 из 8: Вес товара</b>\n\n"
                  "Введите вес одной единицы товара (в кг):\n"
                  "<i>Пример: 0.5 или 2.3</i>",
            "tj": "⚖️ <b>Қадами 6 аз 8: Вазни маҳсулот</b>\n\n"
                  "Вазни як воҳиди маҳсулотро ворид кунед (дар кг):\n"
                  "<i>Намуна: 0.5 ё 2.3</i>"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.product_weight)

async def product_dimensions_back(message: Message, state: FSMContext):
    """Возврат к вводу габаритов"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        texts = {
            "ru": "📏 <b>Шаг 7 из 8: Габариты товара</b>\n\n"
                  "Введите размеры одной единицы (длина×ширина×высота в см):\n"
                  "<i>Пример: 15×8×3 или 20 10 5</i>\n\n"
                  "Или напишите 'Пропустить'",
            "tj": "📏 <b>Қадами 7 аз 8: Андозаҳои маҳсулот</b>\n\n"
                  "Андозаҳои як воҳидро ворид кунед (дарозӣ×барандозӣ×баландӣ дар см):\n"
                  "<i>Намуна: 15×8×3 ё 20 10 5</i>\n\n"
                  "Ё 'Гузарон' нависед"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.product_dimensions)