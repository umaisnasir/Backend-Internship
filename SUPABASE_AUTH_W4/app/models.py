from __future__ import annotations

from pydantic import BaseModel, EmailStr, field_validator


class AuthCredentials(BaseModel):
    """
    Request body shared by signup and login.
    """

    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Password must not be blank")
        return value


class PublicUser(BaseModel):
    """
    Safe user fields that may be returned by this API.
    """

    id: str
    email: EmailStr | None = None
    created_at: str | None = None


class SignupResponse(BaseModel):
    message: str
    user: PublicUser


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PublicInfoResponse(BaseModel):
    message: str


class DashboardResponse(BaseModel):
    message: str
    user_id: str | None = None