"""Application configuration loaded from environment variables via pydantic-settings.

Single Settings instance exported as `settings`. All other modules import from here.
"""

import os

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration for the Candle application."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database — optional so the validator can build it from PG* vars as fallback
    candle_db_url: str = ""
    candle_db_url_test: str = ""

    # Exchanges (all optional — public OHLCV requires no keys)
    binance_api_key: str = ""
    binance_api_secret: str = ""
    kraken_api_key: str = ""
    kraken_api_secret: str = ""
    coinbase_api_key: str = ""
    coinbase_api_secret: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Scheduler
    fetch_interval_minutes: int = 60
    screen_interval_minutes: int = 60
    default_timeframe: str = "4h"
    alert_dedup_hours: int = 4

    # App
    env: str = "development"

    @model_validator(mode="after")
    def resolve_db_url(self) -> "Settings":
        """Build candle_db_url from Railway's PG* variables if not set directly."""
        if not self.candle_db_url:
            host = os.environ.get("PGHOST", "")
            port = os.environ.get("PGPORT", "5432")
            user = os.environ.get("PGUSER", "")
            password = os.environ.get("PGPASSWORD", "")
            database = os.environ.get("PGDATABASE", "")
            if host and user and password and database:
                self.candle_db_url = (
                    f"postgresql://{user}:{password}@{host}:{port}/{database}"
                )
            else:
                raise ValueError(
                    "Database URL not configured: set CANDLE_DB_URL or the "
                    "PGHOST/PGPORT/PGUSER/PGPASSWORD/PGDATABASE variables."
                )
        return self

    @property
    def is_production(self) -> bool:
        """Return True when running in production environment."""
        return self.env == "production"


settings = Settings()
