"""
Base tool interface.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """Abstract base class for agent tools."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get("name", self.__class__.__name__)
        self.description = config.get("description", "")

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool and return results."""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Return OpenAI-compatible function schema."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {"type": "object", "properties": {}},
        }
