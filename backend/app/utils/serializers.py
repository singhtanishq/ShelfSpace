"""ORM → API response serializers (explicit dicts validated by pydantic response models)."""

from typing import Optional

from app.models import Book, Order, ReturnItem, ReturnRequest, User


def author_public(author) -> dict:
    return {"id": author.id, "name": author.name, "slug": author.slug, "bio": author.bio}


def category_public(category) -> dict:
    return {
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
        "description": category.description,
    }


def publisher_public(publisher) -> dict:
    return {"id": publisher.id, "name": publisher.name, "slug": publisher.slug}


def available_quantity(book: Book) -> int:
    return book.inventory.available_quantity if book.inventory else 0


def book_card(book: Book) -> dict:
    return {
        "id": book.id,
        "title": book.title,
        "slug": book.slug,
        "cover_image": book.cover_image,
        "price": float(book.price),
        "discount_percent": float(book.discount_percent),
        "effective_price": float(book.effective_price),
        "rating_avg": float(book.rating_avg or 0),
        "rating_count": int(book.rating_count or 0),
        "is_active": bool(book.is_active),
        "is_featured": bool(book.is_featured),
        "authors": [author_public(a) for a in book.authors],
        "categories": [category_public(c) for c in book.categories],
        "available_quantity": available_quantity(book),
    }


def book_detail(book: Book) -> dict:
    data = book_card(book)
    data.update(
        {
            "isbn": book.isbn,
            "description": book.description,
            "language": book.language,
            "format": book.format.value if book.format else "paperback",
            "pages": book.pages,
            "published_year": book.published_year,
            "publisher": publisher_public(book.publisher) if book.publisher else None,
            "created_at": book.created_at,
            "stock_quantity": book.inventory.stock_quantity if book.inventory else 0,
            "reserved_quantity": book.inventory.reserved_quantity if book.inventory else 0,
            "low_stock_threshold": book.inventory.low_stock_threshold if book.inventory else 5,
            "sales_count": int(book.sales_count or 0),
        }
    )
    return data


def review_public(review) -> dict:
    return {
        "id": review.id,
        "book_id": review.book_id,
        "user_id": review.user_id,
        "rating": review.rating,
        "title": review.title,
        "content": review.content,
        "is_verified_purchase": review.is_verified_purchase,
        "is_hidden": review.is_hidden,
        "created_at": review.created_at,
        "updated_at": review.updated_at,
        "author_name": review.user.full_name if review.user else "Reader",
    }


def order_public(order: Order) -> dict:
    return {
        "id": order.id,
        "order_number": order.order_number,
        "user_id": order.user_id,
        "status": order.status.value,
        "payment_method": order.payment_method.value,
        "payment_status": order.payment_status.value,
        "subtotal": float(order.subtotal),
        "discount_total": float(order.discount_total),
        "shipping_fee": float(order.shipping_fee),
        "tax_total": float(order.tax_total),
        "total": float(order.total),
        "coupon_code": order.coupon_code,
        "shipping_address": order.shipping_address,
        "notes": order.notes,
        "placed_at": order.placed_at,
        "delivered_at": order.delivered_at,
        "cancelled_at": order.cancelled_at,
        "items": [
            {
                "id": item.id,
                "book_id": item.book_id,
                "title": item.title,
                "author_names": item.author_names,
                "cover_image": item.cover_image,
                "isbn": item.isbn,
                "unit_price": float(item.unit_price),
                "quantity": item.quantity,
                "line_total": float(item.line_total),
            }
            for item in order.items
        ],
        "status_history": [
            {
                "from_status": h.from_status.value if h.from_status else None,
                "to_status": h.to_status.value,
                "note": h.note,
                "created_at": h.created_at,
                "changed_by_id": h.changed_by_id,
            }
            for h in order.status_history
        ],
        "returns": [return_public(r) for r in order.returns],
    }


def return_public(request: ReturnRequest, order_number: Optional[str] = None) -> dict:
    return {
        "id": request.id,
        "return_number": request.return_number,
        "order_id": request.order_id,
        "order_number": order_number or (request.order.order_number if request.order else ""),
        "user_id": request.user_id,
        "type": request.type.value,
        "status": request.status.value,
        "reason": request.reason.value,
        "description": request.description,
        "refund_amount": float(request.refund_amount) if request.refund_amount is not None else None,
        "refund_status": request.refund_status.value,
        "admin_note": request.admin_note,
        "created_at": request.created_at,
        "decided_at": request.decided_at,
        "completed_at": request.completed_at,
        "items": [return_item_public(item) for item in request.items],
    }


def return_item_public(item: ReturnItem) -> dict:
    return {
        "order_item_id": item.order_item_id,
        "quantity": item.quantity,
        "title": item.order_item.title if item.order_item else "",
    }


def user_admin_public(user: User, order_count: int = 0, total_spent: float = 0) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": user.role.value,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at,
        "order_count": order_count,
        "total_spent": total_spent,
    }
