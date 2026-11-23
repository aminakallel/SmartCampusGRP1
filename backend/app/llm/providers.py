
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Interface commune pour tous les fournisseurs LLM."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """
        Générer une réponse à partir d'un prompt.

        Args:
            prompt: Le message envoyé au modèle.

        Returns:
            La réponse générée par le modèle.
        """
        pass
