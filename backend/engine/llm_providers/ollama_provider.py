"""
Ollama LLM provider implementation.
Uses OpenAI-compatible API for local models.
"""
import logging
from typing import Any, Dict, List

from backend.engine.llm_providers.openai_provider import OpenAIProvider
from backend.config import get_config

logger = logging.getLogger(__name__)


class OllamaProvider(OpenAIProvider):
    """Ollama local LLM provider - OpenAI compatible API."""

    def __init__(self, config: Dict[str, Any]):
        app_config = get_config()
        provider_config = app_config.llm_provider_config("ollama")
        merged = {**provider_config, **config}
        if "base_url" not in merged:
            merged["base_url"] = "http://localhost:11434/v1"
        if not merged.get("model"):
            merged["model"] = merged.get("default_model", "llama3.2")
        merged["api_key"] = "ollama"  # Ollama doesn't need a real key
        super().__init__(merged)
        logger.info("OllamaProvider initialized: model=%s, base_url=%s", self.model, self.base_url)
