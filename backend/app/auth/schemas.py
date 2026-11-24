import re
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, UUID4, field_validator

from app.auth.models import UserRole


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    nom: str = Field(min_length=2, max_length=50)
    prenom: str = Field(min_length=2, max_length=50)
    langue_preferee: Literal["fr", "tunisien", "arabizi"] = "fr"
    session_id: UUID4 | None = None

    @field_validator("email")
    @classmethod
    def normalize_and_validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if len(normalized) > 255 or not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("email must be a valid address")
        return normalized

    @field_validator("nom", "prenom")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not 2 <= len(normalized) <= 50:
            raise ValueError("name must contain 2 to 50 characters")
        return normalized


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)
    session_id: UUID4 | None = None

    @field_validator("email")
    @classmethod
    def normalize_and_validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if len(normalized) > 255 or not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("email must be a valid address")
        return normalized


class PublicUser(BaseModel):
    id: UUID
    nom: str
    prenom: str
    email: str
    role: UserRole
    langue_preferee: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: PublicUser
    conversation_rattachee: bool = False
