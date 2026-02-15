from sqlalchemy import select
import logging
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import Product, User, UserTrackCode, UserTrackCodeStatus
from database.session import get_db
from database.repository import UserRepository, ProductRepository, UserTrackCodeRepository
from database.models import ProductStatus
from keyboards.client import get_track_codes_keyboard, get_main_menu_keyboard, get_back_cancel_keyboard
from utils.states import ClientState

logger = logging.getLogger(__name__)

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

        check_track_ru = "Проверить трек-код"
        check_track_tj = "Тафтиш кардани рамзи тамошобин"
        my_tracks_ru = "Мои трек-коды"
        my_tracks_tj = "Рамзҳои тамошобини ман"
        add_pending_ru = "Добавить временный трек-код"
        add_pending_tj = "Илова кардани рамзи интизорӣ"
        back_ru = "⬅️ Назад"
        back_tj = "⬅️ Бозгашт"

        if message.text in [check_track_ru, check_track_tj]:
            await check_track_code_start(message, state)

        elif message.text in [my_tracks_ru, my_tracks_tj]:
            await show_my_track_codes(message, state)

        elif message.text in [add_pending_ru, add_pending_tj]:
            await add_pending_track_code_start(message, state)

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

# ========== ПРОВЕРКА ТРЕК-КОДА ==========

async def check_track_code_start(message: Message, state: FSMContext):
    """Начало проверки трек-кода"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)

        texts = {
            "ru": "🔍 <b>Проверка трек-кода</b>\n\n"
                  "Введите трек-код для проверки:",
            "tj": "🔍 <b>Тафтиш кардани рамзи тамошобин</b>\n\n"
                  "Барои тафтиш рамзи тамошобинро ворид кунед:"
        }

        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.check_track_code)

@track_codes_router.message(ClientState.check_track_code)
async def process_check_track_code(message: Message, state: FSMContext):
    """Обработка проверки трек-кода — поиск в products, авто-привязка к пользователю"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт", "❌ Отмена", "❌ Бекор кардан"]:
        await back_to_track_menu(message, state)
        return

    track_code = message.text.strip()

    if not track_code:
        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(message.from_user.id)
            texts = {
                "ru": "❌ Пожалуйста, введите трек-код",
                "tj": "❌ Лутфан, рамзи тамошобин ворид кунед"
            }
            await message.answer(texts[user.language])
        return

    async for session in get_db():
        user_repo = UserRepository(session)
        product_repo = ProductRepository(session)
        utc_repo = UserTrackCodeRepository(session)

        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        product = await product_repo.get_product_by_track_code(track_code)

        if product:
            status_text = get_status_text(product.status.value, user.language)
            product_name = product.product_name or ("Без названия" if user.language == "ru" else "Беном")

            # Авто-привязка: если пользователь ещё не привязан к этому трек-коду — привязываем как ACTIVE
            if not await utc_repo.user_has_track_code(user.id, track_code):
                await utc_repo.add_user_track_code(user.id, track_code, UserTrackCodeStatus.ACTIVE)
                link_msg = {
                    "ru": "\n\n✅ Трек-код добавлен в ваш список.",
                    "tj": "\n\n✅ Рамзи тамошобин ба рӯйхати шумо илова шуд."
                }
            else:
                link_msg = {"ru": "", "tj": ""}

            text = {
                "ru": f"✅ <b>Трек-код найден!</b>\n\n"
                      f"🎯 Трек-код: <code>{track_code}</code>\n"
                      f"🏷️ Название: {product_name}\n"
                      f"📍 Статус: {status_text}\n"
                      f"📅 Дата: {product.created_at.strftime('%d.%m.%Y')}"
                      f"{link_msg['ru']}",
                "tj": f"✅ <b>Рамзи тамошобин ёфт шуд!</b>\n\n"
                      f"🎯 Рамзи тамошобин: <code>{track_code}</code>\n"
                      f"🏷️ Ном: {product_name}\n"
                      f"📍 Статус: {status_text}\n"
                      f"📅 Сана: {product.created_at.strftime('%d.%m.%Y')}"
                      f"{link_msg['tj']}"
            }[user.language]
        else:
            text = {
                "ru": f"❌ Трек-код <code>{track_code}</code> не найден в системе.\n\n"
                      "Если вы ожидаете этот товар, используйте "
                      "\"Добавить временный трек-код\" чтобы получить уведомление при его поступлении.",
                "tj": f"❌ Рамзи тамошобин <code>{track_code}</code> дар система ёфт нашуд.\n\n"
                      "Агар шумо ин маҳсулотро интизор ҳастед, "
                      "\"Илова кардани рамзи интизорӣ\"-ро истифода баред, то ҳангоми воридшавии он хабар гиред."
            }[user.language]

        await message.answer(
            text,
            reply_markup=get_track_codes_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.track_codes_menu)

# ========== МОИ ТРЕК-КОДЫ ==========

async def show_my_track_codes(message: Message, state: FSMContext):
    """Показать трек-коды пользователя (из user_track_codes с LEFT JOIN на products)"""
    async for session in get_db():
        user_repo = UserRepository(session)
        utc_repo = UserTrackCodeRepository(session)

        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        entries = await utc_repo.get_user_track_codes(user.id)

        if not entries:
            texts = {
                "ru": "📭 У вас пока нет добавленных трек-кодов.\n\n"
                      "Используйте 'Проверить трек-код' или 'Добавить временный трек-код'.",
                "tj": "📭 Шумо то ҳол рамзи тамошобин надоред.\n\n"
                      "'Тафтиш кардани рамзи тамошобин' ё 'Илова кардани рамзи интизорӣ'-ро истифода баред."
            }
            await message.answer(texts[user.language])
            return

        # Пагинация
        page_size = 5
        total = len(entries)
        total_pages = (total + page_size - 1) // page_size

        await state.update_data(
            utc_entries=entries,
            utc_total=total,
            utc_page=1
        )

        await _show_utc_page(message, state, entries[:page_size], 1, total, user.language)


async def _show_utc_page(message: Message, state: FSMContext, entries, page: int, total: int, language: str):
    """Показать страницу трек-кодов пользователя"""
    page_size = 5
    total_pages = (total + page_size - 1) // page_size

    text = {
        "ru": f"📦 <b>Ваши трек-коды (страница {page}/{total_pages}):</b>\n\n",
        "tj": f"📦 <b>Рамзҳои тамошобини шумо (саҳифа {page}/{total_pages}):</b>\n\n"
    }[language]

    start_num = (page - 1) * page_size + 1
    for i, entry in enumerate(entries, start_num):
        utc = entry["user_track_code"]
        product = entry["product"]

        if utc.status == UserTrackCodeStatus.ACTIVE and product:
            status_text = get_status_text(product.status.value, language)
            product_name = product.product_name or ("Без названия" if language == "ru" else "Беном")
            text += f"<b>{i}.</b> <code>{utc.track_code}</code>\n"
            text += f"   🏷️ {product_name}\n"
            text += f"   📍 {status_text}\n"
            text += f"   📅 {utc.created_at.strftime('%d.%m.%Y')}\n\n"
        else:
            pending_label = "⏳ Ожидание" if language == "ru" else "⏳ Интизорӣ"
            text += f"<b>{i}.</b> <code>{utc.track_code}</code>\n"
            text += f"   {pending_label}\n"
            text += f"   📅 {utc.created_at.strftime('%d.%m.%Y')}\n\n"

    keyboard = InlineKeyboardBuilder()

    if page > 1:
        keyboard.add(InlineKeyboardButton(
            text="◀️ Назад" if language == "ru" else "◀️ Бозгашт",
            callback_data=f"utc_prev_{page - 1}"
        ))

    if page < total_pages:
        keyboard.add(InlineKeyboardButton(
            text="Вперед ▶️" if language == "ru" else "Оёд ▶️",
            callback_data=f"utc_next_{page + 1}"
        ))

    keyboard.row(InlineKeyboardButton(
        text="🔙 В меню" if language == "ru" else "🔙 Ба меню",
        callback_data="back_to_track_menu"
    ))

    await message.answer(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )


@track_codes_router.callback_query(F.data.startswith("utc_prev_"))
async def utc_prev_page_callback(callback: CallbackQuery, state: FSMContext):
    page_num = int(callback.data.split("_")[2])
    data = await state.get_data()
    entries = data.get('utc_entries', [])
    total = data.get('utc_total', 0)

    if entries:
        page_size = 5
        start_idx = (page_num - 1) * page_size
        end_idx = min(start_idx + page_size, len(entries))
        await state.update_data(utc_page=page_num)

        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
            await _show_utc_page(callback.message, state, entries[start_idx:end_idx], page_num, total, user.language)

    await callback.answer()


@track_codes_router.callback_query(F.data.startswith("utc_next_"))
async def utc_next_page_callback(callback: CallbackQuery, state: FSMContext):
    page_num = int(callback.data.split("_")[2])
    data = await state.get_data()
    entries = data.get('utc_entries', [])
    total = data.get('utc_total', 0)

    if entries:
        page_size = 5
        start_idx = (page_num - 1) * page_size
        end_idx = min(start_idx + page_size, len(entries))
        await state.update_data(utc_page=page_num)

        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
            await _show_utc_page(callback.message, state, entries[start_idx:end_idx], page_num, total, user.language)

    await callback.answer()


# ========== ДОБАВИТЬ ВРЕМЕННЫЙ ТРЕК-КОД ==========

async def add_pending_track_code_start(message: Message, state: FSMContext):
    """Начало добавления временного трек-кода"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)

        texts = {
            "ru": "📝 <b>Добавление временного трек-кода</b>\n\n"
                  "Введите трек-код, который вы хотите отслеживать.\n"
                  "Вы получите уведомление, когда товар поступит на склад.",
            "tj": "📝 <b>Илова кардани рамзи интизорӣ</b>\n\n"
                  "Рамзи тамошобинеро, ки мехоҳед пайгирӣ кунед, ворид кунед.\n"
                  "Шумо хабар мегиред, вақте ки маҳсулот ба анбор ворид мешавад."
        }

        await message.answer(
            texts[user.language],
            reply_markup=get_back_cancel_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.add_pending_track_code)


@track_codes_router.message(ClientState.add_pending_track_code)
async def process_add_pending_track_code(message: Message, state: FSMContext):
    """Обработка добавления временного трек-кода"""
    if message.text in ["⬅️ Назад", "⬅️ Бозгашт", "❌ Отмена", "❌ Бекор кардан"]:
        await back_to_track_menu(message, state)
        return

    track_code = message.text.strip()

    if not track_code:
        async for session in get_db():
            user_repo = UserRepository(session)
            user = await user_repo.get_user_by_telegram_id(message.from_user.id)
            texts = {
                "ru": "❌ Пожалуйста, введите трек-код",
                "tj": "❌ Лутфан, рамзи тамошобин ворид кунед"
            }
            await message.answer(texts[user.language])
        return

    async for session in get_db():
        user_repo = UserRepository(session)
        product_repo = ProductRepository(session)
        utc_repo = UserTrackCodeRepository(session)

        user = await user_repo.get_user_by_telegram_id(message.from_user.id)

        # Проверяем, не добавлен ли уже
        if await utc_repo.user_has_track_code(user.id, track_code):
            texts = {
                "ru": f"ℹ️ Трек-код <code>{track_code}</code> уже есть в вашем списке.",
                "tj": f"ℹ️ Рамзи тамошобин <code>{track_code}</code> аллакай дар рӯйхати шумо ҳаст."
            }
            await message.answer(
                texts[user.language],
                reply_markup=get_track_codes_keyboard(user.language),
                parse_mode="HTML"
            )
            await state.set_state(ClientState.track_codes_menu)
            return

        # Проверяем, существует ли товар в products
        product = await product_repo.get_product_by_track_code(track_code)

        if product:
            # Товар уже существует — добавляем как ACTIVE
            await utc_repo.add_user_track_code(user.id, track_code, UserTrackCodeStatus.ACTIVE)
            status_text = get_status_text(product.status.value, user.language)
            product_name = product.product_name or ("Без названия" if user.language == "ru" else "Беном")

            texts = {
                "ru": f"✅ Товар с трек-кодом <code>{track_code}</code> найден!\n\n"
                      f"🏷️ Название: {product_name}\n"
                      f"📍 Статус: {status_text}\n\n"
                      f"Трек-код добавлен в ваш список.",
                "tj": f"✅ Маҳсулот бо рамзи тамошобин <code>{track_code}</code> ёфт шуд!\n\n"
                      f"🏷️ Ном: {product_name}\n"
                      f"📍 Статус: {status_text}\n\n"
                      f"Рамзи тамошобин ба рӯйхати шумо илова шуд."
            }
        else:
            # Товар не существует — добавляем как PENDING
            await utc_repo.add_user_track_code(user.id, track_code, UserTrackCodeStatus.PENDING)

            texts = {
                "ru": f"⏳ Трек-код <code>{track_code}</code> добавлен как ожидающий.\n\n"
                      "Вы получите уведомление, когда товар поступит на склад.",
                "tj": f"⏳ Рамзи тамошобин <code>{track_code}</code> ҳамчун интизорӣ илова шуд.\n\n"
                      "Шумо хабар мегиред, вақте ки маҳсулот ба анбор ворид мешавад."
            }

        await message.answer(
            texts[user.language],
            reply_markup=get_track_codes_keyboard(user.language),
            parse_mode="HTML"
        )
        await state.set_state(ClientState.track_codes_menu)


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

async def back_to_track_menu(message: Message, state: FSMContext, telegram_id: int = None):
    """Возврат в меню трек-кодов"""
    async for session in get_db():
        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_telegram_id(telegram_id or message.from_user.id)

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


# ========== INLINE CALLBACK ОБРАБОТЧИКИ ==========

@track_codes_router.callback_query(F.data == "back_to_track_menu")
async def back_to_track_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Возврат в меню трек-кодов через callback"""
    await back_to_track_menu(callback.message, state, telegram_id=callback.from_user.id)
    await callback.answer()
