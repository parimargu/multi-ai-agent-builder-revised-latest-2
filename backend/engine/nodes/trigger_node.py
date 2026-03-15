"""
Trigger nodes - start workflow execution.
"""
import logging
from typing import Any, Dict

from backend.engine.nodes.base import BaseNode

logger = logging.getLogger(__name__)


class TriggerNode(BaseNode):
    """Trigger node that initiates workflow execution."""

    async def execute(self, input_data: Dict[str, Any],
                      context: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("TriggerNode [%s]: type=%s", self.label, self.sub_type)

        # Pass through the execution input data
        output = {
            "trigger_type": self.sub_type,
            "data": input_data,
            "message": input_data.get("message", ""),
        }

        return output
