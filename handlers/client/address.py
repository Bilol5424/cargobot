"""
Обработчик меню адресов складов
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.session import get_db
from database.repository import UserRepository
from keyboards.client import get_country_keyboard, get_main_menu_keyboard
from utils.states import ClientState

logger = logging.getLogger(__name__)

# Создаем роутер
address_router = Router()

@address_router.message(ClientState.address_menu)
async def address_handler(message: Message, state: FSMContext):
    """Обработка выбора страны для адреса"""
    logger.info(f"Пользователь {message.from_user.id} в меню адресов: {message.text}")
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            return
        
        # Тексты кнопок
        back_ru = "⬅️ Назад"
        back_tj = "⬅️ Бозгашт"
        
        if message.text in [back_ru, back_tj]:
            await message.answer(
                "Главное меню:" if user.language == "ru" else "Менюи асосӣ:",
                reply_markup=get_main_menu_keyboard(user.language)
            )
            await state.set_state(ClientState.main_menu)
            return
        
        # Адреса складов
        country_addresses = {
            "🇹🇯 Таджикистан": {
                "ru": "📍 <b>Склад в Таджикистане</b>\n\n"
                      "🏢 Адрес: г. Душанбе, ул. Шевченко 45\n"
                      "📞 Телефон: +992 123 45 67 89\n"
                      "⏰ Режим работы: 9:00 - 18:00\n"
                      "📅 Без выходных",
                "tj": "📍 <b>Анбор дар Тоҷикистон</b>\n\n"
                      "🏢 Адрес: Душанбе, кӯчаи Шевченко 45\n"
                      "📞 Телефон: +992 123 45 67 89\n"
                      "⏰ Вақти кор: 9:00 - 18:00\n"
                      "📅 Бе рӯзҳои таътил"
            },
            "🇨🇳 Китай": {
                "ru": "📍 <b>Склад в Китае</b>\n\n"
                      "🏢 Адрес: г. Гуанчжоу, район Байюнь\n"
                      "📞 Телефон: +86 138 0013 8000\n"
                      "⏰ Режим работы: 8:00 - 20:00\n"
                      "📅 Без выходных",
                "tj": "📍 <b>Анбор дар Чин</b>\n\n"
                      "🏢 Адрес: Гуанчжоу, ноҳияи Байюнь\n"
                      "📞 Телефон: +86 138 0013 8000\n"
                      "⏰ Вақти кор: 8:00 - 20:00\n"
                      "📅 Бе рӯзҳои таътил"
            },
            "🇺🇿 Узбекистан": {
                "ru": "📍 <b>Склад в Узбекистане</b>\n\n"
                      "🏢 Адрес: г. Ташкент, ул. Навои 12\n"
                      "📞 Телефон: +998 71 123 45 67\n"
                      "⏰ Режим работы: 9:00 - 18:00\n"
                      "📅 Пн-Пт",
                "tj": "📍 <b>Анбор дар Ӯзбекистон</b>\n\n"
                      "🏢 Адрес: Тошканд, кӯчаи Навоӣ 12\n"
                      "📞 Телефон: +998 71 123 45 67\n"
                      "⏰ Вақти кор: 9:00 - 18:00\n"
                      "📅 Душанбе-Ҷумъа"
            },
            "🇰🇿 Казахстан": {
                "ru": "📍 <b>Склад в Казахстане</b>\n\n"
                      "🏢 Адрес: г. Алматы, ул. Абая 34\n"
                      "📞 Телефон: +7 727 123 45 67\n"
                      "⏰ Режим работы: 9:00 - 19:00\n"
                      "📅 Пн-Сб",
                "tj": "📍 <b>Анбор дар Қазоқистон</b>\n\n"
                      "🏢 Адрес: Олмотӣ, кӯчаи Обой 34\n"
                      "📞 Телефон: +7 727 123 45 67\n"
                      "⏰ Вақти кор: 9:00 - 19:00\n"
                      "📅 Душанбе-Шанбе"
            }
        }
        
        address_info = country_addresses.get(message.text)
        if address_info:
            await message.answer(
                address_info[user.language],
                reply_markup=get_country_keyboard(user.language),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                "Выберите страну из списка:" if user.language == "ru" 
                else "Кишварро аз рӯйхат интихоб кунед:",
                reply_markup=get_country_keyboard(user.language)
            )