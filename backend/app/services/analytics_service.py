"""Admin analytics: dashboard summary, time-series charts, top entities."""

import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import distinct, func
from sqlalchemy.orm import Session

from app.models import (
    Book,
    Category,
    Inventory,
    Order,
    OrderItem,
    OrderStatus,
    PaymentStatus,
    ReturnRequest,
    ReturnStatus,
    User,
    UserRole,
    book_categories,
)
from app.services import settings_service

# Business metrics deliberately exclude cancelled orders.
_REVENUE_STATUSES = [s for s in OrderStatus if s not in (OrderStatus.CANCELLED,)]
_PAID_STATUSES = [PaymentStatus.PAID, PaymentStatus.REFUNDED]


def _range(days: int, date_from: Optional[str] = None, date_to: Optional[str] = None) -> Tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    if date_from and date_to:
        start = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc) + timedelta(days=1)
        return start, end
    return now - timedelta(days=days), now


def summary(db: Session, days: int = 30) -> dict:
    start, end = _range(days)
    revenue_query = (
        db.query(func.coalesce(func.sum(Order.total), 0.0), func.count(Order.id))
        .filter(
            Order.placed_at >= start,
            Order.placed_at < end,
            Order.status.in_(_REVENUE_STATUSES),
            Order.payment_status.in_(_PAID_STATUSES),
        )
        .one()
    )
    total_revenue = float(revenue_query[0] or 0)
    total_orders = int(revenue_query[1] or 0)

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_revenue, today_orders = (
        db.query(func.coalesce(func.sum(Order.total), 0.0), func.count(Order.id))
        .filter(Order.placed_at >= today_start, Order.status.in_(_REVENUE_STATUSES))
        .one()
    )

    low_stock_subq = (
        db.query(Inventory)
        .filter(Inventory.stock_quantity > 0, Inventory.stock_quantity <= Inventory.low_stock_threshold)
        .count()
    )
    out_of_stock = db.query(Inventory).filter(Inventory.stock_quantity <= 0).count()

    inventory_value = (
        db.query(func.coalesce(func.sum(Inventory.stock_quantity * Book.price), 0.0))
        .join(Book, Inventory.book_id == Book.id)
        .filter(Book.is_active.is_(True))
        .scalar()
    )

    return {
        "currency": settings_service.get_str(db, "currency"),
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "total_customers": db.query(func.count(User.id)).filter(User.role == UserRole.CUSTOMER).scalar(),
        "total_books": db.query(func.count(Book.id)).scalar(),
        "active_books": db.query(func.count(Book.id)).filter(Book.is_active.is_(True)).scalar(),
        "inventory_value": round(float(inventory_value or 0), 2),
        "pending_orders": db.query(func.count(Order.id))
        .filter(Order.status.in_([OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PROCESSING]))
        .scalar(),
        "open_returns": db.query(func.count(ReturnRequest.id))
        .filter(ReturnRequest.status.in_([ReturnStatus.REQUESTED, ReturnStatus.APPROVED]))
        .scalar(),
        "low_stock_count": low_stock_subq,
        "out_of_stock_count": out_of_stock,
        "avg_order_value": round(total_revenue / total_orders, 2) if total_orders else 0.0,
        "orders_today": int(today_orders or 0),
        "revenue_today": round(float(today_revenue or 0), 2),
    }


def charts(db: Session, days: int = 30) -> dict:
    start, end = _range(days)
    # SQLite/MySQL compatible daily bucketing via date() on the UTC timestamp.
    revenue_rows = (
        db.query(func.date(Order.placed_at), func.coalesce(func.sum(Order.total), 0.0), func.count(Order.id))
        .filter(
            Order.placed_at >= start,
            Order.placed_at <= end,
            Order.status.in_(_REVENUE_STATUSES),
        )
        .group_by(func.date(Order.placed_at))
        .all()
    )
    customer_rows = (
        db.query(func.date(User.created_at), func.count(distinct(User.id)))
        .filter(User.created_at >= start, User.created_at <= end)
        .group_by(func.date(User.created_at))
        .all()
    )

    by_date = {str(row[0]): (float(row[1] or 0), int(row[2] or 0)) for row in revenue_rows}
    customers_by_date = {str(row[0]): int(row[1] or 0) for row in customer_rows}

    revenue_points: List[dict] = []
    order_points: List[dict] = []
    growth_points: List[dict] = []
    current = start.date()
    end_date = end.date()
    while current <= end_date:
        key = current.isoformat()
        rev, count = by_date.get(key, (0.0, 0))
        revenue_points.append({"date": key, "value": round(rev, 2), "count": count})
        order_points.append({"date": key, "value": rev, "count": count})
        growth_points.append({"date": key, "value": 0, "count": customers_by_date.get(key, 0)})
        current += timedelta(days=1)

    return {"revenue": revenue_points, "orders": order_points, "customer_growth": growth_points}


def top_entities(db: Session, days: int = 30) -> dict:
    start, end = _range(days)
    book_rows = (
        db.query(
            OrderItem.book_id,
            OrderItem.title,
            func.sum(OrderItem.quantity),
            func.sum(OrderItem.line_total),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.placed_at >= start, Order.placed_at <= end, Order.status.in_(_REVENUE_STATUSES))
        .group_by(OrderItem.book_id, OrderItem.title)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )
    books = []
    for row in book_rows:
        book = db.get(Book, row[0]) if row[0] else None
        books.append(
            {
                "book_id": row[0],
                "title": row[1],
                "author_names": book.author_names() if book else "",
                "units_sold": int(row[2] or 0),
                "revenue": round(float(row[3] or 0), 2),
            }
        )

    category_rows = (
        db.query(
            Category.name,
            func.sum(OrderItem.quantity),
            func.sum(OrderItem.line_total),
        )
        .join(book_categories, book_categories.c.category_id == Category.id)
        .join(Book, Book.id == book_categories.c.book_id)
        .join(OrderItem, OrderItem.book_id == Book.id)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.placed_at >= start, Order.placed_at <= end, Order.status.in_(_REVENUE_STATUSES))
        .group_by(Category.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )
    categories = [
        {"name": row[0], "units_sold": int(row[1] or 0), "revenue": round(float(row[2] or 0), 2)}
        for row in category_rows
    ]

    status_rows = (
        db.query(Order.status, func.count(Order.id))
        .filter(Order.placed_at >= start, Order.placed_at <= end)
        .group_by(Order.status)
        .all()
    )
    distribution = [{"status": row[0].value, "count": int(row[1])} for row in status_rows]

    return {"books": books, "categories": categories, "status_distribution": distribution}


def low_stock_books(db: Session, limit: int = 20) -> List[dict]:
    rows = (
        db.query(Inventory, Book)
        .join(Book, Inventory.book_id == Book.id)
        .filter(Book.is_active.is_(True), Inventory.stock_quantity <= Inventory.low_stock_threshold)
        .order_by(Inventory.stock_quantity.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "book_id": book.id,
            "title": book.title,
            "slug": book.slug,
            "stock_quantity": inv.stock_quantity,
            "low_stock_threshold": inv.low_stock_threshold,
        }
        for inv, book in rows
    ]
