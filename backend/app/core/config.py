"""
Application configuration using Pydantic Settings.
"""
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Dumplin API"

    # MongoDB Configuration
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "dumplin"

    # API Key for internal authentication
    API_KEY: Optional[str] = None

    # RevenueCat Configuration
    REVENUECAT_API_KEY: Optional[str] = None  # Secret API key for server-side calls
    REVENUECAT_WEBHOOK_SECRET: Optional[str] = None  # Webhook signing secret

    # Subscription Configuration
    FREE_TIER_WEEKLY_MESSAGE_LIMIT: int = 20

    # Week start calculation (ISO: Monday=0, Sunday=6)
    WEEK_START_DAY: int = 0  # Monday

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
