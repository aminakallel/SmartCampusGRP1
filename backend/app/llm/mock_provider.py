
from app.llm.providers import LLMProvider


class MockLLMProvider(LLMProvider):
    """Fournisseur LLM simulé pour les tests."""

    async def generate(self, prompt: str) -> str:
        return f"Mock response: {prompt}"
