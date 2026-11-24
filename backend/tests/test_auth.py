from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user, get_user_repository, require_admin
from app.auth.models import UserAccount, UserRole
from app.auth.security import (
    InvalidToken,
    JWTSettings,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.main import create_app


TEST_SECRET = "smartcampus-test-jwt-secret-with-32-bytes-minimum"


@pytest.fixture
def auth_client(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", TEST_SECRET)
    monkeypatch.setenv("JWT_ISSUER", "smartcampus-test-suite")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_TTL_SECONDS", "900")
    monkeypatch.setenv("AUTH_USE_IN_MEMORY", "true")
    get_user_repository.cache_clear()
    repository = get_user_repository()
    client = TestClient(create_app())
    yield client, repository
    client.close()
    repository.clear()
    get_user_repository.cache_clear()


def _register(client, **overrides):
    payload = {
        "email": "amina.benali@example.tn",
        "password": "Password123",
        "nom": "Ben Ali",
        "prenom": "Amina",
    }
    payload.update(overrides)
    return client.post("/api/v1/auth/register", json=payload)


def test_register_creates_candidate_and_returns_signed_bearer_token(auth_client):
    client, repository = auth_client
    response = _register(client, email="  AMINA.BENALI@Example.TN  ")

    assert response.status_code == 201
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["user"]["email"] == "amina.benali@example.tn"
    assert payload["user"]["role"] == "candidat"
    assert payload["conversation_rattachee"] is False
    assert "mot_de_passe_hash" not in payload["user"]
    assert "password" not in payload["user"]
    stored = repository.find_by_email("amina.benali@example.tn")
    assert stored is not None
    assert stored.role == UserRole.CANDIDAT
    assert stored.mot_de_passe_hash != "Password123"
    assert verify_password("Password123", stored.mot_de_passe_hash)
    assert response.status_code == 201

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {payload['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["id"] == payload["user"]["id"]


def test_register_rejects_duplicate_email_case_insensitively(auth_client):
    client, _repository = auth_client
    assert _register(client).status_code == 201

    response = _register(client, email="AMINA.BENALI@example.tn")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


@pytest.mark.parametrize(
    "overrides",
    [
        {"email": "not-an-email"},
        {"password": "short"},
        {"nom": "A"},
        {"prenom": " "},
        {"role": "admin"},
    ],
)
def test_register_rejects_invalid_or_privileged_payload(auth_client, overrides):
    client, _repository = auth_client

    response = _register(client, **overrides)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_login_issues_new_token_and_updates_last_login(auth_client):
    client, repository = auth_client
    registered = _register(client).json()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "AMINA.BENALI@example.tn", "password": "Password123"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"] != registered["access_token"]
    assert response.json()["user"]["role"] == "candidat"
    assert repository.find_by_email("amina.benali@example.tn").derniere_connexion is not None


def test_login_uses_same_error_for_unknown_email_and_wrong_password(auth_client):
    client, _repository = auth_client
    _register(client)

    wrong_password = client.post(
        "/api/v1/auth/login",
        json={"email": "amina.benali@example.tn", "password": "WrongPassword"},
    )
    unknown_email = client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@example.tn", "password": "WrongPassword"},
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_me_rejects_missing_invalid_and_tampered_tokens(auth_client):
    client, _repository = auth_client
    registered = _register(client).json()

    assert client.get("/api/v1/auth/me").status_code == 401
    invalid = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"}
    )
    token = registered["access_token"]
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    signature = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered}"}
    )
    assert invalid.status_code == signature.status_code == 401


def test_expired_jwt_is_rejected():
    settings = JWTSettings(secret=TEST_SECRET.encode(), issuer="tests", ttl_seconds=60)
    now = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
    user = UserAccount(
        id=uuid4(),
        nom="Admin",
        prenom="Test",
        email="admin@example.tn",
        mot_de_passe_hash="unused",
        role=UserRole.ADMIN,
        langue_preferee="fr",
        est_actif=True,
        derniere_connexion=None,
        cree_le=now,
        modifie_le=now,
    )
    token = create_access_token(user, settings, now=now)

    with pytest.raises(InvalidToken, match="Expired"):
        decode_access_token(token, settings, now=now + timedelta(seconds=60))


def test_jwt_requires_configured_strong_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "too-short")
    with pytest.raises(RuntimeError, match="at least 32 bytes"):
        JWTSettings.from_environment()

    monkeypatch.setenv("JWT_SECRET", "replace-with-a-long-but-insecure-placeholder")
    with pytest.raises(RuntimeError, match="at least 32 bytes"):
        JWTSettings.from_environment()


def test_auth_refuses_to_start_without_database_or_explicit_test_mode(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", TEST_SECRET)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("AUTH_USE_IN_MEMORY", "false")
    get_user_repository.cache_clear()
    with TestClient(create_app()) as client:
        response = _register(client)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
    get_user_repository.cache_clear()


def test_role_dependency_allows_admin_and_forbids_candidate(auth_client):
    _client, repository = auth_client
    now = datetime.now(timezone.utc)
    admin = repository.add(
        UserAccount(
            id=uuid4(),
            nom="Admin",
            prenom="A",
            email="admin@example.tn",
            mot_de_passe_hash=hash_password("AdminPass123"),
            role=UserRole.ADMIN,
            langue_preferee="fr",
            est_actif=True,
            derniere_connexion=None,
            cree_le=now,
            modifie_le=now,
        )
    )
    candidate = repository.find_by_email("amina.benali@example.tn")
    if candidate is None:
        candidate_response = _register(_client)
        candidate = repository.find_by_email(candidate_response.json()["user"]["email"])
    assert candidate is not None

    protected_app = FastAPI()

    @protected_app.get("/admin-only")
    def admin_only(user: UserAccount = Depends(require_admin)):
        return {"role": user.role.value}

    protected = TestClient(protected_app)
    admin_token = create_access_token(admin)
    candidate_token = create_access_token(candidate)

    assert protected.get(
        "/admin-only", headers={"Authorization": f"Bearer {admin_token}"}
    ).status_code == 200
    denied = protected.get(
        "/admin-only", headers={"Authorization": f"Bearer {candidate_token}"}
    )
    assert denied.status_code == 403


def test_password_hash_uses_salt_and_constant_time_verification():
    first = hash_password("Password123")
    second = hash_password("Password123")

    assert first != second
    assert verify_password("Password123", first)
    assert not verify_password("wrong", first)
    assert not verify_password("Password123", "not-a-hash")
