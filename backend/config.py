"""
Configuration loader for AgentForge.
Reads app_config.yaml and provides typed access to all settings.
"""
import os
import yaml
import re
from pathlib import Path
from functools import lru_cache
from typing import Any, Dict, Optional

import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).parent.parent / "app_config.yaml"


def _resolve_env_vars(value: Any) -> Any:
    """Resolve ${ENV_VAR} references in config values."""
    if isinstance(value, str):
        pattern = re.compile(r'\$\{(\w+)\}')
        def replacer(match):
            env_var = match.group(1)
            return os.environ.get(env_var, match.group(0))
        return pattern.sub(replacer, value)
    elif isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_resolve_env_vars(v) for v in value]
    return value


class AppConfig:
    """Application configuration loaded from app_config.yaml."""

    def __init__(self, config_path: Optional[str] = None):
        path = Path(config_path) if config_path else CONFIG_FILE
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "r") as f:
            self._raw: Dict[str, Any] = yaml.safe_load(f)

        # Load environment variables from .env file if it exists
        load_dotenv()
        
        self._config = _resolve_env_vars(self._raw)
        logger.info("Configuration loaded from %s", path)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value using dot notation: 'server.port'"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    # ---- Shortcut properties ----
    @property
    def app_name(self) -> str:
        return self.get("app.name", "AgentForge")

    @property
    def debug(self) -> bool:
        return self.get("app.debug", False)

    @property
    def server_host(self) -> str:
        return self.get("server.host", "0.0.0.0")

    @property
    def server_port(self) -> int:
        return self.get("server.port", 8000)

    @property
    def database_type(self) -> str:
        url = self.database_url
        if url and url.startswith("sqlite"):
            return "sqlite"
        return self.get("database.type", "postgresql")

    @property
    def database_url(self) -> str:
        url = os.environ.get("DATABASE_URL", self.get("database.url"))
        if not url:
            # Fallback to sqlite by default if nothing else is specified
            path = self.get("database.sqlite_path", "./agentforge.db")
            return f"sqlite+aiosqlite:///{path}"
        return url

    @property
    def redis_url(self) -> str:
        return os.environ.get("REDIS_URL", self.get("redis.url"))

    @property
    def rabbitmq_url(self) -> str:
        return os.environ.get("RABBITMQ_URL", self.get("rabbitmq.url"))

    @property
    def jwt_secret(self) -> str:
        return os.environ.get("JWT_SECRET", self.get("auth.secret_key"))

    @property
    def jwt_algorithm(self) -> str:
        return self.get("auth.algorithm", "HS256")

    @property
    def access_token_expire_minutes(self) -> int:
        return self.get("auth.access_token_expire_minutes", 1440)

    @property
    def celery_broker_url(self) -> str:
        return os.environ.get("CELERY_BROKER_URL", self.get("celery.broker_url"))

    @property
    def celery_result_backend(self) -> str:
        return os.environ.get("CELERY_RESULT_BACKEND", self.get("celery.result_backend"))

    @property
    def log_level(self) -> str:
        return self.get("logging.level", "INFO")

    @property
    def cors_origins(self) -> list:
        return self.get("cors.allow_origins", ["*"])

    def llm_provider_config(self, provider: str) -> Dict[str, Any]:
        return self.get(f"llm_providers.{provider}", {})


@lru_cache()
def get_config() -> AppConfig:
    """Singleton config instance."""
    return AppConfig()
