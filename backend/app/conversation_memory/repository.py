
from app.conversation_memory.schemas import SessionMemorySchema


class InMemoryMemoryRepository:
    """Stockage temporaire des conversations en mémoire."""

    def __init__(self):
        self._sessions: dict[str, SessionMemorySchema] = {}

    def save(self, memory: SessionMemorySchema) -> None:
        """Enregistrer ou remplacer la mémoire d'une session."""
        self._sessions[memory.session_id] = memory

    def get(self, session_id: str) -> SessionMemorySchema | None:
        """Récupérer la mémoire d'une session."""
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        """Supprimer une session. Retourne True si elle existait."""
        return self._sessions.pop(session_id, None) is not None
