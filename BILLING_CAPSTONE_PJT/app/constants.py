from enum import StrEnum


class UsageType(StrEnum):
    API_CALL = "api_call"
    AI_TOKENS = "ai_tokens"


class PlanCode(StrEnum):
    FREE = "free"
    PRO = "pro"


ACTIVE_SUBSCRIPTION_STATUSES = {
    "active",
    "trialing",
}