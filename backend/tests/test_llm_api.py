
import asyncio

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.llm.providers import LLMProvider
from app.llm.router import get_llm_service
from app.llm.service import LLMService


@pytest.fixture
def client():
    get_llm_service.cache_clear()

    with TestClient(app) as test_client:
        yield test_client

    get_llm_service.cache_clear()


class SlowProvider(LLMProvider):
    """Provider simulé qui prend trop de temps pour répondre."""

    async def generate(self, prompt: str) -> str:
        await asyncio.sleep(0.1)
        return "Réponse tardive"


class FailingProvider(LLMProvider):
    """Provider simulé qui retourne une erreur."""

    async def generate(self, prompt: str) -> str:
        raise RuntimeError("Provider connection failed")


def test_generate_response_success(client):
    response = client.post(
        "/api/v1/llm/generate",
        json={"prompt": "Bonjour SmartCampus"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "response": "Mock response: Bonjour SmartCampus"
    }


def test_generate_response_rejects_empty_prompt(client):
    response = client.post(
        "/api/v1/llm/generate",
        json={"prompt": ""},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_generate_response_rejects_long_prompt(client):
    response = client.post(
        "/api/v1/llm/generate",
        json={"prompt": "A" * 4001},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_generate_response_timeout(client):
    app.dependency_overrides[get_llm_service] = lambda: LLMService(
        provider=SlowProvider(),
        timeout_seconds=0.01,
    )

    try:
        response = client.post(
            "/api/v1/llm/generate",
            json={"prompt": "Bonjour"},
        )

        assert response.status_code == 504
        assert response.json()["error"]["code"] == "LLM_TIMEOUT"

    finally:
        app.dependency_overrides.pop(get_llm_service, None)


def test_generate_response_provider_error(client):
    app.dependency_overrides[get_llm_service] = lambda: LLMService(
        provider=FailingProvider(),
        timeout_seconds=1,
    )

    try:
        response = client.post(
            "/api/v1/llm/generate",
            json={"prompt": "Bonjour"},
        )

        assert response.status_code == 502
        assert response.json()["error"]["code"] == "LLM_PROVIDER_ERROR"

    finally:
        app.dependency_overrides.pop(get_llm_service, None)
