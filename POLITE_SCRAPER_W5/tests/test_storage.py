from datetime import UTC, datetime
from decimal import Decimal

from app.models import BookRecord
from app.storage import SQLiteBookRepository


def make_book(
    title: str = "First title",
) -> BookRecord:
    return BookRecord(
        upc="upc-1",
        title=title,
        category="Travel",
        product_type="Books",
        price_gbp=Decimal("10.00"),
        price_excl_tax_gbp=Decimal("10.00"),
        price_incl_tax_gbp=Decimal("10.00"),
        tax_gbp=Decimal("0.00"),
        availability_text=(
            "In stock (3 available)"
        ),
        stock_count=3,
        in_stock=True,
        rating=5,
        review_count=0,
        description="Test description",
        image_url=(
            "https://books.toscrape.com/"
            "media/test.jpg"
        ),
        source_url=(
            "https://books.toscrape.com/"
            "catalogue/test/index.html"
        ),
        scraped_at=datetime.now(UTC),
    )


def test_repository_upsert_updates_existing_row(
    tmp_path,
) -> None:
    repository = SQLiteBookRepository(
        tmp_path / "books.db"
    )

    repository.initialize()

    repository.upsert(
        make_book()
    )

    repository.upsert(
        make_book(
            title="Updated title"
        )
    )

    assert repository.count() == 1

    saved = repository.get_by_upc(
        "upc-1"
    )

    assert saved is not None
    assert saved.title == "Updated title"


def test_repository_stats(
    tmp_path,
) -> None:
    repository = SQLiteBookRepository(
        tmp_path / "books.db"
    )

    repository.initialize()
    repository.upsert(make_book())

    stats = repository.stats()

    assert stats["total_books"] == 1
    assert stats["in_stock_books"] == 1
    assert stats["category_count"] == 1