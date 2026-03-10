from aiogram import Router, F
from aiogram.types import Message
from services.admin_search_service import AdminSearchService
from database.repository import ProductRepository
from database.session import async_session_maker
from keyboards.admin import get_admin_main_keyboard
from config import settings

router = Router()


@router.message(F.text.in_(["🔍 Поиск", "🔍 Ҷустуҷӯ"]))
async def search_menu(message: Message):
    """Меню поиска товара"""
    if not settings.is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещен")
        return

    user_id = message.from_user.id
    async with async_session_maker() as session:
        from database.models import User
        from sqlalchemy import select
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"

    texts = {
        "ru": "🔍 Поиск товара\n\nВведите трек-код для поиска:",
        "tj": "🔍 Ҷустуҷӯи маҳсулот\n\nРамзи трек-кодро барои ҷустуҷӯ дохил кунед:"
    }

    from keyboards.admin import get_back_to_admin_keyboard
    await message.answer(
        texts.get(language, texts["ru"]),
        reply_markup=get_back_to_admin_keyboard(language)
    )


@router.message()
async def search_product(message: Message):
    """Поиск товара по трек-коду"""
    # Игнорируем служебные сообщения
    if message.text.startswith(('🔙', '📊', '📈', '📅', '💾', '➕', '📥', '🔄', '👨‍💼', '🔍', '🇨🇳', '🇹🇯', '⚙️')):
        return

    user_id = message.from_user.id
    if not settings.is_admin(user_id):
        return

    async with async_session_maker() as session:
        from database.models import User
        from sqlalchemy import select
        user = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = user.scalar_one_or_none()
        language = user.language if user else "ru"

        repo = ProductRepository(session)
        service = AdminSearchService(repo)

        product = await service.by_track_code(message.text.strip())

        if not product:
            texts = {
                "ru": f"❌ Товар с трек-кодом '{message.text.strip()}' не найден",
                "tj": f"❌ Маҳсулот бо рамзи '{message.text.strip()}' ёфт нашуд"
            }
            await message.answer(texts.get(language, texts["ru"]))
            return

        # Форматируем информацию о товаре
        status_display = {
            "ru": {
                "created": "📝 Создан",
                "china_warehouse": "🇨🇳 В Китае",
                "in_transit": "✈️ В пути",
                "tajikistan_warehouse": "🇹🇯 Прибыл на склад",
                "ready_for_pickup": "📍 На выдаче",
                "delivered": "✅ Выдан",
                "cancelled": "❌ Отменен",
                "problem": "⚠️ Проблема",
            },
            "tj": {
                "created": "📝 Сохта шуд",
                "china_warehouse": "🇨🇳 Дар Чин",
                "in_transit": "✈️ Дар роҳ",
                "tajikistan_warehouse": "🇹🇯 Дар анбор расид",
                "ready_for_pickup": "📍 Барои супоридан омода",
                "delivered": "✅ Супорида шуд",
                "cancelled": "❌ Бекор шуд",
                "problem": "⚠️ Мушкилот",
            }
        }

        status_name = status_display.get(language, status_display["ru"]).get(
            product.status.value if product.status else "unknown",
            product.status.value if product.status else "Неизвестен"
        )

        texts = {
            "ru": {
                "title": "📦 Информация о товаре",
                "code": "Трек-код",
                "name": "Название",
                "status": "Статус",
                "user": "Пользователь",
                "created": "Создан",
                "updated": "Обновлен"
            },
            "tj": {
                "title": "📦 Маълумот дар бораи маҳсулот",
                "code": "Рамзи трек",
                "name": "Ном",
                "status": "Статус",
                "user": "Корбар",
                "created": "Сохта шуд",
                "updated": "Навсозӣ шуд"
            }
        }

        t = texts.get(language, texts["ru"])

        response = f"{t['title']}\n\n"
        response += f"🔐 {t['code']}: <code>{product.track_code}</code>\n"
        if product.product_name:
            response += f"📝 {t['name']}: {product.product_name}\n"
        response += f"📊 {t['status']}: {status_name}\n"
        if product.user_id:
            response += f"👤 {t['user']} ID: {product.user_id}\n"
        if product.created_at:
            response += f"📅 {t['created']}: {product.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        if product.updated_at:
            response += f"🔄 {t['updated']}: {product.updated_at.strftime('%d.%m.%Y %H:%M')}\n"

        admin_role = settings.get_admin_role(user_id)
        await message.answer(
            response,
            reply_markup=get_admin_main_keyboard(role=admin_role, language=language),
            parse_mode="HTML"
        )
