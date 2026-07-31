from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class AiActionRequest(BaseModel):
    input_tokens: int = Field(ge=0)
    cached_input_tokens: int = Field(
        default=0,
        ge=0,
    )
    output_tokens: int = Field(ge=0)
    reasoning_tokens: int = Field(
        default=0,
        ge=0,
    )

    @field_validator("cached_input_tokens")
    @classmethod
    def validate_cached_tokens(
        cls,
        value: int,
        info,
    ) -> int:
        input_tokens = info.data.get("input_tokens")

        if (
            input_tokens is not None
            and value > input_tokens
        ):
            raise ValueError(
                "cached_input_tokens cannot exceed "
                "input_tokens"
            )

        return value

    @field_validator("reasoning_tokens")
    @classmethod
    def validate_reasoning_tokens(
        cls,
        value: int,
        info,
    ) -> int:
        output_tokens = info.data.get("output_tokens")

        if (
            output_tokens is not None
            and value > output_tokens
        ):
            raise ValueError(
                "reasoning_tokens cannot exceed "
                "output_tokens"
            )

        return value


class MeterResponse(BaseModel):
    event_id: str
    duplicate: bool
    usage_type: str
    quantity: int
    cost_usd: Decimal
    used_after: int
    limit: int
    remaining: int


class QuotaView(BaseModel):
    used: int
    limit: int
    remaining: int
    reached: bool
    cost_usd: Decimal


class AiUsageBreakdown(BaseModel):
    input_tokens: int
    cached_input_tokens: int
    uncached_input_tokens: int
    output_tokens: int
    reasoning_tokens: int
    note: str


class UsageReport(BaseModel):
    tenant_id: str
    period: str
    plan: str
    subscription_status: str
    api_calls: QuotaView
    ai_tokens: QuotaView
    ai_breakdown: AiUsageBreakdown
    usage_cost_usd: Decimal
    plan_fee_usd: Decimal
    estimated_total_usd: Decimal
    pricing_version: str


class CheckoutRequest(BaseModel):
    tenant_id: str


class CheckoutResponse(BaseModel):
    checkout_session_id: str
    checkout_url: str


class WebhookResponse(BaseModel):
    received: bool = True
    duplicate: bool
    event_id: str
    event_type: str