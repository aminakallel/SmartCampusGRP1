
from datetime import datetime, timedelta, timezone

from app.conversation_memory.repository import InMemoryMemoryRepository
from app.conversation_memory.schemas import (
    MessageSchema,
    SessionMemorySchema,
)


class TemporaryMemoryService:
    """Gestion de la mémoire temporaire des conversations."""

    def __init__(
        self,
        repository: InMemoryMemoryRepository | None = None,
        ttl_minutes: int = 30,
        max_messages: int = 20,
    ):
        if ttl_minutes <= 0:
            raise ValueError("ttl_minutes doit être positif")

        if max_messages <= 0:
            raise ValueError("max_messages doit être positif")

        self.repository = repository or InMemoryMemoryRepository()
        self.ttl_minutes = ttl_minutes
        self.max_messages = max_messages

    def _expiration_time(self) -> datetime:
        return datetime.now(timezone.utc) + timedelta(
            minutes=self.ttl_minutes
        )

    def create_session(self, session_id: str) -> SessionMemorySchema:
        """Créer une nouvelle session de conversation."""

        memory = SessionMemorySchema(
            session_id=session_id,
            expires_at=self._expiration_time(),
        )

        self.repository.save(memory)
        return memory

    def get_memory(self, session_id: str) -> SessionMemorySchema | None:
        """Lire la mémoire si la session n'est pas expirée."""

        memory = self.repository.get(session_id)

        if memory is None:
            return None

        if memory.expires_at <= datetime.now(timezone.utc):
            self.repository.delete(session_id)
            return None

        return memory

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> SessionMemorySchema:

        memory = self.get_memory(session_id)

        if memory is None:
            memory = self.create_session(session_id)

        message = MessageSchema(
            role=role,
            content=content,
            metadata=metadata or {},
        )

        memory.messages.append(message)

        # Garder uniquement les derniers messages.
        memory.messages = memory.messages[-self.max_messages:]

        # Renouveler la durée de vie après chaque activité.
        memory.expires_at = self._expiration_time()

        self.repository.save(memory)
        return memory

    def update_temporary_info(
        self,
        session_id: str,
        information: dict,
    ) -> SessionMemorySchema:

        memory = self.get_memory(session_id)

        if memory is None:
            memory = self.create_session(session_id)

        memory.temporary_info.update(information)
        memory.expires_at = self._expiration_time()

        self.repository.save(memory)
        return memory

    def delete_session(self, session_id: str) -> bool:
        """Supprimer explicitement une session."""
        return self.repository.delete(session_id)
