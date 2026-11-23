
from datetime import datetime, timedelta, timezone

from app.conversation_memory.service import TemporaryMemoryService


def test_create_session():
    service = TemporaryMemoryService()

    memory = service.create_session("session_001")

    assert memory.session_id == "session_001"
    assert memory.messages == []
    assert memory.temporary_info == {}


def test_add_and_read_message():
    service = TemporaryMemoryService()

    service.add_message(
        session_id="session_001",
        role="user",
        content="Je cherche une formation en informatique",
    )

    memory = service.get_memory("session_001")

    assert memory is not None
    assert len(memory.messages) == 1
    assert memory.messages[0].role == "user"
    assert memory.messages[0].content == (
        "Je cherche une formation en informatique"
    )


def test_add_assistant_message():
    service = TemporaryMemoryService()

    service.add_message(
        "session_001",
        "user",
        "Bonjour",
    )
    service.add_message(
        "session_001",
        "assistant",
        "Bonjour, comment puis-je vous aider ?",
    )

    memory = service.get_memory("session_001")

    assert len(memory.messages) == 2
    assert memory.messages[1].role == "assistant"


def test_update_temporary_information():
    service = TemporaryMemoryService()

    service.update_temporary_info(
        "session_001",
        {"niveau": "Baccalauréat"},
    )

    memory = service.get_memory("session_001")

    assert memory.temporary_info["niveau"] == "Baccalauréat"


def test_keep_only_last_messages():
    service = TemporaryMemoryService(max_messages=2)

    service.add_message("session_001", "user", "Message 1")
    service.add_message("session_001", "assistant", "Message 2")
    service.add_message("session_001", "user", "Message 3")

    memory = service.get_memory("session_001")

    assert len(memory.messages) == 2
    assert memory.messages[0].content == "Message 2"
    assert memory.messages[1].content == "Message 3"


def test_expired_session_is_deleted():
    service = TemporaryMemoryService()

    memory = service.create_session("session_001")

    memory.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    service.repository.save(memory)

    result = service.get_memory("session_001")

    assert result is None
    assert service.repository.get("session_001") is None


def test_delete_session():
    service = TemporaryMemoryService()

    service.create_session("session_001")

    result = service.delete_session("session_001")

    assert result is True
    assert service.get_memory("session_001") is None
