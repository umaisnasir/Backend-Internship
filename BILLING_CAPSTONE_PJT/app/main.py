from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import (
    RequestValidationError,
)
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.exceptions import (
    AppError,
    QuotaExceededError,
)
from app.routers.actions import (
    router as actions_router,
)
from app.routers.checkout import (
    router as checkout_router,
)
from app.routers.usage import (
    router as usage_router,
)
from app.routers.webhooks import (
    router as webhooks_router,
)


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Idempotent usage metering, monthly "
        "quota enforcement, pinned AI cost "
        "calculation, and Stripe subscription sync."
    ),
)


@app.exception_handler(AppError)
async def app_error_handler(
    request: Request,
    exc: AppError,
) -> JSONResponse:
    content: dict[str, object] = {
        "error": exc.message,
    }

    if isinstance(
        exc,
        QuotaExceededError,
    ):
        content.update(
            {
                "used": exc.used,
                "limit": exc.limit,
                "requested": exc.requested,
                "retry_after": (
                    "next monthly billing period"
                ),
            }
        )

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
    )


@app.exception_handler(
    RequestValidationError
)
async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content=jsonable_encoder(
            {
                "error": "Invalid request",
                "details": exc.errors(),
            }
        ),
    )


app.include_router(actions_router)
app.include_router(usage_router)
app.include_router(checkout_router)
app.include_router(webhooks_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.app_env,
    }


@app.get("/checkout/success")
def checkout_success(
    session_id: str,
) -> dict[str, str]:
    return {
        "message": (
            "Checkout completed. Subscription "
            "state is finalized by webhook."
        ),
        "session_id": session_id,
    }


@app.get("/checkout/cancel")
def checkout_cancel() -> dict[str, str]:
    return {
        "message": (
            "Checkout canceled. "
            "No plan change was made."
        )
    }