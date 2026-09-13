"""Inventory mutations with ledger entries. All functions assume an active transaction."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Inventory,
    InventoryChangeType,
    InventoryTransaction,
)
from app.utils.exceptions import BusinessRuleError, NotFoundError


def get_inventory(db: Session, book_id: int) -> Inventory:
    inv = db.query(Inventory).filter(Inventory.book_id == book_id).first()
    if inv is None:
        raise NotFoundError("Inventory record not found for this book.")
    return inv


def lock_inventory(db: Session, book_ids) -> list:
    """SELECT ... FOR UPDATE the inventory rows to serialize stock mutations."""
    if not book_ids:
        return []
    rows = (
        db.execute(
            select(Inventory)
            .where(Inventory.book_id.in_(list(book_ids)))
            .with_for_update()
        )
        .scalars()
        .all()
    )
    found = {row.book_id for row in rows}
    missing = set(book_ids) - found
    if missing:
        raise NotFoundError("Inventory record missing for some items in your cart.")
    return rows


def adjust_stock(
    db: Session,
    *,
    book_id: int,
    change: int,
    change_type: InventoryChangeType,
    balance_after: Optional[int] = None,
    reference_type: Optional[str] = None,
    reference_id: Optional[str] = None,
    note: Optional[str] = None,
    created_by: Optional[int] = None,
    allow_negative: bool = False,
) -> Inventory:
    """Apply a stock change and append a ledger entry. Caller owns the transaction."""
    invs = lock_inventory(db, [book_id])
    inv = invs[0]
    new_balance = inv.stock_quantity + change
    if new_balance < 0:
        if not allow_negative:
            raise BusinessRuleError(
                f"Insufficient stock: only {inv.stock_quantity} unit(s) available."
            )
        new_balance = 0
    inv.stock_quantity = new_balance
    db.add(
        InventoryTransaction(
            book_id=book_id,
            change=change,
            change_type=change_type,
            balance_after=new_balance,
            reference_type=reference_type,
            reference_id=reference_id,
            note=note,
            created_by=created_by,
        )
    )
    return inv
