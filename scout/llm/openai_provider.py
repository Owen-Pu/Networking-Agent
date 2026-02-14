"""OpenAI LLM provider implementation."""

import os
import logging
from typing import Type, TypeVar
from pydantic import BaseModel
import instructor
from openai import OpenAI

from scout.llm.base import BaseLLMProvider

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT implementation."""

    def __init__(self, api_key: str = None, model: str = "gpt-4o"):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (or read from OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4o)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be set")

        self.model = model
        self.client = instructor.from_openai(OpenAI(api_key=self.api_key))
        logger.info(f"Initialized OpenAI provider with model {model}")

    def generate_structured(
        self, prompt: str, response_model: Type[T], max_retries: int = 2
    ) -> T:
        """Generate structured output with automatic validation."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
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
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.choices[0].message.content
            logger.debug("Successfully generated text response")
            return text
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise
