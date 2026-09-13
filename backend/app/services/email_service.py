"""Transactional email service.

Design:
- `queue_email()` renders the template and persists an `email_logs` row with
  status QUEUED inside the caller's transaction (atomic with the business op).
- A daemon worker thread picks up queued rows and sends them via SMTP.
- When EMAIL_ENABLED is false (development default), the row is marked SKIPPED
  so the whole pipeline is observable without a real SMTP server.

To add a channel later (SMS/push), mirror this pattern: persist an outbox row,
deliver from a worker.
"""

import smtplib
import threading
import time
from datetime import datetime
from email.message import EmailMessage
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.logging import get_logger
from app.models import EmailLog, EmailStatus

logger = get_logger(__name__)

_env = Environment(
    loader=FileSystemLoader("email_templates"),
    autoescape=select_autoescape(["html"]),
)

_worker_stop = threading.Event()


class EmailTemplateNotFoundError(Exception):
    pass


def render_template(template: str, context: Dict[str, Any]) -> tuple:
    """Return (html, text) for the given template name."""
    try:
        html_tmpl = _env.get_template(f"{template}.html")
        text_tmpl = _env.get_template(f"{template}.txt")
    except Exception as exc:
        raise EmailTemplateNotFoundError(f"Email template '{template}' is missing: {exc}") from exc
    html = html_tmpl.render(**context)
    text = text_tmpl.render(**context)
    return html, text


def queue_email(
    db: Session,
    *,
    to_email: str,
    subject: str,
    template: str,
    context: Dict[str, Any],
    related_type: Optional[str] = None,
    related_id: Optional[str] = None,
) -> Optional[EmailLog]:
    """Persist the email as an outbox row. Call within the business transaction."""
    if not to_email:
        return None
    context.setdefault("store_name", "ShelfSpace")
    context.setdefault("frontend_url", settings.FRONTEND_URL)
    db.add(
        EmailLog(
            to_email=to_email,
            subject=subject,
            template=template,
            context=context,
            status=EmailStatus.QUEUED,
            related_type=related_type,
            related_id=str(related_id) if related_id is not None else None,
        )
    )
    return None


def _send_smtp(log: EmailLog) -> None:
    html, text = render_template(log.template, log.context or {})
    msg = EmailMessage()
    msg["Subject"] = log.subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = log.to_email
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
        server.ehlo()
        server.starttls()
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)


def process_queue(batch_limit: int = 20) -> int:
    """Send queued emails. Returns number processed. Runs in the worker thread."""
    from app.core.database import SessionLocal

    session: Session = SessionLocal()
    processed = 0
    try:
        rows = (
            session.execute(
                select(EmailLog)
                .where(EmailLog.status == EmailStatus.QUEUED)
                .order_by(EmailLog.created_at)
                .limit(batch_limit)
            )
            .scalars()
            .all()
        )
        for row in rows:
            try:
                if not settings.EMAIL_ENABLED:
                    row.status = EmailStatus.SKIPPED
                    logger.info("Email skipped (delivery disabled): to=%s template=%s", row.to_email, row.template)
                else:
                    _send_smtp(row)
                    row.status = EmailStatus.SENT
                    row.sent_at = datetime.utcnow()
                    logger.info("Email sent: to=%s template=%s", row.to_email, row.template)
            except EmailTemplateNotFoundError as exc:
                row.status = EmailStatus.FAILED
                row.error = str(exc)[:500]
                logger.error("Email template missing: %s", exc)
            except Exception as exc:
                row.status = EmailStatus.FAILED
                row.error = str(exc)[:500]
                logger.error("Email send failed (to=%s): %s", row.to_email, exc)
            processed += 1
        session.commit()
    finally:
        session.close()
    return processed


def _worker_loop() -> None:  # pragma: no cover - background thread
    while not _worker_stop.is_set():
        try:
            process_queue()
        except Exception:
            logger.exception("Email worker iteration failed")
        _worker_stop.wait(3.0)


def start_worker() -> None:  # pragma: no cover
    if not settings.EMAIL_WORKER_ENABLED:
        logger.info("Email worker disabled by configuration")
        return
    thread = threading.Thread(target=_worker_loop, name="email-worker", daemon=True)
    thread.start()
    logger.info("Email worker started")


def stop_worker() -> None:  # pragma: no cover
    _worker_stop.set()


# Backwards-compatible helper used by the seed script to flush the queue once.
def drain_queue_once() -> int:
    return process_queue()


_time = time  # keep import used even if time-based logic changes
