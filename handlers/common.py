"""
Общие обработчики для всех пользователей
"""
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove, Contact
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from database.session import get_db
from database.repository import UserRepository
from keyboards.client import get_language_keyboard, get_main_menu_keyboard
from utils.states import LanguageState, ClientState
from config import settings

logger = logging.getLogger(__name__)

# Создаем роутер
common_router = Router()

@common_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    logger.info(f"Команда /start от пользователя {message.from_user.id}")
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)

        if user:
            # Пользователь уже существует
            logger.info(
                f"Пользователь {message.from_user.id} уже зарегистрирован (role={user.role})"
            )

            # ✅ ЕСЛИ АДМИН — показываем админ меню
            if user.role and user.role.value != "client":
                from keyboards.admin import get_admin_main_menu

                await message.answer(
                    get_welcome_text(user.language, is_admin=True),
                    reply_markup=get_admin_main_menu(user.role.value, user.language),
                )
                await state.clear()
                return

            # ✅ ИНАЧЕ — клиент
            await message.answer(
                get_welcome_text(user.language),
                reply_markup=get_main_menu_keyboard(user.language),
            )
            await state.set_state(ClientState.main_menu)
        else:
            # Новый пользователь
            logger.info(f"Новый пользователь {message.from_user.id}")
            await message.answer(
                "🇷🇺 Выберите язык / 🇹🇯 Забони худро интихоб кунед\n\n"
                "🇷🇺 Пожалуйста, выберите язык:\n"
                "🇹🇯 Лутфан, забони худро интихоб кунед:",
                reply_markup=get_language_keyboard()
            )
            await state.set_state(LanguageState.choosing_language)

@common_router.message(LanguageState.choosing_language)
async def process_language_choice(message: Message, state: FSMContext):
    """Обработка выбора языка - ТОЛЬКО выбор языка, не контакты"""
    logger.info(f"Выбор языка: {message.text}")
    
    language_map = {
        "🇷🇺 Русский": "ru",
        "🇷🇺 русский": "ru",
        "🇹🇯 Тоҷикӣ": "tj",
        "🇹🇯 тоҷикӣ": "tj"
    }
    
    chosen_language = language_map.get(message.text)
    
    if not chosen_language:
        # Если это не выбор языка, проверяем, не нажал ли пользователь "Поделиться номером"
        # Это временное сообщение, пока пользователь не выбрал язык
        await message.answer("Пожалуйста, выберите язык из предложенных вариантов.")
        return
    
    async for session in get_db():
        user_repo = UserRepository(session)
        
        # Проверяем, является ли пользователь админом
        is_admin = settings.is_admin(message.from_user.id)
        role = "admin_cn" if is_admin else "client"
        
        user = await user_repo.create_user(
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            language=chosen_language,
            role=role
        )
        
        logger.info(f"Создан пользователь: ID={user.id}, роль={role}, язык={chosen_language}")
        
        if role == "client":
            await message.answer(
                get_welcome_text(chosen_language),
                reply_markup=ReplyKeyboardRemove()
            )
            
            # Запрос номера телефона
            texts = {
                "ru": "Пожалуйста, поделитесь своим номером телефона для авторизации:",
                "tj": "Лутфан, барои авторизатсия рақами телефони худро мубодила кунед:"
            }
            
            keyboard = ReplyKeyboardBuilder()
            keyboard.add(KeyboardButton(
                text="📱 Поделиться номером" if chosen_language == "ru" else "📱 Рақами худро мубодила кунед",
                request_contact=True
            ))
            keyboard.add(KeyboardButton(
                text="❌ Отмена" if chosen_language == "ru" else "❌ Бекор кардан"
            ))
            
            await message.answer(
                texts[chosen_language],
                reply_markup=keyboard.as_markup(resize_keyboard=True)
            )
            
            # Переходим в состояние ожидания контакта
            await state.set_state(ClientState.waiting_for_contact)
            
        else:
            # Админы - сразу в меню
            from keyboards.admin import get_admin_main_menu
            await message.answer(
                get_welcome_text(chosen_language, is_admin=True),
                reply_markup=get_admin_main_menu(role, chosen_language)
            )
            await state.clear()

# Добавим отдельный обработчик для контактов в состоянии ожидания контакта
@common_router.message(ClientState.waiting_for_contact, F.contact)
async def process_contact_in_waiting_state(message: Message, state: FSMContext):
    """Обработка полученного контакта в состоянии ожидания"""
    logger.info(f"Пользователь {message.from_user.id} поделился номером телефона (в состоянии ожидания)")
    
    async for session in get_db():
        user_repo = UserRepository(session)
        
        # Получаем пользователя
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        if not user:
            # Если пользователь не найден, создаем его с языком по умолчанию
            await message.answer("Ошибка: пользователь не найден. Пожалуйста, начните с /start")
            return
        
        # Обновляем номер телефона
        await user_repo.update_user_profile(
            telegram_id=message.from_user.id,
            phone=message.contact.phone_number
        )
        
        await message.answer(
            get_welcome_text(user.language),
            reply_markup=get_main_menu_keyboard(user.language)
        )
        await state.set_state(ClientState.main_menu)

# Также оставим общий обработчик контактов на всякий случай
@common_router.message(F.contact)
async def process_contact_general(message: Message, state: FSMContext):
    """Общий обработчик полученного контакта"""
    logger.info(f"Пользователь {message.from_user.id} поделился номером телефона (общий обработчик)")
    
    async for session in get_db():
        user_repo = UserRepository(session)
        
        # Проверяем, есть ли пользователь
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if not user:
            # Если пользователя нет, просим начать с /start
            await message.answer("Пожалуйста, сначала выберите язык с помощью команды /start")
            return
        
        # Обновляем номер телефона
        await user_repo.update_user_profile(
            telegram_id=message.from_user.id,
            phone=message.contact.phone_number
        )
        
        # Обновляем пользователя
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        await message.answer(
            get_welcome_text(user.language),
            reply_markup=get_main_menu_keyboard(user.language)
        )
        await state.set_state(ClientState.main_menu)

@common_router.message(F.text.contains("❌"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Обработка отмены"""
    logger.info(f"Пользователь {message.from_user.id} нажал отмену")
    
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        
        if user:
            await message.answer(
                "Действие отменено. Главное меню:" if user.language == "ru" else "Амал бекор карда шуд. Менюи асосӣ:",
                reply_markup=get_main_menu_keyboard(user.language)
            )
            await state.set_state(ClientState.main_menu)
        else:
            # Если пользователя нет, просим начать заново
            await message.answer("Пожалуйста, начните с команды /start")

def get_welcome_text(language: str = "ru", is_admin: bool = False):
    """Получение приветственного текста"""
    if is_admin:
        return {
            "ru": "Добро пожаловать в панель администратора!",
            "tj": "Ба панели администратор хуш омадед!"
        }[language]
    else:
        return {
            "ru": "Добро пожаловать! Выберите действие из меню:",
            "tj": "Хуш омадед! Амалро аз меню интихоб кунед:"
        }[language]