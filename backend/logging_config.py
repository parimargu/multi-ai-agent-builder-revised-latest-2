"""
Structured logging configuration for AgentForge.
Sets up console + rotating file handlers with consistent formatting.
"""
import logging
import logging.config
import os
from pathlib import Path

from backend.config import get_config


def setup_logging():
    """Configure application-wide logging."""
    config = get_config()
    log_level = config.log_level
    log_format = config.get("logging.format",
                            "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s")
    log_file = config.get("logging.file", "logs/agentforge.log")
    max_bytes = config.get("logging.max_bytes", 10485760)
    backup_count = config.get("logging.backup_count", 5)

    # Ensure log directory exists
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": log_format,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "pythonjsonlogger.json.JsonFormatter",
                "format": "%(asctime)s %(levelname)s %(name)s %(funcName)s %(lineno)d %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "standard",
                "filename": log_file,
                "maxBytes": max_bytes,
                "backupCount": backup_count,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "backend": {
                "level": log_level,
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "celery": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console", "file"],
        },
    }

    logging.config.dictConfig(logging_config)
    logger = logging.getLogger(__name__)
    logger.info("Logging configured: level=%s, file=%s", log_level, log_file)
