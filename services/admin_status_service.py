import logging
from typing import List
from database.repository import ProductRepository

logger = logging.getLogger(__name__)


class AdminStatusService:
    def __init__(self, repo: ProductRepository):
        self.repo = repo

    async def bulk_update(self, codes: List[str], status: str):
        updated = []

        for code in codes:
            product = await self.repo.get_by_track_code(code)

            if not product:
                logger.warning("Track code not found: %s", code)
                continue

            product.status = status
            await self.repo.update(product)
            updated.append(code)

        logger.info("Bulk status update done: %s", len(updated))
        return updated
