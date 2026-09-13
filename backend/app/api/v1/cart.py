"""Cart and wishlist endpoints."""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Book, User, WishlistItem
from app.schemas.order import (
    CartCouponApply,
    CartItemAdd,
    CartItemUpdate,
    CartMergeRequest,
    CartPublic,
    WishlistItemPublic,
)
from app.services import cart_service
from app.utils.exceptions import ConflictError, NotFoundError
from app.utils.serializers import book_card

router = APIRouter(tags=["cart"])


class WishlistAdd(BaseModel):
    book_id: int = Field(gt=0)


# ---------------------------------------------------------------------------
# Cart
# ---------------------------------------------------------------------------


@router.get("/cart", response_model=CartPublic)
def get_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return cart_service.cart_view(db, user)


@router.post("/cart/items", response_model=CartPublic, status_code=201)
def add_cart_item(
    data: CartItemAdd,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cart_service.add_item(db, user, data.book_id, data.quantity)
    return cart_service.cart_view(db, user)


@router.patch("/cart/items/{book_id}", response_model=CartPublic)
def update_cart_item(
    book_id: int,
    data: CartItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cart_service.update_item(db, user, book_id, data.quantity)
    return cart_service.cart_view(db, user)


@router.delete("/cart/items/{book_id}", response_model=CartPublic)
def remove_cart_item(
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cart_service.remove_item(db, user, book_id)
    return cart_service.cart_view(db, user)


@router.delete("/cart", response_model=CartPublic)
def clear_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cart_service.clear_cart(db, user)
    return cart_service.cart_view(db, user)


@router.post("/cart/coupon", response_model=CartPublic)
def apply_coupon(
    data: CartCouponApply,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cart_service.apply_coupon(db, user, data.code)
    return cart_service.cart_view(db, user)


@router.delete("/cart/coupon", response_model=CartPublic)
def remove_coupon(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cart_service.remove_coupon(db, user)
    return cart_service.cart_view(db, user)


@router.post("/cart/merge", response_model=CartPublic)
def merge_cart(
    data: CartMergeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cart_service.merge_guest_cart(db, user, [i.model_dump() for i in data.items])
    return cart_service.cart_view(db, user)


# ---------------------------------------------------------------------------
# Wishlist
# ---------------------------------------------------------------------------


@router.get("/wishlist", response_model=List[WishlistItemPublic])
def get_wishlist(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    items = _wishlist(db, user)
    return [_wishlist_item_view(i) for i in items]


@router.post("/wishlist", status_code=201, response_model=List[WishlistItemPublic])
def add_to_wishlist(
    data: WishlistAdd,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    book = db.get(Book, data.book_id)
    if book is None or not book.is_active:
        raise NotFoundError("Book not found.")
    exists = (
        db.query(WishlistItem)
        .filter(WishlistItem.user_id == user.id, WishlistItem.book_id == data.book_id)
        .first()
    )
    if exists is None:
        db.add(WishlistItem(user_id=user.id, book_id=data.book_id))
        db.flush()
    items = _wishlist(db, user)
    return [_wishlist_item_view(i) for i in items]


@router.delete("/wishlist/{book_id}", status_code=204)
def remove_from_wishlist(
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = (
        db.query(WishlistItem)
        .filter(WishlistItem.user_id == user.id, WishlistItem.book_id == book_id)
        .first()
    )
    if item is not None:
        db.delete(item)
        db.flush()


def _wishlist(db: Session, user: User):
    return (
        db.query(WishlistItem)
        .filter(WishlistItem.user_id == user.id)
        .order_by(WishlistItem.created_at.desc())
        .all()
    )


def _wishlist_item_view(item: WishlistItem) -> dict:
    book = item.book
    return {
        "book_id": book.id,
        "title": book.title,
        "slug": book.slug,
        "cover_image": book.cover_image,
        "author_names": book.author_names(),
        "price": float(book.price),
        "effective_price": float(book.effective_price),
        "discount_percent": float(book.discount_percent),
        "available_quantity": book.inventory.available_quantity if book.inventory else 0,
        "added_at": item.created_at,
    }
