from sqlalchemy import select
import logging
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import KeyboardButton

from database.models import Product, User
from database.session import get_db
from database.repository import UserRepository, ProductRepository
from database.models import ProductStatus, ProductCategory
from keyboards.client import get_track_codes_keyboard, get_main_menu_keyboard, get_back_cancel_keyboard
from keyboards.products import get_product_categories_keyboard, get_special_info_keyboard
from utils.states import ClientState
from services.track_code_generator import TrackCodeGenerator

logger = logging.getLogger(__name__)

# Создаем роутер
track_codes_router = Router()
# ========== ГЛАВНОЕ МЕНЮ ТРЕК-КОДОВ ==========

@track_codes_router.message(ClientState.track_codes_menu)
async def track_codes_handler(message: Message, state: FSMContext):
    """Обработка действий в меню трек-кодов"""
    logger.info(f"Пользователь {message.from_user.id} в меню трек-кодов: {message.text}")
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            return
        
        # Определяем текст кнопок в зависимости от языка
        my_tracks_ru = "Мои трек-коды"
        my_tracks_tj = "Рамзҳои тамошобини ман"
        check_track_ru = "Проверить трек-код"
        check_track_tj = "Тафтиш кардани рамзи тамошобин"
        add_track_ru = "Добавить трек-код"
        add_track_tj = "Илова кардани рамзи тамошобин"
        edit_track_ru = "Изменить товар"
        edit_track_tj = "Тағйир додани маҳсулот"
        export_ru = "Экспорт в Excel"
        export_tj = "Экспорт ба Excel"
        back_ru = "⬅️ Назад"
        back_tj = "⬅️ Бозгашт"
        
        if message.text in [my_tracks_ru, my_tracks_tj]:
            await show_my_track_codes(message, state)
            
        elif message.text in [check_track_ru, check_track_tj]:
            await check_track_code_start(message, state)
            
        elif message.text in [add_track_ru, add_track_tj]:
            await add_track_code_start(message, state)
            
        elif message.text in [edit_track_ru, edit_track_tj]:
            await edit_track_code_start(message, state)
            
        elif message.text in [back_ru, back_tj]:
            await message.answer(
                "Главное меню:" if user.language == "ru" else "Менюи асосӣ:",
                reply_markup=get_main_menu_keyboard(user.language)
            )
            await state.set_state(ClientState.main_menu)
        else:
            await message.answer(
                "Выберите действие из меню" if user.language == "ru"
                else "Амалро аз меню интихоб кунед",
                reply_markup=get_track_codes_keyboard(user.language)
            )

# ========== МОИ ТРЕК-КОДЫ ==========

async def show_my_track_codes(message: Message, state: FSMContext):
    """Показать трек-коды пользователя"""
    async for session in get_db():
        user_repo = UserRepository(session)
        product_repo = ProductRepository(session)
        
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        # Получаем товары пользователя
        products = await product_repo.get_user_products(user.id, limit=50)
        
        if not products:
            texts = {
                "ru": "📭 У вас пока нет добавленных товаров.\n\n"
                      "Нажмите 'Добавить трек-код' чтобы добавить первый товар!",
                "tj": "📭 Шумо то ҳол маҳсулоти иловашуда надоред.\n\n"
                      "Тугмаи 'Илова кардани рамзи тамошобин'-ро пахш кунед, то аввалин маҳсулотро илова кунед!"
            }
            await message.answer(texts[user.language])
            return
        
        # Формируем сообщение с пагинацией
        current_page = 1
        page_size = 5
        start_idx = (current_page - 1) * page_size
        end_idx = min(start_idx + page_size, len(products))
        
        # Сохраняем данные в состоянии
        await state.update_data(
            products_page=current_page,
            user_products=products,
            products_total=len(products)
        )
        
        await show_products_page(message, state, products[start_idx:end_idx], current_page, len(products))

async def show_products_page(message: Message, state: FSMContext, products, page: int, total: int):
    """Показать страницу с товарами"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        page_size = 5
        total_pages = (total + page_size - 1) // page_size
        
        # Заголовок
        text = {
            "ru": f"📦 <b>Ваши товары (страница {page}/{total_pages}):</b>\n\n",
            "tj": f"📦 <b>Маҳсулотҳои шумо (саҳифа {page}/{total_pages}):</b>\n\n"
        }[user.language]
        
        # Добавляем товары
        start_num = (page - 1) * page_size + 1
        for i, product in enumerate(products, start_num):
            status_text = get_status_text(product.status.value, user.language)
            product_name = product.product_name or ("Без названия" if user.language == "ru" else "Беном")
            
            text += f"<b>{i}.</b> <code>{product.track_code}</code>\n"
            text += f"   🏷️ {product_name}\n"
            text += f"   📍 {status_text}\n"
            
            if product.total_value_usd and product.total_value_usd > 0:
                cost_text = f"   💰 ${product.total_value_usd:.2f}\n" if user.language == "ru" else f"   💰 ${product.total_value_usd:.2f}\n"
                text += cost_text
            
            text += f"   📅 {product.created_at.strftime('%d.%m.%Y')}\n\n"
        
        # Создаем клавиатуру с пагинацией
        keyboard = InlineKeyboardBuilder()
        
        if page > 1:
            keyboard.add(InlineKeyboardButton(
                text="◀️ Назад" if user.language == "ru" else "◀️ Бозгашт",
                callback_data=f"prev_page_{page-1}"
            ))
        
        if page < total_pages:
            keyboard.add(InlineKeyboardButton(
                text="Вперед ▶️" if user.language == "ru" else "Оёд ▶️",
                callback_data=f"next_page_{page+1}"
            ))
        
        # Кнопка деталей для первого товара, если он один на странице
        if len(products) == 1:
            keyboard.row(InlineKeyboardButton(
                text="🔍 Подробнее" if user.language == "ru" else "🔍 Тафсилот",
                callback_data=f"view_product_{products[0].id}"
            ))
        
        # Кнопка возврата
        keyboard.row(InlineKeyboardButton(
            text="🔙 В меню" if user.language == "ru" else "🔙 Ба меню",
            callback_data="back_to_track_menu"
        ))
        
        await message.answer(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML"
        )

# ========== ПРОВЕРКА ТРЕК-КОДА ==========

async def check_track_code_start(message: Message, state: FSMContext):
    """Начало проверки трек-кода"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        texts = {
            "ru": "🔍 <b>Проверка трек-кода</b>\n\n"
                  "Введите трек-код для проверки:\n"
                  "<i>Можно ввести несколько кодов через запятую</i>",
            "tj": "🔍 <b>Тафтиш кардани рамзи тамошобин</b>\n\n"
                  "Барои тафтиш рамзи тамошобинро ворид кунед:\n"
                  "<i>Якчанд рамзро бо вергул ҷудо кардан мумкин аст</i>"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.check_track_code)

@track_codes_router.message(ClientState.check_track_code)
async def process_check_track_code(message: Message, state: FSMContext):
    """Обработка проверки трек-кода"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт"]:
        await back_to_track_menu(message, state)
        return
    
    async for session in get_db():
        user_repo = UserRepository(session)
        product_repo = ProductRepository(session)
        
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        # Разделяем трек-коды
        track_codes = [code.strip() for code in message.text.split(",") if code.strip()]
        
        if not track_codes:
            texts = {
                "ru": "❌ Пожалуйста, введите хотя бы один трек-код",
                "tj": "❌ Лутфан, на камтар як рамзи тамошобин ворид кунед"
            }
            await message.answer(texts[user.language])
            return
        
        # Проверяем каждый трек-код
        results = []
        for track_code in track_codes:
            product = await product_repo.get_product_by_track_code(track_code)
            
            if product:
                status_text = get_status_text(product.status.value, user.language)
                product_name = product.product_name or "Без названия"
                
                # Проверяем, принадлежит ли товар пользователю
                belongs_to_user = product.user_id == user.id
                owner_info = ""
                if not belongs_to_user:
                    owner_info = "\n   ⚠️ Этот товар принадлежит другому пользователю" if user.language == "ru" else "\n   ⚠️ Ин маҳсулот ба корбари дигар тааллуқ дорад"
                
                results.append(f"✅ <b>{track_code}</b>\n"
                             f"   🏷️ {product_name}\n"
                             f"   📍 {status_text}{owner_info}")
            else:
                results.append(f"❌ <b>{track_code}</b> - не найден" if user.language == "ru" else f"❌ <b>{track_code}</b> - ёфт нашуд")
        
        # Формируем итоговое сообщение
        text = {
            "ru": f"🔍 <b>Результаты проверки:</b>\n\n" + "\n\n".join(results),
            "tj": f"🔍 <b>Натиҷаҳои тафтиш:</b>\n\n" + "\n\n".join(results)
        }[user.language]
        
        await message.answer(
            text,
            reply_markup=get_track_codes_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.track_codes_menu)

# ========== ДОБАВЛЕНИЕ ТРЕК-КОДА ==========

async def add_track_code_start(message: Message, state: FSMContext):
    """Начало добавления трек-кода"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        # Генерируем трек-код
        track_code = TrackCodeGenerator.generate_track_code(user.telegram_id)
        
        texts = {
            "ru": f"📦 <b>Добавление нового товара</b>\n\n"
                  f"Ваш трек-код: <code>{track_code}</code>\n\n"
                  "Введите название товара:",
            "tj": f"📦 <b>Илова кардани маҳсулоти нав</b>\n\n"
                  f"Рамзи тамошобини шумо: <code>{track_code}</code>\n\n"
                  "Номи маҳсулотро ворид кунед:"
        }
        
        # Сохраняем трек-код в состоянии
        await state.update_data(track_code=track_code)
        
        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.product_name)

@track_codes_router.message(ClientState.product_name)
async def process_product_name(message: Message, state: FSMContext):
    """Обработка ввода названия товара"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт", "❌ Отмена", "❌ Бекор кардан"]:
        await back_to_track_menu(message, state)
        return
    
    await state.update_data(product_name=message.text)
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        texts = {
            "ru": "🏷️ <b>Выберите категорию товара:</b>",
            "tj": "🏷️ <b>Гурӯҳи маҳсулотро интихоб кунед:</b>"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_product_categories_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.product_category)

@track_codes_router.message(ClientState.product_category)
async def process_product_category(message: Message, state: FSMContext):
    """Обработка выбора категории товара"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт", "❌ Отмена", "❌ Бекор кардан"]:
        await state.set_state(ClientState.product_name)
        await process_product_name(message, state)
        return
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        # Маппинг категорий
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
            "ru": "📝 <b>Опишите товар (цвет, размер, особенности):</b>\n\n"
                  "<i>Или напишите 'Пропустить'</i>",
            "tj": "📝 <b>Маҳсулотро тавсиф кунед (ранг, андоза, хусусиятҳо):</b>\n\n"
                  "<i>Ё 'Гузарон' нависед</i>"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.product_description)

@track_codes_router.message(ClientState.product_description)
async def process_product_description(message: Message, state: FSMContext):
    """Обработка ввода описания товара"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт", "❌ Отмена", "❌ Бекор кардан"]:
        await state.set_state(ClientState.product_category)
        await process_product_category(message, state)
        return
    
    skip_texts = ["Пропустить", "Гузарон"]
    description = None if message.text in skip_texts else message.text
    await state.update_data(product_description=description)
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        texts = {
            "ru": "🔢 <b>Введите количество единиц товара:</b>\n\n"
                  "<i>Пример: 1 или 10</i>",
            "tj": "🔢 <b>Миқдори воҳидҳои маҳсулотро ворид кунед:</b>\n\n"
                  "<i>Намуна: 1 ё 10</i>"
        }
        
        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.product_quantity)

@track_codes_router.message(ClientState.product_quantity)
async def process_product_quantity(message: Message, state: FSMContext):
    """Обработка ввода количества"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт", "❌ Отмена", "❌ Бекор кардан"]:
        await state.set_state(ClientState.product_description)
        await process_product_description(message, state)
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
                "ru": "💰 <b>Введите цену за одну единицу товара (в USD):</b>\n\n"
                      "<i>Пример: 199.99</i>",
                "tj": "💰 <b>Нархи як воҳиди маҳсулотро ворид кунед (дар USD):</b>\n\n"
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

@track_codes_router.message(ClientState.product_unit_price)
async def process_product_unit_price(message: Message, state: FSMContext):
    """Обработка ввода цены за единицу"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт", "❌ Отмена", "❌ Бекор кардан"]:
        await state.set_state(ClientState.product_quantity)
        await process_product_quantity(message, state)
        return
    
    try:
        cleaned_text = message.text.replace(",", ".")
        unit_price = float(cleaned_text)
        
        if unit_price < 0:
            raise ValueError
        
        data = await state.get_data()
        quantity = data.get('quantity', 1)
        total_value = unit_price * quantity
        
        await state.update_data(
            unit_price=unit_price,
            total_value=total_value
        )
        
        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(message.from_user.id)
            
            texts = {
                "ru": "⚖️ <b>Введите вес одной единицы товара (в кг):</b>\n\n"
                      "<i>Пример: 0.5 или 2.3</i>",
                "tj": "⚖️ <b>Вазни як воҳиди маҳсулотро ворид кунед (дар кг):</b>\n\n"
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

@track_codes_router.message(ClientState.product_weight)
async def process_product_weight(message: Message, state: FSMContext):
    """Обработка ввода веса"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт", "❌ Отмена", "❌ Бекор кардан"]:
        await state.set_state(ClientState.product_unit_price)
        await process_product_unit_price(message, state)
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
                "ru": "⚠️ <b>Выберите особые свойства товара:</b>",
                "tj": "⚠️ <b>Хусусиятҳои махсуси маҳсулотро интихоб кунед:</b>"
            }
            
            await message.answer(
                texts[user.language],
                reply_markup=get_special_info_keyboard(user.language),
                parse_mode="HTML"
            )
            await state.set_state(ClientState.product_special_info)
            
    except ValueError:
        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(message.from_user.id)
            
            texts = {
                "ru": "❌ Пожалуйста, введите положительное число (например: 0.5, 1.2, 3.0)",
                "tj": "❌ Лутфан, рақами мусбат ворид кунед (масалан: 0.5, 1.2, 3.0)"
            }
            await message.answer(texts[user.language])

@track_codes_router.message(ClientState.product_special_info)
async def process_product_special_info(message: Message, state: FSMContext):
    """Обработка выбора особых свойств и сохранение товара"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт", "❌ Отмена", "❌ Бекор кардан"]:
        await state.set_state(ClientState.product_weight)
        await process_product_weight(message, state)
        return
    
    async for session in get_db():
        user_repo = UserRepository(session)
        product_repo = ProductRepository(session)
        
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        # Определяем свойства
        property_map = {
            "ru": {
                "Хрупкий": {"fragile": True},
                "С батареей": {"has_battery": True},
                "Жидкость": {"is_liquid": True},
                "Нет особых свойств": {}
            },
            "tj": {
                "Нозук": {"fragile": True},
                "Бо батарея": {"has_battery": True},
                "Моеъ": {"is_liquid": True},
                "Хусусияти махсус нест": {}
            }
        }
        
        properties = property_map[user.language].get(message.text, {})
        
        # Получаем все данные
        data = await state.get_data()
        
        try:
            # Создаем товар
            product = await product_repo.create_product(
                track_code=data['track_code'],
                user_id=user.id,
                product_name=data.get('product_name'),
                product_category=data.get('product_category'),
                product_description=data.get('product_description'),
                quantity=data.get('quantity', 1),
                unit_price_usd=data.get('unit_price', 0.0),
                total_value_usd=data.get('total_value', 0.0),
                weight_kg=data.get('weight', 0.0),
                **properties
            )
            
            # Формируем сообщение об успехе
            category_name = get_category_name(data.get('product_category'), user.language)
            
            texts = {
                "ru": f"""✅ <b>Товар успешно добавлен!</b>

📦 <b>Информация о товаре:</b>
🎯 Трек-код: <code>{data['track_code']}</code>
🏷️ Название: {data.get('product_name', 'Не указано')}
📂 Категория: {category_name}
📝 Описание: {data.get('product_description', 'Не указано')}
🔢 Количество: {data.get('quantity', 1)} шт.
💰 Цена за единицу: ${data.get('unit_price', 0.0):.2f}
💵 Общая стоимость: ${data.get('total_value', 0.0):.2f}
⚖️ Вес: {data.get('weight', 0.0):.2f} кг

📅 Дата добавления: {product.created_at.strftime('%d.%m.%Y %H:%M')}
🆔 ID товара: {product.id}

<i>Администраторы теперь видят полную информацию о вашем товаре.</i>""",
                "tj": f"""✅ <b>Маҳсулот бомуваффақият илова карда шуд!</b>

📦 <b>Маълумот дар бораи маҳсулот:</b>
🎯 Рамзи тамошобин: <code>{data['track_code']}</code>
🏷️ Ном: {data.get('product_name', 'Муайян нашудааст')}
📂 Гурӯҳ: {category_name}
📝 Тавсиф: {data.get('product_description', 'Муайян нашудааст')}
🔢 Миқдор: {data.get('quantity', 1)} дона
💰 Нарх барои як воҳид: ${data.get('unit_price', 0.0):.2f}
💵 Арзиши умумӣ: ${data.get('total_value', 0.0):.2f}
⚖️ Вазн: {data.get('weight', 0.0):.2f} кг

📅 Сании илова: {product.created_at.strftime('%d.%m.%Y %H:%M')}
🆔 ID маҳсулот: {product.id}

<i>Администраторҳо акнун маълумоти пурра дар бораи маҳсулоти шуморо мебинанд.</i>"""
            }
            
            await message.answer(
                texts[user.language],
                reply_markup=get_track_codes_keyboard(user.language),
                parse_mode="HTML"
            )
            await state.set_state(ClientState.track_codes_menu)
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении товара: {e}")
            texts = {
                "ru": "❌ Произошла ошибка при сохранении товара. Пожалуйста, попробуйте еще раз.",
                "tj": "❌ Дар захира кардани маҳсулот хато рух дод. Лутфан, бори дигар кӯшиш кунед."
            }
            await message.answer(
                texts[user.language],
                reply_markup=get_track_codes_keyboard(user.language)
            )
            await state.set_state(ClientState.track_codes_menu)

# ========== РЕДАКТИРОВАНИЕ ТОВАРА ==========

# ========== РЕДАКТИРОВАНИЕ ТОВАРА ==========

async def edit_track_code_start(message: Message, state: FSMContext):
    """Начало редактирования товара"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        # Получаем товары пользователя
        product_repo = ProductRepository(session)
        products = await product_repo.get_user_products(user.id, limit=20)
        
        if not products:
            texts = {
                "ru": "❌ У вас нет товаров для редактирования",
                "tj": "❌ Шумо маҳсулот барои таҳрир кардан надоред"
            }
            await message.answer(texts[user.language])
            return
        
        # Сохраняем товары в состоянии для дальнейшего использования
        await state.update_data(edit_products=products)
        
        # Формируем список товаров для выбора
        text = {
            "ru": "✏️ <b>Выберите товар для редактирования:</b>\n\n",
            "tj": "✏️ <b>Маҳсулотро барои таҳрир кардан интихоб кунед:</b>\n\n"
        }[user.language]
        
        keyboard = InlineKeyboardBuilder()
        
        for i, product in enumerate(products, 1):
            product_name = product.product_name or ("Без названия" if user.language == "ru" else "Беном")
            status_text = get_status_text(product.status.value, user.language)
            text += f"{i}. <code>{product.track_code}</code> - {product_name} ({status_text})\n"
            
            # Добавляем кнопку для каждого товара (максимум 10)
            if i <= 10:
                keyboard.add(InlineKeyboardButton(
                    text=f"{i}. {product.track_code[:8]}...",
                    callback_data=f"edit_select_{product.id}"
                ))
        
        keyboard.add(InlineKeyboardButton(
            text="🔙 Назад" if user.language == "ru" else "🔙 Бозгашт",
            callback_data="back_to_track_menu"
        ))
        
        keyboard.adjust(2)
        
        await message.answer(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML"
        )

# ========== INLINE CALLBACK ОБРАБОТЧИКИ ДЛЯ РЕДАКТИРОВАНИЯ ==========

@track_codes_router.callback_query(F.data.startswith("edit_select_"))
async def edit_select_callback(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора товара для редактирования"""
    product_id = int(callback.data.split("_")[2])
    
    async for session in get_db():
        user_repo = UserRepository(session)
        product_repo = ProductRepository(session)
        
        user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
        
        # Получаем товар
        result = await session.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()
        
        if not product or product.user_id != user.id:
            await callback.answer("Товар не найден или недоступен")
            return
        
        # Сохраняем ID товара в состоянии
        await state.update_data(edit_product_id=product_id)
        
        # Показываем меню редактирования
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        
        texts = {
            "ru": f"✏️ <b>Редактирование товара</b>\n\n"
                  f"Трек-код: <code>{product.track_code}</code>\n"
                  f"Название: {product.product_name or 'Не указано'}\n\n"
                  f"Что вы хотите изменить?",
            "tj": f"✏️ <b>Таҳрир кардани маҳсулот</b>\n\n"
                  f"Рамзи тамошобин: <code>{product.track_code}</code>\n"
                  f"Ном: {product.product_name or 'Муайян нашудааст'}\n\n"
                  f"Шумо чӣ мехоҳед тағйир диҳед?"
        }
        
        keyboard = ReplyKeyboardBuilder()
        options = [
            ("📝 Изменить название", "📝 Тағйир додани ном"),
            ("📝 Изменить описание", "📝 Тағйир додани тавсиф"),
            ("🔢 Изменить количество", "🔢 Тағйир додани миқдор"),
            ("💰 Изменить цену", "💰 Тағйир додани нарх"),
            ("⚖️ Изменить вес", "⚖️ Тағйир додани вазн"),
            ("🏷️ Изменить категорию", "🏷️ Тағйир додани гурӯҳ"),
            ("🔙 Назад", "🔙 Бозгашт")
        ]
        
        for option_ru, option_tj in options:
            keyboard.add(KeyboardButton(
                text=option_ru if user.language == "ru" else option_tj
            ))
        
        keyboard.adjust(2, 2, 2, 1)
        
        await callback.message.answer(
            texts[user.language],
            reply_markup=keyboard.as_markup(resize_keyboard=True),
            parse_mode="HTML"
        )
        
        # Устанавливаем состояние редактирования
        await state.set_state(ClientState.edit_product)
    
    await callback.answer()

@track_codes_router.callback_query(F.data.startswith("edit_product_"))
async def edit_product_callback(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования товара"""
    product_id = int(callback.data.split("_")[2])
    
    # Сохраняем ID товара в состоянии
    await state.update_data(edit_product_id=product_id)
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
        
        texts = {
            "ru": "✏️ <b>Редактирование товара</b>\n\nЧто вы хотите изменить?",
            "tj": "✏️ <b>Таҳрир кардани маҳсулот</b>\n\nШумо чӣ мехоҳед тағйир диҳед?"
        }
        
        keyboard = ReplyKeyboardBuilder()
        options = [
            ("📝 Изменить название", "📝 Тағйир додани ном"),
            ("📝 Изменить описание", "📝 Тағйир додани тавсиф"),
            ("🔢 Изменить количество", "🔢 Тағйир додани миқдор"),
            ("💰 Изменить цену", "💰 Тағйир додани нарх"),
            ("⚖️ Изменить вес", "⚖️ Тағйир додани вазн"),
            ("🏷️ Изменить категорию", "🏷️ Тағйир додани гурӯҳ"),
            ("🔙 Назад", "🔙 Бозгашт")
        ]
        
        for option_ru, option_tj in options:
            keyboard.add(KeyboardButton(
                text=option_ru if user.language == "ru" else option_tj
            ))
        
        keyboard.adjust(2, 2, 2, 1)
        
        await callback.message.answer(
            texts[user.language],
            reply_markup=keyboard.as_markup(resize_keyboard=True),
            parse_mode="HTML"
        )
        
        # Устанавливаем состояние редактирования
        await state.set_state(ClientState.edit_product)
    
    await callback.answer()

@track_codes_router.callback_query(F.data.startswith("edit_name_"))
async def edit_name_callback(callback: CallbackQuery, state: FSMContext):
    """Редактирование названия товара"""
    product_id = int(callback.data.split("_")[2])
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
        
        await state.update_data(edit_field="name", edit_product_id=product_id)
        
        texts = {
            "ru": "✏️ <b>Введите новое название товара:</b>",
            "tj": "✏️ <b>Номи нави маҳсулотро ворид кунед:</b>"
        }
        
        await callback.message.edit_text(
            texts[user.language],
            parse_mode="HTML"
        )
        
        # Устанавливаем состояние для ввода нового названия
        from utils.states import ClientState
        await state.set_state(ClientState.edit_product_name)
    
    await callback.answer()

@track_codes_router.callback_query(F.data.startswith("edit_desc_"))
async def edit_desc_callback(callback: CallbackQuery, state: FSMContext):
    """Редактирование описания товара"""
    product_id = int(callback.data.split("_")[2])
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
        
        await state.update_data(edit_field="description", edit_product_id=product_id)
        
        texts = {
            "ru": "✏️ <b>Введите новое описание товара:</b>\n\n<i>Или напишите 'Удалить' чтобы удалить описание</i>",
            "tj": "✏️ <b>Тавсифи нави маҳсулотро ворид кунед:</b>\n\n<i>Ё 'Нест кардан' нависед, то тавсифро нест кунед</i>"
        }
        
        await callback.message.edit_text(
            texts[user.language],
            parse_mode="HTML"
        )
        
        await state.set_state(ClientState.edit_product_desc)
    
    await callback.answer()

# Аналогичные обработчики для остальных полей:
# edit_quantity_, edit_price_, edit_weight_, edit_category_

@track_codes_router.callback_query(F.data == "back_to_edit_list")
async def back_to_edit_list_callback(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку товаров для редактирования"""
    await edit_track_code_start(callback.message, state)
    await callback.answer()

# ========== ОБРАБОТЧИКИ ВВОДА ДАННЫХ ДЛЯ РЕДАКТИРОВАНИЯ ==========

@track_codes_router.message(ClientState.edit_product_name)
async def process_edit_product_name(message: Message, state: FSMContext):
    """Обработка ввода нового названия товара"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт", "❌ Отмена", "❌ Бекор кардан"]:
        await back_to_track_menu(message, state)
        return
    
    data = await state.get_data()
    product_id = data.get('edit_product_id')
    
    async for session in get_db():
        product_repo = ProductRepository(session)
        user_repo = UserRepository(session)
        
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        # Обновляем название товара
        updated_product = await product_repo.update_product(
            product_id,
            product_name=message.text
        )
        
        if updated_product:
            texts = {
                "ru": f"✅ Название товара <code>{updated_product.track_code}</code> успешно изменено на: {message.text}",
                "tj": f"✅ Номи маҳсулот <code>{updated_product.track_code}</code> бомуваффақият тағйир дода шуд ба: {message.text}"
            }
            await message.answer(texts[user.language], parse_mode="HTML")
        else:
            texts = {
                "ru": "❌ Ошибка при изменении названия",
                "tj": "❌ Хато дар тағйир додани ном"
            }
            await message.answer(texts[user.language])
    
    # Возвращаемся в меню трек-кодов
    await back_to_track_menu(message, state)

@track_codes_router.message(ClientState.edit_product_desc)
async def process_edit_product_desc(message: Message, state: FSMContext):
    """Обработка ввода нового описания товара"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт", "❌ Отмена", "❌ Бекор кардан"]:
        await back_to_track_menu(message, state)
        return
    
    data = await state.get_data()
    product_id = data.get('edit_product_id')
    
    # Проверяем, не хочет ли пользователь удалить описание
    delete_texts = ["Удалить", "Нест кардан"]
    new_description = None if message.text in delete_texts else message.text
    
    async for session in get_db():
        product_repo = ProductRepository(session)
        user_repo = UserRepository(session)
        
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        # Обновляем описание товара
        updated_product = await product_repo.update_product(
            product_id,
            product_description=new_description
        )
        
        if updated_product:
            if new_description is None:
                texts = {
                    "ru": f"✅ Описание товара <code>{updated_product.track_code}</code> удалено",
                    "tj": f"✅ Тавсифи маҳсулот <code>{updated_product.track_code}</code> нест карда шуд"
                }
            else:
                texts = {
                    "ru": f"✅ Описание товара <code>{updated_product.track_code}</code> успешно изменено",
                    "tj": f"✅ Тавсифи маҳсулот <code>{updated_product.track_code}</code> бомуваффақият тағйир дода шуд"
                }
            await message.answer(texts[user.language], parse_mode="HTML")
        else:
            texts = {
                "ru": "❌ Ошибка при изменении описания",
                "tj": "❌ Хато дар тағйир додани тавсиф"
            }
            await message.answer(texts[user.language])
    
    # Возвращаемся в меню трек-кодов
    await back_to_track_menu(message, state)

# ========== ЭКСПОРТ В EXCEL ==========

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

async def back_to_track_menu(message: Message, state: FSMContext):
    """Возврат в меню трек-кодов"""
    async for session in get_db():
        user_repo = UserRepository(session)
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

def get_category_name(category, language: str = "ru") -> str:
    """Получение названия категории"""
    if not category:
        return "Не указана" if language == "ru" else "Муайян нашудааст"
    
    category_names = {
        "ru": {
            ProductCategory.ELECTRONICS: "Электроника",
            ProductCategory.CLOTHING: "Одежда",
            ProductCategory.SHOES: "Обувь",
            ProductCategory.HOME_APPLIANCES: "Бытовая техника",
            ProductCategory.BEAUTY: "Косметика",
            ProductCategory.TOYS: "Игрушки",
            ProductCategory.AUTOMOTIVE: "Автозапчасти",
            ProductCategory.SPORTS: "Спорттовары",
            ProductCategory.OTHER: "Другое"
        },
        "tj": {
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
    }
    
    return category_names[language].get(category, str(category))

# ========== INLINE CALLBACK ОБРАБОТЧИКИ ==========



@track_codes_router.callback_query(F.data.startswith("prev_page_"))
async def prev_page_callback(callback: CallbackQuery, state: FSMContext):
    """Обработка перехода на предыдущую страницу"""
    page_num = int(callback.data.split("_")[2])
    
    data = await state.get_data()
    products = data.get('user_products', [])
    total = data.get('products_total', 0)
    
    if products:
        page_size = 5
        start_idx = (page_num - 1) * page_size
        end_idx = min(start_idx + page_size, len(products))
        
        await state.update_data(products_page=page_num)
        await show_products_page(callback.message, state, products[start_idx:end_idx], page_num, total)
    
    await callback.answer()


@track_codes_router.callback_query(F.data.startswith("next_page_"))
async def next_page_callback(callback: CallbackQuery, state: FSMContext):
    """Обработка перехода на следующую страницу"""
    page_num = int(callback.data.split("_")[2])
    
    data = await state.get_data()
    products = data.get('user_products', [])
    total = data.get('products_total', 0)
    
    if products:
        page_size = 5
        start_idx = (page_num - 1) * page_size
        end_idx = min(start_idx + page_size, len(products))
        
        await state.update_data(products_page=page_num)
        await show_products_page(callback.message, state, products[start_idx:end_idx], page_num, total)
    
    await callback.answer()

@track_codes_router.callback_query(F.data.startswith("view_product_"))
async def view_product_callback(callback: CallbackQuery, state: FSMContext):
    """Просмотр детальной информации о товаре"""
    product_id = int(callback.data.split("_")[2])
    
    async for session in get_db():
        product_repo = ProductRepository(session)
        user_repo = UserRepository(session)
        
        user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
        # Получаем товар по ID (нужно добавить метод в репозиторий)
        result = await session.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()
        
        if not product:
            await callback.answer("Товар не найден")
            return
        
        # Проверяем, принадлежит ли товар пользователю
        if product.user_id != user.id:
            await callback.answer("Этот товар не принадлежит вам")
            return
        
        # Формируем детальную информацию
        status_text = get_status_text(product.status.value, user.language)
        category_name = get_category_name(product.product_category, user.language)
        
        # Особые свойства
        special_props = []
        if product.fragile:
            special_props.append("Хрупкий" if user.language == "ru" else "Нозук")
        if product.has_battery:
            special_props.append("С батареей" if user.language == "ru" else "Бо батарея")
        if product.is_liquid:
            special_props.append("Жидкость" if user.language == "ru" else "Моеъ")
        special_text = ", ".join(special_props) if special_props else ("Нет" if user.language == "ru" else "Не")
        
        text = {
            "ru": f"""📦 <b>Детальная информация о товаре</b>

🎯 <b>Трек-код:</b> <code>{product.track_code}</code>
🏷️ <b>Название:</b> {product.product_name or 'Не указано'}
📂 <b>Категория:</b> {category_name}
📝 <b>Описание:</b> {product.product_description or 'Не указано'}
📍 <b>Статус:</b> {status_text}

🔢 <b>Количество:</b> {product.quantity or 1} шт.
💰 <b>Цена за единицу:</b> ${product.unit_price_usd:.2f}
💵 <b>Общая стоимость:</b> ${product.total_value_usd:.2f}
⚖️ <b>Вес:</b> {product.weight_kg:.2f} кг
⚠️ <b>Особые свойства:</b> {special_text}

📅 <b>Дата добавления:</b> {product.created_at.strftime('%d.%m.%Y %H:%M')}
🆔 <b>ID товара:</b> {product.id}""",
            "tj": f"""📦 <b>Маълумоти тафсилотӣ оид ба маҳсулот</b>

🎯 <b>Рамзи тамошобин:</b> <code>{product.track_code}</code>
🏷️ <b>Ном:</b> {product.product_name or 'Муайян нашудааст'}
📂 <b>Гурӯҳ:</b> {category_name}
📝 <b>Тавсиф:</b> {product.product_description or 'Муайян нашудааст'}
📍 <b>Статус:</b> {status_text}

🔢 <b>Миқдор:</b> {product.quantity or 1} дона
💰 <b>Нарх барои як воҳид:</b> ${product.unit_price_usd:.2f}
💵 <b>Арзиши умумӣ:</b> ${product.total_value_usd:.2f}
⚖️ <b>Вазн:</b> {product.weight_kg:.2f} кг
⚠️ <b>Хусусиятҳои махсус:</b> {special_text}

📅 <b>Сании илова:</b> {product.created_at.strftime('%d.%m.%Y %H:%M')}
🆔 <b>ID маҳсулот:</b> {product.id}"""
        }[user.language]
        
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(
            text="🔙 Назад" if user.language == "ru" else "🔙 Бозгашт",
            callback_data="back_to_products"
        ))
        
        # Если товар можно редактировать (статус "Создан" или "На складе в Китае")
        if product.status in [ProductStatus.CREATED, ProductStatus.CHINA_WAREHOUSE]:
            keyboard.add(InlineKeyboardButton(
                text="✏️ Редактировать" if user.language == "ru" else "✏️ Таҳрир кардан",
                callback_data=f"edit_product_{product.id}"
            ))
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML"
        )
    
    await callback.answer()

@track_codes_router.message(ClientState.edit_product)
async def edit_product_menu(message: Message, state: FSMContext):
    """Обработка меню редактирования товара"""
    if message.text in ["🔙 Назад", "🔙 Бозгашт", "⬅️ Назад", "⬅️ Бозгашт"]:
        await back_to_track_menu(message, state)
        return
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        # Определяем, что хочет изменить пользователь
        edit_options = {
            "ru": {
                "📝 Изменить название": "name",
                "📝 Изменить описание": "description",
                "🔢 Изменить количество": "quantity",
                "💰 Изменить цену": "price",
                "⚖️ Изменить вес": "weight",
                "🏷️ Изменить категорию": "category"
            },
            "tj": {
                "📝 Тағйир додани ном": "name",
                "📝 Тағйир додани тавсиф": "description",
                "🔢 Тағйир додани миқдор": "quantity",
                "💰 Тағйир додани нарх": "price",
                "⚖️ Тағйир додани вазн": "weight",
                "🏷️ Тағйир додани гурӯҳ": "category"
            }
        }
        
        action = edit_options[user.language].get(message.text)
        
        if not action:
            await message.answer("Пожалуйста, выберите действие из меню" if user.language == "ru" else "Лутфан, амалро аз меню интихоб кунед")
            return
        
        # Устанавливаем соответствующее состояние
        if action == "name":
            texts = {
                "ru": "Введите новое название товара:",
                "tj": "Номи нави маҳсулотро ворид кунед:"
            }
            await state.set_state(ClientState.edit_product_name)
            
        elif action == "description":
            texts = {
                "ru": "Введите новое описание товара:",
                "tj": "Тавсифи нави маҳсулотро ворид кунед:"
            }
            await state.set_state(ClientState.edit_product_description)
            
        elif action == "quantity":
            texts = {
                "ru": "Введите новое количество товара:",
                "tj": "Миқдори нави маҳсулотро ворид кунед:"
            }
            await state.set_state(ClientState.edit_product_quantity)
            
        elif action == "price":
            texts = {
                "ru": "Введите новую цену за единицу (в USD):",
                "tj": "Нархи нави барои як воҳидро ворид кунед (дар USD):"
            }
            await state.set_state(ClientState.edit_product_price)
            
        elif action == "weight":
            texts = {
                "ru": "Введите новый вес товара (в кг):",
                "tj": "Вазни нави маҳсулотро ворид кунед (дар кг):"
            }
            await state.set_state(ClientState.edit_product_weight)
            
        elif action == "category":
            texts = {
                "ru": "Выберите новую категорию товара:",
                "tj": "Гурӯҳи нави маҳсулотро интихоб кунед:"
            }
            await message.answer(
                texts[user.language],
                reply_markup=get_product_categories_keyboard(user.language)
            )
            await state.set_state(ClientState.edit_product_category)
            return
        
        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language)
        )

@track_codes_router.callback_query(F.data == "back_to_products")
async def back_to_products_callback(callback: CallbackQuery, state: FSMContext):
    """Возврат к списку товаров"""
    data = await state.get_data()
    products = data.get('user_products', [])
    page = data.get('products_page', 1)
    total = data.get('products_total', 0)
    
    if products:
        page_size = 5
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, len(products))
        
        await show_products_page(callback.message, state, products[start_idx:end_idx], page, total)
    
    await callback.answer()

@track_codes_router.callback_query(F.data == "back_to_track_menu")
async def back_to_track_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Возврат в меню трек-кодов через callback"""
    await back_to_track_menu(callback.message, state)
    await callback.answer()