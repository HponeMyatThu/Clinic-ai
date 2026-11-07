"""Ollama configuration and hyperparameters."""

from __future__ import annotations

from dataclasses import dataclass
from app.config import Settings


@dataclass(frozen=True)
class OllamaModelConfig:
    """Immutable Ollama configuration."""

    base_url: str
    model: str
    temperature: float = 0.0
    max_tokens: int = 4096
    timeout: int = 120
    max_retries: int = 3

    @classmethod
    def from_settings(cls, settings: Settings) -> OllamaModelConfig:
        return cls(
            base_url=settings.ollama_base_url.rstrip("/"),
            model=settings.ollama_model,
            temperature=settings.ai_temperature,
            max_tokens=settings.ai_max_tokens,
            timeout=settings.ollama_timeout,
            max_retries=settings.ollama_max_retries,
        )

