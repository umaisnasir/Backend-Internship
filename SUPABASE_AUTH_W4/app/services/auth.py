from __future__ import annotations

from typing import Any

import httpx
from supabase_auth.errors import AuthError

from ..config import get_settings
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
                raise ApiError(409, "User already registered") from exc

            if code == "weak_password":
                raise ApiError(
                    400,
                    "Password does not meet the required security policy",
                ) from exc

            if code in {
                "email_address_invalid",
                "validation_failed",
            }:
                raise ApiError(
                    400,
                    "Invalid email or password",
                ) from exc

            if code in {
                "over_request_rate_limit",
                "over_email_send_rate_limit",
            } or status_code == 429:
                raise ApiError(
                    429,
                    "Too many authentication requests. Try again later",
                ) from exc

            if status_code >= 500:
                raise ApiError(
                    502,
                    "Authentication provider is unavailable",
                ) from exc

            raise ApiError(
                400,
                "Unable to create account",
            ) from exc

        if response.user is None:
            raise ApiError(
                502,
                "Supabase did not return the created user",
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
                    429,
                    "Too many authentication requests. Try again later",
                ) from exc

            if code == "email_not_confirmed":
                raise ApiError(
                    401,
                    "Email address is not confirmed",
                    headers={"WWW-Authenticate": "Bearer"},
                ) from exc

            if status_code >= 500:
                raise ApiError(
                    502,
                    "Authentication provider is unavailable",
                ) from exc

            raise ApiError(
                401,
                "Invalid login credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        session = response.session

        if (
            session is None
            or not session.access_token
            or not session.refresh_token
        ):
            raise ApiError(
                502,
                "Supabase did not return a complete session",
            )

        return TokenResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            token_type="bearer",
        )

    def verify_access_token(self, access_token: str) -> Any:
        client = create_supabase_client()

        try:
            response = client.auth.get_user(access_token)
        except AuthError as exc:
            code = _error_code(exc)
            status_code = _error_status(exc)

            if code == "over_request_rate_limit" or status_code == 429:
                raise ApiError(
                    429,
                    "Too many authentication requests. Try again later",
                ) from exc

            if status_code >= 500:
                raise ApiError(
                    503,
                    "Authentication verification is unavailable",
                ) from exc

            raise ApiError(
                401,
                "Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        if response.user is None:
            raise ApiError(
                401,
                "Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return response.user

    def logout(self, access_token: str) -> None:
        """
        Revoke the current Supabase Auth session.

        The API receives only an access token. Therefore, it calls the
        official Supabase Auth logout endpoint directly instead of
        reconstructing an SDK session that would require a refresh token.
        """

        settings = get_settings()
        logout_url = (
            f"{settings.supabase_url.rstrip('/')}/auth/v1/logout"
        )

        try:
            response = httpx.post(
                logout_url,
                params={"scope": "local"},
                headers={
                    "apikey": settings.supabase_key,
                    "Authorization": f"Bearer {access_token}",
                },
                timeout=10.0,
                follow_redirects=True,
            )
        except httpx.RequestError as exc:
            raise ApiError(
                503,
                "Authentication provider is unavailable",
            ) from exc

        if response.status_code in {200, 204}:
            return

        if response.status_code == 429:
            raise ApiError(
                429,
                "Too many authentication requests. Try again later",
            )

        if response.status_code in {400, 401, 403}:
            raise ApiError(
                401,
                "Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        raise ApiError(
            502,
            "Unable to revoke the Supabase session",
        )


auth_service = AuthService()