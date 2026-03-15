"""
Output node - formats and sends final output.
"""
import logging
import json
from typing import Any, Dict
from backend.engine.nodes.base import BaseNode

logger = logging.getLogger(__name__)


class OutputNode(BaseNode):
    """Output node that formats the final response."""

    async def execute(self, input_data: Dict[str, Any],
                      context: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("OutputNode [%s]: formatting output", self.label)

        output_format = self.config.get("format", "text")

        if output_format == "json":
            return {"output": input_data, "format": "json"}
        else:
            message = input_data.get("message", "")
            if not message and isinstance(input_data, dict):
                message = json.dumps(input_data, indent=2)
            return {"output": message, "format": "text"}
