"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate_structured(self, prompt: str, response_model: Type[T], max_retries: int = 2) -> T:
        """
        Generate structured output with automatic validation and retry.

        Args:
            prompt: The prompt to send to the LLM
            response_model: Pydantic model for the expected response
            max_retries: Maximum number of retries on validation errors

        Returns:
            Validated instance of response_model
        """
        pass

    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        """
        Generate unstructured text output.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            Generated text response
        """
        pass
