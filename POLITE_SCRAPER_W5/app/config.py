from functools import lru_cache
from pathlib import Path
from urllib.parse import urljoin

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SCRAPER_",
        extra="ignore",
    )

    base_url: HttpUrl = "https://books.toscrape.com/"
    start_path: str = "catalogue/page-1.html"

    user_agent: str = (
        "StudentPoliteScraper/1.0 "
        "(educational project; contact: your-email@example.com)"
    )

    min_delay_seconds: float = Field(default=1.5, ge=1.0)
    timeout_seconds: float = Field(default=15.0, gt=0)
    max_retries: int = Field(default=3, ge=0, le=8)
    backoff_base_seconds: float = Field(default=1.0, gt=0)

    default_max_books: int = Field(default=30, ge=1, le=1000)
    max_consecutive_failures: int = Field(default=5, ge=1, le=50)

    database_path: Path = Path("data/books.db")
    structured_jsonl_path: Path = Path("data/processed/books.jsonl")
    rag_jsonl_path: Path = Path("data/processed/rag_corpus.jsonl")
    csv_path: Path = Path("data/processed/books.csv")

    log_level: str = "INFO"
    log_path: Path = Path("logs/scraper.log")

    @field_validator("user_agent")
    @classmethod
    def require_identifying_user_agent(cls, value: str) -> str:
        lowered = value.lower()

        if "your-email@example.com" in lowered or "contact" not in lowered:
            raise ValueError(
                "Set SCRAPER_USER_AGENT to an identifying value "
                "with a real contact address."
            )

        return value

    @property
    def start_url(self) -> str:
        return urljoin(str(self.base_url), self.start_path)

    @property
    def robots_url(self) -> str:
        return urljoin(str(self.base_url), "/robots.txt")

    @property
    def robot_agent_token(self) -> str:
        return self.user_agent.split("/", maxsplit=1)[0].strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()