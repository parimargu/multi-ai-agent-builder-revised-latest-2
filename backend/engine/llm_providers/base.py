"""
Base LLM provider interface.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get("model", "")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 4096)

    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Send messages and get a response."""
        pass

    @abstractmethod
    async def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """Chat with tool-calling support. Returns response with optional tool calls."""
        pass

    def _format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Ensure messages are in standard format."""
        formatted = []
        for msg in messages:
            formatted.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })
        return formatted
