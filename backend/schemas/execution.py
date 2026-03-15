"""
Pydantic schemas for execution endpoints.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class ExecutionCreate(BaseModel):
    input_data: Dict[str, Any] = {}


class ExecutionLogResponse(BaseModel):
    id: UUID
    node_id: UUID
    node_label: str
    node_type: str
    status: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    error_message: Optional[str]
    duration_ms: Optional[float]
    timestamp: datetime

    class Config:
        from_attributes = True


class ExecutionResponse(BaseModel):
    id: UUID
    agent_id: UUID
    tenant_id: UUID
    user_id: UUID
    status: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    error_message: Optional[str]
    celery_task_id: Optional[str]
    duration_seconds: Optional[float]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    logs: List[ExecutionLogResponse] = []

    class Config:
        from_attributes = True


class ExecutionListResponse(BaseModel):
    id: UUID
    agent_id: UUID
    status: str
    duration_seconds: Optional[float]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
