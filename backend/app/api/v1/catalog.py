"""Public catalog endpoints: books, home feed, facets, terms, reviews."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_user
from app.core.database import get_db
from app.models import Author, Book, Category, Publisher, User
from app.schemas.catalog import (
    AuthorPublic,
    BookDetail,
    BookList,
    CatalogFacets,
    CategoryPublic,
    HomeFeed,
    PublisherPublic,
    RelatedBooks,
    ReviewCreate,
    ReviewList,
    ReviewPublic,
    ReviewUpdate,
)
from app.services import catalog_service, review_service
from app.utils.pagination import PaginationParams, Page
from app.utils.serializers import book_card, book_detail, review_public

router = APIRouter(tags=["catalog"])


@router.get("/home", response_model=HomeFeed, response_model_exclude_none=True)
def home(db: Session = Depends(get_db)):
    feed = catalog_service.get_home_feed(db)
    return {
        "featured": [book_card(b) for b in feed["featured"]],
        "best_sellers": [book_card(b) for b in feed["best_sellers"]],
        "new_arrivals": [book_card(b) for b in feed["new_arrivals"]],
        "categories": [c for c in feed["categories"]],
    }


@router.get("/books", response_model=BookList)
def list_books(
    q: str = Query(default=None, max_length=200, description="Search title, author, ISBN, publisher, description"),
    category: str = Query(default=None, description="Category slug"),
    author: str = Query(default=None, description="Author slug"),
    language: str = Query(default=None),
    min_price: float = Query(default=None, ge=0),
    max_price: float = Query(default=None, ge=0),
    min_rating: float = Query(default=None, ge=0, le=5),
    in_stock: bool = Query(default=False),
    sort: str = Query(default="popularity", pattern="^(popularity|newest|price_asc|price_desc|rating|title)$"),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
):
    books, total = catalog_service.query_books(
        db,
        q=q,
        category_slug=category,
        author_slug=author,
        language=language,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        in_stock=in_stock,
        sort=sort,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    return BookList(
        items=[book_card(b) for b in books],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=(total + pagination.page_size - 1) // pagination.page_size,
    )


@router.get("/books/facets", response_model=CatalogFacets, response_model_exclude_none=True)
def facets(db: Session = Depends(get_db)):
    data = catalog_service.get_facets(db)
    return {
        "price_min": data["price_min"],
        "price_max": data["price_max"],
        "languages": data["languages"],
        "categories": data["categories"],
        "authors": data["authors"],
    }


@router.get("/books/{slug}", response_model=BookDetail, response_model_exclude_none=True)
def book_detail_route(slug: str, db: Session = Depends(get_db)):
    book = catalog_service.get_book_by_slug(db, slug)
    data = book_detail(book)
    data.pop("stock_quantity", None)
    data.pop("reserved_quantity", None)
    data.pop("low_stock_threshold", None)
    data.pop("sales_count", None)
    return data


@router.get("/books/{slug}/related", response_model=RelatedBooks, response_model_exclude_none=True)
def related_books(slug: str, db: Session = Depends(get_db)):
    book = catalog_service.get_book_by_slug(db, slug)
    related, by_same_author = catalog_service.get_related_books(db, book)
    return {"related": [book_card(b) for b in related], "by_same_author": [book_card(b) for b in by_same_author]}


@router.get("/books/{slug}/reviews", response_model=ReviewList)
def book_reviews(
    slug: str,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
):
    book = catalog_service.get_book_by_slug(db, slug)
    reviews, total = review_service.list_reviews_for_book(
        db, book, page=pagination.page, page_size=pagination.page_size
    )
    return ReviewList(
        items=[review_public(r) for r in reviews],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=(total + pagination.page_size - 1) // pagination.page_size,
    )


@router.post("/books/{slug}/reviews", response_model=ReviewPublic, status_code=201)
def create_review(
    slug: str,
    data: ReviewCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    book = catalog_service.get_book_by_slug(db, slug)
    review = review_service.create_review(db, user, book, data)
    return review_public(review)


@router.put("/reviews/{review_id}", response_model=ReviewPublic)
def update_review(
    review_id: int,
    data: ReviewUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    review = review_service.update_review(db, user, review_id, data)
    return review_public(review)


@router.delete("/reviews/{review_id}", status_code=204)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    review_service.delete_review(db, user, review_id)


@router.get("/categories", response_model=list[CategoryPublic])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name).all()


@router.get("/authors", response_model=list[AuthorPublic])
def list_authors(db: Session = Depends(get_db)):
    return db.query(Author).order_by(Author.name).all()


@router.get("/publishers", response_model=list[PublisherPublic])
def list_publishers(db: Session = Depends(get_db)):
    return db.query(Publisher).order_by(Publisher.name).all()
