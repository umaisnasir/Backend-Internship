import logging
import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import httpx

from app.config import Settings
from app.exceptions import (
    ExternalDomainError,
    FetchError,
    RobotsDeniedError,
)
from app.rate_limiter import PoliteRateLimiter
from app.robots import RobotsPolicy


logger = logging.getLogger(__name__)


RETRYABLE_STATUS_CODES = {
    429,
    500,
    502,
    503,
    504,
}


class PoliteHttpClient:
    def __init__(
        self,
        settings: Settings,
        client: httpx.Client,
        robots: RobotsPolicy,
        rate_limiter: PoliteRateLimiter,
    ) -> None:
        self.settings = settings
        self.client = client
        self.robots = robots
        self.rate_limiter = rate_limiter

        self._allowed_host = urlparse(
            str(settings.base_url)
        ).netloc.lower()

    def get_text(self, url: str) -> str:
        self._validate_domain(url)

        if not self.robots.can_fetch(url):
            raise RobotsDeniedError(
                f"robots.txt disallows: {url}"
            )

        last_error: Exception | None = None

        for attempt in range(
            self.settings.max_retries + 1
        ):
            self.rate_limiter.wait()

            try:
                logger.info(
                    "GET %s (attempt %s)",
                    url,
                    attempt + 1,
                )

                response = self.client.get(url)

                self._validate_domain(
                    str(response.url)
                )

            except httpx.HTTPError as exc:
                last_error = exc

                if (
                    attempt
                    == self.settings.max_retries
                ):
                    break

                self._sleep_before_retry(
                    attempt,
                    None,
                )

                continue

            if (
                response.status_code
                in RETRYABLE_STATUS_CODES
            ):
                last_error = FetchError(
                    "Retryable HTTP "
                    f"{response.status_code} "
                    f"while fetching {url}"
                )

                if (
                    attempt
                    == self.settings.max_retries
                ):
                    break

                self._sleep_before_retry(
                    attempt,
                    response,
                )

                continue

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise FetchError(
                    "Non-retryable HTTP "
                    f"{response.status_code} "
                    f"while fetching {url}"
                ) from exc

            return response.text

        raise FetchError(
            f"Failed to fetch {url} after retries"
        ) from last_error

    def _validate_domain(self, url: str) -> None:
        target_host = urlparse(
            url
        ).netloc.lower()

        if target_host != self._allowed_host:
            raise ExternalDomainError(
                "Refusing to leave "
                f"{self._allowed_host}; "
                f"received {target_host}"
            )

    def _sleep_before_retry(
        self,
        attempt: int,
        response: httpx.Response | None,
    ) -> None:
        retry_after = self._retry_after_seconds(
            response
        )

        delay = retry_after or (
            self.settings.backoff_base_seconds
            * (2**attempt)
        )

        logger.warning(
            "Retrying after %.2f seconds",
            delay,
        )

        time.sleep(delay)

    @staticmethod
    def _retry_after_seconds(
        response: httpx.Response | None,
    ) -> float | None:
        if response is None:
            return None

        value = response.headers.get(
            "Retry-After"
        )

        if not value:
            return None

        if value.isdigit():
            return float(value)

        try:
            retry_at = parsedate_to_datetime(
                value
            )

            seconds = (
                retry_at - datetime.now(UTC)
            ).total_seconds()

            return max(0.0, seconds)

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return None