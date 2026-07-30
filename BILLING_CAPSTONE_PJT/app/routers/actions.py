from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Header,
)
from sqlalchemy.orm import Session

from app.db import get_db
from app.pricing import (
    AiTokenUsage,
    nano_usd_to_decimal_usd,
)
from app.schemas import (
    AiActionRequest,
    MeterResponse,
)
from app.services.metering import (
    MeterResult,
    MeteringService,
)


router = APIRouter(
    prefix="/v1/actions",
    tags=["Billable actions"],
)

service = MeteringService()


@router.post(
    "/call",
    response_model=MeterResponse,
    summary="Perform one billable API call",
)
def billable_call(
    tenant_id: Annotated[
        str,
        Header(alias="X-Tenant-ID"),
    ],
    idempotency_key: Annotated[
        str,
        Header(
            alias="Idempotency-Key",
            min_length=8,
            max_length=255,
        ),
    ],
    session: Session = Depends(get_db),
) -> MeterResponse:
    with session.begin():
        result = service.record_api_call(
            session,
            tenant_id=tenant_id,
            idempotency_key=idempotency_key,
        )

    return build_response(result)


@router.post(
    "/ai",
    response_model=MeterResponse,
    summary="Record one billable AI request",
)
def billable_ai_action(
    body: AiActionRequest,
    tenant_id: Annotated[
        str,
        Header(alias="X-Tenant-ID"),
    ],
    idempotency_key: Annotated[
        str,
        Header(
            alias="Idempotency-Key",
            min_length=8,
            max_length=255,
        ),
    ],
    session: Session = Depends(get_db),
) -> MeterResponse:
    usage = AiTokenUsage(
        input_tokens=body.input_tokens,
        cached_input_tokens=(
            body.cached_input_tokens
        ),
        output_tokens=body.output_tokens,
        reasoning_tokens=(
            body.reasoning_tokens
        ),
    )

    with session.begin():
        result = service.record_ai_tokens(
            session,
            tenant_id=tenant_id,
            idempotency_key=idempotency_key,
            usage=usage,
        )

    return build_response(result)


def build_response(
    result: MeterResult,
) -> MeterResponse:
    remaining = max(
        result.limit - result.used_after,
        0,
    )

    return MeterResponse(
        event_id=result.event.id,
        duplicate=result.duplicate,
        usage_type=result.event.usage_type,
        quantity=result.event.quantity,
        cost_usd=nano_usd_to_decimal_usd(
            result.event.cost_nano_usd
        ),
        used_after=result.used_after,
        limit=result.limit,
        remaining=remaining,
    )