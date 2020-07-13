"""Admin analytics, settings, audit-log and misc schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    currency: str
    total_revenue: float
    total_orders: int
    total_customers: int
    total_books: int
    active_books: int
    inventory_value: float
    pending_orders: int
    open_returns: int
    low_stock_count: int
    out_of_stock_count: int
    avg_order_value: float
    orders_today: int
    revenue_today: float


class SeriesPoint(BaseModel):
    date: str
    value: float
    count: int = 0


class ChartResponse(BaseModel):
    revenue: List[SeriesPoint]
    orders: List[SeriesPoint]
    customer_growth: List[SeriesPoint]


class TopBook(BaseModel):
    book_id: Optional[int]
    title: str
    author_names: str = ""
    units_sold: int
    revenue: float


class TopCategory(BaseModel):
    name: str
    units_sold: int
    revenue: float


class StatusDistribution(BaseModel):
    status: str
    count: int


class TopEntities(BaseModel):
    books: List[TopBook]
    categories: List[TopCategory]
    status_distribution: List[StatusDistribution]


class StoreSettingsPublic(BaseModel):
    store_name: str
    support_email: str
    tax_percent: float
    shipping_fee: float
    free_shipping_threshold: float
    return_window_days: int
    low_stock_threshold: int
    currency: str


class StoreSettingsUpdate(BaseModel):
    store_name: Optional[str] = None
    support_email: Optional[str] = None
    tax_percent: Optional[float] = None
    shipping_fee: Optional[float] = None
    free_shipping_threshold: Optional[float] = None
    return_window_days: Optional[int] = None
    low_stock_threshold: Optional[int] = None
    currency: Optional[str] = None


class AuditLogPublic(BaseModel):
    id: int
    actor_id: Optional[int]
    actor_name: Optional[str]
    action: str
    entity_type: str
    entity_id: Optional[str]
    detail: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogList(BaseModel):
    items: List[AuditLogPublic]
    total: int
    page: int
    page_size: int
    pages: int
