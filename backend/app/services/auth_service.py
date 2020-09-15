"""Authentication and account management business logic."""

import secrets  # noqa: F401  (reserved for future token schemes)
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import jwt as pyjwt
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    generate_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models import Address, NotificationType, User, UserRefreshToken, UserRole
from app.schemas.user import (
    AddressCreate,
    AddressUpdate,
    RegisterRequest,
    UpdateProfileRequest,
)
from app.services import email_service, notification_service, settings_service
from app.utils.exceptions import AuthError, BusinessRuleError, ConflictError, NotFoundError, ValidationError

logger = get_logger(__name__)

VERIFICATION_TOKEN_HOURS = 48
RESET_TOKEN_HOURS = 1


# ---------------------------------------------------------------------------
# Registration / verification
# ---------------------------------------------------------------------------


def register(db: Session, data: RegisterRequest) -> Tuple[User, Optional[str]]:
    """Create an unverified account. Returns (user, verification_url|None).

    verification_url is only populated when email delivery is disabled
    (development convenience); it is always queued for delivery otherwise.
    """
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise ConflictError("An account with this email already exists.")
    if db.query(User).filter(User.username == data.username).first():
        raise ConflictError("This username is already taken.")

    user = User(
        email=data.email.lower(),
        username=data.username,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        role=UserRole.CUSTOMER,
    )
    db.add(user)
    db.flush()

    raw_token = generate_token()
    user.verification_token = hash_token(raw_token)
    user.verification_token_expires = datetime.now(timezone.utc) + timedelta(hours=VERIFICATION_TOKEN_HOURS)

    settings_service.get_str(db, "support_email")  # ensure settings row context (cheap)
    support_email = settings_service.get_str(db, "support_email")

    email_service.queue_email(
        db,
        to_email=user.email,
        subject=f"Verify your {settings.APP_NAME} account",
        template="verify_email",
        context={
            "user_name": user.full_name,
            "verification_url": _frontend_url(f"/verify-email?token={raw_token}"),
            "support_email": support_email,
        },
        related_type="user",
        related_id=user.id,
    )
    notification_service.notify(
        db,
        user=user,
        type=NotificationType.ACCOUNT,
        title="Welcome to ShelfSpace",
        body="Your account has been created. Verify your email to get the full experience.",
        link="/account",
    )

    verification_url = None
    if not settings.EMAIL_ENABLED:
        verification_url = _frontend_url(f"/verify-email?token={raw_token}")
    return user, verification_url


def verify_email(db: Session, token: str) -> User:
    token_hash = hash_token(token)
    user = db.query(User).filter(User.verification_token == token_hash).first()
    if user is None:
        raise ValidationError("This verification link is invalid or has already been used.")
    expires = _as_utc(user.verification_token_expires)
    if expires and expires < datetime.now(timezone.utc):
        raise ValidationError("This verification link has expired. Please request a new one.")
    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    return user


def resend_verification(db: Session, email: str) -> None:
    user = db.query(User).filter(User.email == email.lower()).first()
    if user is None or user.is_verified or not user.is_active:
        return  # do not reveal account existence
    raw_token = generate_token()
    user.verification_token = hash_token(raw_token)
    user.verification_token_expires = datetime.now(timezone.utc) + timedelta(hours=VERIFICATION_TOKEN_HOURS)
    email_service.queue_email(
        db,
        to_email=user.email,
        subject=f"Verify your {settings.APP_NAME} account",
        template="verify_email",
        context={
            "user_name": user.full_name,
            "verification_url": _frontend_url(f"/verify-email?token={raw_token}"),
            "support_email": settings_service.get_str(db, "support_email"),
        },
        related_type="user",
        related_id=user.id,
    )


# ---------------------------------------------------------------------------
# Login / tokens
# ---------------------------------------------------------------------------


def authenticate(db: Session, identifier: str, password: str) -> User:
    user = (
        db.query(User)
        .filter(or_(User.email == identifier.lower(), User.username == identifier.lower()))
        .first()
    )
    if user is None or not verify_password(password, user.hashed_password):
        # Same message for unknown user and wrong password (no account enumeration).
        raise AuthError("Incorrect email/username or password.")
    if not user.is_active:
        raise AuthError("This account has been deactivated. Contact support for help.")
    return user


def issue_tokens(db: Session, user: User, refresh_token_plain: Optional[str] = None) -> dict:
    """Create an access JWT and a (new) revocable refresh token."""
    if refresh_token_plain is None:
        refresh_token_plain = generate_token()
        db.add(
            UserRefreshToken(
                user_id=user.id,
                token_hash=hash_token(refresh_token_plain),
                expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            )
        )
    return {
        "access_token": create_access_token(str(user.id), {"role": user.role.value}),
        "refresh_token": refresh_token_plain,
        "token_type": "bearer",
        "user": user,
    }


def refresh_tokens(db: Session, refresh_token_plain: str) -> dict:
    token_hash = hash_token(refresh_token_plain)
    row = db.query(UserRefreshToken).filter(UserRefreshToken.token_hash == token_hash).first()
    if row is None or row.revoked_at is not None:
        raise AuthError("Invalid refresh token. Please sign in again.")
    expires = _as_utc(row.expires_at)
    if expires and expires < datetime.now(timezone.utc):
        raise AuthError("Your session has expired. Please sign in again.")
    user = db.get(User, row.user_id)
    if user is None or not user.is_active:
        raise AuthError("Account unavailable. Please sign in again.")
    # Rotate: revoke the used token and issue a fresh one.
    row.revoked_at = datetime.now(timezone.utc)
    return issue_tokens(db, user)


def logout(db: Session, refresh_token_plain: str) -> None:
    token_hash = hash_token(refresh_token_plain)
    row = db.query(UserRefreshToken).filter(UserRefreshToken.token_hash == token_hash).first()
    if row is not None and row.revoked_at is None:
        row.revoked_at = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Password reset / change
# ---------------------------------------------------------------------------


def forgot_password(db: Session, email: str) -> None:
    user = db.query(User).filter(User.email == email.lower()).first()
    if user is None or not user.is_active:
        return  # do not reveal account existence
    raw_token = generate_token()
    user.reset_password_token = hash_token(raw_token)
    user.reset_password_token_expires = datetime.now(timezone.utc) + timedelta(hours=RESET_TOKEN_HOURS)
    email_service.queue_email(
        db,
        to_email=user.email,
        subject=f"Reset your {settings.APP_NAME} password",
        template="password_reset",
        context={
            "user_name": user.full_name,
            "reset_url": _frontend_url(f"/reset-password?token={raw_token}"),
            "support_email": settings_service.get_str(db, "support_email"),
        },
        related_type="user",
        related_id=user.id,
    )


def reset_password(db: Session, token: str, new_password: str) -> None:
    token_hash = hash_token(token)
    user = db.query(User).filter(User.reset_password_token == token_hash).first()
    if user is None:
        raise ValidationError("This password reset link is invalid or has already been used.")
    expires = _as_utc(user.reset_password_token_expires)
    if expires and expires < datetime.now(timezone.utc):
        raise ValidationError("This password reset link has expired. Please request a new one.")
    user.hashed_password = hash_password(new_password)
    user.reset_password_token = None
    user.reset_password_token_expires = None
    # Revoke every active session for safety.
    now = datetime.now(timezone.utc)
    for row in db.query(UserRefreshToken).filter(UserRefreshToken.user_id == user.id).all():
        if row.revoked_at is None:
            row.revoked_at = now


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.hashed_password):
        raise AuthError("Your current password is incorrect.")
    if current_password == new_password:
        raise BusinessRuleError("The new password must be different from the current one.")
    user.hashed_password = hash_password(new_password)


# ---------------------------------------------------------------------------
# Profile / addresses
# ---------------------------------------------------------------------------


def update_profile(db: Session, user: User, data: UpdateProfileRequest) -> User:
    if data.full_name is not None:
        user.full_name = data.full_name.strip()
    if data.phone is not None:
        user.phone = data.phone
    return user


def list_addresses(db: Session, user: User) -> list:
    return db.query(Address).filter(Address.user_id == user.id).order_by(Address.is_default.desc(), Address.id).all()


def create_address(db: Session, user: User, data: AddressCreate) -> Address:
    if data.is_default:
        db.query(Address).filter(Address.user_id == user.id).update({"is_default": False})
    elif not db.query(Address).filter(Address.user_id == user.id).first():
        data.is_default = True  # first address is always default
    address = Address(user_id=user.id, **data.model_dump())
    db.add(address)
    db.flush()
    return address


def update_address(db: Session, user: User, address_id: int, data: AddressUpdate) -> Address:
    address = _get_own_address(db, user, address_id)
    if data.is_default:
        db.query(Address).filter(Address.user_id == user.id).update({"is_default": False})
    for field, value in data.model_dump().items():
        setattr(address, field, value)
    return address


def delete_address(db: Session, user: User, address_id: int) -> None:
    address = _get_own_address(db, user, address_id)
    was_default = address.is_default
    db.delete(address)
    db.flush()
    if was_default:
        remaining = db.query(Address).filter(Address.user_id == user.id).order_by(Address.id).first()
        if remaining:
            remaining.is_default = True


def _get_own_address(db: Session, user: User, address_id: int) -> Address:
    address = db.get(Address, address_id)
    if address is None or address.user_id != user.id:
        raise NotFoundError("Address not found.")
    return address


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _frontend_url(path: str) -> str:
    return f"{settings.FRONTEND_URL}{path}"


def _as_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
