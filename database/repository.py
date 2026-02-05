from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, or_
from sqlalchemy.sql import func
from typing import List, Optional, Tuple, Dict
from datetime import datetime, timedelta
import pandas as pd
import os
from sqlalchemy import select
from .models import User, UserRole, Product, ProductStatus, ProductCategory

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def create_user(self, telegram_id: int, phone: str = None, 
                        full_name: str = None, language: str = "ru",
                        role: str = "client") -> User:
        """Создание пользователя"""
        try:
            user_role = UserRole(role)
        except ValueError:
            user_role = UserRole.CLIENT
        
        user = User(
            telegram_id=telegram_id,
            phone=phone,
            full_name=full_name,
            language=language,
            role=user_role
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def update_user_language(self, telegram_id: int, language: str) -> Optional[User]:
        stmt = update(User).where(User.telegram_id == telegram_id).values(language=language)
        await self.session.execute(stmt)
        await self.session.commit()
        return await self.get_user_by_telegram_id(telegram_id)
    
    async def update_user_profile(self, telegram_id: int, **kwargs) -> Optional[User]:
        update_data = {}
        for key, value in kwargs.items():
            if value is not None:
                update_data[key] = value
        
        if update_data:
            stmt = update(User).where(User.telegram_id == telegram_id).values(**update_data)
            await self.session.execute(stmt)
            await self.session.commit()
        
        return await self.get_user_by_telegram_id(telegram_id)

class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.model = Product  # Для использования в других методах
    
    async def get_user_products(self, user_id: int, skip: int = 0, limit: int = 5) -> List[Product]:
        result = await self.session.execute(
            select(Product)
            .where(Product.user_id == user_id)
            .order_by(Product.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_product_by_track_code(self, track_code: str) -> Optional[Product]:
        result = await self.session.execute(
            select(Product).where(Product.track_code == track_code)
        )
        return result.scalar_one_or_none()
    
    async def create_product(self, track_code: str, user_id: int, 
                           country_from: str = "China", **kwargs) -> Product:
        product = Product(
            track_code=track_code,
            user_id=user_id,
            country_from=country_from,
            status=ProductStatus.CREATED,
            **kwargs
        )
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product
    
    async def update_product(self, product_id: int, **kwargs) -> Optional[Product]:
        # Получаем продукт
        result = await self.session.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()
        
        if not product:
            return None
        
        # Обновляем поля
        for key, value in kwargs.items():
            if value is not None:
                setattr(product, key, value)
        
        product.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(product)
        return product
    
    async def update_product_status(self, product_id: int, status: ProductStatus) -> Optional[Product]:
        return await self.update_product(product_id, status=status)
    
    async def get_products_by_status(self, status: ProductStatus, 
                                   skip: int = 0, limit: int = 50) -> List[Product]:
        result = await self.session.execute(
            select(Product)
            .where(Product.status == status)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_detailed_product_info(self, track_code: str) -> Optional[dict]:
        """Получить детальную информацию о товаре с данными пользователя"""
        result = await self.session.execute(
            select(Product, User)
            .join(User, Product.user_id == User.id)
            .where(Product.track_code == track_code)
        )
        
        row = result.first()
        if row:
            product, user = row
            return {
                "product": product,
                "user": user,
                "product_info": {
                    "name": product.product_name,
                    "category": product.product_category.value if product.product_category else None,
                    "description": product.product_description,
                    "quantity": product.quantity,
                    "unit_price": product.unit_price_usd,
                    "total_value": product.total_value_usd,
                    "weight": product.weight_kg,
                    "dimensions": f"{product.length_cm}×{product.width_cm}×{product.height_cm} см" if product.length_cm else None,
                    "fragile": product.fragile,
                    "has_battery": product.has_battery,
                    "is_liquid": product.is_liquid
                },
                "user_info": {
                    "name": user.full_name,
                    "phone": user.phone,
                    "region": user.region,
                    "telegram_id": user.telegram_id
                }
            }
        return None
    
    # НОВЫЕ МЕТОДЫ ДЛЯ ФУНКЦИОНАЛА
    
    async def search_products(self, search_term: str, user_id: Optional[int] = None) -> List[Product]:
        """Поиск товаров по трек-коду, названию или описанию"""
        query = select(Product)
        
        if user_id:
            query = query.where(Product.user_id == user_id)
        
        query = query.where(
            or_(
                Product.track_code.ilike(f"%{search_term}%"),
                Product.product_name.ilike(f"%{search_term}%"),
                Product.product_description.ilike(f"%{search_term}%")
            )
        ).order_by(Product.created_at.desc())
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def bulk_update_status(
        self, 
        track_codes: List[str], 
        new_status: ProductStatus,
        arrival_date: Optional[datetime] = None
    ) -> Tuple[int, List[str]]:
        """
        Массовое обновление статусов товаров
        
        Returns:
            tuple: (количество обновленных, список обновленных трек-кодов)
        """
        if not track_codes:
            return 0, []
        
        # Получаем товары
        result = await self.session.execute(
            select(Product).where(Product.track_code.in_(track_codes))
        )
        products = result.scalars().all()
        
        updated_count = 0
        updated_codes = []
        
        for product in products:
            product.status = new_status
            if arrival_date and new_status == ProductStatus.TAJIKISTAN_WAREHOUSE:
                product.arrival_date = arrival_date
            product.updated_at = datetime.utcnow()
            updated_count += 1
            updated_codes.append(product.track_code)
        
        await self.session.commit()
        return updated_count, updated_codes
    
    async def update_product_by_track_code(
        self, 
        track_code: str, 
        user_id: int,
        **kwargs
    ) -> Optional[Product]:
        """Обновление товара по трек-коду (для пользователя)"""
        # Проверяем, что товар принадлежит пользователю
        result = await self.session.execute(
            select(Product).where(
                Product.track_code == track_code,
                Product.user_id == user_id
            )
        )
        product = result.scalar_one_or_none()
        
        if not product:
            return None
        
        # Не позволяем изменять статус, если товар уже отправлен
        if product.status not in [ProductStatus.CREATED, ProductStatus.CHINA_WAREHOUSE]:
            # Разрешаем изменять только описание и название
            allowed_fields = ['product_name', 'product_description']
            kwargs = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        # Обновляем поля
        for key, value in kwargs.items():
            if value is not None:
                setattr(product, key, value)
        
        product.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(product)
        
        return product
    
    async def get_products_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        status: Optional[ProductStatus] = None
    ) -> List[Product]:
        """Получение товаров за определенный период"""
        query = select(Product).where(
            Product.created_at.between(start_date, end_date)
        )
        
        if status:
            query = query.where(Product.status == status)
        
        query = query.order_by(Product.created_at.desc())
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_delivery_statistics(
        self,
        month: int,
        year: int
    ) -> Dict[str, int]:
        """Статистика доставки за месяц"""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # Всего товаров за месяц
        total_query = select(func.count(Product.id)).where(
            Product.created_at.between(start_date, end_date)
        )
        total_result = await self.session.execute(total_query)
        total = total_result.scalar() or 0
        
        # Доставленные товары
        delivered_query = select(func.count(Product.id)).where(
            Product.created_at.between(start_date, end_date),
            Product.status == ProductStatus.DELIVERED
        )
        delivered_result = await self.session.execute(delivered_query)
        delivered = delivered_result.scalar() or 0
        
        # Принятые товары (на складе в Таджикистане)
        accepted_query = select(func.count(Product.id)).where(
            Product.created_at.between(start_date, end_date),
            Product.status == ProductStatus.TAJIKISTAN_WAREHOUSE
        )
        accepted_result = await self.session.execute(accepted_query)
        accepted = accepted_result.scalar() or 0
        
        # В пути
        transit_query = select(func.count(Product.id)).where(
            Product.created_at.between(start_date, end_date),
            Product.status == ProductStatus.IN_TRANSIT
        )
        transit_result = await self.session.execute(transit_query)
        transit = transit_result.scalar() or 0
        
        return {
            "total": total,
            "delivered": delivered,
            "accepted": accepted,
            "transit": transit,
            "pending": total - delivered - accepted - transit
        }
    
    async def export_to_excel(self, products: List[Product]) -> bytes:
        """Экспорт товаров в Excel"""
        try:
            # Создаем DataFrame
            data = []
            for product in products:
                data.append({
                    "Трек-код": product.track_code,
                    "Название": product.product_name or "",
                    "Категория": product.product_category.value if product.product_category else "",
                    "Статус": product.status.value,
                    "Вес (кг)": product.weight_kg or 0,
                    "Стоимость ($)": product.total_value_usd or 0,
                    "Количество": product.quantity or 1,
                    "Дата создания": product.created_at.strftime("%Y-%m-%d %H:%M"),
                    "Дата обновления": product.updated_at.strftime("%Y-%m-%d %H:%M") if product.updated_at else "",
                    "Дата прибытия": product.arrival_date.strftime("%Y-%m-%d") if hasattr(product, 'arrival_date') and product.arrival_date else "",
                    "Особые свойства": self._get_special_properties(product)
                })
            
            df = pd.DataFrame(data)
            
            # Конвертируем в Excel
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                with pd.ExcelWriter(tmp.name, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Товары')
                
                # Читаем файл
                with open(tmp.name, 'rb') as f:
                    excel_data = f.read()
                
                # Удаляем временный файл
                os.unlink(tmp.name)
            
            return excel_data
            
        except Exception as e:
            print(f"Ошибка экспорта в Excel: {e}")
            return b""
    
    def _get_special_properties(self, product: Product) -> str:
        """Получение строки с особыми свойствами"""
        properties = []
        if product.fragile:
            properties.append("Хрупкий")
        if product.has_battery:
            properties.append("С батареей")
        if product.is_liquid:
            properties.append("Жидкость")
        return ", ".join(properties) if properties else "Нет"