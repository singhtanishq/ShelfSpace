"""Return and replacement request lifecycle.

Business rules (configurable via store settings):
- Orders are eligible after delivery, within `return_window_days`.
- One open (requested/approved) request per order at a time.
- Per-item quantities are capped by the purchased quantity minus quantities
  already covered by active or completed requests.
- Completed returns restock the items and settle the refund (mock).
- Completed replacements issue new copies from stock.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session, selectinload

from app.models import (
    InventoryChangeType,
    NotificationType,
    Order,
    OrderItem,
    OrderStatus,
    PaymentStatus,
    RefundStatus,
    ReturnItem,
    ReturnReason,
    ReturnRequest,
    ReturnType,
    ReturnStatus,
    User,
)
from app.schemas.order import ReturnCreate, ReturnDecision
from app.services import email_service, inventory_service, notification_service, settings_service
from app.utils.exceptions import BusinessRuleError, NotFoundError, ValidationError


def return_window_days(db: Session) -> int:
    return settings_service.get_int(db, "return_window_days")


def _eligible_order(db: Session, order_number: str, user: Optional[User], require_admin: bool) -> Order:
    order = (
        db.query(Order)
        .options(selectinload(Order.items), selectinload(Order.returns).selectinload(ReturnRequest.items))
        .filter(Order.order_number == order_number)
        .first()
    )
    if order is None:
        raise NotFoundError("Order not found.")
    if not require_admin and user is not None and order.user_id != user.id:
        raise NotFoundError("Order not found.")
    return order


def eligibility(db: Session, order: Order) -> dict:
    """Explain whether/why the order can (not) be returned or replaced."""
    if order.status not in (OrderStatus.DELIVERED, OrderStatus.RETURNED):
        return {"eligible": False, "reason": "Only delivered orders can be returned or replaced."}
    if order.delivered_at is None:
        return {"eligible": False, "reason": "Delivery date is not recorded for this order."}
    delivered = order.delivered_at if order.delivered_at.tzinfo else order.delivered_at.replace(tzinfo=timezone.utc)
    days_since = (datetime.now(timezone.utc) - delivered).days
    window = return_window_days(db)
    if days_since > window:
        return {
            "eligible": False,
            "reason": f"The return window of {window} days after delivery has passed.",
        }
    open_request = any(r.status in (ReturnStatus.REQUESTED, ReturnStatus.APPROVED) for r in order.returns)
    if open_request:
        return {"eligible": False, "reason": "There is already an open request for this order."}
    remaining = _remaining_quantities(db, order)
    if all(qty <= 0 for qty in remaining.values()):
        return {"eligible": False, "reason": "All items in this order have already been returned."}
    return {"eligible": True, "reason": None, "days_since_delivery": days_since, "window_days": window}


def _remaining_quantities(db: Session, order: Order) -> dict:
    """Per order_item quantity still available for a new request."""
    consumed: dict = {item.id: 0 for item in order.items}
    for request in order.returns:
        if request.status in (ReturnStatus.REQUESTED, ReturnStatus.APPROVED, ReturnStatus.COMPLETED):
            for ri in request.items:
                consumed[ri.order_item_id] = consumed.get(ri.order_item_id, 0) + ri.quantity
    return {item.id: item.quantity - consumed.get(item.id, 0) for item in order.items}


def create_request(db: Session, user: User, order_number: str, data: ReturnCreate) -> ReturnRequest:
    order = _eligible_order(db, order_number, user, require_admin=False)
    if order.user_id != user.id:
        raise NotFoundError("Order not found.")
    info = eligibility(db, order)
    if not info["eligible"]:
        raise BusinessRuleError(info["reason"])

    items_by_id = {item.id: item for item in order.items}
    remaining = _remaining_quantities(db, order)
    for entry in data.items:
        item = items_by_id.get(entry.order_item_id)
        if item is None:
            raise ValidationError("One of the selected items does not belong to this order.")
        if entry.quantity > remaining[item.id]:
            raise ValidationError(
                f"Only {remaining[item.id]} of '{item.title}' can still be returned/replaced."
            )

    request = ReturnRequest(
        return_number=f"tmp-{uuid.uuid4().hex[:12]}",  # provisional; finalized below once id is known
        order_id=order.id,
        user_id=user.id,
        type=ReturnType(data.type),
        status=ReturnStatus.REQUESTED,
        reason=ReturnReason(data.reason),
        description=data.description,
        refund_amount=None,
    )
    db.add(request)
    db.flush()
    request.return_number = f"RT-{request.id:05d}"
    db.flush()

    for entry in data.items:
        db.add(ReturnItem(return_id=request.id, order_item_id=entry.order_item_id, quantity=entry.quantity))

    if data.type == "return":
        refund = 0.0
        for entry in data.items:
            item = items_by_id[entry.order_item_id]
            refund += float(item.unit_price) * entry.quantity
        request.refund_amount = round(refund, 2)

    db.flush()
    _queue_request_email(
        db,
        user,
        request,
        order,
        headline="Request received",
        message="We have received your request and our team will review it shortly.",
    )
    notification_service.notify(
        db,
        user=user,
        type=NotificationType.RETURN,
        title=f"{data.type.capitalize()} request {request.return_number} submitted",
        body="We will review your request and update you shortly.",
        link=f"/account/orders/{order.order_number}",
    )
    return request


def list_requests(db: Session, *, user: Optional[User] = None, status: Optional[str] = None, type: Optional[str] = None) -> List[ReturnRequest]:
    query = (
        db.query(ReturnRequest)
        .options(selectinload(ReturnRequest.items).selectinload(ReturnItem.order_item))
        .order_by(ReturnRequest.created_at.desc())
    )
    if user is not None:
        query = query.filter(ReturnRequest.user_id == user.id)
    if status:
        query = query.filter(ReturnRequest.status == ReturnStatus(status))
    if type:
        query = query.filter(ReturnRequest.type == ReturnType(type))
    return query.all()


def decide(db: Session, admin: User, request_id: int, decision: str, data: ReturnDecision) -> ReturnRequest:
    request = (
        db.query(ReturnRequest)
        .options(selectinload(ReturnRequest.items).selectinload(ReturnItem.order_item), selectinload(ReturnRequest.order))
        .filter(ReturnRequest.id == request_id)
        .first()
    )
    if request is None:
        raise NotFoundError("Request not found.")
    order = request.order

    if decision == "approve":
        if request.status != ReturnStatus.REQUESTED:
            raise BusinessRuleError("Only pending requests can be approved.")
        request.status = ReturnStatus.APPROVED
        if request.type == ReturnType.RETURN:
            request.refund_status = RefundStatus.INITIATED
        message = "Your request has been approved."
        if request.type == ReturnType.RETURN:
            message += " Our courier partner will collect the package within 1-2 business days."
        else:
            message += " Your replacement will be dispatched shortly."
        headline = "Request approved"

    elif decision == "reject":
        if request.status != ReturnStatus.REQUESTED:
            raise BusinessRuleError("Only pending requests can be rejected.")
        request.status = ReturnStatus.REJECTED
        message = "Unfortunately your request has been rejected."
        headline = "Request rejected"

    elif decision == "complete":
        if request.status != ReturnStatus.APPROVED:
            raise BusinessRuleError("Only approved requests can be completed.")
        _complete_request(db, request)
        message = "Your request has been completed."
        headline = "Request completed"
    else:
        raise ValueError("Unknown decision")

    request.decided_by_id = admin.id
    request.decided_at = datetime.now(timezone.utc)
    request.admin_note = data.note

    _queue_request_email(db, request.user, request, order, headline=headline, message=message)
    notification_service.notify(
        db,
        user=request.user,
        type=NotificationType.RETURN,
        title=f"{request.type.value.capitalize()} request {request.return_number}: {decision}",
        body=message,
        link=f"/account/orders/{order.order_number}",
    )
    return request


def _complete_request(db: Session, request: ReturnRequest) -> None:
    order = request.order
    request.status = ReturnStatus.COMPLETED
    request.completed_at = datetime.now(timezone.utc)

    if request.type == ReturnType.RETURN:
        for ri in request.items:
            if ri.order_item.book_id is not None:
                try:
                    inventory_service.adjust_stock(
                        db,
                        book_id=ri.order_item.book_id,
                        change=ri.quantity,
                        change_type=InventoryChangeType.RETURN_TO_STOCK,
                        reference_type="return",
                        reference_id=request.return_number,
                        note=f"Restocked from return {request.return_number}",
                        created_by=request.decided_by_id,
                    )
                except (NotFoundError, BusinessRuleError):
                    pass
        request.refund_status = RefundStatus.COMPLETED
        remaining = _remaining_quantities(db, order)
        if order.status == OrderStatus.DELIVERED:
            if all(qty <= 0 for qty in remaining.values()):
                order.status = OrderStatus.RETURNED
            if order.payment_status == PaymentStatus.PAID:
                order.payment_status = PaymentStatus.REFUNDED
    else:  # replacement: issue new copies from stock
        for ri in request.items:
            if ri.order_item.book_id is not None:
                try:
                    inventory_service.adjust_stock(
                        db,
                        book_id=ri.order_item.book_id,
                        change=-ri.quantity,
                        change_type=InventoryChangeType.REPLACEMENT_ISSUE,
                        reference_type="replacement",
                        reference_id=request.return_number,
                        note=f"Replacement issued for {request.return_number}",
                        created_by=request.decided_by_id,
                        allow_negative=True,
                    )
                except (NotFoundError, BusinessRuleError):
                    pass


def _queue_request_email(
    db: Session, user: User, request: ReturnRequest, order: Order, *, headline: str, message: str
) -> None:
    email_service.queue_email(
        db,
        to_email=user.email,
        subject=f"{request.type.value.capitalize()} request {request.return_number} update",
        template="return_update",
        context={
            "user_name": user.full_name,
            "request_type": request.type.value,
            "return_number": request.return_number,
            "headline": headline,
            "message": message,
            "note": request.admin_note,
            "refund_amount": float(request.refund_amount) if request.refund_amount is not None else None,
            "refund_status": request.refund_status.value,
            "support_email": settings_service.get_str(db, "support_email"),
        },
        related_type="return",
        related_id=request.return_number,
    )
