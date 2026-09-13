"""API v1 aggregation."""

from fastapi import APIRouter

from app.api.v1 import addresses, auth, cart, catalog, notifications, orders
from app.api.v1.admin import router as admin_router

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(catalog.router)
api_router.include_router(cart.router)
api_router.include_router(orders.router)
api_router.include_router(notifications.router)
api_router.include_router(addresses.router)
api_router.include_router(admin_router)
