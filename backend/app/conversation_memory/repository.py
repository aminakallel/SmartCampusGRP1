from threading import RLock
from uuid import UUID

from app.conversation_memory.schemas import SessionMemorySchema


class InMemoryMemoryRepository:
    """Process-local repository keyed by the canonical SA-25 session UUID."""

    def __init__(self):
        self._sessions: dict[UUID, SessionMemorySchema] = {}
        self._lock = RLock()

    def save(self, memory: SessionMemorySchema) -> None:
        with self._lock:
            self._sessions[UUID(str(memory.session_id))] = memory

    def get(self, session_id: UUID | str) -> SessionMemorySchema | None:
        with self._lock:
            return self._sessions.get(UUID(str(session_id)))

    def delete(self, session_id: UUID | str) -> bool:
        with self._lock:
            return self._sessions.pop(UUID(str(session_id)), None) is not None

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()
