"""Custom exceptions for Ollama service communication."""

from __future__ import annotations


class OllamaException(Exception):
    """Base exception for all Ollama errors."""
    pass


class OllamaConnectionError(OllamaException):
    """Cannot connect to local Ollama instance."""
    pass


class OllamaTimeoutError(OllamaException):
    """Ollama inference request exceeded timeout."""
    pass


class OllamaModelNotFoundError(OllamaException):
    """Requested model is not downloaded or available in Ollama."""
    pass


class OllamaInvalidResponseError(OllamaException):
    """Ollama output could not be parsed as valid JSON."""
    pass


class OllamaServiceUnavailableError(OllamaException):
    """Ollama daemon is stopped or unhealthy."""
    pass

