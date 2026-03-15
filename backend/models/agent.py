"""
Agent, AgentNode, and AgentEdge models for workflow definition.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Integer, UUID, JSON
from sqlalchemy.orm import relationship

from backend.database import Base


class Agent(Base):
    """An AI Agent workflow definition."""
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    status = Column(String(50), default="draft")  # draft, active, archived
    tags = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    tenant = relationship("Tenant", back_populates="agents")
    user = relationship("User", back_populates="agents")
    nodes = relationship("AgentNode", back_populates="agent", cascade="all, delete-orphan")
    edges = relationship("AgentEdge", back_populates="agent", cascade="all, delete-orphan")
    executions = relationship("Execution", back_populates="agent", cascade="all, delete-orphan")


class AgentNode(Base):
    """A node in the agent workflow graph."""
    __tablename__ = "agent_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    node_type = Column(String(50), nullable=False)  # trigger, agent, llm, memory, tool, condition, output
    sub_type = Column(String(100), default="")  # e.g., openai_chat, buffer_memory, http_request
    label = Column(String(255), nullable=False)
    description = Column(Text, default="")
    position_x = Column(Float, default=0.0)
    position_y = Column(Float, default=0.0)
    config = Column(JSON, default=dict)  # Node-specific configuration
    parent_node_id = Column(UUID(as_uuid=True), ForeignKey("agent_nodes.id"), nullable=True)  # For sub-nodes
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    agent = relationship("Agent", back_populates="nodes")
    sub_nodes = relationship("AgentNode", backref="parent_node", remote_side=[id])


class AgentEdge(Base):
    """An edge connecting two nodes in the workflow."""
    __tablename__ = "agent_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    source_node_id = Column(UUID(as_uuid=True), ForeignKey("agent_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id = Column(UUID(as_uuid=True), ForeignKey("agent_nodes.id", ondelete="CASCADE"), nullable=False)
    source_port = Column(String(50), default="output")  # output, true, false, error
    target_port = Column(String(50), default="input")  # input, model, memory, tool
    edge_type = Column(String(50), default="default")  # default, conditional, sub_node
    label = Column(String(255), default="")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    agent = relationship("Agent", back_populates="edges")
