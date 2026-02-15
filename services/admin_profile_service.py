from database.repository import AdminRepository


class AdminProfileService:
    def __init__(self, repo: AdminRepository):
        self.repo = repo

    async def get_profile(self, admin_id: int):
        return await self.repo.get(admin_id)

    async def update_name(self, admin_id: int, name: str):
        admin = await self.repo.get(admin_id)
        admin.name = name
        await self.repo.update(admin)
        return admin
