"""Admin: coupons, review moderation, store settings and audit logs."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user
from app.core.database import get_db
from app.models import Coupon, User
from app.schemas.admin import AuditLogList, StoreSettingsPublic, StoreSettingsUpdate
from app.schemas.catalog import ReviewPublic
from app.schemas.order import CouponCreate, CouponPublic, CouponUpdate
from app.services import audit_service, review_service, settings_service
from app.utils.exceptions import ConflictError, NotFoundError
from app.utils.pagination import PaginationParams
from app.utils.serializers import review_public

router = APIRouter(prefix="/admin", tags=["admin-misc"])


# ---------------------------------------------------------------------------
# Coupons
# ---------------------------------------------------------------------------


@router.get("/admin/coupons", response_model=List[CouponPublic])
def admin_list_coupons(
    db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)
):
    return db.query(Coupon).order_by(Coupon.created_at.desc()).all()


@router.post("/admin/coupons", response_model=CouponPublic, status_code=201)
def admin_create_coupon(
    data: CouponCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)
):
    from app.models import CouponDiscountType

    code = data.code.strip().upper()
    if db.query(Coupon).filter(Coupon.code == code).first() is not None:
        raise ConflictError("A coupon with this code already exists.")
    if data.discount_type == "percent" and data.value > 100:
        from app.utils.exceptions import ValidationError

        raise ValidationError("Percentage discounts cannot exceed 100.")
    coupon = Coupon(
        code=code,
        description=data.description,
        discount_type=CouponDiscountType(data.discount_type),
        value=data.value,
        min_order_amount=data.min_order_amount,
        max_discount_amount=data.max_discount_amount,
        usage_limit=data.usage_limit,
        starts_at=data.starts_at,
        expires_at=data.expires_at,
        is_active=data.is_active,
    )
    db.add(coupon)
    db.flush()
    audit_service.log(db, actor=admin, action="coupon.create", entity_type="coupon", entity_id=coupon.id, detail={"code": code})
    return coupon


@router.put("/admin/coupons/{coupon_id}", response_model=CouponPublic)
def admin_update_coupon(
    coupon_id: int,
    data: CouponUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    coupon = db.get(Coupon, coupon_id)
    if coupon is None:
        raise NotFoundError("Coupon not found.")
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(coupon, field, value)
    audit_service.log(db, actor=admin, action="coupon.update", entity_type="coupon", entity_id=coupon.id, detail={"fields": list(updates.keys())})
    return coupon


@router.delete("/admin/coupons/{coupon_id}")
def admin_delete_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    coupon = db.get(Coupon, coupon_id)
    if coupon is None:
        raise NotFoundError("Coupon not found.")
    if coupon.used_count > 0:
        coupon.is_active = False
        audit_service.log(db, actor=admin, action="coupon.deactivate", entity_type="coupon", entity_id=coupon.id, detail={"code": coupon.code})
        return {"deactivated": True, "code": coupon.code, "reason": "Coupon has been used; it was deactivated instead of deleted."}
    audit_service.log(db, actor=admin, action="coupon.delete", entity_type="coupon", entity_id=coupon.id, detail={"code": coupon.code})
    db.delete(coupon)
    return {"deleted": True, "code": coupon.code}


# ---------------------------------------------------------------------------
# Review moderation
# ---------------------------------------------------------------------------


@router.get("/admin/reviews", response_model=List[ReviewPublic])
def admin_list_reviews(
    hidden: Optional[bool] = Query(default=None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    reviews = review_service.list_all_reviews(db, hidden=hidden)
    return [review_public(r) for r in reviews]


@router.put("/admin/reviews/{review_id}/hide", response_model=ReviewPublic)
def admin_hide_review(
    review_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)
):
    review = review_service.set_hidden(db, review_id, hidden=True)
    audit_service.log(db, actor=admin, action="review.hide", entity_type="review", entity_id=review.id)
    return review_public(review)


@router.put("/admin/reviews/{review_id}/show", response_model=ReviewPublic)
def admin_show_review(
    review_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)
):
    review = review_service.set_hidden(db, review_id, hidden=False)
    audit_service.log(db, actor=admin, action="review.show", entity_type="review", entity_id=review.id)
    return review_public(review)


# ---------------------------------------------------------------------------
# Store settings
# ---------------------------------------------------------------------------


@router.get("/admin/settings", response_model=StoreSettingsPublic)
def admin_get_settings(db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    return settings_service.all_settings(db)


@router.put("/admin/settings", response_model=StoreSettingsPublic)
def admin_update_settings(
    data: StoreSettingsUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    updates = data.model_dump(exclude_unset=True, exclude_none=True)
    result = settings_service.update_settings(db, updates)
    audit_service.log(db, actor=admin, action="settings.update", entity_type="settings", detail=updates)
    return result


# ---------------------------------------------------------------------------
# Audit logs
# ---------------------------------------------------------------------------


@router.get("/admin/audit-logs", response_model=AuditLogList)
def admin_audit_logs(
    action: Optional[str] = Query(default=None),
    entity_type: Optional[str] = Query(default=None),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    from app.models import AuditLog

    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    total = query.count()
    logs = (
        query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .offset(pagination.offset())
        .limit(pagination.page_size)
        .all()
    )
    return AuditLogList(
        items=logs,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=(total + pagination.page_size - 1) // pagination.page_size,
    )
