from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from services.admin_report_service import AdminReportService
from database.repository import ProductRepository

router = Router()


@router.message(F.text == "📊 Месячный отчёт")
async def report(message: Message):
    service = AdminReportService(ProductRepository())

    buffer = await service.monthly_report_excel()

    file = BufferedInputFile(
        buffer.read(),
        filename="monthly_report.xlsx"
    )

    await message.answer_document(file)
