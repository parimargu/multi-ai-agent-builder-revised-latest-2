"""
LLM node - passes through model configuration.
"""
import logging
from typing import Any, Dict

from backend.engine.nodes.base import BaseNode

logger = logging.getLogger(__name__)


class LLMNode(BaseNode):
    """LLM model node - provides model configuration to parent agent node."""

    async def execute(self, input_data: Dict[str, Any],
                      context: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("LLMNode [%s]: sub_type=%s", self.label, self.sub_type)
        return {
            "sub_type": self.sub_type,
            "config": self.config,
            "model": self.config.get("model", ""),
        }
