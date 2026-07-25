from fastapi import APIRouter, status

from ..models import PublicInfoResponse


router = APIRouter(
    prefix="/public",
    tags=["Public"],
)


@router.get(
    "/info",
    response_model=PublicInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Return public information",
)
def public_info() -> PublicInfoResponse:
    return PublicInfoResponse(
        message="Welcome stranger! This info is public."
    )