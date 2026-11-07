"""AI integration layer."""

from app.ai.base_provider import BaseAIProvider, AIResponse
from app.ai.ollama.client import OllamaClient
from app.ai.ollama.model_config import OllamaModelConfig

__all__ = ["BaseAIProvider", "AIResponse", "OllamaClient", "OllamaModelConfig"]

