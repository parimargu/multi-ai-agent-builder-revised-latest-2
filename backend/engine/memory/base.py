"""
Base memory interface.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BaseMemory(ABC):
    """Abstract base class for memory providers."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    async def add_message(self, role: str, content: str, session_id: str = "default"):
        """Add a message to memory."""
        pass

    @abstractmethod
    async def get_messages(self, session_id: str = "default") -> List[Dict[str, str]]:
        """Retrieve conversation history."""
        pass

    @abstractmethod
    async def clear(self, session_id: str = "default"):
        """Clear memory for a session."""
        pass
