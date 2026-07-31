from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Header,
)
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.schemas import (
    CheckoutRequest,
    CheckoutResponse,
)
from app.services.stripe_service import (
    StripeService,
)


settings = get_settings()

router = APIRouter(
    prefix="/v1/billing",
    tags=["Billing"],
)

service = StripeService(
    secret_key=settings.stripe_secret_key,
    webhook_secret=(
        settings.stripe_webhook_secret
    ),
    base_url=settings.base_url,
)


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    summary=(
        "Create a Stripe Checkout "
        "subscription session"
    ),
)
def create_checkout(
    body: CheckoutRequest,
    idempotency_key: Annotated[
        str,
        Header(
            alias="Idempotency-Key",
            min_length=8,
            max_length=255,
        ),
    ],
    session: Session = Depends(get_db),
) -> CheckoutResponse:
    checkout_session = (
        service.create_checkout_session(
            session,
            tenant_id=body.tenant_id,
            idempotency_key=idempotency_key,
        )
    )

    return CheckoutResponse(
        checkout_session_id=(
            checkout_session.id
        ),
        checkout_url=checkout_session.url,
    )