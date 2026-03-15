"""
Condition node - If/Else and Switch routing.
"""
import logging
import json
from typing import Any, Dict
from backend.engine.nodes.base import BaseNode

logger = logging.getLogger(__name__)


class ConditionNode(BaseNode):
    """Condition node for if/else or switch-based flow control."""

    async def execute(self, input_data: Dict[str, Any],
                      context: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("ConditionNode [%s]: sub_type=%s", self.label, self.sub_type)

        condition = self.config.get("condition", "")
        result = False

        try:
            # Simple expression evaluation
            eval_globals = {"data": input_data, "json": json}
            result = bool(eval(condition, eval_globals)) if condition else True
        except Exception as e:
            logger.warning("Condition evaluation error: %s", str(e))

        return {
            "result": result,
            "branch": "true" if result else "false",
            "data": input_data,
        }
