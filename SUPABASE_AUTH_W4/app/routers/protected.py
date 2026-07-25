from typing import Annotated

from fastapi import APIRouter, Depends, Header, status

from ..exceptions import ApiError
from ..models import PublicUser
from ..services.auth import auth_service, serialize_user


router = APIRouter(
    prefix="/protected",
    tags=["Protected"],
)


def extract_bearer_token(
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


@router.get(
    "/profile",
    response_model=PublicUser,
    status_code=status.HTTP_200_OK,
    summary="Return the verified user's profile",
)
def profile(
    access_token: Annotated[
        str,
        Depends(extract_bearer_token),
    ],
) -> PublicUser:
    user = auth_service.verify_access_token(access_token)
    return serialize_user(user)


@router.get(
    "/dashboard",
    status_code=status.HTTP_200_OK,
    summary="Temporary Stage 3 dashboard",
)
def dashboard(
    access_token: Annotated[
        str,
        Depends(extract_bearer_token),
    ],
) -> dict[str, str]:
    # Still intentionally unverified until Stage 4.
    return {
        "message": "Temporary dashboard access granted",
        "warning": "Dashboard token is not verified until Stage 4",
    }