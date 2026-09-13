"""Audit trail for important administrative and business operations."""

from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models import AuditLog

logger = get_logger(__name__)


def log(
    db: Session,
    *,
    actor: Optional[Any],
    action: str,
    entity_type: str,
    entity_id: Optional[Any] = None,
    detail: Optional[dict] = None,
) -> None:
    """Record an audit entry in the same transaction as the mutation itself."""
    try:
        db.add(
            AuditLog(
                actor_id=getattr(actor, "id", None),
                actor_name=getattr(actor, "full_name", None) or getattr(actor, "username", None),
                action=action,
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id is not None else None,
                detail=detail,
            )
        )
        db.flush()
    except Exception:  # auditing must never break the business operation
        db.rollback()
        logger.exception("Failed to write audit log for action=%s", action)
