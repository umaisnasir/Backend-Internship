from typing import Annotated

from fastapi import APIRouter, Depends, status

from ..dependencies.auth import AuthContext, get_auth_context
from ..models import DashboardResponse, PublicUser
from ..services.auth import serialize_user


router = APIRouter(
    prefix="/protected",
    tags=["Protected"],
)


@router.get(
    "/profile",
    response_model=PublicUser,
    status_code=status.HTTP_200_OK,
    summary="Return the verified user's profile",
)
def profile(
    context: Annotated[
        AuthContext,
        Depends(get_auth_context),
    ],
) -> PublicUser:
    return serialize_user(context.user)


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Return a protected dashboard response",
)
def dashboard(
    context: Annotated[
        AuthContext,
        Depends(get_auth_context),
    ],
) -> DashboardResponse:
    return DashboardResponse(
        message="Welcome to your protected dashboard",
        user_id=str(context.user.id),
    )