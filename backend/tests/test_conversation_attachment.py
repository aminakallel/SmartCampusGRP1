from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid1, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.routes.guest_sessions import get_guest_session_store
from app.auth.dependencies import get_user_repository
from app.conversation_memory.router import get_memory_service
from app.main import create_app
from app.services.conversation_attachment import (
    AttachmentError,
    ConversationAttachmentService,
    ConversationMessage,
    GuestContextAlreadyClaimed,
    GuestContextNotFound,
    GuestConversationContext,
    InMemoryConversationAttachmentRepository,
    SessionMemoryAttachmentRepository,
)
from app.conversation_memory.service import TemporaryMemoryService
from app.services.guest_sessions import InMemoryGuestSessionStore


class FakeClock:
    def __init__(self):
        self.current = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.current


@pytest.fixture
def attachment_setup():
    repository = InMemoryConversationAttachmentRepository()
    service = ConversationAttachmentService(repository)
    session_id = uuid4()
    account_id = uuid4()
    messages = (
        ConversationMessage("msg-fake-001", "user", "Je cherche une formation en informatique.", "2026-11-22T10:00:00Z"),
        ConversationMessage("msg-fake-002", "assistant", "Quel est votre niveau d'études ?", "2026-11-22T10:00:03Z"),
    )
    context = GuestConversationContext(
        session_id=session_id,
        conversation_id="conv_fake_001",
        messages=messages,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    repository.add_guest_context(context)
    return repository, service, session_id, account_id, context


def test_guest_conversation_is_attached_to_new_account_without_losing_context(attachment_setup):
    repository, service, session_id, account_id, original = attachment_setup

    result = service.attach(session_id, account_id)
    stored = repository.read(session_id)

    assert result.session_id == session_id
    assert result.account_id == account_id
    assert result.conversation_id == original.conversation_id
    assert result.messages == original.messages
    assert stored is not None
    assert stored.account_id == account_id
    assert stored.attached_at == result.attached_at
    assert stored.messages == original.messages
    assert stored.expires_at == original.expires_at


def test_guest_session_uuid_from_sa25_api_is_accepted_and_conversation_id_preserved():
    with TestClient(create_app()) as client:
        guest_session = client.post("/api/v1/sessions/visiteur").json()

    session_id = UUID(guest_session["session_id"])
    assert session_id.version == 4
    assert guest_session["conversation_id"].startswith("conv_")
    repository = InMemoryConversationAttachmentRepository()
    repository.add_guest_context(
        GuestConversationContext(
            session_id=session_id,
            conversation_id=guest_session["conversation_id"],
            messages=(ConversationMessage("msg-fake", "user", "Question", "2026-11-22T10:00:00Z"),),
            expires_at=datetime.fromisoformat(guest_session["expires_at"].replace("Z", "+00:00")),
        )
    )

    result = ConversationAttachmentService(repository).attach(session_id, uuid4())

    assert result.session_id == session_id
    assert result.conversation_id == guest_session["conversation_id"]
    assert len(result.messages) == 1


def test_repeating_attachment_to_same_account_is_idempotent(attachment_setup):
    _repository, service, session_id, account_id, _original = attachment_setup

    first = service.attach(session_id, account_id)
    repeated = service.attach(session_id, account_id)

    assert repeated.already_attached is True
    assert repeated.attached_at == first.attached_at
    assert repeated.conversation_id == first.conversation_id
    assert repeated.messages == first.messages


def test_guest_context_cannot_be_taken_over_by_another_account(attachment_setup):
    _repository, service, session_id, account_id, _original = attachment_setup
    service.attach(session_id, account_id)

    with pytest.raises(GuestContextAlreadyClaimed):
        service.attach(session_id, uuid4())


def test_concurrent_claims_allow_only_one_account(attachment_setup):
    repository, service, session_id, _account_id, _original = attachment_setup
    account_ids = (uuid4(), uuid4())

    def attempt(account_id):
        try:
            return service.attach(session_id, account_id).account_id
        except GuestContextAlreadyClaimed:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(attempt, account_ids))

    winners = [account_id for account_id in outcomes if account_id is not None]
    assert len(winners) == 1
    assert repository.read(session_id).account_id == winners[0]


def test_missing_or_expired_guest_context_cannot_be_attached(attachment_setup):
    repository, service, _session_id, account_id, _original = attachment_setup
    expired_session_id = uuid4()
    repository.add_guest_context(
        GuestConversationContext(
            session_id=expired_session_id,
            conversation_id="conv_expired_fake",
            messages=(),
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
    )

    with pytest.raises(GuestContextNotFound):
        service.attach(uuid4(), account_id)
    with pytest.raises(GuestContextNotFound):
        service.attach(expired_session_id, account_id)


def test_session_id_must_be_uuid_v4_but_account_uuid_version_is_unrestricted(attachment_setup):
    _repository, service, session_id, _account_id, _original = attachment_setup

    with pytest.raises(AttachmentError, match="session_id must be a UUID v4"):
        service.attach(UUID(int=1), uuid4())

    account_id = uuid1()
    assert service.attach(session_id, account_id).account_id == account_id


def test_account_id_must_be_uuid(attachment_setup):
    _repository, service, session_id, _account_id, _original = attachment_setup

    with pytest.raises(AttachmentError, match="account_id must be a UUID"):
        service.attach(session_id, "usr_fake_001")


def test_context_rejects_naive_expiration_timestamp():
    with pytest.raises(AttachmentError, match="expires_at must be timezone-aware"):
        GuestConversationContext(
            session_id=uuid4(),
            conversation_id="conv_fake",
            messages=(),
            expires_at=datetime(2026, 11, 22),
        )


def test_context_requires_conversation_id_and_consistent_attachment_metadata():
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    with pytest.raises(AttachmentError, match="conversation_id must not be empty"):
        GuestConversationContext(uuid4(), " ", (), expires_at)

    with pytest.raises(AttachmentError, match="account_id and attached_at must be set together"):
        GuestConversationContext(uuid4(), "conv_fake", (), expires_at, account_id=uuid4())


def test_repository_rejects_duplicate_guest_session(attachment_setup):
    repository, _service, _session_id, _account_id, original = attachment_setup

    with pytest.raises(AttachmentError, match="Guest session already exists"):
        repository.add_guest_context(original)


@pytest.fixture
def integrated_client(monkeypatch):
    monkeypatch.setenv("AUTH_USE_IN_MEMORY", "true")
    monkeypatch.setenv("JWT_SECRET", "test-only-secret-with-at-least-32-bytes")
    monkeypatch.setenv("JWT_ISSUER", "smartcampus-tests")
    get_user_repository.cache_clear()
    user_repository = get_user_repository()
    clock = FakeClock()
    session_store = InMemoryGuestSessionStore(clock=clock)
    memory_service = TemporaryMemoryService(clock=clock)
    application = create_app()
    application.dependency_overrides[get_guest_session_store] = lambda: session_store
    application.dependency_overrides[get_memory_service] = lambda: memory_service
    with TestClient(application) as client:
        yield client, application, session_store, memory_service
    application.dependency_overrides.clear()
    get_memory_service.cache_clear()
    user_repository.clear()
    get_user_repository.cache_clear()


def test_sa25_sa26_sa29_api_flow_attaches_the_same_history(integrated_client):
    client, _application, session_store, memory_service = integrated_client
    guest_response = client.post("/api/v1/sessions/visiteur")
    assert guest_response.status_code == 201
    guest = guest_response.json()
    session_id = UUID(guest["session_id"])

    for role, content in (
        ("user", "Je cherche une formation en informatique."),
        ("assistant", "Quel est votre niveau d'études ?"),
    ):
        response = client.post(
            f"/api/v1/memory/sessions/{session_id}/messages",
            json={"role": role, "content": content},
        )
        assert response.status_code == 200

    before = client.get(f"/api/v1/memory/sessions/{session_id}").json()
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": "amina.candidate@example.tn",
            "password": "Candidate123",
            "nom": "Ben Ali",
            "prenom": "Amina",
            "session_id": str(session_id),
        },
    )
    assert registration.status_code == 201
    registered = registration.json()
    account_id = registered["user"]["id"]
    assert registered["conversation_rattachee"] is True

    response = client.post(
        "/api/v1/chat/rattacher",
        headers={
            "X-Session-ID": str(session_id),
            "Authorization": f"Bearer {registered['access_token']}",
        },
    )

    assert response.status_code == 200
    attached = response.json()
    assert attached["session_id"] == str(session_id)
    assert attached["conversation_id"] == guest["conversation_id"]
    assert attached["account_id"] == str(account_id)
    assert attached["message_count"] == 2
    after = client.get(f"/api/v1/memory/sessions/{session_id}").json()
    assert after["messages"] == before["messages"]
    assert after["conversation_id"] == guest["conversation_id"]
    assert after["expires_at"] == guest["expires_at"]
    assert after["account_id"] == str(account_id)
    assert after["attached_at"] == attached["attached_at"]
    assert session_store.read(session_id).account_id == UUID(account_id)
    assert memory_service.get_memory(session_id).account_id == UUID(account_id)
    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {registered['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["id"] == account_id


def test_sa29_api_is_idempotent_and_rejects_account_takeover(integrated_client):
    client, _application, _session_store, _memory_service = integrated_client
    guest = client.post("/api/v1/sessions/visiteur").json()
    session_id = guest["session_id"]
    first_account = client.post(
        "/api/v1/auth/register",
        json={"email": "first@example.tn", "password": "Password123", "nom": "First", "prenom": "User"},
    ).json()
    first_headers = {
        "X-Session-ID": session_id,
        "Authorization": f"Bearer {first_account['access_token']}",
    }
    first = client.post("/api/v1/chat/rattacher", headers=first_headers)
    repeated = client.post("/api/v1/chat/rattacher", headers=first_headers)

    assert first.status_code == 200
    assert repeated.status_code == 200
    assert repeated.json()["already_attached"] is True
    assert repeated.json()["attached_at"] == first.json()["attached_at"]
    assert repeated.json()["account_id"] == first_account["user"]["id"]

    other_account = client.post(
        "/api/v1/auth/register",
        json={"email": "second@example.tn", "password": "Password123", "nom": "Second", "prenom": "User"},
    ).json()
    conflict = client.post(
        "/api/v1/chat/rattacher",
        headers={
            "X-Session-ID": session_id,
            "Authorization": f"Bearer {other_account['access_token']}",
        },
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "CONFLICT"


def test_login_can_attach_an_existing_visitor_session(integrated_client):
    client, _application, session_store, memory_service = integrated_client
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "email": "returning.candidate@example.tn",
            "password": "Password123",
            "nom": "Returning",
            "prenom": "Candidate",
        },
    )
    assert registered.status_code == 201

    guest = client.post("/api/v1/sessions/visiteur").json()
    session_id = UUID(guest["session_id"])
    client.post(
        f"/api/v1/memory/sessions/{session_id}/messages",
        json={"role": "user", "content": "Je reviens après connexion."},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "returning.candidate@example.tn",
            "password": "Password123",
            "session_id": str(session_id),
        },
    )

    assert login.status_code == 200
    assert login.json()["conversation_rattachee"] is True
    account_id = UUID(login.json()["user"]["id"])
    assert session_store.read(session_id).account_id == account_id
    attached_memory = memory_service.get_memory(session_id)
    assert attached_memory.account_id == account_id
    assert attached_memory.messages[0].content == "Je reviens après connexion."


def test_sa29_endpoint_requires_valid_sa28_authentication(monkeypatch):
    monkeypatch.setenv("AUTH_USE_IN_MEMORY", "true")
    monkeypatch.setenv("JWT_SECRET", "test-only-secret-with-at-least-32-bytes")
    client = TestClient(create_app())
    session_id = client.post("/api/v1/sessions/visiteur").json()["session_id"]

    response = client.post("/api/v1/chat/rattacher", headers={"X-Session-ID": session_id})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    authenticated_but_unconfigured = client.post(
        "/api/v1/chat/rattacher",
        headers={
            "X-Session-ID": session_id,
            "Authorization": "Bearer fake-token",
        },
    )
    assert authenticated_but_unconfigured.status_code == 401
    assert authenticated_but_unconfigured.json()["error"]["code"] == "UNAUTHORIZED"


def test_sa29_returns_not_found_if_sa26_memory_is_missing():
    clock = FakeClock()
    session_store = InMemoryGuestSessionStore(clock=clock)
    session = session_store.create()
    memory_service = TemporaryMemoryService(clock=clock)
    service = ConversationAttachmentService(
        SessionMemoryAttachmentRepository(session_store, memory_service)
    )

    with pytest.raises(GuestContextNotFound):
        service.attach(session.session_id, uuid4())
    assert session_store.read(session.session_id).account_id is None


def test_sa29_rejects_sa25_sa26_conversation_mismatch_without_partial_attach():
    clock = FakeClock()
    session_store = InMemoryGuestSessionStore(clock=clock)
    session = session_store.create()
    memory_service = TemporaryMemoryService(clock=clock)
    memory_service.create_session(
        session.session_id,
        "conv_different_from_sa25",
        session.expires_at,
    )
    service = ConversationAttachmentService(
        SessionMemoryAttachmentRepository(session_store, memory_service)
    )

    with pytest.raises(AttachmentError, match="conversation_id values differ"):
        service.attach(session.session_id, uuid4())
    assert session_store.read(session.session_id).account_id is None
    assert memory_service.get_memory(session.session_id).account_id is None


def test_sa29_rolls_back_sa25_claim_if_sa26_update_fails():
    clock = FakeClock()
    session_store = InMemoryGuestSessionStore(clock=clock)
    session = session_store.create()
    memory_service = TemporaryMemoryService(clock=clock)
    memory_service.create_session(
        session.session_id,
        session.conversation_id,
        session.expires_at,
    )

    def fail_attach(*_args, **_kwargs):
        raise ValueError("simulated memory write failure")

    memory_service.attach_account = fail_attach
    service = ConversationAttachmentService(
        SessionMemoryAttachmentRepository(session_store, memory_service)
    )

    with pytest.raises(AttachmentError, match="Could not attach session memory"):
        service.attach(session.session_id, uuid4())
    assert session_store.read(session.session_id).account_id is None
