"""
Execution and ExecutionLog models for tracking agent runs.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, UUID, JSON
from sqlalchemy.orm import relationship

from backend.database import Base


class Execution(Base):
    """A single execution run of an agent workflow."""
    __tablename__ = "executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(50), default="pending")  # pending, running, completed, failed, cancelled
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    celery_task_id = Column(String(255), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    agent = relationship("Agent", back_populates="executions")
    user = relationship("User", back_populates="executions")
    logs = relationship("ExecutionLog", back_populates="execution", cascade="all, delete-orphan",
                        order_by="ExecutionLog.timestamp")


class ExecutionLog(Base):
    """Log entry for each node execution within a workflow run."""
    __tablename__ = "execution_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("executions.id", ondelete="CASCADE"),
                          nullable=False, index=True)
    node_id = Column(UUID(as_uuid=True), nullable=False)
    node_label = Column(String(255), default="")
    node_type = Column(String(50), default="")
    status = Column(String(50), default="running")  # running, completed, failed, skipped
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    execution = relationship("Execution", back_populates="logs")
