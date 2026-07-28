import argparse
import json
import sys

from pydantic import ValidationError

from app.bootstrap import (
    build_httpx_client,
    build_scraper_service,
    configure_logging,
)
from app.config import get_settings
from app.exceptions import ScraperError
from app.storage import SQLiteBookRepository


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="polite-scraper",
        description=(
            "A robots-aware, rate-limited scraper "
            "for Books to Scrape."
        ),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    scrape_parser = subparsers.add_parser(
        "scrape",
        help="Scrape and store books",
    )

    scrape_parser.add_argument(
        "--max-books",
        type=int,
        default=None,
        help=(
            "Maximum number of book "
            "detail pages to save"
        ),
    )

    subparsers.add_parser(
        "check-robots",
        help="Inspect robots.txt permission",
    )

    subparsers.add_parser(
        "stats",
        help="Show SQLite dataset statistics",
    )

    subparsers.add_parser(
        "export",
        help="Rebuild JSONL and CSV from SQLite",
    )

    return parser


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    try:
        settings = get_settings()

        configure_logging(
            settings.log_level,
            settings.log_path,
        )

    except ValidationError as exc:
        print(
            "Configuration error:",
            file=sys.stderr,
        )

        print(
            exc,
            file=sys.stderr,
        )

        return 2

    repository = SQLiteBookRepository(
        settings.database_path
    )

    repository.initialize()

    try:
        if args.command == "stats":
            print(
                json.dumps(
                    repository.stats(),
                    indent=2,
                )
            )

            return 0

        with build_httpx_client(
            settings
        ) as client:
            service, robots = (
                build_scraper_service(
                    settings,
                    client,
                )
            )

            if args.command == "check-robots":
                result = {
                    "robots_url": (
                        settings.robots_url
                    ),
                    "start_url": (
                        settings.start_url
                    ),
                    "allowed": robots.can_fetch(
                        settings.start_url
                    ),
                    "effective_delay_seconds": (
                        robots
                        .effective_delay_seconds()
                    ),
                    "user_agent": (
                        settings.user_agent
                    ),
                }

                print(
                    json.dumps(
                        result,
                        indent=2,
                    )
                )

                return (
                    0
                    if result["allowed"]
                    else 3
                )

            if args.command == "export":
                service.export_all()

                print(
                    "Exports rebuilt from SQLite."
                )

                return 0

            if args.command == "scrape":
                max_books = (
                    args.max_books
                    or settings.default_max_books
                )

                summary = service.scrape(
                    max_books=max_books
                )

                print(
                    summary.model_dump_json(
                        indent=2
                    )
                )

                return 0

    except ScraperError as exc:
        print(
            f"Scraper error: {exc}",
            file=sys.stderr,
        )

        return 1

    except ValueError as exc:
        print(
            f"Input error: {exc}",
            file=sys.stderr,
        )

        return 2

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())