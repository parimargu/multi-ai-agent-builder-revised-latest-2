"""
OpenRouter LLM provider implementation.
Uses OpenAI-compatible API.
"""
import logging
from typing import Any, Dict, List

from backend.engine.llm_providers.openai_provider import OpenAIProvider
from backend.config import get_config

logger = logging.getLogger(__name__)


class OpenRouterProvider(OpenAIProvider):
    """OpenRouter API provider - OpenAI compatible."""

    def __init__(self, config: Dict[str, Any]):
        app_config = get_config()
        provider_config = app_config.llm_provider_config("openrouter")
        merged = {**provider_config, **config}
        if "base_url" not in merged:
            merged["base_url"] = "https://openrouter.ai/api/v1"
        if not merged.get("model"):
            merged["model"] = merged.get("default_model", "meta-llama/llama-3.3-70b-instruct")
        super().__init__(merged)
        logger.info("OpenRouterProvider initialized: model=%s", self.model)
