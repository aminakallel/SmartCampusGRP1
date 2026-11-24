"""Application settings loaded from the process environment or a local .env."""

from functools import lru_cache
from urllib.parse import urlsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


class Settings(BaseSettings):
    app_name: str = "SmartCampus AI API"
    app_version: str = "0.1.0"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://smartcampus:change-me-local@127.0.0.1:55432/smartcampus"
    log_level: str = "INFO"
    cors_origins: str = ""
    llm_timeout_seconds: float = Field(default=30.0, gt=0, le=120)
    agents_base_url: str = "http://agents:8001"
    llm_provider: str = "mock"
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        try:
            url = make_url(value)
            port = url.port
        except (ArgumentError, ValueError):
            raise ValueError("DATABASE_URL must be a valid PostgreSQL URL") from None

        if url.drivername != "postgresql+psycopg" or not url.host or not url.database:
            raise ValueError("DATABASE_URL must identify a PostgreSQL database using psycopg")

        if url.host.lower() in {"localhost", "127.0.0.1", "::1"} and port in (None, 5432):
            raise ValueError("Local DATABASE_URL must not use port 5432, reserved for PostgreSQL Odoo")
        return value

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: str) -> str:
        origins = [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
        for origin in origins:
            parsed = urlsplit(origin)
            try:
                parsed.port
            except ValueError:
                raise ValueError("CORS_ORIGINS contains an invalid port") from None
            if (
                origin == "*"
                or parsed.scheme not in {"http", "https"}
                or not parsed.netloc
                or not parsed.hostname
                or parsed.path
                or parsed.query
                or parsed.fragment
                or parsed.username
                or parsed.password
            ):
                raise ValueError("CORS_ORIGINS must contain explicit HTTP(S) origins; wildcard is forbidden")
        return ",".join(dict.fromkeys(origins))

    @property
    def allowed_origins(self) -> list[str]:
        return [origin for origin in self.cors_origins.split(",") if origin]


@lru_cache
def get_settings() -> Settings:
    return Settings()
