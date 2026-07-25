from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends, Header

from ..exceptions import ApiError
from ..services.auth import auth_service


@dataclass(frozen=True)
class AuthContext:
    """
    Verified authentication information for one request.
    """

    access_token: str
    user: Any


def extract_access_token(
    authorization: Annotated[
        str | None,
        Header(alias="Authorization"),
    ] = None,
) -> str:
    if authorization is None:
        raise ApiError(
            status_code=401,
            message="Access token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, separator, token = authorization.partition(" ")

    if (
        not separator
        or scheme.lower() != "bearer"
        or not token.strip()
    ):
        raise ApiError(
            status_code=401,
            message="Access token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token.strip()


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