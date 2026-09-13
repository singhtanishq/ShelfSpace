"""Admin: dashboard, analytics and low-stock alerts."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user
from app.core.database import get_db
from app.models import User
from app.schemas.admin import ChartResponse, DashboardSummary, TopEntities
from app.services import analytics_service

router = APIRouter(tags=["admin-dashboard"])


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(
    days: int = Query(default=30, ge=1, le=3650),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    return analytics_service.summary(db, days=days)


@router.get("/dashboard/charts", response_model=ChartResponse)
def dashboard_charts(
    days: int = Query(default=30, ge=1, le=3650),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    return analytics_service.charts(db, days=days)


@router.get("/dashboard/top", response_model=TopEntities)
def dashboard_top(
    days: int = Query(default=30, ge=1, le=3650),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    return analytics_service.top_entities(db, days=days)


@router.get("/dashboard/low-stock")
def dashboard_low_stock(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    return analytics_service.low_stock_books(db)
