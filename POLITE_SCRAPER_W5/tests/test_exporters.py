import json
from datetime import UTC, datetime
from decimal import Decimal

from app.exporters import (
    export_rag_jsonl,
    export_structured_jsonl,
)
from app.models import BookRecord


def test_jsonl_exports_are_valid(
    tmp_path,
) -> None:
    book = BookRecord(
        upc="upc-1",
        title="Test book",
        category="Travel",
        product_type="Books",
        price_gbp=Decimal("10.00"),
        price_excl_tax_gbp=Decimal("10.00"),
        price_incl_tax_gbp=Decimal("10.00"),
        tax_gbp=Decimal("0.00"),
        availability_text=(
            "In stock (1 available)"
        ),
        stock_count=1,
        in_stock=True,
        rating=4,
        review_count=0,
        description="Description",
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

    structured_path = (
        tmp_path / "books.jsonl"
    )

    rag_path = (
        tmp_path / "rag.jsonl"
    )

    export_structured_jsonl(
        [book],
        structured_path,
    )

    export_rag_jsonl(
        [book],
        rag_path,
    )

    structured = json.loads(
        structured_path.read_text(
            encoding="utf-8"
        )
    )

    rag = json.loads(
        rag_path.read_text(
            encoding="utf-8"
        )
    )

    assert structured["upc"] == "upc-1"
    assert rag["id"] == "upc-1"

    assert (
        "Title: Test book"
        in rag["text"]
    )