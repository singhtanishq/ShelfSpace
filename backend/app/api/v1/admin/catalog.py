"""Admin: book management, cover uploads, inventory and taxonomy management."""

from typing import List

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_admin_user
from app.core.database import get_db
from app.models import Author, Book, Category, Inventory, Publisher, User
from app.schemas.catalog import (
    AdminBook,
    AuthorPublic,
    BookCreate,
    BookUpdate,
    CategoryPublic,
    InventoryAdjustRequest,
    InventoryRow,
    InventoryTransactionPublic,
    PublisherPublic,
    TermCreate,
    TermUpdate,
)
from app.services import catalog_service, inventory_service
from app.utils.exceptions import ValidationError
from app.utils.pagination import PaginationParams
from app.utils.serializers import book_detail

router = APIRouter(tags=["admin-catalog"])


@router.get("/admin/books", response_model=List[AdminBook])
def admin_list_books(
    q: str = Query(default=None, max_length=200),
    include_inactive: bool = Query(default=True),
    category: str = Query(default=None),
    low_stock: bool = Query(default=False),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    books, _total = catalog_service.query_books(
        db,
        q=q,
        category_slug=category,
        include_inactive=include_inactive,
        sort="title",
        page=pagination.page,
        page_size=pagination.page_size,
    )
    if low_stock:
        books = [b for b in books if b.inventory and b.inventory.is_low_stock]
    return [book_detail(b) for b in books]


@router.get("/admin/books/{book_id}", response_model=AdminBook)
def admin_get_book(
    book_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    return book_detail(catalog_service.get_book_by_id(db, book_id))


@router.post("/admin/books", response_model=AdminBook, status_code=201)
def admin_create_book(
    data: BookCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    book = catalog_service.create_book(db, data, actor=admin)
    return book_detail(book)


@router.put("/admin/books/{book_id}", response_model=AdminBook)
def admin_update_book(
    book_id: int,
    data: BookUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    book = catalog_service.update_book(db, book_id, data, actor=admin)
    return book_detail(book)


@router.delete("/admin/books/{book_id}")
def admin_delete_book(
    book_id: int,
    hard: bool = Query(default=False),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    return catalog_service.delete_book(db, book_id, actor=admin, hard=hard)


@router.post("/admin/books/{book_id}/cover", response_model=AdminBook)
async def admin_upload_cover(
    book_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    content = await file.read()
    book = catalog_service.save_cover(db, book_id, content, file.content_type or "", actor=admin)
    return book_detail(book)


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------


@router.get("/admin/inventory", response_model=List[InventoryRow])
def admin_inventory(
    filter: str = Query(default="all", pattern="^(all|low|out)$"),
    q: str = Query(default=None, max_length=200),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    query = (
        db.query(Inventory)
        .join(Book, Inventory.book_id == Book.id)
        .options(selectinload(Inventory.book).selectinload(Book.authors))
        .order_by(Inventory.stock_quantity.asc())
    )
    if q:
        query = query.filter(Book.title.ilike(f"%{q}%"))
    if filter == "low":
        query = query.filter(
            Inventory.stock_quantity > 0,
            Inventory.stock_quantity <= Inventory.low_stock_threshold,
        )
    elif filter == "out":
        query = query.filter(Inventory.stock_quantity <= 0)
    rows = query.offset(pagination.offset()).limit(pagination.page_size).all()
    return [_inventory_row(inv) for inv in rows]


@router.post("/admin/inventory/{book_id}/adjust", response_model=InventoryRow)
def admin_adjust_inventory(
    book_id: int,
    data: InventoryAdjustRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    from app.models import InventoryChangeType

    if data.change == 0:
        raise ValidationError("Adjustment must be a non-zero quantity.")
    change_type = InventoryChangeType.RESTOCK if data.change > 0 else InventoryChangeType.ADJUSTMENT
    inventory_service.adjust_stock(
        db,
        book_id=book_id,
        change=data.change,
        change_type=change_type,
        reference_type="manual",
        note=data.note,
        created_by=admin.id,
    )
    return _inventory_row(inventory_service.get_inventory(db, book_id))


@router.get("/admin/inventory/{book_id}/transactions", response_model=List[InventoryTransactionPublic])
def admin_inventory_transactions(
    book_id: int,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    from app.models import InventoryTransaction

    rows = (
        db.query(InventoryTransaction)
        .filter(InventoryTransaction.book_id == book_id)
        .order_by(InventoryTransaction.created_at.desc(), InventoryTransaction.id.desc())
        .offset(pagination.offset())
        .limit(pagination.page_size)
        .all()
    )
    return rows


# ---------------------------------------------------------------------------
# Taxonomy: categories / authors / publishers
# ---------------------------------------------------------------------------


@router.get("/admin/categories", response_model=List[CategoryPublic])
def admin_categories(db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    return db.query(Category).order_by(Category.name).all()


@router.get("/admin/authors", response_model=List[AuthorPublic])
def admin_authors(db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    return db.query(Author).order_by(Author.name).all()


@router.get("/admin/publishers", response_model=List[PublisherPublic])
def admin_publishers(db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)):
    return db.query(Publisher).order_by(Publisher.name).all()


@router.post("/admin/categories", response_model=CategoryPublic, status_code=201)
def admin_create_category(
    data: TermCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)
):
    return catalog_service.create_term(db, Category, data, actor=admin, entity_name="category")


@router.post("/admin/authors", response_model=AuthorPublic, status_code=201)
def admin_create_author(
    data: TermCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)
):
    return catalog_service.create_term(db, Author, data, actor=admin, entity_name="author")


@router.post("/admin/publishers", response_model=PublisherPublic, status_code=201)
def admin_create_publisher(
    data: TermCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)
):
    return catalog_service.create_term(db, Publisher, data, actor=admin, entity_name="publisher")


@router.put("/admin/categories/{term_id}", response_model=CategoryPublic)
def admin_update_category(
    term_id: int, data: TermUpdate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)
):
    return catalog_service.update_term(db, Category, term_id, data, actor=admin, entity_name="category")


@router.put("/admin/authors/{term_id}", response_model=AuthorPublic)
def admin_update_author(
    term_id: int, data: TermUpdate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)
):
    return catalog_service.update_term(db, Author, term_id, data, actor=admin, entity_name="author")


@router.put("/admin/publishers/{term_id}", response_model=PublisherPublic)
def admin_update_publisher(
    term_id: int, data: TermUpdate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)
):
    return catalog_service.update_term(db, Publisher, term_id, data, actor=admin, entity_name="publisher")


@router.delete("/admin/categories/{term_id}", status_code=204)
def admin_delete_category(
    term_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)
):
    catalog_service.delete_term(db, Category, term_id, actor=admin, entity_name="category")


@router.delete("/admin/authors/{term_id}", status_code=204)
def admin_delete_author(
    term_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)
):
    catalog_service.delete_term(db, Author, term_id, actor=admin, entity_name="author")


@router.delete("/admin/publishers/{term_id}", status_code=204)
def admin_delete_publisher(
    term_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin_user)
):
    catalog_service.delete_term(db, Publisher, term_id, actor=admin, entity_name="publisher")


def _inventory_row(inv: Inventory) -> dict:
    book = inv.book
    return {
        "book_id": book.id,
        "title": book.title,
        "slug": book.slug,
        "cover_image": book.cover_image,
        "stock_quantity": inv.stock_quantity,
        "reserved_quantity": inv.reserved_quantity,
        "available_quantity": inv.available_quantity,
        "low_stock_threshold": inv.low_stock_threshold,
        "is_low_stock": inv.is_low_stock,
        "is_active": book.is_active,
        "price": float(book.price),
    }
