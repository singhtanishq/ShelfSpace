"""Reviews: creation gated by verified purchases, cached book rating aggregates."""

from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.models import Book, Order, OrderItem, OrderStatus, Review, User
from app.schemas.catalog import ReviewCreate, ReviewUpdate
from app.utils.exceptions import BusinessRuleError, ConflictError, NotFoundError

_PURCHASE_STATUSES = (OrderStatus.DELIVERED, OrderStatus.RETURNED)


def has_verified_purchase(db: Session, user_id: int, book_id: int) -> bool:
    return (
        db.query(OrderItem.id)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(
            Order.user_id == user_id,
            Order.status.in_(_PURCHASE_STATUSES),
            OrderItem.book_id == book_id,
        )
        .first()
        is not None
    )


def create_review(db: Session, user: User, book: Book, data: ReviewCreate) -> Review:
    if not book.is_active:
        raise NotFoundError("Book not found.")
    existing = db.query(Review).filter(Review.book_id == book.id, Review.user_id == user.id).first()
    if existing is not None:
        raise ConflictError("You have already reviewed this book. You can edit your existing review.")

    review = Review(
        book_id=book.id,
        user_id=user.id,
        rating=data.rating,
        title=data.title,
        content=data.content,
        is_verified_purchase=has_verified_purchase(db, user.id, book.id),
    )
    db.add(review)
    db.flush()
    _refresh_book_rating(db, book)
    return review


def update_review(db: Session, user: User, review_id: int, data: ReviewUpdate) -> Review:
    review = _get_review(db, review_id)
    if review.user_id != user.id:
        raise NotFoundError("Review not found.")
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        if value is not None:
            setattr(review, field, value)
    db.flush()
    _refresh_book_rating(db, review.book)
    return review


def delete_review(db: Session, user: User, review_id: int) -> None:
    review = _get_review(db, review_id)
    if review.user_id != user.id:
        raise NotFoundError("Review not found.")
    book = review.book
    db.delete(review)
    db.flush()
    _refresh_book_rating(db, book)


def set_hidden(db: Session, review_id: int, hidden: bool) -> Review:
    review = _get_review(db, review_id)
    review.is_hidden = hidden
    db.flush()
    _refresh_book_rating(db, review.book)
    return review


def list_reviews_for_book(
    db: Session, book: Book, *, page: int = 1, page_size: int = 10
) -> tuple:
    query = (
        db.query(Review)
        .options(selectinload(Review.user))
        .filter(Review.book_id == book.id, Review.is_hidden.is_(False))
        .order_by(Review.created_at.desc())
    )
    total = query.count()
    reviews = query.offset((page - 1) * page_size).limit(page_size).all()
    return reviews, total


def list_all_reviews(db: Session, *, hidden: Optional[bool] = None, book_id: Optional[int] = None) -> List[Review]:
    query = db.query(Review).options(selectinload(Review.user), selectinload(Review.book))
    if hidden is not None:
        query = query.filter(Review.is_hidden == hidden)
    if book_id is not None:
        query = query.filter(Review.book_id == book_id)
    return query.order_by(Review.created_at.desc()).limit(200).all()


def list_reviews_by_user(db: Session, user: User) -> List[Review]:
    return (
        db.query(Review)
        .options(selectinload(Review.book))
        .filter(Review.user_id == user.id)
        .order_by(Review.created_at.desc())
        .all()
    )


def _get_review(db: Session, review_id: int) -> Review:
    review = db.query(Review).options(selectinload(Review.book)).filter(Review.id == review_id).first()
    if review is None:
        raise NotFoundError("Review not found.")
    return review


def _refresh_book_rating(db: Session, book: Book) -> None:
    avg, count = (
        db.query(func.avg(Review.rating), func.count(Review.id))
        .filter(Review.book_id == book.id, Review.is_hidden.is_(False))
        .one()
    )
    book.rating_avg = round(float(avg), 2) if avg is not None else 0.0
    book.rating_count = int(count or 0)
