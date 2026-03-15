"""
Groq LLM provider implementation.
Uses OpenAI-compatible API.
"""
import logging
from typing import Any, Dict, List

from backend.engine.llm_providers.openai_provider import OpenAIProvider
from backend.config import get_config

logger = logging.getLogger(__name__)


class GroqProvider(OpenAIProvider):
    """Groq API provider - OpenAI compatible."""

    def __init__(self, config: Dict[str, Any]):
        app_config = get_config()
        provider_config = app_config.llm_provider_config("groq")
        merged = {**provider_config, **config}
        # Ensure groq-specific defaults
        if "base_url" not in merged:
            merged["base_url"] = "https://api.groq.com/openai/v1"
        if not merged.get("model"):
            merged["model"] = merged.get("default_model", "llama-3.3-70b-versatile")
        super().__init__(merged)
        logger.info("GroqProvider initialized: model=%s", self.model)
