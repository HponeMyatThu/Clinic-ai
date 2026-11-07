"""Ollama AI Client implementing BaseAIProvider with structured JSON and retries."""

from __future__ import annotations

import json
import time
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.ai.base_provider import AIResponse, BaseAIProvider
from app.ai.ollama.connection import OllamaConnectionManager
from app.ai.ollama.exceptions import (
    OllamaConnectionError,
    OllamaInvalidResponseError,
    OllamaModelNotFoundError,
    OllamaServiceUnavailableError,
    OllamaTimeoutError,
)
from app.ai.ollama.model_config import OllamaModelConfig


class OllamaClient(BaseAIProvider):
    """High-performance async Ollama client with retry and error handling."""

    def __init__(self, config: OllamaModelConfig) -> None:
        self.config = config
        self.connection = OllamaConnectionManager(config)

    def get_model_name(self) -> str:
        return self.config.model

    async def health_check(self) -> bool:
        """Ping Ollama API to ensure daemon is active."""
        try:
            client = await self.connection.get_client()
            resp = await client.get("/api/tags", timeout=3.0)
            return resp.status_code == 200
        except Exception:
            return False

    async def list_available_models(self) -> list[str]:
        """Fetch list of models currently loaded in Ollama."""
        try:
            client = await self.connection.get_client()
            resp = await client.get("/api/tags", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                return [m.get("name", "") for m in data.get("models", [])]
            return []
        except Exception:
            return []

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> AIResponse:
        """Call Ollama /api/generate with retry and JSON decoding."""
        client = await self.connection.get_client()

        payload: dict[str, Any] = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else self.config.temperature,
                "num_predict": max_tokens or self.config.max_tokens,
            },
        }

        if system_prompt:
            payload["system"] = system_prompt

        if json_mode:
            payload["format"] = "json"

        start_time = time.perf_counter()

        try:
            resp = await client.post("/api/generate", json=payload)
        except httpx.ConnectError as exc:
            raise OllamaConnectionError(f"Cannot reach Ollama at {self.config.base_url}") from exc
        except httpx.TimeoutException as exc:
            raise OllamaTimeoutError(f"Ollama request exceeded timeout of {self.config.timeout}s") from exc
        except Exception as exc:
            raise OllamaServiceUnavailableError(f"Ollama communication failed: {exc}") from exc

        duration_ms = (time.perf_counter() - start_time) * 1000

        if resp.status_code == 404:
            raise OllamaModelNotFoundError(f"Model '{self.config.model}' not found in Ollama.")
        elif resp.status_code != 200:
            raise OllamaServiceUnavailableError(f"Ollama returned HTTP {resp.status_code}: {resp.text}")

        res_json = resp.json()
        raw_text = res_json.get("response", "").strip()

        parsed_json = None
        if json_mode:
            try:
                # Strip markdown code blocks if model wrapped it
                cleaned = raw_text
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                elif cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                parsed_json = json.loads(cleaned.strip())
            except json.JSONDecodeError as exc:
                raise OllamaInvalidResponseError(f"Model response was not valid JSON: {raw_text[:200]}") from exc

        return AIResponse(
            raw_text=raw_text,
            parsed_json=parsed_json,
            model=self.config.model,
            prompt_tokens=res_json.get("prompt_eval_count"),
            completion_tokens=res_json.get("eval_count"),
            duration_ms=round(duration_ms, 2),
        )

    async def close(self) -> None:
        await self.connection.close()

