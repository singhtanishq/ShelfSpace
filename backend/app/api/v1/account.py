"""Account area: address book and personal review history."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.user import AddressCreate, AddressPublic, AddressUpdate
from app.services import auth_service, review_service
from app.utils.serializers import review_public

router = APIRouter(prefix="/account", tags=["account"])


# ---------------------------------------------------------------------------
# Addresses
# ---------------------------------------------------------------------------


@router.get("/addresses", response_model=list[AddressPublic])
def list_addresses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return auth_service.list_addresses(db, user)


@router.post("/addresses", response_model=AddressPublic, status_code=201)
def create_address(
    data: AddressCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return auth_service.create_address(db, user, data)


@router.put("/addresses/{address_id}", response_model=AddressPublic)
def update_address(
    address_id: int,
    data: AddressUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return auth_service.update_address(db, user, address_id, data)


@router.delete("/addresses/{address_id}", status_code=204)
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    auth_service.delete_address(db, user, address_id)


# ---------------------------------------------------------------------------
# Reviews written by the signed-in user
# ---------------------------------------------------------------------------


@router.get("/reviews", response_model=list)
def my_reviews(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    reviews = review_service.list_reviews_by_user(db, user)
    return [review_public(r) for r in reviews]
