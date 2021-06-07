"""Order lifecycle: checkout, tracking, cancellation and status transitions.

Checkout is a single database transaction: inventory rows are locked
(SELECT ... FOR UPDATE), stock is validated and decremented, the order and
payment rows are created and the cart is cleared atomically — overselling and
half-committed orders are impossible.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session, selectinload

from app.models import (
    ALLOWED_STATUS_TRANSITIONS,
    Book,
    CANCELLABLE_STATUSES,
    Cart,
    CartItem,
    Coupon,
    Address,
    InventoryChangeType,
    InventoryTransaction,
    NotificationType,
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
    Payment,
    PaymentMethod,
    PaymentStatus,
    User,
)
from app.schemas.order import CheckoutRequest
from app.services import (
    coupon_service,
    email_service,
    inventory_service,
    notification_service,
    payment_service,
    settings_service,
)
from app.utils.exceptions import BusinessRuleError, NotFoundError, ValidationError

STATUS_LABELS = {
    "pending": "Pending",
    "confirmed": "Confirmed",
    "processing": "Processing",
    "shipped": "Shipped",
    "out_for_delivery": "Out for delivery",
    "delivered": "Delivered",
    "cancelled": "Cancelled",
    "returned": "Returned",
}


# ---------------------------------------------------------------------------
# Checkout
# ---------------------------------------------------------------------------


def checkout(db: Session, user: User, data: CheckoutRequest) -> Order:
    cart = (
        db.query(Cart)
        .options(
            selectinload(Cart.items)
            .selectinload(CartItem.book)
            .selectinload(Book.authors),
            selectinload(Cart.items).selectinload(CartItem.book).selectinload(Book.inventory),
        )
        .filter(Cart.user_id == user.id)
        .first()
    )
    if cart is None or not cart.items:
        raise BusinessRuleError("Your cart is empty.")

    shipping_address = _resolve_shipping_address(db, user, data)

    # Authoritative re-validation of every line against live (locked) stock.
    inventory_rows = {
        inv.book_id: inv
        for inv in inventory_service.lock_inventory(db, [item.book_id for item in cart.items])
    }
    for item in cart.items:
        book = item.book
        if book is None or not book.is_active:
            raise BusinessRuleError("One of the items in your cart is no longer available.")
        inv = inventory_rows[book.id]
        if item.quantity > inv.available_quantity:
            raise BusinessRuleError(
                f"Only {inv.available_quantity} unit(s) of '{book.title}' are available. "
                "Please adjust your cart."
            )

    # Totals are always computed server-side; client values are never trusted.
    subtotal = round(sum(float(item.book.effective_price) * item.quantity for item in cart.items), 2)

    discount = 0.0
    coupon = db.get(Coupon, cart.coupon_id) if cart.coupon_id else None
    if coupon is not None:
        coupon, discount = coupon_service.validate_coupon(db, coupon.code, subtotal)

    shipping_fee = _shipping_fee(db, subtotal - discount)
    tax = round((subtotal - discount) * settings_service.get_float(db, "tax_percent") / 100, 2)
    total = round(subtotal - discount + shipping_fee + tax, 2)

    # Payment authorization (mock gateway; COD is captured on delivery).
    method = PaymentMethod(data.payment_method)
    transaction_ref: Optional[str] = None
    payment_status = PaymentStatus.PENDING
    if method != PaymentMethod.COD:
        reference_hint = data.card_number if method == PaymentMethod.CARD else data.upi_id
        transaction_ref = payment_service.charge(
            amount=total, method=method, reference_hint=reference_hint
        )
        payment_status = PaymentStatus.PAID

    order = Order(
        order_number=f"tmp-{uuid.uuid4().hex[:12]}",  # provisional; finalized below once id is known
        user_id=user.id,
        status=OrderStatus.PENDING,
        payment_method=method,
        payment_status=payment_status,
        subtotal=subtotal,
        discount_total=discount,
        shipping_fee=shipping_fee,
        tax_total=tax,
        total=total,
        coupon_id=coupon.id if coupon else None,
        coupon_code=coupon.code if coupon else None,
        shipping_address=shipping_address,
        notes=data.notes,
    )
    db.add(order)
    db.flush()
    order.order_number = f"SS-{datetime.now(timezone.utc):%Y%m%d}-{order.id:05d}"
    db.flush()

    for item in cart.items:
        book = item.book
        unit_price = float(book.effective_price)
        order.items.append(
            OrderItem(
                book_id=book.id,
                title=book.title,
                author_names=book.author_names(),
                isbn=book.isbn,
                cover_image=book.cover_image,
                unit_price=unit_price,
                quantity=item.quantity,
                line_total=round(unit_price * item.quantity, 2),
            )
        )
        inv = inventory_rows[book.id]
        inv.stock_quantity -= item.quantity
        db.add(
            InventoryTransaction(
                book_id=book.id,
                change=-item.quantity,
                change_type=InventoryChangeType.SALE,
                balance_after=inv.stock_quantity,
                reference_type="order",
                reference_id=order.order_number,
                note=f"Sale via checkout {order.order_number}",
            )
        )
        book.sales_count += item.quantity

    db.add(
        Payment(
            order_id=order.id,
            provider="mock",
            method=method,
            amount=total,
            status=payment_status,
            transaction_ref=transaction_ref,
            paid_at=datetime.now(timezone.utc) if payment_status == PaymentStatus.PAID else None,
        )
    )
    db.add(
        OrderStatusHistory(
            order_id=order.id,
            from_status=None,
            to_status=OrderStatus.PENDING,
            changed_by_id=user.id,
            note="Order placed",
        )
    )
    if coupon is not None:
        coupon.used_count += 1

    # Empty the cart as part of the same transaction.
    cart.items.clear()
    cart.coupon_id = None

    _queue_order_email(
        db,
        user,
        order,
        template="order_confirmation",
        subject=f"Order {order.order_number} confirmed",
        headline="Order confirmed",
        message=(
            "Thank you for your order! It is being processed and you will receive updates "
            "as it moves through fulfilment."
        ),
    )
    notification_service.notify(
        db,
        user=user,
        type=NotificationType.ORDER,
        title=f"Order {order.order_number} placed",
        body=f"Your order for {len(order.items)} item(s) totalling {total:.2f} has been placed.",
        link=f"/account/orders/{order.order_number}",
    )
    return order


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------


def get_order(
    db: Session, order_number: str, *, user: Optional[User] = None, require_admin: bool = False
) -> Order:
    order = (
        db.query(Order)
        .options(
            selectinload(Order.items),
            selectinload(Order.status_history),
            selectinload(Order.returns).selectinload("items"),
        )
        .filter(Order.order_number == order_number)
        .first()
    )
    if order is None:
        raise NotFoundError("Order not found.")
    if not require_admin and user is not None and order.user_id != user.id:
        raise NotFoundError("Order not found.")  # do not leak other users' order numbers
    return order


def list_orders(
    db: Session,
    *,
    user: Optional[User] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> tuple:
    query = (
        db.query(Order)
        .options(selectinload(Order.items), selectinload(Order.returns).selectinload("items"))
        .order_by(Order.placed_at.desc(), Order.id.desc())
    )
    if user is not None:
        query = query.filter(Order.user_id == user.id)
    if status:
        query = query.filter(Order.status == OrderStatus(status))
    if q:
        query = query.filter(Order.order_number.ilike(f"%{q.strip()}%"))
    total = query.count()
    orders = query.offset((page - 1) * page_size).limit(page_size).all()
    return orders, total


# ---------------------------------------------------------------------------
# Cancellation & status transitions
# ---------------------------------------------------------------------------


def cancel_order(
    db: Session, order: Order, actor: User, note: Optional[str] = None, is_admin: bool = False
) -> Order:
    if order.status not in CANCELLABLE_STATUSES:
        raise BusinessRuleError(
            f"An order with status '{STATUS_LABELS[order.status.value]}' can no longer be cancelled."
        )
    return transition_status(
        db, order, OrderStatus.CANCELLED, actor=actor, note=note or "Order cancelled", is_admin=is_admin
    )


def transition_status(
    db: Session,
    order: Order,
    new_status: OrderStatus,
    *,
    actor: User,
    note: Optional[str],
    is_admin: bool = False,
) -> Order:
    """Apply a validated status transition with all side effects."""
    if order.status == new_status:
        raise BusinessRuleError("The order is already in this status.")
    if new_status not in ALLOWED_STATUS_TRANSITIONS.get(order.status, set()):
        raise BusinessRuleError(
            f"Transition '{STATUS_LABELS[order.status.value]}' → "
            f"'{STATUS_LABELS[new_status.value]}' is not allowed."
        )
    if new_status == OrderStatus.CANCELLED and not is_admin and actor.id != order.user_id:
        raise NotFoundError("Order not found.")

    previous = order.status
    order.status = new_status
    now = datetime.now(timezone.utc)

    if new_status == OrderStatus.CANCELLED:
        order.cancelled_at = now
        for item in order.items:
            if item.book_id is not None:
                try:
                    inv = inventory_service.adjust_stock(
                        db,
                        book_id=item.book_id,
                        change=item.quantity,
                        change_type=InventoryChangeType.RETURN_TO_STOCK,
                        reference_type="order_cancel",
                        reference_id=order.order_number,
                        note=f"Restocked after cancellation of {order.order_number}",
                        created_by=actor.id,
                    )
                except (NotFoundError, BusinessRuleError):
                    inv = None  # inventory row gone (book deleted); nothing to restock
                if inv is not None:
                    book = db.get(Book, item.book_id)
                    if book is not None:
                        book.sales_count = max(book.sales_count - item.quantity, 0)
        if order.payment_status == PaymentStatus.PAID:
            order.payment_status = PaymentStatus.REFUNDED
            _record_refund_payment(db, order)
        message = "Your order has been cancelled."
        if order.payment_status == PaymentStatus.REFUNDED:
            message += " Your payment has been refunded to the original payment method."
        headline = "Order cancelled"

    elif new_status == OrderStatus.DELIVERED:
        order.delivered_at = now
        if order.payment_method == PaymentMethod.COD and order.payment_status == PaymentStatus.PENDING:
            order.payment_status = PaymentStatus.PAID
            _record_cod_capture(db, order)
        message = "Your order has been delivered. We hope you enjoy your books!"
        headline = "Delivered"

    elif new_status == OrderStatus.RETURNED:
        message = "Your return has been completed and the refund is on its way."
        headline = "Returned"

    else:
        message = f"Good news! Your order is now {STATUS_LABELS[new_status.value].lower()}."
        headline = STATUS_LABELS[new_status.value]

    db.add(
        OrderStatusHistory(
            order_id=order.id,
            from_status=previous,
            to_status=new_status,
            changed_by_id=actor.id,
            note=note,
        )
    )
    _queue_order_email(
        db,
        order.user,
        order,
        template="order_status",
        subject=f"Update on order {order.order_number}",
        headline=headline,
        message=message,
    )
    notification_service.notify(
        db,
        user=order.user,
        type=NotificationType.ORDER,
        title=f"Order {order.order_number}: {STATUS_LABELS[new_status.value]}",
        body=message,
        link=f"/account/orders/{order.order_number}",
    )
    return order


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_shipping_address(db: Session, user: User, data: CheckoutRequest) -> dict:
    if data.address_id is not None:
        address = db.get(Address, data.address_id)
        if address is None or address.user_id != user.id:
            raise NotFoundError("Selected address not found.")
        return {
            "full_name": address.full_name,
            "phone": address.phone,
            "line1": address.line1,
            "line2": address.line2,
            "city": address.city,
            "state": address.state,
            "postal_code": address.postal_code,
            "country": address.country,
        }
    if data.shipping_address is not None:
        return data.shipping_address.model_dump()
    raise ValidationError("A shipping address is required to place an order.")


def _shipping_fee(db: Session, discounted_subtotal: float) -> float:
    fee = settings_service.get_float(db, "shipping_fee")
    threshold = settings_service.get_float(db, "free_shipping_threshold")
    if threshold > 0 and discounted_subtotal >= threshold:
        return 0.0
    return round(fee, 2)


def _record_cod_capture(db: Session, order: Order) -> None:
    payment = next((p for p in order.payments if p.status == PaymentStatus.PENDING), None)
    if payment is not None:
        payment.status = PaymentStatus.PAID
        payment.paid_at = datetime.now(timezone.utc)
        payment.transaction_ref = f"mock_cod_{order.order_number}"
    else:
        db.add(
            Payment(
                order_id=order.id,
                provider="mock",
                method=order.payment_method,
                amount=order.total,
                status=PaymentStatus.PAID,
                transaction_ref=f"mock_cod_{order.order_number}",
                paid_at=datetime.now(timezone.utc),
            )
        )


def _record_refund_payment(db: Session, order: Order) -> None:
    db.add(
        Payment(
            order_id=order.id,
            provider="mock",
            method=order.payment_method,
            amount=order.total,
            status=PaymentStatus.REFUNDED,
            transaction_ref=f"mock_refund_{order.order_number}",
            paid_at=datetime.now(timezone.utc),
        )
    )


def _queue_order_email(
    db: Session, user: User, order: Order, *, template: str, subject: str, headline: str, message: str
) -> None:
    email_service.queue_email(
        db,
        to_email=user.email,
        subject=subject,
        template=template,
        context={
            "user_name": user.full_name,
            "order_number": order.order_number,
            "items": [
                {"title": i.title, "quantity": i.quantity, "line_total": float(i.line_total)}
                for i in order.items
            ],
            "total": float(order.total),
            "currency": settings_service.get_str(db, "currency"),
            "payment_method": order.payment_method.value,
            "status_label": STATUS_LABELS[order.status.value],
            "headline": headline,
            "message": message,
            "support_email": settings_service.get_str(db, "support_email"),
        },
        related_type="order",
        related_id=order.order_number,
    )
