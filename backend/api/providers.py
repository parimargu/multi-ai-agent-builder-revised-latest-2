"""
Provider information API routes: available LLMs, tools, memory types.
"""
import logging
from typing import Any, Dict, List
from fastapi import APIRouter, Depends

from backend.core.dependencies import get_current_user
from backend.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/providers", tags=["Providers"])


@router.get("/node-types")
async def get_node_types(current_user: User = Depends(get_current_user)):
    """Get all available node types for the workflow builder."""
    return {
        "node_types": [
            {
                "type": "trigger",
                "label": "Triggers",
                "icon": "⚡",
                "sub_types": [
                    {"id": "manual_trigger", "label": "Manual Trigger", "icon": "▶️",
                     "description": "Manually start a workflow", "ports": {"output": ["output"]}},
                    {"id": "webhook_trigger", "label": "Webhook", "icon": "🔗",
                     "description": "Trigger via HTTP webhook", "ports": {"output": ["output"]},
                     "config_schema": {"url_path": "string", "method": "string"}},
                    {"id": "chat_trigger", "label": "Chat Message", "icon": "💬",
                     "description": "When chat message received", "ports": {"output": ["output"]}},
                    {"id": "schedule_trigger", "label": "Schedule", "icon": "⏰",
                     "description": "Run on a schedule", "ports": {"output": ["output"]},
                     "config_schema": {"cron": "string"}},
                ]
            },
            {
                "type": "agent",
                "label": "AI Agents",
                "icon": "🤖",
                "sub_types": [
                    {"id": "tools_agent", "label": "AI Agent", "icon": "🤖",
                     "description": "Tools Agent - Uses tools to accomplish tasks",
                     "ports": {"input": ["input"], "output": ["output"],
                              "sub_input": ["model", "memory", "tool", "output_parser"]},
                     "config_schema": {"system_prompt": "text", "max_iterations": "number"}},
                    {"id": "conversational_agent", "label": "Conversational Agent", "icon": "💭",
                     "description": "Agent for multi-turn conversations",
                     "ports": {"input": ["input"], "output": ["output"],
                              "sub_input": ["model", "memory"]},
                     "config_schema": {"system_prompt": "text"}},
                ]
            },
            {
                "type": "llm",
                "label": "LLM Models",
                "icon": "🧠",
                "sub_types": [
                    {"id": "openai_chat", "label": "OpenAI Chat Model", "icon": "🟢",
                     "description": "GPT-4o, GPT-4o-mini, etc.",
                     "ports": {"output": ["model"]},
                     "config_schema": {"model": "string", "temperature": "number", "max_tokens": "number"}},
                    {"id": "gemini_chat", "label": "Google Gemini", "icon": "🔵",
                     "description": "Gemini Pro, Gemini Flash",
                     "ports": {"output": ["model"]},
                     "config_schema": {"model": "string", "temperature": "number"}},
                    {"id": "groq_chat", "label": "Groq", "icon": "🟠",
                     "description": "Llama, Mixtral on Groq",
                     "ports": {"output": ["model"]},
                     "config_schema": {"model": "string", "temperature": "number"}},
                    {"id": "openrouter_chat", "label": "OpenRouter", "icon": "🟣",
                     "description": "Access multiple models via OpenRouter",
                     "ports": {"output": ["model"]},
                     "config_schema": {"model": "string", "temperature": "number"}},
                    {"id": "ollama_chat", "label": "Ollama (Local)", "icon": "🦙",
                     "description": "Local LLM via Ollama",
                     "ports": {"output": ["model"]},
                     "config_schema": {"model": "string", "base_url": "string", "temperature": "number"}},
                ]
            },
            {
                "type": "memory",
                "label": "Memory",
                "icon": "💾",
                "sub_types": [
                    {"id": "buffer_memory", "label": "Window Buffer Memory", "icon": "📋",
                     "description": "Short-term sliding window memory",
                     "ports": {"output": ["memory"]},
                     "config_schema": {"window_size": "number"}},
                    {"id": "persistent_memory", "label": "Persistent Memory", "icon": "🗄️",
                     "description": "Long-term database-backed memory",
                     "ports": {"output": ["memory"]},
                     "config_schema": {"session_id": "string"}},
                ]
            },
            {
                "type": "tool",
                "label": "Tools",
                "icon": "🔧",
                "sub_types": [
                    {"id": "http_request", "label": "HTTP Request", "icon": "🌐",
                     "description": "Make HTTP API calls",
                     "ports": {"output": ["tool"]},
                     "config_schema": {"url": "string", "method": "string", "headers": "json", "body": "json"}},
                    {"id": "code_executor", "label": "Code Executor", "icon": "💻",
                     "description": "Execute Python code",
                     "ports": {"output": ["tool"]},
                     "config_schema": {"code": "text", "language": "string"}},
                    {"id": "search_web", "label": "Web Search", "icon": "🔍",
                     "description": "Search the web",
                     "ports": {"output": ["tool"]},
                     "config_schema": {"api_key": "string"}},
                    {"id": "custom_function", "label": "Custom Function", "icon": "⚙️",
                     "description": "Define a custom tool function",
                     "ports": {"output": ["tool"]},
                     "config_schema": {"function_name": "string", "description": "text", "code": "text"}},
                ]
            },
            {
                "type": "condition",
                "label": "Flow Control",
                "icon": "🔀",
                "sub_types": [
                    {"id": "if_condition", "label": "If/Else", "icon": "🔀",
                     "description": "Conditional branching",
                     "ports": {"input": ["input"], "output": ["true", "false"]},
                     "config_schema": {"condition": "text"}},
                    {"id": "switch_condition", "label": "Switch", "icon": "🔀",
                     "description": "Multi-way branching",
                     "ports": {"input": ["input"], "output": ["case1", "case2", "case3", "default"]},
                     "config_schema": {"cases": "json"}},
                ]
            },
            {
                "type": "output",
                "label": "Output",
                "icon": "📤",
                "sub_types": [
                    {"id": "send_response", "label": "Send Response", "icon": "📤",
                     "description": "Send final reply / output",
                     "ports": {"input": ["input"]},
                     "config_schema": {"format": "string"}},
                    {"id": "output_parser", "label": "Output Parser", "icon": "📋",
                     "description": "Parse and structure output",
                     "ports": {"input": ["input"], "output": ["output_parser"]},
                     "config_schema": {"schema": "json"}},
                ]
            },
        ]
    }
