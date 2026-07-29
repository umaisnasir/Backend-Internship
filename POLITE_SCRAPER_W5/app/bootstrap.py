import logging
from pathlib import Path

import httpx

from app.config import Settings
from app.http_client import PoliteHttpClient
from app.rate_limiter import PoliteRateLimiter
from app.robots import RobotsPolicy
from app.service import ScraperService
from app.storage import SQLiteBookRepository


def configure_logging(
    level: str,
    log_path: Path,
) -> None:
    log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    formatter = logging.Formatter(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    )

    root_logger = logging.getLogger()

    root_logger.setLevel(
        getattr(
            logging,
            level.upper(),
            logging.INFO,
        )
    )

    root_logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = logging.FileHandler(
        log_path,
        encoding="utf-8",
    )

    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


def build_httpx_client(
    settings: Settings,
) -> httpx.Client:
    timeout = httpx.Timeout(
        settings.timeout_seconds
    )

    limits = httpx.Limits(
        max_connections=1,
        max_keepalive_connections=1,
    )

    return httpx.Client(
        headers={
            "User-Agent": settings.user_agent,
            "Accept": (
                "text/html,"
                "application/xhtml+xml"
            ),
            "Accept-Language": (
                "en-GB,en;q=0.9"
            ),
        },
        timeout=timeout,
        limits=limits,
        follow_redirects=True,
    )


def build_scraper_service(
    settings: Settings,
    client: httpx.Client,
) -> tuple[ScraperService, RobotsPolicy]:
    rate_limiter = PoliteRateLimiter(
        settings.min_delay_seconds
    )

    # Record the robots.txt request so the first
    # page fetch also respects the delay.
    rate_limiter.wait()

    robots = RobotsPolicy(settings)
    robots.load(client)

    rate_limiter.delay_seconds = (
        robots.effective_delay_seconds()
    )

    fetcher = PoliteHttpClient(
        settings=settings,
        client=client,
        robots=robots,
        rate_limiter=rate_limiter,
    )

    repository = SQLiteBookRepository(
        settings.database_path
    )

    service = ScraperService(
        settings=settings,
        fetcher=fetcher,
        repository=repository,
    )

    return service, robots