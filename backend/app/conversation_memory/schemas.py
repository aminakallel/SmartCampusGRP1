from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, UUID4, model_validator


class MessageSchema(BaseModel):
    """Message conservé dans la mémoire temporaire SA-26."""

    model_config = ConfigDict(str_strip_whitespace=True)

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, object] = Field(default_factory=dict)


class SessionMemorySchema(BaseModel):
    """Mémoire liée aux identifiants et à l'expiration d'une session SA-25."""

    model_config = ConfigDict(str_strip_whitespace=True)

    session_id: UUID4
    conversation_id: str = Field(min_length=1)
    messages: list[MessageSchema] = Field(default_factory=list)
    temporary_info: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    account_id: UUID | None = None
    attached_at: datetime | None = None

    @model_validator(mode="after")
    def validate_attachment_and_timestamps(self):
        for name in ("created_at", "expires_at"):
            value = getattr(self, name)
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError(f"{name} must be timezone-aware")
        if (self.account_id is None) != (self.attached_at is None):
            raise ValueError("account_id and attached_at must be set together")
        if self.attached_at is not None and (
            self.attached_at.tzinfo is None or self.attached_at.utcoffset() is None
        ):
            raise ValueError("attached_at must be timezone-aware")
        return self


class MessageCreate(BaseModel):
    """Données reçues pour ajouter un message."""

    model_config = ConfigDict(str_strip_whitespace=True)

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)
    metadata: dict[str, object] = Field(default_factory=dict)


class TemporaryInfoUpdate(BaseModel):
    information: dict[str, object] = Field(default_factory=dict)
