from typing import Annotated

from fastapi import APIRouter, Depends, Header, status

from ..exceptions import ApiError


router = APIRouter(
    prefix="/protected",
    tags=["Protected"],
)


def require_unverified_bearer_token(
    authorization: Annotated[
        str | None,
        Header(alias="Authorization"),
    ] = None,
) -> str:
    """
    Stage 2 only: checks header format but does not verify the JWT.
    """

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


@router.get(
    "/dashboard",
    status_code=status.HTTP_200_OK,
    summary="Temporary Stage 2 dashboard",
)
def dashboard(
    token: Annotated[
        str,
        Depends(require_unverified_bearer_token),
    ],
) -> dict[str, str]:
    return {
        "message": "Temporary dashboard access granted",
        "warning": "Token format checked, but token not verified",
    }