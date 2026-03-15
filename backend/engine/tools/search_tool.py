"""
Web search tool.
"""
import logging
from typing import Any, Dict

import httpx

from backend.engine.tools.base import BaseTool

logger = logging.getLogger(__name__)


class SearchTool(BaseTool):
    """Tool for performing web searches."""

    def __init__(self, config: Dict[str, Any]):
        config.setdefault("name", "web_search")
        config.setdefault("description", "Search the web for information")
        super().__init__(config)

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        query = input_data.get("query", "")
        logger.info("SearchTool: query='%s'", query)

        # Using a simple DuckDuckGo-style search
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers={"User-Agent": "AgentForge/1.0"},
                )
                return {
                    "query": query,
                    "results": response.text[:2000],  # Truncate for safety
                    "status": "success",
                }
        except Exception as e:
            logger.error("SearchTool error: %s", str(e))
            return {"error": str(e), "query": query}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["query"],
            },
        }
