from fastapi import (
    FastAPI,
    HTTPException,
    Query,
)

from app.config import get_settings
from app.models import BookRecord
from app.storage import SQLiteBookRepository


settings = get_settings()

repository = SQLiteBookRepository(
    settings.database_path
)

repository.initialize()


app = FastAPI(
    title="Polite Scraper Dataset API",
    version="1.0.0",
    description=(
        "Read-only API for the books collected "
        "by the Week 5 scraper."
    ),
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": (
            "Polite Scraper Dataset API"
        ),
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "database_records": (
            repository.count()
        ),
    }


@app.get(
    "/books",
    response_model=list[BookRecord],
)
def list_books(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    category: str | None = None,
) -> list[BookRecord]:
    return repository.list_books(
        limit=limit,
        offset=offset,
        category=category,
    )


@app.get(
    "/books/{upc}",
    response_model=BookRecord,
)
def get_book(upc: str) -> BookRecord:
    book = repository.get_by_upc(upc)

    if book is None:
        raise HTTPException(
            status_code=404,
            detail="Book not found",
        )

    return book


@app.get("/stats")
def stats() -> dict[str, object]:
    return repository.stats()