"""Temporary anonymous visitor session service with process-local storage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Callable
from uuid import UUID, uuid4


DEFAULT_SESSION_TTL = timedelta(hours=24)
Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class GuestSession:
    """Session metadata only; conversation messages are outside this service."""

    session_id: UUID
    conversation_id: str
    created_at: datetime
    expires_at: datetime


class InMemoryGuestSessionStore:
    """Thread-safe, process-local store for the database-not-ready phase.

    Expired records are removed on create, read, and explicit expiry operations.
    A process restart clears the store; use a shared database or cache before
    running multiple API workers in production.
    """

    def __init__(
        self,
        ttl: timedelta = DEFAULT_SESSION_TTL,
        clock: Clock = utc_now,
    ) -> None:
        if ttl.total_seconds() <= 0:
            raise ValueError("Session TTL must be positive")
        self._ttl = ttl
        self._clock = clock
        self._lock = RLock()
        self._sessions: dict[UUID, GuestSession] = {}

    def create(self) -> GuestSession:
        with self._lock:
            now = self._now()
            self._purge_expired_locked(now)
            session = GuestSession(
                session_id=uuid4(),
                conversation_id=f"conv_{uuid4()}",
                created_at=now,
                expires_at=now + self._ttl,
            )
            self._sessions[session.session_id] = session
            return session

    def read(self, session_id: UUID) -> GuestSession | None:
        with self._lock:
            now = self._now()
            self._purge_expired_locked(now)
            return self._sessions.get(session_id)

    def expire(self, session_id: UUID) -> bool:
        """Remove a session immediately; return False when absent or expired."""
        with self._lock:
            now = self._now()
            self._purge_expired_locked(now)
            return self._sessions.pop(session_id, None) is not None

    def purge_expired(self) -> int:
        """Remove expired records and return the number removed."""
        with self._lock:
            return self._purge_expired_locked(self._now())

    def _now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("Session clock must return a timezone-aware datetime")
        return now.astimezone(timezone.utc)

    def _purge_expired_locked(self, now: datetime) -> int:
        expired_ids = [
            session_id
            for session_id, session in self._sessions.items()
            if session.expires_at <= now
        ]
        for session_id in expired_ids:
            del self._sessions[session_id]
        return len(expired_ids)
