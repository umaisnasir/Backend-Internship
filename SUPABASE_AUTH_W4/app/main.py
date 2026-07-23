from fastapi import FastAPI

from .config import get_settings


# Validate configuration when the application starts.
# The server will fail early with a clear message if .env
# is missing or contains placeholder values.
get_settings()


app = FastAPI(
    title="Supabase Authentication API",
    version="0.1.0",
    description=(
        "A FastAPI project using Supabase Auth for "
        "signup, login, logout, and protected routes."
    ),
)


@app.get(
    "/",
    summary="Describe the API",
)
def read_root() -> dict[str, str]:
    """
    Return basic information about the application.
    """

    return {
        "name": "Supabase Authentication API",
        "version": "0.1.0",
        "stage": "Stage 0",
        "docs": "/docs",
    }


@app.get(
    "/health",
    summary="Check whether the API is running",
)
def health_check() -> dict[str, str]:
    """
    Confirm that the server and configuration loaded.
    """

    return {
        "status": "ok",
        "supabase_configuration": "loaded",
    }