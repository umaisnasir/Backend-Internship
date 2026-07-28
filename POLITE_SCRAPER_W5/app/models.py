from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class BookRecord(BaseModel):
    upc: str = Field(min_length=1)
    title: str = Field(min_length=1)
    category: str = Field(min_length=1)
    product_type: str = Field(min_length=1)

    price_gbp: Decimal = Field(ge=0)
    price_excl_tax_gbp: Decimal = Field(ge=0)
    price_incl_tax_gbp: Decimal = Field(ge=0)
    tax_gbp: Decimal = Field(ge=0)

    availability_text: str
    stock_count: int = Field(ge=0)
    in_stock: bool

    rating: int = Field(ge=1, le=5)
    review_count: int = Field(ge=0)

    description: str | None = None

    image_url: HttpUrl
    source_url: HttpUrl
    scraped_at: datetime

    def to_rag_document(self) -> "RagDocument":
        description = self.description or "No description provided."

        text = (
            f"Title: {self.title}\n"
            f"Category: {self.category}\n"
            f"Product type: {self.product_type}\n"
            f"Price: £{self.price_gbp}\n"
            f"Availability: {self.availability_text}\n"
            f"Rating: {self.rating} out of 5\n"
            f"Reviews: {self.review_count}\n"
            f"Description: {description}"
        )

        metadata: dict[str, Any] = {
            "upc": self.upc,
            "category": self.category,
            "price_gbp": str(self.price_gbp),
            "stock_count": self.stock_count,
            "in_stock": self.in_stock,
            "rating": self.rating,
            "source_url": str(self.source_url),
            "scraped_at": self.scraped_at.isoformat(),
        }

        return RagDocument(
            id=self.upc,
            text=text,
            metadata=metadata,
        )


class RagDocument(BaseModel):
    id: str
    text: str
    metadata: dict[str, Any]


class ScrapeSummary(BaseModel):
    requested_limit: int
    listing_pages_fetched: int
    detail_pages_fetched: int
    records_saved: int
    records_skipped: int
    total_records_in_database: int
    structured_jsonl_path: str
    rag_jsonl_path: str
    csv_path: str