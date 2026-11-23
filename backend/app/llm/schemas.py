
from pydantic import BaseModel, Field


class LLMGenerateRequest(BaseModel):
    """Données reçues par l'API pour générer une réponse."""

    prompt: str = Field(min_length=1, max_length=4000)


class LLMGenerateResponse(BaseModel):
    """Réponse retournée par l'API."""

    response: str
