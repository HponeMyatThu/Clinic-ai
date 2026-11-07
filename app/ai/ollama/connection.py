"""Connection manager for Ollama HTTP communication."""

from __future__ import annotations

import httpx
from app.ai.ollama.model_config import OllamaModelConfig


class OllamaConnectionManager:
    """Manages persistent connection pooling to local Ollama daemon."""

    def __init__(self, config: OllamaModelConfig) -> None:
        self.config = config
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or initialize the persistent async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(self.config.timeout, connect=5.0),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            )
        return self._client

    async def close(self) -> None:
        """Close connection pool."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

