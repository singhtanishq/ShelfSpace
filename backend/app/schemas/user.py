"""Auth and user account schemas."""

import re
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.]{3,30}$")
PHONE_RE = re.compile(r"^\+?[0-9\s-]{7,20}$")


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    username: str
    full_name: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not USERNAME_RE.match(v):
            raise ValueError(
                "Username must be 3-30 characters and contain only letters, digits, dots or underscores."
            )
        return v.lower()

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=255, description="Email or username")
    password: str = Field(min_length=1, max_length=128)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserPublic


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    phone: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if not PHONE_RE.match(v):
            raise ValueError("Invalid phone number.")
        return v


class AuthMessage(BaseModel):
    message: str
    verification_url: Optional[str] = None  # populated in development only


class AddressBase(BaseModel):
    label: str = Field(default="Home", max_length=50)
    full_name: str = Field(min_length=2, max_length=120)
    phone: str
    line1: str = Field(min_length=4, max_length=255)
    line2: Optional[str] = Field(default=None, max_length=255)
    city: str = Field(min_length=2, max_length=80)
    state: str = Field(min_length=2, max_length=80)
    postal_code: str = Field(min_length=4, max_length=20)
    country: str = Field(default="India", max_length=80)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not PHONE_RE.match(v):
            raise ValueError("Invalid phone number.")
        return v


class AddressCreate(AddressBase):
    is_default: bool = False


class AddressUpdate(AddressBase):
    is_default: bool = False


class AddressPublic(AddressBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_default: bool
    created_at: datetime


class AdminUserUpdate(BaseModel):
    role: Optional[Literal["customer", "admin"]] = None
    is_active: Optional[bool] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None


class AdminUserPublic(UserPublic):
    order_count: int = 0
    total_spent: float = 0


class AddressList(BaseModel):
    items: List[AddressPublic]
