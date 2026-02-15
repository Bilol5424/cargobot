from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, or_, and_
from sqlalchemy.sql import func
from typing import List, Optional, Tuple, Dict
from datetime import datetime
import pandas as pd
import os

from .models import (
    User,
    UserRole,
    Product,
    ProductStatus,
    ProductCategory,
    UserTrackCode,
    UserTrackCodeStatus,
    AdminProfile,
)


# =========================================================
# USER REPOSITORY
# =========================================================

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create_user(
        self,
        telegram_id: int,
        phone: str = None,
        full_name: str = None,
        language: str = "ru",
        role: str = "client",
    ) -> User:
        try:
            user_role = UserRole(role)
        except ValueError:
            user_role = UserRole.CLIENT

        user = User(
            telegram_id=telegram_id,
            phone=phone,
            full_name=full_name,
            language=language,
            role=user_role,
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user


# =========================================================
# PRODUCT REPOSITORY
# =========================================================

class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.model = Product

    async def get_product_by_track_code(self, track_code: str) -> Optional[Product]:
        result = await self.session.execute(
            select(Product).where(Product.track_code == track_code)
        )
        return result.scalar_one_or_none()

    async def create_product(
        self,
        track_code: str,
        user_id: int,
        country_from: str = "China",
        **kwargs,
    ) -> Product:
        product = Product(
            track_code=track_code,
            user_id=user_id,
            country_from=country_from,
            status=ProductStatus.CREATED,
            **kwargs,
        )
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product


# =========================================================
# USER TRACK CODE REPOSITORY
# =========================================================

class UserTrackCodeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_user_track_code(
        self,
        user_id: int,
        track_code: str,
        status: UserTrackCodeStatus = UserTrackCodeStatus.PENDING,
    ) -> UserTrackCode:
        utc = UserTrackCode(
            user_id=user_id,
            track_code=track_code,
            status=status,
        )
        self.session.add(utc)
        await self.session.commit()
        await self.session.refresh(utc)
        return utc


# =========================================================
# ✅ ADMIN REPOSITORY (ИСПРАВЛЕНО)
# =========================================================

class AdminRepository:
    """
    Полностью async репозиторий администратора
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, tg_user_id: int) -> Optional[AdminProfile]:
        result = await self.session.execute(
            select(AdminProfile).where(
                AdminProfile.tg_user_id == tg_user_id
            )
        )
        return result.scalar_one_or_none()

    async def create(self, tg_user_id: int, name: str = None) -> AdminProfile:
        admin = AdminProfile(
            tg_user_id=tg_user_id,
            name=name,
        )
        self.session.add(admin)
        await self.session.commit()
        await self.session.refresh(admin)
        return admin

    async def update(self, admin: AdminProfile) -> AdminProfile:
        await self.session.commit()
        await self.session.refresh(admin)
        return admin
