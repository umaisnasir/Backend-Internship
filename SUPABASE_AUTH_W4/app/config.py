from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_FILE)


@dataclass(frozen=True)
class Settings:
    """
    Environment configuration required by the application.
    """

    supabase_url: str
    supabase_key: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Load and validate the required environment variables.

    The values are cached because configuration does not need
    to be read repeatedly during the same server process.
    """

    supabase_url = (
        os.getenv("SUPABASE_URL") or ""
    ).strip()

    supabase_key = (
        os.getenv("SUPABASE_KEY") or ""
    ).strip()

    missing_variables: list[str] = []

    if not supabase_url:
        missing_variables.append("SUPABASE_URL")

    if not supabase_key:
        missing_variables.append("SUPABASE_KEY")

    if missing_variables:
        missing_text = ", ".join(missing_variables)

        raise RuntimeError(
            "Missing required environment variables: "
            f"{missing_text}. Copy .env.example to .env "
            "and add your own Supabase project values."
        )

    if (
        "replace_with" in supabase_url
        or "replace_with" in supabase_key
    ):
        raise RuntimeError(
            "Placeholder Supabase values detected. "
            "Replace them inside SUPABASE_AUTH_W4/.env."
        )

    return Settings(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
    )