from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.constants import UsageType
from app.exceptions import TenantNotFoundError
from app.models import Tenant, UsageEvent
from app.pricing import (
    PRICING_VERSION,
    nano_usd_to_decimal_usd,
)
from app.services.metering import month_bounds


class ReportingService:
    def monthly_report(
        self,
        session: Session,
        *,
        tenant_id: str,
        month: str | None = None,
    ) -> dict[str, object]:
        reference = parse_month(month)

        period_start, period_end = month_bounds(
            reference
        )

        tenant = session.scalar(
            select(Tenant).where(
                Tenant.id == tenant_id
            )
        )

        if tenant is None:
            raise TenantNotFoundError(
                f"Tenant {tenant_id} was not found"
            )

        rows = session.execute(
            select(
                UsageEvent.usage_type,
                func.coalesce(
                    func.sum(UsageEvent.quantity),
                    0,
                ),
                func.coalesce(
                    func.sum(
                        UsageEvent.cost_nano_usd
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(
                        UsageEvent.input_tokens
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(
                        UsageEvent.cached_input_tokens
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(
                        UsageEvent.output_tokens
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(
                        UsageEvent.reasoning_tokens
                    ),
                    0,
                ),
            )
            .where(
                UsageEvent.tenant_id == tenant_id,
                UsageEvent.occurred_at
                >= period_start,
                UsageEvent.occurred_at
                < period_end,
            )
            .group_by(UsageEvent.usage_type)
        ).all()

        grouped: dict[
            str,
            tuple[int, int, int, int, int, int],
        ] = {}

        for row in rows:
            grouped[str(row[0])] = tuple(
                int(value)
                for value in row[1:]
            )

        calls = grouped.get(
            UsageType.API_CALL.value,
            (0, 0, 0, 0, 0, 0),
        )

        tokens = grouped.get(
            UsageType.AI_TOKENS.value,
            (0, 0, 0, 0, 0, 0),
        )

        call_used, call_cost, *_ = calls

        (
            token_used,
            token_cost,
            input_tokens,
            cached_input_tokens,
            output_tokens,
            reasoning_tokens,
        ) = tokens

        usage_cost_nano = (
            call_cost + token_cost
        )

        plan_fee_usd = (
            Decimal(
                tenant.plan.monthly_price_cents
            )
            / Decimal(100)
        ).quantize(
            Decimal("0.01")
        )

        usage_cost_usd = (
            nano_usd_to_decimal_usd(
                usage_cost_nano
            )
        )

        return {
            "tenant_id": tenant.id,
            "period": period_start.strftime(
                "%Y-%m"
            ),
            "plan": tenant.plan_code,
            "subscription_status": (
                tenant.subscription_status
            ),
            "api_calls": quota_view(
                used=call_used,
                limit=int(
                    tenant.plan.api_call_limit
                ),
                cost_nano=call_cost,
            ),
            "ai_tokens": quota_view(
                used=token_used,
                limit=int(
                    tenant.plan.ai_token_limit
                ),
                cost_nano=token_cost,
            ),
            "ai_breakdown": {
                "input_tokens": input_tokens,
                "cached_input_tokens": (
                    cached_input_tokens
                ),
                "uncached_input_tokens": (
                    input_tokens
                    - cached_input_tokens
                ),
                "output_tokens": output_tokens,
                "reasoning_tokens": (
                    reasoning_tokens
                ),
                "note": (
                    "Reasoning tokens are already "
                    "included in output_tokens and "
                    "are not added again."
                ),
            },
            "usage_cost_usd": usage_cost_usd,
            "plan_fee_usd": plan_fee_usd,
            "estimated_total_usd": (
                usage_cost_usd
                + plan_fee_usd
            ).quantize(
                Decimal("0.000000001")
            ),
            "pricing_version": (
                PRICING_VERSION
            ),
        }


def quota_view(
    *,
    used: int,
    limit: int,
    cost_nano: int,
) -> dict[str, object]:
    remaining = max(
        limit - used,
        0,
    )

    return {
        "used": used,
        "limit": limit,
        "remaining": remaining,
        "reached": used >= limit,
        "cost_usd": (
            nano_usd_to_decimal_usd(
                cost_nano
            )
        ),
    }


def parse_month(
    month: str | None,
) -> datetime:
    if month is None:
        return datetime.now(UTC)

    try:
        parsed = datetime.strptime(
            month,
            "%Y-%m",
        )
    except ValueError as exc:
        raise ValueError(
            "month must use YYYY-MM format"
        ) from exc

    return parsed.replace(tzinfo=UTC)