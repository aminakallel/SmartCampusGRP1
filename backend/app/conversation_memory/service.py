from datetime import datetime, timezone
from uuid import UUID

from app.conversation_memory.repository import InMemoryMemoryRepository
from app.conversation_memory.schemas import MessageSchema, SessionMemorySchema


class MemorySessionNotFound(LookupError):
    """The matching SA-25 session is absent or expired."""


class MemoryOwnershipConflict(ValueError):
    """A memory has already been attached to another account."""


class TemporaryMemoryService:
    """Memory whose identifier and expiry are owned by the SA-25 session."""

    def __init__(
        self,
        repository: InMemoryMemoryRepository | None = None,
        max_messages: int = 20,
        clock=None,
    ):
        if max_messages <= 0:
            raise ValueError("max_messages doit être positif")
        self.repository = repository or InMemoryMemoryRepository()
        self.max_messages = max_messages
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def create_session(
        self,
        session_id: UUID | str,
        conversation_id: str,
        expires_at: datetime,
        created_at: datetime | None = None,
    ) -> SessionMemorySchema:
        session_uuid = self._parse_session_id(session_id)
        if not isinstance(conversation_id, str) or not conversation_id.strip():
            raise ValueError("conversation_id must not be empty")
        self._require_aware(expires_at, "expires_at")
        created_at = created_at or self._clock()
        self._require_aware(created_at, "created_at")
        existing = self.repository.get(session_uuid)
        if existing is not None:
            if (
                existing.conversation_id != conversation_id
                or existing.expires_at != expires_at
                or existing.created_at != created_at
            ):
                raise ValueError("session memory contract does not match SA-25 session")
            return existing
        memory = SessionMemorySchema(
            session_id=session_uuid,
            conversation_id=conversation_id,
            created_at=created_at,
            expires_at=expires_at,
        )
        self.repository.save(memory)
        return memory

    def get_memory(self, session_id: UUID | str) -> SessionMemorySchema | None:
        session_uuid = self._parse_session_id(session_id)
        memory = self.repository.get(session_uuid)
        if memory is None:
            return None
        now = self._clock()
        self._require_aware(now, "clock")
        if memory.expires_at <= now:
            self.repository.delete(session_uuid)
            return None
        return memory

    def add_message(
        self,
        session_id: UUID | str,
        role: str,
        content: str,
        metadata: dict[str, object] | None = None,
    ) -> SessionMemorySchema:
        memory = self._require_memory(session_id)
        message = MessageSchema(role=role, content=content, metadata=metadata or {})
        memory.messages.append(message)
        memory.messages = memory.messages[-self.max_messages :]
        self.repository.save(memory)
        return memory

    def update_temporary_info(
        self,
        session_id: UUID | str,
        information: dict[str, object],
    ) -> SessionMemorySchema:
        memory = self._require_memory(session_id)
        memory.temporary_info.update(information)
        self.repository.save(memory)
        return memory

    def attach_account(
        self,
        session_id: UUID | str,
        account_id: UUID,
        attached_at: datetime | None = None,
    ) -> SessionMemorySchema:
        memory = self._require_memory(session_id)
        if not isinstance(account_id, UUID):
            raise ValueError("account_id must be a UUID")
        now = attached_at or self._clock()
        self._require_aware(now, "attached_at")
        if memory.account_id is not None and memory.account_id != account_id:
            raise MemoryOwnershipConflict("Memory already belongs to another account")
        if memory.account_id is None:
            memory.account_id = account_id
            memory.attached_at = now
            self.repository.save(memory)
        return memory

    def delete_session(self, session_id: UUID | str) -> bool:
        return self.repository.delete(self._parse_session_id(session_id))

    def _require_memory(self, session_id: UUID | str) -> SessionMemorySchema:
        memory = self.get_memory(session_id)
        if memory is None:
            raise MemorySessionNotFound("Guest session not found or expired")
        return memory

    @staticmethod
    def _parse_session_id(session_id: UUID | str) -> UUID:
        try:
            parsed = session_id if isinstance(session_id, UUID) else UUID(session_id)
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError("session_id must be a UUID v4") from exc
        if parsed.version != 4:
            raise ValueError("session_id must be a UUID v4")
        return parsed

    @staticmethod
    def _require_aware(value: datetime, field_name: str) -> None:
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{field_name} must be timezone-aware")
