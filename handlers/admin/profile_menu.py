from aiogram import Router, F
from aiogram.types import Message

from keyboards.admin_extra import profile_keyboard
from services.admin_profile_service import AdminProfileService
from database.repository import AdminRepository
from database.session import async_session_maker

router = Router()


@router.message(F.text == "👤 Профиль администратора")
async def profile(message: Message):
    async with async_session_maker() as session:
        repo = AdminRepository(session)
        service = AdminProfileService(repo)

        admin = await service.get_profile(message.from_user.id)

        if not admin:
            admin = await repo.create(
                tg_user_id=message.from_user.id,
                name=message.from_user.full_name,
            )

        await message.answer(
            f"ID: {admin.id}\nИмя: {admin.name}",
            reply_markup=profile_keyboard,
        )
