"""Provisional visitor-to-account conversation attachment service.

This in-memory implementation is a contract scaffold for SA-29. It does not
implement authentication, HTTP routes, or database persistence while those
contracts are still pending.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Protocol
from uuid import UUID

from app.conversation_memory.service import (
    MemoryOwnershipConflict,
    MemorySessionNotFound,
    TemporaryMemoryService,
)
from app.services.guest_sessions import (
    GuestSessionNotFound,
    GuestSessionOwnershipConflict,
    InMemoryGuestSessionStore,
)


class AttachmentError(ValueError):
    """Base class for invalid or conflicting attachment requests."""


class GuestContextNotFound(AttachmentError):
    """The guest context is missing or has already expired."""


class GuestContextAlreadyClaimed(AttachmentError):
    """A guest context is already attached to a different account."""


def _require_aware_datetime(value: datetime, field_name: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise AttachmentError(f"{field_name} must be timezone-aware")


@dataclass(frozen=True, slots=True)
class ConversationMessage:
    """Temporary message fixture shape based on Roua's frontend types."""

    id: str
    role: str
    content: str
    created_at: str


@dataclass(frozen=True, slots=True)
class GuestConversationContext:
    """Guest session and history snapshot used by the replaceable repository."""

    session_id: UUID
    conversation_id: str
    messages: tuple[object, ...]
    expires_at: datetime
    account_id: UUID | None = None
    attached_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.session_id, UUID) or self.session_id.version != 4:
            raise AttachmentError("session_id must be a UUID v4")
        if not isinstance(self.conversation_id, str) or not self.conversation_id.strip():
            raise AttachmentError("conversation_id must not be empty")
        if not isinstance(self.messages, tuple):
            raise AttachmentError("messages must be a tuple")
        if self.account_id is not None and not isinstance(self.account_id, UUID):
            raise AttachmentError("account_id must be a UUID")
        _require_aware_datetime(self.expires_at, "expires_at")
        if (self.account_id is None) != (self.attached_at is None):
            raise AttachmentError("account_id and attached_at must be set together")
        if self.attached_at is not None:
            _require_aware_datetime(self.attached_at, "attached_at")


@dataclass(frozen=True, slots=True)
class AttachmentResult:
    session_id: UUID
    conversation_id: str
    account_id: UUID
    attached_at: datetime
    messages: tuple[object, ...]
    already_attached: bool = False


class ConversationAttachmentRepository(Protocol):
    """Persistence seam to implement after Roua/Yasmine contracts are final."""

    def attach(self, session_id: UUID, account_id: UUID, now: datetime) -> AttachmentResult: ...


class InMemoryConversationAttachmentRepository:
    """Thread-safe fake store for SA-29 scenario and contract tests."""

    def __init__(self) -> None:
        self._contexts: dict[UUID, GuestConversationContext] = {}
        self._lock = RLock()

    def add_guest_context(self, context: GuestConversationContext) -> None:
        with self._lock:
            if context.session_id in self._contexts:
                raise AttachmentError("Guest session already exists")
            self._contexts[context.session_id] = context

    def read(self, session_id: UUID) -> GuestConversationContext | None:
        with self._lock:
            return self._contexts.get(session_id)

    def attach(self, session_id: UUID, account_id: UUID, now: datetime) -> AttachmentResult:
        with self._lock:
            context = self._contexts.get(session_id)
            if context is None or context.expires_at <= now:
                self._contexts.pop(session_id, None)
                raise GuestContextNotFound("Guest session not found or expired")
            if context.account_id is not None:
                if context.account_id != account_id:
                    raise GuestContextAlreadyClaimed("Guest session belongs to another account")
                return AttachmentResult(
                    session_id=session_id,
                    conversation_id=context.conversation_id,
                    account_id=account_id,
                    attached_at=context.attached_at,
                    messages=context.messages,
                    already_attached=True,
                )

            attached = GuestConversationContext(
                session_id=context.session_id,
                conversation_id=context.conversation_id,
                messages=context.messages,
                expires_at=context.expires_at,
                account_id=account_id,
                attached_at=now,
            )
            self._contexts[session_id] = attached
            return AttachmentResult(
                session_id=session_id,
                conversation_id=attached.conversation_id,
                account_id=account_id,
                attached_at=now,
                messages=attached.messages,
            )


class SessionMemoryAttachmentRepository:
    """Coordinate SA-25 session metadata and SA-26 memory in local storage."""

    def __init__(
        self,
        session_store: InMemoryGuestSessionStore,
        memory_service: TemporaryMemoryService,
    ) -> None:
        self._session_store = session_store
        self._memory_service = memory_service
        self._lock = RLock()

    def attach(self, session_id: UUID, account_id: UUID, now: datetime) -> AttachmentResult:
        with self._lock:
            session = self._session_store.read(session_id)
            memory = self._memory_service.get_memory(session_id)
            if session is None or memory is None:
                raise GuestContextNotFound("Guest session or memory not found or expired")
            if session.conversation_id != memory.conversation_id:
                raise AttachmentError("SA-25 and SA-26 conversation_id values differ")
            if session.expires_at != memory.expires_at:
                raise AttachmentError("SA-25 and SA-26 expiry values differ")
            if session.created_at != memory.created_at:
                raise AttachmentError("SA-25 and SA-26 creation timestamps differ")

            if session.account_id is not None and session.account_id != account_id:
                raise GuestContextAlreadyClaimed("Guest session belongs to another account")
            if memory.account_id is not None and memory.account_id != account_id:
                raise GuestContextAlreadyClaimed("Conversation memory belongs to another account")
            if memory.account_id is not None and session.account_id is None:
                raise AttachmentError("SA-25 and SA-26 attachment state differs")
            if session.account_id is not None and memory.account_id is not None:
                if session.attached_at != memory.attached_at:
                    raise AttachmentError("SA-25 and SA-26 attachment timestamps differ")
                return AttachmentResult(
                    session_id=session_id,
                    conversation_id=session.conversation_id,
                    account_id=account_id,
                    attached_at=session.attached_at,
                    messages=tuple(memory.messages),
                    already_attached=True,
                )

            try:
                attached_session = self._session_store.attach_account(session_id, account_id)
            except GuestSessionNotFound as exc:
                raise GuestContextNotFound(str(exc)) from exc
            except GuestSessionOwnershipConflict as exc:
                raise GuestContextAlreadyClaimed(str(exc)) from exc
            try:
                attached_memory = self._memory_service.attach_account(
                    session_id,
                    account_id,
                    attached_at=attached_session.attached_at,
                )
            except (MemorySessionNotFound, MemoryOwnershipConflict, ValueError) as exc:
                self._session_store.rollback_account_attachment(session_id, account_id)
                if isinstance(exc, MemoryOwnershipConflict):
                    raise GuestContextAlreadyClaimed(str(exc)) from exc
                raise AttachmentError("Could not attach session memory") from exc

            return AttachmentResult(
                session_id=session_id,
                conversation_id=attached_session.conversation_id,
                account_id=account_id,
                attached_at=attached_session.attached_at,
                messages=tuple(attached_memory.messages),
            )


class ConversationAttachmentService:
    """Attach a guest conversation to an account ID supplied by trusted auth."""

    def __init__(self, repository: ConversationAttachmentRepository) -> None:
        self._repository = repository

    def attach(self, session_id: UUID, account_id: UUID) -> AttachmentResult:
        if not isinstance(session_id, UUID) or session_id.version != 4:
            raise AttachmentError("session_id must be a UUID v4")
        # SA-13 defines the account key as UUID, without restricting its version.
        if not isinstance(account_id, UUID):
            raise AttachmentError("account_id must be a UUID")
        return self._repository.attach(session_id, account_id, datetime.now(timezone.utc))
