"""Tests for Fix 3: Grouped conflicts, ordinal recommendation distance, simulation-based verdicts, and bounded rebuttal."""

import pytest
from conflict.detector import (
    detect_conflicts,
    detect_contradictory_recommendations,
    detect_assumption_divergence,
)
from conflict.resolver import resolve_conflicts_with_simulation
from simulation.saas_model import simulate, STRATEGY_A, STRATEGY_B, STRATEGY_C
from state.schemas import Assumption, Conflict, Evidence, Finding
from state.company import load_company_snapshot


def test_ordinal_recommendation_filtering():
    """Proceed vs proceed_with_limits (distance = 1) is not a conflict; proceed vs reject (distance = 3) is."""
    f_proceed = Finding(
        agent="Growth",
        task_id="t1",
        claim="Grow fast",
        recommendation="proceed",
        confidence=0.8,
    )
    f_limits = Finding(
        agent="CFO",
        task_id="t2",
        claim="Protect margins",
        recommendation="proceed_with_limits",
        confidence=0.8,
    )
    f_reject = Finding(
        agent="Risk",
        task_id="t3",
        claim="Too risky",
        recommendation="reject",
        confidence=0.8,
    )

    # Proceed vs Proceed_with_limits should NOT create a conflict
    conflicts_minor = detect_contradictory_recommendations({"Growth": f_proceed, "CFO": f_limits})
    assert len(conflicts_minor) == 0

    # Proceed vs Reject should create a contradictory_recommendation conflict
    conflicts_major = detect_contradictory_recommendations({"Growth": f_proceed, "Risk": f_reject})
    assert len(conflicts_major) == 1
    assert conflicts_major[0].type == "contradictory_recommendation"


def test_assumption_divergence_grouped_by_parameter():
    """Group assumption divergences by parameter rather than generating combinatorial pairs."""
    f_cfo = Finding(
        agent="CFO",
        task_id="t1",
        claim="Low conversion",
        recommendation="proceed_with_limits",
        assumptions=[
            Assumption(name="free_to_paid_conversion", low=0.010, base=0.015, high=0.020, unit="ratio", provenance="ai_assumption")
        ],
    )
    f_growth = Finding(
        agent="Growth",
        task_id="t2",
        claim="High conversion",
        recommendation="proceed",
        assumptions=[
            Assumption(name="free_to_paid_conversion", low=0.035, base=0.045, high=0.060, unit="ratio", provenance="ai_assumption")
        ],
    )
    f_product = Finding(
        agent="Product",
        task_id="t3",
        claim="Medium-high conversion",
        recommendation="proceed_with_limits",
        assumptions=[
            Assumption(name="free_to_paid_conversion", low=0.030, base=0.038, high=0.050, unit="ratio", provenance="ai_assumption")
        ],
    )

    conflicts = detect_assumption_divergence({"CFO": f_cfo, "Growth": f_growth, "Product": f_product})
    # Should produce exactly 1 conflict for free_to_paid_conversion containing all disagreeing agents
    assert len(conflicts) == 1
    assert conflicts[0].type == "assumption_divergence"
    assert "free_to_paid_conversion" in conflicts[0].disputed_item
    assert set(conflicts[0].agents) == {"CFO", "Growth", "Product"}


def test_overlapping_assumptions_remove_conflict():
    """When assumption ranges overlap, no assumption divergence conflict is flagged."""
    f1 = Finding(
        agent="CFO",
        task_id="t1",
        claim="Low conversion",
        recommendation="proceed_with_limits",
        assumptions=[
            Assumption(name="free_to_paid_conversion", low=0.015, base=0.025, high=0.035, unit="ratio", provenance="ai_assumption")
        ],
    )
    f2 = Finding(
        agent="Growth",
        task_id="t2",
        claim="Higher conversion",
        recommendation="proceed",
        assumptions=[
            Assumption(name="free_to_paid_conversion", low=0.030, base=0.040, high=0.050, unit="ratio", provenance="ai_assumption")
        ],
    )
    # [0.015, 0.035] overlaps with [0.030, 0.050] at 0.030..0.035
    conflicts = detect_assumption_divergence({"CFO": f1, "Growth": f2})
    assert len(conflicts) == 0


def test_simulation_resolution_verdicts_and_status():
    """Conflict resolver evaluates decision relevance and attaches status, verdict, and simulation IDs."""
    f_cfo = Finding(
        agent="CFO",
        task_id="t1",
        claim="Conservative conversion",
        recommendation="proceed_with_limits",
        assumptions=[
            Assumption(name="free_to_paid_conversion", low=0.010, base=0.015, high=0.020, unit="ratio", provenance="ai_assumption")
        ],
    )
    f_growth = Finding(
        agent="Growth",
        task_id="t2",
        claim="Optimistic conversion",
        recommendation="proceed",
        evidence=[Evidence(source_type="company_data", source_ref="funnel", snippet="High top of funnel")],
        assumptions=[
            Assumption(name="free_to_paid_conversion", low=0.040, base=0.050, high=0.065, unit="ratio", provenance="ai_assumption")
        ],
    )

    conflicts = detect_conflicts({"CFO": f_cfo, "Growth": f_growth})
    assert len(conflicts) >= 1

    company = load_company_snapshot()
    resolved_conflicts, sim_runs = resolve_conflicts_with_simulation(
        conflicts=conflicts,
        findings={"CFO": f_cfo, "Growth": f_growth},
        company=company,
    )

    assert len(resolved_conflicts) == len(conflicts)
    for c in resolved_conflicts:
        assert c.status in ("resolved_immaterial", "resolved_converged", "unresolved_material")
        assert c.verdict in ("decision_relevant", "immaterial")
        assert len(c.simulation_ids) > 0
        # If decision relevant and no rebuttal convergence, must remain unresolved
        if c.verdict == "decision_relevant" and c.status == "unresolved_material":
            assert c.resolved is False
