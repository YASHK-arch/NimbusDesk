"""Unit tests for Fix 8: Conflict resolver bugs, dynamic competitor, signed deltas, and simulation-based recommendation resolution."""

import pytest
from conflict.resolver import resolve_conflicts_with_simulation
from simulation.adapter import get_simulator_adapter
from simulation.sensitivity import find_flip_point
from state.schemas import Assumption, CompanySnapshot, Conflict, Finding


def test_contradictory_recommendation_supports_proceed_when_feasible():
    """Verify that proceed vs reject conflict is resolved by simulation supporting proceed if feasible positive strategy exists."""
    cfo_finding = Finding(
        agent="CFO",
        task_id="task_cfo",
        claim="Runway at risk; reject the plan.",
        recommendation="reject",
        confidence=0.85,
        assumptions=[],
    )
    growth_finding = Finding(
        agent="Growth",
        task_id="task_growth",
        claim="Growth upside is massive; proceed.",
        recommendation="proceed",
        confidence=0.90,
        assumptions=[],
    )

    conflict = Conflict(
        id="conf_rec_1",
        type="contradictory_recommendation",
        agents=["CFO", "Growth"],
        disputed_item="Recommendation divergence: CFO recommends 'reject' vs Growth recommends 'proceed'",
        evidence=[],
        resolved=False,
        status="detected",
    )

    resolved_conflicts, sim_runs = resolve_conflicts_with_simulation(
        conflicts=[conflict],
        findings={"CFO": cfo_finding, "Growth": growth_finding},
        min_runway=10.0,
    )

    assert len(resolved_conflicts) == 1
    c = resolved_conflicts[0]
    assert c.resolved is True
    assert c.status == "resolved_simulation"
    assert c.resolution_method == "simulation_supports_Growth"
    assert "contradicts CFO" in c.resolution or "supports Growth" in c.resolution


def test_contradictory_recommendation_supports_reject_when_unfeasible():
    """Verify that when no feasible strategy exists (min runway strict), reject agent is supported."""
    cfo_finding = Finding(
        agent="CFO",
        task_id="task_cfo",
        claim="Runway at risk; reject.",
        recommendation="reject",
        confidence=0.85,
        assumptions=[],
    )
    growth_finding = Finding(
        agent="Growth",
        task_id="task_growth",
        claim="Proceed anyway.",
        recommendation="proceed",
        confidence=0.90,
        assumptions=[],
    )

    conflict = Conflict(
        id="conf_rec_2",
        type="contradictory_recommendation",
        agents=["CFO", "Growth"],
        disputed_item="Recommendation divergence: CFO recommends 'reject' vs Growth recommends 'proceed'",
        evidence=[],
        resolved=False,
        status="detected",
    )

    # Impose impossible runway floor of 1000 months
    resolved_conflicts, sim_runs = resolve_conflicts_with_simulation(
        conflicts=[conflict],
        findings={"CFO": cfo_finding, "Growth": growth_finding},
        min_runway=1000.0,
    )

    assert len(resolved_conflicts) == 1
    c = resolved_conflicts[0]
    assert c.resolved is True
    assert c.status == "resolved_simulation"
    assert c.resolution_method == "simulation_supports_CFO"
    assert "contradicts Growth" in c.resolution or "supports CFO" in c.resolution


def test_contradictory_recommendation_mixed_evidence_unresolved():
    """Verify that when evidence is mixed (feasible under proceed, unfeasible under reject), marked unresolved_material."""
    cfo_finding = Finding(
        agent="CFO",
        task_id="task_cfo",
        claim="Runway at risk; low conversion and high cannibalization.",
        recommendation="reject",
        confidence=0.85,
        assumptions=[
            Assumption(
                name="free_to_paid_conversion",
                low=0.005,
                base=0.008,
                high=0.012,
                unit="ratio",
                provenance="ai_assumption",
                source_ref="mock",
                confidence=0.7,
                proposed_by="CFO",
            ),
            Assumption(
                name="starter_cannibalization_rate",
                low=0.20,
                base=0.30,
                high=0.40,
                unit="ratio",
                provenance="ai_assumption",
                source_ref="mock",
                confidence=0.7,
                proposed_by="CFO",
            ),
        ],
    )
    growth_finding = Finding(
        agent="Growth",
        task_id="task_growth",
        claim="High conversion; proceed.",
        recommendation="proceed",
        confidence=0.90,
        assumptions=[
            Assumption(
                name="free_to_paid_conversion",
                low=0.035,
                base=0.045,
                high=0.065,
                unit="ratio",
                provenance="ai_assumption",
                source_ref="mock",
                confidence=0.8,
                proposed_by="Growth",
            )
        ],
    )

    conflict = Conflict(
        id="conf_rec_mixed",
        type="contradictory_recommendation",
        agents=["CFO", "Growth"],
        disputed_item="Recommendation divergence: CFO recommends 'reject' vs Growth recommends 'proceed'",
        evidence=[],
        resolved=False,
        status="detected",
    )

    resolved_conflicts, sim_runs = resolve_conflicts_with_simulation(
        conflicts=[conflict],
        findings={"CFO": cfo_finding, "Growth": growth_finding},
        min_runway=10.0,
    )

    assert len(resolved_conflicts) == 1
    c = resolved_conflicts[0]
    assert c.resolved is False
    assert c.status == "unresolved_material"
    assert c.resolution_method == "unresolved_material"


def test_signed_deltas_formatting():
    """Verify that negative deltas in conflict resolution text never output '+$'."""
    cfo_finding = Finding(
        agent="CFO",
        task_id="task_cfo",
        claim="Conservative",
        recommendation="proceed_with_limits",
        confidence=0.80,
        assumptions=[
            Assumption(
                name="free_to_paid_conversion",
                low=0.040,
                base=0.045,
                high=0.050,
                unit="ratio",
                provenance="ai_assumption",
                source_ref="mock",
                confidence=0.7,
                proposed_by="CFO",
            )
        ],
    )
    growth_finding = Finding(
        agent="Growth",
        task_id="task_growth",
        claim="Aggressive",
        recommendation="proceed_with_limits",
        confidence=0.80,
        assumptions=[
            Assumption(
                name="free_to_paid_conversion",
                low=0.010,
                base=0.015,
                high=0.020,
                unit="ratio",
                provenance="ai_assumption",
                source_ref="mock",
                confidence=0.7,
                proposed_by="Growth",
            )
        ],
    )

    conflict = Conflict(
        id="conf_asm_delta",
        type="assumption_divergence",
        agents=["CFO", "Growth"],
        disputed_item="Non-overlapping bounds on 'free_to_paid_conversion'",
        evidence=[],
        resolved=False,
        status="detected",
    )

    resolved_conflicts, sim_runs = resolve_conflicts_with_simulation(
        conflicts=[conflict],
        findings={"CFO": cfo_finding, "Growth": growth_finding},
    )

    c = resolved_conflicts[0]
    # In this direction, Growth base (0.015) is lower than CFO base (0.045), so delta is negative
    assert "+$-" not in c.resolution
    assert "+$-" not in c.resolution.lower()


def test_find_flip_point_returns_exists_false_when_no_crossing():
    """Verify find_flip_point returns exists: False when ranking does not flip within parameter bounds."""
    adapter = get_simulator_adapter("free_plan")
    res = find_flip_point(
        primary_strategy=adapter.strategies[1],  # Strategy B
        competing_strategy=adapter.strategies[2],  # Strategy C
        parameter_name="free_to_paid_conversion",
        param_min=0.030,
        param_max=0.060,
        adapter=adapter,
    )

    # In 3%-6% range, Strategy B strongly dominates Strategy C throughout, so no flip point exists
    assert res["exists"] is False
    assert res["flip_value"] is None


def test_converged_status_only_after_rebuttal_and_unanimous_ranking():
    """Verify that resolved_converged is only assigned after rebuttal when all 3 baselines agree."""
    cfo_finding = Finding(
        agent="CFO",
        task_id="task_cfo",
        claim="Revised",
        recommendation="proceed_with_limits",
        confidence=0.85,
        assumptions=[
            Assumption(
                name="free_to_paid_conversion",
                low=0.020,
                base=0.024,
                high=0.030,
                unit="ratio",
                provenance="ai_assumption",
                source_ref="mock",
                confidence=0.8,
                proposed_by="CFO",
            )
        ],
    )
    growth_finding = Finding(
        agent="Growth",
        task_id="task_growth",
        claim="Revised",
        recommendation="proceed_with_limits",
        confidence=0.85,
        assumptions=[
            Assumption(
                name="free_to_paid_conversion",
                low=0.022,
                base=0.028,
                high=0.035,
                unit="ratio",
                provenance="ai_assumption",
                source_ref="mock",
                confidence=0.8,
                proposed_by="Growth",
            )
        ],
    )

    conflict = Conflict(
        id="conf_converge_test",
        type="assumption_divergence",
        agents=["CFO", "Growth"],
        disputed_item="Non-overlapping bounds on 'free_to_paid_conversion'",
        evidence=[],
        resolved=False,
        status="detected",
    )

    # 1. Without rebuttal_round=True: not marked converged_after_rebuttal
    resolved_pre, _ = resolve_conflicts_with_simulation(
        conflicts=[conflict.model_copy()],
        findings={"CFO": cfo_finding, "Growth": growth_finding},
        rebuttal_round=False,
    )
    assert resolved_pre[0].resolution_method != "converged_after_rebuttal"

    # 2. With rebuttal_round=True: marked converged_after_rebuttal
    resolved_post, _ = resolve_conflicts_with_simulation(
        conflicts=[conflict.model_copy()],
        findings={"CFO": cfo_finding, "Growth": growth_finding},
        rebuttal_round=True,
    )
    assert resolved_post[0].status == "resolved_converged"
    assert resolved_post[0].resolution_method == "converged_after_rebuttal"
    assert "Consensus achieved after rebuttal" in resolved_post[0].resolution

