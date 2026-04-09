from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

UserRole = Literal["user", "admin"]


class AuthenticatedUser(BaseModel):
    user_id: str
    username: str
    role: UserRole
    is_active: bool
    password_must_change: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    password: str

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("username is required.")
        if len(normalized) < 3 or len(normalized) > 32:
            raise ValueError("username must be between 3 and 32 characters.")
        if any(character not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for character in normalized):
            raise ValueError("username may only contain lowercase letters, digits, '_' or '-'.")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 6:
            raise ValueError("password must be at least 6 characters.")
        if len(normalized) > 128:
            raise ValueError("password must be 128 characters or fewer.")
        return normalized


class LoginRequest(RegisterRequest):
    pass


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str
    new_password: str

    @field_validator("current_password", "new_password")
    @classmethod
    def normalize_password(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 6:
            raise ValueError("password must be at least 6 characters.")
        if len(normalized) > 128:
            raise ValueError("password must be 128 characters or fewer.")
        return normalized


class AuthUserEnvelope(BaseModel):
    user: AuthenticatedUser


class LoginResponse(AuthUserEnvelope):
    must_change_password: bool


class AuthStatusResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ResetPasswordResponse(BaseModel):
    status: Literal["ok"] = "ok"
    temporary_password: str


class StoredAuthSession(BaseModel):
    auth_session_id: str
    user_id: str
    token_hash: str
    created_at: datetime
    expires_at: datetime
    last_seen_at: datetime


class AuthLoginResult(BaseModel):
    user: AuthenticatedUser
    raw_token: str
    expires_at: datetime


class AuthSessionCookie(BaseModel):
    key: str = "carbonrag_session"
    max_age_seconds: int = Field(default=7 * 24 * 60 * 60)
