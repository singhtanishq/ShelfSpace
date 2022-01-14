"""Catalog schemas: books, authors, categories, publishers, reviews."""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AuthorPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    bio: Optional[str] = None


class CategoryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: Optional[str] = None


class PublisherPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str


class BookCard(BaseModel):
    """Compact book representation for lists/cards."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    cover_image: Optional[str] = None
    price: float
    discount_percent: float
    effective_price: float
    rating_avg: float
    rating_count: int
    is_active: bool
    is_featured: bool
    authors: List[AuthorPublic] = []
    categories: List[CategoryPublic] = []
    available_quantity: int = 0


class BookDetail(BookCard):
    isbn: Optional[str] = None
    description: Optional[str] = None
    language: str
    format: str
    pages: Optional[int] = None
    published_year: Optional[int] = None
    publisher: Optional[PublisherPublic] = None
    created_at: datetime


class BookList(BaseModel):
    items: List[BookCard]
    total: int
    page: int
    page_size: int
    pages: int


class CatalogFacets(BaseModel):
    """Aggregate filter options for the catalog page."""

    price_min: float
    price_max: float
    languages: List[str]
    categories: List[CategoryPublic]
    authors: List[AuthorPublic]


class RelatedBooks(BaseModel):
    related: List[BookCard]
    by_same_author: List[BookCard]


class HomeFeed(BaseModel):
    featured: List[BookCard]
    best_sellers: List[BookCard]
    new_arrivals: List[BookCard]
    categories: List[CategoryPublic]


# ---- Admin ----


class BookBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    isbn: Optional[str] = Field(default=None, max_length=20)
    description: Optional[str] = None
    language: str = Field(default="English", max_length=40)
    format: Literal["paperback", "hardcover"] = "paperback"
    pages: Optional[int] = Field(default=None, ge=1, le=20000)
    published_year: Optional[int] = Field(default=None, ge=1000, le=2100)
    publisher_id: Optional[int] = None
    price: float = Field(gt=0, le=1_000_000)
    discount_percent: float = Field(default=0, ge=0, le=100)
    is_active: bool = True
    is_featured: bool = False
    author_ids: List[int] = []
    category_ids: List[int] = []
    stock_quantity: int = Field(default=0, ge=0, le=1_000_000)
    low_stock_threshold: int = Field(default=5, ge=0, le=10_000)


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    isbn: Optional[str] = Field(default=None, max_length=20)
    description: Optional[str] = None
    language: Optional[str] = Field(default=None, max_length=40)
    format: Optional[Literal["paperback", "hardcover"]] = None
    pages: Optional[int] = Field(default=None, ge=1, le=20000)
    published_year: Optional[int] = Field(default=None, ge=1000, le=2100)
    publisher_id: Optional[int] = None
    price: Optional[float] = Field(default=None, gt=0, le=1_000_000)
    discount_percent: Optional[float] = Field(default=None, ge=0, le=100)
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    author_ids: Optional[List[int]] = None
    category_ids: Optional[List[int]] = None


class AdminBook(BookDetail):
    stock_quantity: int = 0
    reserved_quantity: int = 0
    low_stock_threshold: int = 5
    sales_count: int = 0


class InventoryRow(BaseModel):
    book_id: int
    title: str
    slug: str
    cover_image: Optional[str] = None
    stock_quantity: int
    reserved_quantity: int
    available_quantity: int
    low_stock_threshold: int
    is_low_stock: bool
    is_active: bool
    price: float


class InventoryAdjustRequest(BaseModel):
    change: int
    note: Optional[str] = Field(default=None, max_length=255)


class InventoryTransactionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    change: int
    change_type: str
    balance_after: int
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    note: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime


class TermCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: Optional[str] = Field(default=None, max_length=255)


class TermUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=160)
    description: Optional[str] = Field(default=None, max_length=255)


# ---- Reviews ----


class ReviewPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    user_id: int
    rating: int
    title: Optional[str] = None
    content: str
    is_verified_purchase: bool
    created_at: datetime
    updated_at: datetime
    author_name: str = ""
    is_hidden: bool = False


class ReviewList(BaseModel):
    items: List[ReviewPublic]
    total: int
    page: int
    page_size: int
    pages: int


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    title: Optional[str] = Field(default=None, max_length=150)
    content: str = Field(min_length=3, max_length=4000)


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    title: Optional[str] = Field(default=None, max_length=150)
    content: Optional[str] = Field(default=None, min_length=3, max_length=4000)
