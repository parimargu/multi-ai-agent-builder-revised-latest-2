"""
AI Agent node - orchestrates LLM, memory, and tools.
"""
import json
import logging
from typing import Any, Dict, List

from backend.engine.nodes.base import BaseNode
from backend.engine.node_registry import get_llm_provider, get_memory_provider, get_tool_provider

logger = logging.getLogger(__name__)


class AgentNode(BaseNode):
    """AI Agent node that orchestrates LLM, memory, and tools."""

    async def execute(self, input_data: Dict[str, Any],
                      context: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("AgentNode [%s]: executing, sub_type=%s", self.label, self.sub_type)

        system_prompt = self.config.get("system_prompt", "You are a helpful AI assistant.")
        max_iterations = self.config.get("max_iterations", 5)

        # Get sub-node configurations from context
        llm_config = context.get("sub_nodes", {}).get("model", {})
        memory_config = context.get("sub_nodes", {}).get("memory", {})
        tool_configs = context.get("sub_nodes", {}).get("tools", [])

        # Initialize LLM
        llm_sub_type = llm_config.get("sub_type", "openai_chat")
        llm = get_llm_provider(llm_sub_type, llm_config.get("config", {}))

        # Initialize memory (optional)
        memory = None
        if memory_config:
            mem_sub_type = memory_config.get("sub_type", "buffer_memory")
            memory = get_memory_provider(mem_sub_type, {
                **memory_config.get("config", {}),
                "agent_id": context.get("agent_id"),
            })

        # Initialize tools
        tools = []
        for tc in tool_configs:
            try:
                tool = get_tool_provider(tc.get("sub_type", ""), tc.get("config", {}))
                tools.append(tool)
            except ValueError as e:
                logger.warning("Skipping unknown tool: %s", e)

        # Build messages
        messages = [{"role": "system", "content": system_prompt}]

        # Add memory history
        if memory:
            session_id = context.get("session_id", "default")
            history = await memory.get_messages(session_id)
            messages.extend(history)

        # Add current input
        user_message = input_data.get("message") or input_data.get("data", {}).get("message", "")
        if isinstance(user_message, dict):
            user_message = json.dumps(user_message)
        if not user_message:
            user_message = json.dumps(input_data)

        messages.append({"role": "user", "content": str(user_message)})

        # Agent loop with tools
        final_response = ""
        for iteration in range(max_iterations):
            logger.debug("AgentNode iteration %d/%d", iteration + 1, max_iterations)

            if tools:
                tool_schemas = [t.get_schema() for t in tools]
                result = await llm.chat_with_tools(messages, tool_schemas)

                if result.get("tool_calls"):
                    # Execute tool calls
                    for tc in result["tool_calls"]:
                        tool_name = tc["name"]
                        try:
                            args = json.loads(tc["arguments"]) if isinstance(tc["arguments"], str) else tc["arguments"]
                        except json.JSONDecodeError:
                            args = {}

                        # Find matching tool
                        tool_result = {"error": f"Tool '{tool_name}' not found"}
                        for t in tools:
                            if t.name == tool_name:
                                tool_result = await t.execute(args)
                                break

                        messages.append({"role": "assistant", "content": json.dumps({"tool_call": tc})})
                        messages.append({"role": "user", "content": f"Tool result: {json.dumps(tool_result)}"})

                    continue  # Loop back for next iteration
                else:
                    final_response = result.get("content", "")
                    break
            else:
                final_response = await llm.chat(messages)
                break
        else:
            final_response = await llm.chat(messages)

        # Save to memory
        if memory:
            session_id = context.get("session_id", "default")
            await memory.add_message("user", str(user_message), session_id)
            await memory.add_message("assistant", final_response, session_id)

        logger.info("AgentNode [%s]: completed, response=%d chars", self.label, len(final_response))

        return {
            "message": final_response,
            "iterations": iteration + 1 if 'iteration' in dir() else 1,
        }
