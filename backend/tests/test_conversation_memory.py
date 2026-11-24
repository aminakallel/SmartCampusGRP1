from datetime import datetime, timedelta, timezone
from uuid import uuid1, uuid4

import pytest

from app.conversation_memory.service import (
    MemorySessionNotFound,
    TemporaryMemoryService,
)


class FakeClock:
    def __init__(self):
        self.current = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.current

    def advance(self, amount):
        self.current += amount


@pytest.fixture
def memory_context():
    clock = FakeClock()
    service = TemporaryMemoryService(clock=clock)
    session_id = uuid4()
    conversation_id = "conv_4e8d2a9e-5df5-4c6a-97b5-16d439f2ac15"
    expires_at = clock.current + timedelta(hours=24)
    memory = service.create_session(session_id, conversation_id, expires_at)
    return service, clock, session_id, conversation_id, expires_at, memory


def test_create_memory_uses_sa25_session_and_conversation_contract(memory_context):
    _service, _clock, session_id, conversation_id, expires_at, memory = memory_context

    assert memory.session_id == session_id
    assert memory.conversation_id == conversation_id
    assert memory.expires_at == expires_at
    assert memory.messages == []
    assert memory.temporary_info == {}


def test_add_and_read_message_preserves_sa26_fields(memory_context):
    service, _clock, session_id, _conversation_id, expires_at, _memory = memory_context

    service.add_message(
        session_id=session_id,
        role="user",
        content="Je cherche une formation en informatique",
        metadata={"langue": "fr"},
    )

    memory = service.get_memory(session_id)
    assert memory is not None
    assert len(memory.messages) == 1
    assert memory.messages[0].role == "user"
    assert memory.messages[0].content == "Je cherche une formation en informatique"
    assert memory.messages[0].metadata == {"langue": "fr"}
    assert memory.expires_at == expires_at


def test_add_assistant_message_keeps_order(memory_context):
    service, _clock, session_id, _conversation_id, _expires_at, _memory = memory_context
    service.add_message(session_id, "user", "Bonjour")
    service.add_message(session_id, "assistant", "Comment puis-je vous aider ?")

    memory = service.get_memory(session_id)
    assert memory is not None
    assert [message.role for message in memory.messages] == ["user", "assistant"]


def test_update_temporary_information(memory_context):
    service, _clock, session_id, _conversation_id, _expires_at, _memory = memory_context
    service.update_temporary_info(session_id, {"niveau": "Baccalauréat"})

    memory = service.get_memory(session_id)
    assert memory is not None
    assert memory.temporary_info["niveau"] == "Baccalauréat"


def test_keep_only_last_messages(memory_context):
    _service, clock, session_id, conversation_id, expires_at, _memory = memory_context
    service = TemporaryMemoryService(max_messages=2, clock=clock)
    service.create_session(session_id, conversation_id, expires_at)
    service.add_message(session_id, "user", "Message 1")
    service.add_message(session_id, "assistant", "Message 2")
    service.add_message(session_id, "user", "Message 3")

    memory = service.get_memory(session_id)
    assert memory is not None
    assert [message.content for message in memory.messages] == ["Message 2", "Message 3"]


def test_expired_memory_is_deleted_at_the_sa25_expiration(memory_context):
    service, clock, session_id, _conversation_id, _expires_at, _memory = memory_context
    clock.advance(timedelta(hours=24))

    assert service.get_memory(session_id) is None
    assert service.repository.get(session_id) is None


def test_delete_memory_does_not_create_or_extend_session(memory_context):
    service, _clock, session_id, _conversation_id, _expires_at, _memory = memory_context

    assert service.delete_session(session_id) is True
    assert service.get_memory(session_id) is None
    with pytest.raises(MemorySessionNotFound):
        service.add_message(session_id, "user", "No active session")


def test_unknown_session_cannot_create_memory_implicitly():
    service = TemporaryMemoryService()
    with pytest.raises(MemorySessionNotFound):
        service.add_message(uuid4(), "user", "No guest session")


def test_memory_rejects_non_v4_session():
    service = TemporaryMemoryService()
    with pytest.raises(ValueError, match="UUID v4"):
        service.create_session(uuid1(), "conv_fake", datetime.now(timezone.utc))


def test_memory_refuses_session_contract_mismatch(memory_context):
    service, _clock, session_id, _conversation_id, expires_at, _memory = memory_context
    with pytest.raises(ValueError, match="does not match SA-25"):
        service.create_session(session_id, "conv_other", expires_at)
