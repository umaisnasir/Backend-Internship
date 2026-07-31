class AppError(Exception):
    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class TenantNotFoundError(AppError):
    status_code = 404


class PlanNotFoundError(AppError):
    status_code = 404


class IdempotencyConflictError(AppError):
    status_code = 409


class BillingRequiredError(AppError):
    status_code = 402


class QuotaExceededError(AppError):
    status_code = 429

    def __init__(
        self,
        message: str,
        *,
        used: int,
        limit: int,
        requested: int,
    ) -> None:
        super().__init__(message)

        self.used = used
        self.limit = limit
        self.requested = requested