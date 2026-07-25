from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends, Security
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from ..exceptions import ApiError
from ..services.auth import auth_service


bearer_scheme = HTTPBearer(
    bearerFormat="JWT",
    scheme_name="SupabaseBearer",
    description=(
        "Paste only the Supabase access token. "
        "Swagger adds the Bearer prefix automatically."
    ),
    auto_error=False,
)


@dataclass(frozen=True)
class AuthContext:
    access_token: str
    user: Any


def extract_access_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Security(bearer_scheme),
    ],
) -> str:
    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not credentials.credentials.strip()
    ):
        raise ApiError(
            status_code=401,
            message="Access token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials.strip()


def get_auth_context(
    access_token: Annotated[
        str,
        Depends(extract_access_token),
    ],
) -> AuthContext:
    user = auth_service.verify_access_token(access_token)

    return AuthContext(
        access_token=access_token,
        user=user,
    )