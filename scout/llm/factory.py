"""LLM provider factory."""

import os
import logging
from scout.llm.base import BaseLLMProvider
from scout.llm.anthropic_provider import AnthropicProvider
from scout.llm.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


def get_llm_provider() -> BaseLLMProvider:
    """
    Get LLM provider based on PROVIDER environment variable.

    Returns:
        Configured LLM provider instance

    Raises:
        ValueError: If provider is unknown or credentials are missing
    """
    provider = os.getenv("PROVIDER", "anthropic").lower()

    if provider == "anthropic":
        logger.info("Using Anthropic provider")
        return AnthropicProvider()
    elif provider == "openai":
        logger.info("Using OpenAI provider")
        return OpenAIProvider()
    else:
        raise ValueError(
            f"Unknown provider: {provider}. Must be 'anthropic' or 'openai'"
        )
