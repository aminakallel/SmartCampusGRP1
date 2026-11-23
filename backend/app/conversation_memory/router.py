
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, status

from app.conversation_memory.schemas import (
    MessageCreate,
    SessionMemorySchema,
    TemporaryInfoUpdate,
)
from app.conversation_memory.service import TemporaryMemoryService


@lru_cache
def get_memory_service() -> TemporaryMemoryService:
    """Fournir une instance partagée du service mémoire."""
    return TemporaryMemoryService()


router = APIRouter(
    prefix="/memory/sessions",
    tags=["Temporary Memory"],
)


@router.post(
    "/{session_id}/messages",
    response_model=SessionMemorySchema,
)
def add_message(
    session_id: str,
    message: MessageCreate,
    service: TemporaryMemoryService = Depends(get_memory_service),
):
    """Ajouter un message à la mémoire d'une session."""

    return service.add_message(
        session_id=session_id,
        role=message.role,
        content=message.content,
        metadata=message.metadata,
    )


@router.get(
    "/{session_id}",
    response_model=SessionMemorySchema,
)
def get_session_memory(
    session_id: str,
    service: TemporaryMemoryService = Depends(get_memory_service),
):
    """Consulter la mémoire d'une session."""

    memory = service.get_memory(session_id)

    if memory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired",
        )

    return memory


@router.patch(
    "/{session_id}/information",
    response_model=SessionMemorySchema,
)
def update_session_information(
    session_id: str,
    data: TemporaryInfoUpdate,
    service: TemporaryMemoryService = Depends(get_memory_service),
):
    """Mettre à jour les informations temporaires."""

    return service.update_temporary_info(
        session_id=session_id,
        information=data.information,
    )


@router.delete("/{session_id}")
def delete_session(
    session_id: str,
    service: TemporaryMemoryService = Depends(get_memory_service),
):
    """Supprimer la mémoire d'une session."""

    deleted = service.delete_session(session_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return {"message": "Session deleted successfully"}
