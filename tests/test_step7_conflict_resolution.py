"""Unit and integration tests for Step 7: Conflict detection rules and simulation-based resolution."""

import pytest
from conflict.detector import (
    detect_assumption_divergence,
    detect_conflicts,
    detect_contradictory_recommendations,
    detect_missing_evidence,
    detect_unresolved_dependencies,
)
from conflict.resolver import resolve_conflicts_with_simulation
from orchestrator.parser import parse_decision_query
from orchestrator.supervisor import Supervisor
from state.schemas import Assumption, Conflict, Evidence, Finding, Task


def test_detect_contradictory_recommendations():
    """Verify detection when agents take opposing strategic stances."""
    f1 = Finding(
        agent="Growth",
        task_id="t1",
        claim="Scale market footprint aggressively",
        recommendation="proceed",
        assumptions=[],
        evidence=[Evidence(source_type="company_data", source_ref="f", snippet="s")],
        status="ok",
    )
    f2 = Finding(
        agent="CFO",
        task_id="t2",
        claim="Protect margin and runway floor",
        recommendation="reject",
        assumptions=[],
        evidence=[Evidence(source_type="company_data", source_ref="f", snippet="s")],
        status="ok",
    )

    conflicts = detect_contradictory_recommendations({"Growth": f1, "CFO": f2})
    assert len(conflicts) == 1
    assert conflicts[0].type == "contradictory_recommendation"
    assert "Growth" in conflicts[0].agents
    assert "CFO" in conflicts[0].agents


def test_detect_assumption_divergence():
    """Verify detection when agents propose non-overlapping ranges for the same metric."""
    f1 = Finding(
        agent="CFO",
        task_id="t1",
        claim="Conservative conversion",
        recommendation="proceed_with_limits",
        assumptions=[
            Assumption(
                name="free_to_paid_conversion",
                low=0.010,
                base=0.015,
                high=0.022,
                unit="%",
                provenance="external_research",
            )
        ],
        evidence=[Evidence(source_type="company_data", source_ref="f", snippet="s")],
        status="ok",
    )
    f2 = Finding(
        agent="Growth",
        task_id="t2",
        claim="High growth conversion",
        recommendation="proceed",
        assumptions=[
            Assumption(
                name="free_to_paid_conversion",
                low=0.035,
                base=0.045,
                high=0.065,
                unit="%",
                provenance="external_research",
            )
        ],
        evidence=[Evidence(source_type="company_data", source_ref="f", snippet="s")],
        status="ok",
    )

    conflicts = detect_assumption_divergence({"CFO": f1, "Growth": f2})
    assert len(conflicts) == 1
    assert conflicts[0].type == "assumption_divergence"
    assert "free_to_paid_conversion" in conflicts[0].disputed_item


def test_detect_missing_evidence():
    """Verify detection when an agent makes a recommendation without evidence."""
    f_no_ev = Finding(
        agent="Growth",
        task_id="t1",
        claim="Unsubstantiated upside",
        recommendation="proceed",
        assumptions=[],
        evidence=[],  # Missing evidence
        status="ok",
    )
    conflicts = detect_missing_evidence({"Growth": f_no_ev})
    assert len(conflicts) == 1
    assert conflicts[0].type == "missing_evidence"


def test_detect_unresolved_dependencies():
    """Verify detection of blocked tasks."""
    t1 = Task(id="task_1", owner_agent="CFO", status="failed")
    t2 = Task(id="task_2", owner_agent="Supervisor", depends_on=["task_1"], status="pending")
    conflicts = detect_unresolved_dependencies({"task_1": t1, "task_2": t2})
    assert len(conflicts) == 1
    assert conflicts[0].type == "dependency_block"


def test_simulation_based_resolution():
    """Verify resolving conflict via simulator generates numerical evidence and simulation IDs."""
    f_cfo = Finding(
        agent="CFO",
        task_id="t1",
        claim="Low conversion",
        recommendation="proceed_with_limits",
        assumptions=[
            Assumption(
                name="free_to_paid_conversion",
                low=0.010,
                base=0.015,
                high=0.022,
                unit="%",
                provenance="external_research",
            )
        ],
        evidence=[Evidence(source_type="company_data", source_ref="f", snippet="s")],
        status="ok",
    )
    f_growth = Finding(
        agent="Growth",
        task_id="t2",
        claim="High conversion",
        recommendation="proceed",
        assumptions=[
            Assumption(
                name="free_to_paid_conversion",
                low=0.035,
                base=0.045,
                high=0.065,
                unit="%",
                provenance="external_research",
            )
        ],
        evidence=[Evidence(source_type="company_data", source_ref="f", snippet="s")],
        status="ok",
    )

    conflict = Conflict(
        id="conf-001",
        type="assumption_divergence",
        agents=["CFO", "Growth"],
        disputed_item="free_to_paid_conversion",
        evidence=[],
    )

    resolved, sim_runs = resolve_conflicts_with_simulation([conflict], {"CFO": f_cfo, "Growth": f_growth})

    assert len(resolved) == 1
    assert resolved[0].resolved is True
    assert len(resolved[0].simulation_ids) == 2
    assert len(sim_runs) == 2
    assert "MRR delta" in resolved[0].resolution
    assert "flips below" in resolved[0].resolution


@pytest.mark.asyncio
async def test_end_to_end_conflict_resolution_in_workflow():
    """Verify full supervisor workflow naturally detects and resolves CFO vs Growth conflict."""
    supervisor = Supervisor()
    decision, _ = parse_decision_query("Should we launch a free plan?")
    state = await supervisor.run_workflow(decision=decision)

    assert state.status == "completed"
    assert len(state.conflicts) >= 1

    # At least one conflict must be between CFO and Growth and resolved with simulation
    cfo_growth_conf = next(
        (c for c in state.conflicts if "CFO" in c.agents and "Growth" in c.agents),
        None,
    )
    assert cfo_growth_conf is not None
    assert cfo_growth_conf.resolved is True
    assert len(cfo_growth_conf.simulation_ids) == 2
    assert len(state.simulation_runs) >= 2
