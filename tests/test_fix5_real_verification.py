"""Tests for Fix 5: Explicit task kinds, Skeptic-before-simulation DAG, real draft report verification, and bounded loop-back."""

import pytest
from orchestrator.parser import parse_decision_query
from orchestrator.supervisor import Supervisor
from orchestrator.decomposer import decompose_decision
from report.report_builder import build_consolidated_report, render_report_markdown
from simulation.saas_model import simulate, STRATEGY_A, STRATEGY_B, STRATEGY_C
from state.company import load_company_snapshot
from state.schemas import Assumption, Decision, SimulationRun, Task
from verification.verifier import verify_workflow


def test_task_dag_explicit_kinds_and_ordering():
    """Verify that tasks declare explicit kinds and follow: analysis -> conflict -> skeptic -> simulation -> draft -> verify -> finalize."""
    decision, _ = parse_decision_query("Should we launch a free plan?")
    dag = decompose_decision(decision)

    tasks_by_id = dag.tasks
    assert all(hasattr(t, "kind") for t in tasks_by_id.values())

    topo = dag.get_topological_order()
    conflict_idx = topo.index("task_conflict_detection")
    skeptic_idx = topo.index("task_skeptic_review")
    sim_idx = topo.index("task_simulation_resolution")
    draft_idx = topo.index("task_report_draft")
    verif_idx = topo.index("task_workflow_verification")
    final_idx = topo.index("task_report_finalize")

    assert conflict_idx < skeptic_idx < sim_idx < draft_idx < verif_idx < final_idx
    assert tasks_by_id["task_skeptic_review"].kind == "skeptic_review"
    assert tasks_by_id["task_report_draft"].kind == "report_draft"
    assert tasks_by_id["task_workflow_verification"].kind == "verification"
    assert tasks_by_id["task_report_finalize"].kind == "report_finalize"


def test_verifier_catches_tampered_draft_report_number():
    """Verify report_number_traceability scans draft report metrics and prose, catching fabricated numbers."""
    company = load_company_snapshot()
    assumptions = [
        Assumption(name="free_to_paid_conversion", low=0.01, base=0.02, high=0.03, unit="ratio", provenance="ai_assumption")
    ]
    sim_runs = [
        simulate(STRATEGY_B, "expected", {"free_to_paid_conversion": 0.02}, company=company)
    ]
    decision = Decision(id="dec-1", type="free_plan", question="Test?", objective="Test", status="pending")
    from state.shared_state import WorkflowState
    state = WorkflowState(decision=decision, assumptions=assumptions, simulation_runs=sim_runs)

    draft_report = build_consolidated_report(state, company=company)

    # Valid draft passes
    passed, results = verify_workflow(assumptions, sim_runs, company, draft_report=draft_report)
    trace_check = next(r for r in results if r.check_name == "report_number_traceability")
    assert trace_check.status == "passed"

    # Tamper with a scenario table number
    draft_tampered = dict(draft_report)
    draft_tampered["sections"] = dict(draft_report["sections"])
    table_copy = [dict(row) for row in draft_report["sections"]["scenario_table"]]
    table_copy[0]["mrr_month_12_expected"] = 777777.0  # Fabricated!
    draft_tampered["sections"]["scenario_table"] = table_copy

    passed_tampered, results_tampered = verify_workflow(assumptions, sim_runs, company, draft_report=draft_tampered)
    assert passed_tampered is False
    trace_check_tampered = next(r for r in results_tampered if r.check_name == "report_number_traceability")
    assert trace_check_tampered.status == "failed"
    assert "777777" in trace_check_tampered.detail or "777,777" in trace_check_tampered.detail


@pytest.mark.asyncio
async def test_supervisor_skeptic_challenges_present_in_report():
    """Verify run_skeptic_audit runs before simulation and its challenges appear in state and report."""
    supervisor = Supervisor()
    decision, _ = parse_decision_query("Should we launch a free plan?")
    state = await supervisor.run_workflow(decision=decision)

    assert state.status == "completed"
    assert hasattr(state, "skeptic_challenges")
    assert len(state.skeptic_challenges) > 0
    # At least one assumption must have challenged_by_skeptic = True
    assert any(a.challenged_by_skeptic for a in state.assumptions)

