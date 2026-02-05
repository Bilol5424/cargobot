from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Float, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum
from sqlalchemy.sql import func

# Импортируем Base из session.py
from database.session import Base

class UserRole(enum.Enum):
    CLIENT = "client"
    ADMIN_CN = "admin_cn"
    ADMIN_TJ = "admin_tj"

class ProductStatus(enum.Enum):
    CREATED = "created"
    CHINA_WAREHOUSE = "china_warehouse"
    IN_TRANSIT = "in_transit"
    TAJIKISTAN_WAREHOUSE = "tajikistan_warehouse"
    DELIVERED = "delivered"
    COMPLETED = "completed"

class DoorDeliveryStatus(enum.Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class ProductCategory(enum.Enum):
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    SHOES = "shoes"
    HOME_APPLIANCES = "home_appliances"
    BEAUTY = "beauty"
    TOYS = "toys"
    AUTOMOTIVE = "automotive"
    SPORTS = "sports"
    OTHER = "other"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    phone = Column(String(20))
    full_name = Column(String(100))
    region = Column(String(100))
    language = Column(String(10), default="ru")  # 'ru' или 'tj'
    role = Column(Enum(UserRole), default=UserRole.CLIENT)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    products = relationship("Product", back_populates="user")
    Base = declarative_base()
class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    track_code = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Основная информация
    product_name = Column(String(200))
    product_category = Column(Enum(ProductCategory))
    product_description = Column(String(500))
    quantity = Column(Integer, default=1)
    unit_price_usd = Column(Float, default=0.0)
    total_value_usd = Column(Float, default=0.0)
    weight_kg = Column(Float, default=0.0)
    length_cm = Column(Float)
    width_cm = Column(Float)
    height_cm = Column(Float)
    
    # Особые свойства
    fragile = Column(Boolean, default=False)
    has_battery = Column(Boolean, default=False)
    is_liquid = Column(Boolean, default=False)
    
    # Статус и доставка
    status = Column(Enum(ProductStatus), default=ProductStatus.CREATED)
    country_from = Column(String(50))
    delivery_type = Column(String(50))
    send_date = Column(DateTime)
    expected_delivery_date = Column(DateTime)
    door_delivery_status = Column(Enum(DoorDeliveryStatus), default=DoorDeliveryStatus.PENDING)
    
    # Новое поле: Дата прибытия в Таджикистан
    arrival_date = Column(DateTime)
    
    # Даты
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="products")