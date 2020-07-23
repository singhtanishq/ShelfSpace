"""FastAPI dependencies for authentication and authorization."""

from typing import Optional

import jwt as pyjwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models import User, UserRole
from app.utils.exceptions import AppError, AuthError, PermissionDeniedError

bearer_scheme = HTTPBearer(auto_error=False)

AuthErrors = (AuthError, PermissionDeniedError, AppError)


def _extract_token(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthError("Not authenticated. Please provide a bearer token.")
    return credentials.credentials


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = _extract_token(credentials)
    try:
        payload = decode_token(token, expected_type="access")
    except pyjwt.ExpiredSignatureError:
        raise AuthError("Your session has expired. Please sign in again.")
    except pyjwt.PyJWTError:
        raise AuthError("Invalid authentication token.")

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if user is None:
        raise AuthError("Account no longer exists.")
    if not user.is_active:
        raise AuthError("This account has been deactivated.")
    request.state.user = user
    return user


def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Like get_current_user but returns None for anonymous visitors."""
    if credentials is None:
        return None
    try:
        return get_current_user(request, credentials, db)
    except AuthErrors:
        return None


def get_current_admin_user(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise PermissionDeniedError("Administrator privileges are required for this operation.")
    return user
