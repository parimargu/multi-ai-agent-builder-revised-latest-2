"""
Execution API routes: run agents, check status, view logs.
"""
import logging
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.core.dependencies import get_current_user
from backend.models.user import User
from backend.models.agent import Agent
from backend.models.execution import Execution, ExecutionLog
from backend.schemas.execution import ExecutionCreate, ExecutionResponse, ExecutionListResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Executions"])


@router.post("/agents/{agent_id}/execute", response_model=ExecutionResponse,
             status_code=status.HTTP_202_ACCEPTED)
async def execute_agent(
    agent_id: UUID,
    data: ExecutionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Queue an agent for execution via Celery."""
    # Verify agent exists
    result = await db.execute(
        select(Agent)
        .where(Agent.id == agent_id, Agent.tenant_id == current_user.tenant_id)
        .options(selectinload(Agent.nodes), selectinload(Agent.edges))
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if not agent.nodes:
        raise HTTPException(status_code=400, detail="Agent has no nodes to execute")

    # Create execution record
    execution = Execution(
        agent_id=agent_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        status="pending",
        input_data=data.input_data,
    )
    db.add(execution)
    await db.flush()

    # Try to dispatch to Celery, fallback to direct execution
    try:
        from backend.workers.celery_app import execute_agent_workflow
        task = execute_agent_workflow.delay(str(execution.id))
        execution.celery_task_id = task.id
        execution.status = "queued"
        logger.info("Agent execution queued: execution_id=%s, celery_task=%s", execution.id, task.id)
    except Exception as e:
        logger.warning("Celery unavailable, marking as pending for direct execution: %s", str(e))
        execution.status = "pending"

    await db.flush()

    return ExecutionResponse(
        id=execution.id, agent_id=execution.agent_id,
        tenant_id=execution.tenant_id, user_id=execution.user_id,
        status=execution.status, input_data=execution.input_data,
        output_data={}, error_message=None,
        celery_task_id=execution.celery_task_id,
        duration_seconds=None, started_at=None, completed_at=None,
        created_at=execution.created_at, logs=[],
    )


@router.get("/executions", response_model=List[ExecutionListResponse])
async def list_executions(
    agent_id: UUID = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List executions for current tenant, optionally filtered by agent."""
    query = select(Execution).where(Execution.tenant_id == current_user.tenant_id)
    if agent_id:
        query = query.where(Execution.agent_id == agent_id)
    query = query.order_by(Execution.created_at.desc()).limit(100)

    result = await db.execute(query)
    return [ExecutionListResponse.model_validate(e) for e in result.scalars().all()]


@router.get("/executions/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get execution details with logs."""
    result = await db.execute(
        select(Execution)
        .where(Execution.id == execution_id, Execution.tenant_id == current_user.tenant_id)
        .options(selectinload(Execution.logs))
    )
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    return ExecutionResponse.model_validate(execution)
