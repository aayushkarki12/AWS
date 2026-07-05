"""Pydantic schemas for authentication endpoints."""
import re
import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.config import settings

_PASSWORD_UPPER = re.compile(r"[A-Z]")
_PASSWORD_LOWER = re.compile(r"[a-z]")
_PASSWORD_DIGIT = re.compile(r"\d")
_PASSWORD_SPECIAL = re.compile(r"[^A-Za-z0-9]")


def _validate_password_strength(password: str) -> str:
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters")
    if not _PASSWORD_UPPER.search(password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not _PASSWORD_LOWER.search(password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not _PASSWORD_DIGIT.search(password):
        raise ValueError("Password must contain at least one digit")
    if not _PASSWORD_SPECIAL.search(password):
        raise ValueError("Password must contain at least one special character")
    return password


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class UserPublic(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: str
    is_active: bool
    is_email_verified: bool

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublic


class SessionPublic(BaseModel):
    id: uuid.UUID
    device_label: str | None
    ip_address: str | None
    user_agent: str | None
    created_at: str
    expires_at: str
    is_current: bool = False
