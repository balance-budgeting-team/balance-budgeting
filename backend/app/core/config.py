"""Backend settings read from environment variables.

Defaults match the local development database in ``compose.yaml``. They are
local-only development values, not real credentials.
"""

import os
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

DEFAULT_DATABASE_URL = "postgresql+psycopg://balance:balance@localhost:5432/balance"
DEFAULT_TIMEZONE = "America/Indiana/Indianapolis"
# Expo / React Native web dev servers. Native mobile requests do not use CORS.
DEFAULT_CORS_ORIGINS = "http://localhost:8081,http://localhost:19006"


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    database_url: str = field(
        default_factory=lambda: os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
    )
    timezone: ZoneInfo = field(
        default_factory=lambda: ZoneInfo(
            os.environ.get("BALANCE_TIMEZONE", DEFAULT_TIMEZONE)
        )
    )
    cors_origins: list[str] = field(
        default_factory=lambda: _split_csv(
            os.environ.get("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
        )
    )
    # Prototype has no sign-in yet, so every request acts as this demo user.
    demo_user_id: int = 1


settings = Settings()
