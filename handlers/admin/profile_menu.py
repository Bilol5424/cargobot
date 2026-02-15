from aiogram import Router, F
from aiogram.types import Message
from keyboards.admin_extra import profile_keyboard
from services.admin_profile_service import AdminProfileService
from database.repository import AdminRepository

router = Router()


@router.message(F.text == "👤 Профиль администратора")
async def profile(message: Message):
    service = AdminProfileService(AdminRepository())

    admin = await service.get_profile(message.from_user.id)

    await message.answer(
        f"ID: {admin.id}\nИмя: {admin.name}",
        reply_markup=profile_keyboard
    )
