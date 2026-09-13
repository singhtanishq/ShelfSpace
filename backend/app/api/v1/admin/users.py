"""Admin: user management."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user
from app.core.database import get_db
from app.models import Order, OrderStatus, PaymentStatus, User, UserRole
from app.schemas.user import AdminUserPublic, AdminUserUpdate
from app.services import audit_service, notification_service
from app.utils.exceptions import BusinessRuleError, NotFoundError
from app.utils.pagination import PaginationParams
from app.utils.serializers import user_admin_public

router = APIRouter(prefix="/admin", tags=["admin-users"])


@router.get("/admin/users", response_model=List[AdminUserPublic])
def admin_list_users(
    q: Optional[str] = Query(default=None, max_length=120, description="Name/email/username search"),
    role: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    query = db.query(User)
    if q:
        term = f"%{q}%"
        query = query.filter(
            User.full_name.ilike(term) | User.email.ilike(term) | User.username.ilike(term)
        )
    if role:
        query = query.filter(User.role == UserRole(role))
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    total = query.count()
    users = (
        query.order_by(User.created_at.desc())
        .offset(pagination.offset())
        .limit(pagination.page_size)
        .all()
    )
    stats = _user_order_stats(db)
    return [
        user_admin_public(
            u,
            order_count=stats.get(u.id, {}).get("orders", 0),
            total_spent=stats.get(u.id, {}).get("spent", 0.0),
        )
        for u in users
    ]


@router.get("/admin/users/{user_id}", response_model=AdminUserPublic)
def admin_get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.")
    stats = _user_order_stats(db).get(user_id, {"orders": 0, "spent": 0.0})
    return user_admin_public(user, order_count=stats["orders"], total_spent=stats["spent"])


@router.put("/admin/users/{user_id}", response_model=AdminUserPublic)
def admin_update_user(
    user_id: int,
    data: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.")
    if user.id == admin.id and (data.role == "customer" or data.is_active is False):
        raise BusinessRuleError("You cannot demote or deactivate your own admin account.")

    changes = {}
    if data.role is not None and data.role != user.role.value:
        user.role = UserRole(data.role)
        changes["role"] = data.role
    if data.is_active is not None and data.is_active != user.is_active:
        user.is_active = data.is_active
        changes["is_active"] = data.is_active
        if not data.is_active:
            notification_service.notify(
                db,
                user=user,
                type=notification_service.NotificationType.ACCOUNT,
                title="Account deactivated",
                body="Your account has been deactivated by an administrator. Contact support for assistance.",
            )
    if data.full_name is not None:
        user.full_name = data.full_name
        changes["full_name"] = data.full_name
    if data.phone is not None:
        user.phone = data.phone
        changes["phone"] = data.phone

    audit_service.log(db, actor=admin, action="user.update", entity_type="user", entity_id=user.id, detail=changes)
    stats = _user_order_stats(db).get(user_id, {"orders": 0, "spent": 0.0})
    return user_admin_public(user, order_count=stats["orders"], total_spent=stats["spent"])


@router.delete("/admin/users/{user_id}")
def admin_delete_user(
    user_id: int,
    hard: bool = Query(default=False),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Deactivate (default) or hard-delete users with no order history."""
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.")
    if user.id == admin.id:
        raise BusinessRuleError("You cannot delete your own admin account.")

    has_orders = db.query(Order.id).filter(Order.user_id == user.id).first() is not None
    if hard:
        if has_orders:
            raise BusinessRuleError(
                "This user has order history and cannot be permanently deleted. Deactivate the account instead."
            )
        audit_service.log(db, actor=admin, action="user.delete", entity_type="user", entity_id=user.id, detail={"username": user.username})
        db.delete(user)
        return {"deleted": True, "username": user.username}
    user.is_active = False
    audit_service.log(db, actor=admin, action="user.deactivate", entity_type="user", entity_id=user.id, detail={"username": user.username})
    return {"deactivated": True, "username": user.username}


def _user_order_stats(db: Session) -> dict:
    rows = (
        db.query(
            Order.user_id,
            func.count(Order.id),
            func.coalesce(func.sum(Order.total), 0.0),
        )
        .filter(
            Order.status.in_([s for s in OrderStatus if s != OrderStatus.CANCELLED]),
            Order.payment_status.in_([PaymentStatus.PAID, PaymentStatus.REFUNDED]),
        )
        .group_by(Order.user_id)
        .all()
    )
    return {row[0]: {"orders": int(row[1]), "spent": float(row[2])} for row in rows}
