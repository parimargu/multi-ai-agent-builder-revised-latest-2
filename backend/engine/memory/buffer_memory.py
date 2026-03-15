"""
Buffer memory - short-term sliding window memory.
"""
import logging
from typing import Any, Dict, List
from collections import defaultdict

from backend.engine.memory.base import BaseMemory
from backend.config import get_config

logger = logging.getLogger(__name__)


class BufferMemory(BaseMemory):
    """In-memory sliding window buffer for short-term conversation history."""

    # Class-level storage (shared across instances within same process)
    _stores: Dict[str, List[Dict[str, str]]] = defaultdict(list)

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        app_config = get_config()
        self.window_size = config.get("window_size",
                                       app_config.get("memory.buffer_max_messages", 20))
        logger.info("BufferMemory initialized: window_size=%d", self.window_size)

    async def add_message(self, role: str, content: str, session_id: str = "default"):
        """Add a message, trimming to window size."""
        self._stores[session_id].append({"role": role, "content": content})
        # Trim to window size
        if len(self._stores[session_id]) > self.window_size:
            self._stores[session_id] = self._stores[session_id][-self.window_size:]
        logger.debug("BufferMemory: added %s message, session=%s, total=%d",
                     role, session_id, len(self._stores[session_id]))

    async def get_messages(self, session_id: str = "default") -> List[Dict[str, str]]:
        """Get messages within the window."""
        return list(self._stores.get(session_id, []))

    async def clear(self, session_id: str = "default"):
        """Clear buffer for a session."""
        self._stores.pop(session_id, None)
        logger.info("BufferMemory: cleared session=%s", session_id)
