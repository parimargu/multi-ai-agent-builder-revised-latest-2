"""
Persistent memory - long-term database-backed memory.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List
from uuid import UUID

from backend.engine.memory.base import BaseMemory
from backend.config import get_config

logger = logging.getLogger(__name__)


class PersistentMemory(BaseMemory):
    """Database-backed persistent memory for long-term conversation history."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.agent_id = config.get("agent_id")
        app_config = get_config()
        self.ttl_hours = config.get("ttl_hours",
                                     app_config.get("memory.persistent_ttl_hours", 720))
        logger.info("PersistentMemory initialized: agent=%s, ttl=%dh", self.agent_id, self.ttl_hours)

    async def add_message(self, role: str, content: str, session_id: str = "default"):
        """Persist a message to the database."""
        from backend.database import async_session
        from backend.models.memory import MemoryStore

        async with async_session() as db:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=self.ttl_hours) if self.ttl_hours else None
            record = MemoryStore(
                agent_id=self.agent_id,
                session_id=session_id,
                memory_type="persistent",
                role=role,
                content=content,
                expires_at=expires_at,
            )
            db.add(record)
            await db.commit()
            logger.debug("PersistentMemory: saved %s message, session=%s", role, session_id)

    async def get_messages(self, session_id: str = "default") -> List[Dict[str, str]]:
        """Retrieve all non-expired messages from the database."""
        from backend.database import async_session
        from backend.models.memory import MemoryStore
        from sqlalchemy import select, or_

        async with async_session() as db:
            now = datetime.now(timezone.utc)
            result = await db.execute(
                select(MemoryStore)
                .where(
                    MemoryStore.agent_id == self.agent_id,
                    MemoryStore.session_id == session_id,
                    MemoryStore.memory_type == "persistent",
                    or_(MemoryStore.expires_at.is_(None), MemoryStore.expires_at > now),
                )
                .order_by(MemoryStore.created_at)
            )
            records = result.scalars().all()
            return [{"role": r.role, "content": r.content} for r in records]

    async def clear(self, session_id: str = "default"):
        """Delete all memory records for a session."""
        from backend.database import async_session
        from backend.models.memory import MemoryStore
        from sqlalchemy import delete

        async with async_session() as db:
            await db.execute(
                delete(MemoryStore).where(
                    MemoryStore.agent_id == self.agent_id,
                    MemoryStore.session_id == session_id,
                )
            )
            await db.commit()
            logger.info("PersistentMemory: cleared session=%s", session_id)
