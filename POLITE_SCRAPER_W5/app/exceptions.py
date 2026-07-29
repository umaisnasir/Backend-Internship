class ScraperError(Exception):
    """Base exception for scraper failures."""


class RobotsPolicyError(ScraperError):
    """Raised when robots.txt cannot be checked safely."""


class RobotsDeniedError(ScraperError):
    """Raised when robots.txt disallows a URL."""


class FetchError(ScraperError):
    """Raised when a page cannot be fetched after retries."""


class ParseError(ScraperError):
    """Raised when required fields cannot be extracted from a page."""


class ExternalDomainError(ScraperError):
    """Raised when the scraper tries to leave the configured host."""