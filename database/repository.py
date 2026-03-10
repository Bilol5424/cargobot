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

    async def export_to_excel(self, products: List[Product]) -> bytes:
        """Экспорт списка товаров в Excel файл (возвращает bytes)"""
        import pandas as pd
        from io import BytesIO

        data = []
        for product in products:
            data.append({
                "ID": product.id,
                "Трек-код": product.track_code,
                "Название": product.product_name or "-",
                "Категория": product.product_category.value if product.product_category else "-",
                "Описание": product.product_description or "-",
                "Количество": product.quantity or 1,
                "Цена за единицу (USD)": product.unit_price_usd or 0,
                "Общая стоимость (USD)": product.total_value_usd or 0,
                "Вес (кг)": product.weight_kg or 0,
                "Длина (см)": product.length_cm or "-",
                "Ширина (см)": product.width_cm or "-",
                "Высота (см)": product.height_cm or "-",
                "Хрупкий": "Да" if product.fragile else "Нет",
                "Батарея": "Да" if product.has_battery else "Нет",
                "Жидкость": "Да" if product.is_liquid else "Нет",
                "Статус": product.status.value if product.status else "-",
                "Страна отправления": product.country_from or "-",
                "Тип доставки": product.delivery_type or "-",
                "Дата отправки": product.send_date.strftime("%d.%m.%Y %H:%M") if product.send_date else "-",
                "Ожидаемая доставка": product.expected_delivery_date.strftime("%d.%m.%Y") if product.expected_delivery_date else "-",
                "Статус доставки до дверей": product.door_delivery_status.value if product.door_delivery_status else "-",
                "Дата прибытия": product.arrival_date.strftime("%d.%m.%Y %H:%M") if product.arrival_date else "-",
                "Дата создания": product.created_at.strftime("%d.%m.%Y %H:%M") if product.created_at else "-",
                "Дата обновления": product.updated_at.strftime("%d.%m.%Y %H:%M") if product.updated_at else "-",
            })

        df = pd.DataFrame(data)
        output = BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Все товары', index=False)

        output.seek(0)
        return output.getvalue()


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
