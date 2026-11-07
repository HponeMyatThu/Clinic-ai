"""Base prompt template class."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BasePrompt(ABC):
    """Abstract prompt template providing versioning and rendering."""

    version: str = "1.0.0"
    name: str = "base"

    @abstractmethod
    def get_system_prompt(self) -> str:
        pass

    @abstractmethod
    def render(self, **kwargs) -> str:
        pass

