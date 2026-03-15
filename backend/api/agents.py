"""
Agent CRUD API routes with nodes and edges management.
"""
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.core.dependencies import get_current_user
from backend.models.user import User
from backend.models.agent import Agent, AgentNode, AgentEdge
from backend.schemas.agent import (
    AgentCreate, AgentUpdate, AgentResponse, AgentListResponse,
    NodeCreate, NodeUpdate, NodeResponse,
    EdgeCreate, EdgeResponse,
    AgentWorkflowSave,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agents", tags=["Agents"])


@router.get("", response_model=List[AgentListResponse])
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all agents for the current user's tenant."""
    logger.info("Listing agents for tenant=%s", current_user.tenant_id)
    result = await db.execute(
        select(Agent)
        .where(Agent.tenant_id == current_user.tenant_id)
        .options(selectinload(Agent.nodes), selectinload(Agent.edges))
        .order_by(Agent.updated_at.desc())
    )
    agents = result.scalars().all()

    return [
        AgentListResponse(
            id=a.id, name=a.name, description=a.description,
            status=a.status, tags=a.tags or [],
            created_at=a.created_at, updated_at=a.updated_at,
            node_count=len(a.nodes), edge_count=len(a.edges),
        )
        for a in agents
    ]


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    data: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new agent."""
    logger.info("Creating agent: name=%s, user=%s", data.name, current_user.id)
    agent = Agent(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        tags=data.tags,
    )
    db.add(agent)
    await db.flush()

    return AgentResponse(
        id=agent.id, tenant_id=agent.tenant_id, user_id=agent.user_id,
        name=agent.name, description=agent.description, status=agent.status,
        tags=agent.tags or [], created_at=agent.created_at, updated_at=agent.updated_at,
        nodes=[], edges=[],
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get agent details with all nodes and edges."""
    result = await db.execute(
        select(Agent)
        .where(Agent.id == agent_id, Agent.tenant_id == current_user.tenant_id)
        .options(selectinload(Agent.nodes), selectinload(Agent.edges))
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return AgentResponse.model_validate(agent)


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    data: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update agent details."""
    result = await db.execute(
        select(Agent)
        .where(Agent.id == agent_id, Agent.tenant_id == current_user.tenant_id)
        .options(selectinload(Agent.nodes), selectinload(Agent.edges))
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(agent, field, value)

    await db.flush()
    logger.info("Agent updated: id=%s", agent_id)
    return AgentResponse.model_validate(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an agent and all its nodes/edges."""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.tenant_id == current_user.tenant_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    await db.delete(agent)
    logger.info("Agent deleted: id=%s", agent_id)


# ---- Node endpoints ----
@router.post("/{agent_id}/nodes", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
async def add_node(
    agent_id: UUID,
    data: NodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a node to an agent workflow."""
    # Verify agent ownership
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.tenant_id == current_user.tenant_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Agent not found")

    node = AgentNode(agent_id=agent_id, **data.model_dump())
    db.add(node)
    await db.flush()
    logger.info("Node added: id=%s, type=%s, agent=%s", node.id, node.node_type, agent_id)
    return NodeResponse.model_validate(node)


@router.put("/{agent_id}/nodes/{node_id}", response_model=NodeResponse)
async def update_node(
    agent_id: UUID,
    node_id: UUID,
    data: NodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a node's properties."""
    result = await db.execute(
        select(AgentNode).where(AgentNode.id == node_id, AgentNode.agent_id == agent_id)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(node, field, value)

    await db.flush()
    return NodeResponse.model_validate(node)


@router.delete("/{agent_id}/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(
    agent_id: UUID,
    node_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a node from an agent workflow."""
    result = await db.execute(
        select(AgentNode).where(AgentNode.id == node_id, AgentNode.agent_id == agent_id)
    )
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    await db.delete(node)
    logger.info("Node deleted: id=%s", node_id)


# ---- Edge endpoints ----
@router.post("/{agent_id}/edges", response_model=EdgeResponse, status_code=status.HTTP_201_CREATED)
async def add_edge(
    agent_id: UUID,
    data: EdgeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add an edge between two nodes."""
    edge = AgentEdge(agent_id=agent_id, **data.model_dump())
    db.add(edge)
    await db.flush()
    logger.info("Edge added: %s -> %s", data.source_node_id, data.target_node_id)
    return EdgeResponse.model_validate(edge)


@router.delete("/{agent_id}/edges/{edge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_edge(
    agent_id: UUID,
    edge_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove an edge."""
    result = await db.execute(
        select(AgentEdge).where(AgentEdge.id == edge_id, AgentEdge.agent_id == agent_id)
    )
    edge = result.scalar_one_or_none()
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")

    await db.delete(edge)
    logger.info("Edge deleted: id=%s", edge_id)


# ---- Bulk workflow save ----
@router.put("/{agent_id}/workflow")
async def save_workflow(
    agent_id: UUID,
    data: AgentWorkflowSave,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bulk save the entire workflow (replace all nodes and edges)."""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.tenant_id == current_user.tenant_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Delete existing nodes and edges
    # We use a explicit query to avoid loading all into memory if possible, 
    # but for simplicity and correctness in async SQLAlchemy:
    await db.execute(select(AgentNode).where(AgentNode.agent_id == agent_id)) # Not strictly needed but helps session
    
    # Actually, we can just delete from table
    from sqlalchemy import delete
    await db.execute(delete(AgentEdge).where(AgentEdge.agent_id == agent_id))
    await db.execute(delete(AgentNode).where(AgentNode.agent_id == agent_id))
    await db.flush()

    # Create new nodes
    id_map = {}  # incoming_id (might be temp-N or UUID) -> real database UUID
    for node_data in data.nodes:
        incoming_id = node_data.id
        node = AgentNode(
            agent_id=agent_id,
            node_type=node_data.node_type,
            sub_type=node_data.sub_type,
            label=node_data.label,
            description=node_data.description,
            position_x=node_data.position_x,
            position_y=node_data.position_y,
            config=node_data.config,
            parent_node_id=node_data.parent_node_id,
        )
        db.add(node)
        await db.flush()
        if incoming_id:
            id_map[incoming_id] = node.id

    # Create new edges with ID mapping
    for edge_data in data.edges:
        source_id = edge_data.source_node_id
        target_id = edge_data.target_node_id
        
        # Map source
        if source_id in id_map:
            source_uuid = id_map[source_id]
        else:
            try:
                source_uuid = UUID(source_id)
            except ValueError:
                logger.error("Invalid source node ID: %s", source_id)
                continue
                
        # Map target
        if target_id in id_map:
            target_uuid = id_map[target_id]
        else:
            try:
                target_uuid = UUID(target_id)
            except ValueError:
                logger.error("Invalid target node ID: %s", target_id)
                continue

        edge = AgentEdge(
            agent_id=agent_id,
            source_node_id=source_uuid,
            target_node_id=target_uuid,
            source_port=edge_data.source_port,
            target_port=edge_data.target_port,
            edge_type=edge_data.edge_type,
            label=edge_data.label,
        )
        db.add(edge)

    await db.flush()
    logger.info("Workflow saved for agent=%s: %d nodes, %d edges", agent_id, len(data.nodes), len(data.edges))

    # Return full agent
    result = await db.execute(
        select(Agent)
        .where(Agent.id == agent_id)
        .options(selectinload(Agent.nodes), selectinload(Agent.edges))
    )
    return AgentResponse.model_validate(result.scalar_one())
