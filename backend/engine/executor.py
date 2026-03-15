"""
Workflow executor - DAG-based execution engine for agent workflows.
"""
import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from backend.engine.nodes.trigger_node import TriggerNode
from backend.engine.nodes.agent_node import AgentNode
from backend.engine.nodes.llm_node import LLMNode
from backend.engine.nodes.memory_node import MemoryNode
from backend.engine.nodes.tool_node import ToolNode
from backend.engine.nodes.condition_node import ConditionNode
from backend.engine.nodes.output_node import OutputNode

logger = logging.getLogger(__name__)

NODE_CLASS_MAP = {
    "trigger": TriggerNode,
    "agent": AgentNode,
    "llm": LLMNode,
    "memory": MemoryNode,
    "tool": ToolNode,
    "condition": ConditionNode,
    "output": OutputNode,
}


class WorkflowExecutor:
    """
    DAG-based workflow execution engine.
    
    Executes nodes in topological order, handling:
    - Sub-node connections (model, memory, tool -> agent)
    - Conditional branching (if/else, switch)
    - Error handling and logging per node
    """

    def __init__(self, nodes: List[Dict], edges: List[Dict], agent_id: str = ""):
        self.nodes = {str(n["id"]): n for n in nodes}
        self.edges = edges
        self.agent_id = agent_id
        self.execution_logs: List[Dict] = []

        # Build adjacency and reverse adjacency
        self.forward_edges: Dict[str, List[Dict]] = defaultdict(list)
        self.backward_edges: Dict[str, List[Dict]] = defaultdict(list)
        self.sub_node_edges: Dict[str, Dict[str, List[Dict]]] = defaultdict(lambda: defaultdict(list))

        for edge in edges:
            src = str(edge["source_node_id"])
            tgt = str(edge["target_node_id"])
            edge_type = edge.get("edge_type", "default")

            if edge_type == "sub_node" or edge.get("target_port") in ("model", "memory", "tool", "output_parser"):
                self.sub_node_edges[tgt][edge["target_port"]].append(edge)
            else:
                self.forward_edges[src].append(edge)
                self.backward_edges[tgt].append(edge)

    def _get_execution_order(self) -> List[str]:
        """Topological sort of main flow nodes (excluding sub-nodes)."""
        # Find nodes that are sub-nodes (connected via sub_node edges)
        sub_node_ids: Set[str] = set()
        for target_id, ports in self.sub_node_edges.items():
            for port, edges in ports.items():
                for edge in edges:
                    sub_node_ids.add(str(edge["source_node_id"]))

        # Kahn's algorithm for topological sort
        in_degree: Dict[str, int] = defaultdict(int)
        main_nodes = [nid for nid in self.nodes if nid not in sub_node_ids]

        for nid in main_nodes:
            if nid not in in_degree:
                in_degree[nid] = 0

        for src, edges in self.forward_edges.items():
            for edge in edges:
                tgt = str(edge["target_node_id"])
                if tgt in main_nodes:
                    in_degree[tgt] = in_degree.get(tgt, 0) + 1

        queue = [nid for nid in main_nodes if in_degree.get(nid, 0) == 0]
        order = []

        while queue:
            node_id = queue.pop(0)
            order.append(node_id)
            for edge in self.forward_edges.get(node_id, []):
                tgt = str(edge["target_node_id"])
                in_degree[tgt] -= 1
                if in_degree[tgt] == 0:
                    queue.append(tgt)

        return order

    async def _resolve_sub_nodes(self, node_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute sub-nodes (LLM, memory, tools) and collect their configs."""
        sub_nodes = {"model": {}, "memory": {}, "tools": [], "output_parser": {}}

        for port, edges in self.sub_node_edges.get(node_id, {}).items():
            for edge in edges:
                src_id = str(edge["source_node_id"])
                src_node_data = self.nodes.get(src_id)
                if not src_node_data:
                    continue

                node_cls = NODE_CLASS_MAP.get(src_node_data["node_type"])
                if not node_cls:
                    continue

                node_instance = node_cls(
                    node_id=src_id,
                    node_type=src_node_data["node_type"],
                    sub_type=src_node_data.get("sub_type", ""),
                    label=src_node_data.get("label", ""),
                    config=src_node_data.get("config", {}),
                )

                result = await node_instance.execute({}, context)

                if port == "model":
                    sub_nodes["model"] = result
                elif port == "memory":
                    sub_nodes["memory"] = result
                elif port == "tool":
                    sub_nodes["tools"].append(result)
                elif port == "output_parser":
                    sub_nodes["output_parser"] = result

        return sub_nodes

    async def execute(self, input_data: Dict[str, Any],
                      session_id: str = "default") -> Dict[str, Any]:
        """Execute the entire workflow."""
        logger.info("WorkflowExecutor: starting execution, agent=%s, nodes=%d",
                    self.agent_id, len(self.nodes))

        execution_order = self._get_execution_order()
        logger.info("Execution order: %s", [self.nodes[nid].get("label", nid) for nid in execution_order])

        node_outputs: Dict[str, Dict[str, Any]] = {}
        final_output = {}

        context = {
            "agent_id": self.agent_id,
            "session_id": session_id,
            "sub_nodes": {},
        }

        for node_id in execution_order:
            node_data = self.nodes[node_id]
            node_type = node_data["node_type"]
            node_label = node_data.get("label", node_id)
            start_time = time.time()

            log_entry = {
                "node_id": node_id,
                "node_label": node_label,
                "node_type": node_type,
                "status": "running",
                "input_data": {},
                "output_data": {},
                "error_message": None,
                "duration_ms": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            try:
                # Get node class
                node_cls = NODE_CLASS_MAP.get(node_type)
                if not node_cls:
                    raise ValueError(f"Unknown node type: {node_type}")

                # Gather input from upstream nodes
                node_input = dict(input_data)
                for edge in self.backward_edges.get(node_id, []):
                    src_id = str(edge["source_node_id"])
                    src_port = edge.get("source_port", "output")

                    if src_id in node_outputs:
                        src_output = node_outputs[src_id]

                        # Handle conditional branches
                        if node_outputs[src_id].get("branch"):
                            if src_port != node_outputs[src_id]["branch"]:
                                log_entry["status"] = "skipped"
                                log_entry["duration_ms"] = (time.time() - start_time) * 1000
                                self.execution_logs.append(log_entry)
                                continue

                        node_input.update(src_output)

                log_entry["input_data"] = self._safe_json(node_input)

                # Resolve sub-nodes for agent nodes
                if node_type == "agent":
                    sub_nodes = await self._resolve_sub_nodes(node_id, context)
                    context["sub_nodes"] = sub_nodes

                # Create and execute node
                node_instance = node_cls(
                    node_id=node_id,
                    node_type=node_type,
                    sub_type=node_data.get("sub_type", ""),
                    label=node_label,
                    config=node_data.get("config", {}),
                )

                output = await node_instance.execute(node_input, context)
                node_outputs[node_id] = output
                final_output = output

                log_entry["status"] = "completed"
                log_entry["output_data"] = self._safe_json(output)

            except Exception as e:
                logger.error("Node execution failed: node=%s, error=%s", node_label, str(e))
                log_entry["status"] = "failed"
                log_entry["error_message"] = str(e)
                node_outputs[node_id] = {"error": str(e)}

            finally:
                log_entry["duration_ms"] = (time.time() - start_time) * 1000
                self.execution_logs.append(log_entry)

        logger.info("WorkflowExecutor: execution complete, logs=%d", len(self.execution_logs))
        return final_output

    def _safe_json(self, data: Any) -> Dict:
        """Safely convert data to JSON-serializable dict."""
        try:
            if isinstance(data, dict):
                return {k: str(v) if not isinstance(v, (dict, list, str, int, float, bool, type(None))) else v
                        for k, v in data.items()}
            return {"data": str(data)}
        except Exception:
            return {"data": str(data)}
