"""Catalog entities: authors, publishers, categories and books."""

import enum
import re
import unicodedata
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def slugify(value: str) -> str:
    """Deterministic URL-safe slug used for books, authors, categories, publishers."""
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or "item"


class BookFormat(str, enum.Enum):
    PAPERBACK = "paperback"
    HARDCOVER = "hardcover"


book_authors = Table(
    "book_authors",
    Base.metadata,
    Column("book_id", ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    Column("author_id", ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True),
)

book_categories = Table(
    "book_categories",
    Base.metadata,
    Column("book_id", ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    bio: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    books: Mapped[List["Book"]] = relationship(
        secondary="book_authors", back_populates="authors"
    )


class Publisher(Base):
    __tablename__ = "publishers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    books: Mapped[List["Book"]] = relationship(back_populates="publisher")


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        Index("ix_books_title", "title"),
        Index("ix_books_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(280), unique=True, index=True)
    isbn: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(40), default="English")
    format: Mapped[BookFormat] = mapped_column(Enum(BookFormat), default=BookFormat.PAPERBACK)
    pages: Mapped[Optional[int]] = mapped_column()
    published_year: Mapped[Optional[int]] = mapped_column()
    publisher_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("publishers.id", ondelete="SET NULL")
    )
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    discount_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    cover_image: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)

    # Cached review aggregates maintained by the review service.
    rating_avg: Mapped[float] = mapped_column(Numeric(3, 2), default=0)
    rating_count: Mapped[int] = mapped_column(default=0)
    sales_count: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    publisher: Mapped[Optional["Publisher"]] = relationship(back_populates="books")
    authors: Mapped[List["Author"]] = relationship(
        secondary="book_authors", back_populates="books", lazy="selectin"
    )
    categories: Mapped[List["Category"]] = relationship(
        secondary="book_categories", back_populates="books", lazy="selectin"
    )
    inventory: Mapped["Inventory"] = relationship(  # noqa: F821
        back_populates="book", uselist=False, cascade="all, delete-orphan"
    )
    reviews: Mapped[List["Review"]] = relationship(back_populates="book")  # noqa: F821

    @property
    def effective_price(self) -> float:
        """Price after discount, rounded to 2 decimals."""
        price = float(self.price)
        if self.discount_percent:
            price = price * (1 - float(self.discount_percent) / 100)
        return round(price, 2)

    def author_names(self) -> str:
        return ", ".join(a.name for a in self.authors) if self.authors else "Unknown"


def make_unique_slug(Base_, model, value: str, session) -> str:
    """Return a slug unique among rows of `model`, appending -2, -3, ... when needed."""
    base = slugify(value)
    candidate = base
    index = 2
    while session.query(model).filter(model.slug == candidate).first() is not None:
        candidate = f"{base}-{index}"
        index += 1
    return candidate
