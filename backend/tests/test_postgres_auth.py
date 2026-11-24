"""Persistence integration test; requires TEST_DATABASE_URL and SA-17 migration."""

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_user_repository
from app.auth.postgres_repository import PostgresUserRepository
from app.main import create_app


TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "").strip()
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="Set TEST_DATABASE_URL to a disposable PostgreSQL database with SA-17 migration applied",
)


def test_registration_survives_new_repository_and_authenticates_against_sql(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("AUTH_USE_IN_MEMORY", "false")
    monkeypatch.setenv("JWT_SECRET", "test-only-secret-with-at-least-32-bytes")
    monkeypatch.setenv("JWT_ISSUER", "smartcampus-postgres-tests")
    get_user_repository.cache_clear()

    repository = PostgresUserRepository(TEST_DATABASE_URL)
    email = f"sa28-{uuid4()}@example.test"
    try:
        with TestClient(create_app()) as client:
            registration = client.post(
                "/api/v1/auth/register",
                json={"nom": "Test", "prenom": "SQL", "email": email, "password": "Password123"},
            )
            assert registration.status_code == 201
            payload = registration.json()

            duplicate = client.post(
                "/api/v1/auth/register",
                json={"nom": "Autre", "prenom": "Test", "email": email.upper(), "password": "Password123"},
            )
            assert duplicate.status_code == 409

            # A distinct repository instance proves the account was read from SQL,
            # not retained in the request process's in-memory index.
            persisted = PostgresUserRepository(TEST_DATABASE_URL).find_by_email(email)
            assert persisted is not None
            assert str(persisted.id) == payload["user"]["id"]
            assert persisted.mot_de_passe_hash != "Password123"

            login = client.post(
                "/api/v1/auth/login", json={"email": email, "password": "Password123"}
            )
            assert login.status_code == 200
            profile = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {login.json()['access_token']}"},
            )
            assert profile.status_code == 200
            assert profile.json()["id"] == payload["user"]["id"]
            assert PostgresUserRepository(TEST_DATABASE_URL).find_by_email(email).derniere_connexion
    finally:
        persisted = repository.find_by_email(email)
        if persisted:
            repository.delete(persisted.id)
        get_user_repository.cache_clear()
