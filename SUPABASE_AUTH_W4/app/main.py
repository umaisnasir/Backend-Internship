from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .config import get_settings
from .exceptions import ApiError
from .routers.auth import router as auth_router
from .routers.protected import router as protected_router
from .routers.public import router as public_router


get_settings()


app = FastAPI(
    title="Supabase Authentication API",
    version="0.3.0",
    description=(
        "A FastAPI project using Supabase Auth for "
        "signup, login, logout, and protected routes."
    ),
)


@app.exception_handler(ApiError)
async def api_error_handler(
    request: Request,
    exc: ApiError,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message},
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    details: list[dict[str, str]] = []

    for error in exc.errors():
        field_parts = [
            str(part)
            for part in error.get("loc", [])
            if part != "body"
        ]

        details.append(
            {
                "field": ".".join(field_parts) or "body",
                "message": str(error.get("msg", "Invalid value")),
            }
        )

    return JSONResponse(
        status_code=400,
        content={
            "error": "Invalid request body",
            "details": details,
        },
    )


app.include_router(auth_router)
app.include_router(public_router)
app.include_router(protected_router)


@app.get(
    "/",
    summary="Describe the API",
)
def read_root() -> dict[str, str]:
    return {
        "name": "Supabase Authentication API",
        "version": "0.3.0",
        "stage": "Stage 2",
        "docs": "/docs",
    }


@app.get(
    "/health",
    summary="Check whether the API is running",
)
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "supabase_configuration": "loaded",
    }