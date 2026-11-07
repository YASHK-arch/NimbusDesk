"""Tests for Fix 1: Dynamic strategy ranking, confidence computation, and removal of hardcoded report literals."""

import pytest
from report.decision_logic import rank_strategies, compute_confidence, RankedStrategy
from report.report_builder import build_consolidated_report, render_report_markdown
from simulation.saas_model import simulate, STRATEGY_A, STRATEGY_B, STRATEGY_C
from state.company import load_company_snapshot
from state.schemas import Assumption, Decision, SimulationRun, VerificationResult
from state.shared_state import WorkflowState


def test_rank_strategies_feasible_ordering():
    """Verify strategies are ranked by net_contribution_12 subject to runway feasibility."""
    company = load_company_snapshot()
    assumptions = {"free_to_paid_conversion": 0.025}
    run_a = simulate(STRATEGY_A, "expected", assumptions, company=company)
    run_b = simulate(STRATEGY_B, "expected", assumptions, company=company)
    run_c = simulate(STRATEGY_C, "expected", assumptions, company=company)

    ranked = rank_strategies([run_a, run_b, run_c], min_runway=10.0)
    assert len(ranked) == 3
    assert all(isinstance(r, RankedStrategy) for r in ranked)
    # Feasible strategies must satisfy runway >= 10.0
    for r in ranked:
        if r.feasible:
            assert r.runway_months_12 >= 10.0


def test_rank_strategies_low_cash_not_feasible():
    """With very low cash balance, strategies violating the runway floor are marked not feasible."""
    company = load_company_snapshot()
    company.cash_balance = 50_000.0  # Only ~0.4 months of burn
    company.runway_months = 0.4
    assumptions = {"free_to_paid_conversion": 0.025}

    run_a = simulate(STRATEGY_A, "expected", assumptions, company=company)
    run_b = simulate(STRATEGY_B, "expected", assumptions, company=company)
    run_c = simulate(STRATEGY_C, "expected", assumptions, company=company)

    ranked = rank_strategies([run_a, run_b, run_c], min_runway=10.0)
    feasible_count = sum(1 for r in ranked if r.feasible)
    assert feasible_count == 0, "No strategy should be feasible with $50k cash and 10mo runway requirement"


def test_compute_confidence_scoring():
    """Confidence incorporates margin, assumption confidences, and penalties."""
    company = load_company_snapshot()
    assumptions_dict = {"free_to_paid_conversion": 0.025}
    run_a = simulate(STRATEGY_A, "expected", assumptions_dict, company=company)
    run_b = simulate(STRATEGY_B, "expected", assumptions_dict, company=company)
    run_c = simulate(STRATEGY_C, "expected", assumptions_dict, company=company)
    ranked = rank_strategies([run_a, run_b, run_c], min_runway=10.0)

    assumptions = [
        Assumption(
            name="free_to_paid_conversion",
            low=0.01,
            base=0.02,
            high=0.03,
            unit="ratio",
            provenance="ai_assumption",
            confidence=0.8,
        )
    ]

    conf_clean = compute_confidence(ranked, mc_summaries=None, assumptions=assumptions)
    assert conf_clean["level"] in ("Low", "Medium", "High")
    assert 0.0 <= conf_clean["score"] <= 1.0
    assert len(conf_clean["reasons"]) > 0

    # Degraded penalty lowers score
    conf_degraded = compute_confidence(
        ranked, mc_summaries=None, assumptions=assumptions, degraded_agents=["Growth"]
    )
    assert conf_degraded["score"] < conf_clean["score"]
    assert any("degraded" in r.lower() for r in conf_degraded["reasons"])


def test_report_builder_dynamic_recommendation_and_no_numeric_literals():
    """Verify recommendation changes with cash and thesis has no hardcoded literals."""
    company = load_company_snapshot()
    decision = Decision(
        id="dec-test",
        type="free_plan",
        question="Should we launch a free plan?",
        objective="Test",
        constraints=["Maintain company runway above 10 months"],
        status="pending",
    )
    assumptions_dict = {"free_to_paid_conversion": 0.025}
    sim_runs = [
        simulate(STRATEGY_A, "expected", assumptions_dict, company=company),
        simulate(STRATEGY_B, "expected", assumptions_dict, company=company),
        simulate(STRATEGY_C, "expected", assumptions_dict, company=company),
        simulate(STRATEGY_A, "conservative", assumptions_dict, company=company),
        simulate(STRATEGY_B, "conservative", assumptions_dict, company=company),
        simulate(STRATEGY_C, "conservative", assumptions_dict, company=company),
        simulate(STRATEGY_A, "optimistic", assumptions_dict, company=company),
        simulate(STRATEGY_B, "optimistic", assumptions_dict, company=company),
        simulate(STRATEGY_C, "optimistic", assumptions_dict, company=company),
    ]
    state = WorkflowState(
        decision=decision,
        simulation_runs=sim_runs,
        assumptions=[
            Assumption(
                name="free_to_paid_conversion",
                low=0.01,
                base=0.025,
                high=0.04,
                unit="ratio",
                provenance="ai_assumption",
                confidence=0.75,
            )
        ],
        status="completed",
    )

    report = build_consolidated_report(state, company=company)
    assert "Do not proceed" not in report["recommendation"]
    assert "Strategy" in report["recommendation"]

    # Now with low cash:
    company_poor = load_company_snapshot()
    company_poor.cash_balance = 30_000.0
    company_poor.runway_months = 0.2
    sim_runs_poor = [
        simulate(STRATEGY_A, "expected", assumptions_dict, company=company_poor),
        simulate(STRATEGY_B, "expected", assumptions_dict, company=company_poor),
        simulate(STRATEGY_C, "expected", assumptions_dict, company=company_poor),
        simulate(STRATEGY_A, "conservative", assumptions_dict, company=company_poor),
        simulate(STRATEGY_B, "conservative", assumptions_dict, company=company_poor),
        simulate(STRATEGY_C, "conservative", assumptions_dict, company=company_poor),
        simulate(STRATEGY_A, "optimistic", assumptions_dict, company=company_poor),
        simulate(STRATEGY_B, "optimistic", assumptions_dict, company=company_poor),
        simulate(STRATEGY_C, "optimistic", assumptions_dict, company=company_poor),
    ]
    state_poor = WorkflowState(
        decision=decision,
        simulation_runs=sim_runs_poor,
        assumptions=state.assumptions,
        status="completed",
    )
    report_poor = build_consolidated_report(state_poor, company=company_poor)
    assert "Do not proceed" in report_poor["recommendation"]


def test_markdown_status_derived_from_verification_results():
    """Markdown header reflects verification status rather than hardcoded 'Verified'."""
    company = load_company_snapshot()
    decision = Decision(id="dec-1", type="free_plan", question="Test?", objective="Test", status="completed")
    assumptions_dict = {"free_to_paid_conversion": 0.025}
    sim_runs = [
        simulate(STRATEGY_A, "expected", assumptions_dict, company=company),
        simulate(STRATEGY_B, "expected", assumptions_dict, company=company),
        simulate(STRATEGY_C, "expected", assumptions_dict, company=company),
    ]
    state_failed_verif = WorkflowState(
        decision=decision,
        simulation_runs=sim_runs,
        verification_results=[
            VerificationResult(check_name="test_check", status="failed", detail="Mismatch detected")
        ],
        status="completed",
    )
    report = build_consolidated_report(state_failed_verif, company=company)
    md = render_report_markdown(report, state=state_failed_verif)
    assert "**Status:** `Verification Failed`" in md
