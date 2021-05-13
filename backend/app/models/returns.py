"""Return and replacement requests."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.order import Order, OrderItem
    from app.models.user import User


class ReturnType(str, enum.Enum):
    RETURN = "return"
    REPLACEMENT = "replacement"


class ReturnStatus(str, enum.Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class ReturnReason(str, enum.Enum):
    DAMAGED = "damaged"
    DEFECTIVE = "defective"
    WRONG_ITEM = "wrong_item"
    NOT_AS_DESCRIBED = "not_as_described"
    CHANGED_MIND = "changed_mind"
    OTHER = "other"


class RefundStatus(str, enum.Enum):
    NONE = "none"
    INITIATED = "initiated"
    COMPLETED = "completed"


class ReturnRequest(Base):
    __tablename__ = "return_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    return_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    type: Mapped[ReturnType] = mapped_column(Enum(ReturnType))
    status: Mapped[ReturnStatus] = mapped_column(Enum(ReturnStatus), default=ReturnStatus.REQUESTED)
    reason: Mapped[ReturnReason] = mapped_column(Enum(ReturnReason))
    description: Mapped[Optional[str]] = mapped_column(Text)

    refund_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    refund_status: Mapped[RefundStatus] = mapped_column(Enum(RefundStatus), default=RefundStatus.NONE)

    admin_note: Mapped[Optional[str]] = mapped_column(String(255))
    decided_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    order: Mapped["Order"] = relationship(back_populates="returns")
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    items: Mapped[List["ReturnItem"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )


class ReturnItem(Base):
    __tablename__ = "return_items"
    __table_args__ = (UniqueConstraint("return_id", "order_item_id", name="uq_return_item"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    return_id: Mapped[int] = mapped_column(
        ForeignKey("return_requests.id", ondelete="CASCADE"), index=True
    )
    order_item_id: Mapped[int] = mapped_column(
        ForeignKey("order_items.id", ondelete="CASCADE"), index=True
    )
    quantity: Mapped[int] = mapped_column()

    request: Mapped["ReturnRequest"] = relationship(back_populates="items")
    order_item: Mapped["OrderItem"] = relationship()
