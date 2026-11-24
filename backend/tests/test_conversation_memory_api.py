import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app
from app.conversation_memory.router import get_memory_service


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_memory_service():
    get_memory_service.cache_clear()
    yield
    get_memory_service.cache_clear()


def _create_guest_session():
    response = client.post("/api/v1/sessions/visiteur")
    assert response.status_code == 201
    return response.json()


def test_api_add_and_get_message_for_sa25_session():
    guest = _create_guest_session()
    session_id = guest["session_id"]

    response = client.post(
        f"/api/v1/memory/sessions/{session_id}/messages",
        json={
            "role": "user",
            "content": "Je cherche une formation en informatique",
        },
    )

    assert response.status_code == 200
    assert response.json()["session_id"] == session_id
    assert response.json()["conversation_id"] == guest["conversation_id"]
    assert response.json()["created_at"] == guest["created_at"]
    assert response.json()["expires_at"] == guest["expires_at"]

    response = client.get(f"/api/v1/memory/sessions/{session_id}")
    assert response.status_code == 200
    assert response.json()["messages"][0]["content"] == (
        "Je cherche une formation en informatique"
    )


def test_api_update_temporary_information():
    guest = _create_guest_session()
    session_id = guest["session_id"]

    response = client.patch(
        f"/api/v1/memory/sessions/{session_id}/information",
        json={"information": {"niveau": "Baccalauréat", "domaine": "Informatique"}},
    )

    assert response.status_code == 200
    assert response.json()["temporary_info"]["niveau"] == "Baccalauréat"


def test_api_delete_memory_and_deny_subsequent_memory_access():
    guest = _create_guest_session()
    session_id = guest["session_id"]
    client.post(
        f"/api/v1/memory/sessions/{session_id}/messages",
        json={"role": "user", "content": "Bonjour"},
    )

    response = client.delete(f"/api/v1/memory/sessions/{session_id}")
    assert response.status_code == 200
    assert client.get(f"/api/v1/memory/sessions/{session_id}").status_code == 404
    # Deleting SA-26 memory does not silently expire the SA-25 guest session.
    assert client.get(
        "/api/v1/sessions/visiteur", headers={"X-Session-ID": session_id}
    ).status_code == 200


def test_api_unknown_memory_returns_404():
    response = client.get(f"/api/v1/memory/sessions/{uuid4()}")
    assert response.status_code == 404


def test_api_rejects_non_uuid_session_id():
    response = client.get("/api/v1/memory/sessions/not-a-uuid")
    assert response.status_code == 422


def test_api_rejects_empty_message():
    guest = _create_guest_session()
    response = client.post(
        f"/api/v1/memory/sessions/{guest['session_id']}/messages",
        json={"role": "user", "content": ""},
    )
    assert response.status_code == 422
