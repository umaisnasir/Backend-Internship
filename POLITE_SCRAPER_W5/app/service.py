import logging

from pydantic import ValidationError

from app.config import Settings
from app.exceptions import ParseError, ScraperError
from app.exporters import (
    export_csv,
    export_rag_jsonl,
    export_structured_jsonl,
)
from app.http_client import PoliteHttpClient
from app.models import ScrapeSummary
from app.parser import (
    parse_book_page,
    parse_listing_page,
)
from app.storage import SQLiteBookRepository


logger = logging.getLogger(__name__)


class ScraperService:
    def __init__(
        self,
        settings: Settings,
        fetcher: PoliteHttpClient,
        repository: SQLiteBookRepository,
    ) -> None:
        self.settings = settings
        self.fetcher = fetcher
        self.repository = repository

    def scrape(
        self,
        max_books: int,
    ) -> ScrapeSummary:
        if max_books < 1:
            raise ValueError(
                "max_books must be at least 1"
            )

        self.repository.initialize()

        listing_url: str | None = (
            self.settings.start_url
        )

        visited_listing_urls: set[str] = set()
        visited_book_urls: set[str] = set()

        listing_pages_fetched = 0
        detail_pages_fetched = 0
        records_saved = 0
        records_skipped = 0
        consecutive_failures = 0

        while (
            listing_url
            and records_saved < max_books
        ):
            if listing_url in visited_listing_urls:
                raise ParseError(
                    "Pagination loop detected at "
                    f"{listing_url}"
                )

            visited_listing_urls.add(
                listing_url
            )

            listing_html = (
                self.fetcher.get_text(
                    listing_url
                )
            )

            listing_pages_fetched += 1

            book_urls, listing_url = (
                parse_listing_page(
                    listing_html,
                    listing_url,
                )
            )

            for book_url in book_urls:
                if records_saved >= max_books:
                    break

                if book_url in visited_book_urls:
                    records_skipped += 1
                    continue

                visited_book_urls.add(book_url)

                try:
                    book_html = (
                        self.fetcher.get_text(
                            book_url
                        )
                    )

                    detail_pages_fetched += 1

                    book = parse_book_page(
                        book_html,
                        book_url,
                    )

                    self.repository.upsert(book)

                    records_saved += 1
                    consecutive_failures = 0

                    logger.info(
                        "Saved %s",
                        book.title,
                    )

                except (
                    ScraperError,
                    ValidationError,
                ):
                    records_skipped += 1
                    consecutive_failures += 1

                    logger.exception(
                        "Skipping failed book page: %s",
                        book_url,
                    )

                    if (
                        consecutive_failures
                        >= self.settings
                        .max_consecutive_failures
                    ):
                        raise ParseError(
                            "Too many consecutive "
                            "book-page failures; "
                            "stopping to avoid hammering "
                            "a site whose HTML may have changed."
                        )

        self.export_all()

        return ScrapeSummary(
            requested_limit=max_books,
            listing_pages_fetched=(
                listing_pages_fetched
            ),
            detail_pages_fetched=(
                detail_pages_fetched
            ),
            records_saved=records_saved,
            records_skipped=records_skipped,
            total_records_in_database=(
                self.repository.count()
            ),
            structured_jsonl_path=str(
                self.settings
                .structured_jsonl_path
            ),
            rag_jsonl_path=str(
                self.settings.rag_jsonl_path
            ),
            csv_path=str(
                self.settings.csv_path
            ),
        )

    def export_all(self) -> None:
        records = self.repository.all_books()

        export_structured_jsonl(
            records,
            self.settings.structured_jsonl_path,
        )

        export_rag_jsonl(
            records,
            self.settings.rag_jsonl_path,
        )

        export_csv(
            records,
            self.settings.csv_path,
        )