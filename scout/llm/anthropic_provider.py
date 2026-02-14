"""Anthropic LLM provider implementation."""

import os
import logging
from typing import Type, TypeVar
from pydantic import BaseModel
import instructor
from anthropic import Anthropic

from scout.llm.base import BaseLLMProvider

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude implementation."""

    def __init__(self, api_key: str = None, model: str = "claude-haiku-4-5"):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key (or read from ANTHROPIC_API_KEY env var)
            model: Model to use (default: claude-3-5-sonnet-20241022)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set")

        self.model = model
        self.client = instructor.from_anthropic(Anthropic(api_key=self.api_key))
        logger.info(f"Initialized Anthropic provider with model {model}")

    def generate_structured(
        self, prompt: str, response_model: Type[T], max_retries: int = 2
    ) -> T:
        """Generate structured output with automatic validation."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
                response_model=response_model,
                max_retries=max_retries,
            )
            logger.debug(f"Successfully generated {response_model.__name__}")
            return response
        except Exception as e:
            logger.error(f"Error generating structured output: {e}")
            raise

    def generate_text(self, prompt: str) -> str:
        """Generate unstructured text output."""
        try:
            client = Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text
            logger.debug("Successfully generated text response")
            return text
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise
