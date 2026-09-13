"""In-app notification center."""

from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Notification, NotificationType, User


def notify(
    db: Session,
    *,
    user: User,
    type: NotificationType,
    title: str,
    body: str,
    link: Optional[str] = None,
) -> None:
    """Create an in-app notification (call within the business transaction)."""
    db.add(
        Notification(
            user_id=user.id,
            type=type,
            title=title,
            body=body,
            link=link,
        )
    )
