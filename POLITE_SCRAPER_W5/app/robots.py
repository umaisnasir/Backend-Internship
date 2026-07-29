from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from app.config import Settings
from app.exceptions import RobotsPolicyError


class RobotsPolicy:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._parser = RobotFileParser()
        self._loaded = False
        self._allow_all = False
        self._disallow_all = False

        self._allowed_host = urlparse(
            str(settings.base_url)
        ).netloc.lower()

    def load(self, client: httpx.Client) -> None:
        try:
            response = client.get(
                self.settings.robots_url
            )
        except httpx.HTTPError as exc:
            raise RobotsPolicyError(
                "Could not retrieve robots.txt. "
                "The scraper stops rather than guessing."
            ) from exc

        response_host = urlparse(
            str(response.url)
        ).netloc.lower()

        if response_host != self._allowed_host:
            raise RobotsPolicyError(
                "robots.txt redirected outside "
                f"{self._allowed_host}; refusing to continue."
            )

        if response.status_code == 200:
            self.load_from_text(response.text)
            return

        if response.status_code == 404:
            self._allow_all = True
            self._loaded = True
            return

        if response.status_code in {401, 403}:
            self._disallow_all = True
            self._loaded = True
            return

        raise RobotsPolicyError(
            "robots.txt returned HTTP "
            f"{response.status_code}; refusing to scrape."
        )

    def load_from_text(self, text: str) -> None:
        self._parser = RobotFileParser()

        self._parser.set_url(
            self.settings.robots_url
        )

        self._parser.parse(
            text.splitlines()
        )

        self._loaded = True
        self._allow_all = False
        self._disallow_all = False

    def can_fetch(self, url: str) -> bool:
        self._require_loaded()

        if self._disallow_all:
            return False

        if self._allow_all:
            return True

        return self._parser.can_fetch(
            self.settings.robot_agent_token,
            url,
        )

    def effective_delay_seconds(self) -> float:
        self._require_loaded()

        if self._allow_all or self._disallow_all:
            return self.settings.min_delay_seconds

        crawl_delay = self._parser.crawl_delay(
            self.settings.robot_agent_token
        )

        if crawl_delay is None:
            crawl_delay = self._parser.crawl_delay(
                "*"
            )

        request_rate = self._parser.request_rate(
            self.settings.robot_agent_token
        )

        if request_rate is None:
            request_rate = self._parser.request_rate(
                "*"
            )

        rate_delay = 0.0

        if request_rate and request_rate.requests > 0:
            rate_delay = (
                request_rate.seconds
                / request_rate.requests
            )

        return max(
            self.settings.min_delay_seconds,
            float(crawl_delay or 0),
            float(rate_delay),
        )

    def _require_loaded(self) -> None:
        if not self._loaded:
            raise RobotsPolicyError(
                "robots.txt policy has not been loaded yet."
            )