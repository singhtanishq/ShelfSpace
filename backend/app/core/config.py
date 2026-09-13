"""Application configuration loaded from environment variables / .env file."""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Application
    APP_NAME: str = "ShelfSpace"
    ENVIRONMENT: str = "development"  # development | testing | production
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "mysql+pymysql://root:@localhost:3306/book_shop"
    TEST_DATABASE_URL: str = ""

    # Security
    SECRET_KEY: str = "change-me-to-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS / URLs
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    FRONTEND_URL: str = "http://localhost:5173"

    # Email
    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "ShelfSpace <no-reply@shelfspace.local>"
    EMAIL_WORKER_ENABLED: bool = True

    # Store defaults (runtime-editable via admin settings; used as fallbacks)
    DEFAULT_CURRENCY: str = "INR"
    DEFAULT_TAX_PERCENT: float = 0.0
    DEFAULT_SHIPPING_FEE: float = 0.0
    DEFAULT_FREE_SHIPPING_THRESHOLD: float = 0.0
    DEFAULT_RETURN_WINDOW_DAYS: int = 14
    DEFAULT_LOW_STOCK_THRESHOLD: int = 5

    # Media
    MEDIA_DIR: str = "media"

    # Pagination
    DEFAULT_PAGE_SIZE: int = 12
    MAX_PAGE_SIZE: int = 60

    # Rate limiting (requests per window, per client)
    LOGIN_RATE_LIMIT: int = 10
    LOGIN_RATE_WINDOW_SECONDS: int = 60

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    def ensure_media_dirs(self) -> None:
        """Create media sub-directories if missing."""
        import os

        for sub in ("covers", "invoices"):
            os.makedirs(os.path.join(self.MEDIA_DIR, sub), exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
