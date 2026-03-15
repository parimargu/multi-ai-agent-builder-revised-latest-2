"""
Pydantic schemas for agent, node, and edge endpoints.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---- Node schemas ----
class NodeCreate(BaseModel):
    id: Optional[str] = None  # Temporary ID from frontend
    node_type: str
    sub_type: str = ""
    label: str
    description: str = ""
    position_x: float = 0.0
    position_y: float = 0.0
    config: Dict[str, Any] = {}
    parent_node_id: Optional[UUID] = None


class NodeUpdate(BaseModel):
    label: Optional[str] = None
    description: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    config: Optional[Dict[str, Any]] = None
    parent_node_id: Optional[UUID] = None


class NodeResponse(BaseModel):
    id: UUID
    agent_id: UUID
    node_type: str
    sub_type: str
    label: str
    description: str
    position_x: float
    position_y: float
    config: Dict[str, Any]
    parent_node_id: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Edge schemas ----
class EdgeCreate(BaseModel):
    source_node_id: str  # Can be UUID or temp-id string
    target_node_id: str  # Can be UUID or temp-id string
    source_port: str = "output"
    target_port: str = "input"
    edge_type: str = "default"
    label: str = ""


class EdgeResponse(BaseModel):
    id: UUID
    agent_id: UUID
    source_node_id: UUID
    target_node_id: UUID
    source_port: str
    target_port: str
    edge_type: str
    label: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Agent schemas ----
class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    tags: List[str] = []


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None


class AgentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    name: str
    description: str
    status: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    nodes: List[NodeResponse] = []
    edges: List[EdgeResponse] = []

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    id: UUID
    name: str
    description: str
    status: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    node_count: int = 0
    edge_count: int = 0

    class Config:
        from_attributes = True


# ---- Bulk save schema ----
class AgentWorkflowSave(BaseModel):
    """Bulk save of nodes and edges for an agent workflow."""
    nodes: List[NodeCreate] = []
    edges: List[EdgeCreate] = []
    node_ids: Dict[str, str] = {}  # temp_id -> actual node_id mapping (for frontend)
