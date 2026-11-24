from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid1

import pytest
from fastapi.testclient import TestClient

from app.api.routes.guest_sessions import get_guest_session_store
from app.conversation_memory.router import get_memory_service
from app.conversation_memory.service import TemporaryMemoryService
from app.main import create_app
from app.services.guest_sessions import InMemoryGuestSessionStore


class FakeClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 11, 22, 12, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.current

    def advance(self, amount: timedelta) -> None:
        self.current += amount


@pytest.fixture
def session_context():
    clock = FakeClock()
    store = InMemoryGuestSessionStore(ttl=timedelta(hours=24), clock=clock)
    memory_service = TemporaryMemoryService(clock=clock)
    application = create_app()
    application.dependency_overrides[get_guest_session_store] = lambda: store
    application.dependency_overrides[get_memory_service] = lambda: memory_service
    get_memory_service.cache_clear()
    with TestClient(application) as client:
        yield client, store, clock, memory_service
    application.dependency_overrides.clear()
    get_memory_service.cache_clear()


def test_create_guest_session_issues_uuid_v4_and_expiration(session_context):
    client, _store, _clock, memory_service = session_context

    response = client.post("/api/v1/sessions/visiteur")

    assert response.status_code == 201
    payload = response.json()
    session_id = UUID(payload["session_id"])
    assert session_id.version == 4
    conversation_id = payload["conversation_id"]
    assert conversation_id.startswith("conv_")
    assert UUID(conversation_id.removeprefix("conv_")).version == 4
    created_at = datetime.fromisoformat(payload["created_at"])
    expires_at = datetime.fromisoformat(payload["expires_at"])
    assert created_at.tzinfo is not None
    assert expires_at - created_at == timedelta(hours=24)
    memory = memory_service.get_memory(session_id)
    assert memory is not None
    assert str(memory.session_id) == payload["session_id"]
    assert memory.conversation_id == payload["conversation_id"]
    assert memory.expires_at == expires_at


def test_read_guest_session_uses_x_session_id_header(session_context):
    client, _store, _clock, _memory_service = session_context
    created = client.post("/api/v1/sessions/visiteur").json()

    response = client.get(
        "/api/v1/sessions/visiteur",
        headers={"X-Session-ID": created["session_id"]},
    )

    assert response.status_code == 200
    assert response.json() == created


def test_read_requires_session_header_and_uses_error_envelope(session_context):
    client, _store, _clock, _memory_service = session_context

    response = client.get("/api/v1/sessions/visiteur")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_non_v4_session_identifier_is_rejected(session_context):
    client, _store, _clock, _memory_service = session_context

    response = client.get(
        "/api/v1/sessions/visiteur",
        headers={"X-Session-ID": str(uuid1())},
    )

    assert response.status_code == 422
    assert "UUID v4" in response.json()["error"]["message"]


def test_expired_session_is_unreadable_and_purged(session_context):
    client, store, clock, memory_service = session_context
    created = client.post("/api/v1/sessions/visiteur").json()
    clock.advance(timedelta(hours=24))

    response = client.get(
        "/api/v1/sessions/visiteur",
        headers={"X-Session-ID": created["session_id"]},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert store.read(UUID(created["session_id"])) is None
    assert memory_service.get_memory(UUID(created["session_id"])) is None


def test_delete_expires_session_immediately(session_context):
    client, store, _clock, memory_service = session_context
    created = client.post("/api/v1/sessions/visiteur").json()
    session_id = UUID(created["session_id"])

    response = client.delete(
        "/api/v1/sessions/visiteur",
        headers={"X-Session-ID": str(session_id)},
    )

    assert response.status_code == 204
    assert store.read(session_id) is None
    assert memory_service.get_memory(session_id) is None


def test_unknown_session_cannot_be_read_or_expired(session_context):
    client, _store, _clock, _memory_service = session_context
    unknown = str(UUID(int=1, version=4))

    read_response = client.get(
        "/api/v1/sessions/visiteur",
        headers={"X-Session-ID": unknown},
    )
    delete_response = client.delete(
        "/api/v1/sessions/visiteur",
        headers={"X-Session-ID": unknown},
    )

    assert read_response.status_code == 404
    assert delete_response.status_code == 404


def test_store_rejects_non_positive_ttl():
    with pytest.raises(ValueError, match="TTL must be positive"):
        InMemoryGuestSessionStore(ttl=timedelta(seconds=0))
