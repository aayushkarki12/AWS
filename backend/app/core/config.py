"""Centralized application configuration loaded from environment variables."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "AMS API"
    ENVIRONMENT: str = Field(default="development")  # development | staging | production
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://ams_user:ams_password@localhost:5432/ams_db"
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT / Auth
    JWT_SECRET_KEY: str = Field(default="CHANGE_ME_IN_PRODUCTION")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER_ME: int = 30

    # Account lockout / brute force protection
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_MINUTES: int = 15

    # Cookies
    COOKIE_DOMAIN: str | None = None
    COOKIE_SECURE: bool = True
    COOKIE_SAMESITE: str = "lax"
    ACCESS_TOKEN_COOKIE_NAME: str = "ams_access_token"
    REFRESH_TOKEN_COOKIE_NAME: str = "ams_refresh_token"
    CSRF_COOKIE_NAME: str = "ams_csrf_token"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # Rate limiting
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_DEFAULT: str = "100/minute"

    # Password policy
    PASSWORD_MIN_LENGTH: int = 8

    # Logging
    LOG_LEVEL: str = "INFO"

    # File uploads
    UPLOAD_DIR: str = "uploads"
    UPLOAD_URL_PREFIX: str = "/uploads"
    MAX_AVATAR_SIZE_MB: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
