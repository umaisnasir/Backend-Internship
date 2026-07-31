from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Usage Billing API"
    app_env: str = "development"

    database_url: str = "sqlite:///./billing.db"

    base_url: str = "http://localhost:8000"

    stripe_secret_key: str = "sk_test_placeholder"
    stripe_webhook_secret: str = "whsec_placeholder"
    stripe_pro_price_id: str = "price_placeholder"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()