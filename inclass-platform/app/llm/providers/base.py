"""Provider-agnostic LLM interface."""

from abc import ABCMeta, abstractmethod
from typing import Any, Dict, List, Optional


class LLMProviderError(RuntimeError):
    """Raised for provider call/setup failures."""


class LLMProvider(metaclass=ABCMeta):
    """Abstract base interface for model providers."""

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 400,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Return assistant text generated from messages."""
        raise NotImplementedError
