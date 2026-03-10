"""
Обработчик массового добавления трек-кодов администратором.
Поддерживает два способа:
1. Автоматическая генерация трек-кодов
2. Загрузка из Excel файла
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, Document
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
import pandas as pd
import io
import random
import string

from database.session import async_session_maker
from database.models import User, Product, ProductStatus
from database.repository import ProductRepository
from keyboards.admin import get_admin_main_keyboard
from config import settings

logger = logging.getLogger(__name__)
router = Router()


# ============================================================
# СОСТОЯНИЯ
# ============================================================

class BulkAddStates(StatesGroup):
    waiting_for_choice = State()  # Ожидание выбора способа
    waiting_for_count = State()  # Ожидание количества кодов
    waiting_for_file = State()  # Ожидание файла Excel


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def generate_bulk_track_codes(count: int) -> list[str]:
    """
    Генерирует трек-коды в формате: CG + 8 случайных цифр + CN
    Например: CG12345678CN
    """
    codes = set()
    attempts = 0
    max_attempts = count * 10  # Максимум попыток для уникальности

    while len(codes) < count and attempts < max_attempts:
        random_digits = ''.join(random.choices(string.digits, k=8))
        code = f"CG{random_digits}CN"
        codes.add(code)
        attempts += 1

    return list(codes)


# ============================================================
# ОБРАБОТЧИКИ
# ============================================================

@router.message(F.text.in_(["📥 Массовое добавление", "📥 Боркунии оммавӣ"]))
async def bulk_menu(message: Message, state: FSMContext):
    """Главное меню массового добавления"""
    if not settings.is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещен")
        return

    user_id = message.from_user.id
    async with async_session_maker() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"

    # Тексты
    texts = {
        "ru": {
            "title": "📥 Массовое добавление трек-кодов",
            "description": "Выберите способ добавления:",
            "generate": "🔄 Сгенерировать коды",
            "upload_excel": "📄 Загрузить Excel",
            "back": "🔙 Назад",
        },
        "tj": {
            "title": "📥 Боркунии оммавӣ рамзҳо",
            "description": "Усули илова кардан интихоб кунед:",
            "generate": "🔄 Эҷодкунии рамзҳо",
            "upload_excel": "📄 Боргирии Excel",
            "back": "🔙 Бозгашт",
        }
    }

    t = texts.get(language, texts["ru"])

    # Создаем клавиатуру
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    from aiogram.utils.keyboard import ReplyKeyboardBuilder

    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=t["generate"]),
        KeyboardButton(text=t["upload_excel"]),
        width=2
    )
    builder.row(KeyboardButton(text=t["back"]), width=1)

    await message.answer(
        f"{t['title']}\n\n{t['description']}",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

    await state.set_state(BulkAddStates.waiting_for_choice)


@router.message(BulkAddStates.waiting_for_choice, F.text.in_(["🔄 Сгенерировать коды", "🔄 Эҷодкунии рамзҳо"]))
async def choose_generate(message: Message, state: FSMContext):
    """Выбран способ генерации кодов"""
    user_id = message.from_user.id
    async with async_session_maker() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"

    texts = {
        "ru": "🔢 Введите количество трек-кодов для генерации (1-1000):",
        "tj": "🔢 Миқдори рамзҳои трек-кодро дохил кунед (1-1000):",
    }

    await message.answer(texts.get(language, texts["ru"]))
    await state.set_state(BulkAddStates.waiting_for_count)


@router.message(BulkAddStates.waiting_for_choice, F.text.in_(["📄 Загрузить Excel", "📄 Боргирии Excel"]))
async def choose_upload(message: Message, state: FSMContext):
    """Выбран способ загрузки Excel"""
    user_id = message.from_user.id
    async with async_session_maker() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"

    texts = {
        "ru": "📎 Отправьте Excel файл с колонкой трек-кодов (название колонки: 'track_code')",
        "tj": "📎 Файли Excel бо сутуни рамзҳо фиристед (номи сутун: 'track_code')",
    }

    await message.answer(texts.get(language, texts["ru"]))
    await state.set_state(BulkAddStates.waiting_for_file)


@router.message(BulkAddStates.waiting_for_count)
async def process_generate_count(message: Message, state: FSMContext):
    """Обработка введенного количества"""
    user_id = message.from_user.id

    async with async_session_maker() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"
        admin_role = settings.get_admin_role(user_id)

    texts = {
        "ru": {
            "error_invalid": "❌ Введите число от 1 до 1000",
            "generating": "⏳ Генерирую {count} трек-кодов...",
            "checking": "🔍 Проверяю уникальность...",
            "creating": "💾 Создаю записи в БД...",
            "success": "✅ Массовое добавление завершено",
            "count": "Сгенерировано кодов",
            "added": "Добавлено в БД",
            "duplicates": "Найдено дубликатов",
            "title": "📥 Результаты массового добавления",
        },
        "tj": {
            "error_invalid": "❌ Ададро аз 1 то 1000 дохил кунед",
            "generating": "⏳ {count} рамз эҷод мекунам...",
            "checking": "🔍 Бипарвоии ягонагӣ идҷора...",
            "creating": "💾 Сабтҳо дар БД эҷод карда ҳастам...",
            "success": "✅ Боркунии оммавӣ анҷом ёфт",
            "count": "Рамзҳо эҷодшуда",
            "added": "Ба БД илова шуда",
            "duplicates": "Дубликатҳо ёфтшуда",
            "title": "📥 Натичаҳои боркунии оммавӣ",
        }
    }

    t = texts.get(language, texts["ru"])

    # Проверка корректности ввода
    try:
        count = int(message.text)
        if count < 1 or count > 1000:
            await message.answer(t["error_invalid"])
            return
    except ValueError:
        await message.answer(t["error_invalid"])
        return

    # Отправляем статус прогресса
    status_msg = await message.answer(t["generating"].format(count=count))

    try:
        async with async_session_maker() as session:
            repo = ProductRepository(session)

            # 1. Генерируем коды
            generated_codes = generate_bulk_track_codes(count)

            # Обновляем сообщение о прогрессе
            await message.bot.edit_message_text(
                t["checking"],
                chat_id=message.chat.id,
                message_id=status_msg.message_id
            )

            # 2. Проверяем уникальность и создаем
            added_count = 0
            duplicate_count = 0

            await message.bot.edit_message_text(
                t["creating"],
                chat_id=message.chat.id,
                message_id=status_msg.message_id
            )

            for code in generated_codes:
                # Проверяем, есть ли уже такой код
                existing = await session.execute(
                    select(Product).where(Product.track_code == code)
                )

                if existing.scalar_one_or_none() is None:
                    # Создаем новый Product
                    await repo.create_product(
                        track_code=code,
                        user_id=None,  # Не привязан к пользователю
                        country_from="China"
                    )
                    added_count += 1
                else:
                    duplicate_count += 1

            # Формируем результат
            result_text = (
                f"{t['title']}\n\n"
                f"📊 {t['count']}: {len(generated_codes)}\n"
                f"✅ {t['added']}: {added_count}\n"
                f"⚠️  {t['duplicates']}: {duplicate_count}\n\n"
                f"{t['success']}"
            )

            await message.bot.edit_message_text(
                result_text,
                chat_id=message.chat.id,
                message_id=status_msg.message_id
            )

            # Отправляем Excel файл со сгенерированными кодами
            await send_generated_codes_excel(
                message,
                generated_codes,
                added_count,
                duplicate_count,
                language
            )

            # Отправляем клавиатуру админа
            await message.answer(
                "🛠 Админ-панель",
                reply_markup=get_admin_main_keyboard(role=admin_role, language=language)
            )

            logger.info(f"✅ Администратор {user_id} сгенерировал {added_count} трек-кодов")

    except Exception as e:
        logger.error(f"❌ Ошибка при генерации трек-кодов: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {str(e)[:100]}")

    await state.clear()


@router.message(BulkAddStates.waiting_for_file, F.document)
async def process_excel_file(message: Message, state: FSMContext):
    """Обработка загруженного Excel файла"""
    user_id = message.from_user.id

    async with async_session_maker() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"
        admin_role = settings.get_admin_role(user_id)

    texts = {
        "ru": {
            "error_format": "❌ Ошибка формата файла (используйте Excel)",
            "error_no_column": "❌ Колонка 'track_code' не найдена в файле",
            "processing": "⏳ Обрабатываю файл...",
            "checking": "🔍 Проверяю уникальность...",
            "creating": "💾 Создаю записи в БД...",
            "success": "✅ Загрузка Excel завершена",
            "title": "📥 Результаты загрузки Excel",
            "total": "Всего кодов в файле",
            "added": "Добавлено в БД",
            "duplicates": "Найдено дубликатов",
            "errors": "Ошибок",
        },
        "tj": {
            "error_format": "❌ Хатогии формати файл (Excel истифода баред)",
            "error_no_column": "❌ Сутуни 'track_code' дар файл ёфт нашуд",
            "processing": "⏳ Файл кор гируда...",
            "checking": "🔍 Бипарвоии ягонагӣ идҷора...",
            "creating": "💾 Сабтҳо дар БД эҷод карда ҳастам...",
            "success": "✅ Боргирии Excel анҷом ёфт",
            "title": "📥 Натичаҳои боргирии Excel",
            "total": "Ҳамаи рамзҳо дар файл",
            "added": "Ба БД илова шуда",
            "duplicates": "Дубликатҳо ёфтшуда",
            "errors": "Хатогиҳо",
        }
    }

    t = texts.get(language, texts["ru"])

    try:
        # Скачиваем файл правильным способом
        file = await message.bot.get_file(message.document.file_id)
        file_content = await message.bot.download_file(file.file_path)

        # Отправляем статус
        status_msg = await message.answer(t["processing"])

        # Читаем Excel
        try:
            df = pd.read_excel(io.BytesIO(file_content.read()))
        except Exception as e:
            await message.answer(f"{t['error_format']}: {str(e)[:50]}")
            await state.clear()
            return

        # Проверяем наличие колонки
        if 'track_code' not in df.columns:
            await message.answer(t["error_no_column"])
            await state.clear()
            return

        # Извлекаем трек-коды
        track_codes = df['track_code'].astype(str).tolist()
        track_codes = [code.strip() for code in track_codes if code and str(code).lower() != 'nan']

        # Обновляем прогресс
        await message.bot.edit_message_text(
            t["checking"],
            chat_id=message.chat.id,
            message_id=status_msg.message_id
        )

        async with async_session_maker() as session:
            repo = ProductRepository(session)

            added_count = 0
            duplicate_count = 0
            error_count = 0

            await message.bot.edit_message_text(
                t["creating"],
                chat_id=message.chat.id,
                message_id=status_msg.message_id
            )

            for code in track_codes:
                try:
                    # Проверяем уникальность
                    existing = await session.execute(
                        select(Product).where(Product.track_code == code)
                    )

                    if existing.scalar_one_or_none() is None:
                        # Создаем новый Product
                        await repo.create_product(
                            track_code=code,
                            user_id=None,
                            country_from="China"
                        )
                        added_count += 1
                    else:
                        duplicate_count += 1
                except Exception as e:
                    logger.error(f"Ошибка при добавлении {code}: {e}")
                    error_count += 1

            # Формируем результат
            result_text = (
                f"{t['title']}\n\n"
                f"📊 {t['total']}: {len(track_codes)}\n"
                f"✅ {t['added']}: {added_count}\n"
                f"⚠️  {t['duplicates']}: {duplicate_count}\n"
                f"❌ {t['errors']}: {error_count}\n\n"
                f"{t['success']}"
            )

            await message.bot.edit_message_text(
                result_text,
                chat_id=message.chat.id,
                message_id=status_msg.message_id
            )

            # Отправляем отчет в виде файла
            await send_upload_report_excel(
                message,
                track_codes,
                added_count,
                duplicate_count,
                error_count,
                language
            )

            # Отправляем клавиатуру админа
            await message.answer(
                "🛠 Админ-панель",
                reply_markup=get_admin_main_keyboard(role=admin_role, language=language)
            )

            logger.info(f"✅ Администратор {user_id} загрузил Excel: +{added_count}, дубликатов: {duplicate_count}")

    except Exception as e:
        logger.error(f"❌ Ошибка при обработке Excel: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка: {str(e)[:100]}")

    await state.clear()


@router.message(BulkAddStates.waiting_for_file)
async def invalid_file(message: Message):
    """Обработка невалидного файла"""
    user_id = message.from_user.id
    async with async_session_maker() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"

    texts = {
        "ru": "📎 Отправьте Excel файл",
        "tj": "📎 Файли Excel фиристед",
    }

    await message.answer(texts.get(language, texts["ru"]))


@router.message(BulkAddStates.waiting_for_choice, F.text.in_(["🔙 Назад", "🔙 Бозгашт"]))
async def back_to_admin(message: Message, state: FSMContext):
    """Возврат в админ-панель"""
    user_id = message.from_user.id
    admin_role = settings.get_admin_role(user_id)

    async with async_session_maker() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"

    await message.answer(
        "🛠 Админ-панель",
        reply_markup=get_admin_main_keyboard(role=admin_role, language=language)
    )

    await state.clear()


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ЭКСПОРТА
# ============================================================

async def send_generated_codes_excel(message, codes, added, duplicates, language):
    """Отправляет Excel файл с сгенерированными кодами"""
    try:
        # Создаем DataFrame
        df = pd.DataFrame({
            'track_code': codes,
            'status': ['CREATED'] * len(codes),
            'country': ['China'] * len(codes),
        })

        # Сохраняем в Excel
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, sheet_name='TrackCodes')
        excel_buffer.seek(0)

        # Создаем текст для файла
        texts = {
            "ru": f"generated_track_codes_{added}_{duplicates}.xlsx",
            "tj": f"generated_track_codes_{added}_{duplicates}.xlsx",
        }

        filename = texts.get(language, texts["ru"])

        # Отправляем файл
        from aiogram.types import BufferedInputFile
        file = BufferedInputFile(
            excel_buffer.getvalue(),
            filename=filename
        )

        await message.bot.send_document(
            chat_id=message.chat.id,
            document=file,
            caption="📊 Список сгенерированных трек-кодов"
        )
    except Exception as e:
        logger.error(f"Ошибка при создании Excel: {e}")


async def send_upload_report_excel(message, codes, added, duplicates, errors, language):
    """Отправляет отчет о загруженных кодах в Excel"""
    try:
        # Создаем DataFrame с отчетом
        df = pd.DataFrame({
            'track_code': codes,
            'status': ['ADDED' if codes.index(c) < added else 'DUPLICATE' if codes.index(c) < added + duplicates else 'ERROR' for c in codes],
        })

        # Сохраняем в Excel
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, sheet_name='Report')
        excel_buffer.seek(0)

        filename = f"upload_report_{added}_{duplicates}_{errors}.xlsx"

        # Отправляем файл
        from aiogram.types import BufferedInputFile
        file = BufferedInputFile(
            excel_buffer.getvalue(),
            filename=filename
        )

        await message.bot.send_document(
            chat_id=message.chat.id,
            document=file,
            caption="📊 Отчет загрузки"
        )
    except Exception as e:
        logger.error(f"Ошибка при создании отчета: {e}")
