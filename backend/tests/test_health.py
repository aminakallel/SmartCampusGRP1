from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
import pytest

from app.core.config import Settings
from app.main import app, create_app
from app.api.routes import health as health_routes

client = TestClient(app)


def test_health_returns_200() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_route_returns_404() -> None:
    response = client.get("/route-not-defined")
    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "NOT_FOUND", "message": "Not Found", "details": {}}
    }


def test_docs_are_available() -> None:
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_json_is_available_and_lists_only_implemented_routes() -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert set(response.json()["paths"]) == {"/health", "/health/db"}


def test_health_rejects_wrong_method() -> None:
    response = client.post("/health")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"


@pytest.mark.parametrize(
    ("status_code", "error_code"),
    [
        (400, "BAD_REQUEST"),
        (401, "UNAUTHORIZED"),
        (403, "FORBIDDEN"),
        (503, "SERVICE_UNAVAILABLE"),
    ],
)
def test_http_errors_use_the_shared_envelope(status_code: int, error_code: str) -> None:
    error_app = create_app(Settings(_env_file=None))

    @error_app.get("/test-http-error")
    def raise_http_error() -> None:
        raise HTTPException(status_code=status_code, detail="Safe public message")

    response = TestClient(error_app).get("/test-http-error")
    assert response.status_code == status_code
    assert response.json() == {
        "error": {
            "code": error_code,
            "message": "Safe public message",
            "details": {},
        }
    }


def test_validation_error_uses_envelope_without_echoing_input() -> None:
    validation_app = create_app(Settings(_env_file=None))

    @validation_app.post("/test-validation")
    def validate_payload(payload: dict[str, int]) -> dict[str, int]:
        return payload

    secret_input = "never-echo-this-input"
    response = TestClient(validation_app).post(
        "/test-validation", json={"score": "invalid", "password": secret_input}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["message"] == "Request validation failed"
    assert "details" in response.json()["error"]
    assert secret_input not in response.text


def test_unexpected_error_returns_sanitized_500(caplog) -> None:
    caplog.clear()
    error_app = FastAPI()
    error_app.add_exception_handler(Exception, app.exception_handlers[Exception])

    @error_app.get("/test-error")
    def raise_unexpected_error() -> None:
        raise RuntimeError("private diagnostic")

    response = TestClient(error_app, raise_server_exceptions=False).get("/test-error")
    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Internal server error",
            "details": {},
        }
    }
    assert "private diagnostic" not in response.text
    assert "private diagnostic" not in caplog.text


def test_cors_allows_configured_origin_and_rejects_unknown_origin() -> None:
    cors_app = create_app(Settings(_env_file=None, cors_origins="http://localhost:3000"))
    cors_client = TestClient(cors_app)
    allowed = cors_client.options(
        "/health",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )
    blocked = cors_client.options(
        "/health",
        headers={"Origin": "https://unknown.example", "Access-Control-Request-Method": "GET"},
    )
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert blocked.status_code == 400
    assert "access-control-allow-origin" not in blocked.headers


def test_cors_is_disabled_without_configured_origins() -> None:
    cors_app = create_app(Settings(_env_file=None))
    response = TestClient(cors_app).get("/health", headers={"Origin": "https://client.example"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_database_health_error_does_not_return_connection_details(monkeypatch, caplog) -> None:
    secret = "do-not-return-this"
    caplog.clear()

    def fail_to_connect():
        raise OperationalError("SELECT 1", {}, RuntimeError(f"password={secret}"))

    monkeypatch.setattr(health_routes.engine, "connect", fail_to_connect)
    response = client.get("/health/db")
    assert response.status_code == 503
    assert secret not in response.text
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert secret not in caplog.text


def test_database_health_returns_200_when_database_responds(monkeypatch) -> None:
    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, _statement):
            return 1

    monkeypatch.setattr(health_routes.engine, "connect", lambda: FakeConnection())
    response = client.get("/health/db")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "reachable"}


def test_database_health_returns_503_when_database_fails(monkeypatch) -> None:
    def fail_to_connect():
        raise OperationalError("SELECT 1", {}, RuntimeError("connection refused"))

    monkeypatch.setattr(health_routes.engine, "connect", fail_to_connect)
    response = client.get("/health/db")
    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "SERVICE_UNAVAILABLE",
            "message": "Database unavailable",
            "details": {},
        }
    }
