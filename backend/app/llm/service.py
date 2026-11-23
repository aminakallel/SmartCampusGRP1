

import asyncio

from app.core.errors import AppError
from app.llm.providers import LLMProvider


class LLMService:
    """Service responsable de la génération des réponses LLM."""

    def __init__(self, provider: LLMProvider, timeout_seconds: float = 30.0):
        self.provider = provider
        self.timeout_seconds = timeout_seconds

    async def generate_response(self, prompt: str) -> str:
        try:
            return await asyncio.wait_for(
                self.provider.generate(prompt),
                timeout=self.timeout_seconds,
            )

        except asyncio.TimeoutError as exc:
            raise AppError(
                504,
                "LLM_TIMEOUT",
                "Le fournisseur LLM n'a pas répondu à temps",
            ) from exc

        except Exception as exc:
            raise AppError(
                502,
                "LLM_PROVIDER_ERROR",
                "Une erreur est survenue lors de la communication avec le fournisseur LLM",
            ) from exc
