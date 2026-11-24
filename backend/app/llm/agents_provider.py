
import httpx

from app.llm.providers import LLMProvider


class AgentsServiceProvider(LLMProvider):
    """Provider qui communique avec le service Agents via HTTP."""

    def __init__(
        self,
        base_url: str,
        endpoint: str = "/agent/chat",
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        self.transport = transport

    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(
            timeout=30.0,
            transport=self.transport,
        ) as client:
            response = await client.post(
                self.url,
                json={"prompt": prompt},
            )
            response.raise_for_status()

        data = response.json()
        result = data.get("response")

        if not isinstance(result, str):
            raise ValueError("Invalid response from Agents Service")

        return result
