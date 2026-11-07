"""Task DAG representation with cycle detection, topological validation, and dependency resolution."""

from __future__ import annotations

from typing import Any, Dict, List, Set
import networkx as nx
from state.schemas import Task


class TaskDAG:
    """Directed Acyclic Graph of workflow tasks."""

    def __init__(self) -> None:
        self.tasks: Dict[str, Task] = {}
        self.graph = nx.DiGraph()

    def add_task(self, task: Task) -> None:
        self.tasks[task.id] = task
        self.graph.add_node(task.id, owner=task.owner_agent, status=task.status)
        for dep in task.depends_on:
            self.graph.add_edge(dep, task.id)

    def validate(self) -> None:
        """Validate that all referenced dependencies exist and the graph contains no cycles."""
        for task_id, task in self.tasks.items():
            for dep in task.depends_on:
                if dep not in self.tasks:
                    raise ValueError(f"Task '{task_id}' depends on missing dependency '{dep}'")

        if not nx.is_directed_acyclic_graph(self.graph):
            cycles = list(nx.simple_cycles(self.graph))
            raise ValueError(f"Cycle detected in task DAG: {cycles}")

    def get_topological_order(self) -> List[str]:
        self.validate()
        return list(nx.topological_sort(self.graph))

    def get_ready_tasks(self, completed_ids: Set[str], active_ids: Set[str]) -> List[Task]:
        """Return tasks whose dependencies are fully completed and are not already running/completed."""
        ready: List[Task] = []
        for task_id, task in self.tasks.items():
            if task_id in completed_ids or task_id in active_ids:
                continue
            if all(dep in completed_ids for dep in task.depends_on):
                ready.append(task)
        return ready

    def to_dict(self) -> Dict[str, Any]:
        """Export nodes and edges formatted for visualization (e.g. React Flow)."""
        nodes = [
            {
                "id": t.id,
                "owner": t.owner_agent,
                "status": t.status,
                "depends_on": t.depends_on,
                "attempts": t.attempts,
            }
            for t in self.tasks.values()
        ]
        edges = [{"source": u, "target": v} for u, v in self.graph.edges()]
        return {"nodes": nodes, "edges": edges}
