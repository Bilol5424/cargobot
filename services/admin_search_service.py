from database.repository import ProductRepository


class AdminSearchService:
    def __init__(self, repo: ProductRepository):
        self.repo = repo

    async def by_track_code(self, code: str):
        return await self.repo.get_by_track_code(code)
