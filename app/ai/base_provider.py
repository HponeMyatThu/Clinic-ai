"""Abstract AI Provider interface supporting pluggable backends (Ollama, etc.)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, Field


class AIResponse(BaseModel):
    """Standardized response from any AI provider."""

    raw_text: str
    parsed_json: dict[str, Any] | list[Any] | None = None
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    duration_ms: float = 0.0


class BaseAIProvider(ABC):
    """Abstract interface for local or cloud AI model inference."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> AIResponse:
        """Generate response given user prompt and optional system prompt."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if AI engine is responsive."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return configured model identifier."""
        pass

