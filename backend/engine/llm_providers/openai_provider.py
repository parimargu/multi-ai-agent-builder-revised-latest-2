"""
OpenAI LLM provider implementation.
"""
import logging
from typing import Any, Dict, List, Optional

from backend.engine.llm_providers.base import BaseLLMProvider
from backend.config import get_config

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider (GPT-4o, GPT-4o-mini, etc.)."""

    def __init__(self, config: Dict[str, Any]):
        app_config = get_config()
        provider_config = app_config.llm_provider_config("openai")
        merged = {**provider_config, **config}
        super().__init__(merged)
        self.api_key = merged.get("api_key", "")
        self.base_url = merged.get("base_url", "https://api.openai.com/v1")
        if not self.model:
            self.model = merged.get("default_model", "gpt-4o-mini")

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        import openai
        client = openai.AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        logger.info("OpenAI chat: model=%s, messages=%d", self.model, len(messages))

        response = await client.chat.completions.create(
            model=self.model,
            messages=self._format_messages(messages),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **kwargs,
        )
        result = response.choices[0].message.content or ""
        logger.debug("OpenAI response: %s chars", len(result))
        return result

    async def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        **kwargs,
    ) -> Dict[str, Any]:
        import openai
        client = openai.AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        logger.info("OpenAI chat_with_tools: model=%s, tools=%d", self.model, len(tools))

        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {"type": "object", "properties": {}}),
                },
            })

        response = await client.chat.completions.create(
            model=self.model,
            messages=self._format_messages(messages),
            tools=openai_tools if openai_tools else None,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **kwargs,
        )

        choice = response.choices[0]
        result = {
            "content": choice.message.content or "",
            "tool_calls": [],
        }

        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                result["tool_calls"].append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                })

        return result
