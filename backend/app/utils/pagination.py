"""Reusable pagination primitives."""

from math import ceil
from typing import Generic, List, TypeVar

from fastapi import Query
from pydantic import BaseModel

from app.core.config import settings

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(default=12, ge=1, le=60, description="Items per page"),
    ):
        self.page = page
        self.page_size = min(page_size, settings.MAX_PAGE_SIZE)

    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def paginate(items: List[T], total: int, params: PaginationParams) -> Page:
    return Page(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
        pages=ceil(total / params.page_size) if params.page_size else 1,
    )
