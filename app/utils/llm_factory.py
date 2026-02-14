"""
LLM Factory - creates the right LLM provider based on configuration.
Supports: Groq (free, cloud), Ollama (free, local), Claude (paid, cloud).
"""

import os
import logging
from typing import Literal

logger = logging.getLogger(__name__)

LLMProvider = Literal["groq", "ollama", "claude"]

DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"
DEFAULT_OLLAMA_MODEL = "llama3.1:8b"
DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-20250514"


def create_llm(
    provider: LLMProvider = "groq",
    model_name: str = None,
    temperature: float = 0,
    max_tokens: int = 4096,
):
    """Create an LLM instance based on provider.

    Args:
        provider: "groq" (free, cloud), "ollama" (free, local), or "claude" (paid, cloud)
        model_name: Model name override. Defaults per provider.
        temperature: Sampling temperature.
        max_tokens: Max output tokens.

    Returns:
        A LangChain chat model instance.
    """
    if provider == "groq":
        from langchain_groq import ChatGroq

        model = model_name or DEFAULT_GROQ_MODEL
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not set. Get a free key at https://console.groq.com"
            )

        logger.info(f"Using Groq: {model}")

        return ChatGroq(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
        )

    elif provider == "ollama":
        from langchain_ollama import ChatOllama

        model = model_name or DEFAULT_OLLAMA_MODEL
        logger.info(f"Using Ollama: {model}")

        return ChatOllama(
            model=model,
            temperature=temperature,
            num_predict=max_tokens,
        )

    elif provider == "claude":
        from langchain_anthropic import ChatAnthropic

        model = model_name or DEFAULT_CLAUDE_MODEL
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set.")

        logger.info(f"Using Claude: {model}")

        return ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
        )

    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'groq', 'ollama', or 'claude'.")


def detect_provider() -> LLMProvider:
    """Auto-detect which provider to use based on environment."""
    if os.getenv("GROQ_API_KEY"):
        return "groq"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "claude"
    return "ollama"
