from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from services.admin_report_service import AdminReportService
from database.repository import ProductRepository

router = Router()


@router.message(F.text == "📤 Выгрузить все товары")
async def export_all(message: Message):
    service = AdminReportService(ProductRepository())

    buffer = await service.monthly_report_excel()

    file = BufferedInputFile(
        buffer.read(),
        filename="all_products.xlsx"
    )

    await message.answer_document(file)
