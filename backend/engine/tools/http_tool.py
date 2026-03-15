"""
HTTP Request tool - makes external API calls.
"""
import logging
import json
from typing import Any, Dict

import httpx

from backend.engine.tools.base import BaseTool

logger = logging.getLogger(__name__)


class HTTPTool(BaseTool):
    """Tool for making HTTP requests to external APIs."""

    def __init__(self, config: Dict[str, Any]):
        config.setdefault("name", "http_request")
        config.setdefault("description", "Make an HTTP request to an external API")
        super().__init__(config)

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        url = input_data.get("url") or self.config.get("url", "")
        method = (input_data.get("method") or self.config.get("method", "GET")).upper()
        headers = input_data.get("headers") or self.config.get("headers", {})
        body = input_data.get("body") or self.config.get("body")

        logger.info("HTTPTool: %s %s", method, url)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body if body and method in ("POST", "PUT", "PATCH") else None,
                    params=body if body and method == "GET" else None,
                )
                return {
                    "status_code": response.status_code,
                    "body": response.text,
                    "headers": dict(response.headers),
                }
        except Exception as e:
            logger.error("HTTPTool error: %s", str(e))
            return {"error": str(e)}

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to request"},
                    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
                    "body": {"type": "object", "description": "Request body"},
                },
                "required": ["url"],
            },
        }
