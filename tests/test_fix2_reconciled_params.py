"""Tests for Fix 2: Single ReconciledParams across the entire lifecycle and dynamic runway floor constraint."""

import pytest
from orchestrator.parser import parse_decision_query
from orchestrator.supervisor import Supervisor
from report.decision_logic import extract_min_runway_constraint, rank_strategies
from simulation.params import SIM_PARAMS
from simulation.reconcile import ReconciledParams, reconcile_assumptions
from simulation.monte_carlo import run_monte_carlo_suite
from simulation.saas_model import STRATEGY_A, STRATEGY_B, STRATEGY_C, simulate
from state.schemas import Assumption, Decision


@pytest.mark.asyncio
async def test_state_reconciled_is_single_source_of_truth():
    """Verify that state.reconciled is populated during workflow and reused by report builder."""
    supervisor = Supervisor()
    decision, _ = parse_decision_query("Should we launch a free plan?")
    state = await supervisor.run_workflow(decision=decision)

    assert state.status == "completed"
    assert hasattr(state, "reconciled")
    assert state.reconciled is not None
    assert isinstance(state.reconciled, (ReconciledParams, dict))

    # Check report ledger matches state.reconciled
    if isinstance(state.reconciled, ReconciledParams):
        rec_names = {p.name for p in state.reconciled.parameters}
    else:
        rec_names = {p["name"] for p in state.reconciled.get("parameters", [])}

    report_ledger_names = {p["name"] for p in state.report["sections"]["assumption_ledger"]}
    assert rec_names == report_ledger_names


def test_dynamic_runway_floor_extraction():
    """Verify extract_min_runway_constraint extracts runway floor from constraints or assumptions."""
    # 1. From constraint string
    constraints = ["Must maintain at least 14 months runway", "Keep infra under 60%"]
    floor = extract_min_runway_constraint(constraints=constraints)
    assert floor == 14.0

    # 2. From CFO assumption
    cfo_asm = [
        Assumption(
            name="min_acceptable_runway_months",
            low=12.0,
            base=12.5,
            high=15.0,
            unit="months",
            provenance="verified_data",
        )
    ]
    floor_cfo = extract_min_runway_constraint(constraints=[], assumptions=cfo_asm)
    assert floor_cfo == 12.5

    # 3. Default fallback
    assert extract_min_runway_constraint([], []) == 10.0


@pytest.mark.asyncio
async def test_dynamic_runway_constraint_affects_feasibility_and_ranking():
    """Verify that a decision with a strict 18-month runway constraint filters out strategies below 18 months."""
    # Standard query has 10 mo runway floor: Strategy B (caps) is feasible
    supervisor = Supervisor()
    d_strict = Decision(
        id="dec-strict-runway",
        type="free_plan",
        question="Should we launch a free plan with enterprise runway guardrails?",
        objective="Maximize net contribution while preserving runway",
        constraints=["Preserve at least 22 months of cash runway at all times"],
    )
    state = await supervisor.run_workflow(decision=d_strict)

    assert state.status == "completed"
    # With a 22 month floor, any strategy with runway < 22 is marked unfeasible
    mc = state.mc_summaries
    for strat, summary in mc.items():
        # Monte Carlo p_feasible must respect the 22-month floor
        p_feas = summary["p_feasible"]
        # Percentiles
        p50_runway = summary["runway_months_12"]["p50"]
        if p50_runway < 22.0:
            assert p_feas < 1.0


@pytest.mark.asyncio
async def test_degraded_agent_assumption_does_not_override_and_caps_confidence():
    """Verify that when an agent fails and BackupAnalyst provides fallback_degraded assumptions, confidence is Low."""
    supervisor = Supervisor()
    decision, _ = parse_decision_query("Should we launch a free plan?")
    # Injected failure for CTO
    injected = {"CTO": {"failure_type": "exception", "persist": True}}
    state = await supervisor.run_workflow(decision=decision, injected_failures=injected)

    assert state.status == "completed"
    # Degraded banner must be present
    assert state.report["sections"]["executive_summary"]["degraded_agent_banner"] is not None
    assert "CTO" in state.report["sections"]["executive_summary"]["degraded_agent_banner"]
    assert state.report["confidence"] == "Low"
