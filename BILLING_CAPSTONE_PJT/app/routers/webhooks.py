import stripe
from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
)
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.schemas import WebhookResponse
from app.services.stripe_service import (
    StripeService,
)


settings = get_settings()

router = APIRouter(
    tags=["Stripe webhooks"],
)

service = StripeService(
    secret_key=settings.stripe_secret_key,
    webhook_secret=(
        settings.stripe_webhook_secret
    ),
    base_url=settings.base_url,
)


@router.post(
    "/webhooks/stripe",
    response_model=WebhookResponse,
    summary=(
        "Receive and verify Stripe "
        "webhook events"
    ),
)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(
        alias="Stripe-Signature"
    ),
    session: Session = Depends(get_db),
) -> WebhookResponse:
    # Signature verification must use
    # the unmodified raw request bytes.
    payload = await request.body()

    try:
        event = service.verify_event(
            payload=payload,
            signature=stripe_signature,
        )

    except (
        ValueError,
        stripe.error.SignatureVerificationError,
    ) as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid Stripe webhook signature"
            ),
        ) from exc

    with session.begin():
        duplicate = service.process_event(
            session,
            event,
        )

    return WebhookResponse(
        duplicate=duplicate,
        event_id=str(event["id"]),
        event_type=str(event["type"]),
    )