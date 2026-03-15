"""
Celery application and task definitions for async agent execution.
"""
import logging
import asyncio
from datetime import datetime, timezone

from celery import Celery

from backend.config import get_config

logger = logging.getLogger(__name__)

config = get_config()

celery_app = Celery(
    "agentforge",
    broker=config.celery_broker_url,
    backend=config.celery_result_backend,
)

celery_app.conf.update(
    task_serializer=config.get("celery.task_serializer", "json"),
    result_serializer=config.get("celery.result_serializer", "json"),
    accept_content=config.get("celery.accept_content", ["json"]),
    timezone=config.get("celery.timezone", "UTC"),
    task_track_started=config.get("celery.task_track_started", True),
    task_time_limit=config.get("celery.task_time_limit", 300),
    worker_concurrency=config.get("celery.worker_concurrency", 4),
)


def _run_async(coro):
    """Run an async coroutine in a new event loop."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="execute_agent_workflow", bind=True, max_retries=3)
def execute_agent_workflow(self, execution_id: str):
    """
    Celery task: Execute an agent workflow.
    
    1. Load execution record and agent from DB
    2. Build executor from nodes/edges
    3. Run the workflow
    4. Update execution with results
    """
    logger.info("Celery task started: execution_id=%s", execution_id)

    async def _execute():
        from backend.database import async_session
        from backend.models.execution import Execution, ExecutionLog
        from backend.models.agent import Agent, AgentNode, AgentEdge
        from backend.engine.executor import WorkflowExecutor
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        async with async_session() as db:
            # Load execution
            result = await db.execute(
                select(Execution).where(Execution.id == execution_id)
            )
            execution = result.scalar_one_or_none()
            if not execution:
                logger.error("Execution not found: %s", execution_id)
                return

            # Update status
            execution.status = "running"
            execution.started_at = datetime.now(timezone.utc)
            await db.commit()

            # Load agent with nodes and edges
            result = await db.execute(
                select(Agent)
                .where(Agent.id == execution.agent_id)
                .options(selectinload(Agent.nodes), selectinload(Agent.edges))
            )
            agent = result.scalar_one_or_none()
            if not agent:
                execution.status = "failed"
                execution.error_message = "Agent not found"
                await db.commit()
                return

            # Build node/edge dicts
            nodes = [
                {
                    "id": str(n.id),
                    "node_type": n.node_type,
                    "sub_type": n.sub_type,
                    "label": n.label,
                    "config": n.config or {},
                    "parent_node_id": str(n.parent_node_id) if n.parent_node_id else None,
                }
                for n in agent.nodes
            ]
            edges = [
                {
                    "source_node_id": str(e.source_node_id),
                    "target_node_id": str(e.target_node_id),
                    "source_port": e.source_port,
                    "target_port": e.target_port,
                    "edge_type": e.edge_type,
                }
                for e in agent.edges
            ]

            # Execute workflow
            executor = WorkflowExecutor(nodes, edges, str(agent.id))
            try:
                output = await executor.execute(execution.input_data or {})
                execution.status = "completed"
                execution.output_data = output
            except Exception as e:
                logger.error("Workflow execution failed: %s", str(e))
                execution.status = "failed"
                execution.error_message = str(e)

            execution.completed_at = datetime.now(timezone.utc)
            if execution.started_at:
                execution.duration_seconds = (
                    execution.completed_at - execution.started_at
                ).total_seconds()

            # Save execution logs
            for log in executor.execution_logs:
                db_log = ExecutionLog(
                    execution_id=execution.id,
                    node_id=log["node_id"],
                    node_label=log.get("node_label", ""),
                    node_type=log.get("node_type", ""),
                    status=log["status"],
                    input_data=log.get("input_data", {}),
                    output_data=log.get("output_data", {}),
                    error_message=log.get("error_message"),
                    duration_ms=log.get("duration_ms"),
                )
                db.add(db_log)

            await db.commit()
            logger.info("Execution completed: id=%s, status=%s", execution_id, execution.status)

    try:
        _run_async(_execute())
    except Exception as exc:
        logger.error("Celery task failed: %s", str(exc))
        raise self.retry(exc=exc, countdown=10)
