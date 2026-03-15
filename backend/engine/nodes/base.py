"""
Base node interface.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class BaseNode(ABC):
    """Abstract base class for workflow nodes."""

    def __init__(self, node_id: str, node_type: str, sub_type: str,
                 label: str, config: Dict[str, Any]):
        self.node_id = node_id
        self.node_type = node_type
        self.sub_type = sub_type
        self.label = label
        self.config = config

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any],
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the node logic.

        Args:
            input_data: Data from upstream node(s)
            context: Shared execution context (memory, llm, tools, etc.)

        Returns:
            Output data to pass downstream
        """
        pass
