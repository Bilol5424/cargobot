"""
Обработчики массовой загрузки трек-кодов (reply-клавиатура)
"""
import logging
import os
from datetime import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile
from sqlalchemy.future import select

from database.session import async_session_maker
from database.repository import ProductRepository, UserTrackCodeRepository
from database.models import User
from utils.states import AdminStates
from keyboards.admin import get_bulk_import_keyboard, get_back_to_admin_keyboard, get_admin_main_keyboard
from services.bulk_import import BulkImportService
from services.excel_template import generate_import_template
from config import settings

logger = logging.getLogger(__name__)
bulk_import_router = Router()


@bulk_import_router.message(F.text == "📥 Массовая загрузка")
async def bulk_import_start(message: Message, state: FSMContext):
    if not settings.is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещен")
        return

    await message.answer(
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


@bulk_import_router.message(AdminStates.BULK_IMPORT_CHOICE, F.text == "📝 Список трек-кодов")
async def bulk_import_text_start(message: Message, state: FSMContext):
    await message.answer(
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


@bulk_import_router.message(AdminStates.BULK_IMPORT_TEXT_INPUT)
async def process_bulk_import_text(message: Message, state: FSMContext):
    if message.text in ("🔙 Назад", "🔙 Бозгашт", "🔙 Назад в админ-панель"):
        # Возврат в главное меню администратора
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
        return

    text = message.text.strip()
    if not text:
        await message.answer(
            "❌ Текст не может быть пустым. Введите трек-коды:",
            reply_markup=get_back_to_admin_keyboard()
        )
        return

    progress_msg = await message.answer("⏳ Обработка списка трек-кодов...")

    async with async_session_maker() as session:
        product_repo = ProductRepository(session)
        import_service = BulkImportService(product_repo)
        result = await import_service.import_from_text(
            text=text,
            user_id=message.from_user.id,
            default_category="other",
            default_country="China"
        )

        utc_repo = UserTrackCodeRepository(session)
        total_notified = 0
        for track_code in result.success_codes:
            try:
                pending_user_ids = await utc_repo.activate_pending_track_codes(track_code)
                for uid in pending_user_ids:
                    try:
                        u = await session.get(User, uid)
                        if u:
                            notify_text = {
                                "ru": f"📦 Ваш трек-код <code>{track_code}</code> зарегистрирован!\n\n📍 Статус: Создан",
                                "tj": f"📦 Рамзи тамошобини шумо <code>{track_code}</code> сабт шуд!\n\n📍 Статус: Сохта шудааст"
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
                logger.error(f"Ошибка активации pending для {track_code}: {e}")

    await progress_msg.delete()
    summary = result.get_summary(language="ru")
    if total_notified > 0:
        summary += f"\n\n📨 Уведомлено пользователей: {total_notified}"

    await message.answer(summary, reply_markup=get_back_to_admin_keyboard(), parse_mode="HTML")
    await state.clear()


@bulk_import_router.message(AdminStates.BULK_IMPORT_CHOICE, F.text == "📄 Excel файл")
async def bulk_import_excel_start(message: Message, state: FSMContext):
    await message.answer(
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


@bulk_import_router.message(AdminStates.BULK_IMPORT_EXCEL_UPLOAD, F.document)
async def process_bulk_import_excel(message: Message, state: FSMContext):
    document = message.document
    if not document.file_name.endswith(('.xlsx', '.xls')):
        await message.answer(
            "❌ Неверный формат файла. Загрузите файл .xlsx или .xls",
            reply_markup=get_back_to_admin_keyboard()
        )
        return
    if document.file_size > 10 * 1024 * 1024:
        await message.answer(
            "❌ Файл слишком большой. Максимальный размер: 10 MB",
            reply_markup=get_back_to_admin_keyboard()
        )
        return

    progress_msg = await message.answer("⏳ Загрузка и обработка файла...")
    os.makedirs("temp", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"temp/import_{timestamp}_{document.file_name}"

    try:
        await message.bot.download(document, destination=file_path)
        async with async_session_maker() as session:
            product_repo = ProductRepository(session)
            import_service = BulkImportService(product_repo)
            result = await import_service.import_from_excel(
                file_path=file_path,
                user_id=message.from_user.id
            )

            utc_repo = UserTrackCodeRepository(session)
            total_notified = 0
            for track_code in result.success_codes:
                pending_user_ids = await utc_repo.activate_pending_track_codes(track_code)
                for uid in pending_user_ids:
                    try:
                        u = await session.get(User, uid)
                        if u:
                            notify_text = {
                                "ru": f"📦 Ваш трек-код <code>{track_code}</code> зарегистрирован!\n\n📍 Статус: Создан",
                                "tj": f"📦 Рамзи тамошобини шумо <code>{track_code}</code> сабт шуд!\n\n📍 Статус: Сохта шудааст"
                            }
                            await message.bot.send_message(
                                u.telegram_id,
                                notify_text.get(u.language, notify_text["ru"]),
                                parse_mode="HTML"
                            )
                            total_notified += 1
                    except Exception as e:
                        logger.error(f"Ошибка уведомления пользователя {uid}: {e}")

        if os.path.exists(file_path):
            os.remove(file_path)
        await progress_msg.delete()
        summary = result.get_summary(language="ru")
        if total_notified > 0:
            summary += f"\n\n📨 Уведомлено пользователей: {total_notified}"
        await message.answer(summary, reply_markup=get_back_to_admin_keyboard(), parse_mode="HTML")
        await state.clear()
    except Exception as e:
        logger.error(f"Ошибка обработки Excel: {e}", exc_info=True)
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
    await message.answer(
        "❌ Пожалуйста, отправьте файл Excel (.xlsx или .xls)",
        reply_markup=get_back_to_admin_keyboard()
    )


@bulk_import_router.message(AdminStates.BULK_IMPORT_CHOICE, F.text == "📥 Скачать шаблон Excel")
async def download_excel_template(message: Message, state: FSMContext):
    if not settings.is_admin(message.from_user.id):
        return
    try:
        template_path = generate_import_template(language="ru")
        document = FSInputFile(template_path, filename="import_template.xlsx")
        await message.answer_document(
            document=document,
            caption="📥 <b>Шаблон для импорта трек-кодов</b>\n\n"
                    "📋 Заполните файл данными и загрузите обратно через меню "
                    "'📄 Excel файл'\n\n"
                    "ℹ️ В файле есть лист с подробными инструкциями.",
            parse_mode="HTML"
        )
        logger.info(f"Админ {message.from_user.id} скачал шаблон Excel")
    except Exception as e:
        logger.error(f"Ошибка генерации шаблона: {e}", exc_info=True)
        await message.answer(
            f"❌ Ошибка при генерации шаблона:\n{str(e)}",
            reply_markup=get_back_to_admin_keyboard()
        )


@bulk_import_router.message(AdminStates.BULK_IMPORT_CHOICE, F.text == "✍️ Ручной ввод трек-кода")
async def bulk_import_manual_start(message: Message, state: FSMContext):
    await message.answer(
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


@bulk_import_router.message(AdminStates.BULK_IMPORT_MANUAL_TRACK)
async def process_bulk_import_manual(message: Message, state: FSMContext):
    if message.text in ("🔙 Назад", "🔙 Бозгашт", "🔙 Назад в админ-панель"):
        # Возврат в главное меню администратора
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
        return

    track_code = message.text.strip().upper()
    from services.bulk_import import TrackCodeValidator
    valid, err = TrackCodeValidator.validate_track_code(track_code)
    if not valid:
        await message.answer(
            f"❌ Невалидный трек-код: {err}\n\nПопробуйте ещё раз:",
            reply_markup=get_back_to_admin_keyboard()
        )
        return

    async with async_session_maker() as session:
        product_repo = ProductRepository(session)
        existing = await product_repo.get_product_by_track_code(track_code)
        if existing:
            await message.answer(
                f"⚠️ Товар с трек-кодом <code>{track_code}</code> уже существует.\n\n"
                f"📝 Название: {existing.product_name or 'Не указано'}\n"
                f"📊 Статус: {existing.status.value}\n"
                f"📅 Дата создания: {existing.created_at.strftime('%d.%m.%Y %H:%M')}",
                reply_markup=get_back_to_admin_keyboard(),
                parse_mode="HTML"
            )
            await state.clear()
            return

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

            utc_repo = UserTrackCodeRepository(session)
            pending_user_ids = await utc_repo.activate_pending_track_codes(track_code)
            notified_count = 0
            for uid in pending_user_ids:
                u = await session.get(User, uid)
                if u:
                    notify_text = {
                        "ru": f"📦 Ваш трек-код <code>{track_code}</code> зарегистрирован!\n\n📍 Статус: Создан",
                        "tj": f"📦 Рамзи тамошобини шумо <code>{track_code}</code> сабт шуд!\n\n📍 Статус: Сохта шудааст"
                    }
                    await message.bot.send_message(
                        u.telegram_id,
                        notify_text.get(u.language, notify_text["ru"]),
                        parse_mode="HTML"
                    )
                    notified_count += 1

            notify_info = f"\n\n📨 Уведомлено пользователей: {notified_count}" if notified_count else ""
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
            logger.info(f"Админ {message.from_user.id} добавил трек-код вручную: {track_code}")
        except Exception as e:
            logger.error(f"Ошибка создания товара: {e}", exc_info=True)
            await message.answer(
                f"❌ Ошибка при создании товара:\n{str(e)}",
                reply_markup=get_back_to_admin_keyboard()
            )
    await state.clear()