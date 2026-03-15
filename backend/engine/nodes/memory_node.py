"""
Memory node - provides memory configuration.
"""
import logging
from typing import Any, Dict
from backend.engine.nodes.base import BaseNode

logger = logging.getLogger(__name__)


class MemoryNode(BaseNode):
    """Memory node - provides memory configuration to parent agent node."""

    async def execute(self, input_data: Dict[str, Any],
                      context: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("MemoryNode [%s]: sub_type=%s", self.label, self.sub_type)
        return {
            "sub_type": self.sub_type,
            "config": self.config,
        }
