
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.conversation_memory.router import get_memory_service


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_memory_service():
    get_memory_service.cache_clear()
    yield
    get_memory_service.cache_clear()


def test_api_add_and_get_message():
    response = client.post(
        "/api/v1/memory/sessions/session_001/messages",
        json={
            "role": "user",
            "content": "Je cherche une formation en informatique",
        },
    )

    assert response.status_code == 200
    assert len(response.json()["messages"]) == 1

    response = client.get(
        "/api/v1/memory/sessions/session_001"
    )

    assert response.status_code == 200
    assert response.json()["messages"][0]["content"] == (
        "Je cherche une formation en informatique"
    )


def test_api_update_temporary_information():
    response = client.patch(
        "/api/v1/memory/sessions/session_002/information",
        json={
            "information": {
                "niveau": "Baccalauréat",
                "domaine": "Informatique",
            }
        },
    )

    assert response.status_code == 200
    assert response.json()["temporary_info"]["niveau"] == "Baccalauréat"


def test_api_delete_session():
    client.post(
        "/api/v1/memory/sessions/session_003/messages",
        json={"role": "user", "content": "Bonjour"},
    )

    response = client.delete(
        "/api/v1/memory/sessions/session_003"
    )

    assert response.status_code == 200

    response = client.get(
        "/api/v1/memory/sessions/session_003"
    )

    assert response.status_code == 404


def test_api_get_unknown_session_returns_404():
    response = client.get(
        "/api/v1/memory/sessions/unknown_session"
    )

    assert response.status_code == 404


def test_api_rejects_empty_message():
    response = client.post(
        "/api/v1/memory/sessions/session_004/messages",
        json={"role": "user", "content": ""},
    )

    assert response.status_code == 422
