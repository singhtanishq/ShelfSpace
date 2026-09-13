"""Customer order endpoints: checkout, tracking, cancellation, invoices, returns."""

from typing import List

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.order import (
    CancelOrderRequest,
    CheckoutRequest,
    OrderList,
    OrderPublic,
    ReturnCreate,
    ReturnRequestPublic,
)
from app.services import invoice_service, order_service, return_service
from app.utils.pagination import PaginationParams
from app.utils.serializers import order_public, return_public

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/checkout", response_model=OrderPublic, status_code=201)
def checkout(
    data: CheckoutRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = order_service.checkout(db, user, data)
    return order_public(order)


@router.get("", response_model=OrderList)
def my_orders(
    status: str = Query(default=None),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    orders, total = order_service.list_orders(
        db, user=user, status=status, page=pagination.page, page_size=pagination.page_size
    )
    return OrderList(
        items=[order_public(o) for o in orders],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=(total + pagination.page_size - 1) // pagination.page_size,
    )


@router.get("/returns", response_model=List[ReturnRequestPublic])
def my_returns(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    requests = return_service.list_requests(db, user=user)
    return [return_public(r) for r in requests]


@router.get("/{order_number}", response_model=OrderPublic)
def order_detail(
    order_number: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = order_service.get_order(db, order_number, user=user)
    return order_public(order)


@router.post("/{order_number}/cancel", response_model=OrderPublic)
def cancel_order(
    order_number: str,
    data: CancelOrderRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = order_service.get_order(db, order_number, user=user)
    order_service.cancel_order(db, order, actor=user, note=data.note)
    return order_public(order)


@router.get("/{order_number}/invoice")
def download_invoice(
    order_number: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = order_service.get_order(db, order_number, user=user)
    path = invoice_service.generate_invoice(db, order, user_name=user.full_name, user_email=user.email)
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"invoice-{order.order_number}.pdf",
    )


@router.post("/{order_number}/returns", response_model=ReturnRequestPublic, status_code=201)
def create_return(
    order_number: str,
    data: ReturnCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    request = return_service.create_request(db, user, order_number, data)
    return return_public(request, order_number=order_number)
