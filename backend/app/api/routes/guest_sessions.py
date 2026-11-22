"""Guest-session endpoints using UUID v4 session identifiers."""

from datetime import datetime, timedelta
from os import environ
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from pydantic import BaseModel

from app.services.guest_sessions import (
    InMemoryGuestSessionStore,
    GuestSession,
)


def _build_default_store() -> InMemoryGuestSessionStore:
    raw_ttl = environ.get("GUEST_SESSION_TTL_SECONDS")
    if raw_ttl is None:
        return InMemoryGuestSessionStore()
    try:
        ttl_seconds = int(raw_ttl)
    except ValueError as exc:
        raise RuntimeError("GUEST_SESSION_TTL_SECONDS must be an integer") from exc
    if ttl_seconds <= 0:
        raise RuntimeError("GUEST_SESSION_TTL_SECONDS must be positive")
    return InMemoryGuestSessionStore(ttl=timedelta(seconds=ttl_seconds))


_store = _build_default_store()
router = APIRouter(prefix="/api/v1/sessions/visiteur", tags=["sessions visiteur"])


class GuestSessionResponse(BaseModel):
    session_id: UUID
    conversation_id: str
    created_at: datetime
    expires_at: datetime


def get_guest_session_store() -> InMemoryGuestSessionStore:
    """Dependency seam for replacing the process-local store in tests/runtime."""
    return _store


def _response(session: GuestSession) -> GuestSessionResponse:
    return GuestSessionResponse(
        session_id=session.session_id,
        conversation_id=session.conversation_id,
        created_at=session.created_at,
        expires_at=session.expires_at,
    )


def _require_v4(session_id: UUID) -> UUID:
    if session_id.version != 4:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="X-Session-ID must be a UUID v4",
        )
    return session_id


@router.post("", response_model=GuestSessionResponse, status_code=status.HTTP_201_CREATED)
def create_guest_session(
    store: InMemoryGuestSessionStore = Depends(get_guest_session_store),
) -> GuestSessionResponse:
    return _response(store.create())


@router.get("", response_model=GuestSessionResponse)
def read_guest_session(
    x_session_id: UUID = Header(..., alias="X-Session-ID"),
    store: InMemoryGuestSessionStore = Depends(get_guest_session_store),
) -> GuestSessionResponse:
    session_id = _require_v4(x_session_id)
    session = store.read(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Guest session not found or expired")
    return _response(session)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def expire_guest_session(
    x_session_id: UUID = Header(..., alias="X-Session-ID"),
    store: InMemoryGuestSessionStore = Depends(get_guest_session_store),
) -> Response:
    session_id = _require_v4(x_session_id)
    if not store.expire(session_id):
        raise HTTPException(status_code=404, detail="Guest session not found or expired")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
