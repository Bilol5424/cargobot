"""
Модуль для обработки товаров (разделен на подмодули)
"""
from aiogram import Router

from .main import router as main_router
from .add_product import router as add_product_router
from .view_products import router as view_products_router
from .check_track import router as check_track_router
from .product_details import router as product_details_router
from .edit_product import router as edit_product_router
from .export_products import router as export_products_router

# Создаем основной роутер для товаров
products_router = Router()

# Включаем все подроутеры
products_router.include_router(main_router)
products_router.include_router(add_product_router)
products_router.include_router(view_products_router)
products_router.include_router(check_track_router)
products_router.include_router(product_details_router)
products_router.include_router(edit_product_router)
products_router.include_router(export_products_router)

__all__ = ['products_router']