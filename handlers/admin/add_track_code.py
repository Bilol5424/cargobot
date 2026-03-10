"""
Обработчик добавления трек-кода администратором.
Трек-код генерируется автоматически системой.
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select

from database.session import async_session_maker
from database.models import User, Product
from database.repository import ProductRepository
from keyboards.admin import get_admin_main_keyboard
from services.track_code_generator import TrackCodeGenerator
from config import settings

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text.in_(["➕ Добавить трек-код", "📦 Добавить трек-код"]))
async def add_track_code_auto(message: Message):
    """
    Автоматически генерирует трек-код и создает новый Product.
    """
    if not settings.is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещен")
        return

    user_id = message.from_user.id
    admin_role = settings.get_admin_role(user_id)

    try:
        async with async_session_maker() as session:
            # Получаем данные администратора
            admin_user = await session.execute(
                select(User).where(User.telegram_id == user_id)
            )
            admin_user = admin_user.scalar_one_or_none()
            language = admin_user.language if admin_user else "ru"

            # Генерируем уникальный трек-код
            track_code = None
            max_attempts = 10
            attempts = 0

            while attempts < max_attempts:
                generated_code = TrackCodeGenerator.generate_track_code(
                    user_id=user_id,
                    product_type="CN" if admin_role == "admin_cn" else "TJ"
                )

                # Проверяем, нет ли такого трек-кода в базе
                existing_product = await session.execute(
                    select(Product).where(Product.track_code == generated_code)
                )

                if existing_product.scalar_one_or_none() is None:
                    track_code = generated_code
                    break

                attempts += 1

            if track_code is None:
                await message.answer(
                    "❌ Не удалось сгенерировать уникальный трек-код. Попробуйте позже.",
                    reply_markup=get_admin_main_keyboard(role=admin_role, language=language)
                )
                return

            # Определяем страну по роли администратора
            country_from = "China" if admin_role == "admin_cn" else "Tajikistan"

            # Создаем новый Product
            repo = ProductRepository(session)
            product = await repo.create_product(
                track_code=track_code,
                user_id=admin_user.id,
                country_from=country_from
            )

            # Формируем сообщение на нужном языке
            texts = {
                "ru": {
                    "title": "📦 Новый трек-код создан",
                    "track_code": "Трек-код",
                    "status": "Статус",
                    "country": "Страна",
                    "created": "Создан",
                    "china": "Китай",
                    "tajikistan": "Таджикистан",
                },
                "tj": {
                    "title": "📦 Рамзи навъи трек созданишуд",
                    "track_code": "Рамзи трек",
                    "status": "Ҳолат",
                    "country": "Кишвар",
                    "created": "Созданишуд",
                    "china": "Чин",
                    "tajikistan": "Тоҷикистон",
                }
            }

            t = texts.get(language, texts["ru"])
            country_display = t["china"] if country_from == "China" else t["tajikistan"]

            response_text = (
                f"{t['title']}\n\n"
                f"🔐 {t['track_code']}: {product.track_code}\n"
                f"✅ {t['status']}: {t['created']}\n"
                f"🌍 {t['country']}: {country_display}"
            )

            await message.answer(
                response_text,
                reply_markup=get_admin_main_keyboard(role=admin_role, language=language)
            )

            logger.info(f"✅ Администратор {user_id} создал трек-код: {track_code}")

    except Exception as e:
        logger.error(f"❌ Ошибка при добавлении трек-кода: {e}", exc_info=True)

        async with async_session_maker() as session:
            admin_user = await session.execute(
                select(User).where(User.telegram_id == user_id)
            )
            admin_user = admin_user.scalar_one_or_none()
            language = admin_user.language if admin_user else "ru"
            admin_role = settings.get_admin_role(user_id)

        error_texts = {
            "ru": "❌ Ошибка при создании трек-кода",
            "tj": "❌ Хатогӣ дар вақти эҷоди рамзи трек"
        }

        await message.answer(
            error_texts.get(language, error_texts["ru"]),
            reply_markup=get_admin_main_keyboard(role=admin_role, language=language)
        )
