"""
Code execution tool - runs Python code snippets.
"""
import logging
import io
import sys
import traceback
from typing import Any, Dict

from backend.engine.tools.base import BaseTool

logger = logging.getLogger(__name__)


class CodeTool(BaseTool):
    """Tool for executing Python code snippets safely."""

    def __init__(self, config: Dict[str, Any]):
        config.setdefault("name", "code_executor")
        config.setdefault("description", "Execute Python code and return output")
        super().__init__(config)

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        code = input_data.get("code") or self.config.get("code", "")
        if not code:
            return {"error": "No code provided"}

        logger.info("CodeTool: executing code (%d chars)", len(code))

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured = io.StringIO()

        try:
            exec_globals = {"__builtins__": __builtins__}
            exec(code, exec_globals)
            output = captured.getvalue()
            result = exec_globals.get("result", output)
            return {"output": str(result), "stdout": output}
        except Exception as e:
            logger.error("CodeTool error: %s", str(e))
            return {"error": str(e), "traceback": traceback.format_exc()}
        finally:
            sys.stdout = old_stdout

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute"},
                },
                "required": ["code"],
            },
        }
