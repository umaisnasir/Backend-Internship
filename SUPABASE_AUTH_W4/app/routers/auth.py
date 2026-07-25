from fastapi import APIRouter, status

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