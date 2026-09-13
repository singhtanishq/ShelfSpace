"""Authentication endpoints."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.schemas.user import (
    AuthMessage,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenPair,
    UpdateProfileRequest,
    UserPublic,
    VerifyEmailRequest,
)
from app.services import auth_service
from app.utils.exceptions import AuthError
from app.utils.rate_limit import enforce_rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthMessage, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    user, verification_url = auth_service.register(db, data)
    message = "Account created. Check your email to verify your address."
    if not settings.EMAIL_ENABLED:
        message = "Account created. Email delivery is disabled in this environment; use the verification link provided."
    return AuthMessage(message=message, verification_url=verification_url)


@router.post("/verify-email", response_model=AuthMessage)
def verify_email(data: VerifyEmailRequest, db: Session = Depends(get_db)):
    auth_service.verify_email(db, data.token)
    return AuthMessage(message="Your email has been verified. Thank you!")


@router.post("/resend-verification", response_model=AuthMessage)
def resend_verification(data: ResendVerificationRequest, db: Session = Depends(get_db)):
    auth_service.resend_verification(db, data.email)
    return AuthMessage(message="If that address needs verification, a new link has been sent.")


@router.post("/login", response_model=TokenPair)
def login(
    request: Request,
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    enforce_rate_limit(
        request,
        bucket="login",
        limit=settings.LOGIN_RATE_LIMIT,
        window_seconds=settings.LOGIN_RATE_WINDOW_SECONDS,
    )
    user = auth_service.authenticate(db, data.identifier, data.password)
    tokens = auth_service.issue_tokens(db, user)
    return tokens


@router.post("/refresh", response_model=TokenPair)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    return auth_service.refresh_tokens(db, data.refresh_token)


@router.post("/logout", response_model=AuthMessage)
def logout(data: LogoutRequest, db: Session = Depends(get_db)):
    auth_service.logout(db, data.refresh_token)
    return AuthMessage(message="Signed out.")


@router.post("/forgot-password", response_model=AuthMessage)
def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    enforce_rate_limit(request, bucket="forgot-password", limit=5, window_seconds=300)
    auth_service.forgot_password(db, data.email)
    return AuthMessage(message="If an account exists for that email, a reset link has been sent.")


@router.post("/reset-password", response_model=AuthMessage)
def reset_password(
    request: Request,
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    enforce_rate_limit(request, bucket="reset-password", limit=10, window_seconds=300)
    auth_service.reset_password(db, data.token, data.new_password)
    return AuthMessage(message="Your password has been reset. You can now sign in.")


@router.get("/me", response_model=UserPublic)
def me(user=Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserPublic)
def update_me(
    data: UpdateProfileRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return auth_service.update_profile(db, user, data)


@router.put("/me/password", response_model=AuthMessage)
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    auth_service.change_password(db, user, data.current_password, data.new_password)
    return AuthMessage(message="Your password has been updated.")
