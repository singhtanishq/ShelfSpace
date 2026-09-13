"""Cart management: server-backed cart per user with stock-aware totals."""

from typing import List, Optional

from sqlalchemy.orm import Session, selectinload

from app.models import Book, Cart, CartItem, Coupon, User
from app.services import coupon_service, settings_service
from app.utils.exceptions import NotFoundError, ValidationError


def get_or_create_cart(db: Session, user: User) -> Cart:
    cart = (
        db.query(Cart)
        .options(selectinload(Cart.items).selectinload(CartItem.book).selectinload(Book.authors))
        .filter(Cart.user_id == user.id)
        .first()
    )
    if cart is None:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.flush()
    return cart


def add_item(db: Session, user: User, book_id: int, quantity: int = 1) -> Cart:
    book = db.get(Book, book_id)
    if book is None or not book.is_active:
        raise NotFoundError("Book not found.")
    if quantity < 1 or quantity > 99:
        raise ValidationError("Quantity must be between 1 and 99.")

    cart = get_or_create_cart(db, user)
    item = next((i for i in cart.items if i.book_id == book_id), None)
    existing_qty = item.quantity if item else 0
    _ensure_stock(db, book, existing_qty + quantity)
    if item:
        item.quantity = existing_qty + quantity
    else:
        db.add(CartItem(cart_id=cart.id, book_id=book_id, quantity=quantity))
    db.flush()
    return cart


def update_item(db: Session, user: User, book_id: int, quantity: int) -> Cart:
    cart = get_or_create_cart(db, user)
    item = next((i for i in cart.items if i.book_id == book_id), None)
    if item is None:
        raise NotFoundError("This book is not in your cart.")
    if quantity < 1 or quantity > 99:
        raise ValidationError("Quantity must be between 1 and 99.")
    book = db.get(Book, book_id)
    _ensure_stock(db, book, quantity)
    item.quantity = quantity
    db.flush()
    return cart


def remove_item(db: Session, user: User, book_id: int) -> Cart:
    cart = get_or_create_cart(db, user)
    item = next((i for i in cart.items if i.book_id == book_id), None)
    if item is None:
        raise NotFoundError("This book is not in your cart.")
    cart.items.remove(item)  # delete-orphan cascade removes the row
    db.flush()
    return cart


def clear_cart(db: Session, user: User) -> None:
    cart = get_or_create_cart(db, user)
    cart.items.clear()
    cart.coupon_id = None
    db.flush()


def apply_coupon(db: Session, user: User, code: str) -> Cart:
    cart = get_or_create_cart(db, user)
    if not cart.items:
        raise ValidationError("Your cart is empty.")
    subtotal = _subtotal(cart)
    coupon, _ = coupon_service.validate_coupon(db, code, subtotal)
    cart.coupon_id = coupon.id
    db.flush()
    return cart


def remove_coupon(db: Session, user: User) -> Cart:
    cart = get_or_create_cart(db, user)
    cart.coupon_id = None
    db.flush()
    return cart


def merge_guest_cart(db: Session, user: User, items: List[dict]) -> Cart:
    """Merge an anonymous (localStorage) cart into the user cart after login."""
    for entry in items:
        book = db.get(Book, entry.get("book_id"))
        if book is None or not book.is_active:
            continue
        try:
            add_item(db, user, book.id, int(entry.get("quantity", 1)))
        except (NotFoundError, ValidationError):
            continue  # skip unavailable entries instead of failing the merge
    return get_or_create_cart(db, user)


def cart_view(db: Session, user: User) -> dict:
    """Full cart representation including server-computed totals."""
    cart = get_or_create_cart(db, user)
    items = []
    subtotal = 0.0
    total_quantity = 0
    for item in cart.items:
        book = item.book
        if book is None:
            continue
        available = book.inventory.available_quantity if book.inventory else 0
        line = float(book.effective_price) * item.quantity
        subtotal += line
        total_quantity += item.quantity
        items.append(
            {
                "book_id": book.id,
                "title": book.title,
                "slug": book.slug,
                "cover_image": book.cover_image,
                "author_names": book.author_names(),
                "unit_price": float(book.effective_price),
                "original_price": float(book.price),
                "discount_percent": float(book.discount_percent),
                "quantity": item.quantity,
                "line_total": round(line, 2),
                "available_quantity": available,
                "in_stock": available >= item.quantity,
            }
        )
    subtotal = round(subtotal, 2)

    discount = 0.0
    coupon_payload = None
    coupon_error = None
    if cart.coupon_id is not None:
        coupon = db.get(Coupon, cart.coupon_id)
        if coupon is not None and items:
            try:
                coupon, discount = coupon_service.validate_coupon(db, coupon.code, subtotal)
                coupon_payload = {"code": coupon.code, "description": coupon.description}
            except Exception as exc:
                coupon_error = getattr(exc, "message", str(exc))
                discount = 0.0

    shipping = _shipping_fee(db, subtotal - discount)
    tax = round((subtotal - discount) * settings_service.get_float(db, "tax_percent") / 100, 2)
    total = round(subtotal - discount + shipping + tax, 2)

    return {
        "items": items,
        "subtotal": subtotal,
        "discount_total": discount,
        "shipping_fee": shipping,
        "tax_total": tax,
        "total": total,
        "coupon": coupon_payload,
        "coupon_error": coupon_error,
        "currency": settings_service.get_str(db, "currency"),
        "total_quantity": total_quantity,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ensure_stock(db: Session, book: Book, requested: int) -> None:
    available = book.inventory.available_quantity if book.inventory else 0
    if requested > available:
        raise ValidationError(
            f"Only {available} unit(s) of '{book.title}' are available right now."
        )


def _subtotal(cart: Cart) -> float:
    total = 0.0
    for item in cart.items:
        if item.book and item.book.is_active:
            total += float(item.book.effective_price) * item.quantity
    return round(total, 2)


def _shipping_fee(db: Session, discounted_subtotal: float) -> float:
    fee = settings_service.get_float(db, "shipping_fee")
    threshold = settings_service.get_float(db, "free_shipping_threshold")
    if threshold > 0 and discounted_subtotal >= threshold:
        return 0.0
    return round(fee, 2)
