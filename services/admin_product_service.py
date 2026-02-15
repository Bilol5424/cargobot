import logging
from typing import List, Tuple
from database.repository import ProductRepository
from utils.helpers import normalize_track_code

logger = logging.getLogger(__name__)


class AdminProductService:
    def __init__(self, repo: ProductRepository):
        self.repo = repo

    async def add_single(self, track_code: str):
        code = normalize_track_code(track_code)

        if not code:
            raise ValueError("Invalid track code")

        existing = await self.repo.get_by_track_code(code)
        if existing:
            raise ValueError("Duplicate track code")

        product = await self.repo.create(track_code=code)

        logger.info("Product created %s", code)
        return product

    async def add_bulk(self, codes: List[str]) -> Tuple[int, int]:
        success = 0
        failed = 0

        for raw in codes:
            try:
                await self.add_single(raw)
                success += 1
            except Exception:
                failed += 1

        return success, failed
