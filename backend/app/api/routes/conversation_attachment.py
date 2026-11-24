"""SA-29 guest-session attachment endpoint with an SA-28 auth seam."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.auth.models import UserAccount, UserRole
from app.api.routes.guest_sessions import get_guest_session_store
from app.conversation_memory.router import get_memory_service
from app.conversation_memory.service import TemporaryMemoryService
from app.services.conversation_attachment import (
    AttachmentError,
    ConversationAttachmentService,
    GuestContextAlreadyClaimed,
    GuestContextNotFound,
    SessionMemoryAttachmentRepository,
)
from app.services.guest_sessions import InMemoryGuestSessionStore


router = APIRouter(prefix="/api/v1/chat", tags=["conversation attachment"])


class AttachmentResponse(BaseModel):
    session_id: UUID
    conversation_id: str
    account_id: UUID
    attached_at: datetime
    already_attached: bool
    message_count: int


def get_authenticated_account_id(
    user: UserAccount = Depends(get_current_user),
) -> UUID:
    """Return the verified SA-28 identity for a candidate-owned operation."""
    if user.role != UserRole.CANDIDAT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only candidate accounts may attach visitor conversations",
        )
    return user.id


def get_conversation_attachment_service(
    session_store: InMemoryGuestSessionStore = Depends(get_guest_session_store),
    memory_service: TemporaryMemoryService = Depends(get_memory_service),
) -> ConversationAttachmentService:
    repository = SessionMemoryAttachmentRepository(session_store, memory_service)
    return ConversationAttachmentService(repository)


@router.post("/rattacher", response_model=AttachmentResponse)
def attach_guest_conversation(
    x_session_id: UUID = Header(..., alias="X-Session-ID"),
    account_id: UUID = Depends(get_authenticated_account_id),
    service: ConversationAttachmentService = Depends(get_conversation_attachment_service),
) -> AttachmentResponse:
    if x_session_id.version != 4:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="X-Session-ID must be a UUID v4",
        )
    try:
        result = service.attach(x_session_id, account_id)
    except GuestContextNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except GuestContextAlreadyClaimed as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except AttachmentError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return AttachmentResponse(
        session_id=result.session_id,
        conversation_id=result.conversation_id,
        account_id=result.account_id,
        attached_at=result.attached_at,
        already_attached=result.already_attached,
        message_count=len(result.messages),
    )
