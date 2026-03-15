"""
Memory store model for persisting agent conversation memory.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, UUID, JSON

from backend.database import Base


class MemoryStore(Base):
    """Persistent memory storage for agent conversations."""
    __tablename__ = "memory_stores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"),
                      nullable=False, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    memory_type = Column(String(50), nullable=False)  # buffer, persistent
    role = Column(String(50), default="user")  # user, assistant, system
    content = Column(Text, nullable=False)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)
