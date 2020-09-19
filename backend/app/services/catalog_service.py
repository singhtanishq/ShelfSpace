"""Catalog business logic: public browsing/search and admin book management."""

import os
import secrets
import uuid
from typing import List, Optional, Tuple

from PIL import Image, UnidentifiedImageError
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.database import media_path
from app.core.logging import get_logger
from app.models import Author, Book, BookFormat, Category, Inventory, InventoryChangeType, Publisher
from app.models.catalog import make_unique_slug
from app.schemas.catalog import BookCreate, BookUpdate, TermCreate, TermUpdate
from app.services import audit_service
from app.utils.exceptions import BusinessRuleError, NotFoundError, ValidationError

logger = get_logger(__name__)

ALLOWED_COVER_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_COVER_SIZE_BYTES = 5 * 1024 * 1024


# ---------------------------------------------------------------------------
# Public queries
# ---------------------------------------------------------------------------


def query_books(
    db: Session,
    *,
    q: Optional[str] = None,
    category_slug: Optional[str] = None,
    author_slug: Optional[str] = None,
    language: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    in_stock: bool = False,
    include_inactive: bool = False,
    sort: str = "popularity",
    page: int = 1,
    page_size: int = 12,
) -> Tuple[List[Book], int]:
    """Search + filter + sort the active catalog. Returns (books, total)."""
    query = db.query(Book).options(
        selectinload(Book.authors), selectinload(Book.categories), selectinload(Book.inventory)
    )
    if not include_inactive:
        query = query.filter(Book.is_active.is_(True))

    if q:
        term = f"%{q.strip()}%"
        like = or_(
            Book.title.ilike(term),
            Book.isbn.ilike(term),
            Book.description.ilike(term),
        )
        author_ids = [row[0] for row in db.query(Author.id).filter(Author.name.ilike(term)).all()]
        publisher_ids = [row[0] for row in db.query(Publisher.id).filter(Publisher.name.ilike(term)).all()]
        query = query.outerjoin(Book.authors).outerjoin(Book.publisher).filter(
            or_(like, Author.id.in_(author_ids), Publisher.id.in_(publisher_ids))
        ).distinct()

    if category_slug:
        query = query.join(Book.categories).filter(Category.slug == category_slug)
    if author_slug:
        query = query.join(Book.authors).filter(Author.slug == author_slug)
    if language:
        query = query.filter(Book.language == language)
    if min_price is not None:
        query = query.filter(Book.price >= min_price)
    if max_price is not None:
        query = query.filter(Book.price <= max_price)
    if min_rating is not None and min_rating > 0:
        query = query.filter(Book.rating_avg >= min_rating, Book.rating_count > 0)
    if in_stock:
        query = query.join(Book.inventory).filter(Inventory.stock_quantity > 0)

    total = query.count()

    order_by = {
        "newest": Book.created_at.desc(),
        "price_asc": Book.price.asc(),
        "price_desc": Book.price.desc(),
        "rating": Book.rating_avg.desc(),
        "title": Book.title.asc(),
        "popularity": Book.sales_count.desc(),
    }.get(sort, Book.sales_count.desc())
    query = query.order_by(order_by, Book.id.asc())

    return query.offset((page - 1) * page_size).limit(page_size).all(), total


def get_book_by_slug(db: Session, slug: str, include_inactive: bool = False) -> Book:
    book = (
        db.query(Book)
        .options(
            selectinload(Book.authors),
            selectinload(Book.categories),
            selectinload(Book.inventory),
            selectinload(Book.publisher),
        )
        .filter(Book.slug == slug)
        .first()
    )
    if book is None or (book.is_active is False and not include_inactive):
        raise NotFoundError("Book not found.")
    return book


def get_related_books(db: Session, book: Book, limit: int = 8) -> Tuple[List[Book], List[Book]]:
    """Books sharing a category, then other books by the same authors."""
    category_ids = [c.id for c in book.categories]
    author_ids = [a.id for a in book.authors]

    related: List[Book] = []
    if category_ids:
        related = (
            db.query(Book)
            .options(selectinload(Book.authors), selectinload(Book.inventory))
            .filter(Book.is_active.is_(True), Book.id != book.id)
            .join(Book.categories)
            .filter(Category.id.in_(category_ids))
            .order_by(Book.sales_count.desc())
            .limit(limit)
            .all()
        )
    by_same_author: List[Book] = []
    if author_ids:
        excluded = {book.id} | {b.id for b in related}
        by_same_author = (
            db.query(Book)
            .options(selectinload(Book.authors), selectinload(Book.inventory))
            .filter(Book.is_active.is_(True), Book.id != book.id)
            .join(Book.authors)
            .filter(Author.id.in_(author_ids), ~Book.id.in_(excluded))
            .limit(limit)
            .all()
        )
    return related, by_same_author


def get_home_feed(db: Session, per_section: int = 8) -> dict:
    base = (
        db.query(Book)
        .options(selectinload(Book.authors), selectinload(Book.inventory))
        .filter(Book.is_active.is_(True))
    )
    featured = base.filter(Book.is_featured.is_(True)).order_by(Book.sales_count.desc()).limit(per_section).all()
    best_sellers = base.order_by(Book.sales_count.desc()).limit(per_section).all()
    new_arrivals = base.order_by(Book.created_at.desc()).limit(per_section).all()
    categories = db.query(Category).order_by(Category.name).all()
    return {
        "featured": featured,
        "best_sellers": best_sellers,
        "new_arrivals": new_arrivals,
        "categories": categories,
    }


def get_facets(db: Session) -> dict:
    price_min, price_max = (
        db.query(func.min(Book.price), func.max(Book.price)).filter(Book.is_active.is_(True)).one()
    )
    languages = [
        row[0]
        for row in db.query(Book.language).filter(Book.is_active.is_(True)).distinct().order_by(Book.language)
    ]
    categories = db.query(Category).order_by(Category.name).all()
    authors = db.query(Author).order_by(Author.name).all()
    return {
        "price_min": float(price_min or 0),
        "price_max": float(price_max or 0),
        "languages": languages,
        "categories": categories,
        "authors": authors,
    }


# ---------------------------------------------------------------------------
# Admin CRUD
# ---------------------------------------------------------------------------


def create_book(db: Session, data: BookCreate, actor) -> Book:
    _validate_refs(db, data.author_ids, data.category_ids, data.publisher_id)
    slug = make_unique_slug(None, Book, data.title, db)
    book = Book(
        title=data.title.strip(),
        slug=slug,
        isbn=data.isbn,
        description=data.description,
        language=data.language,
        format=BookFormat(data.format),
        pages=data.pages,
        published_year=data.published_year,
        publisher_id=data.publisher_id,
        price=data.price,
        discount_percent=data.discount_percent,
        is_active=data.is_active,
        is_featured=data.is_featured,
    )
    if data.author_ids:
        book.authors = db.query(Author).filter(Author.id.in_(data.author_ids)).all()
    if data.category_ids:
        book.categories = db.query(Category).filter(Category.id.in_(data.category_ids)).all()
    db.add(book)
    db.flush()

    db.add(
        Inventory(
            book_id=book.id,
            stock_quantity=data.stock_quantity,
            low_stock_threshold=data.low_stock_threshold,
        )
    )
    if data.stock_quantity > 0:
        from app.models import InventoryTransaction

        db.add(
            InventoryTransaction(
                book_id=book.id,
                change=data.stock_quantity,
                change_type=InventoryChangeType.RESTOCK,
                balance_after=data.stock_quantity,
                reference_type="book_create",
                note="Initial stock",
                created_by=getattr(actor, "id", None),
            )
        )
    audit_service.log(db, actor=actor, action="book.create", entity_type="book", entity_id=book.id, detail={"title": book.title})
    return book


def update_book(db: Session, book_id: int, data: BookUpdate, actor) -> Book:
    book = _get_book_or_404(db, book_id)
    updates = data.model_dump(exclude_unset=True, exclude={"author_ids", "category_ids"})
    _validate_refs(
        db,
        data.author_ids if data.author_ids is not None else None,
        data.category_ids if data.category_ids is not None else None,
        updates.get("publisher_id", book.publisher_id),
    )
    if "format" in updates and updates["format"]:
        updates["format"] = BookFormat(updates["format"])
    if "title" in updates and updates["title"] and updates["title"].strip() != book.title:
        book.slug = make_unique_slug(None, Book, updates["title"], db)
    for field, value in updates.items():
        if value is not None:
            setattr(book, field, value)
    if data.author_ids is not None:
        _validate_refs(db, data.author_ids, None, None)
        book.authors = db.query(Author).filter(Author.id.in_(data.author_ids)).all()
    if data.category_ids is not None:
        _validate_refs(db, None, data.category_ids, None)
        book.categories = db.query(Category).filter(Category.id.in_(data.category_ids)).all()
    audit_service.log(db, actor=actor, action="book.update", entity_type="book", entity_id=book.id, detail={"fields": list(updates.keys())})
    return book


def delete_book(db: Session, book_id: int, actor, hard: bool = False) -> dict:
    """Archive (default) or hard-delete when unreferenced."""
    from app.models import OrderItem

    book = _get_book_or_404(db, book_id)
    referenced = db.query(OrderItem.id).filter(OrderItem.book_id == book_id).first() is not None
    if hard or not referenced:
        if referenced:
            raise BusinessRuleError(
                "This book appears in existing orders and cannot be permanently deleted. Archive it instead."
            )
        title = book.title
        db.delete(book)
        audit_service.log(db, actor=actor, action="book.delete", entity_type="book", entity_id=book_id, detail={"title": title})
        return {"deleted": True, "title": title}
    book.is_active = False
    book.is_featured = False
    audit_service.log(db, actor=actor, action="book.archive", entity_type="book", entity_id=book.id, detail={"title": book.title})
    return {"archived": True, "title": book.title}


def save_cover(db: Session, book_id: int, content: bytes, content_type: str, actor) -> Book:
    book = _get_book_or_404(db, book_id)
    ext = ALLOWED_COVER_TYPES.get(content_type)
    if ext is None:
        raise ValidationError("Unsupported image type. Allowed: JPEG, PNG, WebP.")
    if len(content) > MAX_COVER_SIZE_BYTES:
        raise ValidationError("Image is too large. Maximum size is 5 MB.")
    try:
        img = Image.open(__import__("io").BytesIO(content))
        img.verify()
    except (UnidentifiedImageError, Exception):
        raise ValidationError("The uploaded file is not a valid image.")

    filename = f"{uuid.uuid4().hex}{ext}"
    path = media_path("covers", filename)
    with open(path, "wb") as fh:
        fh.write(content)

    if book.cover_image and book.cover_image.startswith(f"{settings.MEDIA_DIR}"):
        _safe_remove(book.cover_image)
    book.cover_image = path
    audit_service.log(db, actor=actor, action="book.cover_upload", entity_type="book", entity_id=book.id)
    return book


# ---------------------------------------------------------------------------
# Terms (authors / categories / publishers)
# ---------------------------------------------------------------------------


def create_term(db: Session, model, data: TermCreate, actor, entity_name: str):
    slug = make_unique_slug(None, model, data.name, db)
    term = model(name=data.name.strip(), slug=slug, **({"description": data.description} if hasattr(model, "description") else {}))
    db.add(term)
    db.flush()
    audit_service.log(db, actor=actor, action=f"{entity_name}.create", entity_type=entity_name, entity_id=term.id, detail={"name": term.name})
    return term


def update_term(db: Session, model, term_id: int, data: TermUpdate, actor, entity_name: str):
    term = db.get(model, term_id)
    if term is None:
        raise NotFoundError(f"{entity_name.capitalize()} not found.")
    if data.name is not None and data.name.strip() != term.name:
        term.name = data.name.strip()
        term.slug = make_unique_slug(None, model, term.name, db)
    if data.description is not None and hasattr(term, "description"):
        term.description = data.description
    audit_service.log(db, actor=actor, action=f"{entity_name}.update", entity_type=entity_name, entity_id=term.id, detail={"name": term.name})
    return term


def delete_term(db: Session, model, term_id: int, actor, entity_name: str) -> None:
    term = db.get(model, term_id)
    if term is None:
        raise NotFoundError(f"{entity_name.capitalize()} not found.")
    if entity_name == "author":
        from app.models import book_authors

        if db.query(book_authors).filter(book_authors.c.author_id == term_id).first() is not None:
            raise BusinessRuleError("This author is linked to books and cannot be deleted.")
    if entity_name == "category":
        from app.models import book_categories

        if db.query(book_categories).filter(book_categories.c.category_id == term_id).first() is not None:
            raise BusinessRuleError("This category is linked to books and cannot be deleted.")
    if entity_name == "publisher" and db.query(Book).filter(Book.publisher_id == term_id).first() is not None:
        raise BusinessRuleError("This publisher is linked to books and cannot be deleted.")
    audit_service.log(db, actor=actor, action=f"{entity_name}.delete", entity_type=entity_name, entity_id=term.id, detail={"name": term.name})
    db.delete(term)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_book_or_404(db: Session, book_id: int) -> Book:
    book = (
        db.query(Book)
        .options(selectinload(Book.authors), selectinload(Book.categories), selectinload(Book.inventory))
        .filter(Book.id == book_id)
        .first()
    )
    if book is None:
        raise NotFoundError("Book not found.")
    return book


def _validate_refs(db: Session, author_ids, category_ids, publisher_id) -> None:
    if author_ids:
        found = db.query(Author).filter(Author.id.in_(author_ids)).count()
        if found != len(set(author_ids)):
            raise ValidationError("One or more authors do not exist.")
    if category_ids:
        found = db.query(Category).filter(Category.id.in_(category_ids)).count()
        if found != len(set(category_ids)):
            raise ValidationError("One or more categories do not exist.")
    if publisher_id and db.get(Publisher, publisher_id) is None:
        raise ValidationError("Publisher does not exist.")


def _safe_remove(path: str) -> None:
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        logger.warning("Could not remove old cover file: %s", path)
