"""
Обработчики массовой загрузки трек-кодов для администраторов
"""
import logging
import os
from datetime import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile

from database.session import async_session_maker
from database.repository import ProductRepository, UserTrackCodeRepository, UserRepository
from database.models import User
from utils.states import AdminStates
from keyboards.admin import get_bulk_import_keyboard, get_back_to_admin_keyboard
from services.bulk_import import BulkImportService
from services.excel_template import generate_import_template
from config import settings

logger = logging.getLogger(__name__)
bulk_import_router = Router()


@bulk_import_router.callback_query(F.data == "download_excel_template")
async def download_excel_template(callback: CallbackQuery, state: FSMContext):
    """Скачивание шаблона Excel"""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    await callback.answer("⏳ Генерация шаблона...")

    try:
        # Генерируем шаблон
        template_path = generate_import_template(language="ru")

        # Отправляем файл
        document = FSInputFile(template_path, filename="import_template.xlsx")

        await callback.message.answer_document(
            document=document,
            caption="📥 <b>Шаблон для импорта трек-кодов</b>\n\n"
                    "📋 Заполните файл данными и загрузите обратно через меню "
                    "'📄 Excel файл'\n\n"
                    "ℹ️ В файле есть лист с подробными инструкциями.",
            parse_mode="HTML"
        )

        logger.info(f"Администратор {callback.from_user.id} скачал шаблон Excel")

    except Exception as e:
        logger.error(f"Ошибка генерации шаблона: {e}", exc_info=True)
        await callback.message.answer(
            f"❌ Ошибка при генерации шаблона:\n{str(e)}",
            reply_markup=get_back_to_admin_keyboard()
        )


@bulk_import_router.callback_query(F.data == "admin_bulk_import")
async def bulk_import_start(callback: CallbackQuery, state: FSMContext):
    """Начало массовой загрузки трек-кодов"""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    await callback.message.edit_text(
        "📥 <b>Массовая загрузка трек-кодов</b>\n\n"
        "Выберите способ загрузки:\n\n"
        "📝 <b>Список трек-кодов</b> - введите трек-коды списком через запятую, "
        "точку с запятой или с новой строки\n\n"
        "📄 <b>Excel файл</b> - загрузите файл .xlsx со следующей структурой:\n"
        "   • Колонка A: Трек-код (обязательно)\n"
        "   • Колонка B: Название товара (опционально)\n"
        "   • Колонка C: Категория (опционально)\n"
        "   • Колонка D: Количество (опционально)\n"
        "   • Колонка E: Цена USD (опционально)\n"
        "   • Колонка F: Вес кг (опционально)\n"
        "   • Колонка G: Страна отправления (опционально)\n\n"
        "✍️ <b>Ручной ввод</b> - добавить один трек-код вручную",
        reply_markup=get_bulk_import_keyboard(),
        parse_mode="HTML"
    )

    await state.set_state(AdminStates.BULK_IMPORT_CHOICE)
    await callback.answer()


@bulk_import_router.callback_query(F.data == "bulk_import_text")
async def bulk_import_text_start(callback: CallbackQuery, state: FSMContext):
    """Начало загрузки из текстового списка"""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    await callback.message.edit_text(
        "📝 <b>Массовая загрузка из списка</b>\n\n"
        "Введите трек-коды через запятую, точку с запятой или с новой строки.\n\n"
        "<i>Пример:</i>\n"
        "<code>TRACK001, TRACK002, TRACK003</code>\n"
        "или\n"
        "<code>TRACK001\n"
        "TRACK002\n"
        "TRACK003</code>\n\n"
        "⚠️ Дубликаты будут автоматически пропущены.\n"
        "⚠️ Товары будут созданы с категорией 'Другое' и страной 'China'.",
        reply_markup=get_back_to_admin_keyboard(),
        parse_mode="HTML"
    )

    await state.set_state(AdminStates.BULK_IMPORT_TEXT_INPUT)
    await callback.answer()


@bulk_import_router.message(AdminStates.BULK_IMPORT_TEXT_INPUT)
async def process_bulk_import_text(message: Message, state: FSMContext):
    """Обработка текстового списка трек-кодов"""
    text = message.text.strip()

    if not text:
        await message.answer(
            "❌ Текст не может быть пустым. Введите трек-коды:",
            reply_markup=get_back_to_admin_keyboard()
        )
        return

    # Показываем процесс
    progress_msg = await message.answer("⏳ Обработка списка трек-кодов...")

    async with async_session_maker() as session:
        product_repo = ProductRepository(session)
        import_service = BulkImportService(product_repo)

        # Выполняем импорт
        result = await import_service.import_from_text(
            text=text,
            user_id=message.from_user.id,
            default_category="other",
            default_country="China"
        )

        # Активируем ожидающие трек-коды и уведомляем пользователей
        utc_repo = UserTrackCodeRepository(session)
        user_repo = UserRepository(session)
        total_notified = 0

        for track_code in result.success_codes:
            try:
                pending_user_ids = await utc_repo.activate_pending_track_codes(track_code)

                for uid in pending_user_ids:
                    try:
                        from sqlalchemy import select
                        result_user = await session.execute(
                            select(User).where(User.id == uid)
                        )
                        u = result_user.scalar_one_or_none()
                        if u:
                            notify_text = {
                                "ru": f"📦 Ваш трек-код <code>{track_code}</code> зарегистрирован!\n\n"
                                      f"📍 Статус: Создан",
                                "tj": f"📦 Рамзи тамошобини шумо <code>{track_code}</code> сабт шуд!\n\n"
                                      f"📍 Статус: Сохта шудааст"
                            }
                            await message.bot.send_message(
                                u.telegram_id,
                                notify_text.get(u.language, notify_text["ru"]),
                                parse_mode="HTML"
                            )
                            total_notified += 1
                    except Exception as e:
                        logger.error(f"Ошибка уведомления пользователя {uid}: {e}")
            except Exception as e:
                logger.error(f"Ошибка активации pending трек-кодов для {track_code}: {e}")

    # Удаляем сообщение о прогрессе
    await progress_msg.delete()

    # Формируем итоговый отчёт
    summary = result.get_summary(language="ru")

    if total_notified > 0:
        summary += f"\n\n📨 Уведомлено пользователей: {total_notified}"

    await message.answer(
        summary,
        reply_markup=get_back_to_admin_keyboard(),
        parse_mode="HTML"
    )

    await state.clear()


@bulk_import_router.callback_query(F.data == "bulk_import_excel")
async def bulk_import_excel_start(callback: CallbackQuery, state: FSMContext):
    """Начало загрузки из Excel файла"""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    await callback.message.edit_text(
        "📄 <b>Массовая загрузка из Excel</b>\n\n"
        "Загрузите файл .xlsx со следующей структурой:\n\n"
        "📋 <b>Структура файла (первая строка - заголовки):</b>\n"
        "• Колонка A: <b>Трек-код</b> (обязательно)\n"
        "• Колонка B: Название товара (опционально)\n"
        "• Колонка C: Категория (опционально)\n"
        "• Колонка D: Количество (опционально)\n"
        "• Колонка E: Цена USD (опционально)\n"
        "• Колонка F: Вес кг (опционально)\n"
        "• Колонка G: Страна отправления (опционально)\n\n"
        "📌 <b>Категории:</b> электроника, одежда, обувь, бытовая техника, "
        "косметика, игрушки, автозапчасти, спорттовары, другое\n\n"
        "⚠️ Дубликаты будут автоматически пропущены.",
        reply_markup=get_back_to_admin_keyboard(),
        parse_mode="HTML"
    )

    await state.set_state(AdminStates.BULK_IMPORT_EXCEL_UPLOAD)
    await callback.answer()


@bulk_import_router.message(AdminStates.BULK_IMPORT_EXCEL_UPLOAD, F.document)
async def process_bulk_import_excel(message: Message, state: FSMContext):
    """Обработка Excel файла"""
    document = message.document

    # Проверяем расширение файла
    if not document.file_name.endswith(('.xlsx', '.xls')):
        await message.answer(
            "❌ Неверный формат файла. Загрузите файл .xlsx или .xls",
            reply_markup=get_back_to_admin_keyboard()
        )
        return

    # Проверяем размер файла (максимум 10MB)
    if document.file_size > 10 * 1024 * 1024:
        await message.answer(
            "❌ Файл слишком большой. Максимальный размер: 10 MB",
            reply_markup=get_back_to_admin_keyboard()
        )
        return

    # Показываем процесс
    progress_msg = await message.answer("⏳ Загрузка и обработка файла...")

    # Создаём временную директорию если её нет
    os.makedirs("temp", exist_ok=True)

    # Скачиваем файл
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"temp/import_{timestamp}_{document.file_name}"

    try:
        await message.bot.download(document, destination=file_path)
        logger.info(f"Файл загружен: {file_path}")

        async with async_session_maker() as session:
            product_repo = ProductRepository(session)
            import_service = BulkImportService(product_repo)

            # Выполняем импорт
            result = await import_service.import_from_excel(
                file_path=file_path,
                user_id=message.from_user.id
            )

            # Активируем ожидающие трек-коды и уведомляем пользователей
            utc_repo = UserTrackCodeRepository(session)
            user_repo = UserRepository(session)
            total_notified = 0

            for track_code in result.success_codes:
                try:
                    pending_user_ids = await utc_repo.activate_pending_track_codes(track_code)

                    for uid in pending_user_ids:
                        try:
                            from sqlalchemy import select
                            result_user = await session.execute(
                                select(User).where(User.id == uid)
                            )
                            u = result_user.scalar_one_or_none()
                            if u:
                                notify_text = {
                                    "ru": f"📦 Ваш трек-код <code>{track_code}</code> зарегистрирован!\n\n"
                                          f"📍 Статус: Создан",
                                    "tj": f"📦 Рамзи тамошобини шумо <code>{track_code}</code> сабт шуд!\n\n"
                                          f"📍 Статус: Сохта шудааст"
                                }
                                await message.bot.send_message(
                                    u.telegram_id,
                                    notify_text.get(u.language, notify_text["ru"]),
                                    parse_mode="HTML"
                                )
                                total_notified += 1
                        except Exception as e:
                            logger.error(f"Ошибка уведомления пользователя {uid}: {e}")
                except Exception as e:
                    logger.error(f"Ошибка активации pending трек-кодов для {track_code}: {e}")

        # Удаляем временный файл
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Временный файл удалён: {file_path}")

        # Удаляем сообщение о прогрессе
        await progress_msg.delete()

        # Формируем итоговый отчёт
        summary = result.get_summary(language="ru")

        if total_notified > 0:
            summary += f"\n\n📨 Уведомлено пользователей: {total_notified}"

        await message.answer(
            summary,
            reply_markup=get_back_to_admin_keyboard(),
            parse_mode="HTML"
        )

        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка обработки Excel файла: {e}", exc_info=True)

        # Удаляем временный файл в случае ошибки
        if os.path.exists(file_path):
            os.remove(file_path)

        await progress_msg.delete()
        await message.answer(
            f"❌ Ошибка обработки файла:\n{str(e)}",
            reply_markup=get_back_to_admin_keyboard()
        )
        await state.clear()


@bulk_import_router.message(AdminStates.BULK_IMPORT_EXCEL_UPLOAD)
async def process_bulk_import_excel_invalid(message: Message, state: FSMContext):
    """Обработка неверного типа сообщения при загрузке Excel"""
    await message.answer(
        "❌ Пожалуйста, отправьте файл Excel (.xlsx или .xls)",
        reply_markup=get_back_to_admin_keyboard()
    )


@bulk_import_router.callback_query(F.data == "bulk_import_manual")
async def bulk_import_manual_start(callback: CallbackQuery, state: FSMContext):
    """Ручной ввод одного трек-кода"""
    if not settings.is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return

    await callback.message.edit_text(
        "✍️ <b>Ручной ввод трек-кода</b>\n\n"
        "Введите трек-код товара:\n\n"
        "📝 Требования:\n"
        "• Минимум 6 символов\n"
        "• Максимум 50 символов\n"
        "• Допускаются: буквы (A-Z), цифры (0-9), дефис (-)\n\n"
        "<i>Пример: TRACK12345, CN240215001GN1234</i>",
        reply_markup=get_back_to_admin_keyboard(),
        parse_mode="HTML"
    )

    await state.set_state(AdminStates.BULK_IMPORT_MANUAL_TRACK)
    await callback.answer()


@bulk_import_router.message(AdminStates.BULK_IMPORT_MANUAL_TRACK)
async def process_bulk_import_manual(message: Message, state: FSMContext):
    """Обработка ручного ввода трек-кода"""
    track_code = message.text.strip().upper()

    # Валидация
    from services.bulk_import import TrackCodeValidator
    validator = TrackCodeValidator()

    is_valid, error_msg = validator.validate_track_code(track_code)

    if not is_valid:
        await message.answer(
            f"❌ Невалидный трек-код: {error_msg}\n\n"
            "Попробуйте ещё раз:",
            reply_markup=get_back_to_admin_keyboard()
        )
        return

    # Проверяем на дубликат
    async with async_session_maker() as session:
        product_repo = ProductRepository(session)
        existing = await product_repo.get_product_by_track_code(track_code)

        if existing:
            await message.answer(
                f"⚠️ Товар с трек-кодом <code>{track_code}</code> уже существует в базе данных.\n\n"
                f"📝 Название: {existing.product_name or 'Не указано'}\n"
                f"📊 Статус: {existing.status.value}\n"
                f"📅 Дата создания: {existing.created_at.strftime('%d.%m.%Y %H:%M')}",
                reply_markup=get_back_to_admin_keyboard(),
                parse_mode="HTML"
            )
            await state.clear()
            return

        # Создаём товар с минимальными данными
        try:
            await product_repo.create_product(
                track_code=track_code,
                user_id=message.from_user.id,
                product_name=f"Товар {track_code}",
                product_category="other",
                country_from="China",
                quantity=1,
                unit_price_usd=0.0,
                total_value_usd=0.0,
                weight_kg=0.0
            )

            # Активируем ожидающие трек-коды и уведомляем пользователей
            utc_repo = UserTrackCodeRepository(session)
            pending_user_ids = await utc_repo.activate_pending_track_codes(track_code)

            notified_count = 0
            for uid in pending_user_ids:
                try:
                    from sqlalchemy import select
                    result = await session.execute(
                        select(User).where(User.id == uid)
                    )
                    u = result.scalar_one_or_none()
                    if u:
                        notify_text = {
                            "ru": f"📦 Ваш трек-код <code>{track_code}</code> зарегистрирован!\n\n"
                                  f"📍 Статус: Создан",
                            "tj": f"📦 Рамзи тамошобини шумо <code>{track_code}</code> сабт шуд!\n\n"
                                  f"📍 Статус: Сохта шудааст"
                        }
                        await message.bot.send_message(
                            u.telegram_id,
                            notify_text.get(u.language, notify_text["ru"]),
                            parse_mode="HTML"
                        )
                        notified_count += 1
                except Exception as e:
                    logger.error(f"Ошибка уведомления пользователя {uid}: {e}")

            notify_info = ""
            if notified_count > 0:
                notify_info = f"\n\n📨 Уведомлено пользователей: {notified_count}"

            await message.answer(
                f"✅ Трек-код <code>{track_code}</code> успешно добавлен!\n\n"
                f"📦 Товар создан с базовыми параметрами:\n"
                f"• Название: Товар {track_code}\n"
                f"• Категория: Другое\n"
                f"• Страна: China\n"
                f"• Статус: Создан\n\n"
                f"💡 Вы можете обновить параметры через меню обновления статусов."
                f"{notify_info}",
                reply_markup=get_back_to_admin_keyboard(),
                parse_mode="HTML"
            )

            logger.info(f"Администратор {message.from_user.id} добавил трек-код вручную: {track_code}")

        except Exception as e:
            logger.error(f"Ошибка создания товара: {e}", exc_info=True)
            await message.answer(
                f"❌ Ошибка при создании товара:\n{str(e)}",
                reply_markup=get_back_to_admin_keyboard()
            )

    await state.clear()
