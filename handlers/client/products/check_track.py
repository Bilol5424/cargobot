"""
Проверка трек-кодов
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.session import get_db
from database.repository import UserRepository, ProductRepository
from keyboards.client import get_back_cancel_keyboard, get_track_codes_keyboard
from utils.states import ClientState
from .utils import track_codes_menu_back, get_status_text

logger = logging.getLogger(__name__)
router = Router()

@router.message(ClientState.track_codes_menu, F.text.contains("Проверить трек-код"))
@router.message(ClientState.track_codes_menu, F.text.contains("Тафтиш кардани рамзи тамошобин"))
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
        
@router.message(ClientState.check_track_code)
async def process_check_track_code(message: Message, state: FSMContext):
    """Обработка проверки трек-кода с детальной информацией"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт"]:
        await track_codes_menu_back(message, state)
        return
    
    track_codes = [code.strip() for code in message.text.split(",") if code.strip()]
    
    if not track_codes:
        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(message.from_user.id)
            
            texts = {
                "ru": "❌ Пожалуйста, введите хотя бы один трек-код",
                "tj": "❌ Лутфан, на камтар як рамзи тамошобин ворид кунед"
            }
            await message.answer(texts[user.language])
            return
    
    async for session in get_db():
        user_repo = UserRepository(session)
        product_repo = ProductRepository(session)
        
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        for track_code in track_codes:
            detailed_info = await product_repo.get_detailed_product_info(track_code)
            
            if not detailed_info:
                texts = {
                    "ru": f"❌ Товар с трек-кодом {track_code} не найден",
                    "tj": f"❌ Маҳсулот бо рамзи тамошобин {track_code} ёфт нашуд"
                }
                await message.answer(texts[user.language])
                continue
            
            product = detailed_info["product"]
            product_info = detailed_info["product_info"]
            
            # Формируем детальную информацию
            status_text = get_status_text(product.status.value, user.language)
            
            # Даты
            created_date = product.created_at.strftime("%d.%m.%Y %H:%M")
            arrival_date = product.arrival_date.strftime("%d.%m.%Y") if product.arrival_date else "Не указана"
            expected_date = product.expected_delivery_date.strftime("%d.%m.%Y") if product.expected_delivery_date else "Не указана"
            
            text = {
                "ru": f"""📦 <b>ИНФОРМАЦИЯ О ТОВАРЕ</b>

🎯 <b>Трек-код:</b> <code>{track_code}</code>
🏷️ <b>Название:</b> {product_info['name'] or 'Не указано'}
📂 <b>Категория:</b> {product_info['category'] or 'Не указана'}
📝 <b>Описание:</b> {product_info['description'] or 'Не указано'}

📍 <b>Статус:</b> {status_text}
📅 <b>Дата добавления:</b> {created_date}
📅 <b>Дата прибытия:</b> {arrival_date}
📅 <b>Ожидаемая доставка:</b> {expected_date}

🔢 <b>Количество:</b> {product_info['quantity']} шт.
💰 <b>Цена за единицу:</b> ${product_info['unit_price']:.2f}
💵 <b>Общая стоимость:</b> ${product_info['total_value']:.2f}
⚖️ <b>Вес:</b> {product_info['weight']:.2f} кг
📏 <b>Габариты:</b> {product_info['dimensions'] or 'Не указаны'}

⚠️ <b>Особые свойства:</b> 
{'Хрупкий' if product_info['fragile'] else ''} 
{'С батареей' if product_info['has_battery'] else ''} 
{'Жидкость' if product_info['is_liquid'] else ''} 
{'Нет' if not any([product_info['fragile'], product_info['has_battery'], product_info['is_liquid']]) else ''}""",
                "tj": f"""📦 <b>МАЪЛУМОТ ДАР БОРАИ МАҲСУЛОТ</b>

🎯 <b>Рамзи тамошобин:</b> <code>{track_code}</code>
🏷️ <b>Ном:</b> {product_info['name'] or 'Муайян нашудааст'}
📂 <b>Гурӯҳ:</b> {product_info['category'] or 'Муайян нашудааст'}
📝 <b>Тавсиф:</b> {product_info['description'] or 'Муайян нашудааст'}

📍 <b>Статус:</b> {status_text}
📅 <b>Сании илова:</b> {created_date}
📅 <b>Сании расидан:</b> {arrival_date}
📅 <b>Расониидани интизоршаванда:</b> {expected_date}

🔢 <b>Миқдор:</b> {product_info['quantity']} дона
💰 <b>Нарх барои як воҳид:</b> ${product_info['unit_price']:.2f}
💵 <b>Арзиши умумӣ:</b> ${product_info['total_value']:.2f}
⚖️ <b>Вазн:</b> {product_info['weight']:.2f} кг
📏 <b>Андозаҳо:</b> {product_info['dimensions'] or 'Муайян нашудааст'}

⚠️ <b>Хусусиятҳои махсус:</b> 
{'Нозук' if product_info['fragile'] else ''} 
{'Бо батарея' if product_info['has_battery'] else ''} 
{'Моеъ' if product_info['is_liquid'] else ''} 
{'Не' if not any([product_info['fragile'], product_info['has_battery'], product_info['is_liquid']]) else ''}"""
            }
            
            await message.answer(
                text[user.language],
                parse_mode="HTML"
            )
        
        # Возвращаемся в меню трек-кодов
        from keyboards.client import get_track_codes_keyboard
        await message.answer(
            "📦 Меню трек-кодов:" if user.language == "ru" else "📦 Менюи рамзҳои тамошобин:",
            reply_markup=get_track_codes_keyboard(user.language)
        )
        await state.set_state(ClientState.track_codes_menu)

@router.message(ClientState.check_track_code)
async def process_check_track_code(message: Message, state: FSMContext):
    """Обработка проверки трек-кода"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт"]:
        await track_codes_menu_back(message, state)
        return
    
    track_codes = [code.strip() for code in message.text.split(",") if code.strip()]
    
    if not track_codes:
        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(message.from_user.id)
            
            texts = {
                "ru": "❌ Пожалуйста, введите хотя бы один трек-код",
                "tj": "❌ Лутфан, на камтар як рамзи тамошобин ворид кунед"
            }
            await message.answer(texts[user.language])
            return
    
    async for session in get_db():
        user_repo = UserRepository(session)
        product_repo = ProductRepository(session)
        
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        results = []
        for track_code in track_codes:
            product = await product_repo.get_product_by_track_code(track_code)
            
            if product:
                status_text = get_status_text(product.status.value, user.language)
                results.append(f"✅ <b>{track_code}</b> - {status_text}")
            else:
                results.append(f"❌ <b>{track_code}</b> - не найден" if user.language == "ru" else f"❌ <b>{track_code}</b> - ёфт нашуд")
        
        text = {
            "ru": f"🔍 <b>Результаты проверки:</b>\n\n" + "\n\n".join(results),
            "tj": f"🔍 <b>Натиҷаҳои тафтиш:</b>\n\n" + "\n\n".join(results)
        }
        
        await message.answer(
            text[user.language],
            reply_markup=get_track_codes_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.track_codes_menu)