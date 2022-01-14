"""In-app notification center endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Notification, User
from app.schemas.order import NotificationList, NotificationPublic
from app.utils.exceptions import NotFoundError
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationList)
def list_notifications(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    base = db.query(Notification).filter(Notification.user_id == user.id)
    total = base.count()
    unread = base.filter(Notification.is_read.is_(False)).count()
    items = (
        base.order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset(pagination.offset())
        .limit(pagination.page_size)
        .all()
    )
    return NotificationList(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=(total + pagination.page_size - 1) // pagination.page_size,
        unread_count=unread,
    )


@router.get("/unread-count")
def unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    count = (
        db.query(func.count(Notification.id))
        .filter(Notification.user_id == user.id, Notification.is_read.is_(False))
        .scalar()
    )
    return {"count": count or 0}


@router.post("/{notification_id}/read", response_model=NotificationPublic)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != user.id:
        raise NotFoundError("Notification not found.")
    notification.is_read = True
    return notification


@router.post("/read-all")
def mark_all_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.query(Notification).filter(
        Notification.user_id == user.id, Notification.is_read.is_(False)
    ).update({"is_read": True})
    return {"ok": True}
