from functools import lru_cache
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import UUID4

from app.conversation_memory.schemas import (
    MessageCreate,
    SessionMemorySchema,
    TemporaryInfoUpdate,
)
from app.conversation_memory.service import (
    MemorySessionNotFound,
    TemporaryMemoryService,
)


@lru_cache
def get_memory_service() -> TemporaryMemoryService:
    """Provide the shared process-local SA-26 service."""
    return TemporaryMemoryService()


router = APIRouter(
    prefix="/memory/sessions",
    tags=["Temporary Memory"],
)


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Guest session not found or expired",
    )


@router.post("/{session_id}/messages", response_model=SessionMemorySchema)
def add_message(
    session_id: UUID4,
    message: MessageCreate,
    service: TemporaryMemoryService = Depends(get_memory_service),
) -> SessionMemorySchema:
    try:
        return service.add_message(
            session_id=UUID(str(session_id)),
            role=message.role,
            content=message.content,
            metadata=message.metadata,
        )
    except MemorySessionNotFound as exc:
        raise _not_found() from exc


@router.get("/{session_id}", response_model=SessionMemorySchema)
def get_session_memory(
    session_id: UUID4,
    service: TemporaryMemoryService = Depends(get_memory_service),
) -> SessionMemorySchema:
    memory = service.get_memory(UUID(str(session_id)))
    if memory is None:
        raise _not_found()
    return memory


@router.patch("/{session_id}/information", response_model=SessionMemorySchema)
def update_session_information(
    session_id: UUID4,
    data: TemporaryInfoUpdate,
    service: TemporaryMemoryService = Depends(get_memory_service),
) -> SessionMemorySchema:
    try:
        return service.update_temporary_info(
            session_id=UUID(str(session_id)),
            information=data.information,
        )
    except MemorySessionNotFound as exc:
        raise _not_found() from exc


@router.delete("/{session_id}")
def delete_session(
    session_id: UUID4,
    service: TemporaryMemoryService = Depends(get_memory_service),
) -> dict[str, str]:
    if not service.delete_session(UUID(str(session_id))):
        raise _not_found()
    return {"message": "Session memory deleted successfully"}
