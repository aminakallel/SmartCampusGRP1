
import asyncio

import pytest
import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.llm.providers import LLMProvider
from app.llm.router import get_llm_service
from app.llm.service import LLMService
from app.llm.agents_provider import AgentsServiceProvider


@pytest.fixture
def client():
    get_llm_service.cache_clear()

    with TestClient(app) as test_client:
        yield test_client

    get_llm_service.cache_clear()


class SlowProvider(LLMProvider):
    """Provider simulÃ© qui prend trop de temps pour rÃ©pondre."""

    async def generate(self, prompt: str) -> str:
        await asyncio.sleep(0.1)
        return "RÃ©ponse tardive"


class FailingProvider(LLMProvider):
    """Provider simulÃ© qui retourne une erreur."""

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


def test_agents_provider_success():
    def mock_response(request):
        assert request.method == "POST"
        assert request.url.path == "/agent/chat"
        assert request.read() == b'{"prompt":"Bonjour"}'

        return httpx.Response(
            200,
            json={"response": "Bienvenue Ã  SmartCampus"},
        )

    transport = httpx.MockTransport(mock_response)

    provider = AgentsServiceProvider(
        base_url="http://agents:8001",
        transport=transport,
    )

    result = asyncio.run(provider.generate("Bonjour"))

    assert result == "Bienvenue Ã  SmartCampus"


def test_agents_provider_http_error():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(500)
    )

    provider = AgentsServiceProvider(
        base_url="http://agents:8001",
        transport=transport,
    )

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(provider.generate("Bonjour"))


def test_agents_provider_invalid_response():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"message": "Invalid format"},
        )
    )

    provider = AgentsServiceProvider(
        base_url="http://agents:8001",
        transport=transport,
    )

    with pytest.raises(ValueError, match="Invalid response"):
        asyncio.run(provider.generate("Bonjour"))
def test_agents_provider_error_through_llm_service():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(500)
    )

    provider = AgentsServiceProvider(
        base_url="http://agents:8001",
        transport=transport,
    )

    service = LLMService(
        provider=provider,
        timeout_seconds=5,
    )

    with pytest.raises(Exception) as error:
        asyncio.run(service.generate_response("Bonjour"))

    assert getattr(error.value, "status_code", None) == 502
    assert getattr(error.value, "code", None) == "LLM_PROVIDER_ERROR"
