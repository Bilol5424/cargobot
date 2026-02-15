import io
import pandas as pd
from database.repository import ProductRepository


class AdminReportService:
    def __init__(self, repo: ProductRepository):
        self.repo = repo

    async def monthly_report_excel(self):
        products = await self.repo.get_all()

        data = [
            {
                "Track Code": p.track_code,
                "Status": p.status,
                "Created": p.created_at,
            }
            for p in products
        ]

        df = pd.DataFrame(data)

        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)

        return buffer
