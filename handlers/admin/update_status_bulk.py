from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from keyboards.admin_extra import status_keyboard
from services.admin_status_service import AdminStatusService
from database.repository import ProductRepository
from database.session import async_session_maker

router = Router()

# Глобальная переменная для хранения выбранного статуса
selected_status = None


@router.message(F.text == "🔄 Массово обновить статус")
async def choose_status(message: Message, state: FSMContext):
    global selected_status
    selected_status = None  # Сбрасываем статус

    await message.answer(
        "Выберите новый статус:",
        reply_markup=status_keyboard
    )


@router.message(F.text.in_(["🚚 В пути", "📦 Прибыл", "✅ Выдан"]))
async def ask_codes(message: Message, state: FSMContext):
    global selected_status

    # Сохраняем выбранный статус
    status_map = {
        "🚚 В пути": "in_transit",
        "📦 Прибыл": "tajikistan_warehouse",
        "✅ Выдан": "delivered"
    }

    selected_status = status_map[message.text]

    await message.answer("Отправьте список трек‑кодов")


@router.message()
async def update_status(message: Message):
    global selected_status

    # Проверяем, что статус выбран и это действительно список трек-кодов
    if not selected_status:
        return

    # Игнорируем короткие сообщения и сообщения, начинающиеся с эмодзи
    if len(message.text.strip()) < 5 or message.text.startswith(('🔙', '📊', '📈', '📅', '💾', '➕', '📥', '🔄', '👨‍💼', '🔍', '🇨🇳', '🇹🇯', '⚙️')):
        return  # Пропускаем неподходящие сообщения

    async with async_session_maker() as session:
        lines = message.text.split()
        repo = ProductRepository(session)
        service = AdminStatusService(repo)

        updated = await service.bulk_update(lines, selected_status)

        await message.answer(f"🔄 Обновлено: {len(updated)} из {len(lines)}")

        # Сбрасываем статус после использования
        selected_status = None
