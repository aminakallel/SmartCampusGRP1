
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MessageSchema(BaseModel):
    """Message échangé pendant une conversation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: dict = Field(default_factory=dict)


class SessionMemorySchema(BaseModel):
    """Mémoire temporaire associée à une session."""

    model_config = ConfigDict(str_strip_whitespace=True)

    session_id: str = Field(min_length=1)
    messages: list[MessageSchema] = Field(default_factory=list)
    temporary_info: dict = Field(default_factory=dict)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    expires_at: datetime

class MessageCreate(BaseModel):
    """Données reçues pour ajouter un message."""

    model_config = ConfigDict(str_strip_whitespace=True)

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)
    metadata: dict = Field(default_factory=dict)


class TemporaryInfoUpdate(BaseModel):
    """Données reçues pour mettre à jour les informations temporaires."""

    information: dict = Field(default_factory=dict)
