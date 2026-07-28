from pathlib import Path

from app.config import Settings
from app.robots import RobotsPolicy


def make_settings(
    tmp_path: Path,
) -> Settings:
    return Settings(
        user_agent=(
            "UnitTestBot/1.0 "
            "(contact: test@example.com)"
        ),
        database_path=(
            tmp_path / "books.db"
        ),
    )


def test_robots_policy_blocks_disallowed_path(
    tmp_path,
) -> None:
    settings = make_settings(tmp_path)

    policy = RobotsPolicy(settings)

    policy.load_from_text(
        """
        User-agent: UnitTestBot
        Disallow: /private/
        Crawl-delay: 4
        """
    )

    assert policy.can_fetch(
        "https://books.toscrape.com/"
        "catalogue/page-1.html"
    ) is True

    assert policy.can_fetch(
        "https://books.toscrape.com/"
        "private/secret"
    ) is False

    assert (
        policy.effective_delay_seconds()
        == 4.0
    )


def test_minimum_delay_wins_when_robots_has_no_delay(
    tmp_path,
) -> None:
    settings = make_settings(tmp_path)

    policy = RobotsPolicy(settings)

    policy.load_from_text(
        "User-agent: *\nDisallow:"
    )

    assert (
        policy.effective_delay_seconds()
        == settings.min_delay_seconds
    )