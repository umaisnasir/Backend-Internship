from decimal import Decimal

from app.pricing import (
    AiTokenUsage,
    calculate_ai_cost_nano_usd,
    nano_usd_to_decimal_usd,
)


def test_ai_cost_uses_cached_rate_and_does_not_double_reasoning(
) -> None:
    usage = AiTokenUsage(
        input_tokens=1000,
        cached_input_tokens=400,
        output_tokens=200,
        reasoning_tokens=150,
    )

    cost = calculate_ai_cost_nano_usd(
        usage
    )

    # Uncached input:
    # 600 * 750 = 450,000
    #
    # Cached input:
    # 400 * 75 = 30,000
    #
    # Output, already including reasoning:
    # 200 * 4,500 = 900,000
    #
    # Total:
    # 1,380,000 nano-USD
    assert cost == 1_380_000

    assert (
        nano_usd_to_decimal_usd(cost)
        == Decimal("0.001380000")
    )

    same_output_without_reasoning_detail = (
        AiTokenUsage(
            input_tokens=1000,
            cached_input_tokens=400,
            output_tokens=200,
            reasoning_tokens=0,
        )
    )

    assert (
        calculate_ai_cost_nano_usd(
            same_output_without_reasoning_detail
        )
        == cost
    )