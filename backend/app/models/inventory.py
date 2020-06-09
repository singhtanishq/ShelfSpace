"""Inventory tracking: per-book stock plus an append-only movement ledger."""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.catalog import Book


class InventoryChangeType(str, enum.Enum):
    RESTOCK = "restock"
    SALE = "sale"
    RETURN_TO_STOCK = "return_to_stock"
    REPLACEMENT_ISSUE = "replacement_issue"
    ADJUSTMENT = "adjustment"


class Inventory(Base):
    __tablename__ = "inventories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"), unique=True, index=True
    )
    stock_quantity: Mapped[int] = mapped_column(default=0)
    reserved_quantity: Mapped[int] = mapped_column(default=0)
    low_stock_threshold: Mapped[int] = mapped_column(default=5)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    book: Mapped["Book"] = relationship(back_populates="inventory")

    @property
    def available_quantity(self) -> int:
        return max(self.stock_quantity - self.reserved_quantity, 0)

    @property
    def is_low_stock(self) -> bool:
        return self.stock_quantity <= self.low_stock_threshold


class InventoryTransaction(Base):
    """Append-only audit trail of every stock movement."""

    __tablename__ = "inventory_transactions"
    __table_args__ = (Index("ix_inv_tx_book_created", "book_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), index=True)
    change: Mapped[int] = mapped_column()  # positive = stock in, negative = stock out
    change_type: Mapped[InventoryChangeType] = mapped_column(Enum(InventoryChangeType))
    balance_after: Mapped[int] = mapped_column()
    reference_type: Mapped[Optional[str]] = mapped_column(String(40))
    reference_id: Mapped[Optional[str]] = mapped_column(String(40))
    note: Mapped[Optional[str]] = mapped_column(String(255))
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
