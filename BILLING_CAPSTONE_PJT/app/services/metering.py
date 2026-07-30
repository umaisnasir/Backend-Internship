from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.constants import (
    ACTIVE_SUBSCRIPTION_STATUSES,
    PlanCode,
    UsageType,
)
from app.exceptions import (
    BillingRequiredError,
    IdempotencyConflictError,
    QuotaExceededError,
    TenantNotFoundError,
)
from app.models import Tenant, UsageEvent
from app.pricing import (
    API_CALL_NANO_USD,
    PRICING_VERSION,
    AiTokenUsage,
    calculate_ai_cost_nano_usd,
)


@dataclass(frozen=True)
class MeterResult:
    event: UsageEvent
    duplicate: bool
    used_after: int
    limit: int


class MeteringService:
    def record_api_call(
        self,
        session: Session,
        *,
        tenant_id: str,
        idempotency_key: str,
        occurred_at: datetime | None = None,
    ) -> MeterResult:
        return self._record(
            session,
            tenant_id=tenant_id,
            usage_type=UsageType.API_CALL,
            quantity=1,
            idempotency_key=idempotency_key,
            cost_nano_usd=API_CALL_NANO_USD,
            occurred_at=occurred_at,
        )

    def record_ai_tokens(
        self,
        session: Session,
        *,
        tenant_id: str,
        idempotency_key: str,
        usage: AiTokenUsage,
        occurred_at: datetime | None = None,
    ) -> MeterResult:
        return self._record(
            session,
            tenant_id=tenant_id,
            usage_type=UsageType.AI_TOKENS,
            quantity=usage.quota_quantity,
            idempotency_key=idempotency_key,
            cost_nano_usd=(
                calculate_ai_cost_nano_usd(usage)
            ),
            input_tokens=usage.input_tokens,
            cached_input_tokens=(
                usage.cached_input_tokens
            ),
            output_tokens=usage.output_tokens,
            reasoning_tokens=usage.reasoning_tokens,
            occurred_at=occurred_at,
        )

    def _record(
        self,
        session: Session,
        *,
        tenant_id: str,
        usage_type: UsageType,
        quantity: int,
        idempotency_key: str,
        cost_nano_usd: int,
        input_tokens: int = 0,
        cached_input_tokens: int = 0,
        output_tokens: int = 0,
        reasoning_tokens: int = 0,
        occurred_at: datetime | None = None,
    ) -> MeterResult:
        event_time = occurred_at or datetime.now(UTC)

        period_start, period_end = month_bounds(
            event_time
        )

        # PostgreSQL locks this tenant row until
        # the transaction is committed or rolled back.
        tenant = session.scalar(
            select(Tenant)
            .where(Tenant.id == tenant_id)
            .with_for_update()
        )

        if tenant is None:
            raise TenantNotFoundError(
                f"Tenant {tenant_id} was not found"
            )

        existing = session.scalar(
            select(UsageEvent).where(
                UsageEvent.tenant_id == tenant_id,
                UsageEvent.idempotency_key
                == idempotency_key,
            )
        )

        if existing is not None:
            self._validate_replay(
                existing=existing,
                usage_type=usage_type,
                quantity=quantity,
                input_tokens=input_tokens,
                cached_input_tokens=(
                    cached_input_tokens
                ),
                output_tokens=output_tokens,
                reasoning_tokens=reasoning_tokens,
            )

            used = self._monthly_used(
                session,
                tenant_id=tenant_id,
                usage_type=usage_type,
                period_start=period_start,
                period_end=period_end,
            )

            limit = self._limit_for(
                tenant,
                usage_type,
            )

            return MeterResult(
                event=existing,
                duplicate=True,
                used_after=used,
                limit=limit,
            )

        self._assert_billing_access(tenant)

        used_before = self._monthly_used(
            session,
            tenant_id=tenant_id,
            usage_type=usage_type,
            period_start=period_start,
            period_end=period_end,
        )

        limit = self._limit_for(
            tenant,
            usage_type,
        )

        if used_before + quantity > limit:
            raise QuotaExceededError(
                (
                    f"Monthly {usage_type.value} quota "
                    f"exceeded: used={used_before}, "
                    f"requested={quantity}, limit={limit}"
                ),
                used=used_before,
                requested=quantity,
                limit=limit,
            )

        event = UsageEvent(
            tenant_id=tenant_id,
            usage_type=usage_type.value,
            idempotency_key=idempotency_key,
            quantity=quantity,
            input_tokens=input_tokens,
            cached_input_tokens=cached_input_tokens,
            output_tokens=output_tokens,
            reasoning_tokens=reasoning_tokens,
            cost_nano_usd=cost_nano_usd,
            pricing_version=PRICING_VERSION,
            occurred_at=event_time,
        )

        session.add(event)
        session.flush()

        return MeterResult(
            event=event,
            duplicate=False,
            used_after=used_before + quantity,
            limit=limit,
        )

    @staticmethod
    def _validate_replay(
        *,
        existing: UsageEvent,
        usage_type: UsageType,
        quantity: int,
        input_tokens: int,
        cached_input_tokens: int,
        output_tokens: int,
        reasoning_tokens: int,
    ) -> None:
        replay_payload = (
            usage_type.value,
            quantity,
            input_tokens,
            cached_input_tokens,
            output_tokens,
            reasoning_tokens,
        )

        original_payload = (
            existing.usage_type,
            existing.quantity,
            existing.input_tokens,
            existing.cached_input_tokens,
            existing.output_tokens,
            existing.reasoning_tokens,
        )

        if replay_payload != original_payload:
            raise IdempotencyConflictError(
                "The idempotency key was already "
                "used with a different payload"
            )

    @staticmethod
    def _monthly_used(
        session: Session,
        *,
        tenant_id: str,
        usage_type: UsageType,
        period_start: datetime,
        period_end: datetime,
    ) -> int:
        value = session.scalar(
            select(
                func.coalesce(
                    func.sum(UsageEvent.quantity),
                    0,
                )
            ).where(
                UsageEvent.tenant_id == tenant_id,
                UsageEvent.usage_type
                == usage_type.value,
                UsageEvent.occurred_at
                >= period_start,
                UsageEvent.occurred_at
                < period_end,
            )
        )

        return int(value or 0)

    @staticmethod
    def _limit_for(
        tenant: Tenant,
        usage_type: UsageType,
    ) -> int:
        if usage_type == UsageType.API_CALL:
            return int(
                tenant.plan.api_call_limit
            )

        return int(
            tenant.plan.ai_token_limit
        )

    @staticmethod
    def _assert_billing_access(
        tenant: Tenant,
    ) -> None:
        if (
            tenant.plan_code == PlanCode.PRO
            and tenant.subscription_status
            not in ACTIVE_SUBSCRIPTION_STATUSES
        ):
            raise BillingRequiredError(
                "The Pro subscription is not active. "
                "Update payment details before continuing."
            )


def month_bounds(
    value: datetime,
) -> tuple[datetime, datetime]:
    normalized = value.astimezone(UTC)

    start = normalized.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    if start.month == 12:
        end = start.replace(
            year=start.year + 1,
            month=1,
        )
    else:
        end = start.replace(
            month=start.month + 1,
        )

    return start, end