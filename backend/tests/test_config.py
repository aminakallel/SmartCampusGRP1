import pytest
from pydantic import ValidationError
from sqlalchemy.engine import make_url

from app.core.config import Settings


def test_settings_load_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("APP_NAME", "Config test API")
    settings = Settings(_env_file=None)
    assert settings.app_name == "Config test API"


def test_default_database_port_does_not_target_odoo(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    url = make_url(Settings(_env_file=None).database_url)
    assert url.host == "127.0.0.1"
    assert url.port == 55432


def test_invalid_database_url_rejects_odoo_port_without_echoing_credentials() -> None:
    secret = "do-not-show-this"
    unsafe_url = f"postgresql+psycopg://student:{secret}@127.0.0.1:5432/smartcampus"
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, database_url=unsafe_url)
    assert "5432" in str(error.value)
    assert secret not in str(error.value)


def test_compose_database_hostname_can_use_internal_postgres_port() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql+psycopg://smartcampus:placeholder@db:5432/smartcampus",
    )
    assert make_url(settings.database_url).host == "db"


def test_cors_origins_accept_explicit_http_origins() -> None:
    settings = Settings(_env_file=None, cors_origins="http://localhost:3000, https://campus.example.test/")
    assert settings.allowed_origins == ["http://localhost:3000", "https://campus.example.test"]


@pytest.mark.parametrize(
    "origin",
    ["*", "null", "https://site.example/path", "ftp://site.example", "https://site.example:bad"],
)
def test_cors_origins_reject_wildcard_or_non_origin_values(origin: str) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, cors_origins=origin)


def test_settings_load_dotenv_file(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "APP_NAME=Loaded from dotenv\n"
        "DATABASE_URL=postgresql+psycopg://demo:placeholder@127.0.0.1:55432/smartcampus\n",
        encoding="utf-8",
    )
    settings = Settings(_env_file=env_file)
    assert settings.app_name == "Loaded from dotenv"
    assert make_url(settings.database_url).port == 55432
