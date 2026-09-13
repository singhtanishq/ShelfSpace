"""Admin API aggregation."""

from fastapi import APIRouter

from app.api.v1.admin import catalog, dashboard, orders, system, users

router = APIRouter()
router.include_router(dashboard.router)
router.include_router(catalog.router)
router.include_router(orders.router)
router.include_router(users.router)
router.include_router(system.router)
