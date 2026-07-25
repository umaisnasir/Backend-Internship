from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from ..dependencies.auth import AuthContext, get_auth_context
from ..models import AuthCredentials, SignupResponse, TokenResponse
from ..services.auth import auth_service


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Supabase Auth user",
)
def signup(credentials: AuthCredentials) -> SignupResponse:
    return auth_service.signup(credentials)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Log in and receive Supabase tokens",
)
def login(credentials: AuthCredentials) -> TokenResponse:
    return auth_service.login(credentials)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Revoke the current Supabase Auth session",
)
def logout(
    context: Annotated[
        AuthContext,
        Depends(get_auth_context),
    ],
) -> Response:
    auth_service.logout(context.access_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)