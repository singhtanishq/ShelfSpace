"""Coupon validation and discount computation."""

from datetime import datetime, timezone
from typing import Tuple

from sqlalchemy.orm import Session

from app.models import Coupon, CouponDiscountType
from app.utils.exceptions import NotFoundError, ValidationError


def discount_for(coupon: Coupon, subtotal: float) -> float:
    """Discount amount for a given subtotal (assumes coupon already validated)."""
    if coupon.discount_type == CouponDiscountType.PERCENT:
        discount = subtotal * float(coupon.value) / 100
        if coupon.max_discount_amount is not None:
            discount = min(discount, float(coupon.max_discount_amount))
    else:
        discount = min(float(coupon.value), subtotal)
    return round(discount, 2)


def validate_coupon(db: Session, code: str, subtotal: float) -> Tuple[Coupon, float]:
    """Return (coupon, discount) or raise a descriptive error."""
    coupon = db.query(Coupon).filter(Coupon.code == code.strip().upper()).first()
    if coupon is None:
        raise NotFoundError("This coupon code does not exist.")
    if not coupon.is_active:
        raise ValidationError("This coupon is no longer active.")
    now = datetime.now(timezone.utc)
    if coupon.starts_at and _as_utc(coupon.starts_at) > now:
        raise ValidationError("This coupon is not active yet.")
    if coupon.expires_at and _as_utc(coupon.expires_at) < now:
        raise ValidationError("This coupon has expired.")
    if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
        raise ValidationError("This coupon has reached its usage limit.")
    if subtotal < float(coupon.min_order_amount):
        raise ValidationError(
            f"This coupon requires a minimum order of {float(coupon.min_order_amount):.2f}."
        )
    return coupon, discount_for(coupon, subtotal)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
