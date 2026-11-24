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
    """Temporary session metadata; conversation messages live in SA-26."""

    session_id: UUID
    conversation_id: str
    created_at: datetime
    expires_at: datetime
    account_id: UUID | None = None
    attached_at: datetime | None = None


class GuestSessionNotFound(LookupError):
    """The session is unknown or expired."""


class GuestSessionOwnershipConflict(ValueError):
    """The session is already attached to a different account."""


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

    def attach_account(self, session_id: UUID, account_id: UUID) -> GuestSession:
        """Atomically claim a live session for an account; same-account retries are safe."""
        if not isinstance(account_id, UUID):
            raise ValueError("account_id must be a UUID")
        with self._lock:
            now = self._now()
            self._purge_expired_locked(now)
            session = self._sessions.get(session_id)
            if session is None:
                raise GuestSessionNotFound("Guest session not found or expired")
            if session.account_id is not None:
                if session.account_id != account_id:
                    raise GuestSessionOwnershipConflict(
                        "Guest session belongs to another account"
                    )
                return session
            attached = GuestSession(
                session_id=session.session_id,
                conversation_id=session.conversation_id,
                created_at=session.created_at,
                expires_at=session.expires_at,
                account_id=account_id,
                attached_at=now,
            )
            self._sessions[session_id] = attached
            return attached

    def rollback_account_attachment(self, session_id: UUID, account_id: UUID) -> bool:
        """Undo a just-written attachment if its paired memory update fails."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or session.account_id != account_id:
                return False
            self._sessions[session_id] = GuestSession(
                session_id=session.session_id,
                conversation_id=session.conversation_id,
                created_at=session.created_at,
                expires_at=session.expires_at,
            )
            return True

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
