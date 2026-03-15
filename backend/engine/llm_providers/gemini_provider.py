"""
Google Gemini LLM provider implementation.
"""
import logging
import json
from typing import Any, Dict, List

from backend.engine.llm_providers.base import BaseLLMProvider
from backend.config import get_config

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider."""

    def __init__(self, config: Dict[str, Any]):
        app_config = get_config()
        provider_config = app_config.llm_provider_config("gemini")
        merged = {**provider_config, **config}
        super().__init__(merged)
        self.api_key = merged.get("api_key", "")
        if not self.model:
            self.model = merged.get("default_model", "gemini-2.0-flash")

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        logger.info("Gemini chat: model=%s, messages=%d", self.model, len(messages))

        model = genai.GenerativeModel(self.model)

        # Convert messages to Gemini format
        gemini_messages = []
        for msg in messages:
            role = "user" if msg["role"] in ("user", "system") else "model"
            gemini_messages.append({"role": role, "parts": [msg["content"]]})

        response = model.generate_content(
            gemini_messages,
            generation_config=genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            ),
        )
        result = response.text or ""
        logger.debug("Gemini response: %s chars", len(result))
        return result

    async def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        **kwargs,
    ) -> Dict[str, Any]:
        # Gemini tool calling - simplified version
        response = await self.chat(messages)
        return {"content": response, "tool_calls": []}
