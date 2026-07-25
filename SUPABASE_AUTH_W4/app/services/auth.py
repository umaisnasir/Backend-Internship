from __future__ import annotations

from typing import Any

from supabase_auth.errors import AuthError

from ..exceptions import ApiError
from ..models import (
    AuthCredentials,
    PublicUser,
    SignupResponse,
    TokenResponse,
)
from ..supabase_client import create_supabase_client


def _error_code(exc: AuthError) -> str:
    return str(getattr(exc, "code", "") or "")


def _error_status(exc: AuthError) -> int:
    raw_status = getattr(exc, "status", 0) or 0

    try:
        return int(raw_status)
    except (TypeError, ValueError):
        return 0


def serialize_user(user: Any) -> PublicUser:
    """
    Convert the Supabase user object into the API's safe public model.
    """

    created_at = getattr(user, "created_at", None)

    if created_at is None:
        created_at_text = None
    elif hasattr(created_at, "isoformat"):
        created_at_text = created_at.isoformat()
    else:
        created_at_text = str(created_at)

    return PublicUser(
        id=str(user.id),
        email=getattr(user, "email", None),
        created_at=created_at_text,
    )


class AuthService:
    """
    Application service responsible for Supabase authentication calls.
    """

    def signup(self, credentials: AuthCredentials) -> SignupResponse:
        client = create_supabase_client()

        try:
            response = client.auth.sign_up(
                {
                    "email": str(credentials.email),
                    "password": credentials.password,
                }
            )
        except AuthError as exc:
            code = _error_code(exc)
            status_code = _error_status(exc)

            if code in {"user_already_exists", "email_exists"}:
                raise ApiError(
                    status_code=409,
                    message="User already registered",
                ) from exc

            if code == "weak_password":
                raise ApiError(
                    status_code=400,
                    message="Password does not meet the required security policy",
                ) from exc

            if code in {
                "email_address_invalid",
                "validation_failed",
            }:
                raise ApiError(
                    status_code=400,
                    message="Invalid email or password",
                ) from exc

            if code in {
                "over_request_rate_limit",
                "over_email_send_rate_limit",
            } or status_code == 429:
                raise ApiError(
                    status_code=429,
                    message="Too many authentication requests. Try again later",
                ) from exc

            if status_code >= 500:
                raise ApiError(
                    status_code=502,
                    message="Authentication provider is unavailable",
                ) from exc

            raise ApiError(
                status_code=400,
                message="Unable to create account",
            ) from exc

        if response.user is None:
            raise ApiError(
                status_code=502,
                message="Supabase did not return the created user",
            )

        return SignupResponse(
            message="User created successfully",
            user=serialize_user(response.user),
        )

    def login(self, credentials: AuthCredentials) -> TokenResponse:
        client = create_supabase_client()

        try:
            response = client.auth.sign_in_with_password(
                {
                    "email": str(credentials.email),
                    "password": credentials.password,
                }
            )
        except AuthError as exc:
            code = _error_code(exc)
            status_code = _error_status(exc)

            if code in {
                "over_request_rate_limit",
                "over_email_send_rate_limit",
            } or status_code == 429:
                raise ApiError(
                    status_code=429,
                    message="Too many authentication requests. Try again later",
                ) from exc

            if code == "email_not_confirmed":
                raise ApiError(
                    status_code=401,
                    message="Email address is not confirmed",
                    headers={"WWW-Authenticate": "Bearer"},
                ) from exc

            if status_code >= 500:
                raise ApiError(
                    status_code=502,
                    message="Authentication provider is unavailable",
                ) from exc

            # Do not reveal whether the account exists.
            raise ApiError(
                status_code=401,
                message="Invalid login credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        session = response.session

        if (
            session is None
            or not session.access_token
            or not session.refresh_token
        ):
            raise ApiError(
                status_code=502,
                message="Supabase did not return a complete session",
            )

        return TokenResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            token_type="bearer",
        )


auth_service = AuthService()