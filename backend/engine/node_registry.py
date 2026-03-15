"""
Node registry - maps node types to their handler classes.
"""
import logging
from typing import Any, Dict, Type

logger = logging.getLogger(__name__)

# Registry of node_type -> handler factory
_NODE_HANDLERS: Dict[str, Any] = {}


def register_node(node_type: str):
    """Decorator to register a node handler."""
    def decorator(cls):
        _NODE_HANDLERS[node_type] = cls
        logger.debug("Registered node handler: %s -> %s", node_type, cls.__name__)
        return cls
    return decorator


def get_node_handler(node_type: str):
    """Get the handler class for a node type."""
    handler = _NODE_HANDLERS.get(node_type)
    if not handler:
        logger.warning("No handler registered for node type: %s", node_type)
    return handler


def get_all_node_types():
    """Get all registered node types."""
    return list(_NODE_HANDLERS.keys())


# LLM Provider factory
def get_llm_provider(sub_type: str, config: Dict[str, Any]):
    """Create an LLM provider instance based on sub_type."""
    providers = {
        "openai_chat": "backend.engine.llm_providers.openai_provider.OpenAIProvider",
        "gemini_chat": "backend.engine.llm_providers.gemini_provider.GeminiProvider",
        "groq_chat": "backend.engine.llm_providers.groq_provider.GroqProvider",
        "openrouter_chat": "backend.engine.llm_providers.openrouter_provider.OpenRouterProvider",
        "ollama_chat": "backend.engine.llm_providers.ollama_provider.OllamaProvider",
    }

    provider_path = providers.get(sub_type)
    if not provider_path:
        raise ValueError(f"Unknown LLM provider: {sub_type}")

    module_path, class_name = provider_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls(config)


# Memory factory
def get_memory_provider(sub_type: str, config: Dict[str, Any]):
    """Create a memory provider instance."""
    from backend.engine.memory.buffer_memory import BufferMemory
    from backend.engine.memory.persistent_memory import PersistentMemory

    providers = {
        "buffer_memory": BufferMemory,
        "persistent_memory": PersistentMemory,
    }

    cls = providers.get(sub_type)
    if not cls:
        raise ValueError(f"Unknown memory type: {sub_type}")
    return cls(config)


# Tool factory
def get_tool_provider(sub_type: str, config: Dict[str, Any]):
    """Create a tool instance."""
    from backend.engine.tools.http_tool import HTTPTool
    from backend.engine.tools.code_tool import CodeTool
    from backend.engine.tools.search_tool import SearchTool

    providers = {
        "http_request": HTTPTool,
        "code_executor": CodeTool,
        "search_web": SearchTool,
    }

    cls = providers.get(sub_type)
    if not cls:
        raise ValueError(f"Unknown tool type: {sub_type}")
    return cls(config)
