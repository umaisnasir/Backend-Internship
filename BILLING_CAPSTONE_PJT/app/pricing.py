from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


# Pinned pricing snapshot for deterministic billing and tests.
# Snapshot date: 2026-07-30.
# Model: GPT-5.4-mini, standard short-context pricing.
PRICING_VERSION = "openai-gpt-5.4-mini-2026-07-30"

# 1 USD = 1,000,000,000 nano-USD.
NANO_USD_PER_USD = 1_000_000_000

# Educational service rate: $0.001 for one API call.
API_CALL_NANO_USD = 1_000_000

# $0.75 / 1,000,000 input tokens.
AI_INPUT_NANO_USD_PER_TOKEN = 750

# $0.075 / 1,000,000 cached-input tokens.
AI_CACHED_INPUT_NANO_USD_PER_TOKEN = 75

# $4.50 / 1,000,000 output tokens.
AI_OUTPUT_NANO_USD_PER_TOKEN = 4_500


@dataclass(frozen=True)
class AiTokenUsage:
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    reasoning_tokens: int

    @property
    def quota_quantity(self) -> int:
        # Reasoning tokens are already included in output_tokens.
        return self.input_tokens + self.output_tokens


def validate_ai_usage(usage: AiTokenUsage) -> None:
    values = (
        usage.input_tokens,
        usage.cached_input_tokens,
        usage.output_tokens,
        usage.reasoning_tokens,
    )

    if any(value < 0 for value in values):
        raise ValueError(
            "Token counts cannot be negative"
        )

    if usage.cached_input_tokens > usage.input_tokens:
        raise ValueError(
            "cached_input_tokens cannot exceed input_tokens"
        )

    if usage.reasoning_tokens > usage.output_tokens:
        raise ValueError(
            "reasoning_tokens cannot exceed output_tokens"
        )

    if usage.quota_quantity <= 0:
        raise ValueError(
            "At least one input or output token is required"
        )


def calculate_ai_cost_nano_usd(
    usage: AiTokenUsage,
) -> int:
    validate_ai_usage(usage)

    uncached_input_tokens = (
        usage.input_tokens
        - usage.cached_input_tokens
    )

    input_cost = (
        uncached_input_tokens
        * AI_INPUT_NANO_USD_PER_TOKEN
    )

    cached_input_cost = (
        usage.cached_input_tokens
        * AI_CACHED_INPUT_NANO_USD_PER_TOKEN
    )

    # Do not add reasoning_tokens here.
    # They are a subset of output_tokens.
    output_cost = (
        usage.output_tokens
        * AI_OUTPUT_NANO_USD_PER_TOKEN
    )

    return (
        input_cost
        + cached_input_cost
        + output_cost
    )


def nano_usd_to_decimal_usd(
    value: int,
) -> Decimal:
    return (
        Decimal(value)
        / Decimal(NANO_USD_PER_USD)
    ).quantize(
        Decimal("0.000000001"),
        rounding=ROUND_HALF_UP,
    )