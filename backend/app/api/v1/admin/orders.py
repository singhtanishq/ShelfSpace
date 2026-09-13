"""Admin: order management and return/replacement decisions."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user
from app.core.database import get_db
from app.models import OrderStatus, User
from app.schemas.order import OrderList, OrderPublic, ReturnDecision, ReturnRequestPublic, StatusUpdateRequest
from app.services import audit_service, order_service, return_service
from app.utils.pagination import PaginationParams
from app.utils.serializers import order_public, return_public

router = APIRouter(prefix="/admin", tags=["admin-orders"])


@router.get("/admin/orders", response_model=OrderList)
def admin_list_orders(
    status: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None, max_length=60, description="Order number search"),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    orders, total = order_service.list_orders(
        db, status=status, q=q, page=pagination.page, page_size=pagination.page_size
    )
    return OrderList(
        items=[order_public(o) for o in orders],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=(total + pagination.page_size - 1) // pagination.page_size,
    )


@router.get("/admin/orders/{order_number}", response_model=OrderPublic)
def admin_get_order(
    order_number: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    order = order_service.get_order(db, order_number, require_admin=True)
    return order_public(order)


@router.put("/admin/orders/{order_number}/status", response_model=OrderPublic)
def admin_update_status(
    order_number: str,
    data: StatusUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    order = order_service.get_order(db, order_number, require_admin=True)
    previous = order.status
    order_service.transition_status(
        db, order, OrderStatus(data.status), actor=admin, note=data.note, is_admin=True
    )
    audit_service.log(
        db,
        actor=admin,
        action="order.status_change",
        entity_type="order",
        entity_id=order.order_number,
        detail={"from": previous.value, "to": data.status, "note": data.note},
    )
    return order_public(order)


@router.get("/admin/returns", response_model=List[ReturnRequestPublic])
def admin_list_returns(
    status: Optional[str] = Query(default=None),
    type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    requests = return_service.list_requests(db, status=status, type=type)
    return [return_public(r) for r in requests]


@router.put("/admin/returns/{request_id}/{decision}", response_model=ReturnRequestPublic)
def admin_decide_return(
    request_id: int,
    decision: str,
    data: ReturnDecision,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    if decision not in ("approve", "reject", "complete"):
        from app.utils.exceptions import ValidationError

        raise ValidationError("Decision must be approve, reject or complete.")
    request = return_service.decide(db, admin, request_id, decision, data)
    audit_service.log(
        db,
        actor=admin,
        action=f"return.{decision}",
        entity_type="return",
        entity_id=request.return_number,
        detail={"note": data.note, "type": request.type.value},
    )
    return return_public(request)
