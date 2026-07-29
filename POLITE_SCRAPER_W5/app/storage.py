import sqlite3
from collections.abc import Iterable
from pathlib import Path

from app.models import BookRecord


SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    upc TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    product_type TEXT NOT NULL,

    price_gbp TEXT NOT NULL,
    price_excl_tax_gbp TEXT NOT NULL,
    price_incl_tax_gbp TEXT NOT NULL,
    tax_gbp TEXT NOT NULL,

    availability_text TEXT NOT NULL,

    stock_count INTEGER NOT NULL
        CHECK (stock_count >= 0),

    in_stock INTEGER NOT NULL
        CHECK (in_stock IN (0, 1)),

    rating INTEGER NOT NULL
        CHECK (rating BETWEEN 1 AND 5),

    review_count INTEGER NOT NULL
        CHECK (review_count >= 0),

    description TEXT,

    image_url TEXT NOT NULL,
    source_url TEXT NOT NULL UNIQUE,
    scraped_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_books_category
ON books(category);
"""


UPSERT = """
INSERT INTO books (
    upc,
    title,
    category,
    product_type,
    price_gbp,
    price_excl_tax_gbp,
    price_incl_tax_gbp,
    tax_gbp,
    availability_text,
    stock_count,
    in_stock,
    rating,
    review_count,
    description,
    image_url,
    source_url,
    scraped_at
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

ON CONFLICT(upc) DO UPDATE SET
    title = excluded.title,
    category = excluded.category,
    product_type = excluded.product_type,
    price_gbp = excluded.price_gbp,
    price_excl_tax_gbp = excluded.price_excl_tax_gbp,
    price_incl_tax_gbp = excluded.price_incl_tax_gbp,
    tax_gbp = excluded.tax_gbp,
    availability_text = excluded.availability_text,
    stock_count = excluded.stock_count,
    in_stock = excluded.in_stock,
    rating = excluded.rating,
    review_count = excluded.review_count,
    description = excluded.description,
    image_url = excluded.image_url,
    source_url = excluded.source_url,
    scraped_at = excluded.scraped_at;
"""


class SQLiteBookRepository:
    def __init__(
        self,
        database_path: Path,
    ) -> None:
        self.database_path = database_path

    def initialize(self) -> None:
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self._connect() as connection:
            connection.executescript(SCHEMA)

    def upsert(self, book: BookRecord) -> None:
        with self._connect() as connection:
            connection.execute(
                UPSERT,
                self._book_values(book),
            )

    def upsert_many(
        self,
        books: Iterable[BookRecord],
    ) -> None:
        values = [
            self._book_values(book)
            for book in books
        ]

        if not values:
            return

        with self._connect() as connection:
            connection.executemany(
                UPSERT,
                values,
            )

    def get_by_upc(
        self,
        upc: str,
    ) -> BookRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM books
                WHERE upc = ?
                """,
                (upc,),
            ).fetchone()

        return (
            BookRecord.model_validate(dict(row))
            if row
            else None
        )

    def list_books(
        self,
        limit: int = 50,
        offset: int = 0,
        category: str | None = None,
    ) -> list[BookRecord]:
        query = "SELECT * FROM books"
        parameters: list[object] = []

        if category:
            query += " WHERE category = ?"
            parameters.append(category)

        query += " ORDER BY title LIMIT ? OFFSET ?"

        parameters.extend([
            limit,
            offset,
        ])

        with self._connect() as connection:
            rows = connection.execute(
                query,
                parameters,
            ).fetchall()

        return [
            BookRecord.model_validate(dict(row))
            for row in rows
        ]

    def all_books(self) -> list[BookRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM books
                ORDER BY title
                """
            ).fetchall()

        return [
            BookRecord.model_validate(dict(row))
            for row in rows
        ]

    def count(self) -> int:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM books
                """
            ).fetchone()

        return int(row["count"])

    def stats(self) -> dict[str, object]:
        with self._connect() as connection:
            totals = connection.execute(
                """
                SELECT
                    COUNT(*) AS total_books,

                    SUM(
                        CASE
                            WHEN in_stock = 1
                            THEN 1
                            ELSE 0
                        END
                    ) AS in_stock_books,

                    COUNT(
                        DISTINCT category
                    ) AS category_count,

                    ROUND(
                        AVG(
                            CAST(price_gbp AS REAL)
                        ),
                        2
                    ) AS average_price_gbp

                FROM books
                """
            ).fetchone()

            categories = connection.execute(
                """
                SELECT
                    category,
                    COUNT(*) AS book_count

                FROM books

                GROUP BY category

                ORDER BY
                    book_count DESC,
                    category ASC
                """
            ).fetchall()

        return {
            "total_books": int(
                totals["total_books"] or 0
            ),
            "in_stock_books": int(
                totals["in_stock_books"] or 0
            ),
            "category_count": int(
                totals["category_count"] or 0
            ),
            "average_price_gbp": (
                totals["average_price_gbp"]
            ),
            "books_by_category": [
                dict(row)
                for row in categories
            ],
        }

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path
        )

        connection.row_factory = sqlite3.Row

        return connection

    @staticmethod
    def _book_values(
        book: BookRecord,
    ) -> tuple[object, ...]:
        return (
            book.upc,
            book.title,
            book.category,
            book.product_type,
            str(book.price_gbp),
            str(book.price_excl_tax_gbp),
            str(book.price_incl_tax_gbp),
            str(book.tax_gbp),
            book.availability_text,
            book.stock_count,
            int(book.in_stock),
            book.rating,
            book.review_count,
            book.description,
            str(book.image_url),
            str(book.source_url),
            book.scraped_at.isoformat(),
        )