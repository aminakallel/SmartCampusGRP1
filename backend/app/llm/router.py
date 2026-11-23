
from functools import lru_cache

from fastapi import APIRouter, Depends

from app.llm.mock_provider import MockLLMProvider
from app.llm.schemas import LLMGenerateRequest, LLMGenerateResponse
from app.llm.service import LLMService
from app.core.config import get_settings


router = APIRouter(
    prefix="/llm",
    tags=["LLM"],
)


@lru_cache
def get_llm_service() -> LLMService:
    """Fournir une instance partagée du service LLM."""
    settings = get_settings()

    return LLMService(
        provider=MockLLMProvider(),
        timeout_seconds=settings.llm_timeout_seconds,
    )


@router.post(
    "/generate",
    response_model=LLMGenerateResponse,
    summary="Generate a response using the LLM",
)
async def generate_response(
    request: LLMGenerateRequest,
    service: LLMService = Depends(get_llm_service),
) -> LLMGenerateResponse:
    response = await service.generate_response(request.prompt)

    return LLMGenerateResponse(response=response)
