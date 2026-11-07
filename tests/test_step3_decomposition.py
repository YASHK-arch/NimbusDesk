"""Unit tests for Step 3: Decision intake parser, DAG decomposition, and cycle validation."""

import pytest
from orchestrator.dag import TaskDAG
from orchestrator.decomposer import decompose_decision
from orchestrator.parser import parse_decision_query
from state.schemas import Decision, Task


def test_parse_decision_query_free_plan():
    """Verify natural language parsing for free plan inquiries."""
    decision, is_supported = parse_decision_query("Should we launch a free plan?")
    assert is_supported is True
    assert decision.type == "free_plan"
    assert "runway" in decision.constraints[0].lower()
    assert len(decision.constraints) == 3


def test_parse_decision_query_price_change():
    """Verify natural language parsing for pricing inquiries."""
    decision, is_supported = parse_decision_query("What if we raise prices by 20%?")
    assert is_supported is True
    assert decision.type == "price_change"
    assert "20%" in decision.objective


def test_parse_decision_query_unsupported():
    """Verify clear error guidance for unsupported decision questions."""
    decision, is_supported = parse_decision_query("Should we relocate headquarters to Austin?")
    assert is_supported is False
    assert decision.type == "unsupported"
    assert "Unsupported decision inquiry" in decision.objective
    assert "Free Plan" in decision.objective


def test_decompose_free_plan_dag():
    """Verify task DAG decomposition for free plan decision."""
    decision, _ = parse_decision_query("Should we launch a free plan?")
    dag = decompose_decision(decision)

    assert isinstance(dag, TaskDAG)
    # 5 analyses + discussion (Fix 9) + conflict + skeptic + simulation + draft + verification + finalize = 12 tasks
    assert len(dag.tasks) == 12

    # Verify parallel root tasks
    ready_tasks = dag.get_ready_tasks(completed_ids=set(), active_ids=set())
    ready_owners = {t.owner_agent for t in ready_tasks}
    assert ready_owners == {"CFO", "Growth", "CTO", "Customer", "Product"}

    # Verify topological order per Fix 5 & Fix 9
    topo = dag.get_topological_order()
    assert topo[-1] == "task_report_finalize"
    assert topo.index("task_agent_discussion") > topo.index("task_cfo_analysis")
    assert topo.index("task_conflict_detection") > topo.index("task_agent_discussion")
    assert topo.index("task_skeptic_review") > topo.index("task_conflict_detection")
    assert topo.index("task_simulation_resolution") > topo.index("task_skeptic_review")
    assert topo.index("task_report_draft") > topo.index("task_simulation_resolution")
    assert topo.index("task_workflow_verification") > topo.index("task_report_draft")
    assert topo.index("task_report_finalize") > topo.index("task_workflow_verification")


def test_dag_cycle_detection():
    """Verify that circular task dependencies are caught immediately."""
    dag = TaskDAG()
    t1 = Task(id="task_1", owner_agent="A", depends_on=["task_2"])
    t2 = Task(id="task_2", owner_agent="B", depends_on=["task_1"])
    dag.add_task(t1)
    dag.add_task(t2)

    with pytest.raises(ValueError) as exc_info:
        dag.validate()
    assert "Cycle detected" in str(exc_info.value)


def test_dag_missing_dependency():
    """Verify detection of dangling task dependencies."""
    dag = TaskDAG()
    t1 = Task(id="task_1", owner_agent="A", depends_on=["non_existent_task"])
    dag.add_task(t1)

    with pytest.raises(ValueError) as exc_info:
        dag.validate()
    assert "depends on missing dependency" in str(exc_info.value)
